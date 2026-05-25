# Setup

Install dependencies:

```bash
brew install ffmpeg
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Run checks:

```bash
make test
make build-app
```

Run the app:

```bash
./script/build_and_run.sh
```

Add your OpenAI API key in Settings before processing a video.
