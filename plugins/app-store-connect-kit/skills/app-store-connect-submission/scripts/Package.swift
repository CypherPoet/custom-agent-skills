// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "ASCSubmission",
    platforms: [.macOS(.v13)],
    products: [.executable(name: "asc", targets: ["asc"])],
    targets: [
        .target(name: "ASCCore"),
        .executableTarget(name: "asc", dependencies: ["ASCCore"]),
        .testTarget(name: "ASCCoreTests", dependencies: ["ASCCore"]),
    ]
)
