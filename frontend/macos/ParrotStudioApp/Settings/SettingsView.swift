import SwiftUI

struct SettingsView: View {
    @ObservedObject var settings: SettingsStore
    @State private var apiKey = ""
    @State private var status = ""

    private let keychain = KeychainService()

    var body: some View {
        Form {
            Section("OpenAI") {
                SecureField("API key", text: $apiKey)
                HStack {
                    Button("Save Key") { saveKey() }
                    Button("Delete Key", role: .destructive) { deleteKey() }
                    Text(status).foregroundStyle(.secondary)
                }
                TextField("Transcription model", text: $settings.transcriptionModel)
                TextField("Translation model", text: $settings.translationModel)
            }

            Section("Diagnostics") {
                Toggle("Debug mode", isOn: $settings.debugMode)
            }
        }
        .padding()
        .frame(width: 520)
        .task { loadKeyStatus() }
    }

    private func loadKeyStatus() {
        let existing = try? keychain.readAPIKey()
        status = existing?.isEmpty == false ? "Key saved" : "No key saved"
    }

    private func saveKey() {
        do {
            try keychain.saveAPIKey(apiKey)
            status = "Key saved"
        } catch {
            status = "Could not save key"
        }
    }

    private func deleteKey() {
        do {
            try keychain.deleteAPIKey()
            apiKey = ""
            status = "Key deleted"
        } catch {
            status = "Could not delete key"
        }
    }
}
