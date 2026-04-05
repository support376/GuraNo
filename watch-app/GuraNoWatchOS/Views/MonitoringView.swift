import SwiftUI

struct MonitoringView: View {
    @StateObject private var monitor = HeartRateMonitor()

    var body: some View {
        VStack(spacing: 12) {
            Text("GuraNo")
                .font(.headline)
                .foregroundColor(.blue)

            Text("\(Int(monitor.currentHeartRate))")
                .font(.system(size: 60, weight: .bold, design: .rounded))
                .foregroundColor(.red)

            Text("BPM")
                .font(.caption)
                .foregroundColor(.gray)

            if monitor.isMonitoring {
                Button("중지") {
                    monitor.stopMonitoring()
                }
                .tint(.red)
            } else {
                Button("모니터링 시작") {
                    monitor.requestAuthorization()
                    monitor.startMonitoring()
                }
                .tint(.green)
            }

            Circle()
                .fill(monitor.isMonitoring ? Color.green : Color.gray)
                .frame(width: 8, height: 8)
        }
        .onAppear {
            monitor.requestAuthorization()
        }
    }
}
