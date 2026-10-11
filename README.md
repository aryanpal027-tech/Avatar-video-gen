# Avatar Video Generator

Modular pipeline for turning an article URL or PDF into a short avatar video.

Each stage is optional and can be run independently:

1. Article/PDF ingestion
2. Script generation with Gemini or OpenRouter
3. Script-to-speech with Kokoro TTS
4. Image + voice to talking avatar with MuseTalk
5. Caption generation with faster-whisper
6. Final composition with FFmpeg

## Project layout

```text
avatar_video_gen/
  __init__.py
  config.py
  ingest.py
  script_generator.py
  tts.py
  avatar.py
  captions.py
  ffmpeg_utils.py
  pipeline.py
cli.py
requirements.txt
requirements-avatar.txt
.env.example
```

## Prerequisites

- Python 3.10+
- FFmpeg available on PATH
- For GPU acceleration: NVIDIA CUDA environment compatible with your installed PyTorch / CTranslate2 versions
- MuseTalk cloned separately if you want local avatar generation

## Install core dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

For MuseTalk-specific dependencies, see `requirements-avatar.txt` and the upstream MuseTalk repository. This project deliberately calls MuseTalk through its CLI rather than vendoring it, so you can update/test MuseTalk separately.

## Environment variables

Copy `.env.example` to `.env`.

```bash
cp .env.example .env
```

Set at least one script-generation provider:

```env
GEMINI_API_KEY=...
OPENROUTER_API_KEY=...
```

Optional defaults can also be configured in `.env`.

## 1. Extract article text

From a URL:

```bash
python cli.py ingest --url "https://example.com/article" --output outputs/article.txt
```

From a PDF:

```bash
python cli.py ingest --pdf path/to/article.pdf --output outputs/article.txt
```

## 2. Generate a short-form script

Gemini:

```bash
python cli.py script \
  --input outputs/article.txt \
  --provider gemini \
  --output outputs/script.json
```

OpenRouter:

```bash
python cli.py script \
  --input outputs/article.txt \
  --provider openrouter \
  --model "openai/gpt-4.1-mini" \
  --output outputs/script.json
```

The generated JSON includes a headline, hook, narration, on-screen text suggestions and visual suggestions.

## 3. Generate voice

```bash
python cli.py tts \
  --script outputs/script.json \
  --output outputs/voice.wav \
  --voice af_heart
```

This stage uses Kokoro locally.

## 4. Generate a talking avatar

First clone and set up MuseTalk separately, following its upstream instructions.

Then point this project to the MuseTalk directory:

```bash
python cli.py avatar \
  --image assets/avatar.png \
  --audio outputs/voice.wav \
  --musetalk-dir /path/to/MuseTalk \
  --output outputs/avatar.mp4
```

The wrapper creates a temporary MuseTalk task config and invokes MuseTalk using its CLI.

Because MuseTalk changes over time, the exact command can be overridden:

```bash
python cli.py avatar \
  --image assets/avatar.png \
  --audio outputs/voice.wav \
  --musetalk-dir /path/to/MuseTalk \
  --command-template "python -m scripts.inference --inference_config {config}" \
  --output outputs/avatar.mp4
```

Available placeholders are `{config}`, `{image}`, `{audio}`, and `{output}`.

## 5. Generate captions

```bash
python cli.py captions \
  --audio outputs/voice.wav \
  --output outputs/captions.srt \
  --model small
```

Uses faster-whisper and supports CPU or CUDA.

## 6. Compose final vertical video

```bash
python cli.py compose \
  --video outputs/avatar.mp4 \
  --captions outputs/captions.srt \
  --output outputs/final.mp4
```

Optional background music:

```bash
python cli.py compose \
  --video outputs/avatar.mp4 \
  --captions outputs/captions.srt \
  --music assets/music.mp3 \
  --output outputs/final.mp4
```

## Run the whole pipeline

URL input:

```bash
python cli.py pipeline \
  --url "https://example.com/article" \
  --provider gemini \
  --avatar-image assets/avatar.png \
  --musetalk-dir /path/to/MuseTalk \
  --workdir outputs/run1
```

PDF input:

```bash
python cli.py pipeline \
  --pdf paper.pdf \
  --provider openrouter \
  --model "openai/gpt-4.1-mini" \
  --avatar-image assets/avatar.png \
  --musetalk-dir /path/to/MuseTalk \
  --workdir outputs/run2
```

Skip stages while testing:

```bash
python cli.py pipeline \
  --url "https://example.com/article" \
  --provider gemini \
  --skip-avatar \
  --skip-captions \
  --skip-compose \
  --workdir outputs/script_test
```

## Notes

- Article extraction first tries `trafilatura`, then falls back to BeautifulSoup.
- PDF extraction uses PyMuPDF.
- Gemini uses the current `google-genai` SDK.
- OpenRouter is called through its OpenAI-compatible API.
- Kokoro is local and open-weight; the first run may download model assets.
- faster-whisper can run on CPU or CUDA.
- MuseTalk is kept as a separate dependency because its weights and environment are comparatively large and change more frequently than the rest of this pipeline.
- FFmpeg is responsible for formatting to 1080×1920, burning subtitles and optionally mixing background music.

## Responsible use

Only create avatars of people you are permitted to depict. Do not use this pipeline to impersonate people deceptively or create misleading synthetic media.
