#!/usr/bin/env python3
"""Проверка репозитория: python tools/validate.py (запускать из корня репозитория)."""
import json
import re
import string
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ("ru", "en", "ja", "ko", "ar", "fr", "pl", "de", "uk")
errors = []


def placeholders(text):
    return sorted({name for _, name, _, _ in string.Formatter().parse(text) if name})


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.name}: {exc}")
        return None


files = {lang: load(ROOT / "localization" / f"{lang}.json") for lang in LANGS}
reference = (files.get("en") or {}).get("strings", {})
for lang, data in files.items():
    if data is None:
        continue
    strings = data.get("strings")
    if data.get("schema") != 1 or data.get("language") != lang or not isinstance(strings, dict):
        errors.append(f"{lang}.json: неверные schema/language/strings")
        continue
    for key in reference.keys() - strings.keys():
        errors.append(f"{lang}.json: нет ключа {key}")
    for key in strings.keys() - reference.keys():
        errors.append(f"{lang}.json: лишний ключ {key}")
    for key, text in strings.items():
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{lang}.json: пустое значение {key}")
        elif key in reference:
            try:
                if placeholders(text) != placeholders(reference[key]):
                    errors.append(f"{lang}.json: {key}: плейсхолдеры {placeholders(text)} вместо {placeholders(reference[key])}")
            except ValueError as exc:
                errors.append(f"{lang}.json: {key}: {exc}")

revoked = load(ROOT / "revoked.json")
if revoked is not None:
    if revoked.get("schema") != 1 or not isinstance(revoked.get("revoked_versions"), list):
        errors.append("revoked.json: неверная схема")
    if not all(isinstance(v, str) for v in revoked.get("revoked_versions", [])):
        errors.append("revoked.json: revoked_versions должен быть списком строк")
    mandatory = revoked.get("mandatory_updates", [])
    if not isinstance(mandatory, list):
        errors.append("revoked.json: mandatory_updates должен быть списком")
        mandatory = []
    for index, entry in enumerate(mandatory, 1):
        where = f"revoked.json: mandatory_updates[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{where}: ожидается объект")
            continue
        if not isinstance(entry.get("version"), str) or not re.fullmatch(r"\d+(\.\d+)*", entry["version"]):
            errors.append(f"{where}: version должна быть вида 30.0.0")
        try:
            moment = datetime.fromisoformat(str(entry.get("from")))
            if moment.utcoffset() != timedelta(hours=3):
                errors.append(f"{where}: from должен быть по Гринвичу +3 (суффикс +03:00)")
        except ValueError:
            errors.append(f"{where}: from должен быть датой ISO 8601, например 2026-11-01T12:00:00+03:00")
        if "message" in entry and not isinstance(entry["message"], dict):
            errors.append(f"{where}: message должен быть объектом по языкам")
    message = revoked.get("message", {})
    for lang in LANGS:
        if not str(message.get(lang, "")).strip():
            errors.append(f"revoked.json: нет сообщения для {lang}")

print("\n".join(errors) if errors else f"OK: {len(reference)} ключей, {len(LANGS)} языков")
sys.exit(1 if errors else 0)
