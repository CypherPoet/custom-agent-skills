import AVFoundation
import CryptoKit
import Foundation
import ImageIO
import UniformTypeIdentifiers

enum MediaKind {
    case screenshot, preview
    var assets: String { self == .screenshot ? "appScreenshots" : "appPreviews" }
    var sets: String { self == .screenshot ? "appScreenshotSets" : "appPreviewSets" }
    var relationship: String { self == .screenshot ? "appScreenshotSet" : "appPreviewSet" }
    var displayAttribute: String { self == .screenshot ? "screenshotDisplayType" : "previewType" }
    var stateAttribute: String { self == .screenshot ? "assetDeliveryState" : "videoDeliveryState" }
    var maximum: Int { self == .screenshot ? 10 : 3 }
}

struct MediaFile {
    let name: String
    let bytes: Data

    static func prepare(_ paths: [String], kind: MediaKind) async throws -> [MediaFile] {
        guard !paths.isEmpty, paths.count <= kind.maximum else { throw ASCError("Provide 1–\(kind.maximum) media files.") }
        var names = Set<String>()
        var files: [MediaFile] = []
        for path in paths {
            let url = URL(fileURLWithPath: path)
            guard names.insert(url.lastPathComponent).inserted else { throw ASCError("Media filenames must be unique.") }
            let info = try url.resourceValues(forKeys: [.isRegularFileKey, .fileSizeKey])
            guard info.isRegularFile == true, let size = info.fileSize, size > 0, size <= 500 * 1024 * 1024,
                  let bytes = try? Data(contentsOf: url), bytes.count == size else {
                throw ASCError("Every media input must be a readable, nonempty regular file of at most 500 MiB.")
            }
            if kind == .screenshot {
                guard let source = CGImageSourceCreateWithData(bytes as CFData, nil),
                      let uti = CGImageSourceGetType(source) as String?,
                      [UTType.png.identifier, UTType.jpeg.identifier].contains(uti),
                      let image = CGImageSourceCreateImageAtIndex(source, 0, nil), image.width > 0, image.height > 0,
                      [.none, .noneSkipFirst, .noneSkipLast].contains(image.alphaInfo) else {
                    throw ASCError("Screenshots must decode as PNG/JPEG without an alpha channel.")
                }
            } else {
                guard ["mp4", "mov", "m4v"].contains(url.pathExtension.lowercased()) else { throw ASCError("Previews must use MP4, MOV, or M4V containers.") }
                let asset = AVURLAsset(url: url)
                let duration = try await asset.load(.duration).seconds
                let video = try await asset.loadTracks(withMediaType: .video)
                let audio = try await asset.loadTracks(withMediaType: .audio)
                guard duration.isFinite, (15...30).contains(duration), !video.isEmpty, !audio.isEmpty else {
                    throw ASCError("Previews need 15–30 seconds of video and an audio track.")
                }
                var stereo = false
                for track in audio {
                    for format in try await track.load(.formatDescriptions) {
                        if let stream = CMAudioFormatDescriptionGetStreamBasicDescription(format), stream.pointee.mChannelsPerFrame == 2 { stereo = true }
                    }
                }
                guard stereo else { throw ASCError("Previews need a stereo audio track, even when silent.") }
                guard (try? Data(contentsOf: url)) == bytes else { throw ASCError("Preview changed during validation; retry with stable input files.") }
            }
            files.append(MediaFile(name: url.lastPathComponent, bytes: bytes))
        }
        return files
    }
}

struct MediaUpload {
    let target: Target
    let locale: String
    let displayType: String
    let kind: MediaKind
    let replace: Bool
    let polling: Polling
    var report: (String) -> Void = { print($0) }

