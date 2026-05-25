# Testing

Backend unit tests:

```bash
PYTHONPATH=backend python3 -m unittest discover -s tests -p 'test_*.py'
```

Swift build:

```bash
swift build --package-path frontend/macos/ParrotStudioApp
```

Manual MVP test:

1. Choose a short Persian video.
2. Pick an output MP4 path.
3. Process with a saved OpenAI key.
4. Confirm the MP4 preserves the original audio.
5. Confirm the embedded English subtitle track is selectable.
6. Confirm the `.en.srt` sidecar exists.
