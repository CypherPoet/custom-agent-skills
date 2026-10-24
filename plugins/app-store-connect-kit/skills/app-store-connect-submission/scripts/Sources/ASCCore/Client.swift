import Foundation

typealias JSON = [String: Any]

protocol HTTPTransport {
    func send(_ request: URLRequest) async throws -> (Data, HTTPURLResponse)
}

final class NoRedirects: NSObject, URLSessionTaskDelegate {
    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse,
                    newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) {
        completionHandler(nil)
    }
}

final class SessionTransport: HTTPTransport {
    private let session: URLSession
    init(configuration: URLSessionConfiguration = .ephemeral) {
        configuration.httpCookieStorage = nil
        configuration.urlCredentialStorage = nil
        configuration.urlCache = nil
        configuration.timeoutIntervalForRequest = 60
        configuration.timeoutIntervalForResource = 120
        session = URLSession(configuration: configuration, delegate: NoRedirects(), delegateQueue: nil)
    }
    func send(_ request: URLRequest) async throws -> (Data, HTTPURLResponse) {
        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse else { throw ASCError("Expected an HTTP response.") }
            return (data, http)
        } catch { throw ASCError("Network request failed. Inspect remote state before retrying a write.") }
    }
}

final class Client {
    static let origin = "https://api.appstoreconnect.apple.com"
    let transport: HTTPTransport
    let token: () throws -> String
    init(transport: HTTPTransport, token: @escaping () throws -> String) {
        self.transport = transport
        self.token = token
    }

    static func apiURL(_ path: String) throws -> URL {
        // Permit an absolute URL only for this exact origin (including pagination links).
        guard !path.contains("\\"), !path.contains(where: { $0.isWhitespace || $0.isNewline }) else {
            throw ASCError("Invalid API URL.")
        }
        let raw = path.hasPrefix("/") && !path.hasPrefix("//") ? origin + path : path
        let encoded = raw.replacingOccurrences(of: "[", with: "%5B").replacingOccurrences(of: "]", with: "%5D")
        guard let parts = URLComponents(string: encoded), parts.scheme == "https",
              parts.host?.lowercased() == "api.appstoreconnect.apple.com",
              parts.port == nil || parts.port == 443,
              parts.user == nil, parts.password == nil, parts.fragment == nil,
              let url = parts.url else { throw ASCError("Authenticated requests require the HTTPS App Store Connect API origin.") }
        return url
    }

