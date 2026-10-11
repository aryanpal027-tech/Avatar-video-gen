from __future__ import annotations

from pathlib import Path

from faster_whisper import WhisperModel


def _fmt_srt_time(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def transcribe_to_srt(
    audio_path: str | Path,
    output_path: str | Path,
    model_name: str = "small",
    device: str = "cpu",
    compute_type: str = "int8",
    language: str | None = None,
) -> Path:
    audio_path = Path(audio_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    segments, _ = model.transcribe(
        str(audio_path),
        language=language,
        vad_filter=True,
    )

    lines: list[str] = []
    for i, segment in enumerate(segments, start=1):
        text = segment.text.strip()
        if not text:
            continue
        lines.extend([
            str(i),
            f"{_fmt_srt_time(segment.start)} --> {_fmt_srt_time(segment.end)}",
            text,
            "",
        ])

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
