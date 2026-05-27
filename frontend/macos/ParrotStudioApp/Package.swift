// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "ParrotStudioApp",
    platforms: [.macOS("26.0")],
    products: [
        .executable(name: "ParrotStudio", targets: ["ParrotStudio"])
    ],
    targets: [
        .executableTarget(
            name: "ParrotStudio",
            path: ".",
            exclude: ["Package.swift"],
            sources: [
                "App",
                "Views",
                "Models",
                "Services",
                "IPC",
                "Settings",
                "Support"
            ],
            resources: [
                .copy("Resources")
            ],
            linkerSettings: [
                .linkedFramework("AppKit"),
                .linkedFramework("Security"),
                .linkedFramework("Network")
            ]
        )
    ]
)
