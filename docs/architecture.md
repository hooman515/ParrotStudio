# Architecture

Parrot Studio is split into a SwiftUI macOS shell and a Python worker service.

## Frontend

- Selects one local video file.
- Selects one output MP4 path.
- Reads the OpenAI key from Keychain.
- Starts the Python backend subprocess.
- Sends `start_video_job` commands over a local WebSocket.
- Renders progress, errors, and output artifact paths.

## Backend

- Exposes a localhost WebSocket control channel.
- Uses `ffprobe` to inspect input duration.
- Uses `ffmpeg` to extract compressed audio chunks.
- Sends chunks to OpenAI transcription.
- Translates timestamped segments to English.
- Generates JSON artifacts and SRT.
- Uses `ffmpeg` to mux selectable subtitles into MP4.

The backend emits `status`, `job_progress`, `job_complete`, and `error` events.
