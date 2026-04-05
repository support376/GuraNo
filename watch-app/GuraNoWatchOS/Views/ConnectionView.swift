import SwiftUI
import WatchConnectivity

struct ConnectionView: View {
    @State private var isConnected = WCSession.default.isReachable

    var body: some View {
        VStack {
            Image(systemName: isConnected ? "checkmark.circle.fill" : "xmark.circle")
                .font(.title)
                .foregroundColor(isConnected ? .green : .red)

            Text(isConnected ? "iPhone 연결됨" : "iPhone 연결 안 됨")
                .font(.caption)
        }
    }
}
