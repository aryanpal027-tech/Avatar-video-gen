from __future__ import annotations

import argparse
import json
from pathlib import Path

from avatar_video_gen.avatar import generate_talking_avatar
from avatar_video_gen.captions import transcribe_to_srt
from avatar_video_gen.config import settings
from avatar_video_gen.ffmpeg_utils import compose_vertical_video
from avatar_video_gen.ingest import extract_from_pdf, extract_from_url, save_text
from avatar_video_gen.pipeline import run_pipeline
from avatar_video_gen.script_generator import generate_script
from avatar_video_gen.tts import text_to_speech


def main() -> None:
    parser = argparse.ArgumentParser(description="Modular article/PDF to avatar-video pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--url")
    group.add_argument("--pdf")
    p.add_argument("--output", required=True)

    p = sub.add_parser("script")
    p.add_argument("--input", required=True)
    p.add_argument("--provider", choices=["gemini", "openrouter"], required=True)
    p.add_argument("--model")
    p.add_argument("--output", required=True)

    p = sub.add_parser("tts")
    p.add_argument("--script", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--voice", default=settings.kokoro_voice)
    p.add_argument("--lang-code", default="a")
    p.add_argument("--speed", type=float, default=1.0)

    p = sub.add_parser("avatar")
    p.add_argument("--image", required=True)
    p.add_argument("--audio", required=True)
    p.add_argument("--musetalk-dir", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--command-template", default="python -m scripts.inference --inference_config {config}")

    p = sub.add_parser("captions")
    p.add_argument("--audio", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--model", default=settings.whisper_model)
    p.add_argument("--device", default=settings.whisper_device)
    p.add_argument("--compute-type", default=settings.whisper_compute_type)
    p.add_argument("--language")

    p = sub.add_parser("compose")
    p.add_argument("--video", required=True)
    p.add_argument("--captions")
    p.add_argument("--music")
    p.add_argument("--output", required=True)

    p = sub.add_parser("pipeline")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--url")
    group.add_argument("--pdf")
    p.add_argument("--provider", choices=["gemini", "openrouter"], default="gemini")
    p.add_argument("--model")
    p.add_argument("--avatar-image")
    p.add_argument("--musetalk-dir")
    p.add_argument("--workdir", default="outputs/run")
    p.add_argument("--voice", default=settings.kokoro_voice)
    p.add_argument("--skip-script", action="store_true")
    p.add_argument("--skip-tts", action="store_true")
    p.add_argument("--skip-avatar", action="store_true")
    p.add_argument("--skip-captions", action="store_true")
    p.add_argument("--skip-compose", action="store_true")

    args = parser.parse_args()

    if args.command == "ingest":
        text = extract_from_url(args.url) if args.url else extract_from_pdf(args.pdf)
        save_text(text, args.output)
        print(args.output)
        return

    if args.command == "script":
        source = Path(args.input).read_text(encoding="utf-8")
        data = generate_script(source, args.provider, model=args.model)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(args.output)
        return

    if args.command == "tts":
        data = json.loads(Path(args.script).read_text(encoding="utf-8"))
        print(text_to_speech(data["narration"], args.output, voice=args.voice, lang_code=args.lang_code, speed=args.speed))
        return

    if args.command == "avatar":
        print(generate_talking_avatar(args.image, args.audio, args.musetalk_dir, args.output, args.command_template))
        return

    if args.command == "captions":
        print(transcribe_to_srt(args.audio, args.output, args.model, args.device, args.compute_type, args.language))
        return

    if args.command == "compose":
        print(compose_vertical_video(args.video, args.output, captions_path=args.captions, music_path=args.music))
        return

    result = run_pipeline(
        url=args.url,
        pdf=args.pdf,
        provider=args.provider,
        model=args.model,
        avatar_image=args.avatar_image,
        musetalk_dir=args.musetalk_dir,
        workdir=args.workdir,
        voice=args.voice,
        skip_script=args.skip_script,
        skip_tts=args.skip_tts,
        skip_avatar=args.skip_avatar,
        skip_captions=args.skip_captions,
        skip_compose=args.skip_compose,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
