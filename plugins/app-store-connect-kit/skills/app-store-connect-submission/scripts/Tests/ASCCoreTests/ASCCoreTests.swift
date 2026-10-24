import CryptoKit
import Foundation
import XCTest
@testable import ASCCore

final class MockTransport: HTTPTransport {
    var requests: [URLRequest] = []
    var handler: (URLRequest) throws -> (Int, JSON)
    init(_ handler: @escaping (URLRequest) throws -> (Int, JSON)) { self.handler = handler }
    func send(_ request: URLRequest) async throws -> (Data, HTTPURLResponse) {
        requests.append(request)
        let (status, json) = try handler(request)
        return (try JSONSerialization.data(withJSONObject: json), HTTPURLResponse(url: request.url!, statusCode: status, httpVersion: nil, headerFields: nil)!)
    }
}

func expectError(_ code: Int32 = 1, file: StaticString = #filePath, line: UInt = #line,
                 _ operation: () async throws -> Void) async {
    do { try await operation(); XCTFail("Expected failure", file: file, line: line) }
    catch let error as ASCError { XCTAssertEqual(error.exitCode, code, file: file, line: line) }
    catch { if code != 1 { XCTFail("Unexpected error type", file: file, line: line) } }
}

final class ConfigurationTests: XCTestCase {
    func testDotenvCommentsQuotesExportsAndLiteralExpansion() throws {
        let parsed = try DotEnv.parse(#"""
        # comment
        export ASC_KEY_ID = ABC123
        API_PRIVATE_KEYS_DIR=/Users/example/private_keys   # explanatory comment
        ASC_APP_ID=123 # numeric ID
        QUOTED="a # b\nnext" # outside
        SINGLE='literal $HOME \n # text'
        EMPTY=
        HASH=inside#value
        COMMAND=$(do-not-run)
        """#)
        XCTAssertEqual(parsed["ASC_KEY_ID"], "ABC123")
        XCTAssertEqual(parsed["API_PRIVATE_KEYS_DIR"], "/Users/example/private_keys")
        XCTAssertEqual(parsed["ASC_APP_ID"], "123")
        XCTAssertEqual(parsed["QUOTED"], "a # b\nnext")
        XCTAssertEqual(parsed["SINGLE"], #"literal $HOME \n # text"#)
        XCTAssertEqual(parsed["EMPTY"], "")
        XCTAssertEqual(parsed["HASH"], "inside#value")
        XCTAssertEqual(parsed["COMMAND"], "$(do-not-run)")
    }

    func testMalformedDotenvDoesNotEchoTheValue() {
        for text in ["BROKEN", "X='PRIVATE", "X=\"PRIVATE\"junk", "BAD-NAME=PRIVATE"] {
            XCTAssertThrowsError(try DotEnv.parse(text)) { error in
                XCTAssertFalse(String(describing: error).contains("PRIVATE"))
            }
        }
    }

    func testEnvironmentOverridesIncludingEmptyValue() throws {
        let file = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try Data("X=file\nY=kept".utf8).write(to: file)
        defer { try? FileManager.default.removeItem(at: file) }
        let config = try DotEnv.load(path: file.path, environment: ["X": ""], required: true)
        XCTAssertEqual(config, ["X": "", "Y": "kept"])
    }

    func testKeychainProviderUsesOnlyInjectedLookupAndSignsValidShortLivedJWT() throws {
        // A synthetic in-memory signing key, never registered with any account or saved.
        let key = P256.Signing.PrivateKey()
        var lookups = 0
        let config = ["ASC_KEY_ID": "TEST123", "ASC_ISSUER_ID": "issuer", "ASC_KEY_PROVIDER": "keychain",
                      "ASC_KEYCHAIN_SERVICE": "test-service", "ASC_KEYCHAIN_ACCOUNT": "test-account"]
        let credentials = try Credentials(config: config, readFile: { _ in XCTFail("No fallback"); return Data() }, keychainLookup: { service, account in
            XCTAssertEqual(service, "test-service"); XCTAssertEqual(account, "test-account")
            lookups += 1
            return Data(key.pemRepresentation.utf8)
        })
        let token = try credentials.token(now: Date(timeIntervalSince1970: 1000))
        let parts = token.split(separator: ".").map(String.init)
        func decode(_ text: String) -> Data {
            let base64 = text.replacingOccurrences(of: "-", with: "+").replacingOccurrences(of: "_", with: "/")
            return Data(base64Encoded: base64 + String(repeating: "=", count: (4 - base64.count % 4) % 4))!
        }
        let payload = try JSONSerialization.jsonObject(with: decode(parts[1])) as! JSON
        XCTAssertEqual(payload["iat"] as? Int, 1000)
        XCTAssertEqual(payload["exp"] as? Int, 1600)
        let signature = try P256.Signing.ECDSASignature(rawRepresentation: decode(parts[2]))
        XCTAssertTrue(key.publicKey.isValidSignature(signature, for: Data((parts[0] + "." + parts[1]).utf8)))
        XCTAssertEqual(lookups, 1)
        XCTAssertNotEqual(token, try credentials.token(now: Date(timeIntervalSince1970: 1100)))
    }

    func testProviderFailureIsRedactedAndNeverFallsBack() {
        XCTAssertThrowsError(try Credentials(config: ["ASC_KEY_ID": "TEST", "ASC_ISSUER_ID": "issuer", "ASC_KEY_PROVIDER": "keychain",
                                                     "ASC_KEYCHAIN_SERVICE": "fixture", "ASC_KEYCHAIN_ACCOUNT": "fixture"],
                                            readFile: { _ in XCTFail("No fallback"); return Data() },
                                            keychainLookup: { _, _ in throw ASCError("PRIVATE-VALUE") })) { error in
            XCTAssertFalse(String(describing: error).contains("PRIVATE-VALUE"))
        }
    }
}

final class ClientTests: XCTestCase {
    func testRejectsUnsafeOriginsBeforeGeneratingToken() async {
        let transport = MockTransport { _ in XCTFail("No network"); return (200, [:]) }
        let client = Client(transport: transport, token: { XCTFail("No credential use"); return "secret" })
        for url in ["http://api.appstoreconnect.apple.com/v1/apps", "https://evil.test/v1/apps",
                    "https://api.appstoreconnect.apple.com.evil.test/", "https://api.appstoreconnect.apple.com@evil.test/",
                    "https://api.appstoreconnect.apple.com:444/v1/apps", "//evil.test/x",
                    "https://user@api.appstoreconnect.apple.com/v1/apps", "/v1/apps#fragment", "/\\evil.test"] {
            await expectError { _ = try await client.request("GET", url) }
        }
        XCTAssertEqual(transport.requests.count, 0)
    }

    func testPaginationValidatesEveryNextURL() async {
        let transport = MockTransport { _ in (200, ["data": [], "links": ["next": "https://evil.test/next"]]) }
        var tokens = 0
        let client = Client(transport: transport, token: { tokens += 1; return "test-token" })
        await expectError { _ = try await client.list("/v1/apps?limit=200") }
        XCTAssertEqual(transport.requests.count, 1)
        XCTAssertEqual(tokens, 1)
    }

    func testAPIRedirectIsAnErrorWithoutRetry() async {
        for status in [301, 302, 303, 307, 308] {
            let transport = MockTransport { _ in (status, [:]) }
            let client = Client(transport: transport, token: { "test-token" })
            await expectError { _ = try await client.request("PATCH", "/v1/apps/test", body: [:]) }
            XCTAssertEqual(transport.requests.count, 1)
        }
    }

    func testRedirectDelegateRejectsSameOriginAndForeignRedirects() {
        let session = URLSession(configuration: .ephemeral)
        defer { session.invalidateAndCancel() }
        let task = session.dataTask(with: URL(string: Client.origin)!) // Never resumed.
        let delegate = NoRedirects()
        for destination in [Client.origin + "/next", "https://evil.test", "http://api.appstoreconnect.apple.com"] {
            var called = false
            delegate.urlSession(session, task: task,
                                willPerformHTTPRedirection: HTTPURLResponse(url: URL(string: Client.origin)!, statusCode: 307, httpVersion: nil, headerFields: nil)!,
                                newRequest: URLRequest(url: URL(string: destination)!)) { request in
                called = true; XCTAssertNil(request)
            }
            XCTAssertTrue(called)
        }
    }

    func testSignedUploadsHaveNoBearerAndRejectBadSecondChunkBeforeSendingAnything() async throws {
        let transport = MockTransport { req in
            XCTAssertNil(req.value(forHTTPHeaderField: "Authorization"))
            return (200, [:])
        }
        let client = Client(transport: transport, token: { XCTFail("No signing for asset upload"); return "secret" })
        let op: JSON = ["url": "https://asset.test/upload?signature=private", "method": "PUT", "offset": 0, "length": 3, "requestHeaders": []]
        try await client.upload([op], bytes: Data("abc".utf8))
        XCTAssertEqual(transport.requests[0].httpBody, Data("abc".utf8))
        transport.requests = []
        var first = op; first["length"] = 1
        var invalid = op; invalid["offset"] = 1; invalid["length"] = 9
        await expectError { try await client.upload([first, invalid], bytes: Data("abc".utf8)) }
        invalid = op; invalid["url"] = "http://asset.test/upload"
        await expectError { try await client.upload([invalid], bytes: Data("abc".utf8)) }
        invalid = op; invalid["requestHeaders"] = [["name": "Authorization", "value": "secret"]]
        await expectError { try await client.upload([invalid], bytes: Data("abc".utf8)) }
        XCTAssertTrue(transport.requests.isEmpty)
    }
}

final class PollingTests: XCTestCase {
    func testPendingThenSuccessPollsWithBoundedDelay() async throws {
        var states = ["PROCESSING", "PROCESSING", "VALID"]
        var sleeps = 0
        let polling = Polling(attempts: 3, interval: 2, sleep: { XCTAssertEqual($0, 2); sleeps += 1 })
        try await polling.wait(label: "fixture", success: ["VALID"], failure: ["FAILED", "INVALID"], pending: ["PROCESSING"]) { states.removeFirst() }
        XCTAssertEqual(sleeps, 2)
    }
    func testFailedUnknownAndTimeoutHaveDistinctStatuses() async {
        let polling = Polling(attempts: 1, interval: 0)
        for state in ["FAILED", "INVALID", "UNRECOGNIZED", ""] {
            await expectError { try await polling.wait(label: "fixture", success: ["VALID"], failure: ["FAILED", "INVALID"], pending: ["PROCESSING"]) { state } }
        }
        await expectError(2) { try await polling.wait(label: "fixture", success: ["VALID"], failure: ["FAILED"], pending: ["PROCESSING"]) { "PROCESSING" } }
    }
}

final class MediaServer {
    var assets: [String]
    var delivery = "COMPLETE"
    var uploadStatus = 200
    var changedConcurrently = false
    var wrongPlatform = false
    var wrongLocale = false
    var failDelete = false
    var nextID = 0
    var events: [String] = []
    let kind: MediaKind
    init(oldCount: Int = 1, kind: MediaKind = .screenshot) { self.kind = kind; assets = (0..<oldCount).map { "old\($0)" } }
    lazy var transport = MockTransport { [unowned self] request in try self.handle(request) }
    var client: Client { Client(transport: transport, token: { "test-token" }) }
    func handle(_ req: URLRequest) throws -> (Int, JSON) {
        let path = req.url!.path
        let method = req.httpMethod!
        events.append(method + " " + path)
        if req.url!.host == "asset.test" { XCTAssertNil(req.value(forHTTPHeaderField: "Authorization")); return (uploadStatus, [:]) }
        if path == "/v1/apps/app/appStoreVersions" {
            return (200, ["data": [["id": "version", "attributes": ["platform": wrongPlatform ? "MAC_OS" : "IOS", "appVersionState": "PREPARE_FOR_SUBMISSION"]]]])
        }
        if path.hasSuffix("appStoreVersionLocalizations") {
            return (200, ["data": [["id": "localization", "attributes": ["locale": wrongLocale ? "fr-FR" : "en-US"]]]])
        }
        if path == "/v1/appStoreVersionLocalizations/localization/\(kind.sets)" {
            return (200, ["data": [["id": "set", "attributes": [kind.displayAttribute: kind == .screenshot ? "APP_IPHONE_67" : "IPHONE_67"]]]])
        }
        if path == "/v1/\(kind.sets)/set/\(kind.assets)" {
            var ids = assets
            if changedConcurrently && nextID > 0 { ids.append("concurrent") }
            return (200, ["data": ids.map { ["id": $0] }])
        }
        if path == "/v1/\(kind.assets)" && method == "POST" {
            nextID += 1
            let id = "new\(nextID)"
            assets.append(id)
            return (201, ["data": ["id": id, "attributes": ["uploadOperations": [[
                "url": "https://asset.test/upload", "method": "PUT", "offset": 0, "length": 3, "requestHeaders": [],
            ]]]]])
        }
        if path.hasPrefix("/v1/\(kind.assets)/") {
            let id = req.url!.lastPathComponent
            if method == "DELETE" {
                if failDelete { return (500, [:]) }
                assets.removeAll { $0 == id }; return (204, [:])
            }
            return (200, ["data": ["id": id, "attributes": [kind.stateAttribute: ["state": delivery]]]])
        }
        if path == "/v1/\(kind.sets)/set/relationships/\(kind.assets)" && method == "PATCH" {
            let object = try JSONSerialization.jsonObject(with: req.httpBody!) as! JSON
            assets = (object["data"] as! [JSON]).map { $0["id"] as! String }
            return (204, [:])
        }
        XCTFail("Unexpected mock operation: \(method) \(path)")
        throw ASCError("Unexpected mock operation.")
    }
    func upload(replace: Bool = true) -> MediaUpload {
        MediaUpload(target: Target(appID: "app", versionID: "version", platform: "IOS"), locale: "en-US", displayType: kind == .screenshot ? "APP_IPHONE_67" : "IPHONE_67",
                    kind: kind, replace: replace, polling: Polling(attempts: 1, interval: 0), report: { _ in })
    }
    let files = [MediaFile(name: "fixture.png", bytes: Data("abc".utf8))]
}

final class MediaTests: XCTestCase {
    func testReplacementDeletesOriginalOnlyAfterCompletionAndSetsOrder() async throws {
        let server = MediaServer()
        try await server.upload().run(files: server.files, client: server.client)
        XCTAssertEqual(server.assets, ["new1"])
        let validated = server.events.firstIndex(of: "GET /v1/appScreenshots/new1")!
        let removed = server.events.firstIndex(of: "DELETE /v1/appScreenshots/old0")!
        XCTAssertGreaterThan(removed, validated)
        XCTAssertFalse(server.events.contains("DELETE /v1/appScreenshotSets/set"))
    }
    func testFailedUploadFailedProcessingAndPendingNeverDeleteOriginal() async {
        for scenario in ["upload", "FAILED", "PROCESSING", "unknown"] {
            let server = MediaServer()
            if scenario == "upload" { server.uploadStatus = 500 } else { server.delivery = scenario }
            await expectError(scenario == "PROCESSING" ? 2 : 1) { try await server.upload().run(files: server.files, client: server.client) }
            XCTAssertTrue(server.assets.contains("old0"))
            XCTAssertFalse(server.events.contains { $0.hasPrefix("DELETE") })
        }
    }
    func testNoCapacityAndMissingReplaceFlagFailWithoutWrites() async {
        for count in [1, 10] {
            let server = MediaServer(oldCount: count)
            await expectError { try await server.upload(replace: count == 10).run(files: server.files, client: server.client) }
            XCTAssertTrue(server.events.allSatisfy { $0.hasPrefix("GET") })
        }
    }
    func testWrongTargetAndLocaleFailWithoutWrites() async {
        for platform in [true, false] {
            let server = MediaServer()
            server.wrongPlatform = platform; server.wrongLocale = !platform
            await expectError { try await server.upload().run(files: server.files, client: server.client) }
            XCTAssertTrue(server.events.allSatisfy { $0.hasPrefix("GET") })
        }
    }
    func testConcurrentChangePreservesOriginal() async {
        let server = MediaServer(); server.changedConcurrently = true
        await expectError { try await server.upload().run(files: server.files, client: server.client) }
        XCTAssertTrue(server.assets.contains("old0"))
        XCTAssertFalse(server.events.contains { $0.hasPrefix("DELETE") })
    }
    func testCleanupFailureIsNotReportedAsSuccessOrRetried() async {
        let server = MediaServer(); server.failDelete = true
        await expectError { try await server.upload().run(files: server.files, client: server.client) }
        XCTAssertEqual(server.events.filter { $0.hasPrefix("DELETE") }.count, 1)
        XCTAssertEqual(Set(server.assets), Set(["old0", "new1"]))
    }
    func testMissingFileAndMissingExplicitTargetDoNotReadCredentials() async throws {
        let options = ["upload-screenshots", "--app-id", "app", "--version-id", "version", "--platform", "IOS", "--locale", "en-US", "--display-type", "APP_IPHONE_67", "/missing/fixture.png"]
        for arguments in [options, ["upload-screenshots", "fixture.png"]] {
            let args = try Arguments(arguments)
            await expectError { try await Commands.run(args, makeClient: { XCTFail("No credentials before preflight"); throw ASCError("unexpected") }) }
        }
    }
}
