import Foundation
import WatchConnectivity

class WatchSender: NSObject, WCSessionDelegate {
    static let shared = WatchSender()

    override init() {
        super.init()
        if WCSession.isSupported() {
            WCSession.default.delegate = self
            WCSession.default.activate()
        }
    }

    func sendHeartRate(bpm: Double) {
        guard WCSession.default.isReachable else { return }

        let message: [String: Any] = [
            "type": "heart_rate",
            "bpm": bpm,
            "timestamp": Date().timeIntervalSince1970,
        ]

        WCSession.default.sendMessage(message, replyHandler: nil) { error in
            print("Failed to send HR: \(error.localizedDescription)")
        }
    }

    // MARK: - WCSessionDelegate

    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        print("Watch WCSession activated: \(activationState.rawValue)")
    }
}
