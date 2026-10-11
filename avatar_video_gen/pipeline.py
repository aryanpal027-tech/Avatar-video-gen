from __future__ import annotations

import json
from pathlib import Path

from .avatar import generate_talking_avatar
from .captions import transcribe_to_srt
from .config import settings
from .ffmpeg_utils import compose_vertical_video
from .ingest import extract_from_pdf, extract_from_url, save_text
from .script_generator import generate_script
from .tts import text_to_speech


def run_pipeline(
    *,
    url: str | None = None,
    pdf: str | None = None,
    provider: str = "gemini",
    model: str | None = None,
    avatar_image: str | None = None,
    musetalk_dir: str | None = None,
    workdir: str = "outputs/run",
    voice: str | None = None,
    skip_script: bool = False,
    skip_tts: bool = False,
    skip_avatar: bool = False,
    skip_captions: bool = False,
    skip_compose: bool = False,
) -> dict[str, str]:
    if bool(url) == bool(pdf):
        raise ValueError("Provide exactly one of url or pdf.")

    root = Path(workdir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "article": root / "article.txt",
        "script": root / "script.json",
        "audio": root / "voice.wav",
        "avatar": root / "avatar.mp4",
        "captions": root / "captions.srt",
        "final": root / "final.mp4",
    }

    if url:
        article_text = extract_from_url(url)
    else:
        article_text = extract_from_pdf(pdf)  # type: ignore[arg-type]
    save_text(article_text, paths["article"])

    script_data = None
    if not skip_script:
        script_data = generate_script(article_text, provider=provider, model=model)
        paths["script"].write_text(json.dumps(script_data, indent=2, ensure_ascii=False), encoding="utf-8")
    elif paths["script"].exists():
        script_data = json.loads(paths["script"].read_text(encoding="utf-8"))

    if not skip_tts:
        if not script_data:
            raise RuntimeError("TTS requires an existing/generated script.json.")
        text_to_speech(
            script_data["narration"],
            paths["audio"],
            voice=voice or settings.kokoro_voice,
        )

    if not skip_avatar:
        if not avatar_image or not musetalk_dir:
            raise ValueError("Avatar stage requires avatar_image and musetalk_dir.")
        generate_talking_avatar(
            avatar_image,
            paths["audio"],
            musetalk_dir,
            paths["avatar"],
        )

    if not skip_captions:
        transcribe_to_srt(
            paths["audio"],
            paths["captions"],
            model_name=settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )

    if not skip_compose:
        if not paths["avatar"].exists():
            raise RuntimeError("Compose stage requires avatar.mp4. Run avatar generation or supply the file in workdir.")
        compose_vertical_video(
            paths["avatar"],
            paths["final"],
            captions_path=paths["captions"] if paths["captions"].exists() else None,
        )

    return {key: str(path) for key, path in paths.items() if path.exists()}
