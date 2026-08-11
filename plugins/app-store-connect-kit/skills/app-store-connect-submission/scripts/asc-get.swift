import CryptoKit
import Foundation

// asc-get.swift — GET any App Store Connect API path using the .env key; pretty-print the JSON.
// Read-only. Usage (from the repo root, .env filled — see .env.template):
//     swift scripts/asc-get.swift "/v1/apps/<id>/appStoreVersions?filter[appStoreState]=PREPARE_FOR_SUBMISSION"
// The .p8 is read only to sign the JWT; its contents are never printed.

func config(_ key: String, env: [String: String]) -> String? {
    if let v = ProcessInfo.processInfo.environment[key], !v.isEmpty { return v }
    return env[key]
}

func loadDotEnv(_ path: String = ".env") -> [String: String] {
    guard let text = try? String(contentsOfFile: path, encoding: .utf8) else { return [:] }
    var out: [String: String] = [:]
    for raw in text.split(separator: "\n", omittingEmptySubsequences: true) {
        let line = raw.trimmingCharacters(in: .whitespaces)
        guard !line.isEmpty, !line.hasPrefix("#"), let eq = line.firstIndex(of: "=") else { continue }
        let k = String(line[..<eq]).trimmingCharacters(in: .whitespaces)
        let v = String(line[line.index(after: eq)...]).trimmingCharacters(in: .whitespaces)
        if !k.isEmpty { out[k] = v }
    }
    return out
}

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

func base64url(_ data: Data) -> String {
    data.base64EncodedString()
        .replacingOccurrences(of: "+", with: "-")
        .replacingOccurrences(of: "/", with: "_")
        .replacingOccurrences(of: "=", with: "")
}

func makeJWT(keyID: String, issuerID: String, privateKeyPEM: String) throws -> String {
    let key = try P256.Signing.PrivateKey(pemRepresentation: privateKeyPEM)
    let now = Int(Date().timeIntervalSince1970)
    let header: [String: Any] = ["alg": "ES256", "kid": keyID, "typ": "JWT"]
    let payload: [String: Any] = ["iss": issuerID, "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"]
    let headerJSON = try JSONSerialization.data(withJSONObject: header, options: [.sortedKeys])
    let payloadJSON = try JSONSerialization.data(withJSONObject: payload, options: [.sortedKeys])
    let signingInput = base64url(headerJSON) + "." + base64url(payloadJSON)
    let signature = try key.signature(for: Data(signingInput.utf8))
    return signingInput + "." + base64url(signature.rawRepresentation)
}

func get(path: String, jwt: String) -> (Int, Data) {
    let encoded = path.replacingOccurrences(of: "[", with: "%5B").replacingOccurrences(of: "]", with: "%5D")
    let url = encoded.hasPrefix("http")
        ? URL(string: encoded)!
        : URL(string: "https://api.appstoreconnect.apple.com" + encoded)!
    var request = URLRequest(url: url)
    request.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")
    var result: (Data?, URLResponse?, Error?) = (nil, nil, nil)
    let semaphore = DispatchSemaphore(value: 0)
    URLSession.shared.dataTask(with: request) { d, r, e in result = (d, r, e); semaphore.signal() }.resume()
    semaphore.wait()
    if let error = result.2 { fail("Network error: \(error.localizedDescription)") }
    guard let http = result.1 as? HTTPURLResponse, let data = result.0 else { fail("No response") }
    return (http.statusCode, data)
}

let env = loadDotEnv()
guard let keyID = config("ASC_KEY_ID", env: env),
      let issuerID = config("ASC_ISSUER_ID", env: env),
      let keysDir = config("API_PRIVATE_KEYS_DIR", env: env)
else { fail("Missing ASC_KEY_ID / ASC_ISSUER_ID / API_PRIVATE_KEYS_DIR (see .env.template).") }

guard let path = CommandLine.arguments.dropFirst().first else {
    fail("Usage: swift scripts/asc-get.swift \"<api-path>\"  (e.g. /v1/apps/<id>/appStoreVersions)")
}

let keyPath = (keysDir as NSString).appendingPathComponent("AuthKey_\(keyID).p8")
guard let pem = try? String(contentsOfFile: keyPath, encoding: .utf8) else {
    fail("Couldn't read \(keyPath) — check API_PRIVATE_KEYS_DIR and the filename.")
}

let jwt: String
do { jwt = try makeJWT(keyID: keyID, issuerID: issuerID, privateKeyPEM: pem) }
catch { fail("Couldn't sign the JWT: \(error)") }

let (status, data) = get(path: path, jwt: jwt)
let pretty = (try? JSONSerialization.jsonObject(with: data))
    .flatMap { try? JSONSerialization.data(withJSONObject: $0, options: [.prettyPrinted, .sortedKeys]) }
    .flatMap { String(data: $0, encoding: .utf8) } ?? String(data: data, encoding: .utf8) ?? ""
print("HTTP \(status)")
print(pretty)
exit(status == 200 ? 0 : 1)
