import Foundation

class WebSocketRelay: ObservableObject {
    private var webSocket: URLSessionWebSocketTask?
    @Published var isConnected = false

    func connect(serverURL: String, sessionId: String) {
        guard let url = URL(string: "\(serverURL)/ws/\(sessionId)") else { return }
        let session = URLSession(configuration: .default)
        webSocket = session.webSocketTask(with: url)
        webSocket?.resume()
        isConnected = true
        receiveMessage()
    }

    func sendHeartRate(bpm: Double, timestamp: TimeInterval) {
        let json: [String: Any] = [
            "type": "heart_rate",
            "bpm": bpm,
            "source": "apple_watch",
            "ts": timestamp,
        ]

        guard let data = try? JSONSerialization.data(withJSONObject: json),
              let string = String(data: data, encoding: .utf8) else { return }

        webSocket?.send(.string(string)) { error in
            if let error = error {
                print("WebSocket send error: \(error)")
            }
        }
    }

    private func receiveMessage() {
        webSocket?.receive { [weak self] result in
            switch result {
            case .success:
                self?.receiveMessage()
            case .failure(let error):
                print("WebSocket receive error: \(error)")
                self?.isConnected = false
            }
        }
    }

    func disconnect() {
        webSocket?.cancel(with: .normalClosure, reason: nil)
        isConnected = false
    }
}
