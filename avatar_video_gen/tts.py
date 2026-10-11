from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline


def text_to_speech(
    text: str,
    output_path: str | Path,
    voice: str = "af_heart",
    lang_code: str = "a",
    speed: float = 1.0,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pipeline = KPipeline(lang_code=lang_code)
    chunks = []
    sample_rate = 24000

    for result in pipeline(text, voice=voice, speed=speed):
        audio = result.audio
        if audio is None:
            continue
        chunks.append(np.asarray(audio, dtype=np.float32))

    if not chunks:
        raise RuntimeError("Kokoro produced no audio.")

    merged = np.concatenate(chunks)
    sf.write(output_path, merged, sample_rate)
    return output_path
