import Combine
import Foundation

@MainActor
final class SettingsStore: ObservableObject {
    @Published var transcriptionModel: String {
        didSet { defaults.set(transcriptionModel, forKey: Keys.transcriptionModel) }
    }

    @Published var translationModel: String {
        didSet { defaults.set(translationModel, forKey: Keys.translationModel) }
    }

    @Published var debugMode: Bool {
        didSet { defaults.set(debugMode, forKey: Keys.debugMode) }
    }

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        transcriptionModel = defaults.string(forKey: Keys.transcriptionModel) ?? "whisper-1"
        translationModel = defaults.string(forKey: Keys.translationModel) ?? "gpt-4o-2024-11-20"
        debugMode = defaults.bool(forKey: Keys.debugMode)
    }

    enum Keys {
        static let transcriptionModel = "transcriptionModel"
        static let translationModel = "translationModel"
        static let debugMode = "debugMode"
    }
}
