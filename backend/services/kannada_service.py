import json
import os
from pathlib import Path
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()

KANNADA_CACHE_PATH = Path(os.environ.get("KANNADA_CACHE_PATH", "./data/kannada_cache.json"))

_cache: dict[str, str] = {}


def _load_cache():
    global _cache
    if KANNADA_CACHE_PATH.exists():
        with open(KANNADA_CACHE_PATH, "r", encoding="utf-8") as f:
            _cache = json.load(f)


def _save_cache():
    KANNADA_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(KANNADA_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(_cache, f, ensure_ascii=False, indent=2)


_load_cache()


def translate_to_kannada(text: str) -> str:
    if not text or not text.strip():
        return ""

    if text in _cache:
        return _cache[text]

    try:
        translated = GoogleTranslator(source="en", target="kn").translate(text)
        _cache[text] = translated
        _save_cache()
        return translated
    except Exception:
        return text


def translate_batch(texts: list[str]) -> list[dict]:
    results = []
    for text in texts:
        results.append({
            "english": text,
            "kannada": translate_to_kannada(text),
        })
    return results


def get_cache_stats() -> dict:
    return {
        "cached_translations": len(_cache),
        "cache_path": str(KANNADA_CACHE_PATH),
    }