    func request(_ method: String, _ path: String, body: JSON? = nil, allow404: Bool = false) async throws -> JSON {
        var request = URLRequest(url: try Self.apiURL(path))
        request.httpMethod = method
        request.setValue("Bearer \(try token())", forHTTPHeaderField: "Authorization")
        if let body {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        let (bytes, response) = try await transport.send(request)
        if allow404 && response.statusCode == 404 { return [:] }
        guard (200..<300).contains(response.statusCode) else {
            // Do not echo response bodies, signed URLs, or authorization values.
            throw ASCError("API HTTP \(response.statusCode); redirects and automatic write retries are disabled.")
        }
        if response.statusCode == 204 { return [:] }
        guard let object = try JSONSerialization.jsonObject(with: bytes) as? JSON else {
            throw ASCError("API returned an invalid JSON object.")
        }
        return object
    }

    func list(_ path: String) async throws -> [JSON] {
        var next: String? = path
        var visited = Set<String>()
        var result: [JSON] = []
        while let page = next {
            guard visited.insert(page).inserted, visited.count <= 100 else { throw ASCError("Invalid or excessive API pagination.") }
            let response = try await request("GET", page)
            guard let rows = response["data"] as? [JSON] else { throw ASCError("Expected an API resource list.") }
            result.append(contentsOf: rows)
            let link = (response["links"] as? JSON)?["next"]
            guard link == nil || link is NSNull || link is String else { throw ASCError("Invalid pagination link.") }
            next = link as? String
        }
        return result
    }

    func upload(_ operations: [JSON], bytes: Data) async throws {
        // Validate every range and URL before sending the first byte; do not attach the ASC JWT.
        var requests: [URLRequest] = []
        var expectedOffset = 0
        for op in operations {
            guard let text = op["url"] as? String, let url = URL(string: text), url.scheme == "https",
                  url.host != nil, url.user == nil, url.password == nil, url.fragment == nil,
                  let method = op["method"] as? String, method == "PUT",
                  let offset = op["offset"] as? Int, let length = op["length"] as? Int,
                  offset == expectedOffset, length > 0, offset <= bytes.count, length <= bytes.count - offset,
                  let headers = op["requestHeaders"] as? [JSON] else { throw ASCError("Invalid signed-upload operation.") }
            var req = URLRequest(url: url)
            req.httpMethod = method
            for header in headers {
                guard let name = header["name"] as? String, let value = header["value"] as? String,
                      !["authorization", "cookie", "proxy-authorization", "host"].contains(name.lowercased()),
                      !name.contains(where: { $0.isNewline }), !value.contains(where: { $0.isNewline })
                else { throw ASCError("Unsafe signed-upload header.") }
                req.setValue(value, forHTTPHeaderField: name)
            }
            req.httpBody = bytes.subdata(in: offset..<(offset + length))
            requests.append(req)
            expectedOffset += length
        }
        guard expectedOffset == bytes.count, !requests.isEmpty else { throw ASCError("Upload operations do not cover the file.") }
        for req in requests {
            let (_, response) = try await transport.send(req)
            guard (200..<300).contains(response.statusCode) else { throw ASCError("Asset upload HTTP \(response.statusCode); no redirect or retry was attempted.") }
        }
    }
}

func resource(_ object: JSON) throws -> JSON {
    guard let data = object["data"] as? JSON, data["id"] is String else { throw ASCError("Expected an API resource with an ID.") }
    return data
}

func identifier(_ value: String) throws -> String {
    guard value.range(of: "^[A-Za-z0-9-]+$", options: .regularExpression) != nil else { throw ASCError("Invalid resource ID.") }
    return value
}

struct Target {
    let appID: String
    let versionID: String
    let platform: String
    func verify(_ client: Client) async throws {
        let versions = try await client.list("/v1/apps/\(try identifier(appID))/appStoreVersions?fields[appStoreVersions]=platform,appVersionState&limit=200")
        let matches = versions.filter { $0["id"] as? String == versionID }
        guard matches.count == 1, let attrs = matches[0]["attributes"] as? JSON,
              attrs["platform"] as? String == platform,
              attrs["appVersionState"] as? String == "PREPARE_FOR_SUBMISSION" else {
            throw ASCError("Version must belong to the selected app/platform and be PREPARE_FOR_SUBMISSION. No legacy state fallback is used.")
        }
        _ = try identifier(versionID)
    }
    func localization(_ locale: String, client: Client) async throws -> String {
        let rows = try await client.list("/v1/appStoreVersions/\(try identifier(versionID))/appStoreVersionLocalizations?limit=200")
        let matches = rows.filter { ($0["attributes"] as? JSON)?["locale"] as? String == locale }
        guard matches.count == 1, let id = matches[0]["id"] as? String else { throw ASCError("Expected exactly one localization for the specified locale.") }
        return try identifier(id)
    }
}

struct Polling {
    let attempts: Int
    let interval: Double
    var sleep: (Double) async throws -> Void = { try await Task.sleep(nanoseconds: UInt64($0 * 1_000_000_000)) }
    func wait(label: String, success: Set<String>, failure: Set<String>, pending: Set<String>,
              read: () async throws -> String) async throws {
        guard attempts > 0, attempts <= 360, interval >= 0, interval <= 60 else { throw ASCError("Invalid polling limits.") }
        for attempt in 0..<attempts {
            let state = try await read()
            if success.contains(state) { return }
            if failure.contains(state) { throw ASCError("\(label): \(state).") }
            guard pending.contains(state) else { throw ASCError("\(label): unrecognized processing state; inspect the API response.") }
            if attempt + 1 < attempts { try await sleep(interval) }
        }
        throw ASCError("\(label): still processing after the polling limit; success is unconfirmed.", exitCode: 2)
    }
}
