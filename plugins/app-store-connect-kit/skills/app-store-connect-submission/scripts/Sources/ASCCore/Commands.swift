import Foundation

struct Arguments {
    let command: String
    var options: [String: String] = [:]
    var positional: [String] = []
    var replace = false
    init(_ arguments: [String]) throws {
        guard let command = arguments.first else { throw ASCError(Commands.usage) }
        self.command = command
        let common: Set<String> = ["--env-file", "--attempts", "--interval"]
        let target: Set<String> = ["--app-id", "--version-id", "--platform"]
        let allowed: Set<String>
        switch command {
        case "get": allowed = ["--env-file"]
        case "build-status": allowed = common.union(["--app-id", "--build-id", "--platform"])
        case "upload-screenshots", "upload-previews": allowed = common.union(target).union(["--locale", "--display-type"])
        case "set-review-notes": allowed = target.union(["--env-file"])
        default: throw ASCError(Commands.usage)
        }
        var index = 1
        while index < arguments.count {
            let arg = arguments[index]
            index += 1
            if arg == "--" { positional += arguments[index...]; break }
            if arg == "--replace", command.hasPrefix("upload-"), !replace { replace = true; continue }
            if arg.hasPrefix("--") {
                guard allowed.contains(arg), options[arg] == nil, index < arguments.count,
                      !arguments[index].hasPrefix("--") else { throw ASCError("Unknown, duplicate, or incomplete option: \(arg).") }
                options[arg] = arguments[index]
                index += 1
            } else { positional.append(arg) }
        }
    }
    func required(_ flag: String) throws -> String {
        guard let value = options[flag], !value.isEmpty else { throw ASCError("Explicit \(flag) is required.") }
        return value
    }
    func target() throws -> Target {
        Target(appID: try identifier(required("--app-id")), versionID: try identifier(required("--version-id")), platform: try platform())
    }
    func platform() throws -> String {
        let value = try required("--platform")
        guard ["IOS", "MAC_OS", "TV_OS", "VISION_OS"].contains(value) else { throw ASCError("Unsupported platform; use IOS, MAC_OS, TV_OS, or VISION_OS.") }
        return value
    }
    func polling() throws -> Polling {
        guard let attempts = Int(options["--attempts"] ?? "20"), (1...360).contains(attempts),
              let interval = Double(options["--interval"] ?? "3"), interval.isFinite, (0...60).contains(interval) else {
            throw ASCError("Use 1–360 attempts and an interval of 0–60 seconds.")
        }
        return Polling(attempts: attempts, interval: interval)
    }
}

public enum Commands {
    public static let usage = """
    asc get <API-path> [--env-file PATH]
    asc build-status --app-id ID --build-id ID --platform IOS [--attempts 20 --interval 3]
    asc upload-screenshots|upload-previews --app-id ID --version-id ID --platform IOS
        --locale en-US --display-type TYPE [--replace] [--attempts 20 --interval 3] FILE...
    asc set-review-notes --app-id ID --version-id ID --platform IOS NOTES_FILE
    All commands accept --env-file PATH. Use --help without credentials.
    Exit 0: confirmed success; 1: error/failed/unknown state; 2: processing still pending.
    """

    public static func main(arguments: [String] = Array(CommandLine.arguments.dropFirst())) async -> Int32 {
        if arguments.contains("--help") || arguments == ["help"] { print(usage); return 0 }
        do {
            let args = try Arguments(arguments)
            try await run(args, makeClient: {
                let config = try DotEnv.load(path: args.options["--env-file"] ?? ".env", environment: ProcessInfo.processInfo.environment,
                                             required: args.options["--env-file"] != nil)
                let credentials = try Credentials(config: config)
                return Client(transport: SessionTransport(), token: { try credentials.token() })
            })
            return 0
        } catch let error as ASCError {
            FileHandle.standardError.write(Data((error.description + "\n").utf8))
            return error.exitCode
        } catch {
            // Foundation/AVFoundation errors may contain private file paths or signed URLs.
            FileHandle.standardError.write(Data("Operation failed; inspect inputs and remote state before retrying.\n".utf8))
            return 1
        }
    }

    static func run(_ args: Arguments, makeClient: () throws -> Client, report: @escaping (String) -> Void = { print($0) }) async throws {
        switch args.command {
        case "get":
            guard args.positional.count == 1 else { throw ASCError("Provide one API path.") }
            _ = try Client.apiURL(args.positional[0])
            let result = try await makeClient().request("GET", args.positional[0])
            let bytes = try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
            report(String(decoding: bytes, as: UTF8.self))
        case "upload-screenshots", "upload-previews":
            let target = try args.target()
            let locale = try args.required("--locale")
            let display = try args.required("--display-type")
            let polling = try args.polling()
            let kind: MediaKind = args.command == "upload-screenshots" ? .screenshot : .preview
            let files = try await MediaFile.prepare(args.positional, kind: kind)
            try await MediaUpload(target: target, locale: locale, displayType: display, kind: kind, replace: args.replace,
                                  polling: polling, report: report).run(files: files, client: makeClient())
        case "set-review-notes":
            let target = try args.target()
            guard args.positional.count == 1, let notes = try? String(contentsOfFile: args.positional[0], encoding: .utf8),
                  !notes.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                throw ASCError("Provide a readable, nonempty UTF-8 notes file.")
            }
            let client = try makeClient()
            try await target.verify(client)
            let detail = try await client.request("GET", "/v1/appStoreVersions/\(target.versionID)/appStoreReviewDetail", allow404: true)
            guard !detail.isEmpty else { throw ASCError("Set the review contact in App Store Connect first; no incomplete record was created.") }
            let id = try identifier(requiredID(resource(detail)))
            _ = try await client.request("PATCH", "/v1/appStoreReviewDetails/\(id)", body: ["data": [
                "type": "appStoreReviewDetails", "id": id, "attributes": ["notes": notes],
            ]])
            report("Updated review notes for app \(target.appID), version \(target.versionID), \(target.platform).")
        case "build-status":
            guard args.positional.isEmpty else { throw ASCError("build-status takes no positional arguments.") }
            let appID = try identifier(args.required("--app-id"))
            let buildID = try identifier(args.required("--build-id"))
            let platform = try args.platform()
            let polling = try args.polling()
            let client = try makeClient()
            try await polling.wait(label: "Build \(buildID)", success: ["VALID"], failure: ["FAILED", "INVALID"], pending: ["PROCESSING"]) {
                let response = try await client.request("GET", "/v1/builds/\(buildID)?include=app,preReleaseVersion")
                let row = try resource(response)
                let relations = row["relationships"] as? JSON ?? [:]
                let app = (relations["app"] as? JSON)?["data"] as? JSON
                let prerelease = (relations["preReleaseVersion"] as? JSON)?["data"] as? JSON
                let included = response["included"] as? [JSON] ?? []
                let versions = included.filter { $0["type"] as? String == "preReleaseVersions" && $0["id"] as? String == prerelease?["id"] as? String }
                guard row["id"] as? String == buildID, app?["id"] as? String == appID,
                      versions.count == 1, (versions[0]["attributes"] as? JSON)?["platform"] as? String == platform,
                      let state = (row["attributes"] as? JSON)?["processingState"] as? String else {
                    throw ASCError("Build does not match the explicit app/platform or is missing processing metadata.")
                }
                return state
            }
            report("Build \(buildID): VALID.")
        default: throw ASCError(usage)
        }
    }
}
