import SwiftUI

@main
struct GuraNoWatchApp: App {
    @StateObject private var connector = WatchConnector.shared
    @StateObject private var relay = WebSocketRelay()

    var body: some Scene {
        WindowGroup {
            StatusView(connector: connector, relay: relay)
                .onAppear {
                    connector.onHeartRate = { bpm, ts in
                        relay.sendHeartRate(bpm: bpm, timestamp: ts)
                    }
                }
        }
    }
}
