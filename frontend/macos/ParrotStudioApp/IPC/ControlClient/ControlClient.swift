import Foundation

@MainActor
final class ControlClient: ObservableObject {
    @Published var isConnected = false

    var onEvent: ((ControlEvent) -> Void)?

    private var task: URLSessionWebSocketTask?
    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()

    func connect(port: Int) {
        disconnect()
        let url = URL(string: "ws://127.0.0.1:\(port)")!
        let task = URLSession.shared.webSocketTask(with: url)
        self.task = task
        task.resume()
        isConnected = true
        receive()
    }

    func send<T: Encodable>(_ payload: T) async throws {
        let data = try encoder.encode(payload)
        guard let text = String(data: data, encoding: .utf8) else { return }
        try await task?.send(.string(text))
    }

    func disconnect() {
        task?.cancel(with: .goingAway, reason: nil)
        task = nil
        isConnected = false
    }

    private func receive() {
        task?.receive { [weak self] result in
            Task { @MainActor in
                guard let self else { return }
                switch result {
                case .success(.string(let text)):
                    if let data = text.data(using: .utf8),
                       let event = try? self.decoder.decode(ControlEvent.self, from: data) {
                        self.onEvent?(event)
                    }
                    self.receive()
                case .success(.data(let data)):
                    if let event = try? self.decoder.decode(ControlEvent.self, from: data) {
                        self.onEvent?(event)
                    }
                    self.receive()
                case .failure:
                    self.isConnected = false
                @unknown default:
                    self.receive()
                }
            }
        }
    }
}
