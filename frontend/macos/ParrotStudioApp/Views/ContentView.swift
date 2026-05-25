import AppKit
import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @ObservedObject var settings: SettingsStore
    @ObservedObject var backend: BackendSupervisor
    @ObservedObject var control: ControlClient

    @State private var inputURL: URL?
    @State private var outputURL: URL?
    @State private var sessionState: SessionState = .idle
    @State private var statusMessage = "Choose a video to subtitle"
    @State private var progress = 0.0
    @State private var progressStage = ""
    @State private var lastError: String?
    @State private var completedOutput: String?
    @State private var completedSRT: String?
    @State private var artifactDir: String?

    private let keychain = KeychainService()

    var body: some View {
        VStack(alignment: .leading, spacing: 22) {
            header
            fileSection
            settingsSection
            progressSection
            resultSection
            Spacer()
        }
        .padding(28)
        .frame(minWidth: 860, minHeight: 560)
        .task {
            control.onEvent = handleEvent
        }
        .onReceive(NotificationCenter.default.publisher(for: NSApplication.willTerminateNotification)) { _ in
            shutdownLocalServices()
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Parrot Studio")
                .font(.largeTitle.bold())
            Text(statusMessage)
                .foregroundStyle(sessionState == .error ? .red : .secondary)
        }
    }

    private var fileSection: some View {
        Form {
            LabeledContent("Input video") {
                HStack {
                    Text(inputURL?.path ?? "No video selected")
                        .lineLimit(1)
                        .foregroundStyle(inputURL == nil ? .secondary : .primary)
                    Button("Choose") { chooseInputVideo() }
                }
            }
            LabeledContent("Output video") {
                HStack {
                    Text(outputURL?.path ?? "Choose an MP4 output path")
                        .lineLimit(1)
                        .foregroundStyle(outputURL == nil ? .secondary : .primary)
                    Button("Save As") { chooseOutputVideo() }
                }
            }
        }
        .formStyle(.grouped)
    }

    private var settingsSection: some View {
        Form {
            TextField("Transcription model", text: $settings.transcriptionModel)
            TextField("Translation model", text: $settings.translationModel)
            Toggle("Debug mode", isOn: $settings.debugMode)
            HStack {
                Button {
                    Task { await startJob() }
                } label: {
                    Label("Process Video", systemImage: "play.fill")
                }
                .disabled(inputURL == nil || outputURL == nil || sessionState == .processing || sessionState == .starting)

                Button {
                    Task { await cancelJob() }
                } label: {
                    Label("Cancel", systemImage: "stop.fill")
                }
                .disabled(sessionState != .processing && sessionState != .starting)
            }
        }
        .formStyle(.grouped)
    }

    private var progressSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            ProgressView(value: progress)
            HStack {
                Text(progressStage.isEmpty ? "Idle" : progressStage.capitalized)
                Spacer()
                Text("\(Int(progress * 100))%")
                    .foregroundStyle(.secondary)
            }
            if let lastError {
                Text(lastError)
                    .foregroundStyle(.red)
            }
        }
        .padding(14)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 8))
    }

    @ViewBuilder
    private var resultSection: some View {
        if completedOutput != nil || completedSRT != nil || artifactDir != nil {
            Form {
                if let completedOutput {
                    LabeledContent("Video") { Text(completedOutput).lineLimit(1) }
                }
                if let completedSRT {
                    LabeledContent("SRT") { Text(completedSRT).lineLimit(1) }
                }
                if let artifactDir {
                    LabeledContent("Artifacts") { Text(artifactDir).lineLimit(1) }
                }
            }
            .formStyle(.grouped)
        }
    }

    private func chooseInputVideo() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.title = "Choose a video"
        if panel.runModal() == .OK, let url = panel.url {
            inputURL = url
            if outputURL == nil {
                outputURL = url.deletingPathExtension().appendingPathExtension("subtitled.mp4")
            }
        }
    }

    private func chooseOutputVideo() {
        let panel = NSSavePanel()
        panel.title = "Choose output video"
        panel.allowedContentTypes = [.mpeg4Movie]
        panel.nameFieldStringValue = inputURL?.deletingPathExtension().lastPathComponent.appending("-subtitled.mp4") ?? "subtitled.mp4"
        if panel.runModal() == .OK {
            outputURL = panel.url
        }
    }

    private func startJob() async {
        guard let inputURL, let outputURL else { return }
        let apiKey = (try? keychain.readAPIKey()) ?? ""
        if apiKey.isEmpty {
            lastError = "Add your OpenAI API key in Settings before processing video."
            sessionState = .error
            return
        }

        lastError = nil
        completedOutput = nil
        completedSRT = nil
        artifactDir = nil
        progress = 0
        progressStage = "starting"

        await backend.start()
        guard let ready = backend.ready else {
            lastError = backend.lastError ?? "Backend did not become ready."
            sessionState = .error
            return
        }
        control.connect(port: ready.controlPort)

        let request = StartVideoJobRequest(
            inputPath: inputURL.path,
            outputPath: outputURL.path,
            transcriptionModel: settings.transcriptionModel,
            translationModel: settings.translationModel,
            workDir: nil,
            debug: settings.debugMode,
            openaiAPIKey: apiKey
        )
        do {
            try await control.send(request)
        } catch {
            lastError = "Could not send job command: \(error.localizedDescription)"
            sessionState = .error
        }
    }

    private func cancelJob() async {
        try? await control.send(CancelJobRequest())
        shutdownLocalServices()
        sessionState = .idle
        statusMessage = "Cancelled"
    }

    private func shutdownLocalServices() {
        control.disconnect()
        backend.stop()
    }

    private func handleEvent(_ event: ControlEvent) {
        switch event {
        case .status(let payload):
            sessionState = payload.state
            statusMessage = payload.message
        case .jobProgress(let payload):
            progress = payload.progress
            progressStage = payload.stage
            statusMessage = payload.message
        case .jobComplete(let payload):
            completedOutput = payload.outputVideoPath
            completedSRT = payload.subtitlePath
            artifactDir = payload.artifactDir
            progress = 1
            sessionState = .complete
            statusMessage = "Export complete"
        case .error(let payload):
            sessionState = .error
            lastError = payload.message
            statusMessage = payload.message
        case .metric:
            break
        }
    }
}
