# Troubleshooting

## ffmpeg Missing

Parrot Studio requires both `ffmpeg` and `ffprobe` on `PATH`.

```bash
brew install ffmpeg
```

## No API Key

Open Settings and save an OpenAI API key. The key is stored in Keychain under
service `com.parrot.studio`, account `openai`.

## Output Does Not Play Subtitles

The app embeds selectable subtitles as an MP4 `mov_text` track and also writes an
SRT sidecar. If one player does not show the embedded track, try VLC or load the
sidecar SRT manually.

## Logs

Backend logs are written to:

`~/Library/Logs/Parrot Studio/parrot_studio.log`
