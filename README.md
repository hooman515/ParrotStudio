# Parrot Studio

Parrot Studio is a macOS app for offline, high-quality Persian/Farsi video subtitling.
It takes a local video file, preserves the original Persian audio, creates English
subtitles, and exports an MP4 with a selectable embedded subtitle track plus an SRT
sidecar.

## MVP Flow

1. Choose any video file that `ffmpeg` can read.
2. Choose an output `.mp4` path.
3. Parrot Studio extracts audio chunks with `ffmpeg`.
4. The Python backend transcribes Persian audio with timestamps.
5. It translates segments into English subtitles.
6. It writes `.srt`, JSON artifacts, and an MP4 with embedded selectable subtitles.

## Requirements

- macOS 26 target
- Swift 6 / SwiftPM
- Python 3.12+
- `ffmpeg` and `ffprobe` on `PATH`
- OpenAI API key saved in Settings

## Development

```bash
make test
make build-app
./script/build_and_run.sh
```

The run script builds the SwiftUI app, stages `/Applications/Parrot Studio.app`,
copies the backend into the bundle resources, signs the bundle, and launches it.

## Identity

- App name: `Parrot Studio`
- Bundle id: `com.parrot.studio`
- Keychain service: `com.parrot.studio`
- Keychain account: `openai`

## Outputs

For an output path such as `Movie-subtitled.mp4`, the MVP creates:

- `Movie-subtitled.mp4`
- `Movie-subtitled.en.srt`
- Job artifacts under `~/Library/Application Support/Parrot Studio/Jobs/`
