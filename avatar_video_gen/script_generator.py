from __future__ import annotations

import json
from typing import Any

from google import genai
from openai import OpenAI

from .config import settings


SYSTEM_PROMPT = """You write short-form social media video scripts from source articles.
Return ONLY valid JSON with this schema:
{
  "headline": "...",
  "hook": "...",
  "narration": "...",
  "onscreen_text": ["..."],
  "visual_suggestions": ["..."]
}

Requirements:
- Base all factual claims only on the supplied source text.
- Focus on the single most interesting or important story.
- Use a strong but non-clickbait hook.
- Write naturally for spoken delivery and TTS.
- Keep sentences short.
- Explain technical terms briefly when useful.
- Target roughly 70-110 spoken words unless instructed otherwise.
- Emphasize why the story matters.
- Do not fabricate quotes, numbers, dates, names, or conclusions.
- Do not include markdown fences.
"""


def _clean_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].lstrip()
    data = json.loads(text)
    required = {"headline", "hook", "narration", "onscreen_text", "visual_suggestions"}
    missing = required - set(data)
    if missing:
        raise ValueError(f"Model output is missing required keys: {sorted(missing)}")
    return data


def generate_with_gemini(source_text: str, model: str | None = None) -> dict[str, Any]:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = f"{SYSTEM_PROMPT}\n\nSOURCE ARTICLE:\n{source_text}"
    response = client.models.generate_content(
        model=model or settings.gemini_model,
        contents=prompt,
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    return _clean_json(response.text)


def generate_with_openrouter(source_text: str, model: str | None = None) -> dict[str, Any]:
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )
    response = client.chat.completions.create(
        model=model or settings.openrouter_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"SOURCE ARTICLE:\n{source_text}"},
        ],
        temperature=0.4,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("OpenRouter returned an empty response.")
    return _clean_json(content)


def generate_script(source_text: str, provider: str, model: str | None = None) -> dict[str, Any]:
    provider = provider.lower()
    if provider == "gemini":
        return generate_with_gemini(source_text, model=model)
    if provider == "openrouter":
        return generate_with_openrouter(source_text, model=model)
    raise ValueError("provider must be 'gemini' or 'openrouter'.")
