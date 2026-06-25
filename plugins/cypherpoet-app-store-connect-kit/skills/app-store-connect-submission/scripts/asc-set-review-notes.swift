import CryptoKit
import Foundation

// asc-set-review-notes.swift — set the App Review "Notes" on the in-prep version via the ASC API.
// Reads notes text from a file arg (or stdin). Reads .env. Usage (from your project root):
//     swift scripts/asc-set-review-notes.swift review-notes.txt
//     pbpaste | swift scripts/asc-set-review-notes.swift
// The review-detail record already exists once the review contact is set, so this PATCHes it;
// if somehow absent it POSTs a new one related to the version. The .p8 only signs the JWT.

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
    FileHandle.standardError.write(Data((message + "\n").utf8)); exit(1)
}

func base64url(_ data: Data) -> String {
    data.base64EncodedString().replacingOccurrences(of: "+", with: "-")
        .replacingOccurrences(of: "/", with: "_").replacingOccurrences(of: "=", with: "")
}

func makeJWT(keyID: String, issuerID: String, pem: String) throws -> String {
    let key = try P256.Signing.PrivateKey(pemRepresentation: pem)
    let now = Int(Date().timeIntervalSince1970)
    let h = try JSONSerialization.data(withJSONObject: ["alg": "ES256", "kid": keyID, "typ": "JWT"], options: [.sortedKeys])
    let p = try JSONSerialization.data(
        withJSONObject: ["iss": issuerID, "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"],
        options: [.sortedKeys]
    )
    let input = base64url(h) + "." + base64url(p)
    return try input + "." + base64url(key.signature(for: Data(input.utf8)).rawRepresentation)
}

let base = "https://api.appstoreconnect.apple.com"

func send(_ req: URLRequest) -> (Int, Data) {
    var result: (Data?, URLResponse?, Error?) = (nil, nil, nil)
    let s = DispatchSemaphore(value: 0)
    URLSession.shared.dataTask(with: req) { d, r, e in result = (d, r, e); s.signal() }.resume()
    s.wait()
    if let e = result.2 { fail("Network error: \(e.localizedDescription)") }
    guard let http = result.1 as? HTTPURLResponse, let d = result.0 else { fail("No response") }
    return (http.statusCode, d)
}

func api(_ method: String, _ path: String, jwt: String, body: [String: Any]? = nil) -> [String: Any] {
    let enc = path.replacingOccurrences(of: "[", with: "%5B").replacingOccurrences(of: "]", with: "%5D")
    var req = URLRequest(url: enc.hasPrefix("http") ? URL(string: enc)! : URL(string: base + enc)!)
    req.httpMethod = method
    req.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")
    if let body {
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)
    }
    let (status, data) = send(req)
    if status == 204 { return [:] }
    let obj = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] ?? [:]
    guard (200 ..< 300).contains(status) else {
        fail("HTTP \(status) on \(method) \(path):\n\(String(data: data, encoding: .utf8) ?? "")")
    }
    return obj
}

// MARK: - main

let env = loadDotEnv()
guard let keyID = config("ASC_KEY_ID", env: env), let issuerID = config("ASC_ISSUER_ID", env: env),
      let keysDir = config("API_PRIVATE_KEYS_DIR", env: env), let appID = config("ASC_APP_ID", env: env)
else { fail("Missing ASC_KEY_ID / ASC_ISSUER_ID / API_PRIVATE_KEYS_DIR / ASC_APP_ID (see .env.template).") }

/// Notes text: from the file arg, else stdin.
let notes: String
if let path = CommandLine.arguments.dropFirst().first {
    guard let text = try? String(contentsOfFile: path, encoding: .utf8) else { fail("Can't read \(path)") }
    notes = text.trimmingCharacters(in: .whitespacesAndNewlines)
} else {
    let stdin = String(data: FileHandle.standardInput.readDataToEndOfFile(), encoding: .utf8) ?? ""
    notes = stdin.trimmingCharacters(in: .whitespacesAndNewlines)
}

guard !notes.isEmpty else { fail("No notes text (pass a file path or pipe text in).") }

let keyPath = (keysDir as NSString).appendingPathComponent("AuthKey_\(keyID).p8")
guard let pem = try? String(contentsOfFile: keyPath, encoding: .utf8) else { fail("Can't read \(keyPath).") }
let jwt: String
do { jwt = try makeJWT(keyID: keyID, issuerID: issuerID, pem: pem) } catch { fail("JWT signing failed: \(error)") }

func firstID(_ obj: [String: Any]) -> String? {
    ((obj["data"] as? [[String: Any]])?.first)?["id"] as? String
}

/// Prep version, then its review-detail record (it pre-exists once the contact is set).
let ver = api("GET", "/v1/apps/\(appID)/appStoreVersions?filter[appVersionState]=PREPARE_FOR_SUBMISSION&limit=1", jwt: jwt)
guard let versionID = firstID(ver) else { fail("No PREPARE_FOR_SUBMISSION version found.") }

let existing = api("GET", "/v1/appStoreVersions/\(versionID)/appStoreReviewDetail", jwt: jwt)
let detailID = (existing["data"] as? [String: Any])?["id"] as? String

if let detailID {
    _ = api("PATCH", "/v1/appStoreReviewDetails/\(detailID)", jwt: jwt, body: [
        "data": ["type": "appStoreReviewDetails", "id": detailID, "attributes": ["notes": notes]],
    ])
    print("updated review notes on appStoreReviewDetails/\(detailID)")
} else {
    let created = api("POST", "/v1/appStoreReviewDetails", jwt: jwt, body: [
        "data": ["type": "appStoreReviewDetails", "attributes": ["notes": notes],
                 "relationships": ["appStoreVersion": ["data": ["type": "appStoreVersions", "id": versionID]]]],
    ])
    print("created review notes -> \((created["data"] as? [String: Any])?["id"] as? String ?? "?")")
}
