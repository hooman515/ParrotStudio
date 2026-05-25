import AppKit
import SwiftUI

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }
}

@main
struct ParrotStudioApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @StateObject private var settings = SettingsStore()
    @StateObject private var backend = BackendSupervisor()
    @StateObject private var control = ControlClient()

    var body: some Scene {
        WindowGroup("Parrot Studio") {
            ContentView(
                settings: settings,
                backend: backend,
                control: control
            )
        }

        Settings {
            SettingsView(settings: settings)
        }
    }
}