    func run(files: [MediaFile], client: Client) async throws {
        guard !files.isEmpty, files.count <= kind.maximum, files.allSatisfy({ !$0.bytes.isEmpty }),
              Set(files.map(\.name)).count == files.count,
              displayType.range(of: "^[A-Z][A-Z0-9_]*$", options: .regularExpression) != nil else {
            throw ASCError("Invalid media inputs or display type.")
        }
        try await target.verify(client)
        let locID = try await target.localization(locale, client: client)
        let sets = try await client.list("/v1/appStoreVersionLocalizations/\(locID)/\(kind.sets)?limit=200")
        let matches = sets.filter { ($0["attributes"] as? JSON)?[kind.displayAttribute] as? String == displayType }
        guard matches.count <= 1 else { throw ASCError("Ambiguous media set; inspect App Store Connect.") }
        var setID = try matches.first.map { try identifier(requiredID($0)) }
        let oldIDs: [String]
        if let setID { oldIDs = try await assetIDs(setID, client: client) } else { oldIDs = [] }
        guard oldIDs.isEmpty || replace else { throw ASCError("The target set contains media. Use --replace only after reviewing this exact target.") }
        guard oldIDs.count + files.count <= kind.maximum else {
            throw ASCError("Safe replacement needs room for old and new assets (limit \(kind.maximum)). Existing media is unchanged; use the console for a full set.")
        }
        if setID == nil {
            let created = try await client.request("POST", "/v1/\(kind.sets)", body: ["data": [
                "type": kind.sets, "attributes": [kind.displayAttribute: displayType],
                "relationships": ["appStoreVersionLocalization": ["data": ["type": "appStoreVersionLocalizations", "id": locID]]],
            ]])
            setID = try identifier(requiredID(resource(created)))
        }
        guard let setID else { throw ASCError("Missing target set ID.") }
        report("Target: app \(target.appID), version \(target.versionID), \(target.platform), \(locale), \(displayType); set \(setID).")
        var staged: [String] = []
        do {
            for file in files {
                let reserved = try resource(await client.request("POST", "/v1/\(kind.assets)", body: ["data": [
                    "type": kind.assets, "attributes": ["fileName": file.name, "fileSize": file.bytes.count],
                    "relationships": [kind.relationship: ["data": ["type": kind.sets, "id": setID]]],
                ]]))
                let assetID = try identifier(requiredID(reserved))
                staged.append(assetID)
                report("Reserved \(kind.assets)/\(assetID).")
                guard let operations = (reserved["attributes"] as? JSON)?["uploadOperations"] as? [JSON] else {
                    throw ASCError("Missing upload operations.")
                }
                try await client.upload(operations, bytes: file.bytes)
                let checksum = Insecure.MD5.hash(data: file.bytes).map { String(format: "%02x", $0) }.joined()
                _ = try await client.request("PATCH", "/v1/\(kind.assets)/\(assetID)", body: ["data": [
                    "type": kind.assets, "id": assetID, "attributes": ["uploaded": true, "sourceFileChecksum": checksum],
                ]])
                try await polling.wait(label: "\(kind.assets)/\(assetID)", success: ["COMPLETE"], failure: ["FAILED"],
                                       pending: ["AWAITING_UPLOAD", "UPLOAD_COMPLETE", "PROCESSING"]) {
                    let row = try resource(await client.request("GET", "/v1/\(kind.assets)/\(assetID)?fields[\(kind.assets)]=\(kind.stateAttribute)"))
                    guard let state = ((row["attributes"] as? JSON)?[kind.stateAttribute] as? JSON)?["state"] as? String else {
                        throw ASCError("Missing delivery state; inspect the current API schema.")
                    }
                    return state
                }
            }
            // Detect concurrent edits before ordering or deleting anything from the original set.
            try await target.verify(client)
            let current = try await assetIDs(setID, client: client)
            guard Set(current) == Set(oldIDs + staged), current.count == oldIDs.count + staged.count else {
                throw ASCError("Media set changed concurrently; original assets were not deleted.")
            }
            let ordered = staged + oldIDs
            _ = try await client.request("PATCH", "/v1/\(kind.sets)/\(setID)/relationships/\(kind.assets)", body: [
                "data": ordered.map { ["type": kind.assets, "id": $0] },
            ])
            // Every new asset is validated at this point. Never delete the set itself.
            for oldID in oldIDs { _ = try await client.request("DELETE", "/v1/\(kind.assets)/\(oldID)") }
            guard try await assetIDs(setID, client: client) == staged else {
                throw ASCError("Final media order differs from the requested order; inspect the set before retrying.")
            }
            report("Complete: \(staged.count) validated assets in the requested order.")
        } catch {
            report("Stopped. Inspect set \(setID) and reserved IDs [\(staged.joined(separator: ", "))] before retrying. No automatic cleanup or rollback was attempted.")
            throw error
        }
    }

    private func assetIDs(_ setID: String, client: Client) async throws -> [String] {
        try await client.list("/v1/\(kind.sets)/\(setID)/\(kind.assets)?limit=200").map { try identifier(requiredID($0)) }
    }
}

func requiredID(_ row: JSON) throws -> String {
    guard let id = row["id"] as? String else { throw ASCError("Missing resource ID.") }
    return id
}
