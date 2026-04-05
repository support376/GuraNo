import Foundation
import HealthKit
import WatchConnectivity

class HeartRateMonitor: NSObject, ObservableObject, HKWorkoutSessionDelegate, HKLiveWorkoutBuilderDelegate {
    let healthStore = HKHealthStore()
    var session: HKWorkoutSession?
    var builder: HKLiveWorkoutBuilder?

    @Published var currentHeartRate: Double = 0
    @Published var isMonitoring = false

    func requestAuthorization() {
        let hrType = HKQuantityType.quantityType(forIdentifier: .heartRate)!
        let types: Set<HKSampleType> = [hrType]

        healthStore.requestAuthorization(toShare: types, read: types) { success, error in
            if !success {
                print("HealthKit authorization failed: \(error?.localizedDescription ?? "unknown")")
            }
        }
    }

    func startMonitoring() {
        let config = HKWorkoutConfiguration()
        config.activityType = .other
        config.locationType = .indoor

        do {
            session = try HKWorkoutSession(healthStore: healthStore, configuration: config)
            builder = session?.associatedWorkoutBuilder()
            builder?.dataSource = HKLiveWorkoutDataSource(healthStore: healthStore, workoutConfiguration: config)

            session?.delegate = self
            builder?.delegate = self

            let startDate = Date()
            session?.startActivity(with: startDate)
            builder?.beginCollection(withStart: startDate) { [weak self] success, error in
                DispatchQueue.main.async {
                    self?.isMonitoring = success
                }
            }
        } catch {
            print("Failed to start workout session: \(error)")
        }
    }

    func stopMonitoring() {
        session?.end()
        builder?.endCollection(withEnd: Date()) { _, _ in }
        isMonitoring = false
    }

    // MARK: - HKLiveWorkoutBuilderDelegate

    func workoutBuilderDidCollectEvent(_ workoutBuilder: HKLiveWorkoutBuilder) {}

    func workoutBuilder(_ workoutBuilder: HKLiveWorkoutBuilder, didCollectDataOf collectedTypes: Set<HKSampleType>) {
        guard let hrType = HKQuantityType.quantityType(forIdentifier: .heartRate),
              collectedTypes.contains(hrType) else { return }

        let statistics = workoutBuilder.statistics(for: hrType)
        let hrUnit = HKUnit.count().unitDivided(by: .minute())

        if let value = statistics?.mostRecentQuantity()?.doubleValue(for: hrUnit) {
            DispatchQueue.main.async {
                self.currentHeartRate = value
            }
            // Send to iPhone
            WatchSender.shared.sendHeartRate(bpm: value)
        }
    }

    // MARK: - HKWorkoutSessionDelegate

    func workoutSession(_ workoutSession: HKWorkoutSession, didChangeTo toState: HKWorkoutSessionState, from fromState: HKWorkoutSessionState, date: Date) {}

    func workoutSession(_ workoutSession: HKWorkoutSession, didFailWithError error: Error) {
        print("Workout session failed: \(error)")
    }
}
