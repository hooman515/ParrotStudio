import SwiftUI

struct SettingsView: View {
    @ObservedObject var settings: SettingsStore
    @State private var apiKey = ""
    @State private var status = ""

    private let keychain = KeychainService()

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            settingsSection("OpenAI") {
                SettingsRow("API key") {
                    SecureField("OpenAI API key", text: $apiKey)
                        .textFieldStyle(.roundedBorder)
                }

                HStack(spacing: 8) {
                    Spacer()
                        .frame(width: SettingsLayout.labelWidth)
                    Button("Save Key") { saveKey() }
                    Button("Delete Key", role: .destructive) { deleteKey() }
                    Text(status)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                    Spacer(minLength: 0)
                }

                SettingsRow("Transcription model") {
                    TextField("Transcription model", text: $settings.transcriptionModel)
                        .textFieldStyle(.roundedBorder)
                }

                SettingsRow("Translation model") {
                    TextField("Translation model", text: $settings.translationModel)
                        .textFieldStyle(.roundedBorder)
                }
            }

            settingsSection("Subtitles") {
                SettingsRow("Timing offset") {
                    HStack(spacing: 10) {
                        Stepper(value: $settings.subtitleOffsetSeconds, in: -10...10, step: 0.1) {
                            Text(settings.subtitleOffsetSeconds, format: .number.precision(.fractionLength(1)).sign(strategy: .always()))
                                .monospacedDigit()
                        }
                        Text("seconds")
                            .foregroundStyle(.secondary)
                    }
                }
            }

            settingsSection("Diagnostics") {
                SettingsRow("Debug mode") {
                    Toggle("", isOn: $settings.debugMode)
                        .labelsHidden()
                }
            }
        }
        .padding()
        .frame(width: 620, alignment: .leading)
        .task { loadKeyStatus() }
    }

    private func settingsSection<Content: View>(
        _ title: String,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.headline)
            VStack(alignment: .leading, spacing: 8) {
                content()
            }
        }
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

private struct SettingsRow<Content: View>: View {
    let title: String
    let content: Content

    init(_ title: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.content = content()
    }

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 12) {
            Text(title)
                .foregroundStyle(.secondary)
                .frame(width: SettingsLayout.labelWidth, alignment: .trailing)
            content
                .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}

private enum SettingsLayout {
    static let labelWidth: CGFloat = 150
}
