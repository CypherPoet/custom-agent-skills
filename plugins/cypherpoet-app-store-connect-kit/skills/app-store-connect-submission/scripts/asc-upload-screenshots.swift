import CryptoKit
import Foundation

// asc-upload-screenshots.swift — upload App Store screenshots to the in-prep version via the ASC API.
// Reserve -> PUT bytes -> commit (uploaded + MD5) -> lock display order. Reads .env. Usage (repo root):
//     swift scripts/asc-upload-screenshots.swift shot1.png shot2.png ...
// Uploads in argument order (= product-page display order) into the APP_IPHONE_67 screenshot set
// (Apple's 6.7"/6.9" class — there is no APP_IPHONE_69; smaller iPhone classes auto-scale). PNG,
// no alpha, 1290x2796 or 1320x2868. The .p8 signs the JWT only; it's never printed.

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
        out[String(line[..<eq]).trimmingCharacters(in: .whitespaces)] =
            String(line[line.index(after: eq)...]).trimmingCharacters(in: .whitespaces)
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
    let h = try JSONSerialization.data(
        withJSONObject: ["alg": "ES256", "kid": keyID, "typ": "JWT"],
        options: [.sortedKeys]
    )
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
    // 204 No Content (e.g. relationship PATCH) carries no JSON body.
    if status == 204 { return [:] }
    let obj = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] ?? [:]
    guard (200 ..< 300).contains(status) else {
        fail("HTTP \(status) on \(method) \(path):\n\(String(data: data, encoding: .utf8) ?? "")")
    }
    return obj
}

func md5hex(_ data: Data) -> String {
    Insecure.MD5.hash(data: data).map { String(format: "%02x", $0) }.joined()
}

// MARK: - main

let files = Array(CommandLine.arguments.dropFirst())
guard !files.isEmpty else { fail("Usage: swift scripts/asc-upload-screenshots.swift <shot.png> ...") }

let env = loadDotEnv()
guard let keyID = config("ASC_KEY_ID", env: env), let issuerID = config("ASC_ISSUER_ID", env: env),
      let keysDir = config("API_PRIVATE_KEYS_DIR", env: env), let appID = config("ASC_APP_ID", env: env)
else { fail("Missing ASC_KEY_ID / ASC_ISSUER_ID / API_PRIVATE_KEYS_DIR / ASC_APP_ID (see .env.template).") }

let keyPath = (keysDir as NSString).appendingPathComponent("AuthKey_\(keyID).p8")
guard let pem = try? String(contentsOfFile: keyPath, encoding: .utf8) else { fail("Can't read \(keyPath).") }
let jwt: String
do { jwt = try makeJWT(keyID: keyID, issuerID: issuerID, pem: pem) } catch { fail("JWT signing failed: \(error)") }

func id(_ obj: [String: Any]) -> String {
    (obj["data"] as? [String: Any])?["id"] as? String ?? ""
}

func firstID(_ obj: [String: Any]) -> String? {
    ((obj["data"] as? [[String: Any]])?.first)?["id"] as? String
}

/// Prep version -> en-US localization.
let ver = api(
    "GET",
    "/v1/apps/\(appID)/appStoreVersions?filter[appStoreState]=PREPARE_FOR_SUBMISSION&limit=1",
    jwt: jwt
)
guard let versionID = firstID(ver) else { fail("No PREPARE_FOR_SUBMISSION version found.") }
let locs = api(
    "GET",
    "/v1/appStoreVersions/\(versionID)/appStoreVersionLocalizations?filter[locale]=en-US&limit=1",
    jwt: jwt
)
guard let locID = firstID(locs) else { fail("No en-US localization found.") }
print("version \(versionID), en-US localization \(locID)")

/// Clear any existing APP_IPHONE_67 set first (re-runnable; drops prior or failed uploads).
let existing = api(
    "GET",
    "/v1/appStoreVersionLocalizations/\(locID)/appScreenshotSets?fields[appScreenshotSets]=screenshotDisplayType&limit=50",
    jwt: jwt
)
for s in (existing["data"] as? [[String: Any]]) ?? [] {
    let dt = (s["attributes"] as? [String: Any])?["screenshotDisplayType"] as? String
    if dt == "APP_IPHONE_67", let sid = s["id"] as? String {
        _ = api("DELETE", "/v1/appScreenshotSets/\(sid)", jwt: jwt)
        print("removed existing APP_IPHONE_67 set \(sid)")
    }
}

/// One APP_IPHONE_67 screenshot set for the whole iPhone class.
let set = api("POST", "/v1/appScreenshotSets", jwt: jwt, body: [
    "data": ["type": "appScreenshotSets", "attributes": ["screenshotDisplayType": "APP_IPHONE_67"],
             "relationships": ["appStoreVersionLocalization": ["data": [
                 "type": "appStoreVersionLocalizations",
                 "id": locID,
             ]]]],
])
let setID = id(set)
print("created APP_IPHONE_67 screenshot set \(setID)")

var uploadedIDs: [String] = []
for path in files {
    let url = URL(fileURLWithPath: path)
    guard let bytes = try? Data(contentsOf: url) else { fail("Can't read \(path)") }
    let name = url.lastPathComponent

    // Reserve.
    let reserved = api("POST", "/v1/appScreenshots", jwt: jwt, body: [
        "data": ["type": "appScreenshots", "attributes": ["fileName": name, "fileSize": bytes.count],
                 "relationships": ["appScreenshotSet": ["data": ["type": "appScreenshotSets", "id": setID]]]],
    ])
    let shotID = id(reserved)
    let attrs = (reserved["data"] as? [String: Any])?["attributes"] as? [String: Any] ?? [:]
    let ops = attrs["uploadOperations"] as? [[String: Any]] ?? []

    // Upload each chunk to its pre-signed URL.
    for op in ops {
        guard let urlStr = op["url"] as? String, let method = op["method"] as? String else { continue }
        let offset: Int = (op["offset"] as? Int) ?? 0
        let length: Int = (op["length"] as? Int) ?? (bytes.count - offset)
        var req = URLRequest(url: URL(string: urlStr)!)
        req.httpMethod = method
        for h in op["requestHeaders"] as? [[String: Any]] ?? [] {
            if let n = h["name"] as? String, let v = h["value"] as? String { req.setValue(v, forHTTPHeaderField: n) }
        }
        let chunk: Data = bytes.subdata(in: offset ..< (offset + length))
        req.httpBody = chunk
        let (st, body) = send(req)
        guard (200 ..< 300).contains(st)
        else { fail("upload chunk failed (\(st)) for \(name):\n\(String(data: body, encoding: .utf8) ?? "")") }
    }

    // Commit.
    _ = api("PATCH", "/v1/appScreenshots/\(shotID)", jwt: jwt, body: [
        "data": ["type": "appScreenshots", "id": shotID,
                 "attributes": ["uploaded": true, "sourceFileChecksum": md5hex(bytes)]],
    ])
    uploadedIDs.append(shotID)
    print("uploaded \(name) -> appScreenshot \(shotID)")
}

// Lock display order to the upload order (the set otherwise keeps insertion order, but make it explicit).
_ = api("PATCH", "/v1/appScreenshotSets/\(setID)/relationships/appScreenshots", jwt: jwt, body: [
    "data": uploadedIDs.map { ["type": "appScreenshots", "id": $0] },
])
print("locked order: \(uploadedIDs.count) screenshots")
print("done — poll assetDeliveryState with asc-get (…/appScreenshotSets?include=appScreenshots).")
