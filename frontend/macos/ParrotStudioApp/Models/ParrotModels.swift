import Foundation

enum SessionState: String, Codable, CaseIterable {
    case idle
    case configured
    case starting
    case processing
    case complete
    case capturing
    case stopping
    case error
    case recovering
}

struct BackendReady: Codable {
    var type: String
    var controlPort: Int

    enum CodingKeys: String, CodingKey {
        case type
        case controlPort = "control_port"
    }
}

struct StartVideoJobRequest: Codable {
    var command = "start_video_job"
    var inputPath: String
    var outputPath: String
    var transcriptionModel: String
    var translationModel: String
    var sourceLanguage = "fa"
    var targetLanguage = "en"
    var workDir: String?
    var debug: Bool
    var openaiAPIKey: String

    enum CodingKeys: String, CodingKey {
        case command
        case inputPath = "input_path"
        case outputPath = "output_path"
        case transcriptionModel = "transcription_model"
        case translationModel = "translation_model"
        case sourceLanguage = "source_language"
        case targetLanguage = "target_language"
        case workDir = "work_dir"
        case debug
        case openaiAPIKey = "openai_api_key"
    }
}

struct CancelJobRequest: Codable {
    var command = "cancel_job"
}

enum ControlEvent: Decodable, Identifiable {
    case status(StatusPayload)
    case error(ErrorPayload)
    case metric(MetricPayload)
    case jobProgress(JobProgressPayload)
    case jobComplete(JobCompletePayload)

    var id: UUID { UUID() }

    private enum CodingKeys: String, CodingKey {
        case type
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        switch try container.decode(String.self, forKey: .type) {
        case "status": self = .status(try StatusPayload(from: decoder))
        case "error": self = .error(try ErrorPayload(from: decoder))
        case "metric": self = .metric(try MetricPayload(from: decoder))
        case "job_progress": self = .jobProgress(try JobProgressPayload(from: decoder))
        case "job_complete": self = .jobComplete(try JobCompletePayload(from: decoder))
        default: throw DecodingError.dataCorruptedError(forKey: .type, in: container, debugDescription: "Unknown event type")
        }
    }
}

struct StatusPayload: Decodable {
    var type: String
    var state: SessionState
    var message: String
    var createdAtMS: Int

    enum CodingKeys: String, CodingKey {
        case type, state, message
        case createdAtMS = "created_at_ms"
    }
}

struct JobProgressPayload: Decodable {
    var type: String
    var stage: String
    var progress: Double
    var message: String
    var createdAtMS: Int

    enum CodingKeys: String, CodingKey {
        case type, stage, progress, message
        case createdAtMS = "created_at_ms"
    }
}

struct JobCompletePayload: Decodable {
    var type: String
    var outputVideoPath: String
    var subtitlePath: String
    var artifactDir: String
    var createdAtMS: Int

    enum CodingKeys: String, CodingKey {
        case type
        case outputVideoPath = "output_video_path"
        case subtitlePath = "subtitle_path"
        case artifactDir = "artifact_dir"
        case createdAtMS = "created_at_ms"
    }
}
struct ErrorPayload: Decodable {
    var type: String
    var code: String
    var message: String
    var retryable: Bool
    var createdAtMS: Int

    enum CodingKeys: String, CodingKey {
        case type, code, message, retryable
        case createdAtMS = "created_at_ms"
    }
}

struct MetricPayload: Decodable {
    var type: String
    var stage: String
    var durationMS: Int
    var sessionID: String
    var createdAtMS: Int

    enum CodingKeys: String, CodingKey {
        case type, stage
        case durationMS = "duration_ms"
        case sessionID = "session_id"
        case createdAtMS = "created_at_ms"
    }
}
