import CoreGraphics
import Foundation
import ImageIO
import UniformTypeIdentifiers
import XCTest
@testable import ASCCore

final class CommandTests: XCTestCase {
    func buildResponse(state: String, appID: String = "app", platform: String = "IOS") -> JSON {
        ["data": ["id": "build", "attributes": ["processingState": state], "relationships": [
            "app": ["data": ["id": appID]], "preReleaseVersion": ["data": ["id": "prerelease"]],
        ]], "included": [["type": "preReleaseVersions", "id": "prerelease", "attributes": ["platform": platform]]]]
    }

    func testBuildCommandPollsOnlySelectedBuildAndRefreshesToken() async throws {
        var states = ["PROCESSING", "VALID"]
        var tokenCount = 0
        var reported: [String] = []
        let transport = MockTransport { req in
            XCTAssertEqual(req.url?.path, "/v1/builds/build")
            XCTAssertEqual(URLComponents(url: req.url!, resolvingAgainstBaseURL: false)?.queryItems?.first?.value, "app,preReleaseVersion")
            return (200, self.buildResponse(state: states.removeFirst()))
        }
        let client = Client(transport: transport, token: { tokenCount += 1; return "test-token-\(tokenCount)" })
        let args = try Arguments(["build-status", "--app-id", "app", "--build-id", "build", "--platform", "IOS", "--attempts", "2", "--interval", "0"])
        try await Commands.run(args, makeClient: { client }, report: { reported.append($0) })
        XCTAssertEqual(reported, ["Build build: VALID."])
        XCTAssertEqual(tokenCount, 2)
    }

    func testBuildCommandRejectsWrongAppPlatformFailureAndMissingBuild() async throws {
        let args = try Arguments(["build-status", "--app-id", "app", "--build-id", "build", "--platform", "IOS", "--attempts", "1"])
        let scenarios: [(Int, JSON, Int32)] = [
            (200, buildResponse(state: "VALID", appID: "other"), 1),
            (200, buildResponse(state: "VALID", platform: "MAC_OS"), 1),
            (200, buildResponse(state: "INVALID"), 1),
            (200, buildResponse(state: "FAILED"), 1),
            (200, buildResponse(state: "PROCESSING"), 2),
            (404, ["errors": []], 1),
            (200, ["data": []], 1),
        ]
        for (status, body, code) in scenarios {
            let client = Client(transport: MockTransport { _ in (status, body) }, token: { "test-token" })
            await expectError(code) { try await Commands.run(args, makeClient: { client }, report: { _ in XCTFail("Must not report success") }) }
        }
    }

    func testVersionSelectionUsesExactIDAcrossPages() async throws {
        let transport = MockTransport { req in
            if req.url!.query!.contains("cursor=") {
                return (200, ["data": [["id": "wanted", "attributes": ["platform": "IOS", "appVersionState": "PREPARE_FOR_SUBMISSION"]]]])
            }
            return (200, ["data": [["id": "first-other-version", "attributes": ["platform": "MAC_OS", "appVersionState": "PREPARE_FOR_SUBMISSION"]]],
                          "links": ["next": Client.origin + "/v1/apps/app/appStoreVersions?cursor=next"]])
        }
        let client = Client(transport: transport, token: { "test-token" })
        try await Target(appID: "app", versionID: "wanted", platform: "IOS").verify(client)
        XCTAssertEqual(transport.requests.count, 2)
        await expectError { try await Target(appID: "app", versionID: "not-present", platform: "IOS").verify(client) }
    }

    func testLegacyOrMissingVersionStateFailsClosed() async {
        for state in ["appStoreState", "missing"] {
            let transport = MockTransport { _ in (200, ["data": [["id": "version", "attributes": ["platform": "IOS", state: "PREPARE_FOR_SUBMISSION"]]]]) }
            await expectError { try await Target(appID: "app", versionID: "version", platform: "IOS").verify(Client(transport: transport, token: { "test-token" })) }
        }
    }

    func testNotesRequireExistingReviewContactAndNeverCreateIncompleteRecord() async throws {
        let file = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try Data("Test notes".utf8).write(to: file)
        defer { try? FileManager.default.removeItem(at: file) }
        let args = try Arguments(["set-review-notes", "--app-id", "app", "--version-id", "version", "--platform", "IOS", file.path])
        let transport = MockTransport { req in
            if req.url!.path.hasSuffix("appStoreVersions") {
                return (200, ["data": [["id": "version", "attributes": ["platform": "IOS", "appVersionState": "PREPARE_FOR_SUBMISSION"]]]])
            }
            return (404, [:])
        }
        await expectError { try await Commands.run(args, makeClient: { Client(transport: transport, token: { "test-token" }) }) }
        XCTAssertTrue(transport.requests.allSatisfy { $0.httpMethod == "GET" })
    }

    func testAllFilesAreValidatedBeforeClientCreation() async throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        // Make a tiny synthetic opaque JPEG so the first file passes real ImageIO validation.
        let context = CGContext(data: nil, width: 2, height: 2, bitsPerComponent: 8, bytesPerRow: 8,
                                space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
        let data = NSMutableData()
        let output = CGImageDestinationCreateWithData(data, UTType.jpeg.identifier as CFString, 1, nil)!
        CGImageDestinationAddImage(output, context.makeImage()!, nil)
        XCTAssertTrue(CGImageDestinationFinalize(output))
        let file = directory.appendingPathComponent("valid.jpg")
        try (data as Data).write(to: file)
        let validated = try await MediaFile.prepare([file.path], kind: .screenshot)
        XCTAssertEqual(validated.count, 1)
        let args = try Arguments(["upload-screenshots", "--app-id", "app", "--version-id", "version", "--platform", "IOS",
                                  "--locale", "en-US", "--display-type", "APP_IPHONE_67", file.path, directory.appendingPathComponent("missing.jpg").path])
        await expectError { try await Commands.run(args, makeClient: { XCTFail("Second file must be checked before credential use"); throw ASCError("unexpected") }) }
        await expectError { _ = try await MediaFile.prepare([file.path, file.path], kind: .screenshot) }
        await expectError { _ = try await MediaFile.prepare([directory.path], kind: .screenshot) }
        let corrupt = directory.appendingPathComponent("corrupt.mp4")
        try Data("invalid video".utf8).write(to: corrupt)
        await expectError { _ = try await MediaFile.prepare([corrupt.path], kind: .preview) }
    }

    func testPreviewUsesVideoDeliveryStateAndExplicitOrdering() async throws {
        let server = MediaServer(kind: .preview)
        try await server.upload().run(files: server.files, client: server.client)
        XCTAssertEqual(server.assets, ["new1"])
        XCTAssertTrue(server.transport.requests.contains { $0.url?.query?.contains("videoDeliveryState") == true })
        XCTAssertTrue(server.events.contains("PATCH /v1/appPreviewSets/set/relationships/appPreviews"))
    }

    func testPreviewCapacityAndPendingValidationPreserveOriginals() async {
        let full = MediaServer(oldCount: 3, kind: .preview)
        await expectError { try await full.upload().run(files: full.files, client: full.client) }
        XCTAssertTrue(full.events.allSatisfy { $0.hasPrefix("GET") })
        let pending = MediaServer(kind: .preview); pending.delivery = "PROCESSING"
        await expectError(2) { try await pending.upload().run(files: pending.files, client: pending.client) }
        XCTAssertTrue(pending.assets.contains("old0"))
        XCTAssertFalse(pending.events.contains { $0.hasPrefix("DELETE") })
    }
}
