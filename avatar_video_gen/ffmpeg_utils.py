from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _require_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg was not found on PATH.")
    return ffmpeg


def compose_vertical_video(
    video_path: str | Path,
    output_path: str | Path,
    captions_path: str | Path | None = None,
    music_path: str | Path | None = None,
    width: int = 1080,
    height: int = 1920,
    music_volume: float = 0.12,
) -> Path:
    ffmpeg = _require_ffmpeg()
    video_path = Path(video_path).resolve()
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        raise FileNotFoundError(video_path)

    inputs = ["-i", str(video_path)]
    filters = [
        f"scale={width}:{height}:force_original_aspect_ratio=decrease",
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
    ]

    if captions_path:
        captions = Path(captions_path).resolve()
        if not captions.exists():
            raise FileNotFoundError(captions)
        escaped = str(captions).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        filters.append(
            "subtitles='{}':force_style='Alignment=2,Fontsize=18,Outline=2,Shadow=0,MarginV=90'".format(escaped)
        )

    cmd = [ffmpeg, "-y", *inputs]

    if music_path:
        music = Path(music_path).resolve()
        if not music.exists():
            raise FileNotFoundError(music)
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        cmd += [
            "-filter_complex",
            f"[0:v]{','.join(filters)}[v];[1:a]volume={music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
        ]
    else:
        cmd += ["-vf", ",".join(filters), "-map", "0:v:0", "-map", "0:a?"]

    cmd += [
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        "-shortest",
        str(output_path),
    ]

    completed = subprocess.run(cmd, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"FFmpeg failed with exit code {completed.returncode}.")
    return output_path
