import Foundation
import WatchConnectivity

class WatchConnector: NSObject, ObservableObject, WCSessionDelegate {
    static let shared = WatchConnector()
    @Published var latestHR: Double = 0
    var onHeartRate: ((Double, TimeInterval) -> Void)?

    override init() {
        super.init()
        if WCSession.isSupported() {
            WCSession.default.delegate = self
            WCSession.default.activate()
        }
    }

    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {}
    func sessionDidBecomeInactive(_ session: WCSession) {}
    func sessionDidDeactivate(_ session: WCSession) {
        WCSession.default.activate()
    }

    func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        guard let type = message["type"] as? String, type == "heart_rate",
              let bpm = message["bpm"] as? Double,
              let ts = message["timestamp"] as? TimeInterval else { return }

        DispatchQueue.main.async {
            self.latestHR = bpm
            self.onHeartRate?(bpm, ts)
        }
    }
}
