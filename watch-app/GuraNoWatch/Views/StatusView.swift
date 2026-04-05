import SwiftUI

struct StatusView: View {
    @ObservedObject var connector: WatchConnector
    @ObservedObject var relay: WebSocketRelay
    @State private var serverURL = "ws://192.168.1.100:8000"
    @State private var sessionId = ""

    var body: some View {
        NavigationView {
            VStack(spacing: 16) {
                Text("GuraNo")
                    .font(.largeTitle)
                    .bold()
                    .foregroundColor(.blue)

                // HR Display
                VStack {
                    Text("\(Int(connector.latestHR))")
                        .font(.system(size: 48, weight: .bold))
                        .foregroundColor(.red)
                    Text("BPM")
                        .foregroundColor(.gray)
                }

                // Connection Status
                HStack {
                    Circle()
                        .fill(relay.isConnected ? Color.green : Color.red)
                        .frame(width: 10, height: 10)
                    Text(relay.isConnected ? "서버 연결됨" : "서버 미연결")
                        .font(.caption)
                }

                // Server Config
                TextField("서버 URL", text: $serverURL)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .font(.caption)

                TextField("세션 ID", text: $sessionId)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .font(.caption)

                if relay.isConnected {
                    Button("연결 해제") {
                        relay.disconnect()
                    }
                    .foregroundColor(.red)
                } else {
                    Button("서버 연결") {
                        relay.connect(serverURL: serverURL, sessionId: sessionId)
                    }
                    .disabled(sessionId.isEmpty)
                }
            }
            .padding()
            .navigationTitle("GuraNo")
        }
    }
}
