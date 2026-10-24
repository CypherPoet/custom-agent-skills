import CryptoKit
import Foundation
import LocalAuthentication
import Security

struct ASCError: Error, CustomStringConvertible {
    let description: String
    let exitCode: Int32
    init(_ description: String, exitCode: Int32 = 1) {
        self.description = description
        self.exitCode = exitCode
    }
}

enum DotEnv {
    // Deliberately no shell execution, interpolation, or multiline values.
    static func parse(_ text: String) throws -> [String: String] {
        var values: [String: String] = [:]
        for (index, raw) in text.components(separatedBy: .newlines).enumerated() {
            var line = raw.trimmingCharacters(in: .whitespaces)
            if line.isEmpty || line.hasPrefix("#") { continue }
            if line.hasPrefix("export ") || line.hasPrefix("export\t") {
                line = String(line.dropFirst(6)).trimmingCharacters(in: .whitespaces)
            }
            func invalid() -> ASCError { ASCError("Invalid dotenv syntax on line \(index + 1).") }
            guard let eq = line.firstIndex(of: "=") else { throw invalid() }
            let key = String(line[..<eq]).trimmingCharacters(in: .whitespaces)
            guard key.range(of: "^[A-Za-z_][A-Za-z0-9_]*$", options: .regularExpression) != nil
            else { throw invalid() }
            let rawValue = String(line[line.index(after: eq)...]).trimmingCharacters(in: .whitespaces)
            if let quote = rawValue.first, quote == "\"" || quote == "'" {
                var result = ""
                var position = rawValue.index(after: rawValue.startIndex)
                var closed = false
                while position < rawValue.endIndex {
                    let character = rawValue[position]
                    position = rawValue.index(after: position)
                    if character == quote {
                        closed = true
                        break
                    }
                    if character == "\\" && quote == "\"" {
                        guard position < rawValue.endIndex else { throw invalid() }
                        let escaped = rawValue[position]
                        position = rawValue.index(after: position)
                        switch escaped {
                        case "n": result += "\n"
                        case "r": result += "\r"
                        case "t": result += "\t"
                        case "\\", "\"": result.append(escaped)
                        default: result += "\\"; result.append(escaped)
                        }
                    } else { result.append(character) }
                }
                let tail = rawValue[position...].trimmingCharacters(in: .whitespaces)
                guard closed, tail.isEmpty || tail.hasPrefix("#") else { throw invalid() }
                values[key] = result
            } else {
                // An unquoted # starts a comment only at the start or after whitespace.
                let comment = rawValue.indices.first {
                    rawValue[$0] == "#" && ($0 == rawValue.startIndex || rawValue[rawValue.index(before: $0)].isWhitespace)
                }
                values[key] = String(rawValue[..<(comment ?? rawValue.endIndex)]).trimmingCharacters(in: .whitespaces)
            }
        }
        return values
    }

    static func load(path: String, environment: [String: String], required: Bool) throws -> [String: String] {
        var values: [String: String] = [:]
        if FileManager.default.fileExists(atPath: path) {
            guard let data = FileManager.default.contents(atPath: path), let text = String(data: data, encoding: .utf8)
            else { throw ASCError("Cannot read the dotenv file as UTF-8.") }
            values = try parse(text)
        } else if required { throw ASCError("The specified dotenv file does not exist.") }
        // An explicitly empty environment variable also overrides the file; fail closed later.
        values.merge(environment) { _, process in process }
        return values
    }
}

struct Credentials {
    typealias KeychainLookup = (String, String) throws -> Data
    let keyID: String
    let issuerID: String
    let privateKey: P256.Signing.PrivateKey

    init(config: [String: String], readFile: (String) throws -> Data = { try Data(contentsOf: URL(fileURLWithPath: $0)) },
         keychainLookup: KeychainLookup = Credentials.readKeychain) throws {
        func required(_ key: String) throws -> String {
            guard let value = config[key], !value.isEmpty else { throw ASCError("Missing \(key).") }
            return value
        }
        keyID = try required("ASC_KEY_ID")
        issuerID = try required("ASC_ISSUER_ID")
        guard keyID.range(of: "^[A-Za-z0-9]+$", options: .regularExpression) != nil else {
            throw ASCError("ASC_KEY_ID must contain only letters and digits.")
        }
        let bytes: Data
        switch config["ASC_KEY_PROVIDER"] ?? "file" {
        case "file":
            let directory = try required("API_PRIVATE_KEYS_DIR")
            guard directory.hasPrefix("/") else { throw ASCError("API_PRIVATE_KEYS_DIR must be an absolute path.") }
            do { bytes = try readFile((directory as NSString).appendingPathComponent("AuthKey_\(keyID).p8")) }
            catch { throw ASCError("Cannot read the configured private-key file.") }
        case "keychain":
            let service = try required("ASC_KEYCHAIN_SERVICE")
            let account = try required("ASC_KEYCHAIN_ACCOUNT")
            do { bytes = try keychainLookup(service, account) }
            catch { throw ASCError("Cannot read the configured Keychain item without interaction; no file fallback was attempted.") }
        default: throw ASCError("ASC_KEY_PROVIDER must be file or keychain.")
        }
        guard let pem = String(data: bytes, encoding: .utf8), let key = try? P256.Signing.PrivateKey(pemRepresentation: pem)
        else { throw ASCError("The configured private key is not a valid P-256 PEM key.") }
        privateKey = key
    }

    static func readKeychain(service: String, account: String) throws -> Data {
        // Lookup only. Never creates/imports an item, alters its ACL, or prompts to unlock it.
        let context = LAContext()
        context.interactionNotAllowed = true
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
            kSecUseAuthenticationContext as String: context,
        ]
        var result: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess,
              let bytes = result as? Data else { throw ASCError("Keychain lookup unavailable.") }
        return bytes
    }

    func token(now: Date = Date()) throws -> String {
        func encode(_ data: Data) -> String {
            data.base64EncodedString().replacingOccurrences(of: "+", with: "-")
                .replacingOccurrences(of: "/", with: "_").replacingOccurrences(of: "=", with: "")
        }
        let issued = Int(now.timeIntervalSince1970)
        let header = try JSONSerialization.data(withJSONObject: ["alg": "ES256", "kid": keyID, "typ": "JWT"])
        let payload = try JSONSerialization.data(withJSONObject: [
            "iss": issuerID, "iat": issued, "exp": issued + 600, "aud": "appstoreconnect-v1",
        ])
        let input = encode(header) + "." + encode(payload)
        return try input + "." + encode(privateKey.signature(for: Data(input.utf8)).rawRepresentation)
    }
}
