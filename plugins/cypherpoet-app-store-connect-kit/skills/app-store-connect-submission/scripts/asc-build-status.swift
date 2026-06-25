import CryptoKit
import Foundation

// asc-build-status.swift — poll the latest App Store Connect build's processing state.
//
// No fastlane. Reads the App Store Connect API key config from the environment (or a
// repo-root .env), mints a short-lived ES256 JWT with CryptoKit, and asks the REST API
// for the most recent build of the app named by ASC_APP_ID.
//
// Usage (from the repo root, after filling .env — see .env.template / README):
//     swift scripts/asc-build-status.swift
//
// Config (process env wins; otherwise read from ./.env):
//     ASC_KEY_ID            the key's Key ID (the .p8 must be named AuthKey_<ASC_KEY_ID>.p8)
//     ASC_ISSUER_ID         the Issuer ID (UUID) at the top of the Integrations page
//     API_PRIVATE_KEYS_DIR  absolute path to the dir holding AuthKey_<ASC_KEY_ID>.p8
//     ASC_APP_ID            the app's numeric Apple ID (App Information -> Apple ID)
//
// The .p8 stays a gitignored file this script reads only to sign the JWT — its contents
// are never printed. Same posture as a gh token.

/// Look a key up in the process environment first, then fall back to a `KEY=VALUE` line in ./.env.
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
    let payload: [String: Any] = [
        "iss": issuerID, "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1",
    ]
    let headerJSON = try JSONSerialization.data(withJSONObject: header, options: [.sortedKeys])
    let payloadJSON = try JSONSerialization.data(withJSONObject: payload, options: [.sortedKeys])

    let signingInput = base64url(headerJSON) + "." + base64url(payloadJSON)
    // CryptoKit's ECDSA signature(for:) hashes with SHA-256 (ES256); rawRepresentation is the
    // 64-byte r||s that JWS expects (DER would be wrong here).
    let signature = try key.signature(for: Data(signingInput.utf8))
    return signingInput + "." + base64url(signature.rawRepresentation)
}

func latestBuild(appID: String, jwt: String) -> [String: Any]? {
    var components = URLComponents(string: "https://api.appstoreconnect.apple.com/v1/builds")!
    components.queryItems = [
        URLQueryItem(name: "filter[app]", value: appID),
        // build `version` is a string ("12" sorts after "100"); sort by upload time for "latest".
        URLQueryItem(name: "sort", value: "-uploadedDate"),
        URLQueryItem(name: "limit", value: "1"),
        URLQueryItem(name: "fields[builds]", value: "version,processingState,uploadedDate"),
    ]
    var request = URLRequest(url: components.url!)
    request.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")

    var result: (Data?, URLResponse?, Error?) = (nil, nil, nil)
    let semaphore = DispatchSemaphore(value: 0)
    URLSession.shared.dataTask(with: request) { data, response, error in
        result = (data, response, error)
        semaphore.signal()
    }.resume()
    semaphore.wait()

    if let error = result.2 { fail("Network error: \(error.localizedDescription)") }
    guard let http = result.1 as? HTTPURLResponse, let data = result.0 else { fail("No response") }
    guard http.statusCode == 200 else {
        let body = String(data: data, encoding: .utf8) ?? ""
        fail("HTTP \(http.statusCode) from App Store Connect:\n\(body)")
    }
    let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
    let builds = (json ?? [:])["data"] as? [[String: Any]]
    return builds?.first?["attributes"] as? [String: Any]
}

let env = loadDotEnv()
guard let keyID = config("ASC_KEY_ID", env: env),
      let issuerID = config("ASC_ISSUER_ID", env: env),
      let keysDir = config("API_PRIVATE_KEYS_DIR", env: env),
      let appID = config("ASC_APP_ID", env: env)
else {
    fail("""
    Missing config. Set ASC_KEY_ID, ASC_ISSUER_ID, API_PRIVATE_KEYS_DIR, and ASC_APP_ID
    in the environment or a repo-root .env (see .env.template).
    """)
}

let keyPath = (keysDir as NSString).appendingPathComponent("AuthKey_\(keyID).p8")
guard let pem = try? String(contentsOfFile: keyPath, encoding: .utf8) else {
    fail("Couldn't read the private key at \(keyPath) — check API_PRIVATE_KEYS_DIR and the filename.")
}

let jwt: String
do { jwt = try makeJWT(keyID: keyID, issuerID: issuerID, privateKeyPEM: pem) }
catch { fail("Couldn't sign the JWT (is the .p8 a valid App Store Connect key?): \(error)") }

guard let build = latestBuild(appID: appID, jwt: jwt) else {
    print("No builds found for app \(appID).")
    exit(0)
}

let version = build["version"] as? String ?? "?"
let state = build["processingState"] as? String ?? "?"
let uploaded = build["uploadedDate"] as? String ?? "?"
print("Latest build \(version): \(state)  (uploaded \(uploaded))")
switch state {
case "VALID": print("→ Processed. Now selectable on the version page (and attachable via the API).")
case "PROCESSING": print("→ Still processing. Re-run in a bit.")
case "FAILED", "INVALID": print("→ Processing failed — check App Store Connect for the reason.")
default: break
}
