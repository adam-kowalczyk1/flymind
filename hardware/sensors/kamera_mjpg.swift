// Kamera nadgarstka przez AVFoundation z WYBRANYM formatem (20 XI). ffmpeg sam wybiera format i dla 1280x800@120 pada
// („Configuration of video device failed”) — tu wybieramy format po numerze, w tym MJPG, jeśli macOS go pokazuje.
// Budowa (Claude, bez kamery):  swiftc -O -o /Users/admin/tools/kamera_mjpg hardware/sensors/kamera_mjpg.swift
// Adam WKLEJA w Terminal (sama kamera działa tylko stamtąd):
//   /Users/admin/tools/kamera_mjpg | tee -a ~/Desktop/kamera_mjpg.txt      → lista formatów + prawdziwe kl./s każdego (3 s)
//   /Users/admin/tools/kamera_mjpg stream NR W H                            → szare klatki W×H (surowe bajty) na stdout
//   /Users/admin/tools/kamera_mjpg one NR                                   → pomiar jednego formatu
import AVFoundation
import Foundation

setvbuf(stdout, nil, _IOLBF, 0)
func err(_ s: String) { FileHandle.standardError.write((s + "\n").data(using: .utf8)!) }

func camera() -> AVCaptureDevice? {
    let ds = AVCaptureDevice.DiscoverySession(deviceTypes: [.external], mediaType: .video, position: .unspecified)
    return ds.devices.first { $0.localizedName == "USB Camera" || $0.modelID.contains("VendorID_3141") }   // 0x0c45 = 3141
}

func fourcc(_ f: AVCaptureDevice.Format) -> String {
    let t = CMFormatDescriptionGetMediaSubType(f.formatDescription)
    return String(bytes: [24, 16, 8, 0].map { UInt8((t >> $0) & 255) }, encoding: .ascii) ?? "?"
}

func describe(_ i: Int, _ f: AVCaptureDevice.Format) -> String {
    let d = CMVideoFormatDescriptionGetDimensions(f.formatDescription)
    let r = f.videoSupportedFrameRateRanges.map { String(format: "%.0f–%.0f", $0.minFrameRate, $0.maxFrameRate) }
    return "\(i): \(fourcc(f)) \(d.width)x\(d.height) kl./s \(r.joined(separator: ", "))"
}

final class Sink: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    var n = 0, w = 0, h = 0, t0 = 0.0, t1 = 0.0
    let W: Int, H: Int
    var buf: [UInt8]
    init(_ W: Int, _ H: Int) { self.W = W; self.H = H; buf = [UInt8](repeating: 0, count: W * H) }

    func captureOutput(_ o: AVCaptureOutput, didOutput sb: CMSampleBuffer, from c: AVCaptureConnection) {
        let now = CFAbsoluteTimeGetCurrent()
        if n == 0 { t0 = now }
        t1 = now; n += 1
        guard W > 0, let pb = CMSampleBufferGetImageBuffer(sb) else { return }
        CVPixelBufferLockBaseAddress(pb, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(pb, .readOnly) }
        w = CVPixelBufferGetWidthOfPlane(pb, 0); h = CVPixelBufferGetHeightOfPlane(pb, 0)
        let y = CVPixelBufferGetBaseAddressOfPlane(pb, 0)!.assumingMemoryBound(to: UInt8.self)
        let st = CVPixelBufferGetBytesPerRowOfPlane(pb, 0)
        for oy in 0..<H {                                   // średnia z bloku (jasność Y) → W×H
            let y0 = oy * h / H, y1 = max(y0 + 1, (oy + 1) * h / H)
            for ox in 0..<W {
                let x0 = ox * w / W, x1 = max(x0 + 1, (ox + 1) * w / W)
                var s = 0
                for yy in y0..<y1 { for xx in x0..<x1 { s += Int(y[yy * st + xx]) } }
                buf[oy * W + ox] = UInt8(s / ((y1 - y0) * (x1 - x0)))
            }
        }
        if fwrite(buf, 1, buf.count, stdout) < buf.count { exit(0) }   // odbiorca zamknął rurę
        fflush(stdout)
    }
}

/// Uruchamia kamerę w formacie `idx` z najwyższym kl./s, jaki ten format zgłasza.
func run(_ dev: AVCaptureDevice, _ idx: Int, _ sink: Sink) -> AVCaptureSession {
    let f = dev.formats[idx]
    let r = f.videoSupportedFrameRateRanges.max { $0.maxFrameRate < $1.maxFrameRate }!
    let s = AVCaptureSession()
    let out = AVCaptureVideoDataOutput()
    out.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_420YpCbCr8BiPlanarFullRange]
    out.alwaysDiscardsLateVideoFrames = true                  // bez kolejki: spóźniona klatka przepada
    out.setSampleBufferDelegate(sink, queue: DispatchQueue(label: "kl"))
    s.beginConfiguration()
    s.addInput(try! AVCaptureDeviceInput(device: dev))
    s.addOutput(out)
    try! dev.lockForConfiguration()
    dev.activeFormat = f
    dev.activeVideoMinFrameDuration = r.minFrameDuration
    dev.activeVideoMaxFrameDuration = r.minFrameDuration
    s.commitConfiguration()
    s.startRunning()
    dev.unlockForConfiguration()                              // blokada do po starcie: macOS nie przestawia formatu
    let set = dev.activeFormat == f ? "tak" : "NIE (macOS wybrał \(fourcc(dev.activeFormat)))"
    err(String(format: "format %d ustawiony: %@, żądane %.0f kl./s", idx, set, r.maxFrameRate))
    return s
}

let a = CommandLine.arguments
guard let dev = camera() else {
    print("BRAK kamery USB (dostęp: \(AVCaptureDevice.authorizationStatus(for: .video).rawValue); 3 = jest) — podłącz ją, wklej w Terminal")
    exit(1)
}
if a.count >= 5 && a[1] == "stream" {
    let sink = Sink(Int(a[3])!, Int(a[4])!)
    let s = run(dev, Int(a[2])!, sink)
    withExtendedLifetime(s) { RunLoop.main.run() }
} else if a.count >= 3 && a[1] == "one" {
    let sink = Sink(0, 0)
    let s = run(dev, Int(a[2])!, sink)
    Thread.sleep(forTimeInterval: 3.5)
    s.stopRunning()
    let fps = sink.n > 1 ? Double(sink.n - 1) / (sink.t1 - sink.t0) : 0
    print(String(format: "   → klatek %d, PRAWDZIWE %.0f kl./s", sink.n, fps))
} else {
    print("kamera_mjpg \(Date()): \(dev.localizedName) | \(dev.modelID)")
    for (i, f) in dev.formats.enumerated() {
        print(describe(i, f))
        let p = Process()                                     // każdy format w osobnym procesie: wywrotka nie psuje reszty
        p.executableURL = URL(fileURLWithPath: Bundle.main.executablePath!)
        p.arguments = ["one", String(i)]
        try? p.run()
        p.waitUntilExit()
        if p.terminationStatus != 0 { print("   → BŁĄD (proces padł, kod \(p.terminationStatus))") }
    }
}
