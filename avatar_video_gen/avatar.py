from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


DEFAULT_COMMAND_TEMPLATE = "python -m scripts.inference --inference_config {config}"


def generate_talking_avatar(
    image_path: str | Path,
    audio_path: str | Path,
    musetalk_dir: str | Path,
    output_path: str | Path,
    command_template: str = DEFAULT_COMMAND_TEMPLATE,
) -> Path:
    image_path = Path(image_path).resolve()
    audio_path = Path(audio_path).resolve()
    musetalk_dir = Path(musetalk_dir).resolve()
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not image_path.exists():
        raise FileNotFoundError(image_path)
    if not audio_path.exists():
        raise FileNotFoundError(audio_path)
    if not musetalk_dir.exists():
        raise FileNotFoundError(musetalk_dir)

    with tempfile.TemporaryDirectory(prefix="avatar_video_gen_") as tmp:
        tmpdir = Path(tmp)
        raw_output = tmpdir / "musetalk_output.mp4"
        config_path = tmpdir / "task.json"

        # Keep this config intentionally simple and explicit. If an upstream
        # MuseTalk release changes its schema, override --command-template and/or
        # adapt this file in one place rather than changing the rest of the pipeline.
        config = {
            "task_0": {
                "video_path": str(image_path),
                "audio_path": str(audio_path),
                "output_path": str(raw_output),
            }
        }
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

        command = command_template.format(
            config=str(config_path),
            image=str(image_path),
            audio=str(audio_path),
            output=str(raw_output),
        )
        completed = subprocess.run(
            command,
            cwd=musetalk_dir,
            shell=True,
            check=False,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"MuseTalk command failed with exit code {completed.returncode}: {command}")

        if raw_output.exists():
            shutil.copy2(raw_output, output_path)
            return output_path

        # Some MuseTalk versions determine output paths internally. Try common
        # result locations before asking the caller to provide a custom command.
        candidates = list((musetalk_dir / "results").rglob("*.mp4")) if (musetalk_dir / "results").exists() else []
        if candidates:
            newest = max(candidates, key=lambda p: p.stat().st_mtime)
            shutil.copy2(newest, output_path)
            return output_path

        raise FileNotFoundError(
            "MuseTalk completed but no output MP4 was found. "
            "Use --command-template to match your installed MuseTalk version."
        )
