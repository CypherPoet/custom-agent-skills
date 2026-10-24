// Compatibility launcher. Keep the whole scripts directory together.
import Foundation

let directory = URL(fileURLWithPath: #filePath).deletingLastPathComponent().path
var environment = ProcessInfo.processInfo.environment
let buildDirectory = environment["ASC_BUILD_DIR"] ?? FileManager.default.temporaryDirectory.appendingPathComponent("asc-submission-build").path
guard buildDirectory.hasPrefix("/") else {
    FileHandle.standardError.write(Data("ASC_BUILD_DIR must be an absolute path.\n".utf8))
    exit(1)
}
environment["CLANG_MODULE_CACHE_PATH"] = environment["CLANG_MODULE_CACHE_PATH"] ?? buildDirectory + "/modules"
environment["SWIFTPM_MODULECACHE_OVERRIDE"] = environment["SWIFTPM_MODULECACHE_OVERRIDE"] ?? buildDirectory + "/modules"
let process = Process()
process.environment = environment
process.executableURL = URL(fileURLWithPath: "/usr/bin/xcrun")
process.arguments = ["swift", "run", "--package-path", directory, "--scratch-path", buildDirectory, "--cache-path", buildDirectory + "/cache", "asc", "upload-screenshots"] + Array(CommandLine.arguments.dropFirst())
process.standardInput = FileHandle.standardInput
process.standardOutput = FileHandle.standardOutput
process.standardError = FileHandle.standardError
do {
    try process.run()
    process.waitUntilExit()
    exit(process.terminationReason == .exit ? process.terminationStatus : 1)
} catch {
    FileHandle.standardError.write(Data("Could not launch the bundled ASC tool.\n".utf8))
    exit(1)
}
