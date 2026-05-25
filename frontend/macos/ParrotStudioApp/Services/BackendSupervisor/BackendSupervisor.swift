import Combine
import Foundation

@MainActor
final class BackendSupervisor: ObservableObject {
    @Published var ready: BackendReady?
    @Published var lastError: String?
    @Published var restartCount = 0

    private var process: Process?
    private var restartDates: [Date] = []
    private var shouldRestart = false
    private let decoder = JSONDecoder()

    func start() async {
        if process?.isRunning == true { return }
        shouldRestart = true
        restartCount = 0
        restartDates.removeAll()
        lastError = nil
        await launch()
    }

    func stop() {
        shouldRestart = false
        ready = nil
        process?.terminate()
        process = nil
    }

    private func launch() async {
        let process = Process()
        let launchDate = Date()
        let stdout = Pipe()
        let stderr = Pipe()
        process.standardOutput = stdout
        process.standardError = stderr

        let python = resolvePython()
        process.executableURL = python.executable
        process.arguments = python.arguments
        process.environment = python.environment

        process.terminationHandler = { [weak self] _ in
            Task { @MainActor in
                guard let self else { return }
                self.ready = nil
                if self.shouldRestart {
                    let uptime = Date().timeIntervalSince(launchDate)
                    if uptime < 2 {
                        let stderrData = stderr.fileHandleForReading.availableData
                        let stderrText = String(data: stderrData, encoding: .utf8)?
                            .split(separator: "\n")
                            .suffix(3)
                            .joined(separator: " ")
                        if let stderrText, !stderrText.isEmpty {
                            self.lastError = "Backend exited early: \(stderrText)"
                        }
                    }
                    await self.restartIfAllowed()
                }
            }
        }

        do {
            try process.run()
            self.process = process
            try await readHandshake(from: stdout.fileHandleForReading)
        } catch {
            let stderrData = stderr.fileHandleForReading.availableData
            let stderrText = String(data: stderrData, encoding: .utf8)?
                .split(separator: "\n")
                .suffix(3)
                .joined(separator: " ")
            if let stderrText, !stderrText.isEmpty {
                lastError = "Backend failed to start: \(stderrText)"
            } else {
                lastError = "Backend failed to start: \(error.localizedDescription)"
            }
            if shouldRestart {
                await restartIfAllowed()
            }
        }
    }

    private func readHandshake(from handle: FileHandle) async throws {
        let data = handle.availableData
        guard !data.isEmpty,
              let line = String(data: data, encoding: .utf8)?.split(separator: "\n").first,
              let lineData = String(line).data(using: .utf8) else {
            throw CocoaError(.fileReadCorruptFile)
        }
        ready = try decoder.decode(BackendReady.self, from: lineData)
    }

    private func restartIfAllowed() async {
        let now = Date()
        restartDates = restartDates.filter { now.timeIntervalSince($0) < 60 }
        guard restartDates.count < 3 else {
            lastError = "Parrot Studio's translation engine crashed repeatedly."
            shouldRestart = false
            return
        }
        restartDates.append(now)
        restartCount += 1
        try? await Task.sleep(for: .seconds(1))
        await launch()
    }

    private func resolvePython() -> (executable: URL, arguments: [String], environment: [String: String]) {
        var environment = ProcessInfo.processInfo.environment

        if let override = environment["PARROT_BACKEND_PYTHON"] {
            environment["PYTHONPATH"] = environment["PARROT_BACKEND_ROOT"] ?? "backend"
            if let vendor = environment["PARROT_BACKEND_VENDOR"] {
                environment["PYTHONPATH"] = "\(environment["PYTHONPATH"] ?? ""):\(vendor)"
            }
            return (URL(fileURLWithPath: override), ["-m", "parrot_studio.main"], environment)
        }

        if let resources = Bundle.main.resourceURL {
            let bundled = resources.appending(path: "python/bin/python")
            let backend = resources.appending(path: "backend")
            let vendor = resources.appending(path: "python_lib")
            if FileManager.default.isExecutableFile(atPath: bundled.path) {
                environment["PYTHONPATH"] = pythonPath(backend: backend, vendor: vendor)
                return (bundled, ["-m", "parrot_studio.main"], environment)
            }
            if FileManager.default.fileExists(atPath: backend.path) {
                environment["PYTHONPATH"] = pythonPath(backend: backend, vendor: vendor)
                return (resolveDeveloperPython(), ["-m", "parrot_studio.main"], environment)
            }
        }

        environment["PYTHONPATH"] = "backend"
        return (resolveDeveloperPython(), ["-m", "parrot_studio.main"], environment)
    }

    private func resolveDeveloperPython() -> URL {
        let candidates = [
            "/opt/homebrew/bin/python3",
            "/usr/local/bin/python3",
            "/usr/bin/python3"
        ]
        for candidate in candidates where FileManager.default.isExecutableFile(atPath: candidate) {
            return URL(fileURLWithPath: candidate)
        }
        return URL(fileURLWithPath: "/usr/bin/python3")
    }

    private func pythonPath(backend: URL, vendor: URL) -> String {
        if FileManager.default.fileExists(atPath: vendor.path) {
            return "\(backend.path):\(vendor.path)"
        }
        return backend.path
    }
}
