// Convert Godot's JPEG AVI frames to H.264 without changing frame order or pixels.
// Usage: swift encode-godot-avi.swift input.avi output.mp4 [initial_setup_frames]
import Foundation
import AVFoundation
import CoreGraphics
import ImageIO

let args = CommandLine.arguments
guard args.count >= 3 else { fatalError("input.avi output.mp4 [initial_setup_frames]") }
let bytes = try Data(contentsOf: URL(fileURLWithPath: args[1]))
func number(_ at: Int) -> Int {
    Int(bytes[at]) | Int(bytes[at+1]) << 8 | Int(bytes[at+2]) << 16 | Int(bytes[at+3]) << 24
}
func tag(_ at: Int) -> String { String(decoding: bytes[at..<at+4], as: UTF8.self) }
guard let movi = bytes.range(of: Data("movi".utf8)), let avih = bytes.range(of: Data("avih".utf8)) else { fatalError("Not an AVI") }
let width = number(avih.lowerBound+40), height = number(avih.lowerBound+44)
let fps = Int32((1_000_000.0 / Double(number(avih.lowerBound+8))).rounded())
var at = movi.upperBound
var frames: [Range<Int>] = []
while at + 8 <= bytes.count {
    let size = number(at+4)
    guard size >= 0, at + 8 + size <= bytes.count else { break }
    if ["00db", "00dc"].contains(tag(at)) { frames.append(at+8..<at+8+size) }
    at += 8 + size + size % 2
}
let skip = args.count > 3 ? Int(args[3])! : 0
guard width > 0, height > 0, fps > 0, frames.count > skip else { fatalError("Empty or invalid AVI") }
let output = URL(fileURLWithPath: args[2])
if FileManager.default.fileExists(atPath: output.path) { try FileManager.default.removeItem(at: output) }
let writer = try AVAssetWriter(outputURL: output, fileType: .mp4)
let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
    AVVideoCodecKey: AVVideoCodecType.h264,
    AVVideoWidthKey: width, AVVideoHeightKey: height,
    AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 6_000_000,
        AVVideoExpectedSourceFrameRateKey: fps, AVVideoMaxKeyFrameIntervalKey: fps]])
input.expectsMediaDataInRealTime = false
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input,
    sourcePixelBufferAttributes: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
        kCVPixelBufferWidthKey as String: width, kCVPixelBufferHeightKey as String: height,
        kCVPixelBufferCGImageCompatibilityKey as String: true, kCVPixelBufferCGBitmapContextCompatibilityKey as String: true])
writer.add(input)
guard writer.startWriting() else { fatalError("\(String(describing: writer.error))") }
writer.startSession(atSourceTime: .zero)
for (index, range) in frames.dropFirst(skip).enumerated() {
    while !input.isReadyForMoreMediaData {
        guard writer.status == .writing else { fatalError("\(String(describing: writer.error))") }
        Thread.sleep(forTimeInterval: 0.002)
    }
    try autoreleasepool {
        guard let source = CGImageSourceCreateWithData(bytes.subdata(in: range) as CFData, nil),
              let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else { fatalError("Invalid JPEG frame \(index)") }
        guard image.width == width && image.height == height else { fatalError("AVI header/frame dimensions differ") }
        var buffer: CVPixelBuffer?
        guard CVPixelBufferPoolCreatePixelBuffer(nil, adaptor.pixelBufferPool!, &buffer) == kCVReturnSuccess else { fatalError("Pixel buffer allocation") }
        CVPixelBufferLockBaseAddress(buffer!, [])
        let context = CGContext(data: CVPixelBufferGetBaseAddress(buffer!), width: width, height: height,
            bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(buffer!), space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGBitmapInfo.byteOrder32Little.rawValue | CGImageAlphaInfo.premultipliedFirst.rawValue)!
        context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
        CVPixelBufferUnlockBaseAddress(buffer!, [])
        guard adaptor.append(buffer!, withPresentationTime: CMTime(value: Int64(index), timescale: fps)) else { throw writer.error! }
    }
}
input.markAsFinished()
let group = DispatchGroup(); group.enter()
writer.finishWriting { group.leave() }
group.wait()
guard writer.status == .completed else { fatalError("\(String(describing: writer.error))") }
print("ENCODED \(frames.count - skip) frames, \(width)x\(height), \(fps) fps; skipped \(skip) initial setup frames.")
