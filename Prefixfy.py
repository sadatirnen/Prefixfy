import base64
import difflib
import hashlib
import hmac
import struct
import sys
import json
import math
import mimetypes
import os
import random
import re
import shutil
import secrets
import threading
import time
import types
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date as _date, datetime, timedelta
import uuid
import weakref
import zipfile
import zlib
from bisect import bisect_left, bisect_right
from collections import OrderedDict
from contextlib import contextmanager, nullcontext
from functools import lru_cache
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from base_plugin import BasePlugin, HookFilter, HookResult, HookStrategy, MenuItemData, MenuItemType
from ui.settings import Divider, Header, Input, Selector, Switch, Text
from ui.settings import Input as _SdkInput, Selector as _SdkSelector, Switch as _SdkSwitch, Text as _SdkText
from ui.alert import AlertDialogBuilder
from ui.bulletin import BulletinHelper
from android.widget import CheckBox, EditText as AndroidEditText, LinearLayout
from android.text import InputType
from android.app import Activity
from android.content import Intent
from android.net import Uri
from file_utils import FilesController, delete_file, ensure_dir_exists, get_cache_dir, get_plugins_dir
from client_utils import (
    PLUGINS_QUEUE,
    get_hook_account,
    get_last_fragment,
    get_messages_controller,
    get_selected_account,
    get_user_config,
    run_on_queue,
    send_document,
    send_message as _send_message,
    send_photo,
    send_video,
)
from android_utils import run_on_ui_thread
from hook_utils import find_class, java_class
import plugin_settings as _settings_store

try:
    from re import _constants as _re_constants, _parser as _re_parser
except ImportError:
    try:
        import sre_constants as _re_constants
        import sre_parse as _re_parser
    except ImportError:
        _re_constants = _re_parser = None


__id__ = "double_slash_prefix"
__name__ = "Prefixfy"
__description__ = "Prefixfy — стильное оформление исходящих сообщений: маска с гиперссылкой и 35+ тегами, 30 стилей текста, разделители и милые эффекты, маски для чатов с ротацией, правилами и расписанием, исключения и regex, оформление при редактировании, вложение медиа, Premium Emoji. Конфигурации (в том числе по аккаунтам) с импортом и экспортом, OTA-обновления, 5 языков интерфейса."
__author__ = "@Prefixfy"
__version__ = "54.0.0"
__build__ = "54.0.0_20261127.2_108"
__icon__ = "http_Prefixfy_by_fStikBot/3"
__app_version__ = ">=13.1.1"
__sdk_version__ = ">=1.4.6.5"


REPO_URL = "https://github.com/sadatirnen/Prefixfy"
UPDATE_BASE_URL = "https://raw.githubusercontent.com/sadatirnen/Prefixfy/main/"
MANIFEST_FILE = "version.json"
MANIFEST_FORMAT = 1
MANIFEST_DOMAIN = b"Prefixfy-manifest-v1\n"
FLAGS_FILE = "flags.json"
FLAGS_FORMAT = 1
FLAGS_DOMAIN = b"Prefixfy-flags-v1\n"
FLAGS_CACHE_FILE = ".pfx_profile"
SERIALS_FILE = ".pfx_serials"
KNOWN_BUILDS_FILE = ".pfx_known"
STORE_KEY_FILE = ".pfx_store_key"
FLAGS_MAX_COUNT = 128
FLAGS_MAX_ACCOUNTS = 1024
FLAGS_MAX_BYTES = 256 * 1024
MANIFEST_MAX_FILE_SIZE = 8 * 1024 * 1024
CHANGELOG_MAX_ITEMS = 30
CHANGELOG_ITEM_LIMIT = 300
CHANGELOG_TOTAL_LIMIT = 4000
CHANGELOG_MAX_LANGS = 8
BLACKLIST_MAX_AGE = 3 * 24 * 3600
SIGNED_FUTURE_SKEW = 14 * 24 * 3600
SIGNED_MAX_AGE = 0
REPLY_QUOTE_LIMIT = 40
WEATHER_HOST = "wttr.in"
BLACKLIST_FILE = "blacklist.json"
BLACKLIST_FORMAT = 1
BLACKLIST_DOMAIN = b"Prefixfy-blacklist-v1\n"
BLACKLIST_CACHE_FILE = "Prefixfy_blacklist.json"
BLACKLIST_MAX_BYTES = 1024 * 1024
BLACKLIST_MAX_IDS = 50000
BLACKLIST_KEY = "/yADUrDk9+uuX6ilxfB4WFqZpglH2kwVmN+LN07pNHE="
DEVICE_RECHECK_INTERVAL = 15.0
_ACCOUNT_ID_RE = re.compile(r"[0-9]{1,16}")
UPDATE_ALLOWED_HOSTS = ("raw.githubusercontent.com",)
UPDATE_MIRRORS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("https://cdn.jsdelivr.net/gh/sadatirnen/Prefixfy@main/", ("cdn.jsdelivr.net", "fastly.jsdelivr.net")),
)
REMOTE_FORCE_WAIT = 300
REMOTE_ATTEMPTS = 3
REMOTE_RETRY_PAUSE = 1.5
OTA_TOTAL_TIMEOUT = 180
OTA_VERIFY_ATTEMPTS = 3
UPDATE_PUBLIC_KEYS: Tuple[str, ...] = (
    "MIIBojANBgkqhkiG9w0BAQEFAAOCAY8AMIIBigKCAYEAnCpVgdegnDqZoaOi5H5EOpHiwY8jhprNdIT3jGVauC0Nijz2L/iauWaVxnEOwDT2tqp1tJQ6CrdQxOS/PKV/7QLtGtAseKdpo/4tZjHgx2N9TAPMVb+zK3oWYk+0+OcLFIUoczCa1aZuwaScBqQchmgTj4sQwIbhWDhquE2EtyiF1+6S6GCgV5KyJrqylt2pAcif5z3ixUV27MPzaPbQmuyU+3amsIXDxGcdTFwlHMg/ThFVz77bwV5fkfaNdJrZGDp3+FKSIfjN68v2scL6O9oYHhkDg4AEPUYQkJmNTMnqc0ABFSW9MGuGsMTa0MKNDMaBY5iP2aQmfzLddorBP4ovfOZRzZguFVltFGd44xVOE1w5ceL1WVH+pW+4HX0Ck5FWnHbttaQiLoxXuiIK+F927LLM0yCmKLZC9tcIfMdBXgcaHp1ZaKGOIVvRs8SRaVnQ2z51v3NtjHbakGKwcXit2JlgyKvrHPG2AQj8ci7tApB6BWYffsNkFM4bCBIlAgMBAAE=",
)
REMOTE_FRESH_TTL = 3600.0
REMOTE_MAX_AGE = 12 * 3600.0
REMOTE_RETRY_MIN = 60.0
REMOTE_RETRY_MAX = 30 * 60.0
REMOTE_IDLE_WAIT = 24 * 3600.0
REMOTE_MANUAL_COOLDOWN = 10.0
OTA_SLOT_TTL = 120.0
REMOTE_TIMEOUT = 15
REMOTE_TOTAL_TIMEOUT = 30
REMOTE_MAX_BYTES = 64 * 1024
OTA_STATE_FILE = ".pfx_ota"
OTA_SLOT_DIR = ".pfx_slot"
OTA_SLOT_FILE = "plugin.py"
OTA_SLOT_META = "slot.json"
OTA_SLOT_OLD = "plugin.old"
SLOT_STAGED = "staged"
SLOT_PREVIOUS = "previous"
OTA_DEFAULT_FILE = "prefixfy.py"
WIPE_MARKER_FILE = ".pfx_wipe"
WIPE_FINAL_FILE = ".pfx_wipe_final"
WIPE_FINAL_TTL = 300.0
DORMANT_FILE = ".pfx_dormant"
BLACKLIST_GUARD_FILE = ".pfx_bl"
WIPE_MARKER_TTL = 3600.0
WIPE_COOLDOWN_SEC = 10
OTA_FLAGS_MAX_AGE = 120.0
OTA_LOAD_TIMEOUT = 45.0
OTA_CONFIRM_SEC = 20.0
OTA_MAX_BOOTS = 3
OTA_BAD_LIMIT = 20
OTA_TIME_RE = re.compile(r"\s*([01]?[0-9]|2[0-3])\s*:\s*([0-5][0-9])\s*")
MASK_PLACEHOLDER = "[text]"
IGNORE_KINDS = ("code", "commands", "mentions", "links", "hashtags", "cashtags")
IGNORE_KEYS = tuple(f"ignore_{kind}" for kind in IGNORE_KINDS)
DEFAULT_SEPARATORS = "•, ·, —, ~, |"
LANGUAGE_MODES = (None, "ru", "en", "ja", "ko", "fr")
SETUP_STAGE_KEY = "Prefixfy_setup_stage"
SETUP_SEEN_KEY = "Prefixfy_setup_seen"
WELCOME_UNTIL_KEY = "Prefixfy_welcome_until"
WELCOME_SECONDS = 4 * 3600
UPDATED_UNTIL_KEY = "Prefixfy_updated_until"
UPDATED_BUILD_KEY = "Prefixfy_updated_build"
UPDATED_NOTES_KEY = "Prefixfy_updated_notes"
SETUP_UPDATE_AT_KEY = "Prefixfy_setup_update_at"
DEBUG_ENABLED_KEY = "Prefixfy_debug_enabled"
DEBUG_RECORDING_KEY = "Prefixfy_debug_recording"
DEBUG_DIR_NAME = "Prefixfy_debug"
DEBUG_LOG_NAME = "recording.log"
DEBUG_MAX_BYTES = 4 * 1024 * 1024
DEBUG_TAP_COUNT = 7
DEBUG_TAP_GAP = 0.3
SETUP_UPDATE_WINDOW = 3600
SETUP_STAGE_COUNT = 3
SETUP_DONE = SETUP_STAGE_COUNT + 1
MAX_STORE_JSON_BYTES = 2 * 1024 * 1024
MAX_ACCOUNT_PROFILES = 256
MAX_ACCOUNT_PRESETS = 32
STALE_TMP_AGE = 3600
IMPORT_TEMP_TTL = 3600
MAX_SEPARATOR_COUNT = 99
CAPTION_LIMIT = 1024
PREMIUM_CAPTION_LIMIT = 4096
MAX_CONFIG_NAME_LENGTH = 40
INTERNAL_SEND_TTL = 60
MAX_MESSAGE_ENTITIES = 100
EXPORT_TEMP_TTL = 3600
MAX_CAPTURED_EMOJI = 20
DEFAULT_EMOJI_FALLBACK = "⭐"
MAX_MASKS_IN_LIST = 20
MAX_STYLE_WORDS = 100
MAX_TAG_LINES = 50
MAX_CHAT_COUNTS = 2000
CHAT_COUNTS_KEY = "Prefixfy_chat_counts"
MAX_REGEX_EXCEPTIONS = 20
MAX_REGEX_LENGTH = 200
REGEX_TEXT_LIMIT = 1024
CHAT_TITLE_TTL = 60
CHAT_TITLE_CACHE_MAX = 64
DIALOG_KINDS_MAX = 256
SKIP_ONCE_TTL = 600
CHAT_KINDS = ("private", "group", "channel")
TAG_VALUE_LIMIT = 64
MAX_CONDITIONAL_MASKS = 20
COUNTER_KEY = "Prefixfy_message_count"
MAX_MASK_LENGTH = 1000
MESSAGE_LIMIT = 4096
MAX_SETTING_TEXT = 64 * 1024
MAX_REGEX_REPEATS = 8
REGEX_UNSAFE_REASON = "nested or too many repeats (the message check could hang)"
RANDOM_EMOJI = ("😀", "😎", "✨", "🌟", "💜", "🔥", "🍀", "🦋", "🌈", "⭐", "🎉", "🚀")
MASK_TAG_RE = re.compile(
    r"\[(date|time|datetime|time12|chat|id|weekday|weekday_short|year|year_short|month|monthname|day|week|yearday|"
    r"hour|minute|second|ampm|daypart|timestamp|tz|chattype|username|count|dice|random_emoji|emoji|reply|chatcount|battery|moon|line|quote|"
    r"weather(?::[\w .\-]{1,40})?|(?:since|until):\d{4}-\d{2}-\d{2}|countdown:\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2})?)\]",
    re.IGNORECASE,
)
_TAG_UNSAFE_RE = re.compile(r"[\[\]*_~|`\\\uE000-\uF8FF\s]+")
WEEKDAY_NAMES = {
    "ru": ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"),
    "en": ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
    "ja": ("月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"),
    "ko": ("월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"),
    "fr": ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"),
}

MONTH_NAMES = {
    "ru": ("Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"),
    "en": ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"),
    "ja": tuple(f"{n}月" for n in range(1, 13)),
    "ko": tuple(f"{n}월" for n in range(1, 13)),
    "fr": ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"),
}
WEEKDAY_SHORT = {
    "ru": ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"),
    "ja": ("月", "火", "水", "木", "金", "土", "日"),
    "ko": ("월", "화", "수", "목", "금", "토", "일"),
    "en": ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
    "fr": ("lun", "mar", "mer", "jeu", "ven", "sam", "dim"),
}
DAYPART_NAMES = {
    "ru": ("Утро", "День", "Вечер", "Ночь"),
    "en": ("Morning", "Afternoon", "Evening", "Night"),
    "ja": ("朝", "昼", "夕方", "夜"),
    "ko": ("아침", "낮", "저녁", "밤"),
    "fr": ("Matin", "Après-midi", "Soir", "Nuit"),
}
DAYPART_BOUNDS = ((5 * 60, 12 * 60), (12 * 60, 17 * 60), (17 * 60, 23 * 60), (23 * 60, 5 * 60))
DAYPART_ALIASES = {
    0: ("morning", "утро", "matin", "朝", "아침"),
    1: ("afternoon", "day", "день", "après-midi", "昼", "낮"),
    2: ("evening", "вечер", "soir", "夕方", "저녁"),
    3: ("night", "ночь", "nuit", "夜", "밤"),
}
DAYPART_BY_ALIAS = {alias: index for index, names in DAYPART_ALIASES.items() for alias in names}
_DAYPART_PATTERN = "|".join(re.escape(a) for a in sorted(DAYPART_BY_ALIAS, key=len, reverse=True))


def daypart_index(minutes: int) -> int:
    for index, (start, end) in enumerate(DAYPART_BOUNDS):
        if start < end:
            if start <= minutes < end:
                return index
        elif minutes >= start or minutes < end:
            return index
    return 3


MARKDOWN_STYLE_COUNT = 8
MARKDOWN_STYLE_VALUES = (0, 2, 3, 4, 5, 6, 7)
MARKDOWN_ENTITY_KINDS = frozenset({"Bold", "Italic", "Strike", "Spoiler", "Code", "Pre", "Blockquote"})
MARKDOWN_WRAP_KINDS = {2: "Bold", 3: "Italic", 4: "Strike", 5: "Spoiler", 6: "Code", 7: "Blockquote"}

SETTING_DEFAULTS = {
    "language": 0,
    "chat_scope_enabled": True,
    "process_message": True,
    "process_media": True,
    "process_article": True,
    "process_edit": False,
    "process_edit_message": True,
    "process_edit_media": True,
    "process_edit_article": True,
    "skip_once_on_edit": True,
    "mask": MASK_PLACEHOLDER,
    "markdown_enabled": True,
    "markdown_style": 0,
    "separator_enabled": False,
    "custom_emojis": DEFAULT_SEPARATORS,
    "emoji_count": 1,
    "separator_spaces": True,
    "separator_space_mode": 0,
    "separator_frequency": 4,
    "exceptions": "",
    "ignore_code": True,
    "ignore_commands": True,
    "ignore_mentions": True,
    "ignore_links": True,
    "ignore_hashtags": True,
    "ignore_cashtags": True,
    "ignore_emoji_only": True,
    "disabled_chats": "",
    "text_style_enabled": False,
    "text_style": 0,
    "text_style_random": False,
    "text_style_translit": False,
    "style_words": "",
    "tag_lines": "",
    "mask_rotation_enabled": False,
    "masks_list": "",
    "mask_rotation_mode": 0,
    "regex_exceptions": "",
    "conditional_masks": "",
    "chat_type_rules": "all",
    "attached_media_enabled": False,
    "attached_media_path": "",
    "attached_media_name": "",
    "attached_media_mime": "",
    "cute_enabled": False,
    "cute_kaomoji": False,
    "cute_sparkles": False,
    "cute_exclamations": False,
    "cute_punctuation": False,
    "cute_uwu_suffixes": False,
    "cute_actions": False,
    "cute_actions_newline": False,
    "cute_lowercase": False,
    "cute_uwu_speak": False,
    "cute_stutter": False,
    "cute_stretch": False,
    "cute_soft_sign": False,
    "cute_sentence_frequency": 2,
    "cute_word_frequency": 1,
    "cute_stretch_max": 0,
}

TRANSIENT_SETTING_DEFAULTS = {
    "capture_custom_emoji": False,
}

OTA_SETTING_DEFAULTS = {
    "ota_auto": False,
    "ota_mode": 0,
    "ota_action": 1,
    "ota_time": "04:00",
}

MEDIA_EXTENSIONS = frozenset({
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic", ".heif", ".avif",
    ".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v", ".3gp", ".mpeg", ".mpg",
})


class LocalizationManager:
    LANGUAGE_ITEMS = {
        "ru": ["Русский", "Английский", "Японский", "Корейский", "Французский"],
        "en": ["Russian", "English", "Japanese", "Korean", "French"],
        "ja": ["ロシア語", "英語", "日本語", "韓国語", "フランス語"],
        "ko": ["러시아어", "영어", "일본어", "한국어", "프랑스어"],
        "fr": ["Russe", "Anglais", "Japonais", "Coréen", "Français"],
    }

    STRINGS = {
        "ru": {
            "editor_empty_means_default": "Оставьте поле пустым и нажмите «Сохранить», чтобы вернуть значение по умолчанию.",
            "action_save": "Сохранить",
            "action_delete": "Удалить",
            "action_cancel": "Отмена",
            "action_create": "Создать",
            "action_apply": "Применить",
            "action_next": "Далее",
            "error_operation_failed": "Не удалось выполнить действие",
            "section_scope": "Где работает",
            "section_language": "Язык плагина",
            "section_configurations": "Конфигурации",
            "section_appearance": "Оформление текста",
            "section_general": "Основное",
            "section_about": "О плагине",
            "section_accounts": "Аккаунты",
            "section_updates": "Обновления и проверка",
            "section_cute": "Милые эффекты",
            "plugin_enable": "Режим чёрного списка",
            "plugin_enable_subtext": "Вкл: плагин работает везде, кроме чатов из списка. Выкл: только в чатах из списка (белый список).",
            "language": "Язык",
            "language_auto": "Язык как в Telegram",
            "language_auto_subtext": "Берётся язык интерфейса Telegram. Выключите, чтобы выбрать вручную.",
            "scope_message": "Сообщения",
            "scope_message_subtext": "Оформлять обычные текстовые сообщения.",
            "scope_media": "Подписи к медиа",
            "scope_media_subtext": "Оформлять подписи к фото, видео и файлам.",
            "scope_edit": "При редактировании",
            "scope_edit_subtext": "Оформлять отредактированные сообщения. Уже оформленный текст не меняется.",
            "skip_once_expired": "Пропуск истёк: следующее сообщение будет оформлено",
            "chat_config_menu": "Конфигурация для этого чата",
            "chat_config_auto": "Основная (с учётом расписания)",
            "chat_config_saved": "Конфигурация чата сохранена",
            "chat_config_reset": "Чат снова использует основную конфигурацию",
            "skip_once_menu": "Не оформлять следующее сообщение",
            "skip_once_on": "Следующее сообщение уйдёт без оформления",
            "skip_once_off": "Пропуск отменён",
            "chat_types": "Типы чатов",
            "chat_types_hint": "Оформлять только в чатах выбранных типов.",
            "chat_types_all": "Все чаты",
            "chat_types_none": "Выберите хотя бы один тип",
            "chat_type_private": "Личные",
            "chat_type_group": "Группы",
            "chat_type_channel": "Каналы",
            "scope_edit_message": "Редактирование текста",
            "scope_edit_message_subtext": "Оформлять обычные сообщения после редактирования.",
            "scope_edit_media": "Редактирование подписей",
            "scope_edit_media_subtext": "Оформлять подписи к медиа после редактирования.",
            "scope_article": "Статьи",
            "scope_article_subtext": "Оформлять текстовые блоки статей при отправке.",
            "scope_edit_article": "Редактирование статей",
            "scope_edit_article_subtext": "Оформлять статьи после редактирования.",
            "skip_once_on_edit": "Пропуск действует и на редактирование",
            "skip_once_on_edit_subtext": "Если включён пропуск, следующее редактирование в чате тоже обойдётся без оформления.",
            "mask": "Маска",
            "mask_text": "Текст маски",
            "markdown_style": "Стиль Markdown",
            "markdown_style_subtext": "Маркеры внутри маски или единый стиль для всей маски.",
            "markdown_style_pick": "Стиль",
            "md_manual": "Маркеры вручную",
            "md_bold": "Вся маска жирным",
            "md_italic": "Вся маска курсивом",
            "md_strike": "Вся маска зачёркнутой",
            "md_spoiler": "Вся маска под спойлером",
            "md_mono": "Вся маска моноширинной",
            "mask_rotation": "Ротация масок",
            "mask_rotation_subtext": "Брать маски из списка вместо основной. Маска чата важнее.",
            "masks_list": "Список масок",
            "masks_list_count": "Масок: {n}",
            "masks_list_empty": "По одной маске в строке",
            "masks_list_hint": "По одной маске в строке, в каждой ровно один [text].",
            "masks_list_invalid": "В каждой маске должен быть ровно один [text]",
            "masks_list_limit": "Не больше {n} масок",
            "mask_tags_hint": "Теги: [date], [time], [datetime], [chat], [id], [weekday], [year], [month], [day], [username], [count], [random_emoji], [hour], [minute], [second], [time12], [ampm], [daypart], [week], [yearday], [monthname], [weekday_short], [year_short], [timestamp], [tz], [chattype], [dice].\n[reply] — имя того, кому вы отвечаете; [chatcount] — номер вашего сообщения в этом чате; [battery] — заряд батареи; [moon] — фаза луны; [line] — случайная строка из списка; [since:2026-12-31] / [until:2026-12-31] — сколько дней прошло / осталось; [quote] — начало сообщения, на которое вы отвечаете; [countdown:2026-12-31 18:00] — сколько осталось до момента; [weather] / [weather:Париж] — температура с wttr.in (нужен интернет).",
            "mask_rotation_mode": "Порядок ротации",
            "mask_rotation_mode_random": "Случайно",
            "mask_rotation_mode_sequential": "По очереди",
            "mask_editor_title": "Маска",
            "mask_editor_hint": "[text] — текст сообщения, [text: ссылка] — текст сообщения со ссылкой.",
            "mask_invalid": "В маске должен быть ровно один [text]",
            "unsafe_text_rejected": "Текст с подменой направления (RTL), невидимыми или управляющими символами, Zalgo или слишком длинной цепочкой эмодзи не принимается",
            "mask_too_long": "Маска слишком длинная: не больше {n} символов",
            "mask_preview_sample": "Пример сообщения",
            "mask_preview_invalid": "Маска повреждена: нужен ровно один [text]",
            "conditional_masks": "Маски по содержимому",
            "conditional_masks_hint": "По одному правилу в строке: регулярное выражение => маска. Берётся маска первого правила, которому соответствует текст. В каждой маске ровно один [text].",
            "conditional_masks_count": "Правил: {n}",
            "conditional_masks_empty": "Своя маска для сообщений с нужным текстом",
            "conditional_masks_format": "Строка {n}: нужен формат «выражение => маска»",
            "md_quote": "Вся маска цитатой",
            "text_style": "Стиль текста",
            "text_style_random": "Случайный стиль",
            "text_style_random_subtext": "Новый стиль для каждого сообщения (кроме перевёрнутого).",
            "text_style_subtext": "Меняет только текст сообщения. Fancy, Bold, Gothic и Circled работают с латиницей, L33T — ещё и с кириллицей.",
            "text_style_enable": "Включить стиль текста",
            "text_style_translit": "Транслитерировать кириллицу",
            "text_style_translit_subtext": "Латинские стили будут работать и с русским, и с украинским текстом.",
            "style_words": "Стиль только для отдельных слов",
            "style_words_hint": "По одному слову в строке. Пустой список — стиль для всего текста.",
            "style_words_count": "Слов: {n}",
            "style_words_empty": "Весь текст",
            "style_words_limit": "Не больше {n} слов",
            "tag_lines": "Строки для [line]",
            "tag_lines_hint": "По одной строке в ряд, до 64 символов. Тег [line] подставит случайную.",
            "tag_lines_count": "Строк: {n}",
            "tag_lines_empty": "Строк пока нет",
            "tag_lines_limit": "Не больше {n} строк",
            "separator": "Разделитель",
            "separator_enable": "Включить разделитель",
            "separator_enable_subtext": "Вставлять свои разделители между словами.",
            "separator_set": "Набор разделителей",
            "separator_count": "Разделителей между словами",
            "separator_count_subtext": "Нажмите, чтобы изменить.",
            "separator_custom_title": "Свой набор",
            "separator_custom_message": "Введите разделители через запятую, например:\n•, ·, —, ~, |",
            "separator_preview_sample": "Пример текста для предпросмотра",
            "separator_frequency": "Частота разделителей",
            "separator_frequency_subtext": "Вероятность разделителя между соседними словами. 100% — между каждой парой.",
            "separator_spaces": "Пробелы вокруг разделителя",
            "separator_spaces_subtext": "Если выключено, разделитель ставится вплотную к словам: привет•как•дела.",
            "separator_space_mode": "Где ставить пробелы",
            "separator_space_both": "С обеих сторон",
            "separator_space_left": "Только слева",
            "separator_space_right": "Только справа",
            "cute_enabled": "Включить милые эффекты",
            "cute_enabled_subtext": "Каомодзи, UwU, действия и украшения. Ссылки, @упоминания, #хэштеги и код не меняются.",
            "cute_preview": "Предпросмотр",
            "section_debug": "Отладка",
            "debug_enabled": "Отладка включена",
            "debug_disabled": "Отладка выключена",
            "debug_start": "Начать запись",
            "debug_start_subtext": "Записывает все действия плагина: нажатия, изменения настроек, окна, уведомления, обработку сообщений (только длины, без текста) и служебный журнал. Изменённые значения настроек и id чатов попадают в журнал — проверьте его, прежде чем кому-то отправлять.",
            "debug_stop": "Остановить запись",
            "debug_recording": "Идёт запись · {amount}",
            "debug_log": "Журнал отладки",
            "debug_log_subtext": "{amount}. Нажмите, чтобы сохранить, удалить или продолжить запись.",
            "debug_amount": "строк: {lines}, {size}",
            "debug_actions_message": "Запись остановлена ({amount}). Что сделать с журналом?",
            "debug_to_saved": "Отправить в Избранное",
            "debug_to_device": "Сохранить на устройство",
            "debug_delete": "Удалить журнал",
            "debug_continue": "Продолжить запись",
            "debug_hide": "Скрыть отладку",
            "debug_hide_subtext": "Остановит запись и удалит журнал. То же самое — 7 быстрых нажатий на «Предпросмотр».",
            "debug_started": "Запись журнала начата",
            "debug_exported": "Журнал отладки сохранён",
            "debug_deleted": "Журнал отладки удалён",
            "debug_hidden": "Отладка скрыта",
            "debug_failed": "Не удалось выполнить действие с журналом",
            "cute_preview_sample": "Привет! Как дела? Сегодня отличный день.",
            "cute_preview_none": "Включите хотя бы один эффект. Нажмите, чтобы обновить.",
            "cute_preview_tap": "Нажмите, чтобы обновить.",
            "cute_sentence_frequency": "Частота эффектов для предложений",
            "cute_sentence_frequency_subtext": "Каомодзи, звёздочки, пунктуация, суффиксы и действия.",
            "cute_word_frequency": "Частота эффектов для слов",
            "cute_word_frequency_subtext": "Заикание, растянутые гласные и мягкий знак.",
            "cute_kaomoji": "Каомодзи в конце предложения (◕‿◕)",
            "cute_sparkles": "Звёздочки вокруг предложения ✨",
            "cute_exclamations": "Милые восклицания (! → !✨)",
            "cute_punctuation": "Милая пунктуация (. → .~, ? → ?✨)",
            "cute_uwu_suffixes": "UwU-окончания (nya~, owo)",
            "cute_actions": "Милые действия (*обнимает*)",
            "cute_actions_newline": "Действия с новой строки",
            "cute_lowercase": "Только строчные буквы",
            "cute_uwu_speak": "UwU-речь (р/л → в, r/l → w)",
            "cute_stutter": "Заикание (п-привет)",
            "cute_stretch": "Растягивать гласные (милооо)",
            "cute_stretch_max": "Насколько растягивать гласные",
            "cute_stretch_2x": "Вдвое (x2)",
            "cute_stretch_3x": "Втрое (x3)",
            "cute_soft_sign": "Мягкий знак в конце слов (котикь)",
            "cute_soft_sign_subtext": "Только для русских слов.",
            "regex_exceptions": "Исключения по regex",
            "regex_exceptions_hint": "По одному регулярному выражению в строке. Подходящие сообщения не оформляются.",
            "regex_exceptions_count": "Правил: {n}",
            "regex_exceptions_empty": "Для опытных пользователей",
            "regex_exceptions_invalid": "Ошибка в выражении: {error}",
            "regex_exceptions_limit": "Не больше {n} выражений, до {m} символов в каждом",
            "exceptions": "Исключения",
            "ignore_emoji_only": "Пропускать сообщения только из эмодзи",
            "ignore_emoji_only_subtext": "Сообщения, где одни эмодзи, не оформляются. На подписи к медиа это не влияет.",
            "exceptions_hint": "Сообщения, которые начинаются или заканчиваются этим текстом, не оформляются. По одному значению в строке.",
            "ignore_code": "Не трогать код",
            "ignore_code_subtext": "Блоки ``` и `встроенный код` остаются как есть.",
            "ignore_commands": "Не трогать команды",
            "ignore_commands_subtext": "Команды вроде /start или /help@bot остаются как есть. Сообщение, которое начинается с команды, не оформляется.",
            "ignore_mentions": "Не трогать упоминания",
            "ignore_mentions_subtext": "@username остаются как есть. Сообщение, которое начинается с упоминания, не оформляется.",
            "ignore_links": "Не трогать ссылки",
            "ignore_links_subtext": "Ссылки, адреса сайтов и e-mail остаются как есть. Сообщение из одной ссылки не оформляется.",
            "ignore_hashtags": "Не трогать #хэштеги",
            "ignore_hashtags_subtext": "#хэштеги остаются как есть.",
            "ignore_cashtags": "Не трогать $кэштеги",
            "ignore_cashtags_subtext": "$TON, $BTC и подобные остаются как есть.",
            "ignore_segments": "Что не трогать",
            "ignore_segments_hint": "Отметьте части сообщения, которые нужно оставлять как есть.",
            "ignore_segments_count": "Включено: {n} из {total}",
            "scope_targets": "Что оформлять",
            "scope_targets_hint": "Отметьте, где плагин применяет оформление.",
            "scope_edit_targets": "Настройки правки",
            "scope_edit_targets_hint": "Отметьте, что оформлять при редактировании сообщения.",
            "exceptions_chat_menu": "Исключения: добавить или убрать чат",
            "exceptions_chat_added": "Чат добавлен в исключения",
            "exceptions_chat_removed": "Чат убран из исключений",
            "exceptions_chat_now_off": "В этом чате Prefixfy больше не оформляет сообщения",
            "exceptions_chat_now_on": "В этом чате Prefixfy снова оформляет сообщения",
            "exceptions_chat_other_config": "Список изменён, но этот чат оформляется по другой конфигурации (привязка, расписание или настройки аккаунта)",
            "exceptions_count": "Правил: {n}, чатов: {m}",
            "capture_custom_emoji": "Получить код Premium Emoji",
            "capture_custom_emoji_enabled": "Отправьте сообщение с Premium Emoji — плагин пришлёт его код",
            "capture_custom_emoji_disabled": "Получение кода Premium Emoji отменено",
            "capture_custom_emoji_hint": "Premium Emoji в маске: (id|🙂), где 🙂 — обычный эмодзи для тех, у кого нет Premium. Код можно получить пунктом «Получить код Premium Emoji» в меню чата.",
            "schedule": "Расписание конфигураций",
            "schedule_empty": "Не задано",
            "schedule_count": "Правил: {n}",
            "schedule_message": "По одному правилу в строке: условие = конфигурация.\nУсловия: время ЧЧ:ММ-ЧЧ:ММ или часть суток (утро 05–12, день 12–17, вечер 17–23, ночь 23–05, диапазон вроде «утро-вечер»); дни (пн-пт, сб,вс, выходные, будни); дата ГГГГ-ММ-ДД, ДД.ММ.ГГГГ или ДД.ММ (каждый год), диапазон через «..»; тип чата (личные, группа, канал); «чат ID»; «аккаунт ID»; «случайно N%» (на каждое сообщение).\nУсловия соединяются словами и, или, не и скобками; без слова между ними подразумевается «и». «иначе» — правило на все остальные случаи. Можно писать и по-английски: and, or, not, else.\nПравила с датой важнее остальных, «иначе» проверяется последним, а среди равных выигрывает первое подходящее. Дни и дата у интервала через полночь считаются по дню его начала. На чаты со своей конфигурацией расписание не действует.",
            "schedule_hint": "22:00-07:00 = Ночная\n09:00-18:00 пн-пт = Рабочая\n(31.12 или 01.01) и не канал = Праздничная\nгруппа и вечер = Тихая\nчат -1001234567890 = Особая\nслучайно 20% = Весёлая\nиначе = Основная",
            "schedule_saved": "Расписание сохранено",
            "schedule_error": "Строка {n}: {reason}",
            "schedule_err_format": "нужен формат условие = конфигурация",
            "schedule_err_time": "неверное время",
            "schedule_err_days": "неверные дни недели",
            "schedule_err_config": "нет конфигурации «{name}»",
            "schedule_err_limit": "не больше {n} правил",
            "schedule_err_date": "неверная дата",
            "schedule_err_unknown": "не понимаю «{x}»",
            "schedule_err_parens": "скобки не сходятся",
            "schedule_err_deep": "слишком сложное условие",
            "schedule_err_random": "процент должен быть от 0 до 100",
            "schedule_err_size": "слишком много текста",
            "config_import_cancelled": "Импорт отменён",
            "config_import": "Импортировать",
            "config_export": "Экспортировать",
            "config_reset": "Сбросить к значениям по умолчанию",
            "config_reset_to_plugin": "Не учитывать импортированное: вернуть стандартные настройки плагина",
            "config_reset_to_plugin_unavailable": "Недоступно: конфигурация создана в плагине, сброс и так вернёт её к исходному виду.",
            "config_active": "Активная конфигурация",
            "config_new": "Новая конфигурация",
            "config_new_subtext": "Отдельный набор настроек. Станет активным сразу после создания.",
            "config_name_hint": "Название конфигурации",
            "config_new_source_title": "Основа новой конфигурации",
            "config_new_source_message": "Что взять за основу? Если ничего не выбрать, будут настройки по умолчанию.",
            "config_new_copy_current": "Скопировать настройки текущей конфигурации",
            "config_delete": "Удалить конфигурацию",
            "config_delete_confirm": "Удалить конфигурацию «{name}»?",
            "config_delete_none": "Нет неактивных конфигураций, которые можно удалить",
            "config_imported_name": "Импортированная конфигурация",
            "config_rename": "Переименовать конфигурацию",
            "config_rename_subtext": "Изменить название текущей конфигурации.",
            "config_name_invalid": "Введите название, которого ещё нет.",
            "config_name_taken": "Конфигурация с таким названием уже есть.",
            "config_deleted": "Удалено конфигураций: {n}",
            "config_delete_multi": "Удалить конфигурации",
            "config_delete_multi_subtext": "Удалить неактивные конфигурации. Активная останется.",
            "config_delete_multi_select": "Выберите неактивные конфигурации для удаления.",
            "config_import_new_name": "Название новой конфигурации",
            "config_parts_title": "Части конфигурации",
            "config_parts_message": "Выберите, какие части использовать (доступно: {n}).",
            "config_part_mask": "Маска",
            "config_part_separator": "Разделители",
            "config_part_exceptions": "Исключения и чаты",
            "config_part_exceptions_reset": "Исключения, чаты и область работы",
            "config_part_language": "Язык плагина",
            "config_part_media": "Медиа",
            "config_import_done": "Конфигурация импортирована",
            "config_import_take_name_title": "Название конфигурации",
            "config_import_take_name": "В файле указано название «{name}». Сейчас конфигурация называется «{current}».",
            "config_import_take_name_yes": "Взять «{name}»",
            "config_import_take_name_no": "Оставить «{current}»",
            "config_import_links_title": "Ссылки в конфигурации",
            "config_import_links_message": "В файле есть ссылки. Они могут попадать в ваши исходящие сообщения:",
            "config_import_links_more": "…и ещё {n}",
            "config_import_failed": "Не удалось импортировать конфигурацию",
            "config_import_locked": "Импорт станет доступен после начальной настройки.",
            "config_save_failed": "Не удалось сохранить конфигурацию",
            "config_export_done": "Конфигурация экспортирована",
            "config_export_failed": "Не удалось экспортировать конфигурацию",
            "config_export_destination_title": "Куда сохранить?",
            "config_export_to_saved": "В «Избранное» текущего аккаунта",
            "config_export_to_device": "В память устройства",
            "config_restored": "Выбранные значения сброшены",
            "config_parts_none": "Выберите хотя бы одну часть",
            "config_export_select": "Какие конфигурации экспортировать?",
            "config_export_select_subtext": "Можно выбрать до {n}. Для каждой потом откроется выбор частей. Если выбрано несколько, файлы сразу уйдут в «Избранное» текущего аккаунта.",
            "config_shared_marker": "общая",
            "config_export_parts_title": "Части: {name}",
            "config_export_parts_progress": "Конфигурация {i} из {n}",
            "config_export_limit": "Можно выбрать не больше {n} конфигураций",
            "config_export_none": "Выберите хотя бы одну конфигурацию",
            "config_export_done_multi": "Экспортировано конфигураций: {n}",
            "config_export_partial": "Экспортировано {ok} из {total}",
            "config_import_found_title": "Файл конфигурации",
            "config_import_found_contains": "Что импортировать:",
            "config_part_state_default": "по умолчанию",
            "config_part_state_absent": "нет в файле",
            "config_import_nothing": "В файле нечего импортировать: выбранные части отсутствуют или уже стоят по умолчанию",
            "config_import_skipped": "Пропущено, импортировать нечего: {parts}",
            "config_import_as_new": "Импортировать как новую конфигурацию",
            "config_export_encrypt": "Зашифровать паролем",
            "config_export_encrypting": "Шифрую файл…",
            "password_export_title": "Пароль для файла",
            "password_export_title_named": "Пароль для «{name}»",
            "password_export_message": "Файл будет зашифрован целиком: без пароля не видно даже, какие части в нём есть. Пароль нигде не сохраняется, и восстановить его нельзя.",
            "password_import_title": "Файл защищён паролем",
            "password_import_message": "Введите пароль, чтобы увидеть, какие части есть в файле.",
            "password_wrong": "Неверный пароль или файл повреждён. Попробуйте ещё раз.",
            "password_checking": "Проверяю пароль…",
            "password_hint": "Пароль",
            "password_repeat_hint": "Повторите пароль",
            "password_length": "От {min} до {max} символов",
            "password_mismatch": "Пароли не совпадают",
            "config_import_file_failed": "Не удалось открыть файл конфигурации",
            "config_import_invalid": "В файле нет выбранных частей или он повреждён.",
            "config_default_name": "Конфигурация по умолчанию",
            "config_numbered_name": "Конфигурация {n}",
            "config_actions_subtext": "Выбрать, какие части использовать",
            "config_part_schedule": "Привязки чатов и расписание",
            "config_part_cute": "Милые эффекты",
            "media_attachment": "Медиа",
            "media_attachment_enable": "Прикладывать медиа",
            "media_attachment_enable_subtext": "Отправлять выбранный файл вместе с каждым сообщением.",
            "media_file": "Файл",
            "media_file_none": "Файл не выбран",
            "media_import": "Выбрать медиа",
            "media_delete": "Удалить медиа",
            "media_delete_subtext": "Убрать выбранный файл из Prefixfy.",
            "media_delete_confirm": "Удалить медиа «{name}»? Файл будет удалён из Prefixfy без возможности восстановления.",
            "media_imported": "Медиа добавлено",
            "media_deleted": "Медиа удалено",
            "media_import_failed": "Не удалось добавить медиа",
            "media_delete_failed": "Не удалось удалить медиа",
            "account_mode": "Настройки по аккаунтам",
            "account_mode_subtext": "Свои настройки для каждого аккаунта. Пока вы их не меняли, у всех общие.",
            "account_target": "Какой аккаунт настраивать",
            "account_auto": "Авто (текущий аккаунт)",
            "account_common": "Общие (для всех)",
            "account_auto_now": "Сейчас выбран",
            "account_editing": "Вы настраиваете",
            "account_own": "свои настройки",
            "account_shared": "общие настройки",
            "account_common_hint": "общие настройки (для аккаунтов без своих)",
            "account_none": "аккаунт не определён",
            "account_reset": "Вернуть общие настройки",
            "account_reset_subtext": "Удалить собственные настройки этого аккаунта.",
            "account_reset_title": "Сброс настроек аккаунта",
            "account_reset_confirm": "Удалить собственные настройки этого аккаунта вместе с его конфигурациями? Аккаунт снова будет использовать общие.",
            "account_reset_button": "Сбросить",
            "account_reset_done": "Аккаунт снова использует общие настройки",
            "account_import_title": "Куда применить конфигурацию?",
            "account_import_all": "Ко всем аккаунтам",
            "account_import_common": "К общим (для аккаунтов без своих настроек)",
            "check_now": "Проверить сейчас",
            "check_now_subtext": "Проверить, что сборка плагина официальная.",
            "check_started": "Проверяю…",
            "check_confirm_title": "Проверить сборку?",
            "check_confirm_body": "Что произойдёт: плагин заново скачает данные проверки (манифест, чёрный список, профиль настроек) в обход кэша и убедится, что сборка официальная. Сохранённые данные заменяются только после успешной проверки.\n\nКогда это нужно: сборку не удалось подтвердить и функции приостановлены, вы только что обновили или переустановили плагин, или статус выглядит устаревшим.\n\nЭто безопасно: настройки и конфигурации не затрагиваются. Нужен интернет. Если GitHub не отвечает, плагин повторит запрос и попробует зеркало. Если проверка всё же не пройдёт, всё останется как было.",
            "check_confirm_yes": "Проверить",
            "check_ok": "Проверка пройдена",
            "check_failed": "Проверка не пройдена. Проверьте интернет и попробуйте ещё раз.",
            "ota_auto": "Автообновление",
            "ota_auto_subtext": "Плагин сам скачивает и устанавливает обновления, проверяя подпись и контрольные суммы.",
            "ota_mode": "Когда обновлять",
            "ota_mode_available": "Сразу после выхода",
            "ota_mode_time": "В выбранное время",
            "ota_action": "Что делать с обновлением",
            "ota_action_download": "Только скачать",
            "ota_action_install": "Скачать и установить",
            "ota_time": "Время обновления",
            "ota_time_subtext": "Время устройства в формате ЧЧ:ММ, например 04:00.",
            "ota_time_invalid": "Введите время в формате ЧЧ:ММ, например 04:00",
            "ota_disabled": "Обновления по воздуху отключены",
            "ota_disabled_subtext": "Разработчик временно отключил их. Установите новую версию вручную из репозитория.",
            "ota_installed": "Prefixfy {version} установлен. Перезапускаю…",
            "ota_restart_manual": "Prefixfy {version} установлен. Выключите и снова включите плагин, чтобы применить.",
            "ota_modified_found": "Файл плагина изменён. Устанавливаю официальную сборку {version}…",
            "ota_failed": "Не удалось обновить: {reason}",
            "ota_busy": "Обновление уже идёт",
            "ota_check_note": "Эта проверка не устанавливает новую версию: придёт уведомление, а установить её можно кнопкой «Скачать» под «Требуется обновление».",
            "ota_almost_ready": "Почти готово",
            "ota_almost_ready_subtext": "Версия {version} скачана. Осталось перезапустить плагин.",
            "ota_reload": "Перезапустить",
            "ota_reload_subtext": "Применить обновление и перезапустить плагин.",
            "ota_staged": "Prefixfy {version} скачан. Нажмите «Перезапустить».",
            "ota_download": "Скачать",
            "check_update_found": "Вышел Prefixfy {version}. Нажмите «Скачать» под «Требуется обновление».",
            "ota_download_subtext": "Версия {version}. Сначала покажем сведения об обновлении.",
            "ota_dl_title": "Обновление Prefixfy",
            "ota_dl_size": "Размер",
            "ota_dl_changelog": "Что нового",
            "ota_dl_changelog_none": "Разработчик не предоставил информацию",
            "ota_dl_confirm": "Скачать и установить",
            "ota_dl_warning": "В мобильной сети оператор может взять плату за трафик. Лучше подключиться к Wi-Fi.",
            "ota_unit_kb": "КБ",
            "ota_unit_mb": "МБ",
            "gate_update_required": "Требуется обновление",
            "gate_update_required_subtext": "Установите официальную сборку Prefixfy {version}. До этого плагин не оформляет сообщения.",
            "gate_verify_required": "Проверка не пройдена",
            "gate_verify_required_subtext": "Не удалось проверить сборку, оформление отключено. Проверьте интернет.",
            "gate_account_blocked": "Доступ запрещён",
            "gate_account_blocked_subtext": "Один из аккаунтов на устройстве в чёрном списке Prefixfy. Плагин отключён.",
            "about_plugin": "О плагине",
            "about_plugin_subtext": "Версия, сборка и статус проверки.",
            "about_title": "О Prefixfy",
            "about_version": "Версия",
            "about_build_date": "Дата сборки",
            "about_build_number": "Номер сборки за день",
            "about_serial": "Серийный номер",
            "about_build_label": "Полная метка сборки",
            "about_latest": "Последняя официальная сборка",
            "about_status": "Проверка",
            "about_unknown": "неизвестно",
            "about_note": "Сведения взяты из метки сборки в файле плагина.",
            "status_ok": "пройдена: сборка совпадает с официальным релизом",
            "status_pending": "ещё не проводилась",
            "status_soft": "не подтверждена: дополнительные функции приостановлены",
            "status_blacklisted": "отказано: аккаунт в чёрном списке",
            "status_no_key": "не пройдена: в сборке нет ключа обновлений",
            "status_integrity": "не подтверждена: не удалось прочитать файл плагина",
            "notice_ok": "OK",
            "status_outdated": "не пройдена: сборка устарела, вышла новая",
            "status_modified": "не пройдена: сборка изменена",
            "gate_modified": "Изменённая сборка",
            "gate_modified_subtext": "Файл Prefixfy отличается от официального релиза {version}. Плагин сам установит официальную сборку, а до этого оформление отключено.",
            "notice_verify_body": "Что случилось: эту сборку нельзя проверить — в ней нет действующего ключа для подписанного манифеста.\n\nЧто это значит: плагин не оформляет исходящие сообщения. Настройки сохранены.\n\nЧто делать: установите официальную сборку из репозитория.",
            "notice_soft_body": "Что случилось: Prefixfy не может подтвердить, что сборка официальная. Проверка подписанного манифеста или чёрного списка не завершилась: нет интернета, GitHub недоступен, последняя проверка слишком старая или не читается файл плагина.\n\nЧто приостановлено: все дополнительные функции — стили, Markdown, ротация и маски по содержимому, теги, расписание, конфигурации чатов, медиа, Premium Emoji, оформление при редактировании и импорт. Работает только базовая маска.\n\nЧто делать: проверьте интернет и нажмите «Проверить сейчас». После успешной проверки всё вернётся само.",
            "notice_account_body": "Что случилось: один из аккаунтов Telegram на этом устройстве в чёрном списке Prefixfy.\n\nЧто это значит: плагин на этом устройстве отключён. Настройки не меняются.\n\nЕсли это ошибка, свяжитесь с автором плагина.",
            "gate_soft": "Функции приостановлены",
            "gate_soft_subtext": "Сейчас не удаётся проверить сборку, поэтому работает только базовое оформление. Проверьте интернет — после успешной проверки всё вернётся.",
            "gate_bypass_note": "Эта функция не снимает блокировку.",
            "wipe_row": "Удалить данные",
            "wipe_row_subtext": "Стереть все данные плагина или полностью отказаться от него.",
            "wipe_title": "Удалить данные Prefixfy?",
            "wipe_body": "Будут удалены все данные плагина: конфигурации и настройки аккаунтов, общие настройки, медиа, импортированные файлы и кэш проверок. Плагин перезапустится и начнёт с мастера настройки, как после установки.\n\nЕсли плагин устарел, сначала установится последняя версия, а потом удалятся данные.\n\n«Отказаться от использования» дополнительно отключает плагин: останется только кнопка «Возобновить работу». Обновление в этом случае не скачивается.",
            "wipe_opt_out": "Отказаться от использования",
            "wipe_confirm_clean": "Все файлы и настройки плагина будут удалены. Плагин несколько раз перезапустится (это нормально) и начнёт с мастера настройки. Конфигурации и медиа пропадут безвозвратно — сначала экспортируйте то, что нужно сохранить.",
            "wipe_confirm_title": "Подтвердите удаление",
            "wipe_confirm_out": "Все файлы и настройки плагина будут удалены, после чего плагин отключится. Отменить это нельзя.",
            "wipe_confirm_btn": "Удалить",
            "wipe_started": "Готовлю удаление…",
            "wipe_started_multi": "Готовлю удаление… Плагин перезапустится несколько раз.",
            "wipe_halt": "Идёт очистка",
            "wipe_halt_subtext": "Плагин скоро перезапустится ещё раз и начнёт с чистого листа.",
            "wipe_updating": "Обновляю до {version}, потом удалю данные…",
            "wipe_reinstalling": "Переустанавливаю сборку {version}, потом удалю данные…",
            "wipe_update_failed": "Не удалось обновить плагин: {reason}. Ничего не удалено.",
            "wipe_restart_manual": "Выключите и снова включите плагин, чтобы завершить удаление.",
            "wipe_failed": "Не удалось подготовить удаление. Ничего не удалено.",
            "wipe_done": "Данные удалены, плагин начал с чистого листа",
            "resume_title": "Возобновить работу",
            "resume_subtext": "Prefixfy отключён и ничего не хранит. Нажмите, чтобы начать заново.",
            "resume_confirm_title": "Возобновить работу?",
            "resume_confirm_body": "Плагин запустится как после первой установки, с настройками по умолчанию.",
            "resume_btn": "Возобновить",
            "resume_done": "Prefixfy снова работает",
            "resume_failed": "Не удалось запустить плагин. Выключите и снова включите его.",
            "wipe_auto_reset_done": "Данные плагина были повреждены, поэтому он сброшен",
            "setup_step_1": "Шаг 1 из 3: язык",
            "setup_step_2": "Шаг 2 из 3: оформление",
            "setup_step_3": "Шаг 3 из 3: обновления",
            "setup_next": "Далее",
            "setup_next_subtext": "Перейти к шагу {step} из 3",
            "setup_back": "Назад",
            "setup_back_subtext": "Вернуться к шагу {step} из 3",
            "setup_finish": "Завершить настройку",
            "setup_finish_subtext": "Плагин проверит обновления, установит их при наличии и откроет все настройки.",
            "setup_checking": "Проверяю аккаунт…",
            "setup_checking_subtext": "Запрашиваю у сервера список блокировок. Это займёт несколько секунд.",
            "setup_done": "Начальная настройка завершена",
            "setup_almost_update": "Почти готово, осталось только обновить плагин",
            "setup_finish_update_subtext": "Доступна версия {version}: после проверки плагин обновится и откроет все настройки.",
            "welcome_banner": "Спасибо, что установили Prefixfy!",
            "welcome_banner_subtext": "Нажмите, чтобы узнать, что умеет плагин и с чего начать.",
            "welcome_title": "Добро пожаловать в Prefixfy",
            "welcome_body": "Prefixfy добавляет к вашим сообщениям маску: текст до или после сообщения, оформление и украшения.\n\nЧто умеет плагин:\n• маска с Markdown, стилями текста и разделителями\n• милые эффекты: каомодзи, UwU, украшения\n• медиа, которое прикладывается к сообщениям\n• исключения: чаты, где плагин не работает, или наоборот, только они\n• несколько конфигураций с импортом, экспортом и расписанием\n• свои настройки для каждого аккаунта\n\nС чего начать:\n1. В разделе «Оформление текста» задайте маску.\n2. В разделе «Где работает» выберите, что оформлять.\n3. Чтобы исключить чат или вернуть его, откройте меню в самом чате.\n\nВот и всё — просто пишите сообщения.",
            "welcome_ok": "Понятно",
            "updated_banner": "Обновление завершено",
            "updated_banner_subtext": "Нажмите для просмотра",
        },
        "en": {
            "editor_empty_means_default": "Leave the field empty and tap “Save” to restore the default value.",
            "action_save": "Save",
            "action_delete": "Delete",
            "action_cancel": "Cancel",
            "action_create": "Create",
            "action_apply": "Apply",
            "action_next": "Next",
            "error_operation_failed": "Something went wrong",
            "section_scope": "Where it works",
            "section_language": "Plugin language",
            "section_configurations": "Configurations",
            "section_appearance": "Text appearance",
            "section_general": "General",
            "section_about": "About",
            "section_accounts": "Accounts",
            "section_updates": "Updates and verification",
            "section_cute": "Cute effects",
            "plugin_enable": "Blacklist mode",
            "plugin_enable_subtext": "On: the plugin works everywhere except chats in the list. Off: only in chats from the list (whitelist).",
            "language": "Language",
            "language_auto": "Same as Telegram",
            "language_auto_subtext": "Uses the Telegram interface language. Turn off to choose manually.",
            "scope_message": "Messages",
            "scope_message_subtext": "Style regular text messages.",
            "scope_media": "Media captions",
            "scope_media_subtext": "Style captions of photos, videos and files.",
            "scope_edit": "When editing",
            "scope_edit_subtext": "Style edited messages. Text that is already styled stays as it is.",
            "skip_once_expired": "Skip expired: the next message will be styled",
            "chat_config_menu": "Configuration for this chat",
            "chat_config_auto": "Main (follows the schedule)",
            "chat_config_saved": "Chat configuration saved",
            "chat_config_reset": "The chat uses the main configuration again",
            "skip_once_menu": "Don’t style the next message",
            "skip_once_on": "The next message will be sent unstyled",
            "skip_once_off": "Skip cancelled",
            "chat_types": "Chat types",
            "chat_types_hint": "Style only in chats of the selected types.",
            "chat_types_all": "All chats",
            "chat_types_none": "Select at least one type",
            "chat_type_private": "Private",
            "chat_type_group": "Groups",
            "chat_type_channel": "Channels",
            "scope_edit_message": "Edited text",
            "scope_edit_message_subtext": "Style regular messages after editing.",
            "scope_edit_media": "Edited captions",
            "scope_edit_media_subtext": "Style media captions after editing.",
            "scope_article": "Articles",
            "scope_article_subtext": "Style article text blocks when sending.",
            "scope_edit_article": "Edited articles",
            "scope_edit_article_subtext": "Style articles after editing.",
            "skip_once_on_edit": "Skip also applies to edits",
            "skip_once_on_edit_subtext": "When a skip is active, the next edit in the chat is left unstyled too.",
            "mask": "Mask",
            "mask_text": "Mask text",
            "markdown_style": "Markdown style",
            "markdown_style_subtext": "Markers inside the mask or one style for the whole mask.",
            "markdown_style_pick": "Style",
            "md_manual": "Manual markers",
            "md_bold": "Whole mask bold",
            "md_italic": "Whole mask italic",
            "md_strike": "Whole mask strikethrough",
            "md_spoiler": "Whole mask as spoiler",
            "md_mono": "Whole mask monospace",
            "mask_rotation": "Mask rotation",
            "mask_rotation_subtext": "Use masks from the list instead of the main one. A chat mask takes priority.",
            "masks_list": "Mask list",
            "masks_list_count": "Masks: {n}",
            "masks_list_empty": "One mask per line",
            "masks_list_hint": "One mask per line, each with exactly one [text].",
            "masks_list_invalid": "Each mask needs exactly one [text]",
            "masks_list_limit": "No more than {n} masks",
            "mask_tags_hint": "Tags: [date], [time], [datetime], [chat], [id], [weekday], [year], [month], [day], [username], [count], [random_emoji], [hour], [minute], [second], [time12], [ampm], [daypart], [week], [yearday], [monthname], [weekday_short], [year_short], [timestamp], [tz], [chattype], [dice].\n[reply] — name of the person you reply to; [chatcount] — number of your message in this chat; [battery] — battery level; [moon] — moon phase; [line] — a random line from your list; [since:2026-12-31] / [until:2026-12-31] — days passed / left; [quote] — start of the message you reply to; [countdown:2026-12-31 18:00] — time left until a moment; [weather] / [weather:Paris] — temperature from wttr.in (needs internet).",
            "mask_rotation_mode": "Rotation order",
            "mask_rotation_mode_random": "Random",
            "mask_rotation_mode_sequential": "In turn",
            "mask_editor_title": "Mask",
            "mask_editor_hint": "[text] is your message, [text: link] is your message with a link.",
            "mask_invalid": "The mask needs exactly one [text]",
            "unsafe_text_rejected": "Text with direction overrides (RTL), invisible or control characters, Zalgo or an overly long emoji chain isn’t accepted",
            "mask_too_long": "The mask is too long: {n} characters max",
            "mask_preview_sample": "Sample message",
            "mask_preview_invalid": "The mask is broken: it needs exactly one [text]",
            "conditional_masks": "Masks by content",
            "conditional_masks_hint": "One rule per line: regular expression => mask. The mask of the first rule that matches the text is used. Each mask needs exactly one [text].",
            "conditional_masks_count": "Rules: {n}",
            "conditional_masks_empty": "A separate mask for messages with certain text",
            "conditional_masks_format": "Line {n}: expected “expression => mask”",
            "md_quote": "Whole mask as quote",
            "text_style": "Text style",
            "text_style_random": "Random style",
            "text_style_random_subtext": "A new style for every message (except upside-down).",
            "text_style_subtext": "Changes only the message text. Fancy, Bold, Gothic and Circled work with Latin letters, L33T also with Cyrillic.",
            "text_style_enable": "Enable text style",
            "text_style_translit": "Transliterate Cyrillic",
            "text_style_translit_subtext": "Latin styles will also work with Russian and Ukrainian text.",
            "style_words": "Style only certain words",
            "style_words_hint": "One word per line. An empty list styles the whole text.",
            "style_words_count": "Words: {n}",
            "style_words_empty": "Whole text",
            "style_words_limit": "No more than {n} words",
            "tag_lines": "Lines for [line]",
            "tag_lines_hint": "One line per row, up to 64 characters. The [line] tag inserts a random one.",
            "tag_lines_count": "Lines: {n}",
            "tag_lines_empty": "No lines yet",
            "tag_lines_limit": "No more than {n} lines",
            "separator": "Separator",
            "separator_enable": "Enable separator",
            "separator_enable_subtext": "Insert your own separators between words.",
            "separator_set": "Separator set",
            "separator_count": "Separators between words",
            "separator_count_subtext": "Tap to change.",
            "separator_custom_title": "Custom set",
            "separator_custom_message": "Enter separators separated by commas, for example:\n•, ·, —, ~, |",
            "separator_preview_sample": "Sample text for the preview",
            "separator_frequency": "Separator frequency",
            "separator_frequency_subtext": "Chance of a separator between two neighbouring words. 100% means between every pair.",
            "separator_spaces": "Spaces around the separator",
            "separator_spaces_subtext": "When off, the separator sits right next to the words: hi•how•are•you.",
            "separator_space_mode": "Where to put spaces",
            "separator_space_both": "On both sides",
            "separator_space_left": "Left only",
            "separator_space_right": "Right only",
            "cute_enabled": "Enable cute effects",
            "cute_enabled_subtext": "Kaomoji, UwU, actions and decorations. Links, @mentions, #hashtags and code stay unchanged.",
            "cute_preview": "Preview",
            "section_debug": "Debugging",
            "debug_enabled": "Debugging enabled",
            "debug_disabled": "Debugging disabled",
            "debug_start": "Start recording",
            "debug_start_subtext": "Records every plugin action: taps, setting changes, dialogs, notices, message processing (lengths only, no text) and the service log. Changed setting values and chat IDs end up in the log, so check it before sending it to anyone.",
            "debug_stop": "Stop recording",
            "debug_recording": "Recording · {amount}",
            "debug_log": "Debug log",
            "debug_log_subtext": "{amount}. Tap to save, delete or continue recording.",
            "debug_amount": "{lines} lines, {size}",
            "debug_actions_message": "Recording stopped ({amount}). What should be done with the log?",
            "debug_to_saved": "Send to Saved Messages",
            "debug_to_device": "Save to device",
            "debug_delete": "Delete log",
            "debug_continue": "Continue recording",
            "debug_hide": "Hide debugging",
            "debug_hide_subtext": "Stops recording and deletes the log. Same as 7 quick taps on “Preview”.",
            "debug_started": "Log recording started",
            "debug_exported": "Debug log saved",
            "debug_deleted": "Debug log deleted",
            "debug_hidden": "Debugging hidden",
            "debug_failed": "The log action failed",
            "cute_preview_sample": "Hi! How are you? It’s a great day today.",
            "cute_preview_none": "Turn on at least one effect. Tap to refresh.",
            "cute_preview_tap": "Tap to refresh.",
            "cute_sentence_frequency": "Sentence effect frequency",
            "cute_sentence_frequency_subtext": "Kaomoji, sparkles, punctuation, suffixes and actions.",
            "cute_word_frequency": "Word effect frequency",
            "cute_word_frequency_subtext": "Stutter, stretched vowels and the soft sign.",
            "cute_kaomoji": "Kaomoji at the end of a sentence (◕‿◕)",
            "cute_sparkles": "Sparkles around a sentence ✨",
            "cute_exclamations": "Cute exclamations (! → !✨)",
            "cute_punctuation": "Cute punctuation (. → .~, ? → ?✨)",
            "cute_uwu_suffixes": "UwU endings (nya~, owo)",
            "cute_actions": "Cute actions (*hugs*)",
            "cute_actions_newline": "Actions on a new line",
            "cute_lowercase": "Lowercase only",
            "cute_uwu_speak": "UwU speak (r/l → w, р/л → в)",
            "cute_stutter": "Stutter (h-hi)",
            "cute_stretch": "Stretch vowels (cuteee)",
            "cute_stretch_max": "How much to stretch vowels",
            "cute_stretch_2x": "Double (x2)",
            "cute_stretch_3x": "Triple (x3)",
            "cute_soft_sign": "Soft sign at the end of words (котикь)",
            "cute_soft_sign_subtext": "Russian words only.",
            "regex_exceptions": "Regex exceptions",
            "regex_exceptions_hint": "One regular expression per line. Matching messages are not styled.",
            "regex_exceptions_count": "Rules: {n}",
            "regex_exceptions_empty": "For advanced users",
            "regex_exceptions_invalid": "Invalid expression: {error}",
            "regex_exceptions_limit": "No more than {n} expressions, up to {m} characters each",
            "exceptions": "Exceptions",
            "ignore_emoji_only": "Skip emoji-only messages",
            "ignore_emoji_only_subtext": "Messages made only of emoji are not styled. Media captions are not affected.",
            "exceptions_hint": "Messages that start or end with this text are not styled. One value per line.",
            "ignore_code": "Leave code alone",
            "ignore_code_subtext": "``` blocks and `inline code` stay as they are.",
            "ignore_commands": "Leave commands alone",
            "ignore_commands_subtext": "Commands like /start or /help@bot stay as they are. A message that starts with a command is not styled.",
            "ignore_mentions": "Leave mentions alone",
            "ignore_mentions_subtext": "@usernames stay as they are. A message that starts with a mention is not styled.",
            "ignore_links": "Leave links alone",
            "ignore_links_subtext": "Links, website addresses and e-mails stay as they are. A message that is just a link is not styled.",
            "ignore_hashtags": "Leave #hashtags alone",
            "ignore_hashtags_subtext": "#hashtags stay as they are.",
            "ignore_cashtags": "Leave $cashtags alone",
            "ignore_cashtags_subtext": "$TON, $BTC and similar stay as they are.",
            "ignore_segments": "What to leave alone",
            "ignore_segments_hint": "Select the parts of a message that should stay as they are.",
            "ignore_segments_count": "On: {n} of {total}",
            "scope_targets": "What to style",
            "scope_targets_hint": "Select where the plugin applies styling.",
            "scope_edit_targets": "Edit settings",
            "scope_edit_targets_hint": "Select what to style when a message is edited.",
            "exceptions_chat_menu": "Exceptions: add or remove chat",
            "exceptions_chat_added": "Chat added to exceptions",
            "exceptions_chat_removed": "Chat removed from exceptions",
            "exceptions_chat_now_off": "Prefixfy no longer decorates messages in this chat",
            "exceptions_chat_now_on": "Prefixfy decorates messages in this chat again",
            "exceptions_chat_other_config": "The list was changed, but this chat follows another configuration (chat binding, schedule or account settings)",
            "exceptions_count": "Rules: {n}, chats: {m}",
            "capture_custom_emoji": "Get Premium Emoji code",
            "capture_custom_emoji_enabled": "Send a message with a Premium Emoji and the plugin will reply with its code",
            "capture_custom_emoji_disabled": "Premium Emoji code capture cancelled",
            "capture_custom_emoji_hint": "Premium Emoji in a mask: (id|🙂), where 🙂 is a regular emoji for people without Premium. Get the code with “Get Premium Emoji code” in the chat menu.",
            "schedule": "Configuration schedule",
            "schedule_empty": "Not set",
            "schedule_count": "Rules: {n}",
            "schedule_message": "One rule per line: condition = configuration.\nConditions: time HH:MM-HH:MM or a part of the day (morning 05–12, day 12–17, evening 17–23, night 23–05, or a range like “morning-evening”); days (mon-fri, sat,sun, weekend, weekdays); date YYYY-MM-DD, DD.MM.YYYY or DD.MM (every year), with “..” for a range; chat type (private, group, channel); “chat ID”; “account ID”; “random N%” (rolled for each message).\nCombine conditions with and, or, not and parentheses; with no word between them “and” is assumed. “else” is the rule for every other case. Words in Russian work too: и, или, не, иначе.\nDated rules beat the rest, “else” is checked last, and among equals the first match wins. Days and dates of an interval that crosses midnight refer to the day it started. Chats with their own configuration ignore the schedule.",
            "schedule_hint": "22:00-07:00 = Night\n09:00-18:00 mon-fri = Work\n(31.12 or 01.01) and not channel = Holiday\ngroup and evening = Quiet\nchat -1001234567890 = Special\nrandom 20% = Fun\nelse = Default",
            "schedule_saved": "Schedule saved",
            "schedule_error": "Line {n}: {reason}",
            "schedule_err_format": "expected condition = configuration",
            "schedule_err_time": "invalid time",
            "schedule_err_days": "invalid days of the week",
            "schedule_err_config": "no configuration named “{name}”",
            "schedule_err_limit": "no more than {n} rules",
            "schedule_err_date": "invalid date",
            "schedule_err_unknown": "can’t read “{x}”",
            "schedule_err_parens": "parentheses don’t match",
            "schedule_err_deep": "the condition is too complex",
            "schedule_err_random": "the percentage must be 0 to 100",
            "schedule_err_size": "too much text",
            "config_import_cancelled": "Import cancelled",
            "config_import": "Import",
            "config_export": "Export",
            "config_reset": "Reset to defaults",
            "config_reset_to_plugin": "Ignore imported values: use the plugin’s standard settings",
            "config_reset_to_plugin_unavailable": "Not available: this configuration was created in the plugin, so a reset already returns it to its original state.",
            "config_active": "Active configuration",
            "config_new": "New configuration",
            "config_new_subtext": "A separate set of settings. It becomes active right after it’s created.",
            "config_name_hint": "Configuration name",
            "config_new_source_title": "Base for the new configuration",
            "config_new_source_message": "What should it start from? If you select nothing, default settings are used.",
            "config_new_copy_current": "Copy the current configuration’s settings",
            "config_delete": "Delete configuration",
            "config_delete_confirm": "Delete the configuration “{name}”?",
            "config_delete_none": "There are no inactive configurations to delete",
            "config_imported_name": "Imported configuration",
            "config_rename": "Rename configuration",
            "config_rename_subtext": "Change the name of the current configuration.",
            "config_name_invalid": "Enter a name that isn’t used yet.",
            "config_name_taken": "A configuration with this name already exists.",
            "config_deleted": "Configurations deleted: {n}",
            "config_delete_multi": "Delete configurations",
            "config_delete_multi_subtext": "Delete inactive configurations. The active one stays.",
            "config_delete_multi_select": "Select the inactive configurations to delete.",
            "config_import_new_name": "Name of the new configuration",
            "config_parts_title": "Configuration parts",
            "config_parts_message": "Choose which parts to use ({n} available).",
            "config_part_mask": "Mask",
            "config_part_separator": "Separators",
            "config_part_exceptions": "Exceptions and chats",
            "config_part_exceptions_reset": "Exceptions, chats and scope",
            "config_part_language": "Plugin language",
            "config_part_media": "Media",
            "config_import_done": "Configuration imported",
            "config_import_take_name_title": "Configuration name",
            "config_import_take_name": "The file contains the name “{name}”. The current configuration is called “{current}”.",
            "config_import_take_name_yes": "Use “{name}”",
            "config_import_take_name_no": "Keep “{current}”",
            "config_import_links_title": "Links in this configuration",
            "config_import_links_message": "The file contains links. They may end up in your outgoing messages:",
            "config_import_links_more": "…and {n} more",
            "config_import_failed": "Couldn’t import the configuration",
            "config_import_locked": "Import becomes available after the initial setup.",
            "config_save_failed": "Couldn’t save the configuration",
            "config_export_done": "Configuration exported",
            "config_export_failed": "Couldn’t export the configuration",
            "config_export_destination_title": "Where to save?",
            "config_export_to_saved": "To Saved Messages of the current account",
            "config_export_to_device": "To device storage",
            "config_restored": "Selected values reset",
            "config_parts_none": "Select at least one part",
            "config_export_select": "Which configurations to export?",
            "config_export_select_subtext": "You can select up to {n}. For each one you’ll then choose the parts. If you select several, the files go straight to Saved Messages of the current account.",
            "config_shared_marker": "shared",
            "config_export_parts_title": "Parts: {name}",
            "config_export_parts_progress": "Configuration {i} of {n}",
            "config_export_limit": "You can select no more than {n} configurations",
            "config_export_none": "Select at least one configuration",
            "config_export_done_multi": "Configurations exported: {n}",
            "config_export_partial": "Exported {ok} of {total}",
            "config_import_found_title": "Configuration file",
            "config_import_found_contains": "What to import:",
            "config_part_state_default": "default",
            "config_part_state_absent": "not in file",
            "config_import_nothing": "Nothing to import: the selected parts are missing from the file or already at their defaults",
            "config_import_skipped": "Skipped, nothing to import: {parts}",
            "config_import_as_new": "Import as a new configuration",
            "config_export_encrypt": "Encrypt with a password",
            "config_export_encrypting": "Encrypting the file…",
            "password_export_title": "File password",
            "password_export_title_named": "Password for “{name}”",
            "password_export_message": "The whole file is encrypted: without the password not even its list of parts is visible. The password is not stored anywhere and cannot be recovered.",
            "password_import_title": "Password-protected file",
            "password_import_message": "Enter the password to see which parts the file contains.",
            "password_wrong": "Wrong password or damaged file. Try again.",
            "password_checking": "Checking the password…",
            "password_hint": "Password",
            "password_repeat_hint": "Repeat the password",
            "password_length": "{min} to {max} characters",
            "password_mismatch": "The passwords do not match",
            "config_import_file_failed": "Couldn’t open the configuration file",
            "config_import_invalid": "The file has none of the selected parts or is damaged.",
            "config_default_name": "Default configuration",
            "config_numbered_name": "Configuration {n}",
            "config_actions_subtext": "Choose which parts to use",
            "config_part_schedule": "Chat bindings and schedule",
            "config_part_cute": "Cute effects",
            "media_attachment": "Media",
            "media_attachment_enable": "Attach media",
            "media_attachment_enable_subtext": "Send the selected file with every message.",
            "media_file": "File",
            "media_file_none": "No file selected",
            "media_import": "Choose media",
            "media_delete": "Delete media",
            "media_delete_subtext": "Remove the selected file from Prefixfy.",
            "media_delete_confirm": "Delete the media “{name}”? The file will be removed from Prefixfy for good.",
            "media_imported": "Media added",
            "media_deleted": "Media deleted",
            "media_import_failed": "Couldn’t add the media",
            "media_delete_failed": "Couldn’t delete the media",
            "account_mode": "Per-account settings",
            "account_mode_subtext": "Separate settings for each account. Until you change them, all accounts share the same ones.",
            "account_target": "Account to configure",
            "account_auto": "Auto (current account)",
            "account_common": "Shared (for everyone)",
            "account_auto_now": "Currently selected",
            "account_editing": "You are configuring",
            "account_own": "own settings",
            "account_shared": "shared settings",
            "account_common_hint": "shared settings (for accounts without their own)",
            "account_none": "account not detected",
            "account_reset": "Return to shared settings",
            "account_reset_subtext": "Delete this account’s own settings.",
            "account_reset_title": "Reset account settings",
            "account_reset_confirm": "Delete this account’s own settings together with its configurations? The account will use the shared ones again.",
            "account_reset_button": "Reset",
            "account_reset_done": "The account uses the shared settings again",
            "account_import_title": "Where to apply the configuration?",
            "account_import_all": "To all accounts",
            "account_import_common": "To shared (accounts without their own settings)",
            "check_now": "Check now",
            "check_now_subtext": "Make sure the plugin build is official.",
            "check_started": "Checking…",
            "check_confirm_title": "Check the build?",
            "check_confirm_body": "What happens: the plugin downloads the verification data (manifest, blacklist, settings profile) again, bypassing the cache, and makes sure the build is official. Saved data is replaced only after a successful check.\n\nWhen you need it: the build couldn’t be confirmed and features are paused, you have just updated or reinstalled the plugin, or the status looks out of date.\n\nIt’s safe: settings and configurations are not touched. Internet is required. If GitHub doesn’t respond, the plugin retries and tries a mirror. If the check still fails, everything stays as it was.",
            "check_confirm_yes": "Check",
            "check_ok": "Check passed",
            "check_failed": "Check failed. Check your connection and try again.",
            "ota_auto": "Auto-update",
            "ota_auto_subtext": "The plugin downloads and installs updates itself, verifying the signature and checksums.",
            "ota_mode": "When to update",
            "ota_mode_available": "As soon as released",
            "ota_mode_time": "At a chosen time",
            "ota_action": "What to do with an update",
            "ota_action_download": "Download only",
            "ota_action_install": "Download and install",
            "ota_time": "Update time",
            "ota_time_subtext": "Device time as HH:MM, for example 04:00.",
            "ota_time_invalid": "Enter the time as HH:MM, for example 04:00",
            "ota_disabled": "Over-the-air updates are off",
            "ota_disabled_subtext": "The developer has turned them off for now. Install the new version manually from the repository.",
            "ota_installed": "Prefixfy {version} installed. Restarting…",
            "ota_restart_manual": "Prefixfy {version} installed. Turn the plugin off and on again to apply it.",
            "ota_modified_found": "The plugin file was modified. Installing the official build {version}…",
            "ota_failed": "Update failed: {reason}",
            "ota_busy": "An update is already in progress",
            "ota_check_note": "This check doesn’t install a new version: you’ll get a notice, and you can install it with “Download” under “Update required”.",
            "ota_almost_ready": "Almost ready",
            "ota_almost_ready_subtext": "Version {version} is downloaded. Just restart the plugin.",
            "ota_reload": "Restart",
            "ota_reload_subtext": "Apply the update and restart the plugin.",
            "ota_staged": "Prefixfy {version} downloaded. Tap “Restart”.",
            "ota_download": "Download",
            "check_update_found": "Prefixfy {version} is out. Tap “Download” under “Update required”.",
            "ota_download_subtext": "Version {version}. Update details come first.",
            "ota_dl_title": "Prefixfy update",
            "ota_dl_size": "Size",
            "ota_dl_changelog": "What’s new",
            "ota_dl_changelog_none": "The developer hasn’t provided any information",
            "ota_dl_confirm": "Download and install",
            "ota_dl_warning": "On mobile data your carrier may charge for traffic. Wi-Fi is better.",
            "ota_unit_kb": "KB",
            "ota_unit_mb": "MB",
            "gate_update_required": "Update required",
            "gate_update_required_subtext": "Install the official Prefixfy {version} build. Until then the plugin doesn’t style messages.",
            "gate_verify_required": "Check failed",
            "gate_verify_required_subtext": "The build couldn’t be verified, so styling is off. Check your connection.",
            "gate_account_blocked": "Access denied",
            "gate_account_blocked_subtext": "One of the accounts on this device is on the Prefixfy blacklist. The plugin is disabled.",
            "about_plugin": "About the plugin",
            "about_plugin_subtext": "Version, build and verification status.",
            "about_title": "About Prefixfy",
            "about_version": "Version",
            "about_build_date": "Build date",
            "about_build_number": "Build number of the day",
            "about_serial": "Serial number",
            "about_build_label": "Full build label",
            "about_latest": "Latest official build",
            "about_status": "Verification",
            "about_unknown": "unknown",
            "about_note": "These details come from the build label in the plugin file.",
            "status_ok": "passed: the build matches the official release",
            "status_pending": "not run yet",
            "status_soft": "not confirmed: optional features are paused",
            "status_blacklisted": "denied: an account is blacklisted",
            "status_no_key": "failed: this build has no update key",
            "status_integrity": "not confirmed: the plugin file couldn’t be read",
            "notice_ok": "OK",
            "status_outdated": "failed: the build is outdated, a new one is out",
            "status_modified": "failed: the build was modified",
            "gate_modified": "Modified build",
            "gate_modified_subtext": "The Prefixfy file differs from the official {version} release. The plugin will install the official build itself; until then styling is off.",
            "notice_verify_body": "What happened: this build can’t be verified — it has no valid key for the signed manifest.\n\nWhat it means: the plugin doesn’t style outgoing messages. Your settings are kept.\n\nWhat to do: install the official build from the repository.",
            "notice_soft_body": "What happened: Prefixfy can’t confirm that the build is official. The check of the signed manifest or the blacklist didn’t finish: no internet, GitHub is unreachable, the last check is too old or the plugin file can’t be read.\n\nWhat’s paused: all optional features — text styles, Markdown, mask rotation and masks by content, tags, schedule, chat configurations, media, Premium Emoji, styling of edits and import. Only the basic mask works.\n\nWhat to do: check your connection and tap “Check now”. Everything comes back on its own after a successful check.",
            "notice_account_body": "What happened: one of the Telegram accounts on this device is on the Prefixfy blacklist.\n\nWhat it means: the plugin is disabled on this device. Your settings are not changed.\n\nIf you think this is a mistake, contact the plugin author.",
            "gate_soft": "Features paused",
            "gate_soft_subtext": "The build can’t be verified right now, so only basic styling works. Check your connection — everything comes back after a successful check.",
            "gate_bypass_note": "This feature doesn’t lift the block.",
            "wipe_row": "Delete data",
            "wipe_row_subtext": "Erase all plugin data or stop using the plugin altogether.",
            "wipe_title": "Delete Prefixfy data?",
            "wipe_body": "All plugin data will be deleted: configurations and account settings, shared settings, media, imported files and the verification cache. The plugin restarts and begins with the setup wizard, just like after installation.\n\nIf the plugin is outdated, the latest version is installed first, and then the data is deleted.\n\n“Stop using the plugin” also disables it: only the “Resume” button remains. No update is downloaded in this case.",
            "wipe_opt_out": "Stop using the plugin",
            "wipe_confirm_clean": "All plugin files and settings will be deleted. The plugin restarts a few times (that’s normal) and begins with the setup wizard. Configurations and media will be lost for good — export what you want to keep first.",
            "wipe_confirm_title": "Confirm deletion",
            "wipe_confirm_out": "All plugin files and settings will be deleted, and then the plugin turns off. This can’t be undone.",
            "wipe_confirm_btn": "Delete",
            "wipe_started": "Preparing deletion…",
            "wipe_started_multi": "Preparing deletion… The plugin will restart a few times.",
            "wipe_halt": "Cleaning up",
            "wipe_halt_subtext": "The plugin will restart once more and start from scratch.",
            "wipe_updating": "Updating to {version}, then deleting data…",
            "wipe_reinstalling": "Reinstalling build {version}, then deleting data…",
            "wipe_update_failed": "Couldn’t update the plugin: {reason}. Nothing was deleted.",
            "wipe_restart_manual": "Turn the plugin off and on again to finish the deletion.",
            "wipe_failed": "Couldn’t prepare the deletion. Nothing was deleted.",
            "wipe_done": "Data deleted, the plugin started from scratch",
            "resume_title": "Resume",
            "resume_subtext": "Prefixfy is off and keeps no data. Tap to start over.",
            "resume_confirm_title": "Resume Prefixfy?",
            "resume_confirm_body": "The plugin starts as if freshly installed, with default settings.",
            "resume_btn": "Resume",
            "resume_done": "Prefixfy is working again",
            "resume_failed": "Couldn’t start the plugin. Turn it off and on again.",
            "wipe_auto_reset_done": "Plugin data was damaged, so the plugin was reset",
            "setup_step_1": "Step 1 of 3: language",
            "setup_step_2": "Step 2 of 3: appearance",
            "setup_step_3": "Step 3 of 3: updates",
            "setup_next": "Next",
            "setup_next_subtext": "Go to step {step} of 3",
            "setup_back": "Back",
            "setup_back_subtext": "Back to step {step} of 3",
            "setup_finish": "Finish setup",
            "setup_finish_subtext": "The plugin checks for updates, installs them if there are any and opens all settings.",
            "setup_checking": "Checking the account…",
            "setup_checking_subtext": "Requesting the blacklist from the server. This takes a few seconds.",
            "setup_done": "Initial setup complete",
            "setup_almost_update": "Almost done, only the plugin update is left",
            "setup_finish_update_subtext": "Version {version} is available: after the check the plugin updates itself and opens all settings.",
            "welcome_banner": "Thanks for installing Prefixfy!",
            "welcome_banner_subtext": "Tap to see what the plugin can do and how to start.",
            "welcome_title": "Welcome to Prefixfy",
            "welcome_body": "Prefixfy adds a mask to your messages: text before or after the message, styling and decorations.\n\nWhat it can do:\n• a mask with Markdown, text styles and separators\n• cute effects: kaomoji, UwU, decorations\n• media attached to your messages\n• exceptions: chats where the plugin is off, or only those chats\n• several configurations with import, export and a schedule\n• separate settings for each account\n\nGetting started:\n1. Set your mask in “Text appearance”.\n2. Choose what to style in “Where it works”.\n3. To exclude a chat or bring it back, open the menu inside that chat.\n\nThat’s it — just write messages.",
            "welcome_ok": "Got it",
            "updated_banner": "Update complete",
            "updated_banner_subtext": "Tap to view",
        },
        "ja": {
            "editor_empty_means_default": "空欄のまま「保存」をタップすると、既定値に戻ります。",
            "action_save": "保存",
            "action_delete": "削除",
            "action_cancel": "キャンセル",
            "action_create": "作成",
            "action_apply": "適用",
            "action_next": "次へ",
            "error_operation_failed": "操作を完了できませんでした",
            "section_scope": "適用範囲",
            "section_language": "プラグインの言語",
            "section_configurations": "設定セット",
            "section_appearance": "テキストの装飾",
            "section_general": "基本",
            "section_about": "プラグインについて",
            "section_accounts": "アカウント",
            "section_updates": "アップデートと検証",
            "section_cute": "かわいいエフェクト",
            "plugin_enable": "ブラックリストモード",
            "plugin_enable_subtext": "オン：リスト内のチャット以外のすべてで動作。オフ：リスト内のチャットだけで動作（ホワイトリスト）。",
            "language": "言語",
            "language_auto": "Telegram と同じ言語",
            "language_auto_subtext": "Telegram の表示言語を使います。手動で選ぶ場合はオフにしてください。",
            "scope_message": "メッセージ",
            "scope_message_subtext": "通常のテキストメッセージを装飾します。",
            "scope_media": "メディアのキャプション",
            "scope_media_subtext": "写真・動画・ファイルのキャプションを装飾します。",
            "scope_edit": "編集時",
            "scope_edit_subtext": "編集したメッセージを装飾します。装飾済みのテキストはそのままです。",
            "skip_once_expired": "スキップの期限が切れました。次のメッセージは装飾されます",
            "chat_config_menu": "このチャットの設定セット",
            "chat_config_auto": "メイン（スケジュールに従う）",
            "chat_config_saved": "チャットの設定セットを保存しました",
            "chat_config_reset": "このチャットはメインの設定セットに戻りました",
            "skip_once_menu": "次のメッセージを装飾しない",
            "skip_once_on": "次のメッセージは装飾なしで送信されます",
            "skip_once_off": "スキップを取り消しました",
            "chat_types": "チャットの種類",
            "chat_types_hint": "選んだ種類のチャットでだけ装飾します。",
            "chat_types_all": "すべてのチャット",
            "chat_types_none": "少なくとも 1 つ選んでください",
            "chat_type_private": "個人チャット",
            "chat_type_group": "グループ",
            "chat_type_channel": "チャンネル",
            "scope_edit_message": "テキストの編集",
            "scope_edit_message_subtext": "編集後の通常メッセージを装飾します。",
            "scope_edit_media": "キャプションの編集",
            "scope_edit_media_subtext": "編集後のメディアのキャプションを装飾します。",
            "scope_article": "記事",
            "scope_article_subtext": "送信時に記事のテキストブロックを装飾します。",
            "scope_edit_article": "記事の編集",
            "scope_edit_article_subtext": "編集後の記事を装飾します。",
            "skip_once_on_edit": "スキップを編集にも適用",
            "skip_once_on_edit_subtext": "スキップが有効なとき、チャットでの次の編集も装飾しません。",
            "mask": "マスク",
            "mask_text": "マスクのテキスト",
            "markdown_style": "Markdown のスタイル",
            "markdown_style_subtext": "マスク内のマーカーを使うか、マスク全体に 1 つのスタイルを付けます。",
            "markdown_style_pick": "スタイル",
            "md_manual": "手動マーカー",
            "md_bold": "マスク全体を太字",
            "md_italic": "マスク全体を斜体",
            "md_strike": "マスク全体を取り消し線",
            "md_spoiler": "マスク全体をスポイラー",
            "md_mono": "マスク全体を等幅",
            "mask_rotation": "マスクのローテーション",
            "mask_rotation_subtext": "メインのマスクの代わりにリストのマスクを使います。チャットのマスクが優先されます。",
            "masks_list": "マスクのリスト",
            "masks_list_count": "マスク：{n}",
            "masks_list_empty": "1 行に 1 つのマスク",
            "masks_list_hint": "1 行に 1 つのマスク。どれにも [text] をちょうど 1 つ入れてください。",
            "masks_list_invalid": "各マスクには [text] がちょうど 1 つ必要です",
            "masks_list_limit": "マスクは {n} 個まで",
            "mask_tags_hint": "タグ：[date]、[time]、[datetime]、[chat]、[id]、[weekday]、[year]、[month]、[day]、[username]、[count]、[random_emoji]、[hour]、[minute]、[second]、[time12]、[ampm]、[daypart]、[week]、[yearday]、[monthname]、[weekday_short]、[year_short]、[timestamp]、[tz]、[chattype]、[dice]。\n[reply] — 返信相手の名前、[chatcount] — このチャットでのあなたのメッセージ番号、[battery] — バッテリー残量、[moon] — 月の満ち欠け、[line] — リストからランダムな 1 行、[since:2026-12-31] / [until:2026-12-31] — 経過日数 / 残り日数、[quote] — 返信先メッセージの冒頭、[countdown:2026-12-31 18:00] — 指定の時刻までの残り時間、[weather] / [weather:Paris] — wttr.in の気温（インターネットが必要）。",
            "mask_rotation_mode": "ローテーションの順番",
            "mask_rotation_mode_random": "ランダム",
            "mask_rotation_mode_sequential": "順番に",
            "mask_editor_title": "マスク",
            "mask_editor_hint": "[text] はメッセージ本文、[text: リンク] はリンク付きの本文です。",
            "mask_invalid": "マスクには [text] がちょうど 1 つ必要です",
            "unsafe_text_rejected": "文字方向の上書き（RTL）、不可視文字・制御文字、Zalgo、極端に長い絵文字の連なりを含むテキストは使用できません",
            "mask_too_long": "マスクが長すぎます（{n} 文字まで）",
            "mask_preview_sample": "メッセージの例",
            "mask_preview_invalid": "マスクが壊れています。[text] がちょうど 1 つ必要です",
            "conditional_masks": "内容に応じたマスク",
            "conditional_masks_hint": "1 行に 1 つのルール：正規表現 => マスク。テキストに一致した最初のルールのマスクが使われます。各マスクには [text] がちょうど 1 つ必要です。",
            "conditional_masks_count": "ルール：{n}",
            "conditional_masks_empty": "特定のテキストを含むメッセージに別のマスク",
            "conditional_masks_format": "{n} 行目：「式 => マスク」の形式で入力してください",
            "md_quote": "マスク全体を引用",
            "text_style": "テキストのスタイル",
            "text_style_random": "ランダムなスタイル",
            "text_style_random_subtext": "メッセージごとに新しいスタイル（逆さま以外）。",
            "text_style_subtext": "変わるのはメッセージ本文だけです。Fancy・Bold・Gothic・Circled はラテン文字、L33T はキリル文字にも対応します。",
            "text_style_enable": "テキストのスタイルを有効にする",
            "text_style_translit": "キリル文字を翻字",
            "text_style_translit_subtext": "ロシア語やウクライナ語のテキストにもラテン文字のスタイルが使えます。",
            "style_words": "特定の単語だけにスタイル",
            "style_words_hint": "1 行に 1 単語。空のままならテキスト全体に適用します。",
            "style_words_count": "単語：{n}",
            "style_words_empty": "テキスト全体",
            "style_words_limit": "単語は {n} 個まで",
            "tag_lines": "[line] 用の行",
            "tag_lines_hint": "1 行に 1 つ、64 文字まで。[line] タグにはランダムな 1 行が入ります。",
            "tag_lines_count": "行：{n}",
            "tag_lines_empty": "まだ行がありません",
            "tag_lines_limit": "行は {n} 個まで",
            "separator": "区切り文字",
            "separator_enable": "区切り文字を有効にする",
            "separator_enable_subtext": "単語の間に好きな区切り文字を入れます。",
            "separator_set": "区切り文字のセット",
            "separator_count": "単語間の区切り文字の数",
            "separator_count_subtext": "タップして変更します。",
            "separator_custom_title": "カスタムセット",
            "separator_custom_message": "区切り文字をカンマで区切って入力してください。例：\n•, ·, —, ~, |",
            "separator_preview_sample": "プレビュー用のテキスト例",
            "separator_frequency": "区切り文字の頻度",
            "separator_frequency_subtext": "隣り合う単語の間に区切り文字が入る確率です。100% ならすべての間に入ります。",
            "separator_spaces": "区切り文字の前後にスペース",
            "separator_spaces_subtext": "オフにすると、区切り文字が単語にくっつきます：hi•how•are•you。",
            "separator_space_mode": "スペースの位置",
            "separator_space_both": "両側",
            "separator_space_left": "左側のみ",
            "separator_space_right": "右側のみ",
            "cute_enabled": "かわいいエフェクトを有効にする",
            "cute_enabled_subtext": "顔文字、UwU、アクション、デコレーション。リンク、@メンション、#ハッシュタグ、コードはそのままです。",
            "cute_preview": "プレビュー",
            "section_debug": "デバッグ",
            "debug_enabled": "デバッグを有効にしました",
            "debug_disabled": "デバッグを無効にしました",
            "debug_start": "記録を開始",
            "debug_start_subtext": "プラグインのすべての操作を記録します：タップ、設定の変更、ダイアログ、通知、メッセージ処理（長さのみ、本文なし）、内部ログ。変更した設定値やチャット ID が含まれるため、誰かに送る前に確認してください。",
            "debug_stop": "記録を停止",
            "debug_recording": "記録中 · {amount}",
            "debug_log": "デバッグログ",
            "debug_log_subtext": "{amount}。タップして保存、削除、または記録を続行します。",
            "debug_amount": "{lines} 行、{size}",
            "debug_actions_message": "記録を停止しました（{amount}）。ログをどうしますか？",
            "debug_to_saved": "保存済みメッセージに送信",
            "debug_to_device": "端末に保存",
            "debug_delete": "ログを削除",
            "debug_continue": "記録を続行",
            "debug_hide": "デバッグを隠す",
            "debug_hide_subtext": "記録を停止してログを削除します。「プレビュー」を素早く 7 回タップしても同じです。",
            "debug_started": "ログの記録を開始しました",
            "debug_exported": "デバッグログを保存しました",
            "debug_deleted": "デバッグログを削除しました",
            "debug_hidden": "デバッグを隠しました",
            "debug_failed": "ログの操作に失敗しました",
            "cute_preview_sample": "こんにちは！元気？今日はいい天気だね。",
            "cute_preview_none": "エフェクトを 1 つ以上オンにしてください。タップで更新します。",
            "cute_preview_tap": "タップで更新します。",
            "cute_sentence_frequency": "文のエフェクトの頻度",
            "cute_sentence_frequency_subtext": "顔文字、キラキラ、句読点、語尾、アクション。",
            "cute_word_frequency": "単語のエフェクトの頻度",
            "cute_word_frequency_subtext": "どもり、母音の伸ばし、軟音記号。",
            "cute_kaomoji": "文末に顔文字 (◕‿◕)",
            "cute_sparkles": "文の前後にキラキラ ✨",
            "cute_exclamations": "かわいい感嘆符 (! → !✨)",
            "cute_punctuation": "かわいい句読点 (. → .~, ? → ?✨)",
            "cute_uwu_suffixes": "UwU の語尾 (nya~, owo)",
            "cute_actions": "かわいいアクション (*ぎゅっ*)",
            "cute_actions_newline": "アクションを改行して表示",
            "cute_lowercase": "小文字のみ",
            "cute_uwu_speak": "UwU 口調 (r/l → w, р/л → в)",
            "cute_stutter": "どもり (h-hi)",
            "cute_stretch": "母音を伸ばす (cuteee)",
            "cute_stretch_max": "母音をどれだけ伸ばすか",
            "cute_stretch_2x": "2 倍 (x2)",
            "cute_stretch_3x": "3 倍 (x3)",
            "cute_soft_sign": "語末に軟音記号 (котикь)",
            "cute_soft_sign_subtext": "ロシア語の単語のみ。",
            "regex_exceptions": "正規表現による除外",
            "regex_exceptions_hint": "1 行に 1 つの正規表現。一致したメッセージは装飾しません。",
            "regex_exceptions_count": "ルール：{n}",
            "regex_exceptions_empty": "上級者向け",
            "regex_exceptions_invalid": "式が正しくありません：{error}",
            "regex_exceptions_limit": "式は {n} 個まで、1 つあたり {m} 文字まで",
            "exceptions": "除外",
            "ignore_emoji_only": "絵文字だけのメッセージを除外",
            "ignore_emoji_only_subtext": "絵文字だけのメッセージは装飾しません。メディアのキャプションには影響しません。",
            "exceptions_hint": "このテキストで始まる、または終わるメッセージは装飾しません。1 行に 1 つ。",
            "ignore_code": "コードはそのまま",
            "ignore_code_subtext": "``` ブロックと `インラインコード` はそのまま残ります。",
            "ignore_commands": "コマンドはそのまま",
            "ignore_commands_subtext": "/start や /help@bot などのコマンドはそのまま残ります。コマンドで始まるメッセージは装飾しません。",
            "ignore_mentions": "メンションはそのまま",
            "ignore_mentions_subtext": "@username はそのまま残ります。メンションで始まるメッセージは装飾しません。",
            "ignore_links": "リンクはそのまま",
            "ignore_links_subtext": "リンク、サイトのアドレス、メールアドレスはそのまま残ります。リンクだけのメッセージは装飾しません。",
            "ignore_hashtags": "#ハッシュタグはそのまま",
            "ignore_hashtags_subtext": "#ハッシュタグはそのまま残ります。",
            "ignore_cashtags": "$キャッシュタグはそのまま",
            "ignore_cashtags_subtext": "$TON や $BTC などはそのまま残ります。",
            "ignore_segments": "そのまま残すもの",
            "ignore_segments_hint": "メッセージのうち、変更しない部分を選んでください。",
            "ignore_segments_count": "オン：{total} 個中 {n} 個",
            "scope_targets": "装飾の対象",
            "scope_targets_hint": "装飾を適用する場所を選んでください。",
            "scope_edit_targets": "編集時の設定",
            "scope_edit_targets_hint": "メッセージ編集時に装飾する対象を選んでください。",
            "exceptions_chat_menu": "除外に追加 / 除外から外す",
            "exceptions_chat_added": "チャットを除外に追加しました",
            "exceptions_chat_removed": "チャットを除外から外しました",
            "exceptions_chat_now_off": "このチャットでは Prefixfy はメッセージを装飾しません",
            "exceptions_chat_now_on": "このチャットで Prefixfy が再びメッセージを装飾します",
            "exceptions_chat_other_config": "リストは変更されましたが、このチャットは別の構成（チャットの割り当て、スケジュール、アカウント設定）に従います",
            "exceptions_count": "ルール：{n}、チャット：{m}",
            "capture_custom_emoji": "Premium 絵文字のコードを取得",
            "capture_custom_emoji_enabled": "Premium 絵文字を含むメッセージを送ると、プラグインがコードを返します",
            "capture_custom_emoji_disabled": "Premium 絵文字のコード取得を取り消しました",
            "capture_custom_emoji_hint": "マスク内の Premium 絵文字：(id|🙂)。🙂 は Premium のない人に表示される通常の絵文字です。コードはチャットのメニューの「Premium 絵文字のコードを取得」で取得できます。",
            "schedule": "設定セットのスケジュール",
            "schedule_empty": "未設定",
            "schedule_count": "ルール：{n}",
            "schedule_message": "1 行に 1 つのルール：条件 = 設定セット。\n条件：時刻 HH:MM-HH:MM または時間帯（朝 05–12、昼 12–17、夕方 17–23、夜 23–05、「朝-夕方」のような範囲）、曜日（mon-fri、sat,sun、weekend、weekdays）、日付 YYYY-MM-DD・DD.MM.YYYY・DD.MM（毎年）で範囲は「..」、チャットの種類（private、group、channel）、「chat ID」、「account ID」、「random N%」（メッセージごとに判定）。\n条件は and、or、not と括弧でつなぎます。語がなければ and とみなします。else はそれ以外すべての場合のルールです。и、или、не、иначе も使えます。\n日付付きのルールが優先され、else は最後に確認され、同じ順位では最初に一致したルールが使われます。日付をまたぐ時間帯の曜日と日付は開始日で判定します。独自の設定セットがあるチャットにはスケジュールは適用されません。",
            "schedule_hint": "22:00-07:00 = 夜\n09:00-18:00 mon-fri = 仕事\n(31.12 or 01.01) and not channel = 祝日\ngroup and 夕方 = 静か\nchat -1001234567890 = 特別\nrandom 20% = お楽しみ\nelse = 通常",
            "schedule_saved": "スケジュールを保存しました",
            "schedule_error": "{n} 行目：{reason}",
            "schedule_err_format": "形式は 条件 = 設定セット",
            "schedule_err_time": "時刻が正しくありません",
            "schedule_err_days": "曜日が正しくありません",
            "schedule_err_config": "設定セット「{name}」がありません",
            "schedule_err_limit": "ルールは {n} 個まで",
            "schedule_err_date": "日付が正しくありません",
            "schedule_err_unknown": "「{x}」を読み取れません",
            "schedule_err_parens": "括弧が対応していません",
            "schedule_err_deep": "条件が複雑すぎます",
            "schedule_err_random": "割合は 0〜100 にしてください",
            "schedule_err_size": "テキストが長すぎます",
            "config_import_cancelled": "インポートを取り消しました",
            "config_import": "インポート",
            "config_export": "エクスポート",
            "config_reset": "既定値に戻す",
            "config_reset_to_plugin": "インポートした値を無視して、プラグインの標準設定に戻す",
            "config_reset_to_plugin_unavailable": "使用できません：この設定セットはプラグイン内で作成されたため、リセットで元の状態に戻ります。",
            "config_active": "使用中の設定セット",
            "config_new": "新しい設定セット",
            "config_new_subtext": "別の設定の組み合わせです。作成するとすぐに使用中になります。",
            "config_name_hint": "設定セットの名前",
            "config_new_source_title": "新しい設定セットの元",
            "config_new_source_message": "何を元にしますか？何も選ばなければ既定の設定になります。",
            "config_new_copy_current": "現在の設定セットをコピー",
            "config_delete": "設定セットを削除",
            "config_delete_confirm": "設定セット「{name}」を削除しますか？",
            "config_delete_none": "削除できる未使用の設定セットはありません",
            "config_imported_name": "インポートした設定セット",
            "config_rename": "設定セットの名前を変更",
            "config_rename_subtext": "現在の設定セットの名前を変えます。",
            "config_name_invalid": "まだ使われていない名前を入力してください。",
            "config_name_taken": "同じ名前の設定セットがすでにあります。",
            "config_deleted": "削除した設定セット：{n}",
            "config_delete_multi": "設定セットを削除（複数）",
            "config_delete_multi_subtext": "未使用の設定セットを削除します。使用中のものは残ります。",
            "config_delete_multi_select": "削除する未使用の設定セットを選んでください。",
            "config_import_new_name": "新しい設定セットの名前",
            "config_parts_title": "設定セットの項目",
            "config_parts_message": "使う項目を選んでください（{n} 個から選べます）。",
            "config_part_mask": "マスク",
            "config_part_separator": "区切り文字",
            "config_part_exceptions": "除外とチャット",
            "config_part_exceptions_reset": "例外、チャット、適用範囲",
            "config_part_language": "プラグインの言語",
            "config_part_media": "メディア",
            "config_import_done": "設定セットをインポートしました",
            "config_import_take_name_title": "設定セットの名前",
            "config_import_take_name": "ファイルには「{name}」という名前があります。現在の設定セット名は「{current}」です。",
            "config_import_take_name_yes": "「{name}」にする",
            "config_import_take_name_no": "「{current}」のまま",
            "config_import_links_title": "設定セット内のリンク",
            "config_import_links_message": "ファイルにリンクが含まれています。送信するメッセージに入る可能性があります:",
            "config_import_links_more": "…ほか {n} 件",
            "config_import_failed": "設定セットをインポートできませんでした",
            "config_import_locked": "インポートは初期設定の完了後に使えます。",
            "config_save_failed": "設定セットを保存できませんでした",
            "config_export_done": "設定セットをエクスポートしました",
            "config_export_failed": "設定セットをエクスポートできませんでした",
            "config_export_destination_title": "保存先",
            "config_export_to_saved": "現在のアカウントの「保存済みメッセージ」",
            "config_export_to_device": "端末のストレージ",
            "config_restored": "選んだ値をリセットしました",
            "config_parts_none": "少なくとも 1 つの項目を選んでください",
            "config_export_select": "エクスポートする設定セット",
            "config_export_select_subtext": "{n} 個まで選べます。このあと、それぞれ項目を選びます。複数選ぶと、ファイルは現在のアカウントの「保存済みメッセージ」に直接送られます。",
            "config_shared_marker": "共通",
            "config_export_parts_title": "項目：{name}",
            "config_export_parts_progress": "設定セット {n} 個中 {i} 個目",
            "config_export_limit": "選べる設定セットは {n} 個までです",
            "config_export_none": "少なくとも 1 つの設定セットを選んでください",
            "config_export_done_multi": "エクスポートした設定セット：{n}",
            "config_export_partial": "{total} 個中 {ok} 個をエクスポートしました",
            "config_import_found_title": "設定セットのファイル",
            "config_import_found_contains": "インポートする項目：",
            "config_part_state_default": "既定値",
            "config_part_state_absent": "ファイルにありません",
            "config_import_nothing": "インポートするものがありません：選択した項目はファイルにないか、既定値のままです",
            "config_import_skipped": "スキップ（インポートする内容なし）：{parts}",
            "config_import_as_new": "新しい設定セットとしてインポート",
            "config_export_encrypt": "パスワードで暗号化",
            "config_export_encrypting": "ファイルを暗号化しています…",
            "password_export_title": "ファイルのパスワード",
            "password_export_title_named": "「{name}」のパスワード",
            "password_export_message": "ファイル全体が暗号化され、パスワードなしではどの項目が入っているかも分かりません。パスワードはどこにも保存されず、復元できません。",
            "password_import_title": "パスワードで保護されたファイル",
            "password_import_message": "ファイルに含まれる項目を表示するには、パスワードを入力してください。",
            "password_wrong": "パスワードが違うか、ファイルが壊れています。もう一度お試しください。",
            "password_checking": "パスワードを確認しています…",
            "password_hint": "パスワード",
            "password_repeat_hint": "パスワードをもう一度入力",
            "password_length": "{min}〜{max} 文字",
            "password_mismatch": "パスワードが一致しません",
            "config_import_file_failed": "設定セットのファイルを開けませんでした",
            "config_import_invalid": "ファイルに選んだ項目がないか、ファイルが壊れています。",
            "config_default_name": "既定の設定セット",
            "config_numbered_name": "設定セット {n}",
            "config_actions_subtext": "使う項目を選ぶ",
            "config_part_schedule": "チャットの割り当てとスケジュール",
            "config_part_cute": "かわいいエフェクト",
            "media_attachment": "メディア",
            "media_attachment_enable": "メディアを添付",
            "media_attachment_enable_subtext": "選んだファイルをメッセージごとに一緒に送ります。",
            "media_file": "ファイル",
            "media_file_none": "ファイルが選ばれていません",
            "media_import": "メディアを選ぶ",
            "media_delete": "メディアを削除",
            "media_delete_subtext": "選んだファイルを Prefixfy から削除します。",
            "media_delete_confirm": "メディア「{name}」を削除しますか？ファイルは Prefixfy から完全に削除されます。",
            "media_imported": "メディアを追加しました",
            "media_deleted": "メディアを削除しました",
            "media_import_failed": "メディアを追加できませんでした",
            "media_delete_failed": "メディアを削除できませんでした",
            "account_mode": "アカウントごとの設定",
            "account_mode_subtext": "アカウントごとに別の設定を使えます。変更するまでは、すべてのアカウントで共通です。",
            "account_target": "設定するアカウント",
            "account_auto": "自動（現在のアカウント）",
            "account_common": "共通（全アカウント）",
            "account_auto_now": "現在の選択",
            "account_editing": "設定中",
            "account_own": "独自の設定",
            "account_shared": "共通の設定",
            "account_common_hint": "共通の設定（独自の設定がないアカウント用）",
            "account_none": "アカウントを特定できません",
            "account_reset": "共通の設定に戻す",
            "account_reset_subtext": "このアカウントの独自の設定を削除します。",
            "account_reset_title": "アカウントの設定をリセット",
            "account_reset_confirm": "このアカウントの独自の設定を設定セットごと削除しますか？アカウントは再び共通の設定を使います。",
            "account_reset_button": "リセット",
            "account_reset_done": "このアカウントは共通の設定に戻りました",
            "account_import_title": "設定セットをどこに適用しますか？",
            "account_import_all": "すべてのアカウント",
            "account_import_common": "共通（独自の設定がないアカウント）",
            "check_now": "今すぐ確認",
            "check_now_subtext": "プラグインが公式ビルドかを確認します。",
            "check_started": "確認しています…",
            "check_confirm_title": "ビルドを確認しますか？",
            "check_confirm_body": "内容：検証データ（マニフェスト、ブラックリスト、設定プロファイル）をキャッシュを使わずに再ダウンロードし、公式ビルドかを確認します。保存済みのデータは、確認に成功したときだけ置き換えられます。\n\n使う場面：ビルドを確認できず機能が停止しているとき、プラグインを更新・再インストールした直後、または状態が古いと感じたとき。\n\n安全性：設定と設定セットには影響しません。インターネットが必要です。GitHub が応答しない場合は再試行し、ミラーも試します。それでも失敗した場合は、何も変わりません。",
            "check_confirm_yes": "確認",
            "check_ok": "確認に成功しました",
            "check_failed": "確認に失敗しました。接続を確認してもう一度お試しください。",
            "ota_auto": "自動アップデート",
            "ota_auto_subtext": "署名とチェックサムを検証したうえで、アップデートを自動でダウンロード・インストールします。",
            "ota_mode": "アップデートのタイミング",
            "ota_mode_available": "公開されたらすぐ",
            "ota_mode_time": "指定した時刻",
            "ota_action": "アップデートの扱い",
            "ota_action_download": "ダウンロードのみ",
            "ota_action_install": "ダウンロードしてインストール",
            "ota_time": "アップデートの時刻",
            "ota_time_subtext": "端末の時刻を HH:MM 形式で（例：04:00）。",
            "ota_time_invalid": "時刻を HH:MM 形式で入力してください（例：04:00）",
            "ota_disabled": "OTA アップデートは無効です",
            "ota_disabled_subtext": "開発者が一時的に無効にしています。新しいバージョンはリポジトリから手動でインストールしてください。",
            "ota_installed": "Prefixfy {version} をインストールしました。再起動しています…",
            "ota_restart_manual": "Prefixfy {version} をインストールしました。適用するにはプラグインをオフにしてからオンにしてください。",
            "ota_modified_found": "プラグインのファイルが変更されています。公式ビルド {version} をインストールしています…",
            "ota_failed": "アップデートに失敗しました：{reason}",
            "ota_busy": "アップデートはすでに進行中です",
            "ota_check_note": "この確認では新しいバージョンはインストールされません。通知が届いたら、「アップデートが必要」の下の「ダウンロード」からインストールできます。",
            "ota_almost_ready": "あと少し",
            "ota_almost_ready_subtext": "バージョン {version} をダウンロードしました。プラグインを再起動すれば完了です。",
            "ota_reload": "再起動",
            "ota_reload_subtext": "アップデートを適用してプラグインを再起動します。",
            "ota_staged": "Prefixfy {version} をダウンロードしました。「再起動」をタップしてください。",
            "ota_download": "ダウンロード",
            "check_update_found": "Prefixfy {version} が公開されました。「アップデートが必要」の下の「ダウンロード」をタップしてください。",
            "ota_download_subtext": "バージョン {version}。まずアップデートの詳細を表示します。",
            "ota_dl_title": "Prefixfy のアップデート",
            "ota_dl_size": "サイズ",
            "ota_dl_changelog": "新機能",
            "ota_dl_changelog_none": "開発者から情報は提供されていません",
            "ota_dl_confirm": "ダウンロードしてインストール",
            "ota_dl_warning": "モバイル通信では通信料がかかる場合があります。Wi-Fi をおすすめします。",
            "ota_unit_kb": "KB",
            "ota_unit_mb": "MB",
            "gate_update_required": "アップデートが必要",
            "gate_update_required_subtext": "Prefixfy {version} の公式ビルドをインストールしてください。それまでメッセージは装飾されません。",
            "gate_verify_required": "確認に失敗しました",
            "gate_verify_required_subtext": "ビルドを確認できなかったため、装飾はオフになっています。接続を確認してください。",
            "gate_account_blocked": "アクセスが拒否されました",
            "gate_account_blocked_subtext": "この端末のアカウントのひとつが Prefixfy のブラックリストに入っています。プラグインは無効です。",
            "about_plugin": "プラグインについて",
            "about_plugin_subtext": "バージョン、ビルド、検証の状態。",
            "about_title": "Prefixfy について",
            "about_version": "バージョン",
            "about_build_date": "ビルド日",
            "about_build_number": "その日のビルド番号",
            "about_serial": "シリアル番号",
            "about_build_label": "ビルドラベル（完全）",
            "about_latest": "最新の公式ビルド",
            "about_status": "検証",
            "about_unknown": "不明",
            "about_note": "これらの情報はプラグインファイルのビルドラベルから取得しています。",
            "status_ok": "成功：公式リリースと一致しています",
            "status_pending": "まだ実行されていません",
            "status_soft": "未確認：追加機能は停止中です",
            "status_blacklisted": "拒否：アカウントがブラックリストに入っています",
            "status_no_key": "失敗：このビルドにはアップデート鍵がありません",
            "status_integrity": "未確認：プラグインのファイルを読み取れませんでした",
            "notice_ok": "OK",
            "status_outdated": "失敗：ビルドが古く、新しいバージョンが出ています",
            "status_modified": "失敗：ビルドが変更されています",
            "gate_modified": "変更されたビルド",
            "gate_modified_subtext": "Prefixfy のファイルが公式リリース {version} と異なります。プラグインが自動で公式ビルドをインストールします。それまで装飾はオフです。",
            "notice_verify_body": "何が起きたか：このビルドは検証できません。署名付きマニフェスト用の有効な鍵がありません。\n\nどうなるか：プラグインは送信メッセージを装飾しません。設定は保持されます。\n\nどうすればよいか：リポジトリから公式ビルドをインストールしてください。",
            "notice_soft_body": "何が起きたか：Prefixfy はビルドが公式であることを確認できません。署名付きマニフェストかブラックリストの確認が完了しませんでした（インターネットに接続していない、GitHub にアクセスできない、前回の確認が古すぎる、またはプラグインのファイルを読み取れない）。\n\n停止中の機能：すべての追加機能 — スタイル、Markdown、マスクのローテーションと内容に応じたマスク、タグ、スケジュール、チャットの設定セット、メディア、Premium 絵文字、編集時の装飾、インポート。基本のマスクだけが動作します。\n\nどうすればよいか：接続を確認して「今すぐ確認」をタップしてください。確認に成功すれば、すべて自動で元に戻ります。",
            "notice_account_body": "何が起きたか：この端末の Telegram アカウントのひとつが Prefixfy のブラックリストに入っています。\n\nどうなるか：この端末ではプラグインが無効になります。設定は変更されません。\n\n誤りだと思われる場合は、プラグインの作者に連絡してください。",
            "gate_soft": "機能を一時停止中",
            "gate_soft_subtext": "現在ビルドを確認できないため、基本の装飾だけが動作しています。接続を確認してください。確認に成功すれば元に戻ります。",
            "gate_bypass_note": "この機能でブロックは解除されません。",
            "wipe_row": "データを削除",
            "wipe_row_subtext": "プラグインのデータをすべて消去するか、利用を完全にやめます。",
            "wipe_title": "Prefixfy のデータを削除しますか？",
            "wipe_body": "プラグインのすべてのデータが削除されます：設定セットとアカウントごとの設定、共通の設定、メディア、インポートしたファイル、検証キャッシュ。プラグインは再起動し、インストール直後と同じくセットアップウィザードから始まります。\n\nプラグインが古い場合は、先に最新バージョンをインストールしてからデータを削除します。\n\n「利用をやめる」を選ぶとプラグインも無効になり、「再開」ボタンだけが残ります。この場合アップデートはダウンロードされません。",
            "wipe_opt_out": "利用をやめる",
            "wipe_confirm_clean": "プラグインのすべてのファイルと設定が削除されます。プラグインは何度か再起動し（正常な動作です）、セットアップウィザードから始まります。設定セットとメディアは元に戻せません。残したいものは先にエクスポートしてください。",
            "wipe_confirm_title": "削除の確認",
            "wipe_confirm_out": "プラグインのすべてのファイルと設定を削除し、その後プラグインを無効にします。元に戻せません。",
            "wipe_confirm_btn": "削除",
            "wipe_started": "削除の準備をしています…",
            "wipe_started_multi": "削除の準備をしています… プラグインは何度か再起動します。",
            "wipe_halt": "クリーンアップ中",
            "wipe_halt_subtext": "プラグインはもう一度再起動し、初期状態から始まります。",
            "wipe_updating": "{version} にアップデートしてからデータを削除します…",
            "wipe_reinstalling": "ビルド {version} を再インストールしてからデータを削除します…",
            "wipe_update_failed": "プラグインをアップデートできませんでした：{reason}。何も削除されていません。",
            "wipe_restart_manual": "削除を完了するには、プラグインをオフにしてからオンにしてください。",
            "wipe_failed": "削除を準備できませんでした。何も削除されていません。",
            "wipe_done": "データを削除し、プラグインを初期状態から始めました",
            "resume_title": "再開",
            "resume_subtext": "Prefixfy は無効で、データを保持していません。タップして最初から始めます。",
            "resume_confirm_title": "Prefixfy を再開しますか？",
            "resume_confirm_body": "プラグインはインストール直後と同じく、既定の設定で起動します。",
            "resume_btn": "再開",
            "resume_done": "Prefixfy が再び動作しています",
            "resume_failed": "プラグインを起動できませんでした。オフにしてからオンにしてください。",
            "wipe_auto_reset_done": "プラグインのデータが壊れていたため、リセットしました",
            "setup_step_1": "ステップ 1/3：言語",
            "setup_step_2": "ステップ 2/3：装飾",
            "setup_step_3": "ステップ 3/3：アップデート",
            "setup_next": "次へ",
            "setup_next_subtext": "ステップ {step}/3 へ進む",
            "setup_back": "戻る",
            "setup_back_subtext": "ステップ {step}/3 に戻る",
            "setup_finish": "セットアップを完了",
            "setup_finish_subtext": "アップデートを確認し、あればインストールしてから、すべての設定を開きます。",
            "setup_checking": "アカウントを確認しています…",
            "setup_checking_subtext": "サーバーからブラックリストを取得しています。数秒かかります。",
            "setup_done": "初期設定が完了しました",
            "setup_almost_update": "あと少しです。残りはプラグインの更新だけです",
            "setup_finish_update_subtext": "バージョン {version} があります。確認後にプラグインを更新し、すべての設定を開きます。",
            "welcome_banner": "Prefixfy をインストールしていただきありがとうございます！",
            "welcome_banner_subtext": "タップして、できることと始め方を確認しましょう。",
            "welcome_title": "Prefixfy へようこそ",
            "welcome_body": "Prefixfy はメッセージにマスクを追加します。メッセージの前後のテキスト、装飾、デコレーションです。\n\nできること：\n• Markdown、テキストのスタイル、区切り文字を使ったマスク\n• かわいいエフェクト：顔文字、UwU、デコレーション\n• メッセージに添付するメディア\n• 除外：プラグインを使わないチャット、またはそのチャットだけで使う設定\n• インポート・エクスポート・スケジュールに対応した複数の設定セット\n• アカウントごとの設定\n\nはじめかた：\n1.「テキストの装飾」でマスクを設定します。\n2.「適用範囲」で装飾する対象を選びます。\n3. チャットを除外したり戻したりするには、そのチャットのメニューを開きます。\n\nあとはメッセージを書くだけです。",
            "welcome_ok": "OK",
            "updated_banner": "アップデートが完了しました",
            "updated_banner_subtext": "タップして確認",
        },
        "ko": {
            "editor_empty_means_default": "칸을 비워 두고 ‘저장’을 누르면 기본값으로 돌아갑니다.",
            "action_save": "저장",
            "action_delete": "삭제",
            "action_cancel": "취소",
            "action_create": "만들기",
            "action_apply": "적용",
            "action_next": "다음",
            "error_operation_failed": "작업을 완료하지 못했습니다",
            "section_scope": "적용 범위",
            "section_language": "플러그인 언어",
            "section_configurations": "구성",
            "section_appearance": "텍스트 꾸미기",
            "section_general": "기본",
            "section_about": "플러그인 정보",
            "section_accounts": "계정",
            "section_updates": "업데이트 및 검증",
            "section_cute": "귀여운 효과",
            "plugin_enable": "블랙리스트 모드",
            "plugin_enable_subtext": "켜짐: 목록에 있는 채팅을 제외한 모든 곳에서 작동. 꺼짐: 목록에 있는 채팅에서만 작동 (화이트리스트).",
            "language": "언어",
            "language_auto": "Telegram과 같은 언어",
            "language_auto_subtext": "Telegram 인터페이스 언어를 사용합니다. 직접 고르려면 끄세요.",
            "scope_message": "메시지",
            "scope_message_subtext": "일반 텍스트 메시지를 꾸밉니다.",
            "scope_media": "미디어 캡션",
            "scope_media_subtext": "사진, 동영상, 파일의 캡션을 꾸밉니다.",
            "scope_edit": "편집할 때",
            "scope_edit_subtext": "편집한 메시지를 꾸밉니다. 이미 꾸며진 텍스트는 그대로 둡니다.",
            "skip_once_expired": "건너뛰기가 만료되었습니다. 다음 메시지는 꾸며집니다",
            "chat_config_menu": "이 채팅의 구성",
            "chat_config_auto": "기본 구성 (일정 적용)",
            "chat_config_saved": "채팅 구성을 저장했습니다",
            "chat_config_reset": "이 채팅은 다시 기본 구성을 사용합니다",
            "skip_once_menu": "다음 메시지 꾸미지 않기",
            "skip_once_on": "다음 메시지는 꾸미지 않고 보냅니다",
            "skip_once_off": "건너뛰기를 취소했습니다",
            "chat_types": "채팅 유형",
            "chat_types_hint": "선택한 유형의 채팅에서만 꾸밉니다.",
            "chat_types_all": "모든 채팅",
            "chat_types_none": "유형을 하나 이상 선택하세요",
            "chat_type_private": "개인 채팅",
            "chat_type_group": "그룹",
            "chat_type_channel": "채널",
            "scope_edit_message": "텍스트 편집",
            "scope_edit_message_subtext": "편집한 일반 메시지를 꾸밉니다.",
            "scope_edit_media": "캡션 편집",
            "scope_edit_media_subtext": "편집한 미디어 캡션을 꾸밉니다.",
            "scope_article": "아티클",
            "scope_article_subtext": "보낼 때 아티클의 텍스트 블록을 꾸밉니다.",
            "scope_edit_article": "아티클 편집",
            "scope_edit_article_subtext": "편집한 아티클을 꾸밉니다.",
            "skip_once_on_edit": "건너뛰기를 편집에도 적용",
            "skip_once_on_edit_subtext": "건너뛰기가 켜져 있으면 채팅에서의 다음 편집도 꾸미지 않습니다.",
            "mask": "마스크",
            "mask_text": "마스크 텍스트",
            "markdown_style": "Markdown 스타일",
            "markdown_style_subtext": "마스크 안의 마커를 쓰거나 마스크 전체에 한 가지 스타일을 적용합니다.",
            "markdown_style_pick": "스타일",
            "md_manual": "직접 마커 입력",
            "md_bold": "마스크 전체 굵게",
            "md_italic": "마스크 전체 기울임",
            "md_strike": "마스크 전체 취소선",
            "md_spoiler": "마스크 전체 스포일러",
            "md_mono": "마스크 전체 고정폭",
            "mask_rotation": "마스크 순환",
            "mask_rotation_subtext": "기본 마스크 대신 목록의 마스크를 사용합니다. 채팅 마스크가 우선합니다.",
            "masks_list": "마스크 목록",
            "masks_list_count": "마스크: {n}개",
            "masks_list_empty": "한 줄에 마스크 하나",
            "masks_list_hint": "한 줄에 마스크 하나, 각 마스크에 [text]가 정확히 하나 있어야 합니다.",
            "masks_list_invalid": "각 마스크에 [text]가 정확히 하나 있어야 합니다",
            "masks_list_limit": "마스크는 최대 {n}개",
            "mask_tags_hint": "태그: [date], [time], [datetime], [chat], [id], [weekday], [year], [month], [day], [username], [count], [random_emoji], [hour], [minute], [second], [time12], [ampm], [daypart], [week], [yearday], [monthname], [weekday_short], [year_short], [timestamp], [tz], [chattype], [dice].\n[reply] — 답장 상대의 이름, [chatcount] — 이 채팅에서 내 메시지 번호, [battery] — 배터리 잔량, [moon] — 달의 위상, [line] — 목록에서 무작위로 고른 한 줄, [since:2026-12-31] / [until:2026-12-31] — 지난 날 수 / 남은 날 수, [quote] — 답장하는 메시지의 앞부분, [countdown:2026-12-31 18:00] — 지정한 시각까지 남은 시간, [weather] / [weather:Paris] — wttr.in의 기온 (인터넷 필요).",
            "mask_rotation_mode": "순환 순서",
            "mask_rotation_mode_random": "무작위",
            "mask_rotation_mode_sequential": "차례대로",
            "mask_editor_title": "마스크",
            "mask_editor_hint": "[text]는 메시지 본문, [text: 링크]는 링크가 걸린 본문입니다.",
            "mask_invalid": "마스크에 [text]가 정확히 하나 있어야 합니다",
            "unsafe_text_rejected": "방향 재정의(RTL), 보이지 않는 문자·제어 문자, Zalgo 또는 지나치게 긴 이모지 연속이 포함된 텍스트는 사용할 수 없습니다",
            "mask_too_long": "마스크가 너무 깁니다 (최대 {n}자)",
            "mask_preview_sample": "메시지 예시",
            "mask_preview_invalid": "마스크가 손상되었습니다. [text]가 정확히 하나 필요합니다",
            "conditional_masks": "내용별 마스크",
            "conditional_masks_hint": "한 줄에 규칙 하나: 정규식 => 마스크. 텍스트와 일치하는 첫 번째 규칙의 마스크가 사용됩니다. 각 마스크에 [text]가 정확히 하나 있어야 합니다.",
            "conditional_masks_count": "규칙: {n}개",
            "conditional_masks_empty": "특정 텍스트가 있는 메시지에 다른 마스크",
            "conditional_masks_format": "{n}번째 줄: ‘식 => 마스크’ 형식이어야 합니다",
            "md_quote": "마스크 전체 인용",
            "text_style": "텍스트 스타일",
            "text_style_random": "무작위 스타일",
            "text_style_random_subtext": "메시지마다 새 스타일 (뒤집기 제외).",
            "text_style_subtext": "메시지 본문만 바뀝니다. Fancy, Bold, Gothic, Circled는 라틴 문자에, L33T는 키릴 문자에도 적용됩니다.",
            "text_style_enable": "텍스트 스타일 사용",
            "text_style_translit": "키릴 문자 음역",
            "text_style_translit_subtext": "러시아어와 우크라이나어 텍스트에도 라틴 문자 스타일이 적용됩니다.",
            "style_words": "특정 단어에만 스타일",
            "style_words_hint": "한 줄에 단어 하나. 비워 두면 텍스트 전체에 적용됩니다.",
            "style_words_count": "단어: {n}개",
            "style_words_empty": "텍스트 전체",
            "style_words_limit": "단어는 최대 {n}개",
            "tag_lines": "[line]용 문장",
            "tag_lines_hint": "한 줄에 하나씩, 최대 64자. [line] 태그 자리에 무작위로 한 줄이 들어갑니다.",
            "tag_lines_count": "문장: {n}개",
            "tag_lines_empty": "아직 문장이 없습니다",
            "tag_lines_limit": "문장은 최대 {n}개",
            "separator": "구분자",
            "separator_enable": "구분자 사용",
            "separator_enable_subtext": "단어 사이에 원하는 구분자를 넣습니다.",
            "separator_set": "구분자 세트",
            "separator_count": "단어 사이 구분자 수",
            "separator_count_subtext": "눌러서 변경합니다.",
            "separator_custom_title": "사용자 세트",
            "separator_custom_message": "구분자를 쉼표로 나눠 입력하세요. 예:\n•, ·, —, ~, |",
            "separator_preview_sample": "미리보기용 예시 텍스트",
            "separator_frequency": "구분자 빈도",
            "separator_frequency_subtext": "이웃한 두 단어 사이에 구분자가 들어갈 확률입니다. 100%면 모든 단어 사이에 들어갑니다.",
            "separator_spaces": "구분자 양옆 공백",
            "separator_spaces_subtext": "끄면 구분자가 단어에 바로 붙습니다: hi•how•are•you.",
            "separator_space_mode": "공백 위치",
            "separator_space_both": "양쪽",
            "separator_space_left": "왼쪽만",
            "separator_space_right": "오른쪽만",
            "cute_enabled": "귀여운 효과 사용",
            "cute_enabled_subtext": "카오모지, UwU, 행동, 장식. 링크, @멘션, #해시태그, 코드는 바뀌지 않습니다.",
            "cute_preview": "미리보기",
            "section_debug": "디버그",
            "debug_enabled": "디버그를 켰습니다",
            "debug_disabled": "디버그를 껐습니다",
            "debug_start": "기록 시작",
            "debug_start_subtext": "플러그인의 모든 동작을 기록합니다: 탭, 설정 변경, 대화상자, 알림, 메시지 처리(길이만, 본문 없음), 내부 로그. 바뀐 설정 값과 채팅 ID가 들어가니 다른 사람에게 보내기 전에 확인하세요.",
            "debug_stop": "기록 중지",
            "debug_recording": "기록 중 · {amount}",
            "debug_log": "디버그 로그",
            "debug_log_subtext": "{amount}. 눌러서 저장, 삭제하거나 기록을 이어 가세요.",
            "debug_amount": "{lines}줄, {size}",
            "debug_actions_message": "기록을 멈췄습니다({amount}). 로그를 어떻게 할까요?",
            "debug_to_saved": "저장된 메시지로 보내기",
            "debug_to_device": "기기에 저장",
            "debug_delete": "로그 삭제",
            "debug_continue": "기록 이어 가기",
            "debug_hide": "디버그 숨기기",
            "debug_hide_subtext": "기록을 멈추고 로그를 삭제합니다. ‘미리보기’를 빠르게 7번 눌러도 같습니다.",
            "debug_started": "로그 기록을 시작했습니다",
            "debug_exported": "디버그 로그를 저장했습니다",
            "debug_deleted": "디버그 로그를 삭제했습니다",
            "debug_hidden": "디버그를 숨겼습니다",
            "debug_failed": "로그 작업에 실패했습니다",
            "cute_preview_sample": "안녕! 잘 지내? 오늘 날씨 정말 좋다.",
            "cute_preview_none": "효과를 하나 이상 켜세요. 눌러서 새로고침합니다.",
            "cute_preview_tap": "눌러서 새로고침합니다.",
            "cute_sentence_frequency": "문장 효과 빈도",
            "cute_sentence_frequency_subtext": "카오모지, 반짝이, 문장 부호, 어미, 행동.",
            "cute_word_frequency": "단어 효과 빈도",
            "cute_word_frequency_subtext": "말 더듬기, 모음 늘이기, 연음 부호.",
            "cute_kaomoji": "문장 끝에 카오모지 (◕‿◕)",
            "cute_sparkles": "문장 앞뒤에 반짝이 ✨",
            "cute_exclamations": "귀여운 느낌표 (! → !✨)",
            "cute_punctuation": "귀여운 문장 부호 (. → .~, ? → ?✨)",
            "cute_uwu_suffixes": "UwU 어미 (nya~, owo)",
            "cute_actions": "귀여운 행동 (*꼬옥*)",
            "cute_actions_newline": "행동을 새 줄에 표시",
            "cute_lowercase": "소문자만",
            "cute_uwu_speak": "UwU 말투 (r/l → w, р/л → в)",
            "cute_stutter": "말 더듬기 (h-hi)",
            "cute_stretch": "모음 늘이기 (cuteee)",
            "cute_stretch_max": "모음을 얼마나 늘일지",
            "cute_stretch_2x": "두 배 (x2)",
            "cute_stretch_3x": "세 배 (x3)",
            "cute_soft_sign": "단어 끝에 연음 부호 (котикь)",
            "cute_soft_sign_subtext": "러시아어 단어에만 적용됩니다.",
            "regex_exceptions": "정규식 예외",
            "regex_exceptions_hint": "한 줄에 정규식 하나. 일치하는 메시지는 꾸미지 않습니다.",
            "regex_exceptions_count": "규칙: {n}개",
            "regex_exceptions_empty": "고급 사용자용",
            "regex_exceptions_invalid": "잘못된 식: {error}",
            "regex_exceptions_limit": "식은 최대 {n}개, 각각 최대 {m}자",
            "exceptions": "예외",
            "ignore_emoji_only": "이모지만 있는 메시지 건너뛰기",
            "ignore_emoji_only_subtext": "이모지만으로 된 메시지는 꾸미지 않습니다. 미디어 캡션에는 영향이 없습니다.",
            "exceptions_hint": "이 텍스트로 시작하거나 끝나는 메시지는 꾸미지 않습니다. 한 줄에 하나씩.",
            "ignore_code": "코드는 그대로",
            "ignore_code_subtext": "``` 블록과 `인라인 코드`는 그대로 둡니다.",
            "ignore_commands": "명령어는 그대로",
            "ignore_commands_subtext": "/start, /help@bot 같은 명령어는 그대로 둡니다. 명령어로 시작하는 메시지는 꾸미지 않습니다.",
            "ignore_mentions": "멘션은 그대로",
            "ignore_mentions_subtext": "@username은 그대로 둡니다. 멘션으로 시작하는 메시지는 꾸미지 않습니다.",
            "ignore_links": "링크는 그대로",
            "ignore_links_subtext": "링크, 사이트 주소, 이메일은 그대로 둡니다. 링크만 있는 메시지는 꾸미지 않습니다.",
            "ignore_hashtags": "#해시태그는 그대로",
            "ignore_hashtags_subtext": "#해시태그는 그대로 둡니다.",
            "ignore_cashtags": "$캐시태그는 그대로",
            "ignore_cashtags_subtext": "$TON, $BTC 등은 그대로 둡니다.",
            "ignore_segments": "그대로 둘 부분",
            "ignore_segments_hint": "메시지에서 바꾸지 않을 부분을 선택하세요.",
            "ignore_segments_count": "켜짐: {total}개 중 {n}개",
            "scope_targets": "꾸밀 대상",
            "scope_targets_hint": "꾸밈을 적용할 위치를 선택하세요.",
            "scope_edit_targets": "수정 설정",
            "scope_edit_targets_hint": "메시지를 수정할 때 꾸밀 대상을 선택하세요.",
            "exceptions_chat_menu": "예외에 추가 / 예외에서 빼기",
            "exceptions_chat_added": "채팅을 예외에 추가했습니다",
            "exceptions_chat_removed": "채팅을 예외에서 뺐습니다",
            "exceptions_chat_now_off": "이 채팅에서는 Prefixfy가 더 이상 메시지를 꾸미지 않습니다",
            "exceptions_chat_now_on": "이 채팅에서 Prefixfy가 다시 메시지를 꾸밉니다",
            "exceptions_chat_other_config": "목록은 바뀌었지만 이 채팅은 다른 구성(채팅 연결, 일정 또는 계정 설정)을 따릅니다",
            "exceptions_count": "규칙: {n}개, 채팅: {m}개",
            "capture_custom_emoji": "Premium 이모지 코드 받기",
            "capture_custom_emoji_enabled": "Premium 이모지가 담긴 메시지를 보내면 플러그인이 코드를 알려 줍니다",
            "capture_custom_emoji_disabled": "Premium 이모지 코드 받기를 취소했습니다",
            "capture_custom_emoji_hint": "마스크 안의 Premium 이모지: (id|🙂). 🙂는 Premium이 없는 사람에게 보이는 일반 이모지입니다. 코드는 채팅 메뉴의 ‘Premium 이모지 코드 받기’로 받을 수 있습니다.",
            "schedule": "구성 일정",
            "schedule_empty": "설정 안 됨",
            "schedule_count": "규칙: {n}개",
            "schedule_message": "한 줄에 규칙 하나: 조건 = 구성.\n조건: 시간 HH:MM-HH:MM 또는 시간대(아침 05–12, 낮 12–17, 저녁 17–23, 밤 23–05, ‘아침-저녁’ 같은 범위), 요일(mon-fri, sat,sun, weekend, weekdays), 날짜 YYYY-MM-DD·DD.MM.YYYY·DD.MM(매년)이며 기간은 ‘..’로 잇습니다. 채팅 유형(private, group, channel), ‘chat ID’, ‘account ID’, ‘random N%’(메시지마다 판정).\n조건은 and, or, not과 괄호로 잇습니다. 단어가 없으면 and로 봅니다. else는 그 밖의 모든 경우를 위한 규칙입니다. и, или, не, иначе도 쓸 수 있습니다.\n날짜가 있는 규칙이 먼저이고, else는 마지막에 확인하며, 같은 순위에서는 처음 일치한 규칙이 적용됩니다. 자정을 넘는 시간대의 요일과 날짜는 시작한 날을 기준으로 합니다. 자체 구성이 있는 채팅에는 일정이 적용되지 않습니다.",
            "schedule_hint": "22:00-07:00 = 밤\n09:00-18:00 mon-fri = 업무\n(31.12 or 01.01) and not channel = 휴일\ngroup and 저녁 = 조용히\nchat -1001234567890 = 특별\nrandom 20% = 재미\nelse = 기본",
            "schedule_saved": "일정을 저장했습니다",
            "schedule_error": "{n}번째 줄: {reason}",
            "schedule_err_format": "형식: 조건 = 구성",
            "schedule_err_time": "잘못된 시간",
            "schedule_err_days": "잘못된 요일",
            "schedule_err_config": "‘{name}’ 구성이 없습니다",
            "schedule_err_limit": "규칙은 최대 {n}개",
            "schedule_err_date": "잘못된 날짜",
            "schedule_err_unknown": "‘{x}’을(를) 이해할 수 없습니다",
            "schedule_err_parens": "괄호가 맞지 않습니다",
            "schedule_err_deep": "조건이 너무 복잡합니다",
            "schedule_err_random": "비율은 0~100이어야 합니다",
            "schedule_err_size": "텍스트가 너무 깁니다",
            "config_import_cancelled": "가져오기를 취소했습니다",
            "config_import": "가져오기",
            "config_export": "내보내기",
            "config_reset": "기본값으로 되돌리기",
            "config_reset_to_plugin": "가져온 값 무시: 플러그인 표준 설정으로 되돌리기",
            "config_reset_to_plugin_unavailable": "사용할 수 없음: 이 구성은 플러그인에서 만들어졌으므로 초기화하면 이미 원래 상태로 돌아갑니다.",
            "config_active": "사용 중인 구성",
            "config_new": "새 구성",
            "config_new_subtext": "별도의 설정 묶음입니다. 만들면 바로 사용 중이 됩니다.",
            "config_name_hint": "구성 이름",
            "config_new_source_title": "새 구성의 바탕",
            "config_new_source_message": "무엇을 바탕으로 할까요? 아무것도 고르지 않으면 기본 설정을 사용합니다.",
            "config_new_copy_current": "현재 구성의 설정 복사",
            "config_delete": "구성 삭제",
            "config_delete_confirm": "‘{name}’ 구성을 삭제할까요?",
            "config_delete_none": "삭제할 수 있는 비활성 구성이 없습니다",
            "config_imported_name": "가져온 구성",
            "config_rename": "구성 이름 변경",
            "config_rename_subtext": "현재 구성의 이름을 바꿉니다.",
            "config_name_invalid": "아직 쓰이지 않은 이름을 입력하세요.",
            "config_name_taken": "같은 이름의 구성이 이미 있습니다.",
            "config_deleted": "삭제한 구성: {n}개",
            "config_delete_multi": "구성 삭제 (여러 개)",
            "config_delete_multi_subtext": "비활성 구성을 삭제합니다. 사용 중인 구성은 남습니다.",
            "config_delete_multi_select": "삭제할 비활성 구성을 선택하세요.",
            "config_import_new_name": "새 구성 이름",
            "config_parts_title": "구성 항목",
            "config_parts_message": "사용할 항목을 선택하세요 ({n}개 중 선택).",
            "config_part_mask": "마스크",
            "config_part_separator": "구분자",
            "config_part_exceptions": "예외 및 채팅",
            "config_part_exceptions_reset": "예외, 채팅 및 적용 범위",
            "config_part_language": "플러그인 언어",
            "config_part_media": "미디어",
            "config_import_done": "구성을 가져왔습니다",
            "config_import_take_name_title": "구성 이름",
            "config_import_take_name": "파일에 ‘{name}’이라는 이름이 있습니다. 현재 구성 이름은 ‘{current}’입니다.",
            "config_import_take_name_yes": "‘{name}’으로 변경",
            "config_import_take_name_no": "‘{current}’ 유지",
            "config_import_links_title": "구성에 포함된 링크",
            "config_import_links_message": "파일에 링크가 있습니다. 보내는 메시지에 들어갈 수 있습니다:",
            "config_import_links_more": "…외 {n}개",
            "config_import_failed": "구성을 가져오지 못했습니다",
            "config_import_locked": "가져오기는 초기 설정을 마친 뒤에 사용할 수 있습니다.",
            "config_save_failed": "구성을 저장하지 못했습니다",
            "config_export_done": "구성을 내보냈습니다",
            "config_export_failed": "구성을 내보내지 못했습니다",
            "config_export_destination_title": "어디에 저장할까요?",
            "config_export_to_saved": "현재 계정의 ‘저장된 메시지’",
            "config_export_to_device": "기기 저장소",
            "config_restored": "선택한 값을 초기화했습니다",
            "config_parts_none": "항목을 하나 이상 선택하세요",
            "config_export_select": "내보낼 구성 선택",
            "config_export_select_subtext": "최대 {n}개까지 고를 수 있습니다. 이어서 구성마다 항목을 고릅니다. 여러 개를 고르면 파일이 현재 계정의 ‘저장된 메시지’로 바로 전송됩니다.",
            "config_shared_marker": "공용",
            "config_export_parts_title": "항목: {name}",
            "config_export_parts_progress": "{n}개 중 {i}번째 구성",
            "config_export_limit": "구성은 최대 {n}개까지 고를 수 있습니다",
            "config_export_none": "구성을 하나 이상 선택하세요",
            "config_export_done_multi": "내보낸 구성: {n}개",
            "config_export_partial": "{total}개 중 {ok}개를 내보냈습니다",
            "config_import_found_title": "구성 파일",
            "config_import_found_contains": "가져올 항목:",
            "config_part_state_default": "기본값",
            "config_part_state_absent": "파일에 없음",
            "config_import_nothing": "가져올 내용이 없습니다: 선택한 항목이 파일에 없거나 이미 기본값입니다",
            "config_import_skipped": "건너뜀(가져올 내용 없음): {parts}",
            "config_import_as_new": "새 구성으로 가져오기",
            "config_export_encrypt": "비밀번호로 암호화",
            "config_export_encrypting": "파일을 암호화하는 중…",
            "password_export_title": "파일 비밀번호",
            "password_export_title_named": "“{name}” 비밀번호",
            "password_export_message": "파일 전체가 암호화되어 비밀번호 없이는 어떤 항목이 들어 있는지도 보이지 않습니다. 비밀번호는 어디에도 저장되지 않으며 복구할 수 없습니다.",
            "password_import_title": "비밀번호로 보호된 파일",
            "password_import_message": "파일에 어떤 항목이 있는지 보려면 비밀번호를 입력하세요.",
            "password_wrong": "비밀번호가 틀렸거나 파일이 손상되었습니다. 다시 시도하세요.",
            "password_checking": "비밀번호를 확인하는 중…",
            "password_hint": "비밀번호",
            "password_repeat_hint": "비밀번호 다시 입력",
            "password_length": "{min}~{max}자",
            "password_mismatch": "비밀번호가 일치하지 않습니다",
            "config_import_file_failed": "구성 파일을 열지 못했습니다",
            "config_import_invalid": "파일에 선택한 항목이 없거나 파일이 손상되었습니다.",
            "config_default_name": "기본 구성",
            "config_numbered_name": "구성 {n}",
            "config_actions_subtext": "사용할 항목 고르기",
            "config_part_schedule": "채팅 연결 및 일정",
            "config_part_cute": "귀여운 효과",
            "media_attachment": "미디어",
            "media_attachment_enable": "미디어 첨부",
            "media_attachment_enable_subtext": "선택한 파일을 메시지마다 함께 보냅니다.",
            "media_file": "파일",
            "media_file_none": "선택한 파일 없음",
            "media_import": "미디어 선택",
            "media_delete": "미디어 삭제",
            "media_delete_subtext": "선택한 파일을 Prefixfy에서 삭제합니다.",
            "media_delete_confirm": "‘{name}’ 미디어를 삭제할까요? 파일은 Prefixfy에서 완전히 삭제됩니다.",
            "media_imported": "미디어를 추가했습니다",
            "media_deleted": "미디어를 삭제했습니다",
            "media_import_failed": "미디어를 추가하지 못했습니다",
            "media_delete_failed": "미디어를 삭제하지 못했습니다",
            "account_mode": "계정별 설정",
            "account_mode_subtext": "계정마다 따로 설정합니다. 바꾸기 전까지는 모든 계정이 같은 설정을 씁니다.",
            "account_target": "설정할 계정",
            "account_auto": "자동 (현재 계정)",
            "account_common": "공용 (모든 계정)",
            "account_auto_now": "현재 선택",
            "account_editing": "설정 중",
            "account_own": "계정 전용 설정",
            "account_shared": "공용 설정",
            "account_common_hint": "공용 설정 (전용 설정이 없는 계정용)",
            "account_none": "계정을 확인할 수 없음",
            "account_reset": "공용 설정으로 되돌리기",
            "account_reset_subtext": "이 계정의 전용 설정을 삭제합니다.",
            "account_reset_title": "계정 설정 초기화",
            "account_reset_confirm": "이 계정의 전용 설정을 구성과 함께 삭제할까요? 계정은 다시 공용 설정을 사용합니다.",
            "account_reset_button": "초기화",
            "account_reset_done": "이 계정은 다시 공용 설정을 사용합니다",
            "account_import_title": "구성을 어디에 적용할까요?",
            "account_import_all": "모든 계정",
            "account_import_common": "공용 (전용 설정이 없는 계정)",
            "check_now": "지금 확인",
            "check_now_subtext": "플러그인이 공식 빌드인지 확인합니다.",
            "check_started": "확인하는 중…",
            "check_confirm_title": "빌드를 확인할까요?",
            "check_confirm_body": "하는 일: 검증 데이터(매니페스트, 블랙리스트, 설정 프로필)를 캐시를 거치지 않고 다시 내려받아 공식 빌드인지 확인합니다. 저장된 데이터는 확인에 성공했을 때만 바뀝니다.\n\n필요한 경우: 빌드를 확인하지 못해 기능이 중지되었을 때, 플러그인을 방금 업데이트하거나 다시 설치했을 때, 상태가 오래된 것처럼 보일 때.\n\n안전한가요: 설정과 구성은 건드리지 않습니다. 인터넷이 필요합니다. GitHub가 응답하지 않으면 다시 시도하고 미러도 사용해 봅니다. 그래도 실패하면 아무것도 바뀌지 않습니다.",
            "check_confirm_yes": "확인",
            "check_ok": "확인 완료",
            "check_failed": "확인하지 못했습니다. 인터넷 연결을 확인하고 다시 시도하세요.",
            "ota_auto": "자동 업데이트",
            "ota_auto_subtext": "서명과 체크섬을 검증한 뒤 업데이트를 알아서 내려받아 설치합니다.",
            "ota_mode": "업데이트 시점",
            "ota_mode_available": "나오는 즉시",
            "ota_mode_time": "정한 시각에",
            "ota_action": "업데이트 처리 방식",
            "ota_action_download": "내려받기만",
            "ota_action_install": "내려받고 설치",
            "ota_time": "업데이트 시각",
            "ota_time_subtext": "기기 시간 기준 HH:MM 형식 (예: 04:00).",
            "ota_time_invalid": "시간을 HH:MM 형식으로 입력하세요 (예: 04:00)",
            "ota_disabled": "OTA 업데이트가 꺼져 있습니다",
            "ota_disabled_subtext": "개발자가 잠시 꺼 두었습니다. 새 버전은 저장소에서 직접 설치하세요.",
            "ota_installed": "Prefixfy {version}을(를) 설치했습니다. 다시 시작하는 중…",
            "ota_restart_manual": "Prefixfy {version}을(를) 설치했습니다. 적용하려면 플러그인을 껐다가 다시 켜세요.",
            "ota_modified_found": "플러그인 파일이 변경되었습니다. 공식 빌드 {version}을(를) 설치하는 중…",
            "ota_failed": "업데이트 실패: {reason}",
            "ota_busy": "이미 업데이트가 진행 중입니다",
            "ota_check_note": "이 확인으로는 새 버전이 설치되지 않습니다. 알림이 오면 ‘업데이트 필요’ 아래의 ‘다운로드’로 설치할 수 있습니다.",
            "ota_almost_ready": "거의 다 됐습니다",
            "ota_almost_ready_subtext": "{version} 버전을 내려받았습니다. 플러그인을 다시 시작하기만 하면 됩니다.",
            "ota_reload": "다시 시작",
            "ota_reload_subtext": "업데이트를 적용하고 플러그인을 다시 시작합니다.",
            "ota_staged": "Prefixfy {version}을(를) 내려받았습니다. ‘다시 시작’을 누르세요.",
            "ota_download": "다운로드",
            "check_update_found": "Prefixfy {version}이(가) 나왔습니다. ‘업데이트 필요’ 아래의 ‘다운로드’를 누르세요.",
            "ota_download_subtext": "{version} 버전. 먼저 업데이트 정보를 보여 드립니다.",
            "ota_dl_title": "Prefixfy 업데이트",
            "ota_dl_size": "크기",
            "ota_dl_changelog": "새로운 기능",
            "ota_dl_changelog_none": "개발자가 정보를 제공하지 않았습니다",
            "ota_dl_confirm": "내려받고 설치",
            "ota_dl_warning": "모바일 데이터에서는 통신사 요금이 부과될 수 있습니다. Wi-Fi 사용을 권장합니다.",
            "ota_unit_kb": "KB",
            "ota_unit_mb": "MB",
            "gate_update_required": "업데이트 필요",
            "gate_update_required_subtext": "Prefixfy {version} 공식 빌드를 설치하세요. 그때까지 메시지를 꾸미지 않습니다.",
            "gate_verify_required": "확인 실패",
            "gate_verify_required_subtext": "빌드를 확인하지 못해 꾸미기가 꺼져 있습니다. 인터넷 연결을 확인하세요.",
            "gate_account_blocked": "접근 거부",
            "gate_account_blocked_subtext": "이 기기의 계정 중 하나가 Prefixfy 블랙리스트에 있습니다. 플러그인이 꺼졌습니다.",
            "about_plugin": "플러그인 정보",
            "about_plugin_subtext": "버전, 빌드, 검증 상태.",
            "about_title": "Prefixfy 정보",
            "about_version": "버전",
            "about_build_date": "빌드 날짜",
            "about_build_number": "당일 빌드 번호",
            "about_serial": "일련번호",
            "about_build_label": "전체 빌드 라벨",
            "about_latest": "최신 공식 빌드",
            "about_status": "검증",
            "about_unknown": "알 수 없음",
            "about_note": "이 정보는 플러그인 파일의 빌드 라벨에서 가져옵니다.",
            "status_ok": "통과: 공식 릴리스와 일치합니다",
            "status_pending": "아직 확인하지 않음",
            "status_soft": "미확인: 추가 기능이 중지됨",
            "status_blacklisted": "거부: 블랙리스트에 있는 계정",
            "status_no_key": "실패: 이 빌드에 업데이트 키가 없음",
            "status_integrity": "미확인: 플러그인 파일을 읽지 못함",
            "notice_ok": "확인",
            "status_outdated": "실패: 빌드가 오래되었고 새 버전이 나옴",
            "status_modified": "실패: 빌드가 변경됨",
            "gate_modified": "변경된 빌드",
            "gate_modified_subtext": "Prefixfy 파일이 공식 릴리스 {version}과(와) 다릅니다. 플러그인이 공식 빌드를 알아서 설치하며, 그때까지 꾸미기는 꺼집니다.",
            "notice_verify_body": "무슨 일인가요: 이 빌드는 검증할 수 없습니다. 서명된 매니페스트에 쓸 유효한 키가 없습니다.\n\n어떻게 되나요: 플러그인이 보내는 메시지를 꾸미지 않습니다. 설정은 유지됩니다.\n\n어떻게 하나요: 저장소에서 공식 빌드를 설치하세요.",
            "notice_soft_body": "무슨 일인가요: Prefixfy가 빌드가 공식인지 확인하지 못했습니다. 서명된 매니페스트나 블랙리스트 확인이 끝나지 않았습니다(인터넷 없음, GitHub 접속 불가, 마지막 확인이 너무 오래됨, 플러그인 파일을 읽을 수 없음).\n\n중지된 기능: 모든 추가 기능 — 스타일, Markdown, 마스크 순환과 내용별 마스크, 태그, 일정, 채팅 구성, 미디어, Premium 이모지, 편집 시 꾸미기, 가져오기. 기본 마스크만 작동합니다.\n\n어떻게 하나요: 인터넷 연결을 확인하고 ‘지금 확인’을 누르세요. 확인에 성공하면 모두 자동으로 돌아옵니다.",
            "notice_account_body": "무슨 일인가요: 이 기기의 Telegram 계정 중 하나가 Prefixfy 블랙리스트에 있습니다.\n\n어떻게 되나요: 이 기기에서 플러그인이 꺼집니다. 설정은 바뀌지 않습니다.\n\n잘못된 것 같다면 플러그인 제작자에게 문의하세요.",
            "gate_soft": "기능 일시 중지",
            "gate_soft_subtext": "지금은 빌드를 확인할 수 없어 기본 꾸미기만 작동합니다. 인터넷 연결을 확인하세요. 확인에 성공하면 모두 돌아옵니다.",
            "gate_bypass_note": "이 기능으로는 차단이 풀리지 않습니다.",
            "wipe_row": "데이터 삭제",
            "wipe_row_subtext": "플러그인 데이터를 모두 지우거나 사용을 완전히 그만둡니다.",
            "wipe_title": "Prefixfy 데이터를 삭제할까요?",
            "wipe_body": "플러그인의 모든 데이터가 삭제됩니다: 구성과 계정별 설정, 공용 설정, 미디어, 가져온 파일, 검증 캐시. 플러그인은 다시 시작되고, 설치 직후처럼 설정 마법사부터 시작합니다.\n\n플러그인이 오래된 경우 먼저 최신 버전을 설치한 다음 데이터를 삭제합니다.\n\n‘사용 그만두기’를 고르면 플러그인도 꺼지고 ‘다시 사용’ 버튼만 남습니다. 이 경우 업데이트는 내려받지 않습니다.",
            "wipe_opt_out": "사용 그만두기",
            "wipe_confirm_clean": "플러그인의 모든 파일과 설정이 삭제됩니다. 플러그인은 몇 번 다시 시작되며(정상입니다) 설정 마법사부터 시작합니다. 구성과 미디어는 되돌릴 수 없으니 남기고 싶은 것은 먼저 내보내세요.",
            "wipe_confirm_title": "삭제 확인",
            "wipe_confirm_out": "플러그인의 모든 파일과 설정을 삭제한 뒤 플러그인을 끕니다. 되돌릴 수 없습니다.",
            "wipe_confirm_btn": "삭제",
            "wipe_started": "삭제를 준비하는 중…",
            "wipe_started_multi": "삭제를 준비하는 중… 플러그인이 몇 번 다시 시작됩니다.",
            "wipe_halt": "정리하는 중",
            "wipe_halt_subtext": "플러그인이 한 번 더 다시 시작되어 처음 상태로 돌아갑니다.",
            "wipe_updating": "{version}(으)로 업데이트한 뒤 데이터를 삭제합니다…",
            "wipe_reinstalling": "{version} 빌드를 다시 설치한 뒤 데이터를 삭제합니다…",
            "wipe_update_failed": "플러그인을 업데이트하지 못했습니다: {reason}. 아무것도 삭제되지 않았습니다.",
            "wipe_restart_manual": "삭제를 마치려면 플러그인을 껐다가 다시 켜세요.",
            "wipe_failed": "삭제를 준비하지 못했습니다. 아무것도 삭제되지 않았습니다.",
            "wipe_done": "데이터를 삭제하고 플러그인을 처음 상태로 시작했습니다",
            "resume_title": "다시 사용",
            "resume_subtext": "Prefixfy가 꺼져 있고 데이터를 보관하지 않습니다. 눌러서 처음부터 시작하세요.",
            "resume_confirm_title": "Prefixfy를 다시 사용할까요?",
            "resume_confirm_body": "플러그인이 처음 설치한 것처럼 기본 설정으로 시작합니다.",
            "resume_btn": "다시 사용",
            "resume_done": "Prefixfy가 다시 작동합니다",
            "resume_failed": "플러그인을 시작하지 못했습니다. 껐다가 다시 켜세요.",
            "wipe_auto_reset_done": "플러그인 데이터가 손상되어 초기화했습니다",
            "setup_step_1": "1/3단계: 언어",
            "setup_step_2": "2/3단계: 꾸미기",
            "setup_step_3": "3/3단계: 업데이트",
            "setup_next": "다음",
            "setup_next_subtext": "{step}/3단계로 이동",
            "setup_back": "이전",
            "setup_back_subtext": "{step}/3단계로 돌아가기",
            "setup_finish": "설정 완료",
            "setup_finish_subtext": "업데이트를 확인해 있으면 설치하고, 전체 설정을 엽니다.",
            "setup_checking": "계정을 확인하는 중…",
            "setup_checking_subtext": "서버에서 블랙리스트를 받아오는 중입니다. 몇 초 걸립니다.",
            "setup_done": "초기 설정을 마쳤습니다",
            "setup_almost_update": "거의 다 됐습니다. 플러그인 업데이트만 남았습니다",
            "setup_finish_update_subtext": "{version} 버전이 있습니다. 확인 후 플러그인을 업데이트하고 전체 설정을 엽니다.",
            "welcome_banner": "Prefixfy를 설치해 주셔서 감사합니다!",
            "welcome_banner_subtext": "눌러서 플러그인으로 할 수 있는 일과 시작 방법을 확인하세요.",
            "welcome_title": "Prefixfy에 오신 것을 환영합니다",
            "welcome_body": "Prefixfy는 메시지에 마스크를 더합니다. 메시지 앞뒤의 텍스트, 꾸미기, 장식입니다.\n\n할 수 있는 일:\n• Markdown, 텍스트 스타일, 구분자를 쓴 마스크\n• 귀여운 효과: 카오모지, UwU, 장식\n• 메시지에 첨부되는 미디어\n• 예외: 플러그인을 쓰지 않을 채팅, 또는 그 채팅에서만 쓰기\n• 가져오기, 내보내기, 일정을 지원하는 여러 구성\n• 계정별 설정\n\n시작하기:\n1. ‘텍스트 꾸미기’에서 마스크를 정합니다.\n2. ‘적용 범위’에서 꾸밀 대상을 고릅니다.\n3. 채팅을 제외하거나 되돌리려면 그 채팅의 메뉴를 엽니다.\n\n이제 메시지를 쓰기만 하면 됩니다.",
            "welcome_ok": "확인",
            "updated_banner": "업데이트가 완료되었습니다",
            "updated_banner_subtext": "눌러서 확인하기",
        },
        "fr": {
            "editor_empty_means_default": "Laissez le champ vide et touchez « Enregistrer » pour revenir à la valeur par défaut.",
            "action_save": "Enregistrer",
            "action_delete": "Supprimer",
            "action_cancel": "Annuler",
            "action_create": "Créer",
            "action_apply": "Appliquer",
            "action_next": "Suivant",
            "error_operation_failed": "Une erreur est survenue",
            "section_scope": "Où il agit",
            "section_language": "Langue du plugin",
            "section_configurations": "Configurations",
            "section_appearance": "Apparence du texte",
            "section_general": "Général",
            "section_about": "À propos",
            "section_accounts": "Comptes",
            "section_updates": "Mises à jour et vérification",
            "section_cute": "Effets mignons",
            "plugin_enable": "Mode liste noire",
            "plugin_enable_subtext": "Activé : le plugin agit partout sauf dans les chats de la liste. Désactivé : uniquement dans les chats de la liste (liste blanche).",
            "language": "Langue",
            "language_auto": "Comme dans Telegram",
            "language_auto_subtext": "Utilise la langue de l’interface de Telegram. Désactivez pour choisir vous-même.",
            "scope_message": "Messages",
            "scope_message_subtext": "Mettre en forme les messages texte ordinaires.",
            "scope_media": "Légendes des médias",
            "scope_media_subtext": "Mettre en forme les légendes des photos, vidéos et fichiers.",
            "scope_edit": "Lors de la modification",
            "scope_edit_subtext": "Mettre en forme les messages modifiés. Le texte déjà mis en forme ne change pas.",
            "skip_once_expired": "Saut expiré : le prochain message sera mis en forme",
            "chat_config_menu": "Configuration de ce chat",
            "chat_config_auto": "Principale (selon le planning)",
            "chat_config_saved": "Configuration du chat enregistrée",
            "chat_config_reset": "Le chat utilise de nouveau la configuration principale",
            "skip_once_menu": "Ne pas mettre en forme le prochain message",
            "skip_once_on": "Le prochain message partira sans mise en forme",
            "skip_once_off": "Saut annulé",
            "chat_types": "Types de chats",
            "chat_types_hint": "Mettre en forme uniquement dans les types de chats choisis.",
            "chat_types_all": "Tous les chats",
            "chat_types_none": "Choisissez au moins un type",
            "chat_type_private": "Privés",
            "chat_type_group": "Groupes",
            "chat_type_channel": "Canaux",
            "scope_edit_message": "Texte modifié",
            "scope_edit_message_subtext": "Mettre en forme les messages ordinaires après modification.",
            "scope_edit_media": "Légendes modifiées",
            "scope_edit_media_subtext": "Mettre en forme les légendes des médias après modification.",
            "scope_article": "Articles",
            "scope_article_subtext": "Mettre en forme les blocs de texte des articles à l’envoi.",
            "scope_edit_article": "Articles modifiés",
            "scope_edit_article_subtext": "Mettre en forme les articles après modification.",
            "skip_once_on_edit": "Le saut s’applique aussi aux modifications",
            "skip_once_on_edit_subtext": "Si un saut est actif, la prochaine modification dans le chat reste aussi sans mise en forme.",
            "mask": "Masque",
            "mask_text": "Texte du masque",
            "markdown_style": "Style Markdown",
            "markdown_style_subtext": "Marqueurs dans le masque ou un seul style pour tout le masque.",
            "markdown_style_pick": "Style",
            "md_manual": "Marqueurs manuels",
            "md_bold": "Tout le masque en gras",
            "md_italic": "Tout le masque en italique",
            "md_strike": "Tout le masque barré",
            "md_spoiler": "Tout le masque en spoiler",
            "md_mono": "Tout le masque en monospace",
            "mask_rotation": "Rotation des masques",
            "mask_rotation_subtext": "Utiliser les masques de la liste au lieu du principal. Le masque du chat est prioritaire.",
            "masks_list": "Liste des masques",
            "masks_list_count": "Masques : {n}",
            "masks_list_empty": "Un masque par ligne",
            "masks_list_hint": "Un masque par ligne, chacun avec exactement un [text].",
            "masks_list_invalid": "Chaque masque doit contenir exactement un [text]",
            "masks_list_limit": "{n} masques au maximum",
            "mask_tags_hint": "Balises : [date], [time], [datetime], [chat], [id], [weekday], [year], [month], [day], [username], [count], [random_emoji], [hour], [minute], [second], [time12], [ampm], [daypart], [week], [yearday], [monthname], [weekday_short], [year_short], [timestamp], [tz], [chattype], [dice].\n[reply] — nom de la personne à qui vous répondez ; [chatcount] — numéro de votre message dans ce chat ; [battery] — niveau de batterie ; [moon] — phase de la lune ; [line] — une ligne au hasard de votre liste ; [since:2026-12-31] / [until:2026-12-31] — jours écoulés / restants ; [quote] — début du message auquel vous répondez ; [countdown:2026-12-31 18:00] — temps restant avant un moment ; [weather] / [weather:Paris] — température depuis wttr.in (Internet requis).",
            "mask_rotation_mode": "Ordre de rotation",
            "mask_rotation_mode_random": "Au hasard",
            "mask_rotation_mode_sequential": "À tour de rôle",
            "mask_editor_title": "Masque",
            "mask_editor_hint": "[text] est votre message, [text: lien] est votre message avec un lien.",
            "mask_invalid": "Le masque doit contenir exactement un [text]",
            "unsafe_text_rejected": "Le texte avec inversion de sens (RTL), caractères invisibles ou de contrôle, Zalgo ou chaîne d’émojis trop longue n’est pas accepté",
            "mask_too_long": "Masque trop long : {n} caractères au maximum",
            "mask_preview_sample": "Exemple de message",
            "mask_preview_invalid": "Masque endommagé : il faut exactement un [text]",
            "conditional_masks": "Masques selon le contenu",
            "conditional_masks_hint": "Une règle par ligne : expression régulière => masque. Le masque de la première règle qui correspond au texte est utilisé. Chaque masque doit contenir exactement un [text].",
            "conditional_masks_count": "Règles : {n}",
            "conditional_masks_empty": "Un masque à part pour les messages contenant un texte précis",
            "conditional_masks_format": "Ligne {n} : format attendu « expression => masque »",
            "md_quote": "Tout le masque en citation",
            "text_style": "Style du texte",
            "text_style_random": "Style aléatoire",
            "text_style_random_subtext": "Un nouveau style pour chaque message (sauf à l’envers).",
            "text_style_subtext": "Ne change que le texte du message. Fancy, Bold, Gothic et Circled fonctionnent avec l’alphabet latin, L33T aussi avec le cyrillique.",
            "text_style_enable": "Activer le style du texte",
            "text_style_translit": "Translittérer le cyrillique",
            "text_style_translit_subtext": "Les styles latins fonctionneront aussi avec le russe et l’ukrainien.",
            "style_words": "Styliser seulement certains mots",
            "style_words_hint": "Un mot par ligne. Liste vide : le style s’applique à tout le texte.",
            "style_words_count": "Mots : {n}",
            "style_words_empty": "Tout le texte",
            "style_words_limit": "{n} mots au maximum",
            "tag_lines": "Lignes pour [line]",
            "tag_lines_hint": "Une ligne par rangée, jusqu’à 64 caractères. La balise [line] en insère une au hasard.",
            "tag_lines_count": "Lignes : {n}",
            "tag_lines_empty": "Aucune ligne pour l’instant",
            "tag_lines_limit": "{n} lignes au maximum",
            "separator": "Séparateur",
            "separator_enable": "Activer le séparateur",
            "separator_enable_subtext": "Insérer vos propres séparateurs entre les mots.",
            "separator_set": "Jeu de séparateurs",
            "separator_count": "Séparateurs entre les mots",
            "separator_count_subtext": "Touchez pour modifier.",
            "separator_custom_title": "Jeu personnalisé",
            "separator_custom_message": "Saisissez les séparateurs séparés par des virgules, par exemple :\n•, ·, —, ~, |",
            "separator_preview_sample": "Exemple de texte pour l’aperçu",
            "separator_frequency": "Fréquence des séparateurs",
            "separator_frequency_subtext": "Probabilité d’un séparateur entre deux mots voisins. 100 % : entre chaque paire.",
            "separator_spaces": "Espaces autour du séparateur",
            "separator_spaces_subtext": "Désactivé : le séparateur est collé aux mots : salut•ça•va.",
            "separator_space_mode": "Où placer les espaces",
            "separator_space_both": "Des deux côtés",
            "separator_space_left": "À gauche seulement",
            "separator_space_right": "À droite seulement",
            "cute_enabled": "Activer les effets mignons",
            "cute_enabled_subtext": "Kaomoji, UwU, actions et décorations. Les liens, @mentions, #hashtags et le code ne changent pas.",
            "cute_preview": "Aperçu",
            "section_debug": "Débogage",
            "debug_enabled": "Débogage activé",
            "debug_disabled": "Débogage désactivé",
            "debug_start": "Démarrer l’enregistrement",
            "debug_start_subtext": "Enregistre toutes les actions du plugin : touches, changements de réglages, dialogues, notifications, traitement des messages (longueurs seulement, sans texte) et le journal interne. Les valeurs de réglages modifiées et les ID de chats y figurent : vérifiez-le avant de l’envoyer à qui que ce soit.",
            "debug_stop": "Arrêter l’enregistrement",
            "debug_recording": "Enregistrement · {amount}",
            "debug_log": "Journal de débogage",
            "debug_log_subtext": "{amount}. Touchez pour enregistrer, supprimer ou reprendre l’enregistrement.",
            "debug_amount": "{lines} lignes, {size}",
            "debug_actions_message": "Enregistrement arrêté ({amount}). Que faire du journal ?",
            "debug_to_saved": "Envoyer dans les Messages enregistrés",
            "debug_to_device": "Enregistrer sur l’appareil",
            "debug_delete": "Supprimer le journal",
            "debug_continue": "Reprendre l’enregistrement",
            "debug_hide": "Masquer le débogage",
            "debug_hide_subtext": "Arrête l’enregistrement et supprime le journal. Comme 7 touches rapides sur « Aperçu ».",
            "debug_started": "Enregistrement du journal démarré",
            "debug_exported": "Journal de débogage enregistré",
            "debug_deleted": "Journal de débogage supprimé",
            "debug_hidden": "Débogage masqué",
            "debug_failed": "L’action sur le journal a échoué",
            "cute_preview_sample": "Salut ! Ça va ? Il fait super beau aujourd’hui.",
            "cute_preview_none": "Activez au moins un effet. Touchez pour actualiser.",
            "cute_preview_tap": "Touchez pour actualiser.",
            "cute_sentence_frequency": "Fréquence des effets de phrase",
            "cute_sentence_frequency_subtext": "Kaomoji, étincelles, ponctuation, suffixes et actions.",
            "cute_word_frequency": "Fréquence des effets de mot",
            "cute_word_frequency_subtext": "Bégaiement, voyelles étirées et signe mou.",
            "cute_kaomoji": "Kaomoji en fin de phrase (◕‿◕)",
            "cute_sparkles": "Étincelles autour de la phrase ✨",
            "cute_exclamations": "Exclamations mignonnes (! → !✨)",
            "cute_punctuation": "Ponctuation mignonne (. → .~, ? → ?✨)",
            "cute_uwu_suffixes": "Terminaisons UwU (nya~, owo)",
            "cute_actions": "Actions mignonnes (*fait un câlin*)",
            "cute_actions_newline": "Actions sur une nouvelle ligne",
            "cute_lowercase": "Minuscules uniquement",
            "cute_uwu_speak": "Parler UwU (r/l → w, р/л → в)",
            "cute_stutter": "Bégaiement (s-salut)",
            "cute_stretch": "Étirer les voyelles (mignooon)",
            "cute_stretch_max": "Combien étirer les voyelles",
            "cute_stretch_2x": "Double (x2)",
            "cute_stretch_3x": "Triple (x3)",
            "cute_soft_sign": "Signe mou à la fin des mots (котикь)",
            "cute_soft_sign_subtext": "Mots russes uniquement.",
            "regex_exceptions": "Exceptions regex",
            "regex_exceptions_hint": "Une expression régulière par ligne. Les messages correspondants ne sont pas mis en forme.",
            "regex_exceptions_count": "Règles : {n}",
            "regex_exceptions_empty": "Pour utilisateurs avancés",
            "regex_exceptions_invalid": "Expression invalide : {error}",
            "regex_exceptions_limit": "{n} expressions au maximum, {m} caractères chacune",
            "exceptions": "Exceptions",
            "ignore_emoji_only": "Ignorer les messages composés seulement d’emoji",
            "ignore_emoji_only_subtext": "Les messages composés uniquement d’emoji ne sont pas mis en forme. Les légendes des médias ne sont pas concernées.",
            "exceptions_hint": "Les messages qui commencent ou finissent par ce texte ne sont pas mis en forme. Une valeur par ligne.",
            "ignore_code": "Ne pas toucher au code",
            "ignore_code_subtext": "Les blocs ``` et le `code en ligne` restent tels quels.",
            "ignore_commands": "Ne pas toucher aux commandes",
            "ignore_commands_subtext": "Les commandes comme /start ou /help@bot restent telles quelles. Un message qui commence par une commande n’est pas mis en forme.",
            "ignore_mentions": "Ne pas toucher aux mentions",
            "ignore_mentions_subtext": "Les @username restent tels quels. Un message qui commence par une mention n’est pas mis en forme.",
            "ignore_links": "Ne pas toucher aux liens",
            "ignore_links_subtext": "Les liens, adresses de sites et e-mails restent tels quels. Un message qui n’est qu’un lien n’est pas mis en forme.",
            "ignore_hashtags": "Ne pas toucher aux #hashtags",
            "ignore_hashtags_subtext": "Les #hashtags restent tels quels.",
            "ignore_cashtags": "Ne pas toucher aux $cashtags",
            "ignore_cashtags_subtext": "$TON, $BTC et similaires restent tels quels.",
            "ignore_segments": "À ne pas toucher",
            "ignore_segments_hint": "Cochez les parties du message à laisser telles quelles.",
            "ignore_segments_count": "Activés : {n} sur {total}",
            "scope_targets": "Quoi mettre en forme",
            "scope_targets_hint": "Choisissez où le plugin applique la mise en forme.",
            "scope_edit_targets": "Réglages de modification",
            "scope_edit_targets_hint": "Choisissez quoi mettre en forme lors de la modification d'un message.",
            "exceptions_chat_menu": "Exceptions : ajouter ou retirer le chat",
            "exceptions_chat_added": "Chat ajouté aux exceptions",
            "exceptions_chat_removed": "Chat retiré des exceptions",
            "exceptions_chat_now_off": "Prefixfy ne décore plus les messages dans ce chat",
            "exceptions_chat_now_on": "Prefixfy décore de nouveau les messages dans ce chat",
            "exceptions_chat_other_config": "La liste a été modifiée, mais ce chat suit une autre configuration (liaison de chat, planning ou réglages du compte)",
            "exceptions_count": "Règles : {n}, chats : {m}",
            "capture_custom_emoji": "Obtenir le code d’un Premium Emoji",
            "capture_custom_emoji_enabled": "Envoyez un message avec un Premium Emoji : le plugin vous renverra son code",
            "capture_custom_emoji_disabled": "Capture du code Premium Emoji annulée",
            "capture_custom_emoji_hint": "Premium Emoji dans un masque : (id|🙂), où 🙂 est un emoji ordinaire pour ceux qui n’ont pas Premium. Obtenez le code avec « Obtenir le code d’un Premium Emoji » dans le menu du chat.",
            "schedule": "Planning des configurations",
            "schedule_empty": "Non défini",
            "schedule_count": "Règles : {n}",
            "schedule_message": "Une règle par ligne : condition = configuration.\nConditions : heure HH:MM-HH:MM ou moment de la journée (matin 05–12, après-midi 12–17, soir 17–23, nuit 23–05, ou plage comme « matin-soir ») ; jours (mon-fri, sat,sun, weekend, weekdays) ; date AAAA-MM-JJ, JJ.MM.AAAA ou JJ.MM (chaque année), « .. » pour une plage ; type de chat (private, group, channel) ; « chat ID » ; « account ID » ; « random N% » (tiré à chaque message).\nCombinez les conditions avec and, or, not et des parenthèses ; sans mot entre elles, « and » est sous-entendu. « else » est la règle pour tous les autres cas. Les mots russes и, или, не, иначе fonctionnent aussi.\nLes règles avec date l’emportent, « else » est vérifiée en dernier, et à égalité la première règle qui correspond gagne. Les jours et dates d’un intervalle qui passe minuit se rapportent au jour où il a commencé. Les chats ayant leur propre configuration ne suivent pas le planning.",
            "schedule_hint": "22:00-07:00 = Nuit\n09:00-18:00 mon-fri = Travail\n(31.12 or 01.01) and not channel = Fête\ngroup and soir = Calme\nchat -1001234567890 = Spécial\nrandom 20% = Fun\nelse = Défaut",
            "schedule_saved": "Planning enregistré",
            "schedule_error": "Ligne {n} : {reason}",
            "schedule_err_format": "format attendu : condition = configuration",
            "schedule_err_time": "heure invalide",
            "schedule_err_days": "jours invalides",
            "schedule_err_config": "aucune configuration « {name} »",
            "schedule_err_limit": "{n} règles au maximum",
            "schedule_err_date": "date invalide",
            "schedule_err_unknown": "« {x} » n’est pas compris",
            "schedule_err_parens": "parenthèses non appariées",
            "schedule_err_deep": "condition trop complexe",
            "schedule_err_random": "le pourcentage doit être de 0 à 100",
            "schedule_err_size": "trop de texte",
            "config_import_cancelled": "Importation annulée",
            "config_import": "Importer",
            "config_export": "Exporter",
            "config_reset": "Rétablir les valeurs par défaut",
            "config_reset_to_plugin": "Ignorer les valeurs importées : revenir aux réglages standard du plugin",
            "config_reset_to_plugin_unavailable": "Indisponible : cette configuration a été créée dans le plugin, la réinitialisation la ramène déjà à son état d’origine.",
            "config_active": "Configuration active",
            "config_new": "Nouvelle configuration",
            "config_new_subtext": "Un jeu de réglages séparé. Il devient actif dès sa création.",
            "config_name_hint": "Nom de la configuration",
            "config_new_source_title": "Base de la nouvelle configuration",
            "config_new_source_message": "Sur quoi la baser ? Sans choix, les réglages par défaut sont utilisés.",
            "config_new_copy_current": "Copier les réglages de la configuration actuelle",
            "config_delete": "Supprimer la configuration",
            "config_delete_confirm": "Supprimer la configuration « {name} » ?",
            "config_delete_none": "Aucune configuration inactive à supprimer",
            "config_imported_name": "Configuration importée",
            "config_rename": "Renommer la configuration",
            "config_rename_subtext": "Changer le nom de la configuration actuelle.",
            "config_name_invalid": "Saisissez un nom qui n’est pas encore utilisé.",
            "config_name_taken": "Une configuration porte déjà ce nom.",
            "config_deleted": "Configurations supprimées : {n}",
            "config_delete_multi": "Supprimer des configurations",
            "config_delete_multi_subtext": "Supprimer les configurations inactives. L’active est conservée.",
            "config_delete_multi_select": "Choisissez les configurations inactives à supprimer.",
            "config_import_new_name": "Nom de la nouvelle configuration",
            "config_parts_title": "Parties de la configuration",
            "config_parts_message": "Choisissez les parties à utiliser ({n} disponibles).",
            "config_part_mask": "Masque",
            "config_part_separator": "Séparateurs",
            "config_part_exceptions": "Exceptions et chats",
            "config_part_exceptions_reset": "Exceptions, chats et portée",
            "config_part_language": "Langue du plugin",
            "config_part_media": "Média",
            "config_import_done": "Configuration importée",
            "config_import_take_name_title": "Nom de la configuration",
            "config_import_take_name": "Le fichier contient le nom « {name} ». La configuration actuelle s’appelle « {current} ».",
            "config_import_take_name_yes": "Utiliser « {name} »",
            "config_import_take_name_no": "Garder « {current} »",
            "config_import_links_title": "Liens dans la configuration",
            "config_import_links_message": "Le fichier contient des liens. Ils peuvent apparaître dans vos messages envoyés :",
            "config_import_links_more": "…et {n} de plus",
            "config_import_failed": "Impossible d’importer la configuration",
            "config_import_locked": "L’importation sera disponible après la configuration initiale.",
            "config_save_failed": "Impossible d’enregistrer la configuration",
            "config_export_done": "Configuration exportée",
            "config_export_failed": "Impossible d’exporter la configuration",
            "config_export_destination_title": "Où enregistrer ?",
            "config_export_to_saved": "Dans les Messages enregistrés du compte actuel",
            "config_export_to_device": "Dans la mémoire de l’appareil",
            "config_restored": "Valeurs choisies réinitialisées",
            "config_parts_none": "Choisissez au moins une partie",
            "config_export_select": "Quelles configurations exporter ?",
            "config_export_select_subtext": "Vous pouvez en choisir jusqu’à {n}. Pour chacune, vous choisirez ensuite les parties. Si vous en choisissez plusieurs, les fichiers partent directement dans les Messages enregistrés du compte actuel.",
            "config_shared_marker": "partagée",
            "config_export_parts_title": "Parties : {name}",
            "config_export_parts_progress": "Configuration {i} sur {n}",
            "config_export_limit": "Vous pouvez choisir {n} configurations au maximum",
            "config_export_none": "Choisissez au moins une configuration",
            "config_export_done_multi": "Configurations exportées : {n}",
            "config_export_partial": "{ok} sur {total} exportées",
            "config_import_found_title": "Fichier de configuration",
            "config_import_found_contains": "À importer :",
            "config_part_state_default": "par défaut",
            "config_part_state_absent": "absent du fichier",
            "config_import_nothing": "Rien à importer : les parties choisies sont absentes du fichier ou déjà aux valeurs par défaut",
            "config_import_skipped": "Ignoré, rien à importer : {parts}",
            "config_import_as_new": "Importer comme nouvelle configuration",
            "config_export_encrypt": "Chiffrer avec un mot de passe",
            "config_export_encrypting": "Chiffrement du fichier…",
            "password_export_title": "Mot de passe du fichier",
            "password_export_title_named": "Mot de passe pour « {name} »",
            "password_export_message": "Le fichier entier est chiffré : sans le mot de passe, même la liste de ses parties est invisible. Le mot de passe n’est enregistré nulle part et ne peut pas être récupéré.",
            "password_import_title": "Fichier protégé par mot de passe",
            "password_import_message": "Saisissez le mot de passe pour voir les parties contenues dans le fichier.",
            "password_wrong": "Mot de passe incorrect ou fichier endommagé. Réessayez.",
            "password_checking": "Vérification du mot de passe…",
            "password_hint": "Mot de passe",
            "password_repeat_hint": "Répétez le mot de passe",
            "password_length": "De {min} à {max} caractères",
            "password_mismatch": "Les mots de passe ne correspondent pas",
            "config_import_file_failed": "Impossible d’ouvrir le fichier de configuration",
            "config_import_invalid": "Le fichier ne contient aucune des parties choisies ou il est endommagé.",
            "config_default_name": "Configuration par défaut",
            "config_numbered_name": "Configuration {n}",
            "config_actions_subtext": "Choisir les parties à utiliser",
            "config_part_schedule": "Liaisons des chats et planning",
            "config_part_cute": "Effets mignons",
            "media_attachment": "Média",
            "media_attachment_enable": "Joindre un média",
            "media_attachment_enable_subtext": "Envoyer le fichier choisi avec chaque message.",
            "media_file": "Fichier",
            "media_file_none": "Aucun fichier choisi",
            "media_import": "Choisir un média",
            "media_delete": "Supprimer le média",
            "media_delete_subtext": "Retirer le fichier choisi de Prefixfy.",
            "media_delete_confirm": "Supprimer le média « {name} » ? Le fichier sera retiré de Prefixfy définitivement.",
            "media_imported": "Média ajouté",
            "media_deleted": "Média supprimé",
            "media_import_failed": "Impossible d’ajouter le média",
            "media_delete_failed": "Impossible de supprimer le média",
            "account_mode": "Réglages par compte",
            "account_mode_subtext": "Des réglages séparés pour chaque compte. Tant que vous ne les modifiez pas, tous les comptes partagent les mêmes.",
            "account_target": "Compte à régler",
            "account_auto": "Auto (compte actuel)",
            "account_common": "Partagés (pour tous)",
            "account_auto_now": "Sélectionné actuellement",
            "account_editing": "Vous réglez",
            "account_own": "réglages propres",
            "account_shared": "réglages partagés",
            "account_common_hint": "réglages partagés (pour les comptes sans réglages propres)",
            "account_none": "compte non détecté",
            "account_reset": "Revenir aux réglages partagés",
            "account_reset_subtext": "Supprimer les réglages propres de ce compte.",
            "account_reset_title": "Réinitialiser les réglages du compte",
            "account_reset_confirm": "Supprimer les réglages propres de ce compte ainsi que ses configurations ? Le compte utilisera de nouveau les réglages partagés.",
            "account_reset_button": "Réinitialiser",
            "account_reset_done": "Le compte utilise de nouveau les réglages partagés",
            "account_import_title": "Où appliquer la configuration ?",
            "account_import_all": "À tous les comptes",
            "account_import_common": "Aux réglages partagés (comptes sans réglages propres)",
            "check_now": "Vérifier maintenant",
            "check_now_subtext": "S’assurer que la version du plugin est officielle.",
            "check_started": "Vérification…",
            "check_confirm_title": "Vérifier la version ?",
            "check_confirm_body": "Ce qui se passe : le plugin télécharge à nouveau les données de vérification (manifeste, liste noire, profil de réglages) sans passer par le cache et s’assure que le build est officiel. Les données enregistrées ne sont remplacées qu’après une vérification réussie.\n\nQuand l’utiliser : le build n’a pas pu être confirmé et les fonctions sont suspendues, vous venez de mettre à jour ou de réinstaller le plugin, ou le statut semble périmé.\n\nC’est sans risque : les réglages et configurations ne sont pas touchés. Internet est requis. Si GitHub ne répond pas, le plugin réessaie puis essaie un miroir. Si la vérification échoue malgré tout, rien ne change.",
            "check_confirm_yes": "Vérifier",
            "check_ok": "Vérification réussie",
            "check_failed": "Échec de la vérification. Vérifiez votre connexion et réessayez.",
            "ota_auto": "Mise à jour automatique",
            "ota_auto_subtext": "Le plugin télécharge et installe lui-même les mises à jour en vérifiant la signature et les sommes de contrôle.",
            "ota_mode": "Quand mettre à jour",
            "ota_mode_available": "Dès la sortie",
            "ota_mode_time": "À l’heure choisie",
            "ota_action": "Que faire d’une mise à jour",
            "ota_action_download": "Télécharger seulement",
            "ota_action_install": "Télécharger et installer",
            "ota_time": "Heure de mise à jour",
            "ota_time_subtext": "Heure de l’appareil au format HH:MM, par exemple 04:00.",
            "ota_time_invalid": "Saisissez l’heure au format HH:MM, par exemple 04:00",
            "ota_disabled": "Mises à jour à distance désactivées",
            "ota_disabled_subtext": "Le développeur les a désactivées pour le moment. Installez la nouvelle version manuellement depuis le dépôt.",
            "ota_installed": "Prefixfy {version} installé. Redémarrage…",
            "ota_restart_manual": "Prefixfy {version} installé. Désactivez puis réactivez le plugin pour l’appliquer.",
            "ota_modified_found": "Le fichier du plugin a été modifié. Installation de la version officielle {version}…",
            "ota_failed": "Échec de la mise à jour : {reason}",
            "ota_busy": "Une mise à jour est déjà en cours",
            "ota_check_note": "Cette vérification n’installe pas la nouvelle version : vous recevrez une notification, et vous pourrez l’installer avec « Télécharger » sous « Mise à jour requise ».",
            "ota_almost_ready": "Presque prêt",
            "ota_almost_ready_subtext": "La version {version} est téléchargée. Il reste à redémarrer le plugin.",
            "ota_reload": "Redémarrer",
            "ota_reload_subtext": "Appliquer la mise à jour et redémarrer le plugin.",
            "ota_staged": "Prefixfy {version} téléchargé. Touchez « Redémarrer ».",
            "ota_download": "Télécharger",
            "check_update_found": "Prefixfy {version} est disponible. Touchez « Télécharger » sous « Mise à jour requise ».",
            "ota_download_subtext": "Version {version}. D’abord, les détails de la mise à jour.",
            "ota_dl_title": "Mise à jour de Prefixfy",
            "ota_dl_size": "Taille",
            "ota_dl_changelog": "Nouveautés",
            "ota_dl_changelog_none": "Le développeur n’a fourni aucune information",
            "ota_dl_confirm": "Télécharger et installer",
            "ota_dl_warning": "En données mobiles, votre opérateur peut facturer le trafic. Le Wi-Fi est préférable.",
            "ota_unit_kb": "Ko",
            "ota_unit_mb": "Mo",
            "gate_update_required": "Mise à jour requise",
            "gate_update_required_subtext": "Installez la version officielle de Prefixfy {version}. D’ici là, le plugin ne met pas les messages en forme.",
            "gate_verify_required": "Échec de la vérification",
            "gate_verify_required_subtext": "La version n’a pas pu être vérifiée, la mise en forme est désactivée. Vérifiez votre connexion.",
            "gate_account_blocked": "Accès refusé",
            "gate_account_blocked_subtext": "Un des comptes de cet appareil figure sur la liste noire de Prefixfy. Le plugin est désactivé.",
            "about_plugin": "À propos du plugin",
            "about_plugin_subtext": "Version, build et statut de vérification.",
            "about_title": "À propos de Prefixfy",
            "about_version": "Version",
            "about_build_date": "Date du build",
            "about_build_number": "Numéro du build du jour",
            "about_serial": "Numéro de série",
            "about_build_label": "Étiquette complète du build",
            "about_latest": "Dernier build officiel",
            "about_status": "Vérification",
            "about_unknown": "inconnu",
            "about_note": "Ces informations proviennent de l’étiquette de build du fichier du plugin.",
            "status_ok": "réussie : le build correspond à la version officielle",
            "status_pending": "pas encore effectuée",
            "status_soft": "non confirmée : les fonctions supplémentaires sont suspendues",
            "status_blacklisted": "refusée : un compte est sur liste noire",
            "status_no_key": "échouée : ce build n’a pas de clé de mise à jour",
            "status_integrity": "non confirmée : le fichier du plugin n’a pas pu être lu",
            "notice_ok": "OK",
            "status_outdated": "échouée : le build est obsolète, une nouvelle version est sortie",
            "status_modified": "échouée : le build a été modifié",
            "gate_modified": "Build modifié",
            "gate_modified_subtext": "Le fichier Prefixfy diffère de la version officielle {version}. Le plugin installera lui-même le build officiel ; d’ici là, la mise en forme est désactivée.",
            "notice_verify_body": "Ce qui s’est passé : ce build ne peut pas être vérifié, car il n’a pas de clé valide pour le manifeste signé.\n\nCe que cela signifie : le plugin ne met pas en forme les messages sortants. Vos réglages sont conservés.\n\nQue faire : installez le build officiel depuis le dépôt.",
            "notice_soft_body": "Ce qui s’est passé : Prefixfy ne peut pas confirmer que le build est officiel. La vérification du manifeste signé ou de la liste noire n’a pas abouti : pas d’Internet, GitHub inaccessible, dernière vérification trop ancienne ou fichier du plugin illisible.\n\nCe qui est suspendu : toutes les fonctions supplémentaires — styles, Markdown, rotation et masques selon le contenu, balises, planning, configurations de chat, média, Premium Emoji, mise en forme des modifications et importation. Seul le masque de base fonctionne.\n\nQue faire : vérifiez votre connexion et touchez « Vérifier maintenant ». Tout revient de lui-même après une vérification réussie.",
            "notice_account_body": "Ce qui s’est passé : un des comptes Telegram de cet appareil figure sur la liste noire de Prefixfy.\n\nCe que cela signifie : le plugin est désactivé sur cet appareil. Vos réglages ne changent pas.\n\nSi vous pensez que c’est une erreur, contactez l’auteur du plugin.",
            "gate_soft": "Fonctions suspendues",
            "gate_soft_subtext": "Le build ne peut pas être vérifié pour l’instant, seule la mise en forme de base fonctionne. Vérifiez votre connexion : tout revient après une vérification réussie.",
            "gate_bypass_note": "Cette fonction ne lève pas le blocage.",
            "wipe_row": "Supprimer les données",
            "wipe_row_subtext": "Effacer toutes les données du plugin ou arrêter complètement de l’utiliser.",
            "wipe_title": "Supprimer les données de Prefixfy ?",
            "wipe_body": "Toutes les données du plugin seront supprimées : configurations et réglages des comptes, réglages partagés, médias, fichiers importés et cache de vérification. Le plugin redémarre et commence par l’assistant de configuration, comme après l’installation.\n\nSi le plugin est obsolète, la dernière version est d’abord installée, puis les données sont supprimées.\n\n« Arrêter d’utiliser le plugin » le désactive en plus : seul le bouton « Reprendre » reste. Aucune mise à jour n’est téléchargée dans ce cas.",
            "wipe_opt_out": "Arrêter d’utiliser le plugin",
            "wipe_confirm_clean": "Tous les fichiers et réglages du plugin seront supprimés. Le plugin redémarre plusieurs fois (c’est normal) et commence par l’assistant de configuration. Les configurations et médias seront perdus définitivement : exportez d’abord ce que vous voulez garder.",
            "wipe_confirm_title": "Confirmer la suppression",
            "wipe_confirm_out": "Tous les fichiers et réglages du plugin seront supprimés, puis le plugin se désactivera. C’est irréversible.",
            "wipe_confirm_btn": "Supprimer",
            "wipe_started": "Préparation de la suppression…",
            "wipe_started_multi": "Préparation de la suppression… Le plugin va redémarrer plusieurs fois.",
            "wipe_halt": "Nettoyage en cours",
            "wipe_halt_subtext": "Le plugin va redémarrer encore une fois et repartir de zéro.",
            "wipe_updating": "Mise à jour vers {version}, puis suppression des données…",
            "wipe_reinstalling": "Réinstallation du build {version}, puis suppression des données…",
            "wipe_update_failed": "Impossible de mettre à jour le plugin : {reason}. Rien n’a été supprimé.",
            "wipe_restart_manual": "Désactivez puis réactivez le plugin pour terminer la suppression.",
            "wipe_failed": "Impossible de préparer la suppression. Rien n’a été supprimé.",
            "wipe_done": "Données supprimées, le plugin est reparti de zéro",
            "resume_title": "Reprendre",
            "resume_subtext": "Prefixfy est désactivé et ne conserve aucune donnée. Touchez pour recommencer.",
            "resume_confirm_title": "Reprendre Prefixfy ?",
            "resume_confirm_body": "Le plugin démarre comme s’il venait d’être installé, avec les réglages par défaut.",
            "resume_btn": "Reprendre",
            "resume_done": "Prefixfy fonctionne de nouveau",
            "resume_failed": "Impossible de démarrer le plugin. Désactivez-le puis réactivez-le.",
            "wipe_auto_reset_done": "Les données du plugin étaient endommagées, il a donc été réinitialisé",
            "setup_step_1": "Étape 1 sur 3 : langue",
            "setup_step_2": "Étape 2 sur 3 : apparence",
            "setup_step_3": "Étape 3 sur 3 : mises à jour",
            "setup_next": "Suivant",
            "setup_next_subtext": "Passer à l’étape {step} sur 3",
            "setup_back": "Retour",
            "setup_back_subtext": "Revenir à l’étape {step} sur 3",
            "setup_finish": "Terminer la configuration",
            "setup_finish_subtext": "Le plugin recherche des mises à jour, les installe s’il y en a et ouvre tous les réglages.",
            "setup_checking": "Vérification du compte…",
            "setup_checking_subtext": "Demande de la liste noire au serveur. Cela prend quelques secondes.",
            "setup_done": "Configuration initiale terminée",
            "setup_almost_update": "Presque terminé, il ne reste qu’à mettre à jour le plugin",
            "setup_finish_update_subtext": "La version {version} est disponible : après la vérification, le plugin se met à jour et ouvre tous les réglages.",
            "welcome_banner": "Merci d’avoir installé Prefixfy !",
            "welcome_banner_subtext": "Touchez pour découvrir ce que fait le plugin et comment commencer.",
            "welcome_title": "Bienvenue dans Prefixfy",
            "welcome_body": "Prefixfy ajoute un masque à vos messages : du texte avant ou après le message, de la mise en forme et des décorations.\n\nCe qu’il sait faire :\n• un masque avec Markdown, styles de texte et séparateurs\n• des effets mignons : kaomoji, UwU, décorations\n• un média joint à vos messages\n• des exceptions : les chats où le plugin est désactivé, ou uniquement ceux-là\n• plusieurs configurations avec importation, exportation et planning\n• des réglages séparés pour chaque compte\n\nPour commencer :\n1. Définissez votre masque dans « Apparence du texte ».\n2. Choisissez ce qu’il faut mettre en forme dans « Où il agit ».\n3. Pour exclure un chat ou le réintégrer, ouvrez le menu dans ce chat.\n\nC’est tout : écrivez simplement vos messages.",
            "welcome_ok": "Compris",
            "updated_banner": "Mise à jour terminée",
            "updated_banner_subtext": "Touchez pour voir",
        },
    }

    SUPPORTED_AUTO = frozenset(("ru", "ja", "ko", "fr", "en"))
    LANGUAGE_ALIASES = {
        "jp": "ja", "kr": "ko",
        "russian": "ru", "english": "en", "japanese": "ja", "korean": "ko",
        "french": "fr",
    }
    RU_LIKE_CODES = frozenset(("ru", "uk", "be", "kk", "ky", "uz", "tg", "tk", "az", "hy", "ka", "tt", "ba", "cv", "os", "ce", "mo"))
    _ru_like = False
    AUTO_LANGUAGE_TTL = 5.0
    AUTO_LANGUAGE_REFRESH = 2.0

    def __init__(self, plugin):
        self.plugin = plugin
        self._auto_language: Optional[str] = None
        self._auto_checked = 0.0

    def refresh(self):
        if time.monotonic() - self._auto_checked > self.AUTO_LANGUAGE_REFRESH:
            self._auto_checked = 0.0

    @classmethod
    def _match_language(cls, value) -> Optional[str]:
        code = as_text(value).strip().lower().replace("-", "_")
        if not code:
            return None
        base = cls.LANGUAGE_ALIASES.get(code) or cls.LANGUAGE_ALIASES.get(code.split("_", 1)[0]) or code.split("_", 1)[0]
        return base if base in cls.SUPPORTED_AUTO and language_enabled(base) else None

    def _detect_interface_language(self) -> Optional[str]:
        try:
            locale_class = find_class("org.telegram.messenger.LocaleController")
            controller = locale_class.getInstance() if locale_class is not None else None
            info = controller.getCurrentLocaleInfo() if controller is not None else None
        except Exception as exc:
            self.plugin.log(f"Language detection failed: {exc}")
            return None
        if info is None:
            return None
        readable = False
        self._ru_like = False
        for attr in ("shortName", "pluralLangCode", "baseLangCode"):
            try:
                value = getattr(info, attr, None)
                if callable(value):
                    value = value()
            except Exception:
                continue
            if value:
                readable = True
                found = self._match_language(value)
                if found:
                    return found
                if as_text(value).strip().lower().replace("-", "_").split("_", 1)[0] in self.RU_LIKE_CODES:
                    self._ru_like = True
        if not readable:
            return None
        return "en" if language_enabled("en") and not self._ru_like else "ru"

    def language(self) -> str:
        forced = LANGUAGE_MODES[self.plugin.settings.language_index()]
        if forced and language_enabled(forced):
            return forced
        if not language_auto_enabled():
            return "ru"
        now = time.monotonic()
        if self._auto_language is None or now - self._auto_checked > self.AUTO_LANGUAGE_TTL:
            detected = self._detect_interface_language()
            self._auto_checked = now
            if detected is not None:
                self._auto_language = detected
            elif self._auto_language is None:
                self._auto_language = "ru"
        return self._auto_language

    def tr(self, key: str, **kwargs) -> str:
        table = self.STRINGS.get(self.language(), self.STRINGS["ru"])
        value = table.get(key) or self.STRINGS["en"].get(key) or self.STRINGS["ru"].get(key, key)
        if kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, IndexError, ValueError):
                for code in ("en", "ru"):
                    try:
                        return self.STRINGS[code][key].format(**kwargs)
                    except (KeyError, IndexError, ValueError):
                        continue
        return value

    def language_items(self) -> List[str]:
        names = self.LANGUAGE_ITEMS.get(self.language(), self.LANGUAGE_ITEMS["ru"])
        return [names[index - 1] for index in enabled_language_indices()]

    def invalidate(self):
        self._auto_language = None
        self._auto_checked = 0.0


_SYNODIC_MONTH = 29.530588853


def moon_phase_emoji(moment: Optional[float] = None) -> str:
    julian = (time.time() if moment is None else moment) / 86400.0 + 2440587.5
    age = (julian - 2451550.1) % _SYNODIC_MONTH
    return "\U0001F311\U0001F312\U0001F313\U0001F314\U0001F315\U0001F316\U0001F317\U0001F318"[int(age / _SYNODIC_MONTH * 8 + 0.5) % 8]


def days_tag_value(tag: str, today) -> str:
    kind, _, raw = tag.partition(":")
    try:
        target = _date.fromisoformat(raw)
    except ValueError:
        return ""
    delta = (target - today).days
    return str(max(0, -delta if kind == "since" else delta))


COUNTDOWN_UNITS = {
    "ru": ("д", "ч", "м"), "en": ("d", "h", "m"), "ja": ("日", "時間", "分"),
    "ko": ("일", "시간", "분"), "fr": ("j", "h", "min"),
}


def countdown_tag_value(tag: str, now, language: str) -> str:
    raw = tag.partition(":")[2]
    try:
        target = datetime.strptime(raw, "%Y-%m-%d %H:%M" if " " in raw else "%Y-%m-%d")
    except ValueError:
        return ""
    day, hour, minute = COUNTDOWN_UNITS.get(language, COUNTDOWN_UNITS["ru"])
    seconds = int((target - now).total_seconds())
    if seconds <= 0:
        return f"0{minute}"
    days, rest = divmod(seconds // 60, 1440)
    hours, minutes = divmod(rest, 60)
    if days:
        return f"{days}{day} {hours}{hour}"
    if hours:
        return f"{hours}{hour} {minutes}{minute}"
    return f"{max(1, minutes)}{minute}"


def clamp_int(value, default: int, low: int, high: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def as_text(value) -> str:
    if isinstance(value, str):
        return value
    return "" if value is None else str(value)


ZALGO_MAX_RUN = 4
EMOJI_MAX_ZWJ_LINKS = 6
EMOJI_MAX_RUN = 32
EMOJI_MAX_TAGS = 8
_ZALGO_MARKS = frozenset(("Mn", "Me"))
_unicode_category = unicodedata.category


def _zalgo_spans(text) -> List[Tuple[int, int]]:
    """Границы стопок комбинирующих знаков длиннее ZALGO_MAX_RUN: [(начало, конец), ...]."""
    if not isinstance(text, str) or len(text) <= ZALGO_MAX_RUN or max(text) < "\u0300":
        return []
    spans: List[Tuple[int, int]] = []
    first = None
    count = last = 0
    for index, char in enumerate(text):
        if char >= "\u0300":
            category = _unicode_category(char)
            if category in _ZALGO_MARKS:
                if first is None:
                    first, count = index, 0
                count += 1
                last = index + 1
                continue
            if category == "Cf" and first is not None:
                continue
        if first is not None:
            if count > ZALGO_MAX_RUN:
                spans.append((first, last))
            first = None
    if first is not None and count > ZALGO_MAX_RUN:
        spans.append((first, last))
    return spans


def has_zalgo(text) -> bool:
    return bool(_zalgo_spans(text))


def strip_zalgo(text):
    """Убирает комбинирующие знаки из каждой стопки длиннее лимита; остальной текст не меняется. Не строки возвращаются как есть."""
    spans = _zalgo_spans(text)
    if not spans:
        return text
    out: List[str] = []
    position = 0
    for start, end in spans:
        out.append(text[position:start])
        out.append("".join(ch for ch in text[start:end] if _unicode_category(ch) not in _ZALGO_MARKS))
        position = end
    out.append(text[position:])
    return "".join(out)


_EMOJI_SYMBOL = r"[\u00A9\u00AE\u203C\u2049\u2122\u2139\u2194-\u2199\u21A9-\u21AA\u231A-\u231B\u2328\u23CF\u23E9-\u23F3\u23F8-\u23FA\u24C2\u25AA-\u25AB\u25B6\u25C0\u25FB-\u25FE\u2600-\u2604\u260E\u2611\u2614-\u2615\u2618\u261D\u2620\u2622-\u2623\u2626\u262A\u262E-\u262F\u2638-\u263A\u2640\u2642\u2648-\u2653\u265F-\u2660\u2663\u2665-\u2666\u2668\u267B\u267E-\u267F\u2692-\u2697\u2699\u269B-\u269C\u26A0-\u26A1\u26A7\u26AA-\u26AB\u26B0-\u26B1\u26BD-\u26BE\u26C4-\u26C5\u26C8\u26CE-\u26CF\u26D1\u26D3-\u26D4\u26E9-\u26EA\u26F0-\u26F5\u26F7-\u26FA\u26FD\u2702\u2705\u2708-\u270D\u270F\u2712\u2714\u2716\u271D\u2721\u2728\u2733-\u2734\u2744\u2747\u274C\u274E\u2753-\u2755\u2757\u2763-\u2764\u2795-\u2797\u27A1\u27B0\u27BF\u2934-\u2935\u2B05-\u2B07\u2B1B-\u2B1C\u2B50\u2B55\u3030\u303D\u3297\u3299\U0001F000-\U0001F1E5\U0001F200-\U0001F3FA\U0001F400-\U0001FAFF]"
_EMOJI_ELEMENT = (
    r"(?:[\U0001F1E6-\U0001F1FF]{2}|[#*0-9]\uFE0F?\u20E3|" + _EMOJI_SYMBOL + r")"
    r"\uFE0F?[\U0001F3FB-\U0001F3FF]?"
    r"[\U000E0020-\U000E007E]*\U000E007F?"
)
_EMOJI_TOKEN = _EMOJI_ELEMENT + r"(?:\u200D" + _EMOJI_ELEMENT + r")*"
_EMOJI_CHAR_RE = re.compile(_EMOJI_SYMBOL)
_EMOJI_RUN_RE = re.compile(r"(?:" + _EMOJI_TOKEN + r")+")
_EMOJI_TOKEN_RE = re.compile(_EMOJI_TOKEN)


@lru_cache(maxsize=1)
def _emoji_only_regex():
    return re.compile(_EMOJI_TOKEN + r"(?:\s*" + _EMOJI_TOKEN + r")*")


@lru_cache(maxsize=1)
def _emoji_token_regex():
    return _EMOJI_TOKEN_RE


_BIDI_CLASS = r"\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069"
_CONTROL_CLASS = r"\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f\ud800-\udfff"
_INVISIBLE_CLASS = (
    r"\u00ad\u034f\u115f\u1160\u17b4\u17b5\u180b-\u180f\u200b\u2060-\u2064\u206a-\u206f\u2800\u3164\ufe00-\ufe0d\ufeff\uffa0"
    r"\ufff9-\ufffc\U0001d173-\U0001d17a\U000e0000-\U000e001f\U000e0080-\U000e01ef"
)
_BIDI_RE = re.compile("[" + _BIDI_CLASS + "]")
_CONTROL_RE = re.compile("[" + _CONTROL_CLASS + "]")
_INVISIBLE_RE = re.compile("[" + _INVISIBLE_CLASS + "]")
_ALWAYS_DROP_RE = re.compile("[" + _BIDI_CLASS + _CONTROL_CLASS + _INVISIBLE_CLASS + "]")
_LINE_BREAKS = {0x85: "\n", 0x2028: "\n", 0x2029: "\n"}
_CONDITIONAL_RE = re.compile(r"[\u200c\u200d\ufe0e\ufe0f\U000e0020-\U000e007f]")
_EMOJI_BASE_FOR_VS = frozenset("#*0123456789")
_VS_BASE_CATEGORIES = frozenset(("So", "Sm", "Sk"))
_BLACK_FLAG = "\U0001F3F4"


def _joiner_script(char: str) -> bool:
    """Буква или знак письменности, где ZWNJ/ZWJ значимы: арабское и сирийское, индийские, бирманское, кхмерское."""
    code = ord(char)
    return (0x0600 <= code <= 0x0DFF or 0x1000 <= code <= 0x109F or 0x1780 <= code <= 0x17FF) and _unicode_category(char)[0] in "LM"


def _emojiish(char: str) -> bool:
    return (
        char in ("\ufe0f", "\u20e3") or "\U0001F3FB" <= char <= "\U0001F3FF"
        or _EMOJI_CHAR_RE.fullmatch(char) is not None
    )


def _vs_allowed(previous: str) -> bool:
    return (
        previous in _EMOJI_BASE_FOR_VS or _EMOJI_CHAR_RE.fullmatch(previous) is not None
        or _unicode_category(previous) in _VS_BASE_CATEGORIES
    )


def _resolve_conditional(text: str) -> str:
    out: List[str] = []
    tags = 0
    length = len(text)
    for index, char in enumerate(text):
        code = ord(char)
        if code >= 0xE0020:
            previous = out[-1] if out else ""
            if code == 0xE007F:
                keep = bool(previous) and 0xE0020 <= ord(previous) <= 0xE007E
            else:
                keep = previous == _BLACK_FLAG or (bool(previous) and 0xE0020 <= ord(previous) <= 0xE007E and tags < EMOJI_MAX_TAGS)
            if keep:
                out.append(char)
                tags += 1
            continue
        tags = 0
        if code in (0x200C, 0x200D, 0xFE0E, 0xFE0F):
            previous = out[-1] if out else ""
            following = text[index + 1] if index + 1 < length else ""
            if code in (0xFE0E, 0xFE0F):
                keep = bool(previous) and _vs_allowed(previous)
            elif not previous or not following:
                keep = False
            elif code == 0x200D:
                keep = (_emojiish(previous) and _emojiish(following)) or (_joiner_script(previous) and _joiner_script(following))
            else:
                keep = _joiner_script(previous) and _joiner_script(following)
            if not keep:
                continue
        out.append(char)
    return "".join(out)


def _limit_emoji_run(match) -> str:
    run = match.group(0)
    tokens: List[str] = []
    for token in _EMOJI_TOKEN_RE.findall(run):
        links = token.split("\u200d")
        if len(links) > EMOJI_MAX_ZWJ_LINKS:
            tokens.append("\u200d".join(links[:EMOJI_MAX_ZWJ_LINKS]))
            tokens.extend(links[EMOJI_MAX_ZWJ_LINKS:])
        else:
            tokens.append(token)
    return "".join(tokens[:EMOJI_MAX_RUN])


def limit_emoji_chains(text):
    """Режет ZWJ-цепочки длиннее EMOJI_MAX_ZWJ_LINKS (хвост становится отдельными эмодзи) и серии длиннее EMOJI_MAX_RUN."""
    if not isinstance(text, str) or len(text) < 2:
        return text
    return _EMOJI_RUN_RE.sub(_limit_emoji_run, text)


def sanitize_text(text):
    """Приводит текст к безопасному виду: убирает bidi, невидимые и управляющие символы, Zalgo, аномальные цепочки эмодзи.
    Обычный текст возвращается тем же объектом. Не строки возвращаются как есть. Результат стабилен: повторный вызов ничего не меняет."""
    if not isinstance(text, str) or not text:
        return text
    cleaned = text
    for _ in range(6):
        step = cleaned
        if _ALWAYS_DROP_RE.search(step) or "\x85" in step or "\u2028" in step or "\u2029" in step:
            step = _ALWAYS_DROP_RE.sub("", step.translate(_LINE_BREAKS))
        if _CONDITIONAL_RE.search(step):
            step = _resolve_conditional(step)
        step = limit_emoji_chains(strip_zalgo(step))
        if step == cleaned:
            break
        cleaned = step
    return text if cleaned == text else cleaned


def has_unsafe_text(text) -> bool:
    return isinstance(text, str) and sanitize_text(text) != text


def unsafe_kinds(text) -> frozenset:
    """Что именно не так с текстом: подмножество {"bidi", "invisible", "control", "zalgo", "emoji_chain"}. Для журнала и тестов."""
    if not isinstance(text, str) or not text:
        return frozenset()
    kinds = set()
    if _BIDI_RE.search(text):
        kinds.add("bidi")
    if _CONTROL_RE.search(text) or "\x85" in text:
        kinds.add("control")
    if _INVISIBLE_RE.search(text) or "\u2028" in text or "\u2029" in text:
        kinds.add("invisible")
    base = _ALWAYS_DROP_RE.sub("", text.translate(_LINE_BREAKS))
    if _CONDITIONAL_RE.search(base) and _resolve_conditional(base) != base:
        kinds.add("invisible")
    if has_zalgo(text):
        kinds.add("zalgo")
    if limit_emoji_chains(text) != text:
        kinds.add("emoji_chain")
    return frozenset(kinds)


MASK_TOKEN_RE = re.compile(r"\[text(?:[ \t]*:[ \t]*([^\[\]\r\n]*?))?[ \t]*\]")
_LINK_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:(?://|[^\s/])")


_LINK_SCHEME_PREFIX_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+\-]*):")
_LINK_SAFE_SCHEMES = frozenset(("http", "https", "tg", "mailto", "ton"))
_LINK_BLOCKED_SCHEMES = frozenset(("javascript", "vbscript", "data", "file", "content", "intent", "blob", "about"))


def normalize_link(raw) -> Optional[str]:
    """49.2.0: ссылка из [text: …]. Разрешены http(s), tg, mailto и ton; javascript:, data:, file:, intent: и подобные
    отбрасываются (маска может прийти из чужого файла конфигурации). «site.com:8080/x» и «localhost:3000» раньше
    принимались за схему и уходили без https://, то есть нерабочей ссылкой."""
    link = as_text(raw).strip()
    if not link or any(ch.isspace() for ch in link) or len(link) > 2048:
        return None
    if has_unsafe_text(link):
        return None
    if link.startswith("@") and len(link) > 1:
        name = link[1:]
        return "https://t.me/" + name if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{3,31}", name) else None
    found = _LINK_SCHEME_PREFIX_RE.match(link)
    scheme = found.group(1).lower() if found else ""
    if scheme in _LINK_SAFE_SCHEMES:
        rest = link[found.end():]
        if scheme in ("http", "https") and not rest.startswith("//"):
            return None
        return link if rest else None
    if scheme in _LINK_BLOCKED_SCHEMES:
        return None
    if link.startswith("//"):
        link = link[2:]
    return "https://" + link


def mask_tokens(mask) -> list:
    return list(MASK_TOKEN_RE.finditer(mask)) if isinstance(mask, str) else []


def is_valid_mask(mask) -> bool:
    return isinstance(mask, str) and len(mask) <= MAX_MASK_LENGTH and len(mask_tokens(mask)) == 1


def mask_link(mask) -> Optional[str]:
    tokens = mask_tokens(mask)
    return normalize_link(tokens[0].group(1)) if len(tokens) == 1 else None


def split_mask(mask) -> Optional[Tuple[str, str]]:
    tokens = mask_tokens(mask)
    if len(tokens) == 1:
        return mask[:tokens[0].start()], mask[tokens[0].end():]
    return None


TEXT_STYLE_COUNT = 30
(STYLE_LEET, STYLE_ALTERNATING, STYLE_FULLWIDTH, STYLE_VAPORWAVE,
 STYLE_UPSIDE_DOWN, STYLE_SCRIPT, STYLE_BOLD, STYLE_SQUARED, STYLE_GOTHIC,
 STYLE_DOUBLE_STRUCK, STYLE_MONOSPACE, STYLE_ITALIC, STYLE_BOLD_FRAKTUR, STYLE_SMALL_CAPS,
 STYLE_STRIKETHROUGH, STYLE_UNDERLINE, STYLE_CIRCLED, STYLE_MIRRORED, STYLE_SMILEY,
 STYLE_BUBBLES, STYLE_SUPERSCRIPT, STYLE_SUBSCRIPT, STYLE_MORSE, STYLE_MIXED,
 STYLE_DOUBLE_UNDERLINE, STYLE_OVERLINE, STYLE_DOTTED, STYLE_WAVY, STYLE_SLASHED,
 STYLE_TRANSLIT) = range(TEXT_STYLE_COUNT)

STYLE_KEYS = (
    "leet", "alternating", "fullwidth", "vaporwave", "upside_down", "script", "bold", "squared", "gothic",
    "double_struck", "monospace", "italic", "bold_fraktur", "small_caps", "strikethrough", "underline",
    "circled", "mirrored", "smiley", "bubbles", "superscript", "subscript", "morse", "mixed",
    "double_underline", "overline", "dotted", "wavy", "slashed", "translit",
)
assert len(STYLE_KEYS) == TEXT_STYLE_COUNT

TEXT_STYLE_ITEMS = ("L33T", "aLtErNaTiNg", "Ｆｕｌｌｗｉｄｔｈ", "Ｖ ａ ｐ ｏ ｒ", "uʍop ǝpısdn", "𝓯𝓪𝓷𝓬𝔂", "𝐛𝐨𝐥𝐝", "🅲🅸🆁🅲🅻🅴🅳", "𝔊𝔬𝔱𝔥𝔦𝔠", "𝕕𝕠𝕦𝕓𝕝𝕖-𝕤𝕥𝕣𝕦𝕔𝕜", "𝙼𝚘𝚗𝚘𝚜𝚙𝚊𝚌𝚎", "𝘪𝘵𝘢𝘭𝘪𝘤", "𝖇𝖔𝖑𝖉 𝖋𝖗𝖆𝖐𝖙𝖚𝖗", "sᴍᴀʟʟ ᴄᴀᴘs", "s̶t̶r̶i̶k̶e̶", "u̲n̲d̲e̲r̲l̲i̲n̲e̲", "ⓒⓘⓡⓒⓛⓔⓓ", "ɿoɿɿiM", "☺Smile☺", "🅑🅤🅑🅑🅛🅔", "ˢᵘᵖᵉʳ", "ₐₛᵤₑₐ", "Morse -- --- .-. ... .", "mIxEd 𝓼𝓽𝔶𝓵𝓮", "d̳o̳u̳b̳l̳e̳", "o̅v̅e̅r̅", "ḍọṭṣ", "w̰a̰v̰y̰", "s̸l̸a̸s̸h̸", "Translit")

_LEET_DIGITS = (
    ("3", "EЕЁЄ"),
    ("1", "IИІЇ"),
    ("4", "AА"),
    ("0", "OО"),
)
_LEET_MAP = {letter: digit for digit, letters in _LEET_DIGITS for letter in letters}


def _char_pairs(pairs: str) -> Dict[str, str]:
    table = {}
    for pair in pairs.split():
        if len(pair) != 2:
            raise ValueError(f"bad character pair: {pair!r}")
        table[pair[0]] = pair[1]
    return table


_FLIP_TABLE = _char_pairs(
    "aɐ bq cɔ dp eǝ fɟ gƃ hɥ iᴉ jɾ kʞ ll mɯ nu oo pd qb rɹ ss tʇ un vʌ wʍ xx yʎ zz "
    "A∀ Bᗺ CƆ Dᗡ EƎ FℲ G⅁ HH II Jſ K⋊ L⅂ MW NN OO PԀ QΌ Rᴚ SS T⊥ U∩ VΛ WM XX Y⅄ ZZ "
    "00 1Ɩ 2ᄅ 3Ɛ 4ㄣ 5ϛ 69 7ㄥ 88 96 !¡ ?¿ &⅋ .˙ _‾"
)
_FLIP_TABLE.update({
    "(": ")", ")": "(", "[": "]", "]": "[", "{": "}", "}": "{", "<": ">", ">": "<",
    ",": "'", "'": ",", '"': "„",
})


_MIRROR_TABLE = _char_pairs(
    "bd db pq qp a\u0252 c\u0254 e\u0258 n\u1D0E r\u027F s\u01A8 z\u01B9 "
    "B\u15FA D\u15E1 E\u018E F\uA7FB J\u10B1 K\uA4D8 L\u2143 N\u0418 P\uA7FC Q\u03D8 R\u042F S\u01A7 Z\u01B8 C\u0186 3\u0190 "
    "зэ эз еɘ ЕƎ ЗЭ ЭЗ"
)
_MIRROR_TABLE.update({
    "(": ")", ")": "(", "[": "]", "]": "[", "{": "}", "}": "{", "<": ">", ">": "<",
    "/": "\\", "\\": "/", "«": "»", "»": "«", "?": "\u2E2E",
})


def _leet_char(char: str) -> str:
    upper = char.upper()
    return _LEET_MAP.get(upper, upper)


def _fullwidth_char(char: str) -> str:
    code = ord(char)
    if 0x21 <= code <= 0x7E:
        return chr(code + 0xFEE0)
    return "\u3000" if char == " " else char


def _math_alphabet(char: str, upper_start: int, lower_start: int, digit_start: Optional[int] = None) -> str:
    if "A" <= char <= "Z":
        return chr(upper_start + ord(char) - 65)
    if "a" <= char <= "z":
        return chr(lower_start + ord(char) - 97)
    if digit_start is not None and "0" <= char <= "9":
        return chr(digit_start + ord(char) - 48)
    return char


_GOTHIC_UPPER_EXCEPTIONS = {"C": "\u212D", "H": "\u210C", "I": "\u2111", "R": "\u211C", "Z": "\u2128"}


def _gothic_char(char: str) -> str:
    exception = _GOTHIC_UPPER_EXCEPTIONS.get(char)
    if exception is not None:
        return exception
    return _math_alphabet(char, 0x1D504, 0x1D51E)


_DOUBLE_STRUCK_EXCEPTIONS = {"C": "ℂ", "H": "ℍ", "N": "ℕ", "P": "ℙ", "Q": "ℚ", "R": "ℝ", "Z": "ℤ"}
_ITALIC_EXCEPTIONS = {"h": "ℎ"}
_SMALL_CAPS = dict(zip("abcdefghijklmnopqrstuvwxyz", "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"))


def _small_caps_char(char: str) -> str:
    return _SMALL_CAPS.get(char.lower(), char) if char.isascii() and char.isalpha() else char


def _combine_char(char: str, mark: str) -> str:
    if char.isalnum() or (char.isascii() and char.isprintable() and not char.isspace()):
        return char + mark
    return char


_TRANSLIT_BASE = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "zh", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh",
    "щ": "shch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "і": "i", "ї": "yi", "є": "ye", "ґ": "g",
}


def _translit_char(char: str) -> Optional[str]:
    latin = _TRANSLIT_BASE.get(char.lower())
    if latin is None:
        return None
    return latin.capitalize() if char != char.lower() else latin


_MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....",
    "I": "..", "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.",
    "Q": "--.-", "R": ".-.", "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....",
    "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "!": "-.-.--", "/": "-..-.", ":": "---...",
    "-": "-....-", "(": "-.--.", ")": "-.--.-", "'": ".----.", "\"": ".-..-.", "=": "-...-",
    "+": ".-.-.", "@": ".--.-.",
    "А": ".-", "Б": "-...", "В": ".--", "Г": "--.", "Д": "-..", "Е": ".", "Ё": ".", "Ж": "...-",
    "З": "--..", "И": "..", "Й": ".---", "К": "-.-", "Л": ".-..", "М": "--", "Н": "-.", "О": "---",
    "П": ".--.", "Р": ".-.", "С": "...", "Т": "-", "У": "..-", "Ф": "..-.", "Х": "....", "Ц": "-.-.",
    "Ч": "---.", "Ш": "----", "Щ": "--.-", "Ъ": "-..-", "Ы": "-.--", "Ь": "-..-", "Э": "..-..",
    "Ю": "..--", "Я": ".-.-", "І": "..", "Ї": ".---.", "Є": "..-..", "Ґ": "--.",
}

_COMBINING_MARKS = {
    STYLE_STRIKETHROUGH: "\u0336",
    STYLE_UNDERLINE: "\u0332",
    STYLE_DOUBLE_UNDERLINE: "\u0333",
    STYLE_OVERLINE: "\u0305",
    STYLE_DOTTED: "\u0323",
    STYLE_WAVY: "\u0330",
    STYLE_SLASHED: "\u0338",
}
_CYRILLIC_STYLES = frozenset({
    STYLE_LEET, STYLE_ALTERNATING, STYLE_MIRRORED, STYLE_SMILEY, STYLE_MORSE, STYLE_TRANSLIT, STYLE_MIXED,
    *_COMBINING_MARKS,
})
_MIXED_EXCLUDED = frozenset({
    STYLE_UPSIDE_DOWN, STYLE_MIRRORED, STYLE_MORSE, STYLE_MIXED, STYLE_SUBSCRIPT, STYLE_TRANSLIT, STYLE_SMILEY,
})
_RANDOM_EXCLUDED = frozenset({
    STYLE_UPSIDE_DOWN, STYLE_MIRRORED, STYLE_MORSE, STYLE_SUBSCRIPT, STYLE_TRANSLIT,
})


def _build_script_map(letters: str, marks: str, upper: str = "", upper_marks: str = "", digits: str = "0123456789", digit_marks: str = "", extra: str = "", extra_marks: str = "") -> Dict[str, str]:
    if len(letters) != len(marks) or len(upper) != len(upper_marks) or len(digits) != len(digit_marks) or len(extra) != len(extra_marks):
        raise ValueError("script table length mismatch")
    table = dict(zip(letters, marks))
    table.update(zip(upper, upper_marks))
    table.update(zip(digits, digit_marks))
    table.update(zip(extra, extra_marks))
    return table


_SUPERSCRIPT = _build_script_map(
    "abcdefghijklmnoprstuvwxyz", "\u1d43\u1d47\u1d9c\u1d48\u1d49\u1da0\u1d4d\u02b0\u2071\u02b2\u1d4f\u02e1\u1d50\u207f\u1d52\u1d56\u02b3\u02e2\u1d57\u1d58\u1d5b\u02b7\u02e3\u02b8\u1dbb",
    "ABDEGHIJKLMNOPRTUVW", "\u1d2c\u1d2e\u1d30\u1d31\u1d33\u1d34\u1d35\u1d36\u1d37\u1d38\u1d39\u1d3a\u1d3c\u1d3e\u1d3f\u1d40\u1d41\u2c7d\u1d42",
    "0123456789", "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079",
    "+-=()", "\u207a\u207b\u207c\u207d\u207e",
)
for _upper in "CFSXYZ":
    _SUPERSCRIPT[_upper] = _SUPERSCRIPT[_upper.lower()]
_SUBSCRIPT = _build_script_map(
    "aehijklmnoprstuvx", "\u2090\u2091\u2095\u1d62\u2c7c\u2096\u2097\u2098\u2099\u2092\u209a\u1d63\u209b\u209c\u1d64\u1d65\u2093",
    "", "",
    "0123456789", "\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089",
    "+-=()", "\u208a\u208b\u208c\u208d\u208e",
)
for _upper in "AEHIJKLMNOPRSTUVX":
    _SUBSCRIPT[_upper] = _SUBSCRIPT[_upper.lower()]


def _bubble_char(char: str) -> str:
    if char.isascii() and char.isalpha():
        return chr(0x1F150 + ord(char.upper()) - 65)
    if "1" <= char <= "9":
        return chr(0x2776 + ord(char) - 49)
    if char == "0":
        return "\u24FF"
    return char


def _stateless_style(char: str, style: int) -> str:
    if style == STYLE_FULLWIDTH:
        return _fullwidth_char(char)
    if style == STYLE_UPSIDE_DOWN:
        return _FLIP_TABLE.get(char, char)
    if style == STYLE_SCRIPT:
        return _math_alphabet(char, 0x1D4D0, 0x1D4EA)
    if style == STYLE_BOLD:
        return _math_alphabet(char, 0x1D400, 0x1D41A, 0x1D7CE)
    if style == STYLE_SQUARED:
        return chr(0x1F170 + ord(char.upper()) - 65) if char.isascii() and char.isalpha() else char
    if style == STYLE_GOTHIC:
        return _gothic_char(char)
    if style == STYLE_DOUBLE_STRUCK:
        return _DOUBLE_STRUCK_EXCEPTIONS.get(char, _math_alphabet(char, 0x1D538, 0x1D552, 0x1D7D8))
    if style == STYLE_MONOSPACE:
        return _math_alphabet(char, 0x1D670, 0x1D68A, 0x1D7F6)
    if style == STYLE_ITALIC:
        return _ITALIC_EXCEPTIONS.get(char) or _math_alphabet(char, 0x1D434, 0x1D44E)
    if style == STYLE_BOLD_FRAKTUR:
        return _math_alphabet(char, 0x1D56C, 0x1D586)
    if style == STYLE_SMALL_CAPS:
        return _small_caps_char(char)
    if style == STYLE_CIRCLED:
        if "A" <= char <= "Z":
            return chr(0x24B6 + ord(char) - 65)
        if "a" <= char <= "z":
            return chr(0x24D0 + ord(char) - 97)
        if "1" <= char <= "9":
            return chr(0x2460 + ord(char) - 49)
        if char == "0":
            return "\u24EA"
        return char
    if style == STYLE_BUBBLES:
        return _bubble_char(char)
    if style == STYLE_SUPERSCRIPT:
        return _SUPERSCRIPT.get(char, char)
    if style == STYLE_SUBSCRIPT:
        return _SUBSCRIPT.get(char, char)
    return char


def _style_atoms_full(text: str, style: int, translit: bool = False) -> List[Tuple[str, str]]:
    if style == STYLE_MIXED:
        return _mixed_atoms(text, translit)
    protected = {match.start(): match.end() for match in _PLACEHOLDER_RE.finditer(text)}
    emoji_starts = set()
    if not text.isascii():
        for match in _EMOJI_TOKEN_RE.finditer(text):
            if match.end() - match.start() > 1 and match.start() not in protected:
                protected[match.start()] = match.end()
                emoji_starts.add(match.start())
    atoms: List[Tuple[str, str]] = []
    upper = False
    convert = style == STYLE_TRANSLIT or (translit and style not in _CYRILLIC_STYLES)
    index, size = 0, len(text)
    while index < size:
        end = protected.get(index)
        if end is not None:
            chunk = text[index:end]
            out = chunk
            if style == STYLE_VAPORWAVE and index in emoji_starts and text[end:end + 1] and not text[end:end + 1].isspace():
                out += " "
            atoms.append((chunk, out))
            index = end
            continue
        char = text[index]
        out = char
        latin = _translit_char(char) if convert else None
        if latin is not None:
            if style == STYLE_TRANSLIT:
                out = latin
            elif style == STYLE_VAPORWAVE:
                out = "".join(_fullwidth_char(c) for c in latin)
                following = text[index + 1:index + 2]
                if latin and following and not following.isspace():
                    out += " "
            else:
                out = "".join(_stateless_style(c, style) for c in latin)
        elif style == STYLE_LEET:
            out = _leet_char(char)
        elif style == STYLE_ALTERNATING:
            if char.isalpha():
                out = char.upper() if upper else char.lower()
                upper = not upper
        elif style == STYLE_VAPORWAVE:
            out = _fullwidth_char(char)
            following = text[index + 1:index + 2]
            if not char.isspace() and following and not following.isspace():
                out += " "
        elif style in _COMBINING_MARKS:
            out = _combine_char(char, _COMBINING_MARKS[style])
        elif style == STYLE_MORSE:
            code = _MORSE.get(char.upper())
            if code is not None:
                following = text[index + 1:index + 2]
                out = code + (" " if following and following.upper() in _MORSE else "")
            elif char == " ":
                out = " / "
        elif style == STYLE_MIRRORED:
            out = _MIRROR_TABLE.get(char, char)
        elif style == STYLE_SMILEY:
            if not char.isspace():
                before = text[index - 1:index] if index else ""
                after = text[index + 1:index + 2]
                opens = not before or before.isspace() or before == "\uE001"
                closes = not after or after.isspace() or after == "\uE000"
                out = ("\u263A" if opens else "") + char + ("\u263A" if closes else "")
        else:
            out = _stateless_style(char, style)
        atoms.append((char, out))
        index += 1
    return atoms


def _mixed_atoms(text: str, translit: bool) -> List[Tuple[str, str]]:
    pool = [s for s in available_styles() if s not in _MIXED_EXCLUDED] or [STYLE_BOLD]
    atoms: List[Tuple[str, str]] = []
    word_index = 0
    for part in re.split(r"(\s+)", text):
        if not part:
            continue
        if part.isspace():
            atoms.extend((c, c) for c in part)
            continue
        pick = pool[(word_index + zlib.crc32(part.casefold().encode("utf-8"))) % len(pool)]
        word_index += 1
        atoms.extend(_style_atoms_full(part, pick, translit))
    return atoms


_STYLE_WORD_RE = re.compile("(\uE000\\d+\uE001|\\w+)")


def _style_atoms(text: str, style: int, translit: bool = False, only=None) -> List[Tuple[str, str]]:
    if not only:
        return _style_atoms_full(text, style, translit)
    atoms: List[Tuple[str, str]] = []
    for part in _STYLE_WORD_RE.split(text):
        if not part:
            continue
        if _PLACEHOLDER_RE.fullmatch(part):
            atoms.append((part, part))
        elif part.casefold() in only:
            atoms.extend(_style_atoms_full(part, style, translit))
        else:
            atoms.extend((c, c) for c in part)
    return atoms


def _output_order(atoms: List[Tuple[str, str]], style: int) -> List[int]:
    count = len(atoms)
    if style == STYLE_UPSIDE_DOWN:
        return list(range(count - 1, -1, -1))
    if style != STYLE_MIRRORED:
        return list(range(count))
    order: List[int] = []
    line: List[int] = []
    for index, (source, _) in enumerate(atoms):
        if source == "\n":
            order.extend(reversed(line))
            order.append(index)
            line = []
        else:
            line.append(index)
    order.extend(reversed(line))
    return order


def apply_text_style(text: str, style: int, translit: bool = False, only=None) -> str:
    if not text or not 0 <= style < TEXT_STYLE_COUNT:
        return text
    atoms = _style_atoms(text, style, translit, only)
    return "".join(atoms[index][1] for index in _output_order(atoms, style))


class StyleLayout:
    __slots__ = ("body", "_starts", "_ends", "_new_starts", "_new_ends", "_reordered")

    def __init__(self, atoms: List[Tuple[str, str]], order: List[int]):
        self._reordered = order != sorted(order)
        self._starts, self._ends = [], []
        position = 0
        for source, _ in atoms:
            self._starts.append(position)
            position += utf16_length(source)
            self._ends.append(position)
        self._new_starts = [0] * len(atoms)
        self._new_ends = [0] * len(atoms)
        position = 0
        for index in order:
            self._new_starts[index] = position
            position += utf16_length(atoms[index][1])
            self._new_ends[index] = position
        self.body = "".join(atoms[index][1] for index in order)

    def map_range(self, offset: int, length: int) -> Tuple[int, int]:
        count = len(self._starts)
        if count == 0:
            return offset, length
        first = min(bisect_right(self._ends, offset), count - 1)
        last = first if length <= 0 else max(first, min(bisect_left(self._starts, offset + length) - 1, count - 1))
        if self._reordered:
            touched = range(first, last + 1)
            begin = min(self._new_starts[i] for i in touched)
            finish = max(self._new_ends[i] for i in touched)
        else:
            begin, finish = self._new_starts[first], self._new_ends[last]
        if length <= 0:
            return begin, 0
        return begin, max(0, finish - begin)


_BOT_API_CHANNEL_SHIFT = 10 ** 12


def normalize_dialog_id(number: int) -> int:
    """52.1.0: id канала или супергруппы в формате Bot API (-100XXXXXXXXXX, его показывают боты вроде @userinfobot)
    -> dialog_id клиента (-XXXXXXXXXX). Раньше такой id в списке исключений просто ни с чем не совпадал."""
    if -2 * _BOT_API_CHANNEL_SHIFT < number <= -_BOT_API_CHANNEL_SHIFT:
        return -(-number - _BOT_API_CHANNEL_SHIFT)
    return number


def parse_chat_ids(raw) -> frozenset:
    result = set()
    for token in re.split(r"[\s,;]+", as_text(raw)):
        if not re.fullmatch(r"-?[0-9]{1,19}", token):
            continue
        number = int(token)
        if abs(number) < 2 ** 63 and number != 0:
            result.add(normalize_dialog_id(number))
    return frozenset(result)


def parse_chat_type_rules(raw) -> frozenset:
    parts = {part.strip().lower() for part in as_text(raw).split(",")}
    kinds = frozenset(part for part in parts if part in CHAT_KINDS)
    return frozenset(CHAT_KINDS) if not kinds or "all" in parts else kinds


def dump_chat_type_rules(kinds) -> str:
    wanted = set(kinds)
    chosen = [kind for kind in CHAT_KINDS if kind in wanted]
    return "all" if len(chosen) in (0, len(CHAT_KINDS)) else ",".join(chosen)


def _regex_seq(node):
    return getattr(node, "data", node)


def _regex_is_repeat(op) -> bool:
    return op in (_re_constants.MAX_REPEAT, _re_constants.MIN_REPEAT)


def _regex_has_unbounded(items) -> bool:
    for op, av in _regex_seq(items):
        if _regex_is_repeat(op):
            if av[1] == _re_constants.MAXREPEAT or _regex_has_unbounded(av[2]):
                return True
        elif op == _re_constants.SUBPATTERN:
            if _regex_has_unbounded(av[-1]):
                return True
        elif op == _re_constants.BRANCH:
            if any(_regex_has_unbounded(branch) for branch in av[1]):
                return True
    return False


def _regex_count_unbounded(items) -> int:
    total = 0
    for op, av in _regex_seq(items):
        if _regex_is_repeat(op):
            total += (av[1] == _re_constants.MAXREPEAT) + _regex_count_unbounded(av[2])
        elif op == _re_constants.SUBPATTERN:
            total += _regex_count_unbounded(av[-1])
        elif op == _re_constants.BRANCH:
            total += sum(_regex_count_unbounded(branch) for branch in av[1])
    return total


def _regex_is_flexible(op, av) -> bool:
    """Повтор с переменной длиной совпадения: a*, a+, a?, a{1,40}. Фиксированное a{3} гибким не считается."""
    return _regex_is_repeat(op) and (av[1] == _re_constants.MAXREPEAT or av[1] > av[0])


def _regex_has_flex(items) -> bool:
    for op, av in _regex_seq(items):
        if _regex_is_repeat(op):
            if _regex_is_flexible(op, av) or _regex_has_flex(av[2]):
                return True
        elif op == _re_constants.SUBPATTERN:
            if _regex_has_flex(av[-1]):
                return True
        elif op == _re_constants.BRANCH:
            if any(_regex_has_flex(branch) for branch in av[1]):
                return True
    return False


def _regex_ambiguous_body(items) -> bool:
    carriers, delimiter = 0, False
    for op, av in _regex_seq(items):
        if op in (_re_constants.AT, _re_constants.ASSERT, _re_constants.ASSERT_NOT):
            continue
        if _regex_is_repeat(op):
            if _regex_is_flexible(op, av) or _regex_has_flex(av[2]):
                carriers += 1
            elif av[0] > 0:
                delimiter = True
        elif op == _re_constants.SUBPATTERN:
            if _regex_has_flex(av[-1]):
                carriers += 1
            else:
                delimiter = True
        elif op == _re_constants.BRANCH:
            if any(_regex_has_flex(branch) for branch in av[1]):
                carriers += 1
            else:
                delimiter = True
        else:
            delimiter = True
    return carriers > 1 or (carriers == 1 and not delimiter)


def _regex_nested_repeat(items) -> bool:
    for op, av in _regex_seq(items):
        if _regex_is_repeat(op):
            if (av[1] == _re_constants.MAXREPEAT or av[1] > 8) and _regex_ambiguous_body(av[2]):
                return True
            if _regex_nested_repeat(av[2]):
                return True
        elif op == _re_constants.SUBPATTERN:
            if _regex_nested_repeat(av[-1]):
                return True
        elif op == _re_constants.BRANCH:
            if any(_regex_nested_repeat(branch) for branch in av[1]):
                return True
        elif op in (_re_constants.ASSERT, _re_constants.ASSERT_NOT):
            if _regex_nested_repeat(av[1]):
                return True
    return False


def _regex_first_chars(items):
    seq = list(_regex_seq(items))
    if not seq:
        return None
    op, av = seq[0]
    if op == _re_constants.LITERAL:
        return {av}
    if op == _re_constants.SUBPATTERN:
        return _regex_first_chars(av[-1])
    return None


def _regex_branch_overlap(items) -> bool:
    for op, av in _regex_seq(items):
        if op == _re_constants.BRANCH:
            firsts = [_regex_first_chars(branch) for branch in av[1]]
            if any(first is None for first in firsts):
                return True
            seen = set()
            for first in firsts:
                if seen & first:
                    return True
                seen |= first
            if any(_regex_branch_overlap(branch) for branch in av[1]):
                return True
        elif _regex_is_repeat(op):
            if _regex_branch_overlap(av[2]):
                return True
        elif op == _re_constants.SUBPATTERN:
            if _regex_branch_overlap(av[-1]):
                return True
    return False


def _regex_repeated_ambiguity(items) -> bool:
    for op, av in _regex_seq(items):
        if _regex_is_repeat(op):
            heavy = av[1] == _re_constants.MAXREPEAT or av[1] > 8
            if heavy and (_regex_branch_overlap(av[2]) or (av[1] != _re_constants.MAXREPEAT and _regex_has_unbounded(av[2]))):
                return True
            if _regex_repeated_ambiguity(av[2]):
                return True
        elif op == _re_constants.SUBPATTERN:
            if _regex_repeated_ambiguity(av[-1]):
                return True
        elif op == _re_constants.BRANCH:
            if any(_regex_repeated_ambiguity(branch) for branch in av[1]):
                return True
        elif op in (_re_constants.ASSERT, _re_constants.ASSERT_NOT):
            if _regex_repeated_ambiguity(av[1]):
                return True
    return False


def _regex_has_backref(items) -> bool:
    backrefs = tuple(
        getattr(_re_constants, name) for name in ("GROUPREF", "GROUPREF_EXISTS", "GROUPREF_IGNORE")
        if hasattr(_re_constants, name)
    )
    for op, av in _regex_seq(items):
        if op in backrefs:
            return True
        if _regex_is_repeat(op) and _regex_has_backref(av[2]):
            return True
        if op == _re_constants.SUBPATTERN and _regex_has_backref(av[-1]):
            return True
        if op == _re_constants.BRANCH and any(_regex_has_backref(branch) for branch in av[1]):
            return True
        if op in (_re_constants.ASSERT, _re_constants.ASSERT_NOT) and _regex_has_backref(av[1]):
            return True
    return False


_REGEX_PROBE = tuple(chr(code) for code in range(256)) + tuple("\u044f\u044d\u0451\u6f22\u7ae0\u3000\u200d\U0001F600")
_REGEX_WIDE = 64


def _regex_category_matches(category, ch: str) -> bool:
    name = str(getattr(category, "name", category))
    negate = "NOT_" in name
    if "DIGIT" in name:
        hit = ch.isdecimal()
    elif "SPACE" in name:
        hit = ch.isspace()
    elif "WORD" in name:
        hit = ch.isalnum() or ch == "_"
    elif "LINEBREAK" in name:
        hit = ch == "\n"
    else:
        return True
    return hit != negate


def _regex_literal_matches(code: int, ch: str, ignore_case: bool) -> bool:
    if ord(ch) == code:
        return True
    if ignore_case:
        other = chr(code)
        return ch.lower() == other.lower() or ch.upper() == other.upper()
    return False


def _regex_item_matches(item, ch: str, ignore_case: bool) -> bool:
    op, av = item
    if op == _re_constants.LITERAL:
        return _regex_literal_matches(av, ch, ignore_case)
    if op == _re_constants.NOT_LITERAL:
        return not _regex_literal_matches(av, ch, ignore_case)
    if op == _re_constants.ANY:
        return True
    if op == _re_constants.IN:
        negate = False
        hit = False
        for kind, value in av:
            if kind == _re_constants.NEGATE:
                negate = True
            elif kind == _re_constants.LITERAL:
                hit = hit or _regex_literal_matches(value, ch, ignore_case)
            elif kind == _re_constants.RANGE:
                variants = {ch, ch.lower(), ch.upper()} if ignore_case else {ch}
                hit = hit or any(value[0] <= ord(variant) <= value[1] for variant in variants if len(variant) == 1)
            elif kind == _re_constants.CATEGORY:
                hit = hit or _regex_category_matches(value, ch)
            else:
                return True
        return hit != negate
    return True


def _regex_simple_item(items):
    seq = list(_regex_seq(items))
    if len(seq) != 1:
        return None
    item = seq[0]
    return item if item[0] in (_re_constants.LITERAL, _re_constants.NOT_LITERAL, _re_constants.ANY, _re_constants.IN) else None


def _regex_bodies_overlap(first, second, ignore_case: bool) -> bool:
    if first is None or second is None:
        return True
    return any(
        _regex_item_matches(first, ch, ignore_case) and _regex_item_matches(second, ch, ignore_case)
        for ch in _REGEX_PROBE
    )


def _regex_wide_repeat(op, av) -> bool:
    return _regex_is_repeat(op) and (av[1] == _re_constants.MAXREPEAT or av[1] > _REGEX_WIDE)


def _regex_adjacent_overlap(items, ignore_case: bool) -> bool:
    """Соседние неограниченные повторы, способные съесть одни и те же символы (a*a*b, .*-.*=),
    дают полиномиальный перебор: сообщение в 4096 знаков подвесит отправку."""
    chain: List[Any] = []
    for op, av in _regex_seq(items):
        if op in (_re_constants.AT, _re_constants.ASSERT, _re_constants.ASSERT_NOT):
            if op != _re_constants.AT and _regex_adjacent_overlap(av[1], ignore_case):
                return True
            continue
        if _regex_wide_repeat(op, av):
            if _regex_adjacent_overlap(av[2], ignore_case):
                return True
            body = _regex_simple_item(av[2])
            if any(_regex_bodies_overlap(earlier, body, ignore_case) for earlier in chain):
                return True
            chain = [body] if av[0] > 0 else chain + [body]
            continue
        if op == _re_constants.SUBPATTERN:
            inner = av[-1]
            seq = list(_regex_seq(inner))
            if len(seq) == 1 and _regex_wide_repeat(seq[0][0], seq[0][1]):
                if _regex_adjacent_overlap(inner, ignore_case):
                    return True
                node_op, node_av = seq[0]
                body = _regex_simple_item(node_av[2])
                if any(_regex_bodies_overlap(earlier, body, ignore_case) for earlier in chain):
                    return True
                chain = [body] if node_av[0] > 0 else chain + [body]
                continue
            if _regex_adjacent_overlap(inner, ignore_case):
                return True
            if _regex_has_unbounded(inner):
                if chain:
                    return True
                chain = [None]
            continue
        if op == _re_constants.BRANCH:
            if any(_regex_adjacent_overlap(branch, ignore_case) for branch in av[1]):
                return True
            if any(_regex_has_unbounded(branch) for branch in av[1]):
                if chain:
                    return True
                chain = [None]
            continue
        if _regex_is_repeat(op):
            if _regex_adjacent_overlap(av[2], ignore_case):
                return True
            if av[1] > 1 and _regex_has_unbounded(av[2]):
                return True
            if av[0] > 0 and _regex_simple_item(av[2]) is not None:
                body = _regex_simple_item(av[2])
                chain = [earlier for earlier in chain if _regex_bodies_overlap(earlier, body, ignore_case)]
            continue
        if op in (_re_constants.LITERAL, _re_constants.NOT_LITERAL, _re_constants.ANY, _re_constants.IN):
            chain = [earlier for earlier in chain if _regex_bodies_overlap(earlier, (op, av), ignore_case)]
    return False


def _regex_flex_carriers(items, out: list) -> bool:
    """Собирает тела гибких повторов внутри items. False - внутри есть гибкий повтор не из одного простого элемента
    (группа, ветвление) или вложенный повтор: такой случай безопасным не признаётся."""
    for op, av in _regex_seq(items):
        if _regex_is_repeat(op):
            body = _regex_simple_item(av[2])
            if _regex_is_flexible(op, av):
                if body is None:
                    return False
                out.append(body)
            elif _regex_has_flex(av[2]):
                return False
        elif op == _re_constants.SUBPATTERN:
            if _regex_has_flex(av[-1]) and not _regex_flex_carriers(av[-1], out):
                return False
        elif op == _re_constants.BRANCH:
            if any(_regex_has_flex(branch) for branch in av[1]):
                return False
        elif op in (_re_constants.ASSERT, _re_constants.ASSERT_NOT):
            if _regex_has_flex(av[1]):
                return False
    return True


def _regex_flex_delimiters(items, out: list):
    for op, av in _regex_seq(items):
        if op in (_re_constants.LITERAL, _re_constants.NOT_LITERAL, _re_constants.ANY, _re_constants.IN):
            out.append((op, av))
        elif _regex_is_repeat(op) and not _regex_is_flexible(op, av) and av[0] > 0:
            body = _regex_simple_item(av[2])
            if body is not None:
                out.append(body)
        elif op == _re_constants.SUBPATTERN and not _regex_has_flex(av[-1]):
            _regex_flex_delimiters(av[-1], out)


def _regex_star_height_unsafe(items, ignore_case: bool) -> bool:
    """52.0.0: повтор (max > 1), внутри которого есть ещё один гибкий повтор, допускается только в виде
    «носитель + разделитель», где разделитель не может совпасть с символами носителя: (\\d+,)* - можно,
    (?:.{0,40}a){0,40} - нельзя (точка съедает «a», перебор растёт экспоненциально и подвешивает отправку)."""
    for op, av in _regex_seq(items):
        if _regex_is_repeat(op):
            if av[1] > 1 and _regex_has_flex(av[2]):
                carriers: list = []
                if not _regex_flex_carriers(av[2], carriers):
                    return True
                delimiters: list = []
                _regex_flex_delimiters(av[2], delimiters)
                if not any(
                    not any(_regex_bodies_overlap(carrier, delimiter, ignore_case) for carrier in carriers)
                    for delimiter in delimiters
                ):
                    return True
            if _regex_star_height_unsafe(av[2], ignore_case):
                return True
        elif op == _re_constants.SUBPATTERN:
            if _regex_star_height_unsafe(av[-1], ignore_case):
                return True
        elif op == _re_constants.BRANCH:
            if any(_regex_star_height_unsafe(branch, ignore_case) for branch in av[1]):
                return True
        elif op in (_re_constants.ASSERT, _re_constants.ASSERT_NOT):
            if _regex_star_height_unsafe(av[1], ignore_case):
                return True
    return False


@lru_cache(maxsize=256)
def regex_is_safe(pattern: str) -> bool:
    if _re_parser is None:
        return False
    try:
        tree = _re_parser.parse(pattern)
        ignore_case = bool(getattr(getattr(tree, "state", None), "flags", 0) & re.IGNORECASE)
        return (
            _regex_count_unbounded(tree) <= MAX_REGEX_REPEATS
            and not _regex_star_height_unsafe(tree, ignore_case)
            and not _regex_nested_repeat(tree)
            and not _regex_repeated_ambiguity(tree)
            and not _regex_has_backref(tree)
            and not _regex_adjacent_overlap(tree, bool(getattr(getattr(tree, "state", None), "flags", 0) & re.IGNORECASE))
        )
    except Exception:
        return False


def clean_regex_exceptions(raw) -> str:
    """52.1.0: для импорта: только правильные и безопасные шаблоны (до MAX_REGEX_EXCEPTIONS). Раньше из чужого файла
    сохранялось всё, а негодные строки молча не работали и не давали сохранить редактор."""
    kept = []
    for line in parse_lines(raw):
        if len(kept) >= MAX_REGEX_EXCEPTIONS:
            break
        if len(line) > MAX_REGEX_LENGTH or has_unsafe_text(line) or not regex_is_safe(line):
            continue
        try:
            re.compile(line)
        except re.error:
            continue
        kept.append(line)
    return "\n".join(kept)


def compile_regex_exceptions(raw) -> tuple:
    compiled = []
    for line in parse_lines(raw)[:MAX_REGEX_EXCEPTIONS]:
        if len(line) > MAX_REGEX_LENGTH or not regex_is_safe(line):
            continue
        try:
            compiled.append(re.compile(line))
        except re.error:
            continue
    return tuple(compiled)


def parse_conditional_masks(raw):
    rules, errors = [], []
    for number, line in enumerate(as_text(raw).splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        pattern, separator, mask = line.partition("=>")
        pattern, mask = pattern.strip(), mask.strip()
        if not separator or not pattern or len(pattern) > MAX_REGEX_LENGTH:
            errors.append((number, "format"))
        elif not is_valid_mask(mask):
            errors.append((number, "mask"))
        else:
            try:
                compiled = re.compile(pattern)
            except re.error as exc:
                errors.append((number, "regex:" + str(exc)))
                continue
            if regex_is_safe(pattern):
                rules.append((compiled, mask))
            else:
                errors.append((number, "regex:" + REGEX_UNSAFE_REASON))
    if len(rules) > MAX_CONDITIONAL_MASKS:
        errors.append((0, "limit"))
    return tuple(rules[:MAX_CONDITIONAL_MASKS]), errors


def sanitize_tag_value(value) -> str:
    cleaned = sanitize_text(as_text(value))
    return _TAG_UNSAFE_RE.sub(" ", cleaned).strip()[:TAG_VALUE_LIMIT]


CHAT_CONFIGS_KEY = "Prefixfy_chat_configs"
SCHEDULE_KEY = "Prefixfy_schedule"
ACCT_MODE_KEY = "Prefixfy_acct_mode"
ACCT_TARGET_KEY = "Prefixfy_acct_target"
ACCT_LIVE_KEY = "Prefixfy_acct_live"
ACCT_PINS_KEY = "Prefixfy_acct_shared_pins"
ACCT_SELECTOR_KEY = "Prefixfy_acct_selector"
ACCT_AUTO = "auto"
ACCT_COMMON = "common"
ACCT_ALL = "all"
ACCT_DIR_NAME = "Prefixfy_accounts"
_ACCT_FILE_RE = re.compile(r"([0-9]{1,16})\.json")
_ACCT_DIR_RE = re.compile(r"[0-9]{1,16}")
_PRESET_ID_RE = re.compile(r"acc([0-9]{1,16})_[0-9a-f]{8}")
MAX_SCHEDULE_RULES = 48
MAX_SCHEDULE_EXPR_LENGTH = 240
MAX_SCHEDULE_EXPR_NODES = 40
MAX_SCHEDULE_EXPR_DEPTH = 8
MAX_SCHEDULE_TEXT_LENGTH = 8000
MAX_SCHEDULE_LINES = 200
MAX_SCHEDULE_NAME_LENGTH = 100
MAX_IMPORTED_CHAT_BINDINGS = 2000
_SCHEDULE_DAYS = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
    "пн": 0, "вт": 1, "ср": 2, "чт": 3, "пт": 4, "сб": 5, "вс": 6, "нд": 6,
    "1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6,
}
_SCHEDULE_DATE = r"([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{4}|[0-9]{1,2}\.[0-9]{1,2})"
_SCHEDULE_KIND_ALIASES = {
    "private": ("private", "pm", "dm", "личные", "личный", "лс", "privé", "privés", "個人", "개인"),
    "group": ("group", "groups", "группа", "группы", "groupe", "groupes", "グループ", "그룹"),
    "channel": ("channel", "channels", "канал", "каналы", "canal", "canaux", "チャンネル", "채널"),
}
_SCHEDULE_KIND_BY_ALIAS = {alias: kind for kind, names in _SCHEDULE_KIND_ALIASES.items() for alias in names}
_SCHEDULE_DAYSETS = {
    "weekend": frozenset((5, 6)), "weekends": frozenset((5, 6)), "выходные": frozenset((5, 6)),
    "weekdays": frozenset(range(5)), "workdays": frozenset(range(5)), "будни": frozenset(range(5)),
}
_SCHEDULE_AND = ("and", "и", "et")
_SCHEDULE_OR = ("or", "или", "ou")
_SCHEDULE_NOT = ("not", "не", "non")
_SCHEDULE_ELSE = ("else", "иначе", "sinon", "otherwise")
_SCHEDULE_CHAT = ("chat", "чат")
_SCHEDULE_ACCOUNT = ("account", "аккаунт", "compte")
_SCHEDULE_RANDOM = ("random", "rand", "случайно", "aléatoire")


def _schedule_alt(words) -> str:
    return "|".join(re.escape(word) for word in sorted(words, key=len, reverse=True))


_SD_DAY = r"(?:" + _schedule_alt(_SCHEDULE_DAYS) + r")"
_SD_DAYTOK = _SD_DAY + r"(?:\s*[-–—]\s*" + _SD_DAY + r")?"
_SCHEDULE_TOKEN_RE = re.compile(
    r"\s*(?:"
    r"(?P<date>" + _SCHEDULE_DATE + r"(?:\s*\.\.\s*" + _SCHEDULE_DATE + r")?)(?![\w.])"
    r"|(?P<time>[0-9]{1,2}:[0-9]{2}\s*[-–—]\s*[0-9]{1,2}:[0-9]{2})(?![0-9])"
    r"|(?P<part>(?:" + _DAYPART_PATTERN + r")(?:\s*[-–—]\s*(?:" + _DAYPART_PATTERN + r"))?)(?![^\W\d_])"
    r"|(?P<random>(?:" + _schedule_alt(_SCHEDULE_RANDOM) + r")\s+(?P<pct>[0-9]{1,3})\s*%?)(?!\w)"
    r"|(?P<chat>(?:" + _schedule_alt(_SCHEDULE_CHAT) + r")\s+(?P<chat_id>-?[0-9]{1,19}))(?!\w)"
    r"|(?P<account>(?:" + _schedule_alt(_SCHEDULE_ACCOUNT) + r")\s+(?P<uid>[0-9]{1,16}))(?!\w)"
    r"|(?P<days>" + _SD_DAYTOK + r"(?:\s*,\s*" + _SD_DAYTOK + r"|\s+" + _SD_DAYTOK + r")*)(?!\w)"
    r"|(?P<word>[^\W\d_]+)(?!\w)"
    r"|(?P<op>&&|\|\||[()!&|])"
    r")",
    re.IGNORECASE,
)


class ScheduleRule(NamedTuple):
    expr: tuple
    name: str
    line: int
    tier: int
    needs_chat: bool
    wrapped: tuple


class _ScheduleSyntaxError(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.code = code
        self.detail = detail


def _schedule_days_set(text: str) -> Optional[frozenset]:
    text = re.sub(r"\s*([-–—])\s*", "-", text.strip().lower())
    days = set()
    for token in (t for t in re.split(r"[,\s]+", text) if t):
        ends = re.split(r"[-–—]", token)
        if len(ends) > 2 or any(end not in _SCHEDULE_DAYS for end in ends):
            return None
        a = _SCHEDULE_DAYS[ends[0]]
        b = _SCHEDULE_DAYS[ends[-1]]
        while True:
            days.add(a)
            if a == b:
                break
            a = (a + 1) % 7
    return frozenset(days) if days else None


def _schedule_tokens(text: str):
    position, tokens = 0, []
    text = text.strip()
    while position < len(text):
        match = _SCHEDULE_TOKEN_RE.match(text, position)
        if match is None or match.end() == position:
            raise _ScheduleSyntaxError("schedule_err_unknown", text[position:position + 16].strip())
        position = match.end()
        for kind in ("date", "time", "part", "random", "chat", "account", "days", "word", "op"):
            if match.group(kind) is not None:
                tokens.append((kind, match))
                break
        if len(tokens) > MAX_SCHEDULE_EXPR_NODES * 3:
            raise _ScheduleSyntaxError("schedule_err_deep")
    return tokens


class _ScheduleParser:
    """Условие правила: и / или / не, скобки, «иначе»; между условиями без слова подразумевается «и»."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0
        self.nodes = 0
        self.has_date = False
        self.needs_chat = False
        self.wrapped: List[Tuple[int, int]] = []
        self.is_else = False

    def _peek(self):
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    @staticmethod
    def _op(token) -> str:
        if token is None:
            return ""
        kind, match = token
        if kind not in ("word", "op"):
            return ""
        text = match.group(kind).strip().lower()
        if kind == "op":
            return {"&&": "and", "&": "and", "||": "or", "|": "or", "!": "not"}.get(text, text)
        if text in _SCHEDULE_AND:
            return "and"
        if text in _SCHEDULE_OR:
            return "or"
        if text in _SCHEDULE_NOT:
            return "not"
        if text in _SCHEDULE_ELSE:
            return "else"
        return ""

    def _count(self):
        self.nodes += 1
        if self.nodes > MAX_SCHEDULE_EXPR_NODES:
            raise _ScheduleSyntaxError("schedule_err_deep")

    def parse(self):
        if not self.tokens:
            raise _ScheduleSyntaxError("schedule_err_format")
        if len(self.tokens) == 1 and self._op(self.tokens[0]) == "else":
            self.is_else = True
            return ("else",)
        node = self._or(0)
        if self.index != len(self.tokens):
            text = self.tokens[self.index][1].group(0).strip()
            raise _ScheduleSyntaxError("schedule_err_parens" if text == ")" else "schedule_err_unknown", text[:16])
        return node

    def _or(self, depth):
        if depth > MAX_SCHEDULE_EXPR_DEPTH:
            raise _ScheduleSyntaxError("schedule_err_deep")
        items = [self._and(depth)]
        while self._op(self._peek()) == "or":
            self.index += 1
            items.append(self._and(depth))
        return items[0] if len(items) == 1 else ("or", tuple(items))

    def _starts_unary(self, token) -> bool:
        if token is None:
            return False
        kind, match = token
        if kind == "op":
            return match.group("op").strip() in ("(", "!")
        if kind == "word":
            return self._op(token) in ("", "not")
        return True

    def _and(self, depth):
        items = [self._unary(depth)]
        while True:
            token = self._peek()
            if self._op(token) == "and":
                self.index += 1
                items.append(self._unary(depth))
            elif self._starts_unary(token):
                items.append(self._unary(depth))
            else:
                break
        return items[0] if len(items) == 1 else ("and", tuple(items))

    def _unary(self, depth):
        token = self._peek()
        if token is None:
            raise _ScheduleSyntaxError("schedule_err_format")
        if self._op(token) == "not":
            if depth > MAX_SCHEDULE_EXPR_DEPTH:
                raise _ScheduleSyntaxError("schedule_err_deep")
            self.index += 1
            self._count()
            return ("not", self._unary(depth + 1))
        kind, match = token
        if kind == "op" and match.group("op").strip() == "(":
            self.index += 1
            node = self._or(depth + 1)
            closing = self._peek()
            if closing is None or closing[0] != "op" or closing[1].group("op").strip() != ")":
                raise _ScheduleSyntaxError("schedule_err_parens")
            self.index += 1
            return node
        self.index += 1
        return self._atom(kind, match)

    def _atom(self, kind, match):
        self._count()
        if kind == "date":
            parts = [part for part in re.split(r"\s*\.\.\s*", match.group("date").strip()) if part]
            first, last = _parse_schedule_date(parts[0]), _parse_schedule_date(parts[-1])
            if (first is None or last is None or (first[0] is None) != (last[0] is None)
                    or (first[0] is not None and _date(*first) > _date(*last))):
                raise _ScheduleSyntaxError("schedule_err_date")
            self.has_date = True
            return ("date", (first, last))
        if kind == "time":
            h1, m1, h2, m2 = (int(x) for x in re.findall(r"[0-9]+", match.group("time")))
            if not (0 <= h1 <= 23 and 0 <= h2 <= 23 and 0 <= m1 <= 59 and 0 <= m2 <= 59) or (h1, m1) == (h2, m2):
                raise _ScheduleSyntaxError("schedule_err_time")
            return self._time_node(h1 * 60 + m1, h2 * 60 + m2)
        if kind == "part":
            names = [n for n in re.split(r"\s*[-–—]\s*", match.group("part").strip().casefold()) if n]
            first_part, last_part = DAYPART_BY_ALIAS.get(names[0]), DAYPART_BY_ALIAS.get(names[-1])
            if first_part is None or last_part is None:
                raise _ScheduleSyntaxError("schedule_err_unknown", match.group("part").strip()[:16])
            begin = DAYPART_BOUNDS[first_part][0]
            finish = DAYPART_BOUNDS[last_part][1]
            if begin == finish:
                raise _ScheduleSyntaxError("schedule_err_time")
            return self._time_node(begin, finish)
        if kind == "days":
            days = _schedule_days_set(match.group("days"))
            if days is None:
                raise _ScheduleSyntaxError("schedule_err_days")
            return ("days", days)
        if kind == "random":
            percent = int(match.group("pct"))
            if not 0 <= percent <= 100:
                raise _ScheduleSyntaxError("schedule_err_random")
            return ("random", percent)
        if kind == "chat":
            number = int(match.group("chat_id"))
            if abs(number) >= 2 ** 63:
                raise _ScheduleSyntaxError("schedule_err_unknown", match.group("chat")[:16])
            self.needs_chat = True
            return ("chat", normalize_dialog_id(number))
        if kind == "account":
            self.needs_chat = True
            return ("account", int(match.group("uid")))
        if kind == "word":
            word = match.group("word").strip().lower()
            if word in _SCHEDULE_KIND_BY_ALIAS:
                self.needs_chat = True
                return ("kind", _SCHEDULE_KIND_BY_ALIAS[word])
            if word in _SCHEDULE_DAYSETS:
                return ("days", _SCHEDULE_DAYSETS[word])
        raise _ScheduleSyntaxError("schedule_err_unknown", match.group(0).strip()[:16])

    def _time_node(self, begin, finish):
        if begin > finish:
            self.wrapped.append((begin, finish))
        return ("time", begin, finish)


def parse_schedule_expression(text: str):
    """Условие правила -> (дерево, ярус, нужен ли чат, интервалы через полночь). Ярусы: 0 — с датой, 1 — остальные, 2 — «иначе»."""
    if len(text) > MAX_SCHEDULE_EXPR_LENGTH:
        raise _ScheduleSyntaxError("schedule_err_deep")
    parser = _ScheduleParser(_schedule_tokens(text))
    tree = parser.parse()
    tier = 2 if parser.is_else else (0 if parser.has_date else 1)
    return tree, tier, parser.needs_chat, tuple(parser.wrapped)


_CHAT_ID_RE = re.compile(r"-?[0-9]{1,20}")
_CHAT_BIND_KEY_RE = re.compile(r"(?:[0-9]{1,16}:)?-?[0-9]{1,20}")


def parse_chat_configs(raw) -> Dict[str, str]:
    try:
        data = json.loads(as_text(raw).strip() or "{}")
    except (ValueError, RecursionError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): v for k, v in data.items() if _CHAT_BIND_KEY_RE.fullmatch(str(k)) and isinstance(v, str) and v}


def dump_chat_configs(mapping: Dict[str, str]) -> str:
    return json.dumps(mapping, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _parse_schedule_date(token: str):
    try:
        if "-" in token:
            year, month, day = (int(part) for part in token.split("-"))
        else:
            parts = [int(part) for part in token.split(".")]
            day, month = parts[0], parts[1]
            year = parts[2] if len(parts) > 2 else None
        _date(2000 if year is None else year, month, day)
        return year, month, day
    except (ValueError, IndexError, OverflowError):
        return None


def _schedule_dates_hit(dates, day) -> bool:
    (y1, m1, d1), (y2, m2, d2) = dates
    if y1 is not None:
        return _date(y1, m1, d1) <= day <= _date(y2, m2, d2)
    first, last, today = (m1, d1), (m2, d2), (day.month, day.day)
    return first <= today <= last if first <= last else (today >= first or today <= last)


def _parse_schedule_line(line: str, number: int):
    """Одна строка -> (правило, None) или (None, ошибка). Не бросает исключений."""
    try:
        if has_unsafe_text(line):
            return None, (number, "schedule_err_format", "")
        left, separator, name = line.partition("=")
        name = name.strip()
        if not separator or not name or not left.strip():
            return None, (number, "schedule_err_format", "")
        if len(name) > MAX_SCHEDULE_NAME_LENGTH:
            return None, (number, "schedule_err_size", "")
        tree, tier, needs_chat, wrapped = parse_schedule_expression(left)
        return ScheduleRule(tree, name, number, tier, needs_chat, wrapped), None
    except _ScheduleSyntaxError as exc:
        return None, (number, exc.code, exc.detail)
    except RecursionError:
        return None, (number, "schedule_err_deep", "")
    except Exception:
        return None, (number, "schedule_err_format", "")


def parse_schedule(raw):
    """Строки расписания -> (правила, ошибки). Ошибка — (номер строки, код, подробность).
    Слишком большой текст не разбирается вовсе: правил нет, ошибка одна."""
    text = as_text(raw)
    if len(text) > MAX_SCHEDULE_TEXT_LENGTH:
        return [], [(1, "schedule_err_size", "")]
    lines = text.splitlines()
    if len(lines) > MAX_SCHEDULE_LINES:
        return [], [(MAX_SCHEDULE_LINES + 1, "schedule_err_size", "")]
    rules, errors = [], []
    for number, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rule, error = _parse_schedule_line(line, number)
        if error is not None:
            errors.append(error)
        else:
            rules.append(rule)
    if len(rules) > MAX_SCHEDULE_RULES:
        errors.append((len(lines), "schedule_err_limit", ""))
    return rules[:MAX_SCHEDULE_RULES], errors


def clean_schedule_text(raw) -> str:
    """Для импорта: оставляет только правильные правила (до MAX_SCHEDULE_RULES), всё остальное отбрасывается."""
    text = as_text(raw)
    if len(text) > MAX_SCHEDULE_TEXT_LENGTH:
        return ""
    kept: List[str] = []
    for number, line in enumerate(text.splitlines()[:MAX_SCHEDULE_LINES], 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if _parse_schedule_line(line, number)[0] is not None:
            kept.append(line)
            if len(kept) >= MAX_SCHEDULE_RULES:
                break
    return "\n".join(kept)


class _ScheduleEnv:
    def __init__(self, minutes, anchor, chat, previous=None):
        self.minutes = minutes
        self.anchor = anchor
        self.previous = previous if previous is not None else anchor - timedelta(days=1)
        self._chat_source = chat
        self._chat = None

    def chat(self):
        if self._chat is None:
            try:
                info = self._chat_source() if callable(self._chat_source) else None
                self._chat = tuple(info) if info else (None, None, None)
            except Exception:
                self._chat = (None, None, None)
        return self._chat


def _schedule_in_tail(node, minutes: int) -> bool:
    """Есть ли в группе «и» интервал через полночь, который сейчас в своей части после полуночи.
    Под «не» не заходим: исключённое время не задаёт день группы."""
    op = node[0]
    if op == "time":
        return node[1] > node[2] and minutes < node[2]
    if op in ("and", "or"):
        return any(_schedule_in_tail(item, minutes) for item in node[1])
    return False


def _schedule_eval(node, env) -> bool:
    op = node[0]
    if op == "and":
        if _schedule_in_tail(node, env.minutes) and env.anchor != env.previous:
            saved = env.anchor
            env.anchor = env.previous
            try:
                return all(_schedule_eval(item, env) for item in node[1])
            finally:
                env.anchor = saved
        return all(_schedule_eval(item, env) for item in node[1])
    if op == "or":
        return any(_schedule_eval(item, env) for item in node[1])
    if op == "not":
        return not _schedule_eval(node[1], env)
    if op == "else":
        return True
    if op == "time":
        begin, finish, minutes = node[1], node[2], env.minutes
        return begin <= minutes < finish if begin < finish else (minutes >= begin or minutes < finish)
    if op == "days":
        return env.anchor.weekday() in node[1]
    if op == "date":
        return _schedule_dates_hit(node[1], env.anchor)
    if op == "random":
        return random.random() * 100 < node[1]
    kind, chat_id, uid = env.chat()
    if op == "kind":
        return kind == node[1]
    if op == "chat":
        return chat_id == node[1]
    if op == "account":
        return uid == node[1]
    return False


def schedule_match(rules, now, resolve=None, chat=None):
    """Имя (или результат resolve) первого подходящего правила. Порядок: правила с датой, остальные, затем «иначе».
    День недели и дата правила считаются по дню начала интервала, если время перешло через полночь.
    chat — функция без аргументов, возвращающая (вид чата, id чата, id аккаунта); вызывается только если она нужна."""
    minutes = now.hour * 60 + now.minute
    today = now.date()
    yesterday = today - timedelta(days=1)
    for tier in (0, 1, 2):
        for rule in rules:
            if rule.tier != tier:
                continue
            single_tail = rule.expr[0] == "time" and _schedule_in_tail(rule.expr, minutes)
            env = _ScheduleEnv(minutes, yesterday if single_tail else today, chat if rule.needs_chat else None, yesterday)
            try:
                hit = _schedule_eval(rule.expr, env)
            except Exception:
                hit = False
            if not hit:
                continue
            if resolve is None:
                return rule.name
            target = resolve(rule.name)
            if target:
                return target
    return None


def rename_schedule_target(raw, old_name: str, new_name: str) -> Tuple[str, bool]:
    old = as_text(old_name).strip().casefold()
    if not raw or not old:
        return raw, False
    lines, changed = [], False
    for line in as_text(raw).splitlines():
        head, sep, tail = line.partition("=")
        if sep and tail.strip().casefold() == old:
            flat_name = " ".join(as_text(sanitize_text(as_text(new_name))).split())
            line, changed = f"{head}= {flat_name}", True
        lines.append(line)
    return "\n".join(lines), changed


def parse_lines(raw) -> Tuple[str, ...]:
    seen = {}
    for line in as_text(raw).splitlines():
        line = line.strip()
        if line:
            seen.setdefault(line, None)
    return tuple(seen)


def parse_separators(raw) -> Tuple[str, ...]:
    items = tuple(item.strip() for item in as_text(raw).split(",") if item.strip())
    return items or tuple(DEFAULT_SEPARATORS.split(", "))


def java_int(value) -> Optional[int]:
    try:
        if callable(value):
            value = value()
        for method in ("longValue", "intValue"):
            if hasattr(value, method):
                return int(getattr(value, method)())
        if value is None or isinstance(value, bool):
            return None
        return int(value)
    except (TypeError, ValueError, AttributeError, OverflowError):
        return None


def to_dialog_id(value) -> Optional[int]:
    if value is None:
        return None
    direct = java_int(value)
    if direct is not None:
        return direct or None
    for attr in ("dialog_id", "dialogId", "did"):
        found = java_int(getattr(value, attr, None))
        if found:
            return found
    user_id = java_int(getattr(value, "user_id", None))
    if user_id:
        return user_id
    for attr in ("channel_id", "chat_id"):
        found = java_int(getattr(value, attr, None))
        if found:
            return -abs(found)
    return None


def copy_java_stream(source, sink, chunk_size: int = 64 * 1024, limit: Optional[int] = None):
    buffer = bytearray(chunk_size)
    total = 0
    while True:
        count = source.read(buffer)
        if count == -1:
            break
        if count > 0:
            total += count
            if limit is not None and total > limit:
                raise IOError("file is too large")
            sink.write(bytes(buffer[:count]))


def discard_file(path: Optional[str]):
    if not path:
        return
    try:
        if os.path.isfile(path):
            delete_file(path)
    except Exception:
        pass


def is_plugin_file(path) -> bool:
    try:
        text = as_text(path)
        if not text:
            return False
        base = os.path.realpath(get_plugins_dir())
        return os.path.realpath(text).startswith(base + os.sep)
    except Exception:
        return False


MEDIA_STORE_DIRS = frozenset({"Prefixfy_media", "Prefixfy_configurations"})


def is_media_store_file(path) -> bool:
    """Файл внутри папок самого плагина (или обычный медиафайл прямо в папке плагинов): чужие папки и служебные данные не подходят."""
    if not is_plugin_file(path):
        return False
    try:
        real = os.path.realpath(as_text(path))
        relative = os.path.relpath(real, os.path.realpath(get_plugins_dir()))
        top = relative.split(os.sep, 1)[0]
    except Exception:
        return False
    name = os.path.basename(real)
    if name.startswith(".") or name.endswith((".tmp", ".ota", ".bak", ".json")):
        return False
    if top in MEDIA_STORE_DIRS:
        return os.path.splitext(name)[1].lower() in MEDIA_EXTENSIONS or name.endswith(".bin")
    return (os.sep not in relative and os.path.splitext(real)[1].lower() in MEDIA_EXTENSIONS
            and not os.path.basename(real).startswith("."))


def safe_extension(name) -> str:
    ext = os.path.splitext(as_text(name))[1].lower()
    return ext if re.fullmatch(r"\.[a-z0-9]{1,8}", ext) else ""


def temp_dir(name: str) -> str:
    path = os.path.join(get_cache_dir(), "Prefixfy_tmp", name)
    ensure_dir_exists(path)
    return path


def is_inside(path, directory) -> bool:
    try:
        base = os.path.realpath(directory)
        return os.path.realpath(as_text(path)).startswith(base + os.sep)
    except Exception:
        return False


def is_import_temp(path) -> bool:
    """Только файлы, которые плагин сам распаковал из контейнера, а не произвольный путь из чужого конфига."""
    return bool(path) and is_inside(path, os.path.join(get_cache_dir(), "Prefixfy_tmp", "imports"))


def unique_temp(path: str) -> str:
    return f"{path}.{uuid.uuid4().hex[:8]}.tmp"


class VaultError(ValueError):
    pass


class StoreVault:
    """Запечатывание файлов хранилища (настройки и конфигурации): AES-GCM с привязкой к пути файла.

    Ключ данных (32 байта) лежит на диске только в обёрнутом виде: его оборачивает ключ из Android Keystore, который
    нельзя ни прочитать, ни подделать снаружи приложения. Поэтому подложить в хранилище свой файл в обход плагина
    нельзя: без ключа не получится ни собрать валидный файл, ни переставить чужой — путь файла входит в AAD.
    Отдельный ключ-флаг в Keystore означает «всё уже запечатано»: с него обычные (нешифрованные) файлы отвергаются,
    а удалить запись Keystore снаружи приложения нельзя, так что откатить режим подменой файлов тоже не выйдет.
    """

    MAGIC = b"PFXS\x01"
    KEY_ALIAS = "Prefixfy.store.kek.v1"
    FLAG_ALIAS = "Prefixfy.store.sealed.v2"
    IV_LEN = 12
    TAG_BITS = 128
    KEY_AAD = b"Prefixfy-datakey"

    def __init__(self):
        self._log = lambda message: None
        self._lock = threading.Lock()
        self._keystore = None
        self._usable: Optional[bool] = None
        self._strict = False
        self._data_key: Optional[bytes] = None
        self._degraded = False

    def attach(self, log):
        self._log = log

    @property
    def usable(self) -> bool:
        return bool(self._usable)

    @property
    def strict(self) -> bool:
        return bool(self._usable and self._strict)

    @property
    def degraded(self) -> bool:
        """49.0.0: ключ есть, но сейчас не открывается. Писать нельзя: открытый текст поверх запечатанных файлов
        при следующем запуске был бы отвергнут, и автосброс стёр бы данные."""
        return self._degraded

    @staticmethod
    def _jbytes(data: bytes):
        from java import jarray, jbyte
        data = bytes(data)
        try:
            array = jarray(jbyte)(data)
            if len(array) == len(data):
                return array
        except (TypeError, ValueError, OverflowError):
            pass
        return jarray(jbyte)([b - 256 if b > 127 else b for b in data])

    @staticmethod
    def _pybytes(array) -> bytes:
        try:
            data = bytes(array)
            if len(data) == len(array):
                return data
        except (TypeError, ValueError, BufferError):
            pass
        return bytes(x & 0xFF for x in array)

    def _store(self):
        if self._keystore is None:
            from java import jclass
            keystore = jclass("java.security.KeyStore").getInstance("AndroidKeyStore")
            keystore.load(None)
            self._keystore = keystore
        return self._keystore

    def _has(self, alias: str) -> bool:
        return bool(self._store().containsAlias(alias))

    def _create(self, alias: str):
        from java import jclass
        builder = jclass("android.security.keystore.KeyGenParameterSpec$Builder")(alias, 3)
        spec = builder.setBlockModes("GCM").setEncryptionPaddings("NoPadding").setKeySize(256).build()
        generator = jclass("javax.crypto.KeyGenerator").getInstance("AES", "AndroidKeyStore")
        generator.init(spec)
        generator.generateKey()

    def _kek_seal(self, plain: bytes, aad: bytes) -> bytes:
        from java import jclass
        cipher = jclass("javax.crypto.Cipher").getInstance("AES/GCM/NoPadding")
        cipher.init(1, self._store().getKey(self.KEY_ALIAS, None))
        cipher.updateAAD(self._jbytes(aad))
        body = self._pybytes(cipher.doFinal(self._jbytes(plain)))
        return self.MAGIC + self._pybytes(cipher.getIV()) + body

    def _kek_open(self, blob: bytes, aad: bytes) -> bytes:
        from java import jclass
        head = len(self.MAGIC) + self.IV_LEN
        iv = blob[len(self.MAGIC):head]
        cipher = jclass("javax.crypto.Cipher").getInstance("AES/GCM/NoPadding")
        spec = jclass("javax.crypto.spec.GCMParameterSpec")(self.TAG_BITS, self._jbytes(iv))
        cipher.init(2, self._store().getKey(self.KEY_ALIAS, None), spec)
        cipher.updateAAD(self._jbytes(aad))
        return self._pybytes(cipher.doFinal(self._jbytes(blob[head:])))

    def _aes(self, mode: int, key: bytes, iv: bytes, data: bytes, aad: bytes) -> bytes:
        from java import jclass
        cipher = jclass("javax.crypto.Cipher").getInstance("AES/GCM/NoPadding")
        secret = jclass("javax.crypto.spec.SecretKeySpec")(self._jbytes(key), "AES")
        cipher.init(mode, secret, jclass("javax.crypto.spec.GCMParameterSpec")(self.TAG_BITS, self._jbytes(iv)))
        cipher.updateAAD(self._jbytes(aad))
        return self._pybytes(cipher.doFinal(self._jbytes(data)))

    @staticmethod
    def _write_bytes(path: str, data: bytes):
        temp = unique_temp(path)
        try:
            with open(temp, "wb") as handle:
                handle.write(data)
                handle.flush()
                try:
                    os.fsync(handle.fileno())
                except OSError:
                    pass
            os.replace(temp, path)
        except BaseException:
            discard_file(temp)
            raise

    def _load_data_key(self, kek_fresh: bool = False) -> bytes:
        path = os.path.join(get_plugins_dir(), STORE_KEY_FILE)
        head = len(self.MAGIC) + self.IV_LEN
        try:
            with open(path, "rb") as handle:
                blob = handle.read(512)
        except OSError:
            blob = b""
        if blob:
            try:
                if not blob.startswith(self.MAGIC) or len(blob) <= head + 16:
                    raise ValueError("bad key file")
                key = self._kek_open(blob, self.KEY_AAD)
                if len(key) == 32:
                    return key
                raise ValueError("bad key length")
            except Exception as exc:
                if not kek_fresh and blob.startswith(self.MAGIC) and len(blob) > head + 16:
                    raise VaultError(f"data key is temporarily unreadable: {exc}")
                self._log(f"Prefixfy vault: data key is unreadable, creating a new one: {exc}")
        key = os.urandom(32)
        self._write_bytes(path, self._kek_seal(key, self.KEY_AAD))
        return key

    def prepare(self) -> bool:
        """Вызывается при запуске до чтения хранилища. False — Keystore недоступен, файлы остаются как были."""
        if self._usable is not None:
            return self._usable
        with self._lock:
            if self._usable is not None:
                return self._usable
            try:
                kek_fresh = not self._has(self.KEY_ALIAS)
                if kek_fresh:
                    self._create(self.KEY_ALIAS)
                self._data_key = self._load_data_key(kek_fresh)
                self._strict = self._has(self.FLAG_ALIAS)
                self._usable = True
            except Exception as exc:
                self._usable, self._strict, self._data_key = False, False, None
                self._degraded = isinstance(exc, VaultError)
                self._log(f"Prefixfy vault unavailable, store is not sealed: {exc}")
            return self._usable

    def finish_migration(self):
        """Всё хранилище запечатано: с этой минуты нешифрованные файлы отвергаются."""
        with self._lock:
            if not self._usable or self._strict:
                return
            try:
                if not self._has(self.FLAG_ALIAS):
                    self._create(self.FLAG_ALIAS)
                self._strict = True
            except Exception as exc:
                self._log(f"Prefixfy vault: cannot enable strict mode: {exc}")

    def destroy(self):
        """Удаляет оба ключа из Keystore и сбрасывает состояние: следующий prepare() создаст всё заново, как при первой установке."""
        with self._lock:
            try:
                store = self._store()
                for alias in (self.KEY_ALIAS, self.FLAG_ALIAS):
                    try:
                        if store.containsAlias(alias):
                            store.deleteEntry(alias)
                    except Exception as exc:
                        self._log(f"Prefixfy vault: cannot delete key {alias}: {exc}")
            except Exception as exc:
                self._log(f"Prefixfy vault: keystore is unavailable, keys were not deleted: {exc}")
            self._usable, self._strict, self._data_key = None, False, None
            self._degraded = False

    def subkey(self, label: bytes) -> Optional[bytes]:
        """53.0.0: 64 байта ключа, производного от ключа данных (HMAC-SHA512). None - хранилище недоступно."""
        if not self._usable or self._data_key is None:
            return None
        return hmac.new(bytes(self._data_key), b"Prefixfy-subkey/" + label, hashlib.sha512).digest()

    def seal(self, plain: bytes, aad: bytes) -> bytes:
        if not self._usable or self._data_key is None:
            raise VaultError("vault is not available")
        iv = os.urandom(self.IV_LEN)
        try:
            return self.MAGIC + iv + self._aes(1, self._data_key, iv, plain, aad)
        except Exception as exc:
            raise VaultError(f"sealing failed: {exc}")

    def unseal(self, blob: bytes, aad: bytes) -> bytes:
        head = len(self.MAGIC) + self.IV_LEN
        if not self._usable or self._data_key is None:
            raise VaultError("vault is not available")
        if not blob.startswith(self.MAGIC) or len(blob) <= head + 16:
            raise VaultError("not a sealed file")
        try:
            return self._aes(2, self._data_key, blob[len(self.MAGIC):head], blob[head:], aad)
        except Exception as exc:
            raise VaultError(f"authentication failed: {exc}")


VAULT = StoreVault()


def _store_aad(path: str) -> bytes:
    try:
        relative = os.path.relpath(os.path.realpath(path), os.path.realpath(get_plugins_dir()))
    except ValueError:
        relative = path
    return ("Prefixfy-store|" + relative.replace(os.sep, "/")).encode("utf-8")


def store_encode(path: str, text: str) -> bytes:
    VAULT.prepare()
    if VAULT.degraded:
        raise OSError("store vault is temporarily unavailable")
    data = text.encode("utf-8")
    return VAULT.seal(data, _store_aad(path)) if VAULT.usable else data


def store_decode(path: str, blob: bytes) -> str:
    VAULT.prepare()
    if blob.startswith(VAULT.MAGIC):
        return VAULT.unseal(blob, _store_aad(path)).decode("utf-8")
    if VAULT.strict:
        raise VaultError("unsealed file rejected")
    return blob.decode("utf-8")


def store_read_text(path: str) -> str:
    with open(path, "rb") as handle:
        blob = handle.read(MAX_STORE_JSON_BYTES + 1)
    if len(blob) > MAX_STORE_JSON_BYTES:
        raise ValueError("file is too large")
    return store_decode(path, blob)


VAULT_OVERHEAD = 64


def vault_read_bytes(path: str, limit: int) -> bytes:
    """Содержимое файла кэша или состояния (расшифрованное); как и раньше, длиннее limit байт не отдаёт."""
    VAULT.prepare()
    with open(path, "rb") as handle:
        blob = handle.read(limit + VAULT_OVERHEAD + 1)
    if blob.startswith(VAULT.MAGIC):
        if len(blob) > limit + VAULT_OVERHEAD:
            raise ValueError("file is too large")
        data = VAULT.unseal(blob, _store_aad(path))
    elif VAULT.strict:
        raise VaultError("unsealed file rejected")
    else:
        data = blob
    return data[:limit + 1]


def vault_read_json(path: str, limit: int):
    return json.loads(vault_read_bytes(path, limit).decode("utf-8"))


def vault_write_bytes(path: str, data: bytes):
    VAULT.prepare()
    if VAULT.degraded:
        raise OSError("store vault is temporarily unavailable")
    try:
        payload = VAULT.seal(data, _store_aad(path)) if VAULT.usable else data
    except VaultError as exc:
        raise OSError(str(exc))
    temp = unique_temp(path)
    try:
        with open(temp, "wb") as handle:
            handle.write(payload)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        os.replace(temp, path)
    except BaseException:
        discard_file(temp)
        raise


def vault_write_json(path: str, obj):
    vault_write_bytes(path, json.dumps(obj).encode("utf-8"))


def seal_plain_file(path: str, log) -> bool:
    """Запечатывает один оставшийся от прежних версий файл. False — не удалось, строгий режим включать рано."""
    try:
        with open(path, "rb") as handle:
            blob = handle.read(MAX_STORE_JSON_BYTES + VAULT_OVERHEAD + 1)
    except FileNotFoundError:
        return True
    except OSError as exc:
        log(f"Prefixfy store: cannot read {path} for sealing: {exc}")
        return False
    if blob.startswith(VAULT.MAGIC):
        return True
    try:
        if len(blob) > MAX_STORE_JSON_BYTES:
            raise ValueError("file is too large")
        json.loads(blob.decode("utf-8"))
    except Exception:
        discard_file(path)
        return True
    try:
        vault_write_bytes(path, blob)
    except Exception as exc:
        log(f"Prefixfy store: cannot seal {path}: {exc}")
        return False
    return True


def sweep_old_files(directory: str, max_age: float):
    deadline = time.time() - max_age
    try:
        entries = os.listdir(directory)
    except OSError:
        return
    for entry in entries:
        path = os.path.join(directory, entry)
        try:
            if os.path.isfile(path) and os.path.getmtime(path) < deadline:
                discard_file(path)
        except OSError:
            continue


def copy_file_limited(source: str, target: str, limit: int):
    total = 0
    with open(source, "rb") as reader, open(target, "wb") as writer:
        while True:
            chunk = reader.read(64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > limit:
                raise ValueError("media is too large")
            writer.write(chunk)


def unique_name(base: str, taken, ignore: str = "") -> str:
    used = {as_text(item).strip().casefold() for item in taken}
    used.discard(as_text(ignore).strip().casefold())
    name, number = base, 2
    while name.strip().casefold() in used:
        name = f"{base} {number}"
        number += 1
    return name


_TRACE_SINK = None


def trace_action(event: str, **fields):
    """Записать действие плагина в журнал отладки (если запись идёт и отладка разрешена флагом)."""
    sink = _TRACE_SINK
    if sink is not None:
        try:
            sink(event, fields)
        except Exception:
            pass


def _traced(event: str, label, fn, **extra):
    if fn is None:
        return fn

    def wrapper(*args, **kwargs):
        trace_action(event, item=label, **extra)
        return fn(*args, **kwargs)

    return wrapper


def _traced_change(event: str, key, fn):
    if fn is None:
        return fn

    def wrapper(value, *args, **kwargs):
        trace_action(event, key=key, value=value)
        return fn(value, *args, **kwargs)

    return wrapper


def Text(*args, **kwargs):
    label = kwargs.get("text")
    if kwargs.get("on_click") is not None:
        kwargs["on_click"] = _traced("tap", label, kwargs["on_click"])
    if kwargs.get("on_long_click") is not None:
        kwargs["on_long_click"] = _traced("long_tap", label, kwargs["on_long_click"])
    return _SdkText(*args, **kwargs)


def Switch(*args, **kwargs):
    if kwargs.get("on_change") is not None:
        kwargs["on_change"] = _traced_change("switch", kwargs.get("key"), kwargs["on_change"])
    return _SdkSwitch(*args, **kwargs)


def Selector(*args, **kwargs):
    if kwargs.get("on_change") is not None:
        kwargs["on_change"] = _traced_change("select", kwargs.get("key"), kwargs["on_change"])
    return _SdkSelector(*args, **kwargs)


def Input(*args, **kwargs):
    if kwargs.get("on_change") is not None:
        kwargs["on_change"] = _traced_change("input", kwargs.get("key"), kwargs["on_change"])
    return _SdkInput(*args, **kwargs)


FEATURE_FLAGS: Dict[str, bool] = {
    "regex_exceptions": True,
    "chat_type_rules": True,
    "edit_processing": True,
    "attached_media": True,
    "premium_emoji": True,
    "schedule": True,
    "chat_configs": True,
    "cute_effects": True,
    "articles": True,
    "account_settings": True,
    "config_import": True,
    "lang_auto": True,
    "lang_en": True,
    "lang_ja": True,
    "lang_ko": True,
    "lang_fr": True,
    "debug": False,
}
MASK_TAG_NAMES = ("date", "time", "datetime", "time12", "chat", "id", "weekday", "weekday_short", "year", "year_short", "month", "monthname", "day", "week", "yearday", "hour", "minute", "second", "ampm", "daypart", "timestamp", "tz", "chattype", "username", "count", "dice", "random_emoji", "emoji", "reply", "chatcount", "battery", "moon", "line", "since", "until", "quote", "countdown", "weather")
APPEARANCE_FLAGS: Dict[str, bool] = {
    "mask_rotation": True,
    "conditional_masks": True,
    "markdown": True,
    **{"md_" + _kind: True for _kind in ("bold", "italic", "strike", "spoiler", "mono", "quote")},
    **{"tag_" + _tag: True for _tag in MASK_TAG_NAMES},
    "text_styles": True,
    **{"style_" + _key: True for _key in STYLE_KEYS},
    "separator_spaces": True,
}
FEATURE_FLAGS.update(APPEARANCE_FLAGS)
_FLAG_NAME_RE = re.compile(r"[a-z][a-z0-9_]{0,31}")

AUTO = "auto"
AUTO_PROBABILITY = 0.5
AUTO_INTERVAL = 6 * 3600.0
AUTO_STATE_FILE = ".pfx_auto"


class AutoFlags:

    def __init__(self):
        self._lock = threading.Lock()
        self._draws: Dict[str, Tuple[bool, float]] = {}
        self._loaded = False
        self._rng = random.SystemRandom()

    @staticmethod
    def _path() -> str:
        return os.path.join(get_plugins_dir(), AUTO_STATE_FILE)

    def _load(self):
        if self._loaded:
            return
        self._loaded = True
        try:
            raw = vault_read_json(self._path(), MAX_STORE_JSON_BYTES)
        except (OSError, ValueError, RecursionError):
            return
        if not isinstance(raw, dict):
            return
        for name, item in raw.items():
            if (isinstance(name, str) and isinstance(item, list) and len(item) == 2 and isinstance(item[0], bool)
                    and isinstance(item[1], (int, float)) and not isinstance(item[1], bool) and math.isfinite(item[1])):
                self._draws[name] = (item[0], float(item[1]))

    def _save(self):
        try:
            vault_write_json(self._path(), {name: [on, stamp] for name, (on, stamp) in self._draws.items()})
        except OSError:
            pass

    def _expired(self, name: str, now: float) -> bool:
        draw = self._draws.get(name)
        return draw is None or now - draw[1] >= AUTO_INTERVAL or draw[1] > now + 60.0

    def _roll(self, name: str, now: float) -> Tuple[bool, bool]:
        """Новый бросок. Возвращает (старое значение или None, новое значение)."""
        old = self._draws.get(name)
        value = self._rng.random() < AUTO_PROBABILITY
        self._draws[name] = (value, now)
        return (old[0] if old else None, value)

    def sync(self, names) -> None:
        """Набор auto-флагов изменился: у новых монетка бросается сразу, у ушедших решение забывается."""
        names = set(names)
        with self._lock:
            self._load()
            now = time.time()
            changed = False
            for name in [n for n in self._draws if n not in names]:
                del self._draws[name]
                changed = True
            for name in names:
                if self._expired(name, now):
                    self._roll(name, now)
                    changed = True
            if changed:
                self._save()

    def value(self, name: str) -> bool:
        with self._lock:
            self._load()
            if name not in self._draws:
                self._roll(name, time.time())
                self._save()
            return self._draws[name][0]

    def tick(self, names) -> bool:
        """Перебросить монетку у тех, чей срок вышел. True, если хоть одно решение изменилось."""
        names = list(names)
        if not names:
            return False
        with self._lock:
            self._load()
            now = time.time()
            changed = rolled = False
            for name in names:
                if self._expired(name, now):
                    before, after = self._roll(name, now)
                    rolled = True
                    changed = changed or before != after
            if rolled:
                self._save()
            return changed

    def next_wait(self, names) -> Optional[float]:
        names = list(names)
        if not names:
            return None
        with self._lock:
            self._load()
            now = time.time()
            waits = []
            for name in names:
                draw = self._draws.get(name)
                waits.append(0.0 if draw is None or draw[1] > now + 60.0 else max(0.0, draw[1] + AUTO_INTERVAL - now))
            return min(waits)


class FeatureFlags:

    def __init__(self, defaults: Dict[str, bool]):
        self._defaults = dict(defaults)
        self._global: Dict[str, Any] = dict(defaults)
        self._values: Dict[str, bool] = dict(defaults)
        self._auto = AutoFlags()
        self._auto_names: frozenset = frozenset()
        self._accounts: Dict[int, Dict[str, bool]] = {}
        self._ids: frozenset = frozenset()
        self._serial = -1
        self._digest = ""
        self._soft = False
        self._lock = threading.Lock()

    @property
    def soft(self) -> bool:
        return self._soft

    @property
    def serial(self) -> int:
        return self._serial

    def floor(self, serial: int, digest: str = ""):
        with self._lock:
            if serial > self._serial:
                self._serial = serial
                self._digest = digest

    def set_soft(self, value: bool) -> bool:
        with self._lock:
            changed = self._soft != bool(value)
            self._soft = bool(value)
            return changed

    def on(self, name: str) -> bool:
        if self._soft and not name.startswith("lang_"):
            return False
        return self._values.get(name, True)

    def enabled(self, name: str) -> bool:
        """Значение флага без учёта «мягкой» блокировки (для OTA: это аварийный выключатель)."""
        return bool(self._values.get(name, True))

    def _compose(self) -> Dict[str, bool]:
        merged = dict(self._global)
        matched = [self._accounts[i] for i in sorted(self._ids) if i in self._accounts]
        for name in merged:
            votes = [item[name] for item in matched if name in item]
            if votes:
                merged[name] = all(votes)
            elif merged[name] == AUTO:
                merged[name] = self._auto.value(name)
        return merged

    def auto_tick(self) -> bool:
        """Раз в AUTO_INTERVAL: перебросить монетки auto-флагов. True, если итоговые значения изменились."""
        with self._lock:
            if not self._auto_names or not self._auto.tick(self._auto_names):
                return False
            return self._swap()

    def auto_wait(self) -> Optional[float]:
        """Через сколько секунд нужен следующий бросок; None, если auto-флагов нет и модуль спит."""
        return self._auto.next_wait(self._auto_names) if self._auto_names else None

    def _swap(self) -> bool:
        merged = self._compose()
        changed = merged != self._values
        self._values = merged
        return changed

    def apply(self, flags: Dict[str, Any], serial: int, accounts: Optional[Dict[int, Dict[str, bool]]] = None, digest: str = "") -> bool:
        base: Dict[str, Any] = dict(self._defaults)
        for name, value in flags.items():
            if name not in base:
                continue
            if isinstance(value, bool):
                base[name] = value
            elif value == AUTO:
                base[name] = AUTO
        cleaned: Dict[int, Dict[str, bool]] = {}
        for account_id, overrides in (accounts or {}).items():
            if isinstance(account_id, int) and not isinstance(account_id, bool) and isinstance(overrides, dict):
                cleaned[account_id] = {n: v for n, v in overrides.items() if n in self._defaults and isinstance(v, bool)}
        with self._lock:
            if serial < self._serial:
                raise ValueError(f"flags rollback rejected ({serial} < {self._serial})")
            if serial == self._serial and digest and self._digest and digest != self._digest:
                raise ValueError(f"flags serial {serial} reused with different content")
            self._global = base
            self._auto_names = frozenset(name for name, value in base.items() if value == AUTO)
            self._auto.sync(self._auto_names)
            self._accounts = cleaned
            self._serial = serial
            self._digest = digest
            return self._swap()

    def set_device_accounts(self, ids) -> bool:
        with self._lock:
            self._ids = frozenset(ids)
            return self._swap()


FEATURES = FeatureFlags(FEATURE_FLAGS)

MD_FLAG_BY_KIND = {
    "Bold": "md_bold", "Italic": "md_italic", "Strike": "md_strike", "Spoiler": "md_spoiler",
    "Code": "md_mono", "Pre": "md_mono", "Blockquote": "md_quote",
}
MARKDOWN_PICKS = (
    (0, "md_manual", None), (2, "md_bold", "md_bold"), (3, "md_italic", "md_italic"),
    (4, "md_strike", "md_strike"), (5, "md_spoiler", "md_spoiler"), (6, "md_mono", "md_mono"),
    (7, "md_quote", "md_quote"),
)


_HINT_TAG_RE = re.compile(r"\[([a-z0-9_]+)(?::[^\]]*)?\]")


def _hint_tag_on(match) -> bool:
    return FEATURES.on("tag_" + match.group(1))


def filter_tags_hint(text: str) -> str:
    text = as_text(text)
    if all(FEATURES.on("tag_" + name) for name in MASK_TAG_NAMES):
        return text
    if not any(FEATURES.on("tag_" + name) for name in MASK_TAG_NAMES):
        return ""
    head, _, more = text.partition("\n")
    tokens = list(_HINT_TAG_RE.finditer(head))
    if not tokens:
        return text
    kept = [token.group(0) for token in tokens if _hint_tag_on(token)]
    ending = head.rstrip()[-1:] if head.rstrip()[-1:] in (".", "。") else ""
    new_head = head[:tokens[0].start()] + ", ".join(kept) + ending if kept else ""
    clauses = [
        clause for clause in more.split("; ")
        if clause and (not _HINT_TAG_RE.search(clause) or any(_hint_tag_on(m) for m in _HINT_TAG_RE.finditer(clause)))
    ]
    more_ending = "." if more.rstrip().endswith((".", "。")) else ""
    new_more = "; ".join(clause.rstrip(".。 ") for clause in clauses) + more_ending if clauses else ""
    return "\n".join(part for part in (new_head, new_more) if part)


def md_kind_enabled(kind) -> bool:
    flag = MD_FLAG_BY_KIND.get(kind)
    return flag is None or FEATURES.on(flag)


def style_available(style) -> bool:
    return _is_int(style) and 0 <= style < TEXT_STYLE_COUNT and FEATURES.on("style_" + STYLE_KEYS[style])


def available_styles() -> List[int]:
    return [style for style in range(TEXT_STYLE_COUNT) if style_available(style)]


def random_style_pool() -> Tuple[int, ...]:
    return tuple(style for style in available_styles() if style not in _RANDOM_EXCLUDED)


def language_enabled(code) -> bool:
    return code == "ru" or FEATURES.on("lang_" + as_text(code))


def language_auto_enabled() -> bool:
    return FEATURES.on("lang_auto")


def enabled_language_indices() -> List[int]:
    return [index for index in range(1, len(LANGUAGE_MODES)) if language_enabled(LANGUAGE_MODES[index])]


def language_index_value(value) -> int:
    """Индекс языка из настроек. Вне списка — это автоопределение."""
    index = clamp_int(value, 0, -(2 ** 31), 2 ** 31)
    return index if 0 <= index < len(LANGUAGE_MODES) else 0


def has_language_choice() -> bool:
    return any(LANGUAGE_MODES[index] != "ru" for index in enabled_language_indices())


FREQUENCY_STEPS = (0.10, 0.25, 0.50, 0.75, 1.00)
FREQUENCY_ITEMS = tuple(f"{round(step * 100)}%" for step in FREQUENCY_STEPS)
SEPARATOR_FREQUENCY_DEFAULT = len(FREQUENCY_STEPS) - 1
CUTE_SENTENCE_FREQUENCY_DEFAULT = 2
CUTE_WORD_FREQUENCY_DEFAULT = 1

CUTE_EFFECT_KEYS = (
    "cute_kaomoji", "cute_sparkles", "cute_exclamations", "cute_punctuation", "cute_uwu_suffixes", "cute_actions",
    "cute_lowercase", "cute_uwu_speak", "cute_stutter", "cute_stretch", "cute_soft_sign",
)
CUTE_BOOL_KEYS = CUTE_EFFECT_KEYS + ("cute_actions_newline",)
CUTE_INT_KEYS = {
    "cute_sentence_frequency": (CUTE_SENTENCE_FREQUENCY_DEFAULT, 0, len(FREQUENCY_STEPS) - 1),
    "cute_word_frequency": (CUTE_WORD_FREQUENCY_DEFAULT, 0, len(FREQUENCY_STEPS) - 1),
    "cute_stretch_max": (0, 0, 1),
}
CUTE_KEYS = ("cute_enabled",) + CUTE_BOOL_KEYS + tuple(CUTE_INT_KEYS)


def frequency_step(value, default: int) -> float:
    return FREQUENCY_STEPS[clamp_int(value, default, 0, len(FREQUENCY_STEPS) - 1)]


CUTE_KAOMOJIS = (
    "(◕‿◕)", "♡(˘▽˘)♡", "(つ≧▽≦)つ", "(≧◡≦)", "(*^ω^*)", "(っ˘ω˘ς)", "(´｡• ω •｡`)", "ʕ•ᴥ•ʔ", "(づ｡◕‿‿◕｡)づ",
    "ฅ^•ﻌ•^ฅ", "(*˘︶˘*)", "(*¯︶¯*)", "( ˘ ³˘)♥", "(っ•ᴗ•)っ", "ლ(╹◡╹ლ)", "(๑˃ᴗ˂)ﻭ", "(灬ºωº灬)♡", "૮₍˶ᵔ ᵕ ᵔ˶₎ა",
    "(*ฅ́˘ฅ̀*)", "(●'◡'●)", "ฅ(^◕ᴥ◕^)ฅ", "(=^･ω･^=)", "ʕっ•ᴥ•ʔっ", "ʕ ꈍᴥꈍʔ", "ʕ´•ᴥ•`ʔ", "(◡ ω ◡)", "(◕ᴗ◕✿)",
    "꒰⑅ᵕ༚ᵕ꒱˖♡", "ପ(๑•ᴗ•๑)ଓ ♡", "(⁄ ⁄•⁄ω⁄•⁄ ⁄)",
)
CUTE_SPARKLES = (
    "✨", "⭐", "★", "☆", "₊˚⊹", "⋆｡°✩", "☆彡", "✧･ﾟ", "♡", "❀", "❁", "❃", "❋", "✿", "♫", "♪", "✧˖°", "⋆｡˚", "⋆⭒˚｡⋆",
    "✧*。", "‧₊˚✧", "ପ♡ଓ", "✩°｡⋆⸜", "✮", "✩₊˚.⋆", "☽˚｡⋆", "❥", "༘⋆", "ੈ✩‧₊˚", "ೃ࿔₊", "˗ˏˋ ★ ˎˊ˗",
)
CUTE_UWU_SUFFIXES = (
    "~", " nya~", " uwu", " owo", " >w<", " :3", " nyaaa", "σωσ", "◡ ω ◡", " OwO", " UwU~", " hehe~", " rawr~", " mew",
    " purr~", " ehehe", " uwu~", " (⁄ ⁄>⁄ω⁄<⁄ ⁄)", " kyaa~", " nyaa", " nyuu~", " mya~", " (◕ᴗ◕✿)", " teehee", " hehehe",
    " awoo~", " purrr", " pwease",
)
CUTE_UWU_SUFFIXES_SPACED = tuple(item for item in CUTE_UWU_SUFFIXES if item.startswith(" "))
CUTE_EXCLAMATIONS = (
    "~!", "!!", "!!!", "!~", "!❤", "!✨", "!💖", "!⭐", "!!!1!", "! nya~", "!?!?", "!!!💕", "~!!~", "! ꒰◍ᐡᐤᐡ◍꒱",
    "! ❁◕ ‿ ◕❁", "!!♡", "! (*ฅ́˘ฅ̀*)", "~✿!", "! ♡₊˚", "!⋆₊", "! 🎀", "! 🌸", "!🌟", "!☆",
)
CUTE_PERIODS = (
    ".~", ".✨", ".🌸", ".💖", "~~", " ^^", "₊˚ʚ ᗢ₊˚✧", "✿", ".♡", ".˚ʚ♡ɞ˚", ".ᐟ", ".⋆", ".♬", ".⋆˙⟡♡",
    ".𓆩♡𓆪", ".ੈ✩‧₊˚", ".𓍢ִ໋🌷͙֒", ".:₊˚◞♡", "◞♡ₓₒ",
)
CUTE_QUESTIONS = (
    "?!!", "???", "❓💖", "?~", "❓✨", " <(°.°<)", " uwu?", "?✧", "?🥺", "?(ㅅ´ ˘ `)", "??♡", "??🌸", "?☆", "?♡",
    "?꒰◍ᐡᐤᐡ◍꒱", "?⁺◟(◔ั₀◔ั )◞⁺", " (◕ᴗ◕✿)?", "?⋆", "?𓍢ִ໋🌷͙֒", " nyaa?",
)
CUTE_ACTIONS = {
    "ru": ("*обнимает*", "*нежно обнимает*", "*гладит по голове*", "*хихикает*", "*мурлычет*", "*улыбается*", "*подмигивает*",
           "*машет лапкой*", "*краснеет*", "*прыгает от радости*", "*делает большие глаза*", "*играет с волосами*",
           "*качает хвостиком*", "*делает милое личико*", "*танцует от счастья*", "*прячется за лапками*", "*радостно вздыхает*"),
    "en": ("*hugs*", "*gentle hug*", "*pats head*", "*giggles*", "*purrs*", "*smiles*", "*winks*", "*waves paw*", "*blushes*",
           "*jumps with joy*", "*makes big eyes*", "*plays with hair*", "*wags tail*", "*makes cute face*", "*happy dance*",
           "*hides behind paws*", "*happy sigh*", "*nuzzles*", "*tippy taps*", "*boops nose*"),
    "ja": ("*ぎゅっ*", "*なでなで*", "*にこにこ*", "*くすくす*", "*ごろごろ*", "*ウインク*", "*てれてれ*", "*ぴょんぴょん*",
           "*しっぽふりふり*", "*うるうる*", "*すりすり*"),
    "ko": ("*꼬옥 안아줌*", "*쓰담쓰담*", "*키득키득*", "*골골*", "*방긋*", "*윙크*", "*부끄부끄*", "*폴짝폴짝*",
           "*꼬리 살랑살랑*", "*눈 반짝반짝*", "*볼 비비기*"),
    "fr": ("*câlin*", "*caresse la tête*", "*glousse*", "*ronronne*", "*sourit*", "*fait un clin d’œil*", "*rougit*",
           "*saute de joie*", "*remue la queue*", "*fait les yeux doux*", "*frotte son nez*"),
}
CUTE_VOWELS = {
    "ru": "аеёиоуыэюяАЕЁИОУЫЭЮЯ",
    "en": "aeiouAEIOUàâäæéèêëîïôöœùûüÿÀÂÄÆÉÈÊËÎÏÔÖŒÙÛÜŸ",
}
CUTE_TITLE_ABBREVIATIONS = frozenset((
    "г", "ул", "пр", "пл", "д", "кв", "корп", "им", "проф", "акад", "тов", "гр",
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st",
))
CUTE_ABBREVIATIONS = frozenset((
    "гг", "в", "р", "с", "н", "э", "рис", "табл", "стр", "см", "ср", "напр", "тел", "руб", "коп", "тыс", "млн", "млрд",
    "др", "англ", "рус", "обл", "vs", "fig", "approx", "dept", "inc", "ltd",
))
CUTE_SOFT_SIGN_CONSONANTS = "бвгджзклмнпрстфхцчшщ"
CUTE_UWU_TABLE = str.maketrans({"r": "w", "l": "w", "R": "W", "L": "W", "р": "в", "л": "в", "Р": "В", "Л": "В"})

assert SETTING_DEFAULTS["separator_frequency"] == SEPARATOR_FREQUENCY_DEFAULT
assert all(SETTING_DEFAULTS[_key] is False for _key in ("cute_enabled",) + CUTE_BOOL_KEYS)
assert all(SETTING_DEFAULTS[_key] == _spec[0] for _key, _spec in CUTE_INT_KEYS.items())


CUTE_SIGNATURES = tuple(sorted(
    set(CUTE_KAOMOJIS)
    | {action for actions in CUTE_ACTIONS.values() for action in actions}
    | {item for item in CUTE_SPARKLES if len(item) >= 2 and item != "☆彡"}
    | {item.strip() for item in CUTE_UWU_SUFFIXES if len(item.strip()) >= 4},
    key=len, reverse=True,
))


def cute_already_applied(text: str) -> bool:
    """49.2.0: в тексте уже есть каомодзи, «*действие*» или другая метка милых эффектов. Используется при
    правке: иначе каждое редактирование добавляло ещё по каомодзи и действию в каждое предложение."""
    return any(signature in text for signature in CUTE_SIGNATURES)


class CuteOptions:
    """Настройки «милых» эффектов, разобранные один раз при сборке RuntimeSettings."""
    __slots__ = ("enabled", "active", "sentence_p", "word_p", "stretch_max", "language") + tuple(k[5:] for k in CUTE_BOOL_KEYS)

    def __init__(self, get, language: Optional[str] = None):
        self.enabled = bool(get("cute_enabled")) and FEATURES.on("cute_effects")
        for key in CUTE_BOOL_KEYS:
            setattr(self, key[5:], bool(get(key)))
        self.sentence_p = frequency_step(get("cute_sentence_frequency"), CUTE_SENTENCE_FREQUENCY_DEFAULT)
        self.word_p = frequency_step(get("cute_word_frequency"), CUTE_WORD_FREQUENCY_DEFAULT)
        self.stretch_max = 2 if clamp_int(get("cute_stretch_max"), 0, 0, 1) == 0 else 3
        self.language = language if language in CUTE_ACTIONS else "en"
        self.active = self.enabled and any(getattr(self, key[5:]) for key in CUTE_EFFECT_KEYS)


class RuntimeSettings:
    __slots__ = (
        "language", "chat_scope_enabled", "process_message", "process_media", "process_article", "process_edit",
        "process_edit_message", "process_edit_media", "process_edit_article", "skip_once_on_edit",
        "mask", "mask_parts", "mask_link", "markdown_enabled", "markdown_style", "markdown_wrap", "text_style_enabled", "text_style",
        "text_style_random", "text_style_translit", "style_only", "mask_rotation_enabled", "masks_list", "mask_rotation_mode", "regex_exceptions", "conditional_rules", "chat_type_rules",
        "separator_enabled", "separators", "separator_count", "separator_chance", "separator_spaces", "separator_space_mode", "cute",
        "exceptions", "ignore_kinds", "ignore_emoji_only", "disabled_chats",
        "media_enabled", "media_path", "media_name", "media_mime", "raw",
    )

    def __init__(self, raw: Dict[str, Any]):
        self.raw = dict(raw)

        def get(key):
            value = raw.get(key, SETTING_DEFAULTS[key])
            return sanitize_text(value) if isinstance(value, str) else value

        self.language = language_index_value(get("language"))
        self.chat_scope_enabled = bool(get("chat_scope_enabled"))
        self.process_message = bool(get("process_message"))
        self.process_media = bool(get("process_media"))
        self.process_article = bool(get("process_article")) and FEATURES.on("articles")
        self.process_edit = bool(get("process_edit")) and FEATURES.on("edit_processing")
        self.process_edit_message = bool(get("process_edit_message"))
        self.process_edit_media = bool(get("process_edit_media"))
        self.process_edit_article = bool(get("process_edit_article")) and FEATURES.on("articles")
        self.skip_once_on_edit = bool(get("skip_once_on_edit"))
        style = clamp_int(get("markdown_style"), 0, 0, MARKDOWN_STYLE_COUNT - 1)
        self.markdown_enabled = bool(get("markdown_enabled")) and style != 1 and FEATURES.on("markdown")
        self.markdown_style = 0 if style == 1 else style
        wrap_kind = MARKDOWN_WRAP_KINDS.get(self.markdown_style) if self.markdown_enabled else None
        self.markdown_wrap = wrap_kind if wrap_kind and md_kind_enabled(wrap_kind) else None
        self.mask = as_text(get("mask"))
        self.text_style = clamp_int(get("text_style"), 0, 0, TEXT_STYLE_COUNT - 1)
        self.text_style_random = bool(get("text_style_random"))
        style_ok = bool(random_style_pool()) if self.text_style_random else style_available(self.text_style)
        self.text_style_enabled = bool(get("text_style_enabled")) and FEATURES.on("text_styles") and style_ok
        self.text_style_translit = bool(get("text_style_translit"))
        self.style_only = frozenset(word.casefold() for word in parse_lines(get("style_words"))[:MAX_STYLE_WORDS])
        self.mask_rotation_enabled = bool(get("mask_rotation_enabled")) and FEATURES.on("mask_rotation")
        self.masks_list = tuple([item.strip() for item in as_text(get("masks_list")).splitlines() if item.strip() and is_valid_mask(item.strip())][:MAX_MASKS_IN_LIST])
        if bool(get("mask_rotation_enabled")) and not self.mask_rotation_enabled and self.masks_list and not self.mask.strip():
            self.mask = self.masks_list[0]
        self.mask_rotation_mode = clamp_int(get("mask_rotation_mode"), 0, 0, 1)
        try:
            self.regex_exceptions = compile_regex_exceptions(get("regex_exceptions")) if FEATURES.on("regex_exceptions") else ()
        except Exception:
            self.regex_exceptions = ()
        try:
            self.conditional_rules = tuple(parse_conditional_masks(get("conditional_masks"))[0]) if FEATURES.on("conditional_masks") else ()
        except Exception:
            self.conditional_rules = ()
        try:
            self.chat_type_rules = parse_chat_type_rules(get("chat_type_rules")) if FEATURES.on("chat_type_rules") else frozenset(CHAT_KINDS)
        except Exception:
            self.chat_type_rules = frozenset(CHAT_KINDS)
        self.mask_parts = split_mask(self.mask)
        if self.mask_parts is None and not self.mask.strip():
            self.mask_parts = ("", "")
        self.mask_link = mask_link(self.mask)
        self.separator_enabled = bool(get("separator_enabled"))
        self.separators = parse_separators(get("custom_emojis"))
        self.separator_count = clamp_int(get("emoji_count"), 1, 1, MAX_SEPARATOR_COUNT)
        self.separator_chance = frequency_step(get("separator_frequency"), SEPARATOR_FREQUENCY_DEFAULT)
        spaces_on = FEATURES.on("separator_spaces")
        self.separator_spaces = bool(get("separator_spaces")) if spaces_on else True
        self.separator_space_mode = clamp_int(get("separator_space_mode"), 0, 0, 2) if spaces_on else 0
        self.cute = CuteOptions(get, LANGUAGE_MODES[self.language])
        self.exceptions = parse_lines(get("exceptions"))
        self.ignore_kinds = frozenset(
            kind for kind, key in zip(IGNORE_KINDS, IGNORE_KEYS) if bool(raw.get(key, SETTING_DEFAULTS[key]))
        )
        self.ignore_emoji_only = bool(get("ignore_emoji_only"))
        self.disabled_chats = parse_chat_ids(get("disabled_chats"))
        self.media_enabled = bool(get("attached_media_enabled")) and FEATURES.on("attached_media")
        self.media_path = as_text(get("attached_media_path"))
        self.media_name = as_text(get("attached_media_name"))
        self.media_mime = as_text(get("attached_media_mime"))

    def is_chat_allowed(self, dialog_id: Optional[int]) -> bool:
        if not dialog_id:
            return self.chat_scope_enabled
        listed = dialog_id in self.disabled_chats
        return not listed if self.chat_scope_enabled else listed

    @property
    def mask_is_active(self) -> bool:
        parts = self.mask_parts
        return parts is not None and bool(
            parts[0] or parts[1] or self.mask_link or self.text_style_enabled or self.markdown_wrap
        )


_MISSING_SETTING = object()


def bulk_set_settings(plugin, values: Dict[str, Any]) -> bool:
    """52.0.0: записать много настроек одной операцией.

    plugin_settings.set_setting на каждый ключ заново сериализует и записывает с fsync общий файл настроек ВСЕХ
    плагинов. Смена конфигурации (~70 ключей), импорт и сброс делали так десятки полных перезаписей подряд.
    Здесь чтение, слияние и запись идут под замком хранилища SDK, чтобы параллельный set_setting не потерялся.
    Если пакетная запись не прошла (проверка по прочитанным значениям), ключи пишутся по одному, как раньше."""
    if not values:
        return True
    lock = getattr(_settings_store, "_lock", None)
    try:
        with lock if lock is not None else nullcontext():
            merged = plugin.export_settings()
            if not isinstance(merged, dict):
                raise TypeError("settings export is not a dict")
            merged.update(values)
            plugin.import_settings(merged, reload_settings=False)
        if all(plugin.get_setting(key, _MISSING_SETTING) == value for key, value in values.items()):
            return True
        plugin.log("Prefixfy: bulk settings write was not stored, writing keys one by one")
    except Exception as exc:
        plugin.log(f"Prefixfy: bulk settings write failed, writing keys one by one: {exc}")
    ok = True
    for key, value in values.items():
        try:
            plugin.set_setting(key, value)
        except Exception as exc:
            ok = False
            plugin.log(f"Prefixfy: setting {key} was not stored: {exc}")
    return ok


class PrefixfySettings:
    DEFAULTS = {**SETTING_DEFAULTS, **TRANSIENT_SETTING_DEFAULTS, **OTA_SETTING_DEFAULTS}

    def __init__(self, plugin):
        self.plugin = plugin
        self._batch_lock = threading.RLock()
        self._batch_depth = 0
        self._pending: Dict[str, Any] = {}
        self._pending_reload = False

    def _read(self, key, default):
        with self._batch_lock:
            if key in self._pending:
                return self._pending[key]
        return self.plugin.get_setting(key, default)

    def get(self, key, default=None):
        if default is None:
            default = self.DEFAULTS.get(key)
        value = self._read(key, default)
        return sanitize_text(value) if isinstance(value, str) else value

    def set(self, key, value, reload_settings=False):
        trace_action("setting", key=key, value=value)
        with self._batch_lock:
            batching = self._batch_depth > 0
            if batching:
                self._pending[key] = value
                self._pending_reload = self._pending_reload or bool(reload_settings)
        if not batching:
            self.plugin.set_setting(key, value, reload_settings=reload_settings)
        self.plugin.handle_setting_changed(key)

    @contextmanager
    def batch(self):
        """52.0.0: все set() внутри пишутся на диск одной операцией при выходе из внешнего batch()."""
        with self._batch_lock:
            self._batch_depth += 1
        try:
            yield self
        finally:
            with self._batch_lock:
                self._batch_depth -= 1
                if self._batch_depth > 0:
                    pending, reload_settings = {}, False
                else:
                    pending, reload_settings = self._pending, self._pending_reload
                    self._pending, self._pending_reload = {}, False
            if pending:
                bulk_set_settings(self.plugin, pending)
            if reload_settings:
                self.plugin.reload_settings_ui()

    def raw(self) -> Dict[str, Any]:
        values = {key: self._read(key, default) for key, default in SETTING_DEFAULTS.items()}
        return {key: sanitize_text(value) if isinstance(value, str) else value for key, value in values.items()}

    def snapshot(self) -> RuntimeSettings:
        return RuntimeSettings(self.raw())

    def language_index(self) -> int:
        return language_index_value(self.get("language"))

    def separator_count(self) -> int:
        return clamp_int(self.get("emoji_count"), 1, 1, MAX_SEPARATOR_COUNT)

    def markdown_enabled(self) -> bool:
        return bool(self.get("markdown_enabled")) and clamp_int(self.get("markdown_style"), 0, 0, MARKDOWN_STYLE_COUNT - 1) != 1

    def markdown_style_value(self) -> int:
        style = clamp_int(self.get("markdown_style"), 0, 0, MARKDOWN_STYLE_COUNT - 1)
        return 0 if style == 1 else style

    def disabled_chat_ids(self) -> set:
        return set(parse_chat_ids(self.get("disabled_chats")))

    def set_disabled_chat_ids(self, ids):
        ordered = sorted({int(chat_id) for chat_id in ids})
        self.set("disabled_chats", "\n".join(str(chat_id) for chat_id in ordered))


class _SnapshotSettings:
    """46.0.0: значения сохранённой (не активной) конфигурации только для чтения: те же методы, что у PrefixfySettings."""

    def __init__(self, values):
        self._values = dict(SETTING_DEFAULTS)
        if isinstance(values, dict):
            self._values.update(values)

    def get(self, key, default=None):
        if key in self._values:
            value = self._values[key]
            return sanitize_text(value) if isinstance(value, str) else value
        return PrefixfySettings.DEFAULTS.get(key) if default is None else default

    language_index = PrefixfySettings.language_index
    separator_count = PrefixfySettings.separator_count
    markdown_enabled = PrefixfySettings.markdown_enabled
    markdown_style_value = PrefixfySettings.markdown_style_value


class TextFilter:
    def __init__(self, settings: RuntimeSettings):
        self.exceptions = settings.exceptions
        self.ignore_emoji_only = settings.ignore_emoji_only
        self.regex_exceptions = settings.regex_exceptions

    def skips(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped:
            return True
        for item in self.exceptions:
            if stripped.startswith(item) or stripped.endswith(item):
                return True
        if self.regex_exceptions:
            sample = text[:REGEX_TEXT_LIMIT]
            tail_start = len(text) - REGEX_TEXT_LIMIT if len(text) > REGEX_TEXT_LIMIT else None
            for pattern in self.regex_exceptions:
                if pattern.search(sample):
                    return True
                if tail_start is not None and pattern.search(text, tail_start):
                    return True
        if self.ignore_emoji_only:
            try:
                return _emoji_only_regex().fullmatch(stripped) is not None
            except re.error:
                return False
        return False


class Transformation:
    def transform(self, text: str) -> str:
        raise NotImplementedError


class MaskTransformation(Transformation):
    def __init__(self, settings: RuntimeSettings):
        self.left, self.right = settings.mask_parts
        self.table: List[Tuple[str, str]] = []
        self.link_id: Optional[int] = None
        self.text_style_enabled = settings.text_style_enabled
        self.text_style = settings.text_style
        self.text_style_translit = settings.text_style_translit
        self.style_only = settings.style_only
        self.wrap_id: Optional[int] = None
        compiled = compile_mask_markdown(settings.mask, parse_markdown=settings.markdown_enabled)
        if compiled is not None:
            self.left, self.right, self.table, self.link_id = compiled
            wrap_kind = settings.markdown_wrap
            if wrap_kind and len(self.table) < _MD_MAX_ENTITIES and not (wrap_kind in _MD_CODE_KINDS and self.table):
                self.wrap_id = len(self.table)
                self.table.append((wrap_kind, ""))
        self.separator: Optional["SeparatorTransformation"] = None
        self.left_plain = "" if self._has_custom_emoji(self.left) else _MD_SENTINEL_RE.sub("", self.left)
        self.right_plain = "" if self._has_custom_emoji(self.right) else _MD_SENTINEL_RE.sub("", self.right)
        self.left_visible = _MD_SENTINEL_RE.sub("", self.left)

    def _has_custom_emoji(self, side: str) -> bool:
        for char in side:
            code = ord(char)
            if _MD_BASE <= code < _MD_BASE + 2 * len(self.table):
                if self.table[(code - _MD_BASE) // 2][0] == "CustomEmoji":
                    return True
        return False

    def has_mask(self, text: str) -> bool:
        return bool(self.left_plain and text.startswith(self.left_plain)) or bool(self.right_plain and text.endswith(self.right_plain))

    def prefix_for(self, text: str) -> str:
        return "" if (self.left_plain and text.startswith(self.left_plain)) else self.left_visible

    def transform(self, text: str) -> str:
        has_left = bool(self.left_plain) and text.startswith(self.left_plain)
        has_right = bool(self.right_plain) and text.endswith(self.right_plain)
        prefix = "" if has_left else self.left
        suffix = "" if has_right else self.right
        head = self.left_plain if has_left else ""
        tail = self.right_plain if has_right and len(text) >= len(head) + len(self.right_plain) else ""
        middle = text[len(head):len(text) - len(tail)] if (head or tail) else text
        if self.text_style_enabled:
            middle = apply_text_style(middle, self.text_style, self.text_style_translit, self.style_only)
        if self.separator is not None:
            middle = self.separator.transform(middle)
        text = head + middle + tail
        if self.table:
            body = _MD_BODY_START + text + _MD_BODY_END
            if self.link_id is not None:
                body = chr(_MD_BASE + 2 * self.link_id) + body + chr(_MD_BASE + 2 * self.link_id + 1)
            whole = prefix + body + suffix
            if self.wrap_id is not None:
                whole = chr(_MD_BASE + 2 * self.wrap_id) + whole + chr(_MD_BASE + 2 * self.wrap_id + 1)
            return whole
        return prefix + text + suffix


class SeparatorTransformation(Transformation):
    _WHITESPACE = re.compile(r"(\s+)")
    _WORD_GAP = re.compile("(\u3000+)")

    def __init__(self, settings: RuntimeSettings, table: Optional[List[Tuple[str, str]]] = None):
        if table is None:
            table = []
        prepared = (inject_custom_emoji(_MD_SENTINEL_RE.sub("", item), table) for item in settings.separators)
        self.separators = tuple(item for item in prepared if item) or tuple(DEFAULT_SEPARATORS.split(", "))
        self.count = settings.separator_count
        self.chance = settings.separator_chance
        self.spaces = settings.separator_spaces
        self.space_mode = settings.separator_space_mode
        self._gap = self._WORD_GAP if settings.text_style_enabled and settings.text_style == STYLE_VAPORWAVE else self._WHITESPACE
        self._marks = tuple(sorted({_MD_SENTINEL_RE.sub("", item) for item in self.separators} - {""}, key=len, reverse=True))

    def _is_mark(self, token: str) -> bool:
        return _MD_SENTINEL_RE.sub("", token) in self._marks

    def _beside_mark(self, before: str, after: str) -> bool:
        """49.2.0: промежуток рядом с уже стоящим разделителем не трогаем. Так повторная обработка (правка,
        пересылка своего же сообщения) не удваивает разделители, а обычное тире «Москва — столица» не обрастает ими."""
        if self._is_mark(before) or self._is_mark(after):
            return True
        clean_before, clean_after = _MD_SENTINEL_RE.sub("", before), _MD_SENTINEL_RE.sub("", after)
        if self.spaces and self.space_mode == 1:
            return clean_after.startswith(self._marks)
        if self.spaces and self.space_mode == 2:
            return clean_before.endswith(self._marks)
        return False

    @staticmethod
    def _glue_invisible(tokens: List[str]) -> List[str]:
        if len(tokens) < 3:
            return tokens
        result = [tokens[0]]
        for index in range(1, len(tokens), 2):
            gap, word = tokens[index], tokens[index + 1]
            if _MD_INVISIBLE_RE.fullmatch(word):
                result[-1] += gap + word
            else:
                result.extend((gap, word))
        if len(result) >= 3 and _MD_INVISIBLE_RE.fullmatch(result[0]):
            result[0:3] = [result[0] + result[1] + result[2]]
        return result

    def transform(self, text: str) -> str:
        pool = list(self.separators)
        random.shuffle(pool)
        position = 0
        lines = []
        for line in text.split("\n"):
            core = line.strip()
            tokens = self._glue_invisible(self._gap.split(core))
            if len(tokens) < 3:
                lines.append(line)
                continue
            leading = line[:len(line) - len(line.lstrip())]
            trailing = line[len(line.rstrip()):]
            parts = [tokens[0]]
            for index in range(1, len(tokens), 2):
                gap, word = tokens[index], tokens[index + 1]
                if self._beside_mark(tokens[index - 1], word) or (
                        self.chance < 1.0 and random.random() >= self.chance):
                    parts.append(gap)
                    parts.append(word)
                    continue
                chosen = []
                for _ in range(self.count):
                    chosen.append(pool[position % len(pool)])
                    position += 1
                joined = ("" if not self.spaces else " ").join(chosen)
                if not self.spaces:
                    parts.append(joined)
                elif self.space_mode == 1:
                    parts.append(gap + joined)
                elif self.space_mode == 2:
                    parts.append(joined + gap)
                else:
                    parts.append(gap + joined + gap)
                parts.append(word)
            lines.append(leading + "".join(parts) + trailing)
        return "\n".join(lines)


_LINK_ANY = "[^\\s<>\"`«»“”„]"
_LINK_END = "[^\\s<>\"`«»“”„.,;:!?)\\]}'’…]"
_LINK_TLDS = (
    "com|net|org|ru|ua|io|me|info|biz|edu|gov|app|dev|ai|tv|su|by|kz|xyz|online|site|ph|ly|gg|cc|fm|ws|"
    "pro|club|top|cloud|tech|store|link|page|space|de|fr|pl|jp|kr|uk|eu|co"
)
_LINK_PATTERN = (
    r"[A-Za-z][A-Za-z0-9+.\-]{1,15}://" + _LINK_ANY + "*" + _LINK_END
    + r"|(?<!\w)(?:mailto|tg):" + _LINK_ANY + "*" + _LINK_END
    + r"|(?<![\w@])www\." + _LINK_ANY + "*" + _LINK_END
    + r"|(?<![\w.%+\-@/])[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}(?![\w@])"
    + r"|(?<![\w@.\-/])(?:[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?\.)+(?i:" + _LINK_TLDS + r")(?![\w\-])"
    + r"(?::\d{1,5}(?!\d))?(?:[/?#](?:" + _LINK_ANY + "*" + _LINK_END + ")?)?"
)
_PROTECT_PARTS = (
    ("code", r"```[\s\S]*?```|`[^`\n]+`"),
    ("mentions", r"(?<![\w@])@[A-Za-z][A-Za-z0-9_]{2,31}"),
    ("commands", r"(?<!\S)/[A-Za-z][A-Za-z0-9_]*(?:@[A-Za-z][A-Za-z0-9_]*)?(?![\w/])"),
    ("links", _LINK_PATTERN),
    ("hashtags", r"(?<![\w&/#])#(?!\d+(?!\w))\w{1,64}(?:@[A-Za-z][A-Za-z0-9_]{2,31})?"),
    ("cashtags", r"(?<![\w$])\$[A-Za-z]{1,8}(?!\w)"),
)
_LEADING_PARTS = (
    ("commands", r"[/!.][A-Za-z][A-Za-z0-9_]*(?:@[A-Za-z][A-Za-z0-9_]*)?"),
    ("mentions", r"@[A-Za-z][A-Za-z0-9_]{2,31}"),
)


@lru_cache(maxsize=64)
def _protected_re(kinds: frozenset):
    parts = [pattern for kind, pattern in _PROTECT_PARTS if kind in kinds]
    return re.compile("|".join(parts)) if parts else None


@lru_cache(maxsize=16)
def _leading_special_re(kinds: frozenset):
    parts = [pattern for kind, pattern in _LEADING_PARTS if kind in kinds]
    if not parts:
        return None
    return re.compile(r"\s*(?:" + "|".join(parts) + r")(?![A-Za-z0-9_@])")


_PLACEHOLDER_RE = re.compile("\uE000(\\d+)\uE001")


class CuteTransformation(Transformation):
    """«Милые» эффекты из cutemessages: каомодзи, спарклы, пунктуация, UwU, действия, заикание и т.д.

    Работает по предложениям и словам исходного текста и стоит в конвейере ПЕРЕД маской: префикс и суффикс маски
    не считаются предложениями, а стиль шрифта применяется уже к готовому тексту. Ссылки, @упоминания, #теги,
    команды и код защищены: либо заменены маркерами (_PLACEHOLDER_RE), либо пропускаются по _SKIP_RE.

    36.2.0: сокращения («т.е.», «см.», «Dr. Smith»), инициалы и маркеры списка («1.») не считаются концом предложения;
    после ссылки эффекты ставятся через пробел, чтобы не склеиться с ней.
    """
    _SPLIT_RE = re.compile(r"([.!?…]+(?:[ \t]+|$))")
    _WORD_RE = re.compile(r"\w")
    _TOKEN_RE = re.compile(r"(\s+)")
    _LEAD_RE = re.compile(r"^([^\w\s]+)")
    _TRAIL_RE = re.compile(r"([^\w\s]+)$")
    _TAIL_RE = re.compile(r"([.!?…]*)(\s*)$")
    _SKIP_RE = re.compile("[\uE000\uE001]|" + r"://|(?<!\w)(?:www\.|[@#/$])\w|\w@\w|\w\.\w")
    _DOTTED_ABBR_RE = re.compile(r"(?:\w{1,2}\.)+\w{1,2}")
    _CYRILLIC_RE = re.compile("[\u0400-\u04ff]")
    _JAPANESE_RE = re.compile("[\u3040-\u30ff\u4e00-\u9fff]")
    _KOREAN_RE = re.compile("[\uac00-\ud7af]")
    _LATIN_RE = re.compile("[A-Za-z\u00c0-\u00ff\u0152\u0153\u0178]")
    _FRENCH_RE = re.compile("[\u00e0\u00e2\u00e7\u00e8\u00e9\u00ea\u00eb\u00ee\u00ef\u00f4\u00f9\u00fb\u0153]")

    def __init__(self, settings: "RuntimeSettings"):
        self.options = settings.cute

    @staticmethod
    def _chance(probability: float) -> bool:
        return probability >= 1.0 or random.random() < probability

    @staticmethod
    def _spaced(text: str) -> str:
        if not text or text[0].isspace() or text[0] in ".!?~…,":
            return text
        return " " + text

    def _actions_for(self, text: str) -> Tuple[str, ...]:
        visible = " ".join(token for token in text.split() if not self._SKIP_RE.search(token))
        scores = {
            "ru": len(self._CYRILLIC_RE.findall(visible)),
            "ja": len(self._JAPANESE_RE.findall(visible)),
            "ko": len(self._KOREAN_RE.findall(visible)),
            "latin": len(self._LATIN_RE.findall(visible)),
        }
        best = max(scores, key=scores.get)
        if scores[best] == 0:
            code = self.options.language
        elif best != "latin":
            code = best
        elif self._FRENCH_RE.search(visible):
            code = "fr"
        elif self.options.language == "fr":
            code = self.options.language
        else:
            code = "en"
        return CUTE_ACTIONS.get(code) or CUTE_ACTIONS["en"]

    def _ends_protected(self, core: str) -> bool:
        parts = core.split()
        return bool(parts) and self._SKIP_RE.search(parts[-1]) is not None

    def _false_boundary(self, body: str, delim: str, following: str) -> bool:
        if delim.strip() != ".":
            return False
        words = body.split()
        first = following.lstrip()[:1]
        if not words or not first:
            return False
        tail = words[-1]
        if len(words) == 1 and tail.isdigit() and len(tail) <= 3:
            return True
        if len(tail) == 1 and tail.isalpha() and tail.isupper():
            return first.isupper()
        name = tail.casefold()
        if name in CUTE_TITLE_ABBREVIATIONS:
            return True
        if name in CUTE_ABBREVIATIONS or self._DOTTED_ABBR_RE.fullmatch(tail):
            return first.islower() or first.isdigit()
        return False

    def _stutter(self, word: str) -> str:
        if len(word) > 1 and word[0].isalpha() and "-" not in word:
            first = word[0]
            prefix = first + "-"
            if random.random() < 0.4:
                prefix += first.lower() + "-"
            if first.isupper() and not word.isupper():
                word = first.lower() + word[1:]
            return prefix + word
        return word

    def _stretch(self, word: str) -> str:
        if sum(1 for char in word if char.isalpha()) < 2:
            return word
        vowels = CUTE_VOWELS["ru"] if self._CYRILLIC_RE.search(word) else CUTE_VOWELS["en"]
        limit = self.options.stretch_max
        out: List[str] = []
        for char in word:
            out.append(char)
            if char in vowels and random.random() < 0.6:
                streak = 0
                for previous in reversed(out):
                    if previous != char:
                        break
                    streak += 1
                if streak < limit:
                    out.extend(char * random.randint(1, limit - streak))
        return "".join(out)

    _CYRILLIC_WORD_RE = re.compile("[\u0400-\u04ff]+(?:-[\u0400-\u04ff]+)*")

    @classmethod
    def _soften(cls, word: str) -> str:
        if (len(word) >= 3 and not word.isupper() and cls._CYRILLIC_WORD_RE.fullmatch(word)
                and word[-1].lower() in CUTE_SOFT_SIGN_CONSONANTS):
            return word + "ь"
        return word

    def _word(self, token: str) -> str:
        if self._SKIP_RE.search(token):
            return token
        lead, word, trail = "", token, ""
        found = self._LEAD_RE.match(word)
        if found:
            lead, word = found.group(1), word[len(found.group(1)):]
        found = self._TRAIL_RE.search(word)
        if found:
            trail, word = found.group(1), word[:-len(found.group(1))]
        if not word:
            return token
        if "." in trail and word.casefold() in CUTE_ABBREVIATIONS | CUTE_TITLE_ABBREVIATIONS:
            return token
        opt = self.options
        if opt.lowercase:
            word = word.lower()
        if opt.uwu_speak:
            word = word.translate(CUTE_UWU_TABLE)
        if opt.stretch and self._chance(opt.word_p):
            word = self._stretch(word)
        if opt.soft_sign and self._chance(opt.word_p):
            word = self._soften(word)
        if opt.stutter and self._chance(opt.word_p):
            word = self._stutter(word)
        return lead + word + trail

    def _words(self, core: str) -> str:
        opt = self.options
        if not (opt.lowercase or opt.uwu_speak or opt.stutter or opt.stretch or opt.soft_sign):
            return core
        tokens = self._TOKEN_RE.split(core)
        for index in range(0, len(tokens), 2):
            if tokens[index]:
                tokens[index] = self._word(tokens[index])
        return "".join(tokens)

    def _sentence(self, body: str, delim: str, has_next: bool, actions: Tuple[str, ...]) -> str:
        core = body.strip(" \t")
        if not core or not self._WORD_RE.search(_PLACEHOLDER_RE.sub("", core)):
            return body + delim
        if core.isdigit() and delim.strip() == ".":
            return body + delim
        lead = body[:len(body) - len(body.lstrip(" \t"))]
        trail = body[len(body.rstrip(" \t")):]
        opt = self.options
        probability = opt.sentence_p
        core = self._words(core)
        protected_end = self._ends_protected(core)

        if opt.uwu_suffixes and self._chance(probability):
            suffix = random.choice(CUTE_UWU_SUFFIXES_SPACED if protected_end else CUTE_UWU_SUFFIXES)
            core += suffix if suffix.startswith((" ", "~")) else " " + suffix

        left = right = ""
        if opt.sparkles and self._chance(probability):
            left, right = random.choice(CUTE_SPARKLES), random.choice(CUTE_SPARKLES)

        tail = self._TAIL_RE.match(delim)
        punct, space = (tail.group(1), tail.group(2)) if tail else (delim, "")
        if punct and not protected_end:
            if opt.exclamations and len(punct) <= 3 and set(punct) == {"!"} and self._chance(probability):
                punct = self._spaced(random.choice(CUTE_EXCLAMATIONS))
            elif opt.punctuation and self._chance(probability):
                if "?" in punct and set(punct) <= {"?", "!"}:
                    punct = self._spaced(random.choice(CUTE_QUESTIONS))
                elif punct == ".":
                    punct = self._spaced(random.choice(CUTE_PERIODS))

        result = lead + (left + " " if left else "") + core + trail + punct
        if right:
            result += " " + right
        if opt.kaomoji and self._chance(probability):
            result += " " + random.choice(CUTE_KAOMOJIS)
        action = ""
        if opt.actions and self._chance(probability):
            picked = random.choice(actions)
            if opt.actions_newline:
                action = "\n" + picked + ("\n" if has_next else "")
                space = ""
            else:
                action = " " + picked
        return result + action + space

    def _line(self, line: str, actions: Tuple[str, ...]) -> str:
        parts = self._SPLIT_RE.split(line)
        pairs = [(parts[i], parts[i + 1] if i + 1 < len(parts) else "") for i in range(0, len(parts), 2)]
        out: List[str] = []
        index = 0
        while index < len(pairs):
            body, delim = pairs[index]
            while delim and index + 1 < len(pairs) and self._false_boundary(body, delim, pairs[index + 1][0]):
                index += 1
                body = body + delim + pairs[index][0]
                delim = pairs[index][1]
            has_next = any(item[0].strip() for item in pairs[index + 1:])
            out.append(self._sentence(body, delim, has_next, actions))
            index += 1
        return "".join(out)

    def transform(self, text: str) -> str:
        if not text or not self.options.active:
            return text
        actions = self._actions_for(text)
        return "\n".join(self._line(line, actions) for line in text.split("\n"))


def has_marker_chars(text: str) -> bool:
    return "\uE000" in text or "\uE001" in text or _MD_SENTINEL_RE.search(text) is not None


def protect_special(text: str, kinds: frozenset) -> Tuple[str, List[str]]:
    pattern = _protected_re(kinds)
    if pattern is None or has_marker_chars(text):
        return text, []
    spans: List[str] = []

    def stash(match):
        spans.append(match.group(0))
        return f"\uE000{len(spans) - 1}\uE001"

    return pattern.sub(stash, text), spans


def restore_special(text: str, spans: List[str]) -> str:
    def restore(match):
        index = int(match.group(1))
        return spans[index] if index < len(spans) else match.group(0)

    return _PLACEHOLDER_RE.sub(restore, text)


class TransformationPipeline:
    def __init__(self, settings: RuntimeSettings, logger=None):
        self.filter = TextFilter(settings)
        self.ignore_kinds = settings.ignore_kinds
        self.protect_special = bool(self.ignore_kinds)
        self.logger = logger
        self.transformations: List[Transformation] = []
        self.markdown_table: List[Tuple[str, str]] = []
        self.text_style = settings.text_style
        self.text_style_translit = settings.text_style_translit
        self.style_only = settings.style_only
        self.styling = False
        self._prepared_memo = None
        self._layout_memo = None
        if settings.cute.active:
            self.transformations.append(CuteTransformation(settings))
        if settings.mask_is_active:
            mask = MaskTransformation(settings)
            self.transformations.append(mask)
            self.markdown_table = mask.table
            self.styling = mask.text_style_enabled
        if settings.separator_enabled:
            separator = SeparatorTransformation(settings, self.markdown_table)
            mask_part = self._mask()
            if mask_part is not None:
                mask_part.separator = separator
            else:
                self.transformations.append(separator)

    def _mask(self) -> Optional["MaskTransformation"]:
        for transformation in self.transformations:
            if isinstance(transformation, MaskTransformation):
                return transformation
        return None

    def mask_prefix(self, text: str) -> str:
        mask = self._mask()
        return mask.prefix_for(text) if mask is not None else ""

    def transform(self, text: str) -> str:
        if not self.markdown_table:
            return self._apply(text)
        if _MD_SENTINEL_RE.search(text):
            return text
        return _MD_SENTINEL_RE.sub("", self._apply(text))

    def _style_layout(self, text: str) -> Optional[StyleLayout]:
        if not self.styling:
            return None
        memo = self._layout_memo
        if memo is not None and memo[0] == text:
            return memo[1]
        layout = self._build_style_layout(text)
        self._layout_memo = (text, layout)
        return layout

    def _build_style_layout(self, text: str) -> Optional[StyleLayout]:
        prepared = self._prepare(text)
        if prepared is None:
            return None
        protected, spans = prepared
        atoms = []
        for source, result in _style_atoms(protected, self.text_style, self.text_style_translit, self.style_only):
            marker = _PLACEHOLDER_RE.fullmatch(source)
            if marker is not None and int(marker.group(1)) < len(spans):
                source = result = spans[int(marker.group(1))]
            atoms.append((source, result))
        return StyleLayout(atoms, _output_order(atoms, self.text_style))

    def expected_body(self, text: str) -> str:
        layout = self._style_layout(text)
        return text if layout is None else layout.body

    def entity_mapper(self, text: str):
        layout = self._style_layout(text)
        if layout is None or layout.body == text:
            return None
        return layout.map_range

    def transform_rich(self, text: str):
        if not self.markdown_table or _MD_SENTINEL_RE.search(text):
            return self.transform(text), [], None
        return extract_markdown(self._apply(text), self.markdown_table, self.expected_body(text))

    def _prepare(self, text: str) -> Optional[Tuple[str, List[str]]]:
        memo = self._prepared_memo
        if memo is not None and memo[0] == text:
            return memo[1]
        result = self._prepare_uncached(text)
        self._prepared_memo = (text, result)
        return result

    def _prepare_uncached(self, text: str) -> Optional[Tuple[str, List[str]]]:
        if self.filter.skips(text):
            return None
        if not self.protect_special:
            return text, []
        leading = _leading_special_re(self.ignore_kinds)
        if leading is not None and leading.match(text):
            return None
        if has_marker_chars(text):
            return None
        protected, spans = protect_special(text, self.ignore_kinds)
        if spans and not _PLACEHOLDER_RE.sub("", protected).strip():
            return None
        return protected, spans

    def has_special(self, text: str) -> bool:
        if not self.protect_special:
            return False
        prepared = self._prepare(text)
        return prepared is not None and any(not span.startswith(("#", "$")) for span in prepared[1])

    def ignores(self, text: str) -> bool:
        return self._prepare(text) is None

    def _apply(self, text: str) -> str:
        if not self.transformations:
            return text
        prepared = self._prepare(text)
        if prepared is None:
            return text
        protected, spans = prepared
        for transformation in self.transformations:
            try:
                protected = transformation.transform(protected)
            except Exception as exc:
                if self.logger:
                    self.logger(f"Prefixfy transformation failed: {exc}")
        result = restore_special(protected, spans)
        probe = _MD_SENTINEL_RE.sub("", result) if self.markdown_table else result
        if has_unsafe_text(probe) and not has_unsafe_text(text):
            if self.logger:
                self.logger("Prefixfy: decoration would produce unsafe text, message left as is")
            return text
        return result


_MD_BASE = 0xE100
_MD_MAX_ENTITIES = 64
_MD_TEXT_SLOT = "\uE0FF"
_MD_BODY_START = "\uE0FE"
_MD_BODY_END = "\uE0FD"
_MD_SENTINEL_RE = re.compile("[\uE0FD-\uE0FF\uE100-\uE17F]")
_MD_INVISIBLE_RE = re.compile("[\uE0FD-\uE0FF\uE100-\uE17F]+")
_MD_KINDS = {"**": "Bold", "__": "Italic", "~~": "Strike", "||": "Spoiler", "^^": "Blockquote"}
_MD_ESCAPABLE = ("**", "__", "~~", "||", "^^")
_MD_LANG_RE = re.compile(r"([A-Za-z0-9_+#.\-]{1,32})[ \t]*\n")
_MD_PRE_CLOSE_RE = re.compile(r"(?<!`)```(?!`)")


class _MdMarker:
    __slots__ = ("text", "kind", "role", "partner", "entity_id", "pos")

    def __init__(self, text: str):
        self.text = text
        self.kind = _MD_KINDS[text]
        self.role = None
        self.partner = None
        self.entity_id = None
        self.pos = -1


class _MdCode:
    __slots__ = ("kind", "language", "content", "raw")

    def __init__(self, kind: str, language: str, content: str, raw: str):
        self.kind = kind
        self.language = language
        self.content = content
        self.raw = raw


def _md_has_content(pieces, opener: _MdMarker) -> bool:
    for piece in pieces[opener.pos + 1:]:
        if isinstance(piece, _MdCode) or (isinstance(piece, str) and piece.strip()):
            return True
    return False


def _md_code_span(src: str, i: int, j: int):
    run = j - i
    n = len(src)
    if run == 1:
        k = j
        while True:
            k = src.find("`", k)
            if k < 0:
                return None
            e = k
            while e < n and src[e] == "`":
                e += 1
            if e - k == 1:
                break
            k = e
        content = src[j:k]
        if not content.strip() or "\n" in content:
            return None
        return _MdCode("Code", "", content, src[i:k + 1]), k + 1
    if run == 3:
        match = _MD_PRE_CLOSE_RE.search(src, j)
        if match is None:
            return None
        body = src[j:match.start()]
        language = ""
        lang_match = _MD_LANG_RE.match(body)
        if lang_match and body[lang_match.end():].strip():
            language = lang_match.group(1)
            body = body[lang_match.end():]
        elif body.startswith("\n"):
            body = body[1:]
        if body.endswith("\n"):
            body = body[:-1]
        if not body.strip():
            return None
        return _MdCode("Pre", language, body, src[i:match.end()]), match.end()
    return None


def _md_parse(src: str):
    pieces: list = []
    stack: List[_MdMarker] = []
    buf: List[str] = []
    n = len(src)
    i = 0

    def flush():
        if buf:
            pieces.append("".join(buf))
            buf.clear()

    while i < n:
        ch = src[i]
        if ch == "\\":
            if src.startswith(_MD_ESCAPABLE, i + 1):
                buf.append(src[i + 1:i + 3])
                i += 3
            elif src.startswith("`", i + 1):
                buf.append("`")
                i += 2
            else:
                buf.append(ch)
                i += 1
            continue
        if ch in "*_~|^":
            j = i
            while j < n and src[j] == ch:
                j += 1
            if j - i != 2 or not md_kind_enabled(_MD_KINDS.get(ch * 2)):
                buf.append(src[i:j])
                i = j
                continue
            marker = _MdMarker(ch * 2)
            can_open = can_close = True
            if ch == "_":
                can_open = not (i > 0 and src[i - 1].isalnum())
                can_close = not (j < n and src[j].isalnum())
            flush()
            opener_index = -1
            if can_close:
                for k in range(len(stack) - 1, -1, -1):
                    if stack[k].text == marker.text:
                        opener_index = k
                        break
            if opener_index >= 0:
                opener = stack.pop(opener_index)
                if _md_has_content(pieces, opener):
                    marker.role = "close"
                    marker.partner = opener
                    opener.partner = marker
                    pieces.append(marker)
                    i = j
                    continue
            if can_open:
                marker.role = "open"
                marker.pos = len(pieces)
                stack.append(marker)
            pieces.append(marker)
            i = j
            continue
        if ch == "`":
            j = i
            while j < n and src[j] == "`":
                j += 1
            span = _md_code_span(src, i, j)
            if span is None or not md_kind_enabled(span[0].kind):
                buf.append(src[i:j])
                i = j
            else:
                flush()
                pieces.append(span[0])
                i = span[1]
            continue
        buf.append(ch)
        i += 1
    flush()

    table: List[Tuple[str, str]] = []
    out: List[str] = []
    for piece in pieces:
        if isinstance(piece, str):
            out.append(piece)
        elif isinstance(piece, _MdCode):
            if len(table) < _MD_MAX_ENTITIES:
                entity_id = len(table)
                table.append((piece.kind, piece.language))
                out.append(chr(_MD_BASE + 2 * entity_id) + piece.content + chr(_MD_BASE + 2 * entity_id + 1))
            else:
                out.append(piece.raw)
        elif piece.role == "open" and piece.partner is not None:
            if len(table) < _MD_MAX_ENTITIES:
                piece.entity_id = len(table)
                table.append((piece.kind, ""))
                out.append(chr(_MD_BASE + 2 * piece.entity_id))
            else:
                out.append(piece.text)
        elif piece.role == "close" and piece.partner is not None and piece.partner.entity_id is not None:
            out.append(chr(_MD_BASE + 2 * piece.partner.entity_id + 1))
        else:
            out.append(piece.text)
    return "".join(out), table


_CUSTOM_EMOJI_SCAN_RE = re.compile(r"\((\d{1,19})\|([^()\r\n]{1,32})\)|[\uE100-\uE17F]")
_MD_CODE_KINDS = ("Code", "Pre")
_MAX_DOCUMENT_ID = 2 ** 63 - 1


def normalize_emoji_fallback(text: str) -> Optional[str]:
    text = text.strip()
    regex = _emoji_token_regex()
    if regex.fullmatch(text):
        return text
    found = regex.search(text)
    return found.group(0) if found else None


def parse_custom_emoji_marker(document_id: str, fallback: str) -> Optional[Tuple[int, str]]:
    try:
        number = int(document_id)
    except (TypeError, ValueError):
        return None
    if not 0 < number <= _MAX_DOCUMENT_ID:
        return None
    emoji = normalize_emoji_fallback(fallback)
    return (number, emoji) if emoji else None


def inject_custom_emoji(text: str, table: List[Tuple[str, str]]) -> str:
    if "|" not in text:
        return text
    slots = {int(language): index for index, (kind, language) in enumerate(table) if kind == "CustomEmoji"}
    out: List[str] = []
    position = 0
    in_code = False
    for match in _CUSTOM_EMOJI_SCAN_RE.finditer(text):
        out.append(text[position:match.start()])
        position = match.end()
        token = match.group(0)
        if match.group(1) is None:
            out.append(token)
            entity_id, closing = divmod(ord(token) - _MD_BASE, 2)
            if entity_id < len(table) and table[entity_id][0] in _MD_CODE_KINDS:
                in_code = not closing
            continue
        parsed = None if in_code else parse_custom_emoji_marker(match.group(1), match.group(2))
        if parsed is None:
            out.append(token)
            continue
        document_id, emoji = parsed
        entity_id = slots.get(document_id)
        if entity_id is None and len(table) < _MD_MAX_ENTITIES:
            entity_id = len(table)
            table.append(("CustomEmoji", str(document_id)))
            slots[document_id] = entity_id
        if entity_id is None:
            out.append(emoji)
        else:
            out.append(chr(_MD_BASE + 2 * entity_id) + emoji + chr(_MD_BASE + 2 * entity_id + 1))
    out.append(text[position:])
    return "".join(out)


def compile_mask_markdown(mask: str, parse_markdown: bool = True):
    mask = _MD_SENTINEL_RE.sub("", mask) if isinstance(mask, str) else mask
    tokens = mask_tokens(mask)
    if len(tokens) != 1:
        return None
    link = normalize_link(tokens[0].group(1))
    source = mask[:tokens[0].start()] + _MD_TEXT_SLOT + mask[tokens[0].end():]
    if parse_markdown:
        compiled, table = _md_parse(source)
    else:
        compiled, table = source, []
    compiled = inject_custom_emoji(compiled, table)
    if compiled.count(_MD_TEXT_SLOT) != 1:
        return None
    left, right = compiled.split(_MD_TEXT_SLOT, 1)
    link_id = None
    if link and len(table) < _MD_MAX_ENTITIES:
        link_id = len(table)
        table.append(("TextUrl", link))
    return left, right, table, link_id


def extract_markdown(text: str, table: List[Tuple[str, str]], original: str):
    chars: List[str] = []
    opened: Dict[int, Tuple[int, int]] = {}
    entities = []
    offset = 0
    body_start = body_end = None
    limit = _MD_BASE + 2 * len(table)
    for ch in text:
        code = ord(ch)
        if ch == _MD_BODY_START:
            body_start = (len(chars), offset)
        elif ch == _MD_BODY_END:
            body_end = len(chars)
        elif _MD_BASE <= code < limit:
            entity_id, closing = divmod(code - _MD_BASE, 2)
            if not closing:
                opened[entity_id] = (len(chars), offset)
            else:
                begin = opened.pop(entity_id, None)
                if begin is not None and offset > begin[1] and "".join(chars[begin[0]:]).strip():
                    kind, language = table[entity_id]
                    entities.append((kind, begin[1], offset - begin[1], language))
        elif _MD_SENTINEL_RE.match(ch):
            continue
        else:
            chars.append(ch)
            offset += 2 if code > 0xFFFF else 1
    plain = "".join(chars)
    body_offset = None
    if body_start is not None and body_end is not None and plain[body_start[0]:body_end] == original:
        body_offset = body_start[1]
    entities.sort(key=lambda item: (item[1], -item[2]))
    return plain, entities, body_offset


_SDK_ENTITY_TYPES = {
    "Bold": "BOLD", "Italic": "ITALIC", "Strike": "STRIKETHROUGH",
    "Spoiler": "SPOILER", "Code": "CODE", "Pre": "PRE", "Blockquote": "BLOCKQUOTE",
}


def _sdk_tg_entity(kind: str, offset: int, length: int, language: str):
    errors = []
    for module_name in ("markdown_utils", "extera_utils.markdown_utils", "extera_utils.text_formatting"):
        try:
            module = __import__(module_name, fromlist=["RawEntity", "TLEntityType"])
            entity_type = getattr(module.TLEntityType, _SDK_ENTITY_TYPES[kind])
            options = {"language": language} if kind == "Pre" and language else {}
            raw = module.RawEntity(type=entity_type, offset=offset, length=length, **options)
            entity = raw.to_tlrpc_object()
            if int(entity.offset) == offset and int(entity.length) == length:
                return entity
            errors.append(f"{module_name}: wrong bounds")
        except Exception as exc:
            errors.append(f"{module_name}: {exc}")
    raise RuntimeError("; ".join(errors))


def _new_tg_entity(kind: str):
    name = "org.telegram.tgnet.TLRPC$TL_messageEntity" + kind
    errors = []
    try:
        from java import jclass
        return jclass(name)()
    except Exception as exc:
        errors.append(f"jclass: {exc}")
    try:
        from org.telegram.tgnet import TLRPC
        return getattr(TLRPC, "TL_messageEntity" + kind)()
    except Exception as exc:
        errors.append(f"TLRPC: {exc}")
    raise RuntimeError(f"Telegram entity {kind} unavailable ({'; '.join(errors)})")


def _diff_opcodes(original: str, final_text: str):
    if len(original) * len(final_text) > 40_000_000:
        return None
    return difflib.SequenceMatcher(None, original, final_text, autojunk=False).get_opcodes()


def _diff_map(opcodes, index: int, at_end: bool) -> Optional[int]:
    probe = index - 1 if at_end else index
    for tag, i1, i2, j1, j2 in opcodes:
        if i1 <= probe < i2:
            if tag == "equal":
                return j1 + (probe - i1) + (1 if at_end else 0)
            return j2 if at_end else j1
    return None


def _realign_entities(kept, original: str, final_text: str, start: int):
    result = []
    cursor = _utf16_index(final_text, start) if start else 0
    opcodes = None
    for entity in sorted(kept, key=lambda item: int(item.offset)):
        try:
            offset, length = int(entity.offset), int(entity.length)
            first, last = _utf16_index(original, offset), _utf16_index(original, offset + length)
            piece = original[first:last]
            if not piece:
                continue
            found = final_text.find(piece, cursor)
            if found >= 0:
                entity.offset = utf16_length(final_text[:found])
                cursor = found + len(piece)
                result.append(entity)
                continue
            if opcodes is None:
                opcodes = _diff_opcodes(original, final_text) or ()
            begin, finish = _diff_map(opcodes, first, False), _diff_map(opcodes, last, True)
            if begin is None or finish is None or finish <= begin or finish - begin > len(piece) * 3 + 16:
                continue
            if not (last < len(original) and original[last].isalnum()):
                while finish < len(final_text) and final_text[finish].isalpha():
                    finish += 1
            if begin < cursor:
                begin = cursor
                if finish <= begin:
                    continue
            entity.offset = utf16_length(final_text[:begin])
            entity.length = utf16_length(final_text[begin:finish])
            cursor = finish
            result.append(entity)
        except Exception:
            continue
    return result


def _make_tg_entities(descriptions, existing=None, body_offset=None, remap=None, realign=None):
    created = []
    for kind, offset, length, language in descriptions:
        if kind == "CustomEmoji":
            try:
                entity = _new_tg_entity(kind)
                entity.offset = offset
                entity.length = length
                entity.document_id = int(language)
                if int(entity.document_id) != int(language):
                    raise RuntimeError(f"custom emoji id was not stored: {entity.document_id} != {language}")
            except Exception:
                continue
        elif kind == "TextUrl":
            entity = _new_tg_entity(kind)
            entity.offset = offset
            entity.length = length
            entity.url = language
            if str(entity.url) != language:
                raise RuntimeError("entity url was not stored")
        else:
            try:
                entity = _sdk_tg_entity(kind, offset, length, language)
            except Exception:
                entity = _new_tg_entity(kind)
                entity.offset = offset
                entity.length = length
        if int(entity.offset) != offset or int(entity.length) != length:
            raise RuntimeError(f"entity bounds were not stored: {entity.offset}/{entity.length} != {offset}/{length}")
        if kind == "Pre" and not getattr(entity, "language", None):
            entity.language = language or ""
        created.append(entity)
    kept = []
    if existing is not None and body_offset is not None:
        try:
            kept = list(existing)
        except Exception:
            kept = _iter_entities(existing)
        for entity in kept:
            offset, length = int(entity.offset), int(entity.length)
            if remap is not None:
                offset, length = remap(offset, length)
                entity.length = length
            entity.offset = offset + body_offset
    elif existing is not None and realign is not None:
        try:
            try:
                source = list(existing)
            except Exception:
                source = _iter_entities(existing)
            kept = _realign_entities(source, *realign)
        except Exception:
            kept = []
    combined = sorted(kept + created, key=lambda entity: (int(entity.offset), -int(entity.length)))
    if existing is not None:
        try:
            existing.clear()
            for entity in combined:
                existing.add(entity)
            return existing
        except Exception:
            pass
    try:
        from java.util import ArrayList
        java_entities = ArrayList()
        for entity in combined:
            java_entities.add(entity)
        return java_entities
    except Exception:
        return combined


TAG_GAP = "\uE0F0"


class _TagSideMatcher:
    __slots__ = ("parts", "at_end")

    def __init__(self, parts: Tuple[str, ...], at_end: bool):
        self.parts = parts
        self.at_end = at_end

    def __call__(self, text: str) -> bool:
        parts, gap = self.parts, TAG_VALUE_LIMIT
        if not self.at_end:
            if not text.startswith(parts[0]):
                return False
            positions = {len(parts[0])}
            for part in parts[1:]:
                found = set()
                for position in positions:
                    for begin in range(position, min(len(text), position + gap) + 1):
                        if text.startswith(part, begin):
                            found.add(begin + len(part))
                positions = found
                if not positions:
                    return False
            return True
        if not text.endswith(parts[-1]):
            return False
        positions = {len(text) - len(parts[-1])}
        for part in reversed(parts[:-1]):
            found = set()
            for position in positions:
                for end in range(position, position - gap - 1, -1):
                    begin = end - len(part)
                    if begin >= 0 and text.startswith(part, begin):
                        found.add(begin)
            positions = found
            if not positions:
                return False
        return True


@lru_cache(maxsize=128)
def mask_side_matcher(side: str, at_end: bool):
    parts = side.split(TAG_GAP)
    if not "".join(parts).strip():
        return None
    return _TagSideMatcher(tuple(parts), at_end)


def utf16_length(text: str) -> int:
    if text.isascii():
        return len(text)
    return len(text.encode("utf-16-le", "surrogatepass")) // 2


def body_offset_in(original: str, transformed: str, prefix: str = "") -> Optional[int]:
    if prefix and transformed.startswith(prefix) and transformed[len(prefix):].startswith(original):
        return utf16_length(prefix)
    if transformed.startswith(original):
        return 0
    index = transformed.find(original)
    return None if index < 0 else utf16_length(transformed[:index])


def _utf16_index(text: str, offset: int) -> int:
    units = 0
    for index, char in enumerate(text):
        if units >= offset:
            return index
        units += 2 if ord(char) > 0xFFFF else 1
    return len(text)


def _iter_entities(entities) -> list:
    if entities is None:
        return []
    try:
        return list(entities)
    except Exception:
        pass
    try:
        return [entities.get(index) for index in range(int(entities.size()))]
    except Exception:
        return []


def _entity_name(entity) -> str:
    try:
        return str(entity.getClass().getSimpleName())
    except Exception:
        return type(entity).__name__


def _entity_document_id(entity) -> int:
    for attr in ("document_id", "documentId"):
        try:
            value = int(getattr(entity, attr))
        except Exception:
            continue
        if value > 0:
            return value
    return 0


def _is_custom_emoji_entity(entity) -> bool:
    return "CustomEmoji" in _entity_name(entity) or _entity_document_id(entity) > 0


def entity_sources(params) -> List[Tuple[str, list]]:
    names = ["entities"]
    try:
        names += [name for name in dir(params) if "entit" in name.lower() and not name.startswith("_") and name not in names]
    except Exception:
        pass
    sources = []
    for name in names:
        try:
            value = getattr(params, name)
        except Exception:
            continue
        if value is None or callable(value):
            continue
        sources.append((name, _iter_entities(value)))
    return sources


def custom_emoji_spans(side: str, table: List[Tuple[str, str]], base: int) -> List[Tuple[str, int, int, str]]:
    """Позиции (UTF-16) Premium Emoji в одной стороне скомпилированной маски."""
    spans: List[Tuple[str, int, int, str]] = []
    opened: Dict[int, int] = {}
    offset = base
    limit = _MD_BASE + 2 * len(table)
    for ch in side:
        code = ord(ch)
        if _MD_BASE <= code < limit:
            entity_id, closing = divmod(code - _MD_BASE, 2)
            if table[entity_id][0] != "CustomEmoji":
                continue
            if not closing:
                opened[entity_id] = offset
            else:
                begin = opened.pop(entity_id, None)
                if begin is not None and offset > begin:
                    spans.append(("CustomEmoji", begin, offset - begin, table[entity_id][1]))
        elif _MD_SENTINEL_RE.match(ch):
            continue
        else:
            offset += 2 if code > 0xFFFF else 1
    return spans


def _format_emoji_markers(found) -> List[str]:
    markers, seen = [], set()
    for _, document_id, emoji in sorted(found, key=lambda item: item[0]):
        if document_id not in seen:
            seen.add(document_id)
            markers.append(f"({document_id}|{emoji})")
        if len(markers) >= MAX_CAPTURED_EMOJI:
            break
    return markers


def custom_emoji_markers(message, entities) -> List[str]:
    if not isinstance(message, str) or not message:
        return []
    found = []
    for entity in _iter_entities(entities):
        if not _is_custom_emoji_entity(entity):
            continue
        document_id = _entity_document_id(entity)
        try:
            offset = int(getattr(entity, "offset"))
            length = int(getattr(entity, "length"))
        except Exception:
            continue
        if not 0 < document_id <= _MAX_DOCUMENT_ID or offset < 0 or length <= 0:
            continue
        start = _utf16_index(message, offset)
        end = _utf16_index(message, offset + length)
        emoji = normalize_emoji_fallback(message[start:end]) or DEFAULT_EMOJI_FALLBACK
        found.append((offset, document_id, emoji))
    return _format_emoji_markers(found)


def _input_field_text(fragment):
    view = None
    try:
        view = fragment.getChatActivityEnterView()
    except Exception:
        view = getattr(fragment, "chatActivityEnterView", None)
    if view is None:
        return None
    editor = None
    try:
        editor = view.getEditField()
    except Exception:
        editor = getattr(view, "messageEditText", None)
    if editor is None:
        return None
    return editor.getText()


def custom_emoji_markers_from_input() -> List[str]:
    try:
        fragment = get_last_fragment()
        text = _input_field_text(fragment) if fragment is not None else None
        if text is None:
            return []
        span_class = find_class("org.telegram.ui.Components.AnimatedEmojiSpan")
        if span_class is None:
            return []
        plain = str(text.toString())
        found = []
        for span in list(text.getSpans(0, int(text.length()), span_class)):
            document_id = 0
            for attr in ("documentId", "getDocumentId"):
                try:
                    value = getattr(span, attr)
                    value = int(value() if callable(value) else value)
                except Exception:
                    continue
                if value > 0:
                    document_id = value
                    break
            if not 0 < document_id <= _MAX_DOCUMENT_ID:
                continue
            start = int(text.getSpanStart(span))
            end = int(text.getSpanEnd(span))
            if start < 0 or end <= start:
                continue
            emoji = normalize_emoji_fallback(plain[_utf16_index(plain, start):_utf16_index(plain, end)]) or DEFAULT_EMOJI_FALLBACK
            found.append((start, document_id, emoji))
        return _format_emoji_markers(found)
    except Exception:
        return []


def limit_custom_emoji(descriptions, reserved: int = 0, limit: int = MAX_MESSAGE_ENTITIES):
    free = max(0, limit - reserved - sum(1 for item in descriptions if item[0] != "CustomEmoji"))
    result, used = [], 0
    for item in descriptions:
        if item[0] == "CustomEmoji":
            if used >= free:
                continue
            used += 1
        result.append(item)
    return result


class Runtime:
    MAX_MESSAGE_RUNTIMES = 256

    def __init__(self, settings: RuntimeSettings, config_id: str, logger=None):
        self.settings = settings
        self.config_id = config_id
        self.logger = logger
        self.pipeline = TransformationPipeline(settings, logger)
        self._message_runtimes: "OrderedDict[Tuple[str, int], Runtime]" = OrderedDict()
        self._message_lock = threading.Lock()
        self._caption_runtime: Optional["Runtime"] = None

    def for_caption(self) -> "Runtime":
        """42.1.0: игнор сообщений только из эмодзи действует в обычных сообщениях, но не в подписях к медиа.
        Для подписи берётся такой же рантайм с выключенным «только эмодзи»; он строится один раз и переиспользуется."""
        if not self.settings.ignore_emoji_only:
            return self
        with self._message_lock:
            found = self._caption_runtime
        if found is not None:
            return found
        raw = dict(self.settings.raw)
        raw["ignore_emoji_only"] = False
        built = Runtime(RuntimeSettings(raw), self.config_id, self.logger)
        with self._message_lock:
            if self._caption_runtime is None:
                self._caption_runtime = built
            return self._caption_runtime

    def derived(self, mask: str, style: int, cache: bool = True) -> "Runtime":
        key = (mask, style)
        if cache:
            with self._message_lock:
                found = self._message_runtimes.get(key)
                if found is not None:
                    self._message_runtimes.move_to_end(key)
                    return found
        raw = dict(self.settings.raw)
        raw["mask"] = mask
        raw["text_style"] = style
        built = Runtime(RuntimeSettings(raw), self.config_id, self.logger)
        if not cache:
            return built
        with self._message_lock:
            self._message_runtimes[key] = built
            while len(self._message_runtimes) > self.MAX_MESSAGE_RUNTIMES:
                self._message_runtimes.popitem(last=False)
        return built

    def attached_media(self) -> Optional[Tuple[str, str, str]]:
        s = self.settings
        if not s.media_enabled or not s.media_path or not is_media_store_file(s.media_path) or not os.path.isfile(s.media_path):
            return None
        name = s.media_name or os.path.basename(s.media_path)
        return s.media_path, name, s.media_mime or mimetypes.guess_type(name)[0] or ""


class RuntimeManager:
    def __init__(self, plugin):
        self.plugin = plugin
        self.runtime: Optional[Runtime] = None
        self._suspend = 0
        self._lock = threading.RLock()

    def rebuild(self):
        with self._lock:
            try:
                configurations = getattr(self.plugin, "configurations", None)
                config_id = configurations.live_config_id() if configurations is not None else "default"
                self.runtime = Runtime(self.plugin.settings.snapshot(), config_id, self.plugin.log)
            except Exception as exc:
                import traceback
                self.plugin.log(f"Prefixfy runtime rebuild failed: {exc}\n{traceback.format_exc()}")

    def on_setting_changed(self):
        with self._lock:
            suspended = self._suspend > 0
        if not suspended:
            self.rebuild()

    @contextmanager
    def bulk(self):
        with self._lock:
            self._suspend += 1
        try:
            with self.plugin.settings.batch():
                yield
        finally:
            with self._lock:
                self._suspend = max(0, self._suspend - 1)
                idle = self._suspend == 0
            if idle:
                self.rebuild()


class ConfigurationError(ValueError):
    pass


class ConfigurationSaveError(RuntimeError):
    pass


SCHEMA_KEY = "Prefixfy_schema"
SCHEMA_VERSION = 50

LEGACY_LANGUAGE_LAYOUTS = {
    1: (None, "ru", "en", "ja", "ko", "ar", "fr", "pl", "de", "uk"),
    2: LANGUAGE_MODES + ("de",),
}
LEGACY_LANGUAGE_LAYOUT_KEY = "Prefixfy_language_layout"
LEGACY_LANGUAGE_LIVE_KEY = "Prefixfy_language_live_layout"
LEGACY_LANGUAGE_MARKS_KEY = "Prefixfy_language_migrated"
LEGACY_IGNORE_SPLIT_KEY = "Prefixfy_ignore_split"
LEGACY_IGNORE_KEY = "ignore_special"
LEGACY_CONFIG_FORMATS = ("maskify-config",)
LEGACY_CONFIG_LAYOUT_VERSION = 15
LEGACY_FLAT_CONFIGS_KEY = "Prefixfy_experimental_configurations"
LEGACY_FLAT_ACTIVE_KEY = "Prefixfy_experimental_active_configuration"
LEGACY_FLAT_MAX_RECORDS = 200
LEGACY_FLAGS_CACHE_FILE = "Prefixfy_flags.json"
LEGACY_PREV_FILE = ".pfx_prev"
LEGACY_SETTING_KEYS = (LEGACY_FLAT_CONFIGS_KEY, LEGACY_FLAT_ACTIVE_KEY)


def legacy_language_index(value, layout: int) -> int:
    """Индекс языка из раскладки layout (1 или 2) в текущую. Немецкий становится английским, исчезнувшие языки —
    автоопределением (0). Не целое и отрицательное возвращается как есть: такое отвергает проверка конфигурации."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return value
    table = LEGACY_LANGUAGE_LAYOUTS.get(layout)
    if table is None or value >= len(table):
        return 0
    code = table[value]
    if code == "de":
        code = "en"
    return LANGUAGE_MODES.index(code) if code in LANGUAGE_MODES else 0


def legacy_fill_ignore_keys(source):
    """45.6.0: «ignore_special» разбит на шесть тумблеров. В старых наборах новых ключей нет, и они наследуют старое
    значение; сам «ignore_special» убирается. Набор без него возвращается тем же объектом."""
    if not isinstance(source, dict) or LEGACY_IGNORE_KEY not in source:
        return source
    result = dict(source)
    legacy = result.pop(LEGACY_IGNORE_KEY)
    if isinstance(legacy, bool):
        for key in IGNORE_KEYS:
            result.setdefault(key, legacy)
    return result


def legacy_upgrade_section(data: dict, component: str, section):
    """Раздел импортируемого файла приводится к текущей схеме. Языка в файлах версии ниже 15 — раскладка 1, в остальных —
    раскладка 2 (там «de» = 6)."""
    if component == "language" and isinstance(section, dict):
        value = section.get("value")
        version = data.get("version")
        old_file = not isinstance(version, int) or isinstance(version, bool) or version < LEGACY_CONFIG_LAYOUT_VERSION
        if isinstance(value, int) and not isinstance(value, bool) and (old_file or value >= len(LANGUAGE_MODES)):
            section = {**section, "value": legacy_language_index(value, 1 if old_file else 2)}
    elif component == "exceptions":
        section = legacy_fill_ignore_keys(section)
    return section


class LegacyMigration:
    """Единый мигратор данных версий ниже 50. Создаётся один раз на запуск; если данные уже новые, все методы ничего не делают."""

    def __init__(self, plugin):
        self.plugin = plugin
        self.schema = clamp_int(self._get(SCHEMA_KEY, 0), 0, 0, 1_000_000)
        self.pending = self.schema < SCHEMA_VERSION
        self.layout_pending = clamp_int(self._get(LEGACY_LANGUAGE_LAYOUT_KEY, 1), 1, 1, 2) < 2
        self.ok = True
        self.flat_imported = False

    @staticmethod
    def preexisting_install(plugin) -> bool:
        """Плагин уже стоял до этого запуска (для мастера первой настройки): у любой установки есть версия схемы или раскладка языка."""
        try:
            return plugin.get_setting(SCHEMA_KEY, None) is not None or plugin.get_setting(LEGACY_LANGUAGE_LAYOUT_KEY, None) is not None
        except Exception:
            return False

    def _get(self, key, default=None):
        try:
            return self.plugin.get_setting(key, default)
        except Exception:
            return default

    def _set(self, key, value):
        self.plugin.set_setting(key, value, reload_settings=False)

    def _fail(self, step: str, exc):
        self.ok = False
        self.plugin.log(f"Prefixfy migration step '{step}' failed, it will be retried at the next start: {exc}")

    def _marks(self) -> set:
        try:
            data = json.loads(as_text(self._get(LEGACY_LANGUAGE_MARKS_KEY, "")) or "[]")
        except (ValueError, TypeError):
            return set()
        return {item for item in data if isinstance(item, str)} if isinstance(data, list) else set()

    def _save_marks(self, marks: set):
        try:
            self._set(LEGACY_LANGUAGE_MARKS_KEY, json.dumps(sorted(marks)))
        except Exception as exc:
            self.plugin.log(f"Prefixfy language migration marker failed: {exc}")

    def migrate_settings(self):
        if not self.pending:
            return
        try:
            live_done = clamp_int(self._get(LEGACY_LANGUAGE_LIVE_KEY, 1), 1, 1, 2) >= 2
            if self.layout_pending and not live_done:
                self._set("language", legacy_language_index(self._get("language", 0), 1))
                self._set(LEGACY_LANGUAGE_LIVE_KEY, 2)
            language = self._get("language", 0)
            if isinstance(language, int) and not isinstance(language, bool) and language >= len(LANGUAGE_MODES):
                self._set("language", legacy_language_index(language, 2))
            if not self._get(LEGACY_IGNORE_SPLIT_KEY, 0):
                if self._get(LEGACY_IGNORE_KEY, None) is False:
                    for key in IGNORE_KEYS:
                        self._set(key, False)
                self._set(LEGACY_IGNORE_SPLIT_KEY, 1)
        except Exception as exc:
            self._fail("settings", exc)

    def migrate_files(self):
        if not self.pending:
            return
        base = get_plugins_dir()
        old_flags, new_flags = os.path.join(base, LEGACY_FLAGS_CACHE_FILE), os.path.join(base, FLAGS_CACHE_FILE)
        try:
            if os.path.exists(old_flags):
                if os.path.exists(new_flags):
                    os.remove(old_flags)
                else:
                    os.replace(old_flags, new_flags)
        except OSError as exc:
            self.plugin.log(f"Prefixfy migration: flags cache not moved: {exc}")
        try:
            os.remove(os.path.join(base, LEGACY_PREV_FILE))
        except FileNotFoundError:
            pass
        except OSError as exc:
            self.plugin.log(f"Prefixfy migration: {LEGACY_PREV_FILE} not removed: {exc}")

    def import_flat_configurations(self, manager):
        if not self.pending or manager.configurations:
            return
        raw = self._get(LEGACY_FLAT_CONFIGS_KEY, "")
        if not (isinstance(raw, str) and raw) or len(raw) > 8 * 1024 * 1024:
            return
        try:
            data = json.loads(raw)
        except Exception as exc:
            self.plugin.log(f"Configurations legacy load failed: {exc}")
            manager._degraded = True
            return
        if not isinstance(data, dict):
            return
        legacy_active = as_text(self._get(LEGACY_FLAT_ACTIVE_KEY, ""))
        all_stored = True
        for old_id, record in list(data.items())[:LEGACY_FLAT_MAX_RECORDS]:
            if not isinstance(record, dict):
                continue
            if "current" not in record or "baseline" not in record:
                flat = dict(record)
                name = flat.pop("name", old_id)
                record = {"name": name, "current": dict(flat), "baseline": dict(flat)}
            config_id = (str(old_id) if manager._valid_id(str(old_id)) and manager._owner_of(str(old_id)) is None
                         and str(old_id) not in manager.configurations else manager._new_id())
            current, baseline = record.get("current"), record.get("baseline")
            stored = manager._store_record(config_id, {
                "name": as_text(record.get("name", old_id)),
                "current": legacy_fill_ignore_keys(current) if isinstance(current, dict) else {},
                "baseline": legacy_fill_ignore_keys(baseline) if isinstance(baseline, dict) else {},
            })
            all_stored = all_stored and stored
            if str(old_id) == legacy_active:
                manager.active_id = config_id
        self.flat_imported = bool(manager.configurations) and all_stored
        if not all_stored:
            self.ok = False

    def convert_account_files(self, manager):
        if not self.pending:
            return
        accounts = manager.accounts
        try:
            entries = sorted(os.listdir(accounts.directory))
        except OSError as exc:
            self._fail("account profiles", exc)
            return
        files: Dict[int, str] = {}
        for entry in entries:
            path = os.path.join(accounts.directory, entry)
            match = _ACCT_FILE_RE.fullmatch(entry)
            uid = accounts._canonical_uid(match.group(1)) if match and not os.path.isdir(path) else None
            if uid is not None:
                files[uid] = path
        for uid, path in files.items():
            if uid in accounts._presets:
                discard_file(path)
                continue
            if len(accounts._presets) >= MAX_ACCOUNT_PROFILES:
                accounts.degraded = True
                continue
            try:
                payload = json.loads(store_read_text(path))
                params = payload.get("params") if isinstance(payload, dict) else None
                if not isinstance(params, dict):
                    raise ValueError("no params object")
            except Exception as exc:
                accounts.degraded = True
                manager.plugin.log(f"Prefixfy accounts: cannot read {os.path.basename(path)}: {exc}")
                continue
            try:
                if not self._profile_to_preset(manager, uid, accounts._clean(legacy_fill_ignore_keys(params))):
                    raise ValueError("conversion to a preset failed")
            except Exception as exc:
                accounts.degraded = True
                self._fail("account profile", exc)
                continue
            discard_file(path)

    def _profile_to_preset(self, manager, uid: int, params: dict) -> bool:
        config_id = manager._new_id(uid)
        base_id = manager.active_id if manager.active_id in manager.configurations else next(iter(manager.configurations), "")
        record = {
            "name": manager.plugin._tr("config_default_name"),
            "current": manager._clone_with_media(params, config_id, "current"),
            "baseline": manager._clone_with_media(manager._shared_baseline(), config_id, "baseline"),
        }
        if not manager._store_record(config_id, record):
            manager._discard_record(config_id)
            return False
        manager.accounts.set_active(uid, config_id)
        manager._write_index(uid)
        if self.layout_pending:
            marks = self._marks()
            if f"acc:{uid}" in marks:
                marks.add(f"{config_id}:current")
            if base_id and f"{base_id}:baseline" in marks:
                marks.add(f"{config_id}:baseline")
            self._save_marks(marks)
        return True

    def migrate_languages(self, manager):
        """Раскладка 1 -> текущая переводит каждый набор ровно один раз (метка пишется сразу после записи, поэтому сбой
        посередине не приводит к повторному пересчёту: индексы не идемпотентны). Раскладка 2 -> текущая («de» -> английский)
        безопасна для повторов."""
        if not self.pending:
            return
        records = manager._all_records()
        if self.layout_pending:
            marks = self._marks()
            for config_id, record in records:
                for role in ("current", "baseline"):
                    params = record.get(role) or {}
                    mark = f"{config_id}:{role}"
                    if mark in marks or "language" not in params:
                        continue
                    if manager._sync_params(config_id, role, {**params, "language": legacy_language_index(params["language"], 1)}):
                        marks.add(mark)
                        self._save_marks(marks)
                    else:
                        self.ok = False
        for config_id, record in records:
            for role in ("current", "baseline"):
                params = record.get(role) or {}
                value = params.get("language")
                if isinstance(value, int) and not isinstance(value, bool) and value >= len(LANGUAGE_MODES):
                    if not manager._sync_params(config_id, role, {**params, "language": legacy_language_index(value, 2)}):
                        self.ok = False

    def finish(self):
        """Все шаги прошли: фиксируем версию схемы. Иначе ничего не пишем, и всё повторится при следующем запуске."""
        if not self.pending:
            return
        if not self.ok:
            self.plugin.log("Prefixfy migration is incomplete, it will continue at the next start")
            return
        try:
            self._set(SCHEMA_KEY, SCHEMA_VERSION)
            self._set(LEGACY_LANGUAGE_LAYOUT_KEY, 2)
            self._set(LEGACY_LANGUAGE_LIVE_KEY, 2)
            self._set(LEGACY_IGNORE_SPLIT_KEY, 1)
            self._set(LEGACY_LANGUAGE_MARKS_KEY, "")
            if self.flat_imported:
                for key in LEGACY_SETTING_KEYS:
                    self._set(key, "")
            self.pending = False
        except Exception as exc:
            self.plugin.log(f"Prefixfy migration: schema version not saved: {exc}")


CONFIG_FORMAT = "Prefixfy-config"
CONFIG_VERSION = 15
COMPONENTS = ("mask", "separator", "cute", "exceptions", "language", "media", "schedule")
COMPONENT_ALIASES = {
    "mask": ("mask",),
    "separator": ("separator", "separators"),
    "cute": ("cute",),
    "exceptions": ("exceptions",),
    "language": ("language",),
    "media": ("media", "attached_media"),
    "schedule": ("schedule",),
}
SCOPE_RESET_KEYS = ("process_message", "process_media", "process_article", "process_edit", "process_edit_message",
                    "process_edit_media", "process_edit_article", "skip_once_on_edit")
COMPONENT_KEYS = {
    "language": ("language",),
    "mask": ("mask", "markdown_enabled", "markdown_style", "text_style_enabled", "text_style", "text_style_random", "mask_rotation_enabled", "masks_list", "mask_rotation_mode", "conditional_masks", "text_style_translit", "style_words", "tag_lines"),
    "separator": ("separator_enabled", "custom_emojis", "emoji_count", "separator_frequency", "separator_spaces", "separator_space_mode"),
    "cute": CUTE_KEYS,
    "exceptions": ("exceptions", *SCOPE_RESET_KEYS, *IGNORE_KEYS, "ignore_emoji_only", "disabled_chats", "chat_scope_enabled", "regex_exceptions", "chat_type_rules"),
    "media": ("attached_media_enabled", "attached_media_path", "attached_media_name", "attached_media_mime"),
    "schedule": (),
}
MAX_CONFIG_JSON_BYTES = 1024 * 1024
MAX_MEDIA_BYTES = 256 * 1024 * 1024


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _section_from_flat_settings(settings, component):
    if not isinstance(settings, dict):
        return None
    if component == "mask" and "mask" in settings:
        return {"value": settings["mask"]}
    if component == "separator" and any(k in settings for k in ("separator_enabled", "custom_emojis", "emoji_count")):
        return {
            "enabled": settings.get("separator_enabled", False),
            "values": settings.get("custom_emojis", DEFAULT_SEPARATORS),
            "count": settings.get("emoji_count", 1),
        }
    flat_exception_keys = ("exceptions", "disabled_chats", "chat_scope_enabled", "chat_scope", "ignore_emoji_only",
                           *IGNORE_KEYS)
    if component == "exceptions" and any(k in settings for k in flat_exception_keys):
        return {
            "values": settings.get("exceptions", ""),
            "disabled_chats": settings.get("disabled_chats", ""),
            "chat_scope_enabled": settings.get("chat_scope_enabled", True),
            "chat_scope": settings.get("chat_scope"),
            "ignore_emoji_only": settings.get("ignore_emoji_only", SETTING_DEFAULTS["ignore_emoji_only"]),
            **{key: settings.get(key, SETTING_DEFAULTS[key]) for key in IGNORE_KEYS},
        }
    return None


def extract_component(data: dict, component: str):
    return legacy_upgrade_section(data, component, _extract_raw_component(data, component))


def _extract_raw_component(data: dict, component: str):
    section = None
    for key in COMPONENT_ALIASES[component]:
        if key in data:
            section = data[key]
            break
    else:
        return _section_from_flat_settings(legacy_fill_ignore_keys(data.get("settings")), component)
    if isinstance(section, dict):
        return section
    if component == "language" and _is_int(section):
        return {"value": section}
    if component == "mask" and isinstance(section, str):
        return {"value": section}
    if component in ("separator", "exceptions") and isinstance(section, str):
        return {"values": section}
    return None


def _texts_within_limit(section, depth: int = 0) -> bool:
    if depth > 3:
        return False
    for value in section.values():
        if isinstance(value, str):
            if len(value) > MAX_SETTING_TEXT or has_unsafe_text(value):
                return False
        elif isinstance(value, dict):
            if not _texts_within_limit(value, depth + 1):
                return False
        elif isinstance(value, list):
            if len(value) > 4096 or any(isinstance(item, str) and (len(item) > MAX_SETTING_TEXT or has_unsafe_text(item)) for item in value):
                return False
    return True


_CHAT_KEY_RE = re.compile(r"-?[0-9]{1,20}")


def validate_component(component: str, section: dict) -> bool:
    if not isinstance(section, dict) or not _texts_within_limit(section):
        return False
    if component == "language":
        value = section.get("value")
        return _is_int(value) and 0 <= value < len(LANGUAGE_MODES)
    if component == "mask":
        value = section.get("value")
        if not (isinstance(value, str) and (value == "" or is_valid_mask(value))):
            return False
        style = section.get("style")
        if "markdown" in section and not isinstance(section["markdown"], bool):
            return False
        if "markdown_enabled" in section and not isinstance(section["markdown_enabled"], bool):
            return False
        if "markdown_style" in section and (not _is_int(section["markdown_style"]) or not 0 <= section["markdown_style"] < MARKDOWN_STYLE_COUNT):
            return False
        if style is not None and not (
            isinstance(style, dict) and isinstance(style.get("enabled"), bool)
            and _is_int(style.get("value")) and 0 <= style["value"] < TEXT_STYLE_COUNT
        ):
            return False
        if "text_style_random" in section and not isinstance(section["text_style_random"], bool):
            return False
        if "mask_rotation_enabled" in section and not isinstance(section["mask_rotation_enabled"], bool):
            return False
        if "masks_list" in section and not isinstance(section["masks_list"], str):
            return False
        if "conditional_masks" in section and not isinstance(section["conditional_masks"], str):
            return False
        if "text_style_translit" in section and not isinstance(section["text_style_translit"], bool):
            return False
        for text_key in ("style_words", "tag_lines"):
            if text_key in section and not isinstance(section[text_key], str):
                return False
        if "mask_rotation_mode" in section and (not _is_int(section["mask_rotation_mode"]) or section["mask_rotation_mode"] not in (0, 1)):
            return False
        return True
    if component == "separator":
        values, count, enabled = section.get("values", DEFAULT_SEPARATORS), section.get("count", 1), section.get("enabled", False)
        frequency = section.get("frequency", SEPARATOR_FREQUENCY_DEFAULT)
        return (
            isinstance(values, str) and bool(values.strip())
            and _is_int(count) and 1 <= count <= MAX_SEPARATOR_COUNT
            and isinstance(enabled, bool)
            and _is_int(frequency) and 0 <= frequency < len(FREQUENCY_STEPS)
            and isinstance(section.get("spaces", True), bool)
            and _is_int(section.get("space_mode", 0)) and 0 <= section.get("space_mode", 0) <= 2
        )
    if component == "cute":
        for key in CUTE_KEYS:
            if key not in section:
                continue
            value = section[key]
            if key in CUTE_INT_KEYS:
                _, low, high = CUTE_INT_KEYS[key]
                if not (_is_int(value) and low <= value <= high):
                    return False
            elif not isinstance(value, bool):
                return False
        return True
    if component == "exceptions":
        values = section.get("values", "")
        chats = section.get("disabled_chats", "")
        enabled = section.get("chat_scope_enabled", True)
        scope = section.get("chat_scope")
        if not (isinstance(values, str) and isinstance(chats, str)
                and isinstance(enabled, bool) and isinstance(section.get("ignore_emoji_only", SETTING_DEFAULTS["ignore_emoji_only"]), bool)):
            return False
        if "regex_exceptions" in section and not isinstance(section["regex_exceptions"], str):
            return False
        if "chat_type_rules" in section and not isinstance(section["chat_type_rules"], str):
            return False
        if any(key in section and not isinstance(section[key], bool) for key in IGNORE_KEYS):
            return False
        if scope is None:
            return True
        if not isinstance(scope, dict) or scope.get("mode") not in ("exceptions", "included"):
            return False
        scope_chats = scope.get("chats", chats)
        if not isinstance(scope_chats, str):
            return False
        if "chat_scope_enabled" in section and (scope.get("mode") == "exceptions") != enabled:
            return False
        if "disabled_chats" in section and scope_chats != chats:
            return False
        return True
    if component == "schedule":
        chats, rules = section.get("chats", {}), section.get("rules", "")
        return (
            isinstance(chats, dict) and len(chats) <= 4096
            and all(isinstance(k, str) and _CHAT_KEY_RE.fullmatch(k) and isinstance(v, str) for k, v in chats.items())
            and isinstance(rules, str) and len(rules) <= 64 * 1024 and isinstance(section.get("source", ""), str)
        )
    if component == "media":
        return (isinstance(section.get("enabled", False), bool) and isinstance(section.get("file", ""), str)
                and isinstance(section.get("name", ""), str) and isinstance(section.get("mime", ""), str))
    return False


LINK_SCAN_COMPONENTS = ("mask", "separator", "cute")
_IMPORT_URL_RE = re.compile(r"(?:https?|tg|ton)://[^\s\[\]<>\"']+", re.IGNORECASE)


def _iter_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_strings(item)


def collect_import_links(data: dict, components) -> List[str]:
    """49.3.0: ссылки из выбранных частей конфигурации: «[text: ссылка]» и голые адреса в тексте масок.
    Ссылки, которые normalize_link отклоняет (javascript:, data: и т. п.), не показываются: плагин их всё равно не использует."""
    found: List[str] = []
    seen = set()

    def add(link):
        key = link.casefold()
        if link and key not in seen:
            seen.add(key)
            found.append(link)

    for component in components:
        if component not in LINK_SCAN_COMPONENTS:
            continue
        section = extract_component(data, component)
        for text in _iter_strings(section):
            for token in MASK_TOKEN_RE.finditer(text):
                if token.group(1):
                    add(normalize_link(token.group(1)) or "")
            rest = MASK_TOKEN_RE.sub(" ", text)
            for match in _IMPORT_URL_RE.finditer(rest):
                add(normalize_link(match.group(0).rstrip(".,;:!?)")) or "")
    return found


def detect_components(data: dict) -> Tuple[str, ...]:
    found = []
    for component in COMPONENTS:
        section = extract_component(data, component)
        if section is not None and validate_component(component, section):
            found.append(component)
    return tuple(found)


def _section_setting_values(component: str, section: dict) -> Dict[str, Any]:
    """50.1.0: какие настройки импорт этой части записал бы (без побочных действий). Зеркало apply_components."""
    values: Dict[str, Any] = {}
    if component == "language":
        values["language"] = section.get("value")
    elif component == "mask":
        if "markdown_enabled" in section:
            enabled, style = section["markdown_enabled"], section.get("markdown_style", SETTING_DEFAULTS["markdown_style"])
        elif "markdown_style" in section:
            style = section["markdown_style"]
            enabled = style != 1
        elif "markdown" in section:
            enabled, style = section["markdown"], 0
        else:
            enabled, style = SETTING_DEFAULTS["markdown_enabled"], SETTING_DEFAULTS["markdown_style"]
        values["mask"] = section.get("value")
        values["markdown_enabled"] = enabled
        values["markdown_style"] = 0 if style == 1 else style
        styling = section.get("style")
        if isinstance(styling, dict):
            values["text_style_enabled"], values["text_style"] = styling.get("enabled"), styling.get("value")
        for key in ("text_style_random", "mask_rotation_enabled", "masks_list", "mask_rotation_mode",
                    "conditional_masks", "text_style_translit", "style_words", "tag_lines"):
            if key in section:
                values[key] = section[key]
    elif component == "separator":
        values.update({
            "separator_enabled": section.get("enabled", False),
            "custom_emojis": section.get("values", DEFAULT_SEPARATORS),
            "emoji_count": section.get("count", 1),
            "separator_frequency": section.get("frequency", SEPARATOR_FREQUENCY_DEFAULT),
            "separator_spaces": section.get("spaces", True),
            "separator_space_mode": section.get("space_mode", 0),
        })
    elif component == "cute":
        values.update({key: section.get(key, SETTING_DEFAULTS[key]) for key in CUTE_KEYS})
    elif component == "exceptions":
        scope = section.get("chat_scope")
        if isinstance(scope, dict):
            scope_enabled = scope.get("mode") == "exceptions"
            chats = scope.get("chats", section.get("disabled_chats", ""))
        else:
            scope_enabled = bool(section.get("chat_scope_enabled", True))
            chats = section.get("disabled_chats", "")
        values.update({"exceptions": section.get("values", ""), "disabled_chats": chats, "chat_scope_enabled": scope_enabled})
        for key in ("ignore_emoji_only", *IGNORE_KEYS):
            values[key] = section.get(key, SETTING_DEFAULTS[key])
        if "regex_exceptions" in section:
            values["regex_exceptions"] = clean_regex_exceptions(section["regex_exceptions"])
        if "chat_type_rules" in section:
            values["chat_type_rules"] = dump_chat_type_rules(parse_chat_type_rules(section["chat_type_rules"]))
    return values


IMPORT_USEFUL, IMPORT_DEFAULT, IMPORT_ABSENT = "useful", "default", "absent"


def classify_component(data: dict, component: str) -> str:
    """50.1.0: даёт ли часть конфига что-то при импорте. absent — в файле нет (или она некорректна), default — есть,
    но все значения совпадают со стандартными плагина, useful — есть значения, отличающиеся от стандартных."""
    try:
        section = extract_component(data, component)
        if section is None or not validate_component(component, section):
            return IMPORT_ABSENT
        if component == "schedule":
            return IMPORT_USEFUL if (section.get("chats") or as_text(section.get("rules", "")).strip()) else IMPORT_DEFAULT
        if component == "media":
            return IMPORT_USEFUL if (section.get("enabled", False) and as_text(section.get("file", ""))) else IMPORT_DEFAULT
        values = _section_setting_values(component, section)
        if any(value != SETTING_DEFAULTS[key] for key, value in values.items() if key in SETTING_DEFAULTS):
            return IMPORT_USEFUL
        return IMPORT_DEFAULT
    except Exception:
        return IMPORT_ABSENT


def classify_components(data: dict) -> Dict[str, str]:
    return {component: classify_component(data, component) for component in COMPONENTS}


MAX_CONTAINER_ENTRIES = 16


LOCKED_MAGIC = b"PFXLOCK1"
LOCKED_VERSION = 1
LOCKED_KDF_PBKDF2_SHA256 = 1
LOCKED_ITERATIONS = 600_000
LOCKED_MIN_ITERATIONS = 100_000
LOCKED_MAX_ITERATIONS = 5_000_000
LOCKED_CHUNK = 1 << 20
LOCKED_HEADER = struct.Struct(">8sBBI16s16sIQ")
LOCKED_TAG_SIZE = 32
LOCKED_MAX_PLAIN = MAX_MEDIA_BYTES + MAX_CONFIG_JSON_BYTES + 64 * 1024
_LOCKED_STREAM_LABEL = b"prefixfy/locked/v1/stream\x00"
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 256


class ContainerLockedError(ConfigurationError):
    """Файл зашифрован паролем, а пароль не передан."""


class ContainerPasswordError(ConfigurationError):
    """Неверный пароль или файл повреждён (по шифртексту это не различить)."""


def _locked_keys(password: str, salt: bytes, iterations: int) -> Tuple[bytes, bytes]:
    secret = unicodedata.normalize("NFC", as_text(password)).encode("utf-8")
    material = hashlib.pbkdf2_hmac("sha256", secret, salt, iterations, dklen=64)
    return material[:32], material[32:]


def _locked_xor(data: bytes, k_enc: bytes, nonce: bytes, index: int) -> bytes:
    size = len(data)
    stream = hashlib.shake_256(_LOCKED_STREAM_LABEL + k_enc + nonce + index.to_bytes(8, "big")).digest(size)
    return (int.from_bytes(data, "little") ^ int.from_bytes(stream, "little")).to_bytes(size, "little")


def is_locked_container(path: str) -> bool:
    try:
        with open(path, "rb") as handle:
            return handle.read(len(LOCKED_MAGIC)) == LOCKED_MAGIC
    except OSError:
        return False


def lock_container(source: str, target: str, password: str, iterations: int = LOCKED_ITERATIONS):
    """Зашифровать готовый контейнер source в target."""
    password = as_text(password)
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise ValueError("password length is out of range")
    size = os.path.getsize(source)
    if size > LOCKED_MAX_PLAIN:
        raise ValueError("configuration is too large to encrypt")
    salt, nonce = secrets.token_bytes(16), secrets.token_bytes(16)
    header = LOCKED_HEADER.pack(LOCKED_MAGIC, LOCKED_VERSION, LOCKED_KDF_PBKDF2_SHA256, iterations,
                                salt, nonce, LOCKED_CHUNK, size)
    k_enc, k_mac = _locked_keys(password, salt, iterations)
    mac = hmac.new(k_mac, header, hashlib.sha256)
    written = 0
    temp = target + ".lock"
    try:
        with open(source, "rb") as src, open(temp, "wb") as dst:
            dst.write(header)
            index = 0
            while True:
                chunk = src.read(LOCKED_CHUNK)
                if not chunk:
                    break
                sealed = _locked_xor(chunk, k_enc, nonce, index)
                mac.update(sealed)
                dst.write(sealed)
                written += len(chunk)
                index += 1
            if written != size:
                raise IOError("configuration changed while encrypting")
            dst.write(mac.digest())
        os.replace(temp, target)
    except BaseException:
        discard_file(temp)
        raise


def _locked_header(handle, file_size: int):
    raw = handle.read(LOCKED_HEADER.size)
    if len(raw) != LOCKED_HEADER.size:
        raise ConfigurationError("encrypted configuration is damaged")
    magic, version, kdf, iterations, salt, nonce, chunk, size = LOCKED_HEADER.unpack(raw)
    if magic != LOCKED_MAGIC:
        raise ConfigurationError("not an encrypted configuration")
    if version != LOCKED_VERSION or kdf != LOCKED_KDF_PBKDF2_SHA256:
        raise ConfigurationError("unsupported encrypted configuration")
    if not LOCKED_MIN_ITERATIONS <= iterations <= LOCKED_MAX_ITERATIONS or chunk != LOCKED_CHUNK:
        raise ConfigurationError("unsupported encrypted configuration")
    if size > LOCKED_MAX_PLAIN or file_size != LOCKED_HEADER.size + size + LOCKED_TAG_SIZE:
        raise ConfigurationError("encrypted configuration is damaged")
    return raw, iterations, salt, nonce, size


def unlock_container(source: str, target: str, password: str):
    """Проверить и расшифровать source в target. Ничего не пишет, пока тег не сошёлся."""
    file_size = os.path.getsize(source)
    with open(source, "rb") as src:
        header, iterations, salt, nonce, size = _locked_header(src, file_size)
        k_enc, k_mac = _locked_keys(password, salt, iterations)
        mac = hmac.new(k_mac, header, hashlib.sha256)
        remaining = size
        while remaining:
            chunk = src.read(min(LOCKED_CHUNK, remaining))
            if not chunk:
                raise ConfigurationError("encrypted configuration is damaged")
            mac.update(chunk)
            remaining -= len(chunk)
        if not hmac.compare_digest(mac.digest(), src.read(LOCKED_TAG_SIZE)):
            raise ContainerPasswordError("wrong password or damaged file")
        src.seek(LOCKED_HEADER.size)
        temp = target + ".part"
        try:
            with open(temp, "wb") as dst:
                remaining, index = size, 0
                while remaining:
                    chunk = src.read(min(LOCKED_CHUNK, remaining))
                    dst.write(_locked_xor(chunk, k_enc, nonce, index))
                    remaining -= len(chunk)
                    index += 1
            os.replace(temp, target)
        except BaseException:
            discard_file(temp)
            raise


MEDIA_SEAL_MAGIC = b"PFXMED01"
MEDIA_SEAL_HEADER = struct.Struct(">8s16sQ")
MEDIA_OUTBOX_DIR = "Prefixfy_outbox"
MEDIA_OUTBOX_TTL = 24 * 3600


def _media_keys() -> Optional[Tuple[bytes, bytes]]:
    material = VAULT.subkey(b"media/v1")
    return (material[:32], material[32:]) if material else None


def is_sealed_media(path: str) -> bool:
    try:
        with open(path, "rb") as handle:
            return handle.read(len(MEDIA_SEAL_MAGIC)) == MEDIA_SEAL_MAGIC
    except OSError:
        return False


def seal_media_file(source: str, target: str) -> bool:
    """Записать source в target зашифрованным (атомарно). False - хранилище недоступно, записана открытая копия."""
    keys = _media_keys()
    size = os.path.getsize(source)
    if size > MAX_MEDIA_BYTES:
        raise ValueError("media is too large")
    temp = unique_temp(target)
    try:
        if keys is None:
            copy_file_limited(source, temp, MAX_MEDIA_BYTES)
        else:
            k_enc, k_mac = keys
            nonce = secrets.token_bytes(16)
            header = MEDIA_SEAL_HEADER.pack(MEDIA_SEAL_MAGIC, nonce, size)
            mac = hmac.new(k_mac, header, hashlib.sha256)
            written = 0
            with open(source, "rb") as src, open(temp, "wb") as dst:
                dst.write(header)
                index = 0
                while True:
                    chunk = src.read(LOCKED_CHUNK)
                    if not chunk:
                        break
                    sealed = _locked_xor(chunk, k_enc, nonce, index)
                    mac.update(sealed)
                    dst.write(sealed)
                    written += len(chunk)
                    index += 1
                if written != size:
                    raise IOError("media changed while encrypting")
                dst.write(mac.digest())
        os.replace(temp, target)
    except BaseException:
        discard_file(temp)
        raise
    return keys is not None


def read_media_plain(path: str, write):
    """Отдать содержимое медиа кусками в write(). Зашифрованное сначала целиком проверяется (тег), и только потом
    расшифровывается: подменённый или повреждённый файл не отдаёт ни байта. Открытое (старое) - как есть."""
    with open(path, "rb") as src:
        head = src.read(MEDIA_SEAL_HEADER.size)
        if not head.startswith(MEDIA_SEAL_MAGIC):
            src.seek(0)
            while True:
                chunk = src.read(LOCKED_CHUNK)
                if not chunk:
                    return
                write(chunk)
        if len(head) != MEDIA_SEAL_HEADER.size:
            raise ConfigurationError("media file is damaged")
        _, nonce, size = MEDIA_SEAL_HEADER.unpack(head)
        if size > MAX_MEDIA_BYTES or os.fstat(src.fileno()).st_size != MEDIA_SEAL_HEADER.size + size + LOCKED_TAG_SIZE:
            raise ConfigurationError("media file is damaged")
        keys = _media_keys()
        if keys is None:
            raise VaultError("vault is not available")
        k_enc, k_mac = keys
        mac = hmac.new(k_mac, head, hashlib.sha256)
        remaining = size
        while remaining:
            chunk = src.read(min(LOCKED_CHUNK, remaining))
            if not chunk:
                raise ConfigurationError("media file is damaged")
            mac.update(chunk)
            remaining -= len(chunk)
        if not hmac.compare_digest(mac.digest(), src.read(LOCKED_TAG_SIZE)):
            raise ConfigurationError("media file is damaged or belongs to another device")
        src.seek(MEDIA_SEAL_HEADER.size)
        remaining, index = size, 0
        while remaining:
            chunk = src.read(min(LOCKED_CHUNK, remaining))
            write(_locked_xor(chunk, k_enc, nonce, index))
            remaining -= len(chunk)
            index += 1


def media_plain_copy(path: str, name: str) -> str:
    """Путь к открытой копии медиа для отправки. Telegram загружает файл по пути и асинхронно, поэтому копия живёт в
    закрытой папке плагина до MEDIA_OUTBOX_TTL (на случай медленной загрузки и повторной отправки) и переиспользуется
    для того же файла. Открытое (старое) медиа отправляется напрямую."""
    if not is_sealed_media(path):
        return path
    outbox = os.path.join(get_plugins_dir(), MEDIA_OUTBOX_DIR)
    os.makedirs(outbox, exist_ok=True)
    sweep_old_files(outbox, MEDIA_OUTBOX_TTL)
    stat = os.stat(path)
    digest = hashlib.sha256(f"{os.path.realpath(path)}|{stat.st_size}|{stat.st_mtime_ns}".encode("utf-8")).hexdigest()[:24]
    target = os.path.join(outbox, digest + (safe_extension(name) or safe_extension(path) or ".bin"))
    if os.path.isfile(target):
        os.utime(target, None)
        return target
    temp = unique_temp(target)
    try:
        with open(temp, "wb") as handle:
            read_media_plain(path, handle.write)
        os.replace(temp, target)
    except BaseException:
        discard_file(temp)
        raise
    return target


def clear_media_outbox():
    outbox = os.path.join(get_plugins_dir(), MEDIA_OUTBOX_DIR)
    sweep_old_files(outbox, -1)


def seal_legacy_media(log) -> int:
    """Однократно: открытые медиафайлы в папках медиа плагина шифруются на месте (путь и имя не меняются).
    Файлы прямо в папке плагинов не трогаем: это могут быть чужие файлы."""
    if _media_keys() is None:
        return 0
    sealed = 0
    base = get_plugins_dir()
    for folder_name in sorted(MEDIA_STORE_DIRS):
        for folder, _dirs, files in os.walk(os.path.join(base, folder_name)):
            for name in files:
                path = os.path.join(folder, name)
                try:
                    if not is_media_store_file(path) or is_sealed_media(path):
                        continue
                    if os.path.getsize(path) > MAX_MEDIA_BYTES:
                        continue
                    stat = os.stat(path)
                    seal_media_file(path, path)
                    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
                    sealed += 1
                except Exception as exc:
                    log(f"Prefixfy: media file was not encrypted ({name}): {exc}")
    return sealed


def _zip_entry_count_ok(path: str) -> bool:
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as handle:
            handle.seek(max(0, size - (65535 + 22 + 20)))
            tail = handle.read()
    except OSError:
        return False
    position = tail.rfind(b"PK\x05\x06")
    if position < 0 or position + 22 > len(tail):
        return False
    if position >= 20 and tail[position - 20:position - 16] == b"PK\x06\x07":
        return False
    total = int.from_bytes(tail[position + 10:position + 12], "little")
    this_disk = int.from_bytes(tail[position + 8:position + 10], "little")
    return total == this_disk and 0 < total <= MAX_CONTAINER_ENTRIES


def _check_zip_member(info: zipfile.ZipInfo, limit: int):
    """Запись контейнера: не каталог, без пароля, только stored/deflate (без bz2/lzma), размер в пределах."""
    if info.is_dir() or info.flag_bits & 0x1:
        raise ConfigurationError("invalid container entry")
    if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        raise ConfigurationError("unsupported compression")
    if info.file_size > limit:
        raise ConfigurationError("container entry is too large")


def _container_media_section(data):
    """Раздел media ровно в том виде, как его выберет extract_component: первый из алиасов, если это объект."""
    for alias in COMPONENT_ALIASES["media"]:
        if alias in data:
            return data[alias] if isinstance(data[alias], dict) else None
    return None


def _read_zip_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo, limit: int) -> bytes:
    with archive.open(info) as source:
        data = source.read(limit + 1)
    if len(data) > limit:
        raise ConfigurationError("config.json is too large")
    return data


def _extract_zip_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo, target: str, limit: int):
    written = 0
    try:
        with archive.open(info) as source, open(target, "wb") as sink:
            while True:
                chunk = source.read(64 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > limit:
                    raise ConfigurationError("media is too large")
                sink.write(chunk)
    except BaseException:
        discard_file(target)
        raise


class ConfigTransfer:
    CONFIG_IMPORT_REQUEST_CODE = 7400
    CONFIG_EXPORT_REQUEST_CODE = 7401
    MEDIA_IMPORT_REQUEST_CODE = 7403
    DEBUG_EXPORT_REQUEST_CODE = 7404
    CONFIG_EXTENSION = ".prefixfy"
    EXPORT_MAX_CONFIGS = 10

    def __init__(self, plugin):
        self.plugin = plugin
        self.settings = plugin.settings
        self.localization = plugin.localization
        self.pending_components: Tuple[str, ...] = ()
        self.pending_import_as_new = False
        self.pending_export_id: Optional[str] = None
        self.pending_export_name = ""
        self.pending_export_password: Optional[str] = None
        self._awaiting: Optional[int] = None
        self._file_handler_secret = None
        self.media_data_dir = os.path.join(get_plugins_dir(), "Prefixfy_media")
        ensure_dir_exists(self.media_data_dir)

    def _tr(self, key, **kwargs):
        return self.localization.tr(key, **kwargs)

    def _activity(self):
        fragment = get_last_fragment()
        if not fragment:
            return None, None
        return fragment, fragment.getParentActivity()

    def _toast(self, key, fragment=None, **kwargs):
        self.plugin._toast(key, fragment, **kwargs)

    def media_path(self, source=None) -> str:
        return as_text((source if source is not None else self.settings).get("attached_media_path", ""))

    def media_exists(self, source=None) -> bool:
        path = self.media_path(source)
        return bool(path and is_media_store_file(path) and os.path.isfile(path))

    def media_info(self, source=None) -> Dict[str, str]:
        reader = source if source is not None else self.settings
        name = as_text(reader.get("attached_media_name", "")) or os.path.basename(self.media_path(source))
        mime = as_text(reader.get("attached_media_mime", "")) or mimetypes.guess_type(name)[0] or "application/octet-stream"
        return {"name": name, "mime": mime}

    _MIME_RE = re.compile(r"[a-z0-9.+\-]{1,60}/[a-z0-9.+\-]{1,80}")

    def _prepare_media_target(self, name, mime):
        name = re.sub(r"[\x00-\x1f\x7f]", "", os.path.basename(as_text(name).replace("\\", "/"))).strip()[:120]
        name = as_text(sanitize_text(name)).strip() or "attached_media.bin"
        mime = as_text(mime).strip().lower()
        if not self._MIME_RE.fullmatch(mime):
            mime = mimetypes.guess_type(name)[0] or ""
        ext = safe_extension(name)
        if ext not in MEDIA_EXTENSIONS:
            guessed = (mimetypes.guess_extension(mime) or "") if mime else ""
            ext = guessed if guessed in MEDIA_EXTENSIONS else ""
        if not (mime.startswith(("image/", "video/")) or ext in MEDIA_EXTENSIONS):
            raise ValueError("unsupported media format")
        return name, mime, os.path.join(self.media_data_dir, "attached_media" + (ext or ".bin"))

    def _commit_media(self, temp_path, target, name, mime):
        old = self.media_path()
        try:
            seal_media_file(temp_path, target)
        finally:
            discard_file(temp_path)
        with self.plugin.runtime_manager.bulk():
            self.settings.set("attached_media_path", target)
            self.settings.set("attached_media_name", name)
            self.settings.set("attached_media_mime", mime)
            self.settings.set("attached_media_enabled", True)
        if (old and os.path.abspath(old) != os.path.abspath(target)
                and is_inside(old, self.media_data_dir) and os.path.isfile(old)):
            discard_file(old)

    def store_media_file(self, source_path, name, mime=None):
        name, mime, target = self._prepare_media_target(name, mime)
        if not os.path.isfile(source_path) or os.path.getsize(source_path) > MAX_MEDIA_BYTES:
            raise ValueError("media is missing or too large")
        temp = unique_temp(target)
        try:
            copy_file_limited(source_path, temp, MAX_MEDIA_BYTES)
            self._commit_media(temp, target, name, mime)
        except BaseException:
            discard_file(temp)
            raise

    def store_media_uri(self, uri, name, mime=None):
        _, activity = self._activity()
        if not activity:
            raise IOError("activity unavailable")
        name, mime, target = self._prepare_media_target(name, mime)
        stream = activity.getContentResolver().openInputStream(uri)
        if stream is None:
            raise IOError("cannot read media")
        temp = unique_temp(target)
        try:
            try:
                with open(temp, "wb") as handle:
                    copy_java_stream(stream, handle, limit=MAX_MEDIA_BYTES)
            finally:
                stream.close()
            self._commit_media(temp, target, name, mime)
        except BaseException:
            discard_file(temp)
            raise

    def delete_media(self):
        path = self.media_path()
        with self.plugin.runtime_manager.bulk():
            self.settings.set("attached_media_path", "")
            self.settings.set("attached_media_name", "")
            self.settings.set("attached_media_mime", "")
            self.settings.set("attached_media_enabled", False, reload_settings=True)
        if path and is_inside(path, self.media_data_dir) and os.path.isfile(path):
            discard_file(path)
        clear_media_outbox()

    def _blocked(self, fragment=None, export: bool = False) -> bool:
        remote = getattr(self.plugin, "remote", None)
        if remote is None or remote.allows():
            return False
        if export and remote.export_open():
            return False
        key, kwargs = remote.notice()
        self._toast(key, fragment, **kwargs)
        return True

    def _import_locked(self, fragment=None) -> bool:
        """Импорт конфигураций закрыт, пока не завершена начальная настройка. При любой ошибке проверки: закрыто."""
        try:
            done = self.plugin._setup_stage() >= SETUP_DONE
        except Exception:
            done = False
        if done:
            return False
        self._toast("config_import_locked", fragment)
        return True

    def request_media_import(self, view=None):
        if self._blocked():
            return
        _, activity = self._activity()
        if not activity:
            return
        try:
            from android.os import Build
            if int(Build.VERSION.SDK_INT) >= 33:
                self._awaiting = self.MEDIA_IMPORT_REQUEST_CODE
                activity.startActivityForResult(Intent("android.provider.action.PICK_IMAGES"), self.MEDIA_IMPORT_REQUEST_CODE)
                return
        except Exception as exc:
            self.plugin.log(f"Photo Picker launch failed, using fallback: {exc}")
        intent = Intent(Intent.ACTION_GET_CONTENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType("*/*")
        try:
            intent.putExtra(Intent.EXTRA_MIME_TYPES, ["image/*", "video/*"])
        except Exception:
            pass
        self._awaiting = self.MEDIA_IMPORT_REQUEST_CODE
        activity.startActivityForResult(intent, self.MEDIA_IMPORT_REQUEST_CODE)

    def _uri_display_name(self, uri) -> str:
        _, activity = self._activity()
        if not activity:
            return ""
        try:
            from android.provider import OpenableColumns
            cursor = activity.getContentResolver().query(uri, [OpenableColumns.DISPLAY_NAME], None, None, None)
            if cursor is None:
                return ""
            try:
                if cursor.moveToFirst():
                    index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                    if index >= 0:
                        return as_text(cursor.getString(index))
            finally:
                cursor.close()
        except Exception as exc:
            self.plugin.log(f"Media filename lookup failed: {exc}")
        return ""

    @staticmethod
    def visible_components() -> Tuple[str, ...]:
        hidden = set()
        if not FEATURES.on("attached_media"):
            hidden.add("media")
        if not has_language_choice():
            hidden.add("language")
        if not FEATURES.on("schedule") and not FEATURES.on("chat_configs"):
            hidden.add("schedule")
        return tuple(c for c in COMPONENTS if c not in hidden)

    def _component_label(self, component, for_reset: bool = False):
        if for_reset and component == "exceptions":
            return self._tr("config_part_exceptions_reset")
        return self._tr("config_part_" + component)

    def request_import(self, view=None):
        self._show_selection("import")

    def request_export(self, view=None):
        self._show_selection("export")

    def request_reset(self, view=None):
        self._show_selection("reset")

    def _show_selection(self, operation):
        if self._blocked(export=operation == "export"):
            return
        if operation == "import" and self._import_locked():
            return
        if operation == "export":
            self._show_export_selection()
            return
        fragment, _ = self._activity()
        available = tuple(c for c in self.visible_components() if operation != "reset" or COMPONENT_KEYS.get(c) or c == "schedule")
        rows = [(self._component_label(component, operation == "reset"), True, True) for component in available]
        extra = None
        message = self._tr("config_parts_message", n=len(available))
        imported = False
        if operation == "import":
            extra = (self._tr("config_import_as_new"), False)
        elif operation == "reset":
            imported = self.plugin.configurations.is_imported()
            extra = (self._tr("config_reset_to_plugin"), False, imported)
            if not imported:
                message += "\n\n" + self._tr("config_reset_to_plugin_unavailable")

        def confirm(selected, extra_checked):
            if not selected:
                self._toast("config_parts_none", fragment)
                return False
            components = tuple(available[index] for index in selected)
            if operation == "import":
                self._request_import(components, extra_checked)
            elif operation == "export":
                self._request_export(components)
            else:
                self.plugin.configurations.reset_active_components(components, plugin_defaults=bool(extra_checked and imported))
            return True

        self.plugin.show_checklist(
            self._tr("config_parts_title"), rows, confirm,
            message=message,
            extra=extra, positive=self._tr("action_apply"), fragment=fragment,
        )

    def _request_import(self, components, as_new=False):
        if self._import_locked():
            return
        _, activity = self._activity()
        if not activity:
            return
        self.pending_components = tuple(components)
        self.pending_import_as_new = bool(as_new)
        intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType("application/octet-stream")
        self._awaiting = self.CONFIG_IMPORT_REQUEST_CODE
        activity.startActivityForResult(intent, self.CONFIG_IMPORT_REQUEST_CODE)

    def read_container(self, path: str, password: Optional[str] = None) -> dict:
        """53.0.0: зашифрованный паролем файл сначала проверяется и расшифровывается во временный файл, который
        удаляется сразу после разбора. Без пароля - ContainerLockedError, неверный пароль - ContainerPasswordError."""
        if not is_locked_container(path):
            return self._read_plain_container(path)
        if password is None:
            raise ContainerLockedError("configuration is protected with a password")
        sweep_old_files(temp_dir("imports"), IMPORT_TEMP_TTL)
        plain = os.path.join(temp_dir("imports"), uuid.uuid4().hex + ".unlocked")
        try:
            unlock_container(path, plain, password)
            return self._read_plain_container(plain)
        finally:
            discard_file(plain)

    def _read_plain_container(self, path: str) -> dict:
        if not _zip_entry_count_ok(path):
            raise ConfigurationError("not a .prefixfy container")
        sweep_old_files(temp_dir("imports"), IMPORT_TEMP_TTL)
        extracted = None
        done = False
        try:
            with zipfile.ZipFile(path, "r") as archive:
                if len(archive.infolist()) > MAX_CONTAINER_ENTRIES:
                    raise ConfigurationError("too many container entries")
                try:
                    info = archive.getinfo("config.json")
                except KeyError:
                    raise ConfigurationError("config.json missing")
                _check_zip_member(info, MAX_CONFIG_JSON_BYTES)
                try:
                    data = json.loads(_read_zip_member(archive, info, MAX_CONFIG_JSON_BYTES).decode("utf-8"))
                except (ValueError, RecursionError) as exc:
                    raise ConfigurationError("invalid config.json") from exc
                if not isinstance(data, dict):
                    raise ConfigurationError("root is not an object")
                if data.get("format") not in (None, CONFIG_FORMAT) + LEGACY_CONFIG_FORMATS:
                    raise ConfigurationError("unknown configuration format")

                for alias in COMPONENT_ALIASES["media"]:
                    foreign = data.get(alias)
                    if isinstance(foreign, dict):
                        foreign.pop("_media_path", None)
                media = _container_media_section(data)
                if media is not None:
                    entry = as_text(media.get("file")).replace("\\", "/")
                    if entry:
                        if (entry.startswith("/") or "\x00" in entry or entry == "config.json"
                                or ".." in entry.split("/")):
                            raise ConfigurationError("invalid media path")
                        try:
                            media_info = archive.getinfo(entry)
                        except KeyError:
                            media_info = None
                        if media_info is not None:
                            _check_zip_member(media_info, MAX_MEDIA_BYTES)
                            extracted = os.path.join(temp_dir("imports"), uuid.uuid4().hex + safe_extension(entry))
                            _extract_zip_member(archive, media_info, extracted, MAX_MEDIA_BYTES)
                            media["_media_path"] = extracted
                done = True
                return data
        except zipfile.BadZipFile as exc:
            raise ConfigurationError("not a .prefixfy container") from exc
        except (RuntimeError, NotImplementedError, EOFError, zlib.error, zipfile.LargeZipFile) as exc:
            raise ConfigurationError("unreadable .prefixfy container") from exc
        finally:
            if not done and extracted:
                discard_file(extracted)

    @staticmethod
    def discard_container_media(data):
        media = _container_media_section(data) if isinstance(data, dict) else None
        path = media.get("_media_path") if media is not None else None
        if path and is_import_temp(path) and os.path.isfile(path):
            discard_file(path)

    def _copy_uri_to_temp_file(self, uri) -> str:
        _, activity = self._activity()
        if not activity:
            raise IOError("activity unavailable")
        stream = activity.getContentResolver().openInputStream(uri)
        if stream is None:
            raise IOError("cannot read configuration")
        path = os.path.join(temp_dir("imports"), uuid.uuid4().hex + self.CONFIG_EXTENSION)
        try:
            try:
                with open(path, "wb") as handle:
                    copy_java_stream(stream, handle, limit=MAX_MEDIA_BYTES + MAX_CONFIG_JSON_BYTES + 64 * 1024)
            finally:
                stream.close()
        except BaseException:
            discard_file(path)
            raise
        return path

    def register_file_handler(self):
        if self._file_handler_secret:
            return
        try:
            self._file_handler_secret = self.plugin.add_file_hook(
                FilesController.FileInfo(ext="prefixfy", on_click=self._on_config_file_click)
            )
        except Exception as exc:
            self.plugin.log(f"Prefixfy file handler registration failed: {exc}")
            self._file_handler_secret = None

    def unregister_file_handler(self):
        secret = self._file_handler_secret
        if not secret:
            return
        for attempt in (1, 2):
            try:
                self.plugin.remove_file_hook("prefixfy", secret)
            except Exception as exc:
                self.plugin.log(f"Prefixfy file handler unregistration failed (attempt {attempt}): {exc}")
                continue
            self._file_handler_secret = None
            return

    def _on_config_file_click(self, args):
        fragment = getattr(args, "parent_fragment", None) or get_last_fragment()
        if self._blocked(fragment):
            return
        if self._import_locked(fragment):
            return
        try:
            path = args.file.getAbsolutePath()
        except Exception as exc:
            self.plugin.log(f"Prefixfy file open failed: {exc}")
            self._toast("config_import_file_failed", fragment)
            return

        def opened(data):
            handed_over = False
            try:
                visible = self.visible_components()
                detected = tuple(c for c in detect_components(data) if c in visible)
                if not detected:
                    raise ConfigurationError("configuration has no valid components")
                states = classify_components(data)
                useful = tuple(c for c in detected if states.get(c) == IMPORT_USEFUL)
                if not useful:
                    self._toast("config_import_nothing", fragment)
                    return
                handed_over = True
                run_on_ui_thread(lambda: self._show_opened_parts(data, fragment, visible, states, useful))
            except Exception as exc:
                self.plugin.log(f"Prefixfy file open failed: {exc}")
                self._toast("config_import_file_failed", fragment)
            finally:
                if not handed_over:
                    self.discard_container_media(data)

        self._open_container(path, fragment, opened)

    def _open_container(self, path: str, fragment, on_data, on_finish=None, password: Optional[str] = None):
        """Прочитать контейнер в фоне. Зашифрованный - спросить пароль (снова, если он неверный). on_data(data)
        вызывается в фоновом потоке после успешного чтения; on_finish() - когда исходный файл больше не нужен
        (прочитан, ошибка или отказ от ввода пароля)."""
        def finish():
            if on_finish is not None:
                try:
                    on_finish()
                except Exception as exc:
                    self.plugin.log(f"Prefixfy import cleanup failed: {exc}")

        def work():
            try:
                data = self.read_container(path, password=password)
            except ContainerLockedError:
                run_on_ui_thread(lambda: self._ask_import_password(path, fragment, on_data, on_finish, wrong=False))
                return
            except ContainerPasswordError:
                run_on_ui_thread(lambda: self._ask_import_password(path, fragment, on_data, on_finish, wrong=True))
                return
            except Exception as exc:
                self.plugin.log(f"Prefixfy file open failed: {exc}")
                self._toast("config_import_invalid" if isinstance(exc, ConfigurationError) else "config_import_file_failed",
                            fragment)
                finish()
                return
            finish()
            on_data(data)

        if password is not None:
            self._toast("password_checking", fragment)
        threading.Thread(target=work, name="PrefixfyOpenConfig", daemon=True).start()

    def _ask_import_password(self, path, fragment, on_data, on_finish, wrong: bool):
        def accepted(password):
            self._open_container(path, fragment, on_data, on_finish, password=password)

        def cancelled():
            if on_finish is not None:
                try:
                    on_finish()
                except Exception as exc:
                    self.plugin.log(f"Prefixfy import cleanup failed: {exc}")

        shown = self.plugin.show_password_dialog(
            self._tr("password_import_title"),
            self._tr("password_wrong") if wrong else self._tr("password_import_message"),
            accepted, confirm=False, positive=self._tr("action_next"), fragment=fragment, on_cancel=cancelled,
        )
        if not shown:
            cancelled()

    def _ask_export_password(self, on_password, name: Optional[str] = None, on_cancel=None):
        fragment, _ = self._activity()
        title = self._tr("password_export_title_named", name=name) if name else self._tr("password_export_title")
        self.plugin.show_password_dialog(
            title, self._tr("password_export_message"),
            on_password, confirm=True, positive=self._tr("action_next"), fragment=fragment, on_cancel=on_cancel,
        )

    def _show_opened_parts(self, data, fragment, visible, states, useful):
        shown = False
        try:
            def row_label(c):
                if states.get(c) == IMPORT_DEFAULT:
                    return self._component_label(c) + " — " + self._tr("config_part_state_default")
                if states.get(c) != IMPORT_USEFUL:
                    return self._component_label(c) + " — " + self._tr("config_part_state_absent")
                return self._component_label(c)

            rows = [(row_label(c), c in useful and c != "media", c in useful) for c in visible]

            def confirm(selected, as_new):
                chosen = tuple(visible[i] for i in selected if visible[i] in useful)
                if not chosen:
                    self._toast("config_parts_none", fragment)
                    return False
                self._import_opened_data(data, fragment, chosen, as_new)
                return True

            def on_dismiss_without_import():
                self.discard_container_media(data)

            shown = bool(self.plugin.show_checklist(
                self._tr("config_import_found_title"), rows, confirm,
                message=self._tr("config_import_found_contains"),
                extra=(self._tr("config_import_as_new"), False),
                positive=self._tr("config_import"), fragment=fragment,
                on_cancel=on_dismiss_without_import,
            ))
        except Exception as exc:
            self.plugin.log(f"Prefixfy file open failed: {exc}")
            if fragment:
                self._toast("config_import_file_failed", fragment)
        finally:
            if not shown:
                self.discard_container_media(data)

    IMPORT_LINKS_SHOWN = 8

    @staticmethod
    def _shorten(text, limit) -> str:
        text = as_text(text)
        return text if len(text) <= limit else text[:max(1, limit - 1)].rstrip() + "…"

    def _confirm_import_links(self, links, data, fragment, components, as_new) -> bool:
        """49.3.0: перед импортом показываем ссылки из выбранных частей. Без ответа импорт не начинается."""
        activity = self.plugin._dialog_activity(fragment)
        if not activity:
            return False
        shown = links[:self.IMPORT_LINKS_SHOWN]
        lines = ["• " + self._shorten(link, 80) for link in shown]
        if len(links) > len(shown):
            lines.append(self._tr("config_import_links_more", n=len(links) - len(shown)))
        builder = AlertDialogBuilder(activity)
        builder.set_title(self._tr("config_import_links_title"))
        builder.set_message(self._tr("config_import_links_message") + "\n\n" + "\n".join(lines))
        def accepted(bld, which):
            bld.dismiss()
            self._import_opened_data(data, fragment, components, as_new, links_confirmed=True)

        def declined(bld, which):
            bld.dismiss()
            self.discard_container_media(data)
            self._toast("config_import_cancelled", fragment)

        builder.set_positive_button(self._tr("config_import"), accepted)
        builder.set_negative_button(self._tr("action_cancel"), declined)
        return bool(self.plugin._show_builder(builder, cancelable=False))

    def _import_opened_data(self, data, fragment, components, as_new, links_confirmed=False):
        if self._import_locked(fragment):
            self.discard_container_media(data)
            return
        if not links_confirmed:
            states = classify_components(data)
            useless = tuple(c for c in components if states.get(c) != IMPORT_USEFUL)
            if useless:
                components = tuple(c for c in components if c not in useless)
                if not components:
                    self.discard_container_media(data)
                    self._toast("config_import_nothing", fragment)
                    return
                self._toast("config_import_skipped", fragment, parts=", ".join(self._component_label(c) for c in useless))
        if not links_confirmed:
            try:
                links = collect_import_links(data, components)
            except Exception as exc:
                self.plugin.log(f"Prefixfy import link scan failed: {exc}")
                links = []
            if links:
                def ask_links():
                    try:
                        shown = self._confirm_import_links(links, data, fragment, components, as_new)
                    except Exception as exc:
                        self.plugin.log(f"Prefixfy import link dialog failed: {exc}")
                        shown = False
                    if not shown:
                        self.discard_container_media(data)
                        self._toast("config_import_failed", fragment)

                run_on_ui_thread(ask_links)
                return
        if as_new:
            if self.plugin._acct_on():
                try:
                    asked = self._ask_import_target(data, components, fragment, as_new=True)
                except Exception as exc:
                    self.plugin.log(f"Prefixfy import target dialog failed: {exc}")
                    asked = False
                if not asked:
                    self.plugin.log("Prefixfy import cancelled: the account picker could not be shown")
                    self.discard_container_media(data)
                    self._toast("config_import_failed", fragment)
                return
            self._prompt_import_name(data, fragment, components)
            return
        self._finish_import(data, components, False, None, fragment)

    def _imported_name_base(self, data) -> str:
        """46.3.0: имя из файла (если оно есть) подставляется в диалог имени; изменить его по-прежнему можно."""
        raw = data.get("name") if isinstance(data, dict) else None
        name = ConfigurationsManager.normalize_name(raw) if isinstance(raw, str) else ""
        return name[:MAX_CONFIG_NAME_LENGTH - 4].strip() or self._tr("config_imported_name")

    def _prompt_import_name(self, data, fragment, components, target=None):
        configurations = self.plugin.configurations
        uid = None if target is None else (None if target == ACCT_COMMON else target)
        scoped = target is not None

        def confirm(value, editor):
            name = ConfigurationsManager.normalize_name(value)
            error = configurations.name_error_in(uid, name) if scoped else configurations.name_error(name)
            if error:
                editor.setError(self._tr(error))
                return False
            self._finish_import(data, components, True, name, fragment, target=target)
            return True

        def cancelled():
            self.discard_container_media(data)
            self._toast("config_import_cancelled", fragment)

        if not self.plugin.show_text_dialog(
            self._tr("config_import_new_name"), confirm,
            text=unique_name(
                self._imported_name_base(data),
                configurations.scope_names(uid) if scoped else configurations.selector_items(),
            ),
            hint=self._tr("config_name_hint"),
            positive=self._tr("config_import"), fragment=fragment, on_cancel=cancelled,
        ):
            self.discard_container_media(data)

    def _ask_import_target(self, data, components, fragment, as_new=False) -> bool:
        plugin = self.plugin
        activity = plugin._dialog_activity(fragment)
        if not activity:
            return False
        configs = plugin.configurations
        accounts = plugin._accounts()
        choices: List[Any] = ([] if as_new else [ACCT_ALL]) + [ACCT_COMMON] + list(accounts.values())
        labels = ([] if as_new else [self._tr("account_import_all")]) + [self._tr("account_import_common")]
        labels += [plugin._acct_label(slot, uid, mark=True) for slot, uid in accounts.items()]
        current = ACCT_COMMON if configs.edit_uid is None else configs.edit_uid
        labels = [("✓ " if choice == current else "") + label for choice, label in zip(choices, labels)]
        builder = AlertDialogBuilder(activity)
        builder.set_title(self._tr("account_import_title"))

        guard = DismissGuard(lambda: (self.discard_container_media(data), self._toast("config_import_cancelled", fragment)))

        def picked(bld, which):
            guard.mark()
            bld.dismiss()
            if 0 <= which < len(choices):
                if as_new:
                    run_on_ui_thread(lambda: self._prompt_import_name(data, fragment, components, target=choices[which]))
                else:
                    self._finish_import(data, components, False, None, fragment, target=choices[which])
            else:
                self.discard_container_media(data)

        def cancelled(bld, which):
            guard.mark()
            bld.dismiss()
            self.discard_container_media(data)
            self._toast("config_import_cancelled", fragment)

        builder.set_items(labels, picked)
        builder.set_negative_button(self._tr("action_cancel"), cancelled)
        return bool(plugin._show_builder(builder, guard))

    @staticmethod
    def _file_config_name(data) -> str:
        raw = data.get("name") if isinstance(data, dict) else None
        name = ConfigurationsManager.normalize_name(raw) if isinstance(raw, str) else ""
        return name[:MAX_CONFIG_NAME_LENGTH - 4].strip()

    def _import_rename_plan(self, data, target):
        """48.1.0: импорт в существующую конфигурацию. Если в файле есть имя, отличное от текущего, спрашиваем,
        брать ли его (48.2.0: до импорта, сам импорт выполняется только после ответа). Для «во все аккаунты» вопроса нет: целей несколько."""
        imported = self._file_config_name(data)
        if not imported:
            return None
        configs = self.plugin.configurations
        if target is None:
            uid, config_id = configs.edit_uid, configs.scope_active_id()
        elif target == ACCT_COMMON:
            uid, config_id = None, configs.active_id
        elif isinstance(target, int) and not isinstance(target, bool):
            uid = target
            config_id = configs.accounts.pin(uid) or configs.accounts.active_id(uid)
        else:
            return None
        record = configs._record(config_id) if config_id else None
        if record is None:
            return None
        current = as_text(record.get("name"))
        if ConfigurationsManager.normalize_name(current).casefold() == imported.casefold():
            return None
        return uid, config_id, imported, current

    def _offer_import_rename(self, plan, on_answer, fragment=None) -> bool:
        """48.2.0: вопрос задаётся до импорта. on_answer(take_name) вызывается после нажатия кнопки, и только тогда
        выполняется импорт. Возвращает False, если окно показать не удалось."""
        uid, config_id, imported, current = plan
        activity = self.plugin._dialog_activity(fragment)
        if not activity:
            return False
        builder = AlertDialogBuilder(activity)
        builder.set_title(self._tr("config_import_take_name_title"))
        shown_imported, shown_current = self._shorten(imported, 40), self._shorten(current, 40)
        builder.set_message(self._tr("config_import_take_name", name=shown_imported, current=shown_current))

        def answered(take_name):
            def handler(bld, which):
                bld.dismiss()
                on_answer(take_name)
            return handler

        builder.set_positive_button(
            self._tr("config_import_take_name_yes", name=self._shorten(imported, 16)), answered(True))
        builder.set_negative_button(
            self._tr("config_import_take_name_no", current=self._shorten(current, 16)), answered(False))
        return bool(self.plugin._show_builder(builder, cancelable=False))

    def _apply_import_rename(self, plan, fragment=None):
        uid, _planned_id, imported, _current = plan
        configs = self.plugin.configurations
        try:
            with configs._lock:
                if uid is None:
                    config_id = configs.active_id
                else:
                    config_id = None if configs.accounts.pin(uid) else configs.accounts.active_id(uid)
            if not config_id:
                return
            if not configs.rename_imported(uid, config_id, imported):
                self._toast("config_save_failed", fragment)
        except Exception as exc:
            self.plugin.log(f"Prefixfy import rename failed: {exc}")
            self._toast("config_save_failed", fragment)

    def _finish_import(self, data, components, as_new, name, fragment, target=None):
        if self._import_locked(fragment):
            self.discard_container_media(data)
            return
        if target is None and not as_new:
            if self.plugin._acct_on():
                try:
                    asked = self._ask_import_target(data, components, fragment)
                except Exception as exc:
                    self.plugin.log(f"Prefixfy import target dialog failed: {exc}")
                    asked = False
                if asked:
                    return
                self.plugin.log("Prefixfy import cancelled: the account picker could not be shown")
                self.discard_container_media(data)
                self._toast("config_import_failed", fragment)
                return
            self.plugin.log(
                f"Prefixfy import: account picker skipped (account mode is off or fewer than 2 accounts: "
                f"{len(self.plugin._accounts())} found)"
            )
        rename_plan = None
        if not as_new:
            try:
                rename_plan = self._import_rename_plan(data, target)
            except Exception as exc:
                self.plugin.log(f"Prefixfy import rename plan failed: {exc}")
        if rename_plan is not None:
            plan = rename_plan

            def on_answer(take_name):
                self._run_import(data, components, False, None, fragment, target,
                                 rename_plan=plan if take_name else None)

            def ask():
                try:
                    shown = self._offer_import_rename(plan, on_answer, fragment)
                except Exception as exc:
                    self.plugin.log(f"Prefixfy import rename dialog failed: {exc}")
                    shown = False
                if not shown:
                    self.plugin.log("Prefixfy import: the name question could not be shown, importing without renaming")
                    self._run_import(data, components, False, None, fragment, target)

            run_on_ui_thread(ask)
            return
        self._run_import(data, components, as_new, name, fragment, target)

    def _run_import(self, data, components, as_new, name, fragment, target=None, rename_plan=None):
        if self._import_locked(fragment):
            self.discard_container_media(data)
            return
        try:
            if target is None:
                self.plugin.configurations.import_data(data, components, as_new=as_new, name=name)
            elif as_new:
                self.plugin.configurations.import_new_to_account(data, components, name, target)
            else:
                self.plugin.configurations.import_to_accounts(data, components, target)
            if rename_plan is not None:
                self._apply_import_rename(rename_plan, fragment)
            self.plugin.reload_settings_ui()
            self._toast("config_import_done", fragment)
        except ConfigurationError as exc:
            self.plugin.log(f"Prefixfy import rejected: {exc}")
            self._toast("config_import_invalid", fragment)
        except ConfigurationSaveError as exc:
            self.plugin.log(f"Prefixfy import aborted: {exc}")
            self._toast("config_save_failed", fragment)
        except Exception as exc:
            self.plugin.log(f"Prefixfy import failed: {exc}")
            self._toast("config_import_failed", fragment)
        finally:
            self.discard_container_media(data)

    def apply_components(self, data: dict, components):
        pending = {}
        for component in components:
            section = extract_component(data, component)
            if section is None or not validate_component(component, section):
                raise ConfigurationError("missing or invalid component: " + component)
            pending[component] = section

        with self.plugin.runtime_manager.bulk():
            media = pending.get("media")
            if media is not None:
                if media.get("enabled", False):
                    path = media.get("_media_path")
                    if not path or not is_import_temp(path) or not os.path.isfile(path):
                        raise ConfigurationError("media file is missing from container")
                    self.store_media_file(path, media.get("name") or os.path.basename(media.get("file", "")), media.get("mime"))
                else:
                    self.settings.set("attached_media_enabled", False)

            for component, section in pending.items():
                if component == "language":
                    self.settings.set("language", section["value"])
                elif component == "mask":
                    self._apply_mask_section(section)
                elif component == "separator":
                    self.settings.set("separator_enabled", section.get("enabled", False))
                    self.settings.set("custom_emojis", section.get("values", DEFAULT_SEPARATORS))
                    self.settings.set("emoji_count", section.get("count", 1))
                    self.settings.set("separator_frequency", section.get("frequency", SEPARATOR_FREQUENCY_DEFAULT))
                    self.settings.set("separator_spaces", section.get("spaces", True))
                    self.settings.set("separator_space_mode", section.get("space_mode", 0))
                elif component == "cute":
                    for key in CUTE_KEYS:
                        self.settings.set(key, section.get(key, SETTING_DEFAULTS[key]))
                elif component == "exceptions":
                    self.settings.set("exceptions", section.get("values", ""))
                    scope = section.get("chat_scope")
                    if isinstance(scope, dict):
                        scope_enabled = scope.get("mode") == "exceptions"
                        chats = scope.get("chats", section.get("disabled_chats", ""))
                    else:
                        scope_enabled = bool(section.get("chat_scope_enabled", True))
                        chats = section.get("disabled_chats", "")
                    self.settings.set("disabled_chats", chats)
                    self.settings.set("chat_scope_enabled", scope_enabled)
                    self.settings.set("ignore_emoji_only", section.get("ignore_emoji_only", SETTING_DEFAULTS["ignore_emoji_only"]))
                    for key in IGNORE_KEYS:
                        self.settings.set(key, section.get(key, SETTING_DEFAULTS[key]))
                    if "regex_exceptions" in section:
                        self.settings.set("regex_exceptions", clean_regex_exceptions(section["regex_exceptions"]))
                    if "chat_type_rules" in section:
                        self.settings.set("chat_type_rules", dump_chat_type_rules(parse_chat_type_rules(section["chat_type_rules"])))
        self.plugin.refresh_chat_menu_item()

    def _apply_mask_section(self, section: dict):
        if "markdown_enabled" in section:
            markdown_enabled = section["markdown_enabled"]
            markdown_style = section.get("markdown_style", self.settings.markdown_style_value())
        elif "markdown_style" in section:
            markdown_style = section["markdown_style"]
            markdown_enabled = markdown_style != 1
        elif "markdown" in section:
            markdown_enabled, markdown_style = section["markdown"], 0
        else:
            markdown_enabled, markdown_style = self.settings.markdown_enabled(), self.settings.markdown_style_value()
        if markdown_style == 1:
            markdown_style = 0
        params = {
            "mask": section["value"],
            "markdown_style": markdown_style,
            "markdown_enabled": markdown_enabled,
            "text_style_enabled": bool(self.settings.get("text_style_enabled")),
            "text_style": clamp_int(self.settings.get("text_style"), 0, 0, TEXT_STYLE_COUNT - 1),
        }
        style = section.get("style")
        if isinstance(style, dict):
            params["text_style_enabled"], params["text_style"] = style["enabled"], style["value"]
        for key in ("mask", "markdown_style", "markdown_enabled", "text_style_enabled", "text_style"):
            self.settings.set(key, params[key])
        for key in ("text_style_random", "mask_rotation_enabled", "masks_list", "mask_rotation_mode", "conditional_masks", "text_style_translit", "style_words", "tag_lines"):
            if key in section:
                self.settings.set(key, section[key])

    def _export_candidates(self) -> List[Tuple[Optional[str], str]]:
        """Конфигурации открытой области (общий набор или пресеты аккаунта): [(id, имя)]."""
        configurations = self.plugin.configurations
        with configurations._lock:
            found = [(cid, configurations.selector_label(cid) or cid) for cid in configurations.selector_ids()]
        return found or [(None, "")]

    def _show_export_selection(self):
        """46.0.0: 1) выбор конфигов (до EXPORT_MAX_CONFIGS), 2) отдельный выбор частей для каждого конфига по очереди."""
        fragment, _ = self._activity()
        available = self.visible_components()
        if not available:
            return
        candidates = self._export_candidates()
        if len(candidates) <= 1:
            self._export_ask_parts(list(candidates), 0, [], available)
            return
        active = self.plugin.configurations.effective_selected_id()
        rows = [(name, cid == active, True) for cid, name in candidates]
        limit = self.EXPORT_MAX_CONFIGS

        def confirm(selected, extra_checked):
            if not selected:
                self._toast("config_export_none", fragment)
                return False
            if len(selected) > limit:
                self._toast("config_export_limit", fragment, n=limit)
                return False
            self._export_ask_parts([candidates[index] for index in selected], 0, [], available)
            return True

        self.plugin.show_checklist(
            self._tr("config_export_select"), rows, confirm,
            message=self._tr("config_export_select_subtext", n=limit),
            positive=self._tr("action_next"), fragment=fragment,
        )

    def _export_ask_parts(self, chosen, index, picked, available, preset=None):
        fragment, _ = self._activity()
        config_id, label = chosen[index]
        name = as_text((self.plugin.configurations._record(config_id) or {}).get("name")) or label
        total = len(chosen)
        last = index + 1 >= total
        rows = [(self._component_label(component), True, True) for component in available]
        message = self._tr("config_parts_message", n=len(available))
        title = self._tr("config_parts_title")
        if total > 1:
            title = self._tr("config_export_parts_title", name=label)
            message = self._tr("config_export_parts_progress", i=index + 1, n=total) + "\n\n" + message

        if preset is not None:
            chosen_parts, was_locked = preset
            rows = [(label, component in chosen_parts, enabled)
                    for (label, _checked, enabled), component in zip(rows, available)]
        else:
            was_locked = False

        def proceed(done):
            if last:
                self._export_deliver(done)
            else:
                self._export_ask_parts(chosen, index + 1, done, available)

        def confirm(selected, extra_checked):
            if not selected:
                self._toast("config_parts_none", fragment)
                return False
            components = tuple(available[position] for position in selected)
            if not extra_checked:
                proceed(picked + [(config_id, name, components, None)])
                return True
            run_on_ui_thread(lambda: self._ask_export_password(
                lambda password: proceed(picked + [(config_id, name, components, password)]),
                name=label if total > 1 else None,
                on_cancel=lambda: self._export_ask_parts(chosen, index, picked, available, (components, True)),
            ))
            return True

        self.plugin.show_checklist(
            title, rows, confirm, message=message,
            extra=(self._tr("config_export_encrypt"), was_locked),
            positive=self._tr("action_apply") if last else self._tr("action_next"), fragment=fragment,
        )

    def _export_deliver(self, items):
        """Один конфиг: спрашиваем, куда сохранить. Несколько: принудительно в Избранное активного аккаунта.
        items: [(config_id, имя, части, пароль или None)] - пароль у каждого конфига свой."""
        fragment, _ = self._activity()
        if not items or self._blocked(fragment, export=True):
            return
        if len(items) == 1:
            config_id, name, components, password = items[0]
            self._request_export(components, config_id, name, password)
        else:
            self._export_many_to_saved(items[: self.EXPORT_MAX_CONFIGS])

    def _request_export(self, components, config_id=None, name="", password: Optional[str] = None):
        _, activity = self._activity()
        if not activity or not components:
            return
        builder = AlertDialogBuilder(activity)
        builder.set_title(self._tr("config_export_destination_title"))
        builder.set_items(
            [self._tr("config_export_to_saved"), self._tr("config_export_to_device")],
            lambda bld, which: self._on_export_destination(bld, which, tuple(components), config_id, name, password),
        )
        builder.set_negative_button(self._tr("action_cancel"), lambda bld, which: bld.dismiss())
        self.plugin._show_builder(builder)

    def _on_export_destination(self, builder, which, components, config_id=None, name="", password=None):
        builder.dismiss()
        if which == 0:
            self._export_to_saved_messages(components, config_id, name, password)
        elif which == 1:
            self._request_export_to_device(components, config_id, name, password)

    @staticmethod
    def _file_stem(name) -> str:
        return re.sub(r"[^\w\-]+", "_", as_text(name), flags=re.UNICODE).strip("_")[:40]

    def _request_export_to_device(self, components, config_id=None, name="", password=None):
        _, activity = self._activity()
        if not activity:
            return
        self.pending_components = components
        self.pending_export_id = config_id
        self.pending_export_name = as_text(name)
        self.pending_export_password = password
        intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType("application/octet-stream")
        base = self._file_stem(name) or (components[0] if len(components) == 1 else "Prefixfy_config")
        intent.putExtra(Intent.EXTRA_TITLE, base + self.CONFIG_EXTENSION)
        self._awaiting = self.CONFIG_EXPORT_REQUEST_CODE
        activity.startActivityForResult(intent, self.CONFIG_EXPORT_REQUEST_CODE)

    def request_debug_export(self, path: str):
        _, activity = self._activity()
        if not activity:
            discard_file(path)
            return
        self.pending_debug_path = path
        intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType("text/plain")
        intent.putExtra(Intent.EXTRA_TITLE, os.path.basename(path))
        self._awaiting = self.DEBUG_EXPORT_REQUEST_CODE
        activity.startActivityForResult(intent, self.DEBUG_EXPORT_REQUEST_CODE)

    def _finish_debug_export(self, result_code, data):
        path, self.pending_debug_path = getattr(self, "pending_debug_path", None), None
        fragment, _ = self._activity()
        uri = data.getData() if data is not None and result_code == -1 else None
        if not path or uri is None:
            if path:
                discard_file(path)
            return

        def work():
            try:
                self._write_file_to_uri(uri, path)
                self._toast("debug_exported", fragment)
            except Exception as exc:
                self.plugin.log(f"Prefixfy debug export failed: {exc}")
                self._toast("debug_failed", fragment)
            finally:
                discard_file(path)

        threading.Thread(target=work, name="PrefixfyDebugExport", daemon=True).start()

    def _saved_messages_target(self):
        account = get_selected_account()
        if account is None:
            raise RuntimeError("active account is not available")
        user_config = get_user_config(account)
        current_user = user_config.getCurrentUser() if user_config else None
        user_id = java_int(getattr(current_user, "id", None)) if current_user is not None else None
        if not user_id or user_id <= 0:
            raise RuntimeError("active account user id is not available")
        return account, user_id

    def _export_to_saved_messages(self, components, config_id=None, name="", password=None):
        self._export_many_to_saved([(config_id, name, components, password)], single=True)

    def _export_many_to_saved(self, items, single: bool = False):
        fragment, _ = self._activity()
        try:
            account, user_id = self._saved_messages_target()
        except Exception as exc:
            self.plugin.log(f"Saved Messages export failed: {exc}")
            self._toast("config_export_failed", fragment)
            return
        if any(item[3] for item in items):
            self._toast("config_export_encrypting", fragment)

        def work():
            sent = 0
            for config_id, name, components, password in items:
                try:
                    path = self.build_config_file(components, temp_dir("exports"), config_id=config_id, name=name,
                                                  password=password)
                    send_document(user_id, path, caption="", account=account)
                    sent += 1
                except Exception as exc:
                    self.plugin.log(f"Saved Messages export of {config_id} failed: {exc}")
            if single:
                self._toast("config_export_done" if sent else "config_export_failed", fragment)
            elif sent == len(items):
                self._toast("config_export_done_multi", fragment, n=sent)
            elif sent:
                self._toast("config_export_partial", fragment, ok=sent, total=len(items))
            else:
                self._toast("config_export_failed", fragment)

        threading.Thread(target=work, name="PrefixfyExport", daemon=True).start()

    def _export_source(self, config_id):
        """None — живые настройки (активный конфиг), иначе сохранённые значения выбранного конфига."""
        configurations = self.plugin.configurations
        if not config_id or config_id == configurations.scope_active_id():
            return None
        with configurations._lock:
            record = configurations._record(config_id)
            if not record:
                raise ValueError("configuration is not available")
            return _SnapshotSettings(record.get("current"))

    def selected_data(self, components, media_ready: Optional[bool] = None, source=None, config_id=None, config_name=None) -> dict:
        s = source if source is not None else self.settings
        data = {"format": CONFIG_FORMAT, "version": CONFIG_VERSION}
        name = ConfigurationsManager.normalize_name(config_name) if config_name else ""
        if name:
            data["name"] = name
        if "language" in components:
            data["language"] = {"value": s.language_index()}
        if "mask" in components:
            data["mask"] = {
                "value": as_text(s.get("mask")),
                "markdown": s.markdown_enabled(),
                "markdown_enabled": s.markdown_enabled(),
                "markdown_style": s.markdown_style_value(),
                "style": {
                    "enabled": bool(s.get("text_style_enabled")),
                    "value": clamp_int(s.get("text_style"), 0, 0, TEXT_STYLE_COUNT - 1),
                },
                "text_style_random": bool(s.get("text_style_random")),
                "mask_rotation_enabled": bool(s.get("mask_rotation_enabled")),
                "masks_list": as_text(s.get("masks_list")),
                "mask_rotation_mode": clamp_int(s.get("mask_rotation_mode"), 0, 0, 1),
                "conditional_masks": as_text(s.get("conditional_masks")),
                "text_style_translit": bool(s.get("text_style_translit")),
                "style_words": as_text(s.get("style_words")),
                "tag_lines": as_text(s.get("tag_lines")),
            }
        if "separator" in components:
            data["separator"] = {
                "enabled": bool(s.get("separator_enabled")),
                "values": as_text(s.get("custom_emojis")),
                "count": s.separator_count(),
                "frequency": clamp_int(s.get("separator_frequency"), SEPARATOR_FREQUENCY_DEFAULT, 0, len(FREQUENCY_STEPS) - 1),
                "spaces": bool(s.get("separator_spaces")),
                "space_mode": clamp_int(s.get("separator_space_mode"), 0, 0, 2),
            }
        if "cute" in components:
            data["cute"] = {
                key: clamp_int(s.get(key), *CUTE_INT_KEYS[key]) if key in CUTE_INT_KEYS else bool(s.get(key))
                for key in CUTE_KEYS
            }
        if "exceptions" in components:
            scope_enabled = bool(s.get("chat_scope_enabled"))
            chats = as_text(s.get("disabled_chats"))
            data["exceptions"] = {
                "values": as_text(s.get("exceptions")),
                "disabled_chats": chats,
                "chat_scope_enabled": scope_enabled,
                "chat_scope": {"mode": "exceptions" if scope_enabled else "included", "chats": chats},
                "ignore_emoji_only": bool(s.get("ignore_emoji_only")),
                **{key: bool(s.get(key)) for key in IGNORE_KEYS},
                "regex_exceptions": as_text(s.get("regex_exceptions")),
                "chat_type_rules": dump_chat_type_rules(parse_chat_type_rules(s.get("chat_type_rules"))),
            }
        if "schedule" in components:
            data["schedule"] = self.plugin.export_schedule_section(config_id)
        if "media" in components:
            exists = self.media_exists(source) if media_ready is None else bool(media_ready)
            info = self.media_info(source) if exists else {"name": "", "mime": ""}
            data["media"] = {
                "enabled": bool(s.get("attached_media_enabled")) and exists,
                "file": "",
                "name": info["name"],
                "mime": info["mime"],
            }
        return data

    def build_config_file(self, components, directory: str, config_id=None, name="", password: Optional[str] = None) -> str:
        if not components:
            raise ValueError("no components selected")
        source = self._export_source(config_id)
        ensure_dir_exists(directory)
        self._prune_old_exports(directory)
        media_ready = "media" in components and self.media_exists(source)
        config = self.selected_data(
            components, media_ready=media_ready, source=source, config_id=config_id,
            config_name=name,
        )
        stem = self._file_stem(name)
        path = os.path.join(directory, f"Prefixfy_{stem + '_' if stem else ''}{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}{self.CONFIG_EXTENSION}")
        temp = path + ".tmp"
        try:
            with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                if media_ready:
                    entry = "media/attached_media" + safe_extension(config["media"]["name"])
                    config["media"]["file"] = entry
                    info = zipfile.ZipInfo(entry, date_time=time.localtime()[:6])
                    info.compress_type = zipfile.ZIP_STORED
                    with archive.open(info, "w", force_zip64=True) as stream:
                        read_media_plain(self.media_path(source), stream.write)
                payload = json.dumps(config, ensure_ascii=False, indent=2).encode("utf-8")
                if len(payload) > MAX_CONFIG_JSON_BYTES:
                    raise ValueError("configuration is too large to export")
                archive.writestr("config.json", payload)
            if password:
                lock_container(temp, path, password)
                discard_file(temp)
            else:
                os.replace(temp, path)
        except BaseException:
            discard_file(temp)
            raise
        return path

    @staticmethod
    def _prune_old_exports(directory: str):
        sweep_old_files(directory, EXPORT_TEMP_TTL)

    def _write_file_to_uri(self, uri, path):
        _, activity = self._activity()
        if not activity:
            raise IOError("activity unavailable")
        resolver = activity.getContentResolver()
        try:
            stream = resolver.openOutputStream(uri, "wt")
        except Exception:
            stream = resolver.openOutputStream(uri)
        if stream is None:
            raise IOError("cannot write configuration")
        try:
            with open(path, "rb") as handle:
                while True:
                    chunk = handle.read(64 * 1024)
                    if not chunk:
                        break
                    stream.write(chunk)
            stream.flush()
        finally:
            stream.close()

    def handle_activity_result(self, request_code, result_code, data) -> bool:
        if request_code not in (self.MEDIA_IMPORT_REQUEST_CODE, self.CONFIG_IMPORT_REQUEST_CODE, self.CONFIG_EXPORT_REQUEST_CODE,
                                self.DEBUG_EXPORT_REQUEST_CODE):
            return False
        if request_code == self.DEBUG_EXPORT_REQUEST_CODE:
            if self._awaiting != request_code:
                return False
            self._awaiting = None
            self._finish_debug_export(result_code, data)
            return True
        if self._awaiting != request_code:
            return False
        self._awaiting = None
        if self._blocked(export=request_code == self.CONFIG_EXPORT_REQUEST_CODE):
            self.pending_components, self.pending_import_as_new = (), False
            self.pending_export_id, self.pending_export_name = None, ""
            self.pending_export_password = None
            return True
        fragment, _ = self._activity()
        components, as_new = self.pending_components, self.pending_import_as_new
        export_id, export_name = self.pending_export_id, self.pending_export_name
        export_password = getattr(self, "pending_export_password", None)
        if request_code != self.MEDIA_IMPORT_REQUEST_CODE:
            self.pending_components, self.pending_import_as_new = (), False
            self.pending_export_id, self.pending_export_name = None, ""
            self.pending_export_password = None
        if request_code == self.CONFIG_IMPORT_REQUEST_CODE and self._import_locked(fragment):
            return True
        uri = data.getData() if (result_code == Activity.RESULT_OK and data is not None) else None
        if uri is None:
            return True

        _, activity = self._activity()
        resolver = activity.getContentResolver() if activity is not None else None

        def media_import():
            try:
                mime = ""
                try:
                    mime = as_text(resolver.getType(uri)) if resolver is not None else ""
                except Exception:
                    pass
                self.store_media_uri(uri, self._uri_display_name(uri) or "attached_media.bin", mime)
                self._toast("media_imported", fragment)
            except Exception as exc:
                self.plugin.log(f"Media import failed: {exc}")
                self._toast("media_import_failed", fragment)
            run_on_ui_thread(self.plugin.reload_settings_ui)

        def config_export():
            path = None
            if export_password:
                self._toast("config_export_encrypting", fragment)
            try:
                path = self.build_config_file(components, temp_dir("exports"), config_id=export_id, name=export_name,
                                              password=export_password)
                self._write_file_to_uri(uri, path)
                self._toast("config_export_done", fragment)
            except Exception as exc:
                self.plugin.log(f"Configuration export failed: {exc}")
                self._toast("config_export_failed", fragment)
            finally:
                if path and os.path.isfile(path):
                    delete_file(path)

        def config_import():
            try:
                temp_path = self._copy_uri_to_temp_file(uri)
            except Exception as exc:
                self.plugin.log(f"Configuration read failed: {exc}")
                self._toast("config_import_failed", fragment)
                return

            def cleanup():
                if temp_path and os.path.isfile(temp_path):
                    delete_file(temp_path)

            def opened(parsed):
                def show():
                    try:
                        self._import_opened_data(parsed, fragment, components, as_new)
                    except Exception as exc:
                        self.discard_container_media(parsed)
                        self.plugin.log(f"Configuration import dialog failed: {exc}")
                        self._toast("config_import_failed", fragment)

                run_on_ui_thread(show)

            self._open_container(temp_path, fragment, opened, cleanup)

        if request_code == self.MEDIA_IMPORT_REQUEST_CODE:
            work = media_import
        elif request_code == self.CONFIG_EXPORT_REQUEST_CODE:
            work = config_export
        else:
            work = config_import
        threading.Thread(target=work, name="PrefixfyTransfer", daemon=True).start()
        return True


class ConfigurationsManager:
    SELECTOR_KEY = "Prefixfy_experimental_configuration_selector"
    MEDIA_DIR_NAME = "Prefixfy_configurations"
    STORE_DIR_NAME = "Prefixfy_store"
    INDEX_NAME = "index.json"
    AUTOSAVE_DELAY_MS = 1500
    AUTOSAVE_RETRY_MS = 10000
    CONFIG_KEYS = tuple(SETTING_DEFAULTS)
    _ID_RE = re.compile(r"[A-Za-z0-9_\-]{1,64}")

    def __init__(self, plugin):
        self.plugin = plugin
        self.settings = plugin.settings
        self._ui_revision = 0
        self.generation = 0
        self._foreign_runtimes: Dict[str, Tuple[int, "Runtime"]] = {}
        self._foreign_lock = threading.Lock()
        self._lock = threading.RLock()
        self._autosave_dirty = False
        self._autosave_armed = False
        self._autosave_last_change = 0.0
        self._closed = False
        self._loading = False
        self._failed_writes = set()
        self._degraded = False
        self._acct_reset_visible: Optional[bool] = None
        self.media_dir = os.path.join(get_plugins_dir(), self.MEDIA_DIR_NAME)
        self.store_dir = os.path.join(get_plugins_dir(), self.STORE_DIR_NAME)
        ensure_dir_exists(self.media_dir)
        ensure_dir_exists(self.store_dir)
        VAULT.attach(plugin.log)
        VAULT.prepare()
        self.active_id = ""
        self.edit_uid: Optional[int] = self._stored_live_uid()
        self.accounts = AccountProfiles(self)
        self.configurations: Dict[str, dict] = {}
        self._load_store()
        legacy = plugin._legacy
        legacy.import_flat_configurations(self)
        self.accounts.load()
        legacy.convert_account_files(self)
        legacy.migrate_languages(self)
        if not self.configurations:
            baseline = self._snapshot_with_media("default", "baseline")
            self._store_record("default", {
                "name": plugin._tr("config_default_name"),
                "current": self._clone_with_media(baseline, "default", "current"),
                "baseline": baseline,
            })
            self.active_id = "default"
        elif self.active_id not in self.configurations:
            self.active_id = next(iter(self.configurations))
        self._dedupe_names()
        self._collect_orphan_media()
        self._write_index()

    @classmethod
    def _valid_id(cls, config_id) -> bool:
        return isinstance(config_id, str) and cls._ID_RE.fullmatch(config_id) is not None

    @staticmethod
    def _owner_of(config_id) -> Optional[int]:
        """uid аккаунта, которому принадлежит пресет с таким идентификатором; None — конфигурация общего набора."""
        match = _PRESET_ID_RE.fullmatch(config_id) if isinstance(config_id, str) else None
        if match is None:
            return None
        uid = int(match.group(1))
        return uid if str(uid) == match.group(1) and 0 < uid <= 2 ** 53 else None

    @classmethod
    def _id_belongs(cls, config_id, owner: Optional[int]) -> bool:
        return cls._valid_id(config_id) and cls._owner_of(config_id) == owner

    def _account_root(self, uid: int) -> str:
        return os.path.join(self.accounts.directory, str(int(uid)))

    def _root_of(self, config_id: str) -> str:
        owner = self._owner_of(config_id)
        return self.store_dir if owner is None else self._account_root(owner)

    def _config_dir(self, config_id: str) -> str:
        return os.path.join(self._root_of(config_id), config_id)

    def _bucket(self, config_id, create: bool = False) -> Dict[str, dict]:
        """Словарь, в котором лежит (или должна лежать) запись: общий набор или пресеты её аккаунта."""
        owner = self._owner_of(config_id)
        if owner is None:
            return self.configurations
        return self.accounts.bucket(owner, create)

    def _record(self, config_id) -> Optional[dict]:
        if not config_id:
            return None
        return self._bucket(config_id).get(config_id)

    def _bump(self, config_id: str):
        """Запись изменилась: кэши рантаймов, собранные по старому содержимому, больше не годятся."""
        if self._owner_of(config_id) is None:
            self.generation += 1
        else:
            self.accounts.invalidate()

    def _all_records(self) -> List[Tuple[str, dict]]:
        return list(self.configurations.items()) + self.accounts.all_records()

    def scope_records(self) -> Dict[str, dict]:
        """Список конфигураций открытой области: общий набор либо пресеты открытого аккаунта."""
        return self.configurations if self.edit_uid is None else self.accounts.bucket(self.edit_uid)

    def scope_active_id(self) -> Optional[str]:
        """Активная конфигурация открытой области. У аккаунта без своих пресетов её нет: он идёт за общим набором."""
        if self.edit_uid is None:
            return self.active_id
        return self.accounts.pin(self.edit_uid) or self.accounts.active_id(self.edit_uid)

    def _set_active(self, uid: Optional[int], config_id: Optional[str]):
        if uid is None:
            self.active_id = config_id or ""
        elif config_id:
            self.accounts.set_active(uid, config_id)

    def _shared_baseline(self, config_id: Optional[str] = None) -> dict:
        record = (
            (self.configurations.get(config_id) if config_id else None)
            or self.configurations.get(self.active_id)
            or next(iter(self.configurations.values()), None)
        )
        return dict((record or {}).get("baseline") or SETTING_DEFAULTS)

    def _param_path(self, config_id: str, role: str, key: str) -> str:
        return os.path.join(self._config_dir(config_id), role, key + ".json")

    ORIGIN_CREATED = "created"
    ORIGIN_IMPORTED = "imported"

    def _origin_path(self, config_id: str) -> str:
        return os.path.join(self._config_dir(config_id), "origin.json")

    def _name_path(self, config_id: str) -> str:
        return os.path.join(self._config_dir(config_id), "name.json")

    @staticmethod
    def _atomic_write(path: str, text: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        temp = unique_temp(path)
        try:
            payload = store_encode(path, text)
            with open(temp, "wb") as handle:
                handle.write(payload)
                handle.flush()
                try:
                    os.fsync(handle.fileno())
                except OSError:
                    pass
            os.replace(temp, path)
        except BaseException:
            discard_file(temp)
            raise

    @staticmethod
    def _clean_stale_temp(root: str):
        """При старте никто ещё не пишет: оставшиеся от прошлого сбоя .tmp-файлы можно убрать."""
        try:
            for folder, _dirs, files in os.walk(root):
                for entry in files:
                    if entry.endswith(".tmp"):
                        discard_file(os.path.join(folder, entry))
        except OSError:
            pass

    @staticmethod
    def _index_text(path: str) -> Optional[str]:
        """Текст индекса, если файл читается и действительно устроен как индекс (а не просто валидный json)."""
        try:
            raw = store_read_text(path)
            data = json.loads(raw)
            return raw if isinstance(data, dict) and isinstance(data.get("order"), list) else None
        except Exception:
            return None

    def seal_files(self) -> bool:
        """Запечатывает файлы хранилища (общие и аккаунтов), оставшиеся от версий без шифрования."""
        complete = True
        for root in (self.store_dir, self.accounts.directory):
            for folder, _dirs, files in os.walk(root):
                for entry in files:
                    if entry.endswith(".tmp") or not (entry.endswith(".json") or entry.endswith(".json.bak")):
                        continue
                    complete = seal_plain_file(os.path.join(folder, entry), self.plugin.log) and complete
        return complete

    def _read_json(self, path: str):
        if not os.path.isfile(path):
            return False, None
        try:
            return True, json.loads(store_read_text(path))
        except Exception as exc:
            self.plugin.log(f"Prefixfy store: cannot read {path}: {exc}")
            self._degraded = True
            return False, None

    def _read_index(self, root: Optional[str] = None) -> Optional[dict]:
        path = os.path.join(root or self.store_dir, self.INDEX_NAME)
        for candidate in (path, path + ".bak"):
            ok, data = self._read_json(candidate)
            if ok and isinstance(data, dict) and isinstance(data.get("order"), list):
                return data
        return None

    def _write_index(self, owner: Optional[int] = None) -> bool:
        if owner is None:
            root, active, order = self.store_dir, self.active_id, list(self.configurations)
        else:
            root, active, order = self._account_root(owner), self.accounts.active_id(owner) or "", self.accounts.ids(owner)
        path = os.path.join(root, self.INDEX_NAME)
        payload = json.dumps(
            {"version": 1, "active": active, "order": order},
            ensure_ascii=False, separators=(",", ":"),
        )
        try:
            previous = self._index_text(path)
            if previous is not None:
                self._atomic_write(path + ".bak", previous)
            self._atomic_write(path, payload)
            return True
        except Exception as exc:
            self.plugin.log(f"Prefixfy store: index write failed: {exc}")
            self._degraded = True
            return False

    def _read_params(self, config_id: str, role: str, fallback: Optional[dict]) -> Dict[str, Any]:
        result = {}
        for key in self.CONFIG_KEYS:
            default = fallback.get(key, SETTING_DEFAULTS[key]) if fallback is not None else SETTING_DEFAULTS[key]
            ok, value = self._read_json(self._param_path(config_id, role, key))
            result[key] = self._coerce(key, value) if ok else default
        return result

    def _read_record(self, config_id: str) -> Optional[dict]:
        directory = self._config_dir(config_id)
        if not os.path.isdir(directory):
            return None
        name_ok, name = self._read_json(self._name_path(config_id))
        if not name_ok and not os.path.isdir(os.path.join(directory, "current")):
            return None
        current = self._read_params(config_id, "current", None)
        baseline = self._read_params(config_id, "baseline", None)
        origin_ok, origin = self._read_json(self._origin_path(config_id))
        if not origin_ok or origin not in (self.ORIGIN_CREATED, self.ORIGIN_IMPORTED):
            origin = self.ORIGIN_CREATED
        return {"name": name if name_ok and isinstance(name, str) else "", "current": current, "baseline": baseline, "origin": origin}

    def _load_records(self, root: str, owner: Optional[int]) -> Tuple[Dict[str, dict], str]:
        """Записи из папки хранилища: общего набора (owner=None) или пресетов одного аккаунта. Возвращает (записи, активная)."""
        index = self._read_index(root)
        ids: List[str] = []
        if index:
            for config_id in index["order"]:
                if self._id_belongs(config_id, owner) and config_id not in ids:
                    ids.append(config_id)
        try:
            entries = sorted(os.listdir(root))
        except OSError as exc:
            self.plugin.log(f"Prefixfy store: listing failed: {exc}")
            entries = []
        for entry in entries:
            path = os.path.join(root, entry)
            if not os.path.isdir(path):
                continue
            if entry.endswith(".deleted"):
                shutil.rmtree(path, ignore_errors=True)
            elif entry in ids:
                continue
            elif self._id_belongs(entry, owner) and os.path.isfile(os.path.join(path, "name.json")):
                ids.append(entry)
            else:
                shutil.rmtree(path, ignore_errors=True)
        records: Dict[str, dict] = {}
        for config_id in ids:
            record = self._read_record(config_id)
            if record is not None:
                records[config_id] = record
        return records, (as_text(index.get("active")) if index else "")

    def _load_store(self):
        self._clean_stale_temp(self.store_dir)
        records, active = self._load_records(self.store_dir, None)
        self.configurations.update(records)
        self.active_id = active if active in self.configurations else ""

    def _sync_params(self, config_id: str, role: str, new: dict) -> bool:
        record = self._record(config_id)
        if record is None:
            return False
        old = record.get(role) or {}
        merged = {}
        all_ok = True
        for key in self.CONFIG_KEYS:
            value = self._coerce(key, new.get(key, old.get(key, SETTING_DEFAULTS[key])))
            merged[key] = value
            marker = (config_id, role, key)
            if (marker not in self._failed_writes and key in old
                    and old[key] == value and type(old[key]) is type(value)):
                continue
            try:
                self._atomic_write(self._param_path(config_id, role, key), json.dumps(value, ensure_ascii=False))
                self._failed_writes.discard(marker)
            except Exception as exc:
                all_ok = False
                self._failed_writes.add(marker)
                self._degraded = True
                self.plugin.log(f"Prefixfy store: write failed ({config_id}/{role}/{key}): {exc}")
        record[role] = merged
        self._bump(config_id)
        return all_ok

    def runtime_for(self, config_id: str) -> Optional["Runtime"]:
        generation = self.generation
        with self._foreign_lock:
            cached = self._foreign_runtimes.get(config_id)
            if cached is not None and cached[0] == generation:
                return cached[1]
        record = self.configurations.get(config_id)
        if not record:
            return None
        try:
            runtime = Runtime(RuntimeSettings(dict(record.get("current", {}))), config_id, self.plugin.log)
        except Exception as exc:
            self.plugin.log(f"Prefixfy runtime for configuration failed: {exc}")
            return None
        with self._foreign_lock:
            if len(self._foreign_runtimes) >= 16:
                self._foreign_runtimes.clear()
            self._foreign_runtimes[config_id] = (generation, runtime)
        return runtime

    def find_id_by_name(self, name: str) -> Optional[str]:
        wanted = self.normalize_name(name).casefold()
        for config_id, record in self.configurations.items():
            if as_text(record.get("name")).strip().casefold() == wanted:
                return config_id
        return None

    def _write_name(self, config_id: str) -> bool:
        record = self._record(config_id)
        if record is None:
            return False
        try:
            self._atomic_write(self._name_path(config_id), json.dumps(record["name"], ensure_ascii=False))
            return True
        except Exception as exc:
            self.plugin.log(f"Prefixfy store: name write failed ({config_id}): {exc}")
            return False

    def _store_record(self, config_id: str, record: dict) -> bool:
        """True только если записано всё. name.json пишется последним: он же признак целой записи."""
        origin = record.get("origin", self.ORIGIN_CREATED)
        with self.accounts._lock:
            self._bucket(config_id, True)[config_id] = {"name": as_text(record["name"]), "current": {}, "baseline": {}, "origin": origin}
        stored = self._sync_params(config_id, "current", record["current"])
        stored = self._sync_params(config_id, "baseline", record["baseline"]) and stored
        try:
            self._atomic_write(self._origin_path(config_id), json.dumps(origin))
        except Exception as exc:
            stored = False
            self.plugin.log(f"Prefixfy store: origin write failed ({config_id}): {exc}")
        if not stored:
            return False
        return self._write_name(config_id)

    def _discard_record(self, config_id: str):
        """Откат записи, которая не легла на диск целиком."""
        with self.accounts._lock:
            record = self._bucket(config_id).pop(config_id, None)
        self._failed_writes = {m for m in self._failed_writes if m[0] != config_id}
        tomb = self._bury(config_id)
        if tomb:
            shutil.rmtree(tomb, ignore_errors=True)
        if record:
            self._remove_media_of(record)

    def _bury(self, config_id: str) -> Optional[str]:
        path = self._config_dir(config_id)
        if not os.path.isdir(path):
            return None
        tomb = path + ".deleted"
        try:
            shutil.rmtree(tomb, ignore_errors=True)
            os.replace(path, tomb)
            return tomb
        except OSError:
            shutil.rmtree(path, ignore_errors=True)
            return None

    def _dedupe_names(self):
        self._dedupe_bucket(self.configurations)
        for uid in self.accounts.uids():
            self._dedupe_bucket(self.accounts.bucket(uid))

    def _dedupe_bucket(self, bucket: Dict[str, dict]):
        seen: List[str] = []
        for config_id, record in list(bucket.items()):
            base = self.normalize_name(record.get("name")) or self.plugin._tr("config_default_name")
            name = unique_name(base, seen)
            if name != record.get("name"):
                record["name"] = name
                self._write_name(config_id)
            seen.append(name)

    def _referenced_media(self) -> set:
        referenced = {os.path.abspath(as_text(self.settings.get("attached_media_path")))}
        for _config_id, data in self._all_records():
            for snapshot in (data.get("current", {}), data.get("baseline", {})):
                referenced.add(os.path.abspath(as_text(snapshot.get("attached_media_path"))))
        return referenced

    def _collect_orphan_media(self):
        if self._degraded or self.accounts.degraded:
            return
        referenced = self._referenced_media()
        directories = [self.media_dir]
        transfer = getattr(self.plugin, "transfer", None)
        if transfer is not None:
            directories.append(transfer.media_data_dir)
        stale = time.time() - STALE_TMP_AGE
        for directory in directories:
            try:
                for entry in os.listdir(directory):
                    path = os.path.abspath(os.path.join(directory, entry))
                    if not os.path.isfile(path):
                        continue
                    if entry.endswith(".tmp"):
                        if os.path.getmtime(path) < stale:
                            delete_file(path)
                    elif path not in referenced:
                        delete_file(path)
            except OSError as exc:
                self.plugin.log(f"Configuration media cleanup failed: {exc}")

    @staticmethod
    def _coerce(key: str, value):
        default = SETTING_DEFAULTS[key]
        if isinstance(default, bool):
            return value if isinstance(value, bool) else default
        if isinstance(default, int):
            return clamp_int(value, default, -2 ** 31, 2 ** 31 - 1)
        return sanitize_text(value) if isinstance(value, str) and len(value) <= MAX_SETTING_TEXT else default

    def _snapshot(self) -> Dict[str, Any]:
        return {key: self._coerce(key, self.settings.get(key, SETTING_DEFAULTS[key])) for key in self.CONFIG_KEYS}

    def _copy_media(self, source: str, config_id: str, role: str) -> Optional[str]:
        if (not source or not self._valid_id(config_id) or not is_media_store_file(source)
                or not os.path.isfile(source)):
            return None
        suffix = "-baseline" if role == "baseline" else ""
        target = os.path.join(self.media_dir, f"{config_id}{suffix}{safe_extension(source) or '.bin'}")
        if os.path.abspath(source) != os.path.abspath(target) and not self._is_fresh_copy(source, target):
            temp = unique_temp(target)
            try:
                try:
                    shutil.copy2(source, temp)
                except OSError:
                    shutil.copyfile(source, temp)
                os.replace(temp, target)
            except BaseException:
                discard_file(temp)
                raise
        return target

    @staticmethod
    def _is_fresh_copy(source: str, target: str) -> bool:
        try:
            if not os.path.isfile(target):
                return False
            first, second = os.stat(source), os.stat(target)
            return first.st_size == second.st_size and abs(first.st_mtime - second.st_mtime) <= 0.002
        except OSError:
            return False

    def _clone_with_media(self, snapshot, config_id, role="current") -> Dict[str, Any]:
        cloned = dict(snapshot or {})
        try:
            target = self._copy_media(as_text(cloned.get("attached_media_path")), config_id, role)
            if target:
                cloned["attached_media_path"] = target
        except Exception as exc:
            self.plugin.log(f"Configuration media copy failed: {exc}")
        return cloned

    def _snapshot_with_media(self, config_id, role="current") -> Dict[str, Any]:
        data = self._clone_with_media(self._snapshot(), config_id, role)
        if not data.get("attached_media_enabled", False) and not os.path.isfile(as_text(data.get("attached_media_path"))):
            data["attached_media_path"] = ""
        return data

    def _remove_media_of(self, record: dict):
        referenced = self._referenced_media()
        for snapshot in (record.get("current", {}), record.get("baseline", {})):
            path = as_text(snapshot.get("attached_media_path"))
            if (path and os.path.abspath(path) not in referenced and is_media_store_file(path)
                    and os.path.isfile(path)):
                discard_file(path)

    def _restore_live(self, snapshot):
        try:
            self._load_snapshot(snapshot)
        except Exception as exc:
            self.plugin.log(f"Prefixfy live settings restore failed: {exc}")

    def _current(self, config_id=None) -> dict:
        record = self._record(config_id) if config_id else self.configurations.get(self.active_id)
        return (record or {}).get("current", {})

    def _load_snapshot(self, data):
        self._loading = True
        try:
            with self.plugin.runtime_manager.bulk():
                for key in self.CONFIG_KEYS:
                    if key in data:
                        self.settings.set(key, data[key])
        finally:
            self._loading = False

    def save_active(self) -> bool:
        with self._lock:
            self._autosave_dirty = False
            uid = self.edit_uid
            if uid is not None:
                saved = self._save_account(uid)
                if not saved:
                    self._autosave_dirty = True
                return saved
            if self.active_id not in self.configurations:
                return True
            saved = self._sync_params(self.active_id, "current", self._snapshot_with_media(self.active_id, "current"))
            if not saved:
                self._autosave_dirty = True
            return saved

    def _save_account(self, uid: int) -> bool:
        """Живые настройки — в активный пресет аккаунта. Пока пресетов нет и настройки совпадают с общими, ничего не пишем."""
        pinned = self.accounts.pin(uid)
        if pinned:
            if self._same_as_shared(self._snapshot(), pinned):
                return True
            return self._fork_account(uid) is not None
        config_id = self.accounts.active_id(uid)
        if config_id is None:
            if self._same_as_shared(self._snapshot()):
                return True
            return self._fork_account(uid) is not None
        return self._sync_params(config_id, "current", self._snapshot_with_media(config_id, "current"))

    def _fork_account(self, uid: int, avoid=()) -> Optional[str]:
        """Первый собственный пресет аккаунта: копия живых настроек. Baseline — как у активной общей конфигурации,
        чтобы «сброс» возвращал то, что аккаунт получил от общего набора. avoid — имена, которые нельзя занять."""
        pinned = self.accounts.pin(uid)
        config_id = self._new_id(uid)
        taken = list(avoid) + [as_text(item.get("name")) for item in list(self.accounts.bucket(uid).values())]
        base_name = as_text((self._record(pinned) or {}).get("name")) if pinned else ""
        record = {
            "name": unique_name(base_name or self.plugin._tr("config_default_name"), taken),
            "current": self._snapshot_with_media(config_id, "current"),
            "baseline": self._clone_with_media(self._shared_baseline(pinned), config_id, "baseline"),
        }
        if not self._store_record(config_id, record):
            self._discard_record(config_id)
            return None
        self.accounts.set_active(uid, config_id)
        if pinned:
            self.accounts.set_pin(uid, None)
        self._write_index(uid)
        return config_id

    def _retry_later(self):
        with self._lock:
            self._autosave_dirty = True
            if not self._closed and not self._autosave_armed:
                self._arm_autosave(self.AUTOSAVE_RETRY_MS)

    def _save_active_checked(self) -> bool:
        try:
            saved = self.save_active()
        except Exception as exc:
            self.plugin.log(f"Prefixfy save_active failed: {exc}")
            saved = False
        if not saved:
            self._retry_later()
        return saved

    def _require_saved(self):
        if not self._save_active_checked():
            raise ConfigurationSaveError("active configuration could not be saved")

    def schedule_autosave(self):
        if self._loading:
            return
        with self._lock:
            if self._closed:
                return
            self._autosave_dirty = True
            self._autosave_last_change = time.monotonic()
            if not self._autosave_armed:
                self._arm_autosave(self.AUTOSAVE_DELAY_MS)

    def _arm_autosave(self, delay_ms: int):
        self._autosave_armed = True
        ref = weakref.ref(self)

        def task():
            manager = ref()
            if manager is not None:
                manager._autosave_tick()

        try:
            run_on_queue(task, PLUGINS_QUEUE, max(1, int(delay_ms)))
        except Exception as exc:
            self._autosave_armed = False
            self.plugin.log(f"Prefixfy autosave scheduling failed: {exc}")

    def _autosave_tick(self):
        refresh = False
        with self._lock:
            self._autosave_armed = False
            if self._closed or not self._autosave_dirty:
                return
            remaining = self.AUTOSAVE_DELAY_MS / 1000.0 - (time.monotonic() - self._autosave_last_change)
            if remaining > 0.02:
                self._arm_autosave(remaining * 1000 + 1)
                return
            try:
                saved = self.save_active()
            except Exception as exc:
                self.plugin.log(f"Prefixfy autosave failed: {exc}")
                saved = False
            if not saved:
                self._autosave_dirty = True
                self._arm_autosave(self.AUTOSAVE_RETRY_MS)
            elif self.edit_uid is not None and self._acct_reset_visible is not None:
                try:
                    refresh = self.account_differs(self.edit_uid) != self._acct_reset_visible
                except Exception as exc:
                    self.plugin.log(f"Prefixfy account reset visibility check failed: {exc}")
        if refresh:
            try:
                self.plugin.reload_settings_ui()
            except Exception as exc:
                self.plugin.log(f"Prefixfy settings refresh failed: {exc}")

    def shutdown(self):
        with self._lock:
            try:
                if not self.save_active():
                    self.plugin.log("Prefixfy final save failed: changes since the last successful write may be lost")
            except Exception as exc:
                self.plugin.log(f"Prefixfy final save raised: {exc}")
            finally:
                self._closed = True
                self._autosave_dirty = False
        with self._foreign_lock:
            self._foreign_runtimes.clear()
        self.accounts.invalidate()

    @property
    def selector_key(self) -> str:
        return f"{self.SELECTOR_KEY}_{self._ui_revision}"

    def _refresh_ui(self):
        self._ui_revision += 1
        self.plugin.reload_settings_ui()

    def selector_items(self) -> List[str]:
        return [as_text(data.get("name", key)) for key, data in self.scope_records().items()]

    def selector_index(self) -> int:
        keys = list(self.scope_records())
        active = self.scope_active_id()
        return keys.index(active) if active in keys else 0

    def selector_ids(self) -> List[str]:
        """46.5.0: что показывает выбор конфигурации. В общем наборе — он сам, у аккаунта — общие конфигурации и его пресеты."""
        shared = list(self.configurations)
        if self.edit_uid is None:
            return shared
        return shared + list(self.accounts.bucket(self.edit_uid))

    def selector_label(self, config_id: str) -> str:
        name = as_text((self._record(config_id) or {}).get("name", config_id))
        if self.edit_uid is not None and self._owner_of(config_id) is None:
            return f"{name} • {self.plugin._tr('config_shared_marker')}"
        return name

    def selector_display_items(self) -> List[str]:
        return [self.selector_label(config_id) for config_id in self.selector_ids()]

    def effective_selected_id(self) -> str:
        """Что выбрано в списке: у аккаунта без своих пресетов и выбора — активная общая конфигурация."""
        if self.edit_uid is None:
            return self.active_id
        return self.accounts.pin(self.edit_uid) or self.accounts.active_id(self.edit_uid) or self.active_id

    def selector_display_index(self) -> int:
        ids = self.selector_ids()
        selected = self.effective_selected_id()
        return ids.index(selected) if selected in ids else 0

    def _activate(self, config_id: str):
        with self._lock:
            uid = self.edit_uid
            previous = self.active_id if uid is None else self.accounts.active_id(uid)
            previous_pin = self.accounts.pin(uid) if uid is not None else None
            self._autosave_dirty = False
            if previous_pin:
                self.accounts.set_pin(uid, None)
            self._set_active(uid, config_id)
            try:
                self._load_snapshot(self._target_snapshot())
            except Exception:
                self._set_active(uid, previous)
                if previous_pin:
                    self.accounts.set_pin(uid, previous_pin)
                self._restore_live(self._target_snapshot())
                raise
            self._write_index(uid)
            self._collect_orphan_media()
        self.plugin.refresh_chat_menu_item()
        self._refresh_ui()

    def switch(self, index):
        with self._lock:
            keys = self.selector_ids()
            if not _is_int(index) or not 0 <= index < len(keys) or keys[index] == self.effective_selected_id():
                return
            if not self._save_active_checked():
                self.plugin._toast("config_save_failed")
                self._refresh_ui()
                return
            target = keys[index]
            uid = self.edit_uid
            if uid is not None and self._owner_of(target) is None:
                self._pin_shared(uid, target)
            else:
                self._activate(target)

    def _pin_shared(self, uid: int, config_id: str):
        """46.5.0: аккаунт переходит на общую конфигурацию по ссылке; первая его правка сделает собственную копию."""
        previous_pin = self.accounts.pin(uid)
        self._autosave_dirty = False
        self.accounts.set_pin(uid, config_id)
        try:
            self._load_snapshot(self._target_snapshot())
        except Exception:
            self.accounts.set_pin(uid, previous_pin)
            self._restore_live(self._target_snapshot())
            raise
        self.plugin.refresh_chat_menu_item()
        self._refresh_ui()

    def _new_id(self, owner: Optional[int] = None) -> str:
        prefix = "config_" if owner is None else f"acc{int(owner)}_"
        while True:
            config_id = prefix + uuid.uuid4().hex[:8]
            if config_id not in self._bucket(config_id) and not os.path.exists(self._config_dir(config_id)):
                return config_id

    @staticmethod
    def normalize_name(name) -> str:
        return " ".join(sanitize_text(as_text(name)).split())[:MAX_CONFIG_NAME_LENGTH].strip()

    def is_name_taken(self, name, ignore_id=None) -> bool:
        """Имена уникальны в пределах области: общего набора или пресетов одного аккаунта."""
        key = self.normalize_name(name).casefold()
        owner = self._owner_of(ignore_id) if ignore_id else self.edit_uid
        records = self.configurations if owner is None else self.accounts.bucket(owner)
        return any(
            as_text(data.get("name", config_id)).strip().casefold() == key
            for config_id, data in list(records.items())
            if config_id != ignore_id
        )

    def name_error(self, name, ignore_id=None) -> Optional[str]:
        name = self.normalize_name(name)
        if not name:
            return "config_name_invalid"
        if self.is_name_taken(name, ignore_id):
            return "config_name_taken"
        return None

    def add(self, name: str, copy_current: bool = False):
        with self._lock:
            uid = self.edit_uid
            name = self.normalize_name(name)
            if name and self.is_name_taken(name):
                raise ConfigurationError("configuration name is already taken")
            self._require_saved()
            self._ensure_account_preset(uid, avoid=[name] if name else [])
            taken = self.selector_items()
            if not name:
                name = unique_name(self.plugin._tr("config_numbered_name", n=len(taken) + 1), taken)
            config_id = self._new_id(uid)
            if copy_current:
                source = self._current(self.scope_active_id())
                record = {
                    "name": name,
                    "current": self._clone_with_media(source, config_id, "current"),
                    "baseline": self._clone_with_media(source, config_id, "baseline"),
                }
            else:
                record = {"name": name, "current": dict(SETTING_DEFAULTS), "baseline": dict(SETTING_DEFAULTS)}
            if not self._store_record(config_id, record):
                self._discard_record(config_id)
                raise ConfigurationSaveError("configuration could not be stored")
            self._activate(config_id)

    def _ensure_account_preset(self, uid: Optional[int], avoid=()):
        """Перед добавлением новой конфигурации аккаунту без своих пресетов нужен первый: то, что он использует сейчас."""
        if uid is None:
            return
        if self.accounts.active_id(uid) is None or self.accounts.pin(uid):
            if len(self.accounts.ids(uid)) >= MAX_ACCOUNT_PRESETS:
                raise ConfigurationError("too many configurations for the account")
            if self._fork_account(uid, avoid) is None:
                raise ConfigurationSaveError("account configuration could not be stored")
        if len(self.accounts.ids(uid)) >= MAX_ACCOUNT_PRESETS:
            raise ConfigurationError("too many configurations for the account")

    def create_from_import(self, data, components, name=None):
        with self._lock:
            uid = self.edit_uid
            name = self.normalize_name(name)
            if name and self.is_name_taken(name):
                raise ConfigurationError("configuration name is already taken")
            self._require_saved()
            self._ensure_account_preset(uid, avoid=[name] if name else [])
            if not name:
                name = unique_name(self.plugin._tr("config_imported_name"), self.selector_items())
            previous = self._snapshot()
            config_id = None
            try:
                self._load_snapshot(SETTING_DEFAULTS)
                self.plugin.transfer.apply_components(data, components)
                config_id = self._new_id(uid)
                baseline = self._snapshot_with_media(config_id, "baseline")
                stored = self._store_record(config_id, {
                    "name": name,
                    "current": self._clone_with_media(baseline, config_id, "current"),
                    "baseline": baseline,
                    "origin": self.ORIGIN_IMPORTED,
                })
            except Exception:
                if config_id:
                    self._discard_record(config_id)
                self._restore_live(previous)
                raise
            if not stored:
                self._discard_record(config_id)
                self._restore_live(previous)
                raise ConfigurationSaveError("imported configuration could not be stored")
            self._activate(config_id)

    def is_imported(self, config_id: Optional[str] = None) -> bool:
        record = self._record(config_id or self.scope_active_id()) or {}
        return record.get("origin") == self.ORIGIN_IMPORTED

    def _setup_finished(self) -> bool:
        try:
            return self.plugin._setup_stage() >= SETUP_DONE
        except Exception:
            return False

    def import_data(self, data, components, as_new=False, name=None):
        if not self._setup_finished():
            raise ConfigurationError("initial setup is not finished")
        remote = getattr(self.plugin, "remote", None)
        if remote is not None and not remote.allows():
            raise ConfigurationError("plugin update required")
        if not FEATURES.on("config_import"):
            raise ConfigurationError("configuration import is switched off")
        shared_target = self.edit_uid is None
        if as_new:
            self.create_from_import(data, components, name=name)
        else:
            with self._lock:
                before = self._snapshot()
                try:
                    self.plugin.transfer.apply_components(data, components)
                except Exception:
                    self._restore_live(before)
                    raise
                if not self._save_active_checked():
                    self.plugin.log("Prefixfy import applied but not yet saved: retry scheduled")
        if "schedule" in components and (shared_target or not as_new):
            section = extract_component(data, "schedule")
            if section is not None:
                new_name = as_text((self.configurations.get(self.active_id) or {}).get("name")) if as_new else None
                self.plugin.import_schedule_section(section, new_name)

    def rename(self, config_id, name) -> bool:
        with self._lock:
            config_id = str(config_id)
            record = self._record(config_id)
            if self.edit_uid is not None and self._owner_of(config_id) != self.edit_uid:
                return False
            if record is None or self.name_error(name, ignore_id=config_id):
                return False
            old_name = as_text(record.get("name"))
            record["name"] = self.normalize_name(name)
            if not self._write_name(config_id):
                record["name"] = old_name
                return False
            self._bump(config_id)
            new_name = record["name"]
        if self._owner_of(config_id) is None:
            self.plugin.rename_in_schedule(old_name, new_name)
        self._refresh_ui()
        return True

    def rename_imported(self, uid, config_id, name) -> bool:
        """48.1.0: переименование импортированной конфигурации в её области (None — общий набор, иначе uid аккаунта).
        Если имя занято другой конфигурацией области, добавляется номер."""
        with self._lock:
            origin = self.edit_uid
            self.edit_uid = uid
            try:
                records = self.configurations if uid is None else self.accounts.bucket(uid)
                if config_id not in records:
                    return False
                base = self.normalize_name(name)[:MAX_CONFIG_NAME_LENGTH - 4].strip()
                taken = [as_text(data.get("name", cid)) for cid, data in list(records.items()) if cid != config_id]
                return self.rename(config_id, unique_name(base, taken))
            finally:
                self.edit_uid = origin
                self._refresh_ui()

    def inactive_ids(self) -> List[str]:
        active = self.scope_active_id()
        return [config_id for config_id in self.scope_records() if config_id != active]

    def delete_many(self, config_ids) -> int:
        with self._lock:
            owner = self.edit_uid
            records = self.scope_records()
            active = self.scope_active_id()
            selected = [cid for cid in dict.fromkeys(str(c) for c in config_ids)
                        if cid in records and cid != active]
            if not selected:
                return 0
            removed = []
            tombs = []
            for config_id in selected:
                tomb = self._bury(config_id)
                if tomb:
                    tombs.append(tomb)
                with self.accounts._lock:
                    removed.append(records.pop(config_id))
            self._failed_writes = {m for m in self._failed_writes if m[0] not in selected}
            self._write_index(owner)
            for tomb in tombs:
                shutil.rmtree(tomb, ignore_errors=True)
            for record in removed:
                self._remove_media_of(record)
        if owner is None:
            self.generation += 1
            self.plugin.prune_chat_bindings()
        else:
            self.accounts.invalidate()
            self.plugin.prune_chat_bindings()
        self._refresh_ui()
        self.plugin._toast("config_deleted", n=len(selected))
        return len(selected)

    def reset_active_components(self, components, plugin_defaults: bool = False):
        with self._lock:
            failed = not self._save_active_checked()
            if not failed:
                uid = self.edit_uid
                config_id = self.scope_active_id()
                if uid is not None and (config_id is None or self._owner_of(config_id) != uid):
                    config_id = self._fork_account(uid)
                    failed = config_id is None
            if not failed:
                config = self._record(config_id)
                if not config:
                    self.plugin._toast("config_save_failed")
                    return
                baseline = config.get("baseline", {})
                if plugin_defaults and self.is_imported(config_id):
                    baseline = dict(SETTING_DEFAULTS)
                current = dict(config.get("current", {}))
                for component in components:
                    for key in COMPONENT_KEYS.get(component, ()):
                        if key in baseline:
                            current[key] = baseline[key]
                if "media" in components:
                    baseline_media = as_text(baseline.get("attached_media_path"))
                    if baseline.get("attached_media_enabled", False) and os.path.isfile(baseline_media):
                        current["attached_media_path"] = self._clone_with_media(
                            {"attached_media_path": baseline_media}, config_id, "current"
                        ).get("attached_media_path", "")
                    elif not baseline.get("attached_media_enabled", False):
                        current["attached_media_path"] = ""
                if not self._sync_params(config_id, "current", current):
                    self._retry_later()
                self._load_snapshot(current)
        if failed:
            self.plugin._toast("config_save_failed")
            return
        if "schedule" in components:
            try:
                self.plugin.reset_schedule_section()
            except Exception as exc:
                self.plugin.log(f"Prefixfy schedule reset failed: {exc}")
        self.plugin.refresh_chat_menu_item()
        self._refresh_ui()
        self.plugin._toast("config_restored")

    @property
    def acct_selector_key(self) -> str:
        return f"{ACCT_SELECTOR_KEY}_{self._ui_revision}"

    def live_config_id(self) -> str:
        if self.edit_uid is None:
            return self.active_id
        return self.accounts.pin(self.edit_uid) or self.accounts.active_id(self.edit_uid) or f"acc_{self.edit_uid}"

    def _stored_live_uid(self) -> Optional[int]:
        try:
            raw = as_text(self.plugin.get_setting(ACCT_LIVE_KEY, "")).strip()
        except Exception:
            return None
        if not _ACCOUNT_ID_RE.fullmatch(raw):
            return None
        value = int(raw)
        return value if 0 < value <= 2 ** 53 else None

    def _write_live_marker(self):
        try:
            self.plugin.set_setting(ACCT_LIVE_KEY, "" if self.edit_uid is None else str(self.edit_uid))
        except Exception as exc:
            self.plugin.log(f"Prefixfy account marker failed: {exc}")

    def _target_snapshot(self) -> dict:
        """Что должно лежать в живых настройках: активный пресет открытого аккаунта, а без него — активная общая конфигурация."""
        if self.edit_uid is not None:
            pinned = self.accounts.pin(self.edit_uid)
            if pinned:
                return self._current(pinned)
            record = self.accounts.active_record(self.edit_uid)
            if record is not None:
                return record.get("current") or {}
        return self._current(self.active_id)

    def _params_signature(self, params) -> tuple:
        """Параметры конфигурации для сравнения. Путь к медиа у каждой конфигурации свой (копия файла), поэтому
        сравнивается только наличие вложения, а не путь."""
        params = params if isinstance(params, dict) else {}
        signature = []
        for key in self.CONFIG_KEYS:
            value = self._coerce(key, params.get(key, SETTING_DEFAULTS[key]))
            signature.append(bool(value) if key == "attached_media_path" else value)
        return tuple(signature)

    def account_differs(self, uid) -> bool:
        """True, если у аккаунта есть свои конфигурации и они отличаются от общего набора: числом, порядком, именами,
        параметрами или выбранной активной конфигурацией. Без своих конфигураций аккаунт идёт за общим набором: False."""
        if uid is None:
            return False
        with self._lock:
            if self.accounts.pin(uid):
                return True
            own_ids = self.accounts.ids(uid)
            if not own_ids:
                return False
            shared_ids = list(self.configurations)
            if len(own_ids) != len(shared_ids):
                return True
            own = self.accounts.bucket(uid)
            own_active = self.accounts.active_id(uid)
            live = self._snapshot() if uid == self.edit_uid else None
            for own_id, shared_id in zip(own_ids, shared_ids):
                own_record = own.get(own_id) or {}
                shared_record = self.configurations.get(shared_id) or {}
                if as_text(own_record.get("name")) != as_text(shared_record.get("name")):
                    return True
                own_params = live if (live is not None and own_id == own_active) else own_record.get("current")
                if self._params_signature(own_params) != self._params_signature(shared_record.get("current")):
                    return True
            shared_active = self.active_id if self.active_id in self.configurations else shared_ids[0]
            return own_ids.index(own_active) != shared_ids.index(shared_active)

    def account_reset_available(self, uid) -> bool:
        """Показывать ли пункт «Сбросить к общим настройкам». При сбое сравнения пункт показывается: сброс безопасен."""
        try:
            available = self.account_differs(uid)
        except Exception as exc:
            self.plugin.log(f"Prefixfy account comparison failed: {exc}")
            available = self.accounts.has(uid)
        self._acct_reset_visible = available
        return available

    def _same_as_shared(self, snapshot: dict, config_id: Optional[str] = None) -> bool:
        shared = self._current(config_id or self.active_id)
        return all(
            snapshot.get(key) == self._coerce(key, shared.get(key, SETTING_DEFAULTS[key]))
            for key in self.CONFIG_KEYS
        )

    def _switch_live(self, uid: Optional[int]):
        previous = self.edit_uid
        self.edit_uid = uid
        try:
            self._load_snapshot(self._target_snapshot())
        except Exception:
            self.edit_uid = previous
            self._restore_live(self._target_snapshot())
            raise
        self._write_live_marker()

    def resolve_target(self) -> Optional[int]:
        plugin = self.plugin
        if not plugin._acct_on():
            return None
        raw = as_text(plugin.get_setting(ACCT_TARGET_KEY, ACCT_AUTO)).strip()
        accounts = plugin._accounts()
        if raw == ACCT_AUTO:
            return accounts.get(plugin._current_account_slot())
        if _ACCOUNT_ID_RE.fullmatch(raw) and int(raw) in accounts.values():
            return int(raw)
        return None

    def sync_target(self) -> bool:
        with self._lock:
            uid = self.resolve_target()
            if uid == self.edit_uid:
                return False
            if not self._save_active_checked():
                return False
            self._switch_live(uid)
        self.plugin.refresh_chat_menu_item()
        return True

    def reset_account(self):
        failed = False
        with self._lock:
            uid = self.edit_uid
            if uid is None:
                return
            self._autosave_dirty = False
            if (self.accounts.has(uid) or self.accounts.pin(uid)) and not self.accounts.delete(uid):
                failed = True
            self._load_snapshot(self._target_snapshot())
        self.plugin.prune_chat_bindings()
        self.plugin.refresh_chat_menu_item()
        self._refresh_ui()
        self.plugin._toast("config_save_failed" if failed else "account_reset_done")

    def _import_into(self, uid: Optional[int], data, components):
        self._switch_live(uid)
        self.plugin.transfer.apply_components(data, components)
        if not self._save_active_checked():
            if uid is not None:
                raise ConfigurationSaveError("account configuration could not be saved")
            self.plugin.log("Prefixfy import applied but not yet saved: retry scheduled")

    def import_to_accounts(self, data, components, target):
        """target: ACCT_ALL (общий набор + все свои наборы), ACCT_COMMON или user_id аккаунта."""
        if not self._setup_finished():
            raise ConfigurationError("initial setup is not finished")
        remote = getattr(self.plugin, "remote", None)
        if remote is not None and not remote.allows():
            raise ConfigurationError("plugin update required")
        if not FEATURES.on("config_import"):
            raise ConfigurationError("configuration import is switched off")
        present = set(self.plugin._accounts().values())
        if target == ACCT_ALL:
            plan = [None] + [uid for uid in self.accounts.uids() if uid in present]
        elif target == ACCT_COMMON:
            plan = [None]
        elif isinstance(target, int) and not isinstance(target, bool) and target in present:
            plan = [target]
        else:
            raise ConfigurationError("unknown import target")
        with self._lock:
            if not self._save_active_checked():
                raise ConfigurationSaveError("active configuration could not be saved")
            origin = self.edit_uid
            try:
                for uid in plan:
                    self._import_into(uid, data, components)
            finally:
                try:
                    self._switch_live(origin)
                except Exception as exc:
                    self.plugin.log(f"Prefixfy live set restore after import failed: {exc}")
        if "schedule" in components:
            section = extract_component(data, "schedule")
            if section is not None:
                self.plugin.import_schedule_section(section, None)
        self.plugin.refresh_chat_menu_item()

    def scope_names(self, uid) -> List[str]:
        """Названия конфигураций набора аккаунта uid (None — общий набор), не переключая живые настройки."""
        with self._lock:
            origin = self.edit_uid
            self.edit_uid = uid
            try:
                return self.selector_items()
            finally:
                self.edit_uid = origin

    def name_error_in(self, uid, name):
        with self._lock:
            origin = self.edit_uid
            self.edit_uid = uid
            try:
                return self.name_error(name)
            finally:
                self.edit_uid = origin

    def import_new_to_account(self, data, components, name, target):
        """Импорт как новая конфигурация в наборе target: user_id аккаунта или ACCT_COMMON (общий набор)."""
        if not self._setup_finished():
            raise ConfigurationError("initial setup is not finished")
        remote = getattr(self.plugin, "remote", None)
        if remote is not None and not remote.allows():
            raise ConfigurationError("plugin update required")
        if not FEATURES.on("config_import"):
            raise ConfigurationError("configuration import is switched off")
        present = set(self.plugin._accounts().values())
        if target == ACCT_COMMON:
            uid = None
        elif isinstance(target, int) and not isinstance(target, bool) and target in present:
            uid = target
        else:
            raise ConfigurationError("unknown import target")
        new_name = None
        with self._lock:
            if not self._save_active_checked():
                raise ConfigurationSaveError("active configuration could not be saved")
            origin = self.edit_uid
            try:
                self._switch_live(uid)
                self.create_from_import(data, components, name=name)
                if uid is None:
                    new_name = as_text((self.configurations.get(self.active_id) or {}).get("name"))
            finally:
                try:
                    self._switch_live(origin)
                except Exception as exc:
                    self.plugin.log(f"Prefixfy live set restore after import failed: {exc}")
        if uid is None and "schedule" in components:
            section = extract_component(data, "schedule")
            if section is not None:
                self.plugin.import_schedule_section(section, new_name)
        self.plugin.refresh_chat_menu_item()

    def request_add(self, view=None):
        def confirm(value, editor):
            name = self.normalize_name(value)
            if name:
                error = self.name_error(name)
                if error:
                    editor.setError(self.plugin._tr(error))
                    return False
            self._ask_add_source(name)
            return True

        self.plugin.show_text_dialog(
            self.plugin._tr("config_new"), confirm,
            hint=self.plugin._tr("config_name_hint"),
        )

    def _ask_add_source(self, name: str):
        def confirm(_selected, copy_current):
            self._create(name, copy_current)
            return True

        shown = self.plugin.show_checklist(
            self.plugin._tr("config_new_source_title"), [], confirm,
            message=self.plugin._tr("config_new_source_message"),
            extra=(self.plugin._tr("config_new_copy_current"), False),
            positive=self.plugin._tr("action_create"),
        )
        if not shown:
            self._create(name, False)

    def _create(self, name: str, copy_current: bool):
        try:
            self.add(name, copy_current)
        except ConfigurationSaveError as exc:
            self.plugin.log(f"Configuration creation aborted: {exc}")
            self.plugin._toast("config_save_failed")
        except Exception as exc:
            self.plugin.log(f"Configuration creation failed: {exc}")
            self.plugin._toast("error_operation_failed")

    def request_rename(self, view=None):
        config_id = self.scope_active_id()
        if not config_id or (self.edit_uid is not None and self._owner_of(config_id) != self.edit_uid):
            return
        current = self._record(config_id) or {}
        current_name = as_text(current.get("name", config_id))

        def confirm(value, editor):
            if self.normalize_name(value) == current_name:
                return True
            error = self.name_error(value, ignore_id=config_id)
            if error:
                editor.setError(self.plugin._tr(error))
                return False
            if self.rename(config_id, value):
                return True
            editor.setError(self.plugin._tr("config_save_failed"))
            return False

        self.plugin.show_text_dialog(
            self.plugin._tr("config_rename"), confirm, text=current_name,
        )

    def request_delete(self, view=None):
        ids = self.inactive_ids()
        if not ids:
            self.plugin._toast("config_delete_none")
            return
        if len(ids) == 1:
            self._confirm_delete_single(ids[0])
            return
        rows = [(as_text((self._record(cid) or {}).get("name", cid)), False, True) for cid in ids]

        def confirm(selected, _extra):
            chosen = [ids[index] for index in selected]
            if not chosen:
                self.plugin._toast("config_parts_none")
                return False
            self.delete_many(chosen)
            return True

        self.plugin.show_checklist(
            self.plugin._tr("config_delete_multi"), rows, confirm,
            message=self.plugin._tr("config_delete_multi_select"), positive=self.plugin._tr("action_delete"),
        )

    def _confirm_delete_single(self, config_id: str):
        activity = self.plugin._dialog_activity()
        if not activity:
            return
        name = (self._record(config_id) or {}).get("name", config_id)
        builder = AlertDialogBuilder(activity)
        builder.set_title(self.plugin._tr("config_delete"))
        builder.set_message(self.plugin._tr("config_delete_confirm", name=name))

        def confirm(bld, which):
            bld.dismiss()
            self.delete_many([config_id])

        builder.set_positive_button(self.plugin._tr("action_delete"), confirm)
        builder.set_negative_button(self.plugin._tr("action_cancel"), lambda b, w: b.dismiss())
        self.plugin._show_builder(builder)

    def append_settings(self, settings: list):
        tr = self.plugin._tr
        uid = self.edit_uid
        title = tr("section_configurations")
        if uid is not None:
            slot = next((s for s, u in self.plugin._accounts().items() if u == uid), None)
            title += " • " + self.plugin._acct_label(slot, uid)
        settings.append(Header(text=title))
        count = len(self.scope_records())
        pinned = uid is not None and self.accounts.pin(uid) is not None
        has_own = uid is None or (count >= 1 and not pinned)
        has_several = len(self.selector_ids()) >= 2
        if has_several:
            selector_key, selector_index = self.selector_key, self.selector_display_index()
            try:
                self.plugin.set_setting(selector_key, selector_index)
            except Exception as exc:
                self.plugin.log(f"Prefixfy configuration selector state failed: {exc}")
            settings.append(Selector(
                key=selector_key,
                text=tr("config_active"),
                default=selector_index,
                items=self.selector_display_items(),
                icon="msg_settings",
                on_change=self.switch,
            ))
        settings.append(Text(
            text=tr("config_new"),
            subtext=tr("config_new_subtext"),
            icon="msg_add",
            on_click=self.request_add,
        ))
        if has_own:
            settings.append(Text(
                text=tr("config_rename"),
                subtext=tr("config_rename_subtext"),
                icon="msg_edit",
                on_click=self.request_rename,
            ))
        if self.inactive_ids():
            settings.append(Text(
                text=tr("config_delete_multi"),
                subtext=tr("config_delete_multi_subtext"),
                icon="msg_delete",
                on_click=self.request_delete,
            ))


_VERSION_RE = re.compile(r"([0-9]{1,4})\.([0-9]{1,4})\.([0-9]{1,4})(?:_([0-9]{8})\.([0-9]{1,4})_([0-9]{1,12}))?")
_HEX64_RE = re.compile(r"[0-9a-f]{64}")
_HEX128_RE = re.compile(r"[0-9a-f]{128}")
_MANIFEST_FILE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._\-]{0,79}")


def parse_version(value) -> Tuple[int, ...]:
    match = _VERSION_RE.fullmatch(as_text(value).strip())
    if match is None:
        return ()
    return tuple(int(part) for part in match.groups() if part is not None)


def format_version(parts) -> str:
    parts = tuple(parts)
    if len(parts) == 6:
        return f"{parts[0]}.{parts[1]}.{parts[2]}_{parts[3]:08d}.{parts[4]}_{parts[5]}"
    return ".".join(map(str, parts))


_RSA_OID = bytes.fromhex("06092a864886f70d010101")
_SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")


def _der_read(data: bytes, pos: int) -> Tuple[int, int, int]:
    if pos + 2 > len(data):
        raise ValueError("truncated DER")
    tag = data[pos]
    length = data[pos + 1]
    pos += 2
    if length & 0x80:
        count = length & 0x7F
        if count == 0 or count > 4 or pos + count > len(data):
            raise ValueError("bad DER length")
        length = int.from_bytes(data[pos:pos + count], "big")
        pos += count
    end = pos + length
    if end > len(data):
        raise ValueError("truncated DER")
    return tag, pos, end


def _rsa_public_numbers(der: bytes) -> Tuple[int, int]:
    tag, start, end = _der_read(der, 0)
    if tag != 0x30 or end != len(der):
        raise ValueError("bad SPKI")
    tag, alg_start, alg_end = _der_read(der, start)
    if tag != 0x30 or not der[alg_start:alg_end].startswith(_RSA_OID):
        raise ValueError("not an RSA key")
    tag, bit_start, bit_end = _der_read(der, alg_end)
    if tag != 0x03 or bit_end != end or der[bit_start] != 0:
        raise ValueError("bad key bit string")
    inner = der[bit_start + 1:bit_end]
    tag, seq_start, seq_end = _der_read(inner, 0)
    if tag != 0x30 or seq_end != len(inner):
        raise ValueError("bad RSA key")
    tag, n_start, n_end = _der_read(inner, seq_start)
    if tag != 0x02:
        raise ValueError("bad modulus")
    tag, e_start, e_end = _der_read(inner, n_end)
    if tag != 0x02 or e_end != seq_end:
        raise ValueError("bad exponent")
    modulus = int.from_bytes(inner[n_start:n_end], "big")
    exponent = int.from_bytes(inner[e_start:e_end], "big")
    if modulus.bit_length() < 2048 or exponent != 65537:
        raise ValueError("weak RSA key")
    return modulus, exponent


def _rsa_sha256_verify(public_der: bytes, message: bytes, signature: bytes) -> bool:
    try:
        modulus, exponent = _rsa_public_numbers(public_der)
        size = (modulus.bit_length() + 7) // 8
        if len(signature) != size:
            return False
        number = int.from_bytes(signature, "big")
        if number >= modulus:
            return False
        encoded = pow(number, exponent, modulus).to_bytes(size, "big")
        tail = _SHA256_DIGEST_INFO + hashlib.sha256(message).digest()
        expected = b"\x00\x01" + b"\xff" * (size - len(tail) - 3) + b"\x00" + tail
        return hmac.compare_digest(encoded, expected)
    except Exception:
        return False


def _manifest_int(body: Dict[str, Any], key: str) -> int:
    value = body.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2 ** 53:
        raise ValueError(f"manifest: bad {key}")
    return value


_CHANGELOG_BULLET_RE = re.compile(r"^[\u2022\-*\u2013\u2014]\s+")
_CHANGELOG_LANG_RE = re.compile(r"[a-z]{2,3}")
_CHANGELOG_DEFAULT_KEYS = frozenset(("", "default", "all", "*"))


def _changelog_lines(value) -> Tuple[str, ...]:
    """Строка (по строке на пункт) или список строк -> очищенные пункты. Всё, что не строка, молча пропускается."""
    if isinstance(value, str):
        items = value.splitlines()
    elif isinstance(value, (list, tuple)):
        items = value
    else:
        return ()
    lines: List[str] = []
    total = 0
    for item in items:
        if not isinstance(item, str):
            continue
        text = _CHANGELOG_BULLET_RE.sub("", " ".join(sanitize_text(item).split()))[:CHANGELOG_ITEM_LIMIT].strip()
        if not text:
            continue
        if total + len(text) > CHANGELOG_TOTAL_LIMIT:
            break
        lines.append(text)
        total += len(text)
        if len(lines) >= CHANGELOG_MAX_ITEMS:
            break
    return tuple(lines)


def parse_changelog(value) -> Dict[str, Tuple[str, ...]]:
    """Поле "changelog" манифеста -> {код языка: пункты}; "" — общий список для всех языков.
    Принимает строку, список строк или словарь {язык: строка или список}. Никогда не бросает исключений:
    непонятное содержимое даёт пустой результат, а манифест остаётся годным."""
    try:
        if isinstance(value, dict):
            result: Dict[str, Tuple[str, ...]] = {}
            for key, item in value.items():
                if len(result) >= CHANGELOG_MAX_LANGS:
                    break
                code = as_text(key).strip().lower().replace("-", "_").split("_", 1)[0]
                if code in _CHANGELOG_DEFAULT_KEYS:
                    code = ""
                elif not _CHANGELOG_LANG_RE.fullmatch(code):
                    continue
                lines = _changelog_lines(item)
                if lines:
                    result.setdefault(code, lines)
            return result
        lines = _changelog_lines(value)
        return {"": lines} if lines else {}
    except Exception:
        return {}


def changelog_for_language(changelog, language) -> Tuple[str, ...]:
    """Пункты на языке плагина; если такого нет, то общий список, затем английский, русский и любой другой."""
    try:
        if not isinstance(changelog, dict) or not changelog:
            return ()
        for code in (as_text(language), "", "en", "ru"):
            if changelog.get(code):
                return tuple(changelog[code])
        return tuple(next(iter(changelog.values())))
    except Exception:
        return ()


def _body_digest(body: Dict[str, Any], ignore: Tuple[str, ...] = ("issued_at",)) -> str:
    content = {key: value for key, value in body.items() if key not in ignore}
    packed = json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(packed).hexdigest()


def _check_issued_at(value: int, what: str):
    if 1_500_000_000 <= value < 4_000_000_000:
        seconds = float(value)
    elif 1_500_000_000_000 <= value < 4_000_000_000_000:
        seconds = value / 1000.0
    elif value >= 4_000_000_000:
        raise ValueError(f"{what}: issued in the future")
    else:
        return
    now = time.time()
    if seconds > now + SIGNED_FUTURE_SKEW:
        raise ValueError(f"{what}: issued in the future")
    if SIGNED_MAX_AGE and now - seconds > SIGNED_MAX_AGE:
        raise ValueError(f"{what}: issued too long ago")


def _optional_build(body: Dict[str, Any], key: str) -> Tuple[int, ...]:
    value = body.get(key)
    if value is None or value == "":
        return ()
    parts = parse_version(value)
    if not parts:
        raise ValueError(f"flags: bad {key}")
    return parts


def build_in_range(low: Tuple[int, ...], high: Tuple[int, ...]) -> bool:
    build = parse_version(__build__)[:3]
    if low and build < low[:3]:
        return False
    if high and build > high[:3]:
        return False
    return True


def _verify_signed(raw: bytes, domain: bytes, what: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if not UPDATE_PUBLIC_KEYS:
        raise ValueError("no update public key configured")
    try:
        signed = json.loads(raw.decode("utf-8"))
    except RecursionError as exc:
        raise ValueError(f"{what} is too deeply nested") from exc
    if not isinstance(signed, dict):
        raise ValueError(f"{what} is not an object")
    body = dict(signed)
    signature_text = body.pop("signature", None)
    if not isinstance(signature_text, str):
        raise ValueError(f"{what} is not signed")
    signature = base64.b64decode(signature_text, validate=True)
    message = domain + json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    if not any(_rsa_sha256_verify(base64.b64decode(key), message, signature) for key in UPDATE_PUBLIC_KEYS):
        raise ValueError(f"bad {what} signature")
    return signed, body


def verify_manifest(raw: bytes) -> Dict[str, Any]:
    signed, body = _verify_signed(raw, MANIFEST_DOMAIN, "manifest")
    if _manifest_int(body, "format") != MANIFEST_FORMAT:
        raise ValueError("unsupported manifest format")
    version = parse_version(body.get("version"))
    if not version:
        raise ValueError("manifest: bad version")
    sha256 = as_text(body.get("sha256"))
    sha512 = as_text(body.get("sha512"))
    name = as_text(body.get("file"))
    if not _HEX64_RE.fullmatch(sha256):
        raise ValueError("manifest: missing or bad sha256")
    if sha512 and not _HEX128_RE.fullmatch(sha512):
        raise ValueError("manifest: bad sha512")
    if name and (not _MANIFEST_FILE_RE.fullmatch(name) or ".." in name):
        raise ValueError("manifest: bad file name")
    size = body.get("size", 0)
    if "size" in body and (isinstance(size, bool) or not isinstance(size, int) or not 0 < size <= MANIFEST_MAX_FILE_SIZE):
        raise ValueError("manifest: bad size")
    serial = _manifest_int(body, "serial")
    issued_at = _manifest_int(body, "issued_at")
    _check_issued_at(issued_at, "manifest")
    if len(version) == 6 and version[5] != serial:
        raise ValueError("manifest: serial does not match the serial in the version tag")
    build = parse_version(__build__)
    if len(build) == 6 and serial < build[5]:
        raise ValueError(f"manifest: older than this build ({serial} < {build[5]})")
    return {
        "serial": serial,
        "issued_at": issued_at,
        "version": version,
        "sha256": sha256,
        "sha512": sha512,
        "size": size,
        "file": name,
        "changelog": parse_changelog(body.get("changelog")),
        "digest": _body_digest(body, ("issued_at", "changelog")),
        "signed": signed,
    }


def verify_flags(raw: bytes) -> Dict[str, Any]:
    signed, body = _verify_signed(raw, FLAGS_DOMAIN, "flags")
    if _manifest_int(body, "format") != FLAGS_FORMAT:
        raise ValueError("unsupported flags format")
    issued_at = _manifest_int(body, "issued_at")
    _check_issued_at(issued_at, "flags")
    low, high = _optional_build(body, "min_build"), _optional_build(body, "max_build")
    values = body.get("flags")
    if not isinstance(values, dict) or len(values) > FLAGS_MAX_COUNT:
        raise ValueError("flags: bad flags object")
    known: Dict[str, Any] = {}
    for name, value in values.items():
        if name in FEATURE_FLAGS and _FLAG_NAME_RE.fullmatch(name) and (isinstance(value, bool) or value == AUTO):
            known[name] = value
    raw_accounts = body.get("accounts", {})
    if not isinstance(raw_accounts, dict) or len(raw_accounts) > FLAGS_MAX_ACCOUNTS:
        raise ValueError("flags: bad accounts object")
    accounts: Dict[int, Dict[str, bool]] = {}
    for key, overrides in raw_accounts.items():
        if not (isinstance(key, str) and _ACCOUNT_ID_RE.fullmatch(key) and 0 < int(key) <= 2 ** 53):
            raise ValueError("flags: bad account id")
        if not isinstance(overrides, dict) or len(overrides) > FLAGS_MAX_COUNT:
            raise ValueError("flags: bad account overrides")
        accounts[int(key)] = {
            name: value for name, value in overrides.items()
            if name in FEATURE_FLAGS and isinstance(value, bool) and _FLAG_NAME_RE.fullmatch(name)
        }
    return {
        "serial": _manifest_int(body, "serial"),
        "issued_at": issued_at,
        "min_build": low,
        "max_build": high,
        "flags": known,
        "accounts": accounts,
        "digest": _body_digest(body),
        "signed": signed,
    }


def _blacklist_keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        out += hmac.new(key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest()
        counter += 1
    return bytes(out[:length])


def _decrypt_blacklist_ids(blob: str) -> List[Any]:
    raw = base64.b64decode(blob, validate=True)
    if len(raw) <= 16 or len(raw) > BLACKLIST_MAX_BYTES:
        raise ValueError("blacklist: bad encrypted payload")
    nonce, cipher = raw[:16], raw[16:]
    key = base64.b64decode(BLACKLIST_KEY)
    stream = _blacklist_keystream(key, nonce, len(cipher))
    packed = (int.from_bytes(cipher, "big") ^ int.from_bytes(stream, "big")).to_bytes(len(cipher), "big")
    unpacker = zlib.decompressobj()
    plain = unpacker.decompress(packed, BLACKLIST_MAX_BYTES)
    if unpacker.unconsumed_tail or not unpacker.eof:
        raise ValueError("blacklist: payload too large or truncated")
    try:
        values = json.loads(plain.decode("utf-8"))
    except RecursionError as exc:
        raise ValueError("blacklist: payload is too deeply nested") from exc
    if not isinstance(values, list):
        raise ValueError("blacklist: bad ids list")
    return values


def verify_blacklist(raw: bytes) -> Dict[str, Any]:
    signed, body = _verify_signed(raw, BLACKLIST_DOMAIN, "blacklist")
    if _manifest_int(body, "format") != BLACKLIST_FORMAT:
        raise ValueError("unsupported blacklist format")
    if "ids_enc" in body:
        if not isinstance(body["ids_enc"], str):
            raise ValueError("blacklist: bad encrypted payload")
        try:
            values = _decrypt_blacklist_ids(body["ids_enc"])
        except (ValueError, zlib.error, UnicodeDecodeError, RecursionError) as exc:
            raise ValueError(f"blacklist: cannot decrypt ids ({exc})")
    else:
        values = body.get("ids")
    if not isinstance(values, list) or len(values) > BLACKLIST_MAX_IDS:
        raise ValueError("blacklist: bad ids list")
    ids = set()
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int) or not 0 < value <= 2 ** 53:
            raise ValueError("blacklist: bad account id")
        ids.add(value)
    issued_at = _manifest_int(body, "issued_at")
    _check_issued_at(issued_at, "blacklist")
    return {
        "serial": _manifest_int(body, "serial"),
        "issued_at": issued_at,
        "ids": frozenset(ids),
        "digest": _body_digest(body),
        "signed": signed,
    }


def _scan_device_accounts(logger=None) -> Optional[Dict[int, int]]:
    """{слот: user_id} активных аккаунтов. None — список получить не удалось (это не то же самое, что «аккаунтов нет»)."""
    found, complete = _scan_device_accounts_ex(logger)
    return found if complete else None


def device_account_scan(logger=None) -> Tuple[Optional[frozenset], bool]:
    """48.2.0: (id найденных аккаунтов, полный ли список). Неполный список тоже полезен: если хоть один найденный
    аккаунт в ЧС, это известно наверняка, а раньше сбой одного слота прятал все аккаунты устройства."""
    found, complete = _scan_device_accounts_ex(logger)
    return (None if found is None else frozenset(found.values())), complete


def _scan_device_accounts_ex(logger=None) -> Tuple[Optional[Dict[int, int]], bool]:
    try:
        config_class = find_class("org.telegram.messenger.UserConfig")
        try:
            count = int(config_class.MAX_ACCOUNT_COUNT)
        except Exception:
            count = 16
    except Exception as exc:
        if logger:
            logger(f"Prefixfy device accounts lookup failed: {exc}")
        return None, False
    result: Dict[int, int] = {}
    failed = False
    for index in range(max(1, min(count, 32))):
        try:
            config = config_class.getInstance(index)
            if config is None or not bool(config.isClientActivated()):
                continue
            user_id = java_int(config.getClientUserId())
        except Exception as exc:
            failed = True
            if logger:
                logger(f"Prefixfy device account slot {index} lookup failed: {exc}")
            continue
        if user_id and user_id > 0:
            result[index] = user_id
    return result, not failed


def device_account_ids(logger=None) -> Optional[frozenset]:
    found = _scan_device_accounts(logger)
    return None if found is None else frozenset(found.values())


def device_account_map(logger=None) -> Optional[Dict[int, int]]:
    """{индекс_слота: user_id} для активных аккаунтов этого устройства; None, если узнать не удалось."""
    return _scan_device_accounts(logger)


class AccountProfiles:
    """Пресеты настроек отдельных аккаунтов («Настройки по аккаунтам»).

    У аккаунта может быть несколько пресетов (конфигураций), один из них активен. Каждый пресет лежит так же, как
    конфигурация общего набора: папка <uid>/<id пресета>/ с отдельными файлами параметров и индекс <uid>/index.json.
    Пока у аккаунта нет ни одного пресета, он использует активную общую конфигурацию (то, что было до появления режима);
    первый пресет появляется лениво — при первой правке настроек этого аккаунта или при добавлении конфигурации.
    Профили прежних версий (<uid>.json) при запуске превращаются в первый пресет аккаунта.
    Менять данные должен ConfigurationsManager (под своим замком), здесь — хранение, поиск и рантаймы для отправки.
    """

    def __init__(self, manager):
        self.manager = manager
        self.directory = os.path.join(get_plugins_dir(), ACCT_DIR_NAME)
        ensure_dir_exists(self.directory)
        self.generation = 0
        self._lock = threading.RLock()
        self._presets: Dict[int, Dict[str, dict]] = {}
        self._active: Dict[int, str] = {}
        self._runtimes: Dict[int, Tuple[int, "Runtime"]] = {}
        self._preset_runtimes: Dict[str, Tuple[int, "Runtime"]] = {}
        self._pins: Dict[int, str] = {}
        self.degraded = False

    def _path(self, uid) -> str:
        return os.path.join(self.directory, f"{int(uid)}.json")

    @staticmethod
    def _canonical_uid(text) -> Optional[int]:
        if not isinstance(text, str) or _ACCT_DIR_RE.fullmatch(text) is None or str(int(text)) != text:
            return None
        uid = int(text)
        return uid if 0 < uid <= 2 ** 53 else None

    @staticmethod
    def _clean(params) -> Dict[str, Any]:
        coerce = ConfigurationsManager._coerce
        return {key: coerce(key, params.get(key, SETTING_DEFAULTS[key])) for key in ConfigurationsManager.CONFIG_KEYS}

    def load(self):
        manager = self.manager
        ConfigurationsManager._clean_stale_temp(self.directory)
        try:
            entries = sorted(os.listdir(self.directory))
        except OSError as exc:
            manager.plugin.log(f"Prefixfy accounts: listing failed: {exc}")
            self.degraded = True
            return
        for entry in entries:
            path = os.path.join(self.directory, entry)
            if os.path.isdir(path):
                if entry.endswith(".deleted"):
                    shutil.rmtree(path, ignore_errors=True)
                    continue
                uid = self._canonical_uid(entry)
                if uid is None:
                    continue
                if len(self._presets) >= MAX_ACCOUNT_PROFILES:
                    self.degraded = True
                    continue
                records, active = manager._load_records(path, uid)
                if records:
                    with self._lock:
                        self._presets[uid] = records
                        self._active[uid] = active if active in records else next(iter(records))
        self._load_pins()

    def _load_pins(self):
        """46.5.0: общие конфигурации, выбранные аккаунтами (ссылкой, без копирования)."""
        manager = self.manager
        try:
            raw = as_text(manager.plugin.get_setting(ACCT_PINS_KEY, "")).strip()
            data = json.loads(raw) if raw else {}
        except Exception as exc:
            manager.plugin.log(f"Prefixfy accounts: pins unreadable: {exc}")
            return
        if not isinstance(data, dict):
            return
        with self._lock:
            for key, value in data.items():
                uid = self._canonical_uid(key)
                if uid is not None and ConfigurationsManager._valid_id(value) and ConfigurationsManager._owner_of(value) is None:
                    self._pins[uid] = value

    def _save_pins(self):
        with self._lock:
            payload = json.dumps({str(uid): cid for uid, cid in self._pins.items()}, separators=(",", ":"))
        try:
            self.manager.plugin.set_setting(ACCT_PINS_KEY, payload, reload_settings=False)
        except Exception as exc:
            self.manager.plugin.log(f"Prefixfy accounts: pins save failed: {exc}")

    def pin(self, uid) -> Optional[str]:
        """Общая конфигурация, которую использует аккаунт. None — не выбрана или уже удалена."""
        if uid is None:
            return None
        with self._lock:
            pinned = self._pins.get(int(uid))
        return pinned if pinned and pinned in self.manager.configurations else None

    def set_pin(self, uid, config_id: Optional[str]):
        uid = int(uid)
        with self._lock:
            if config_id:
                self._pins[uid] = config_id
            else:
                self._pins.pop(uid, None)
            self._runtimes.pop(uid, None)
            self.generation += 1
        self._save_pins()

    def invalidate(self):
        with self._lock:
            self.generation += 1
            self._runtimes.clear()
            self._preset_runtimes.clear()

    def uids(self) -> List[int]:
        with self._lock:
            return sorted(uid for uid, bucket in self._presets.items() if bucket)

    def has(self, uid) -> bool:
        if uid is None:
            return False
        with self._lock:
            return bool(self._presets.get(int(uid)))

    def bucket(self, uid, create: bool = False) -> Dict[str, dict]:
        """Пресеты аккаунта (живой словарь). Если их нет и create=False — пустой словарь, который никуда не привязан."""
        uid = int(uid)
        with self._lock:
            found = self._presets.get(uid)
            if found is None:
                if not create:
                    return {}
                found = self._presets[uid] = {}
            return found

    def ids(self, uid) -> List[str]:
        with self._lock:
            return list(self._presets.get(int(uid), {}))

    def active_id(self, uid) -> Optional[str]:
        if uid is None:
            return None
        uid = int(uid)
        with self._lock:
            bucket = self._presets.get(uid)
            if not bucket:
                return None
            active = self._active.get(uid)
            return active if active in bucket else next(iter(bucket))

    def set_active(self, uid, config_id: str):
        uid = int(uid)
        with self._lock:
            self._active[uid] = config_id
            self._runtimes.pop(uid, None)
            self.generation += 1

    def active_record(self, uid) -> Optional[dict]:
        config_id = self.active_id(uid)
        if config_id is None:
            return None
        with self._lock:
            return self._presets.get(int(uid), {}).get(config_id)

    def all_records(self) -> List[Tuple[str, dict]]:
        with self._lock:
            return [(config_id, record) for bucket in self._presets.values() for config_id, record in bucket.items()]

    def delete(self, uid) -> bool:
        """Удаляет все пресеты аккаунта: дальше он снова использует общий набор."""
        uid = int(uid)
        manager = self.manager
        root = manager._account_root(uid)
        tomb = root + ".deleted"
        with self._lock:
            try:
                if os.path.isdir(root):
                    shutil.rmtree(tomb, ignore_errors=True)
                    os.replace(root, tomb)
                if os.path.isfile(self._path(uid)):
                    os.remove(self._path(uid))
            except OSError as exc:
                manager.plugin.log(f"Prefixfy accounts: delete failed ({uid}): {exc}")
                return False
            removed = self._presets.pop(uid, None) or {}
            self._active.pop(uid, None)
            self._runtimes.pop(uid, None)
            had_pin = self._pins.pop(uid, None) is not None
            self.generation += 1
        if had_pin:
            self._save_pins()
        shutil.rmtree(tomb, ignore_errors=True)
        manager._failed_writes = {m for m in manager._failed_writes if m[0] not in removed}
        for record in list(removed.values()):
            manager._remove_media_of(record)
        return True

    def runtime_for(self, uid) -> Optional["Runtime"]:
        if uid is None:
            return None
        uid = int(uid)
        pinned = self.pin(uid)
        if pinned:
            return self.manager.runtime_for(pinned)
        with self._lock:
            cached = self._runtimes.get(uid)
            if cached is not None and cached[0] == self.generation:
                return cached[1]
            config_id = self.active_id(uid)
            record = self._presets.get(uid, {}).get(config_id) if config_id else None
            if record is None:
                return None
            try:
                runtime = Runtime(RuntimeSettings(dict(record.get("current") or {})), config_id, self.manager.plugin.log)
            except Exception as exc:
                self.manager.plugin.log(f"Prefixfy account runtime failed ({uid}): {exc}")
                return None
            self._runtimes[uid] = (self.generation, runtime)
            return runtime

    def runtime_for_preset(self, uid, config_id) -> Optional["Runtime"]:
        """Рантайм любого пресета аккаунта (не только активного): для конфигураций отдельных чатов."""
        if uid is None or not config_id:
            return None
        uid = int(uid)
        with self._lock:
            cached = self._preset_runtimes.get(config_id)
            if cached is not None and cached[0] == self.generation:
                return cached[1]
            record = self._presets.get(uid, {}).get(config_id)
            if record is None:
                return None
            try:
                runtime = Runtime(RuntimeSettings(dict(record.get("current") or {})), config_id, self.manager.plugin.log)
            except Exception as exc:
                self.manager.plugin.log(f"Prefixfy account preset runtime failed ({uid}): {exc}")
                return None
            if len(self._preset_runtimes) >= 16:
                self._preset_runtimes.clear()
            self._preset_runtimes[config_id] = (self.generation, runtime)
            return runtime


class _SameHostRedirect(urllib.request.HTTPRedirectHandler):

    def __init__(self, hosts=UPDATE_ALLOWED_HOSTS):
        super().__init__()
        self._hosts = tuple(hosts)

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parts = urllib.parse.urlsplit(newurl)
        if parts.scheme != "https" or (parts.hostname or "").lower() not in self._hosts:
            raise urllib.error.URLError("redirect to a foreign host blocked")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class WeatherCache:

    TTL = 30 * 60
    RETRY = 5 * 60
    STALE = 6 * 3600
    MAX_ITEMS = 8

    def __init__(self, log):
        self._log = log
        self._lock = threading.Lock()
        self._items: Dict[str, Tuple[float, str, float]] = {}
        self._busy: set = set()
        self._closed = False

    def close(self):
        with self._lock:
            self._closed = True
            self._items.clear()

    def get(self, city: str) -> str:
        key = as_text(city).strip().casefold()[:40]
        now = time.monotonic()
        with self._lock:
            entry = self._items.get(key)
            text = entry[1] if entry and entry[1] and now - entry[0] <= self.STALE else ""
            due = entry is None or now >= entry[2]
            start = due and not self._closed and key not in self._busy
            if start:
                self._busy.add(key)
        if start:
            try:
                threading.Thread(target=self._refresh, args=(key,), name="PrefixfyWeather", daemon=True).start()
            except Exception as exc:
                with self._lock:
                    self._busy.discard(key)
                self._log(f"Prefixfy weather thread failed: {exc}")
        return text

    def _refresh(self, key: str):
        text = ""
        try:
            text = self._fetch(key)
        except Exception as exc:
            self._log(f"Prefixfy weather lookup failed: {exc}")
        now = time.monotonic()
        with self._lock:
            self._busy.discard(key)
            if self._closed:
                return
            old = self._items.get(key)
            if text:
                self._items[key] = (now, text, now + self.TTL)
            elif old is not None:
                self._items[key] = (old[0], old[1], now + self.RETRY)
            else:
                self._items[key] = (now, "", now + self.RETRY)
            while len(self._items) > self.MAX_ITEMS:
                self._items.pop(min(self._items, key=lambda name: self._items[name][0]))

    @staticmethod
    def _fetch(key: str) -> str:
        import ssl
        query = urllib.parse.urlencode({"format": "%c%t"})
        request = urllib.request.Request(
            f"https://{WEATHER_HOST}/{urllib.parse.quote(key, safe='')}?{query}",
            headers={"User-Agent": f"Prefixfy/{__build__}", "Accept": "text/plain"},
        )
        opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
            _SameHostRedirect((WEATHER_HOST,)),
        )
        with opener.open(request, timeout=REMOTE_TIMEOUT) as response:
            final = urllib.parse.urlsplit(response.geturl())
            if final.scheme != "https" or (final.hostname or "").lower() != WEATHER_HOST:
                raise ValueError("unexpected final host")
            body = response.read(257)
        text = " ".join(body.decode("utf-8", "replace").split())
        if len(text) > 32 or "°" not in text or not any(char.isdigit() for char in text):
            return ""
        return text


def parse_ota_time(value) -> Optional[Tuple[int, int]]:
    match = OTA_TIME_RE.fullmatch(as_text(value))
    return (int(match.group(1)), int(match.group(2))) if match else None


def _ota_state_path() -> str:
    return os.path.join(get_plugins_dir(), OTA_STATE_FILE)


def _ota_read() -> Dict[str, Any]:
    try:
        with open(_ota_state_path(), "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, RecursionError):
        return {}


def _ota_write(data: Dict[str, Any], log=None):
    path = _ota_state_path()
    try:
        _write_file_atomic(path, json.dumps(data).encode("utf-8"))
    except (OSError, TypeError, ValueError) as exc:
        if log:
            log(f"Prefixfy OTA state not saved: {exc}")


def _ota_boots(data: Dict[str, Any]) -> int:
    """49.0.0: счётчик запусков из файла состояния OTA; мусор в файле не роняет сторож отката."""
    value = data.get("boots") if isinstance(data, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) and 0 <= value < 1000 else 0


def _ota_bad_serials() -> List[int]:
    bad = _ota_read().get("bad", [])
    return [item for item in bad if isinstance(item, int) and not isinstance(item, bool)] if isinstance(bad, list) else []


def _write_file_atomic(path: str, data: bytes):
    temp = unique_temp(path)
    try:
        with open(temp, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        try:
            os.remove(temp)
        except OSError:
            pass


def _ota_own_path(data: Dict[str, Any]) -> str:
    """Файл, который можно перезаписывать при откате: только сам плагин, а не путь из файла состояния."""
    own = globals().get("__file__")
    if own:
        return os.path.realpath(own)
    stored = as_text(data.get("path"))
    try:
        base = os.path.realpath(get_plugins_dir())
        real = os.path.realpath(stored) if stored else ""
    except Exception:
        return ""
    return real if real.startswith(base + os.sep) and real.endswith(".py") else ""


def _slot_dir() -> str:
    return os.path.join(get_plugins_dir(), OTA_SLOT_DIR)


def _slot_file() -> str:
    return os.path.join(_slot_dir(), OTA_SLOT_FILE)


def _slot_meta_path() -> str:
    return os.path.join(_slot_dir(), OTA_SLOT_META)


def _slot_meta_read() -> Dict[str, Any]:
    try:
        with open(_slot_meta_path(), "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError, RecursionError):
        return {}
    if not isinstance(data, dict) or data.get("role") not in (SLOT_STAGED, SLOT_PREVIOUS):
        return {}
    return data


def _slot_exists() -> bool:
    return os.path.exists(_slot_dir())


def _slot_clear(log=None):
    """Очистить неактивный раздел целиком."""
    shutil.rmtree(_slot_dir(), ignore_errors=True)
    if log is not None and _slot_exists():
        log("Prefixfy: the inactive slot could not be fully cleared")


def _slot_store(data: bytes, meta: Dict[str, Any]):
    """Записать содержимое неактивного раздела. Описание пишется последним: пока его нет, раздел считается пустым."""
    os.makedirs(_slot_dir(), exist_ok=True)
    try:
        os.remove(_slot_meta_path())
    except OSError:
        pass
    _write_file_atomic(_slot_file(), data)
    _write_file_atomic(_slot_meta_path(), json.dumps(meta).encode("utf-8"))


def _slot_verified_bytes(meta: Dict[str, Any], role: str) -> bytes:
    """Содержимое неактивного раздела, если оно цело и является плагином с нужным id."""
    if meta.get("role") != role:
        raise ValueError(f"inactive slot is not {role}")
    with open(_slot_file(), "rb") as handle:
        blob = handle.read(MANIFEST_MAX_FILE_SIZE + 1)
    if len(blob) > MANIFEST_MAX_FILE_SIZE:
        raise ValueError("slot file is too large")
    digest = hashlib.sha256(blob).hexdigest()
    if not hmac.compare_digest(digest, as_text(meta.get("sha256"))):
        raise ValueError("slot file is damaged")
    if role == SLOT_STAGED:
        signed = meta.get("manifest")
        if not isinstance(signed, dict):
            raise ValueError("staged slot has no signed manifest")
        info = verify_manifest(json.dumps(signed, ensure_ascii=True).encode("utf-8"))
        if not hmac.compare_digest(digest, info["sha256"]):
            raise ValueError("staged slot does not match the signed manifest")
        if info["sha512"] and not hmac.compare_digest(hashlib.sha512(blob).hexdigest(), info["sha512"]):
            raise ValueError("staged slot does not match the signed manifest")
        if tuple(info["version"]) != parse_version(meta.get("version")) or info["serial"] != meta.get("serial"):
            raise ValueError("staged slot version differs from the signed manifest")
    source = blob.decode("utf-8")
    if re.search(r'^__id__\s*=\s*"' + re.escape(__id__) + r'"\s*$', source, re.MULTILINE) is None:
        raise ValueError("slot holds another plugin")
    compile(source, "prefixfy_slot.py", "exec")
    return blob


def _slot_swap(log, heal: bool = False) -> Dict[str, Any]:
    """Сменить активный раздел: новая версия из неактивного раздела становится основным файлом,
    а прежний основной файл остаётся в неактивном разделе как «прошлая версия»."""
    data0 = _ota_read()
    path = _ota_own_path(data0)
    if not path:
        raise OSError("plugin path is unknown")
    if not os.access(os.path.dirname(path), os.W_OK):
        raise OSError("plugin folder is read-only")
    meta = _slot_meta_read()
    incoming = _slot_verified_bytes(meta, SLOT_STAGED)
    with open(path, "rb") as handle:
        current = handle.read()
    if current == incoming and not heal:
        raise ValueError("this version is already installed")
    old = os.path.join(_slot_dir(), OTA_SLOT_OLD)
    _write_file_atomic(old, current)
    _ota_write({
        "state": "pending", "to": as_text(meta.get("version")), "serial": meta.get("serial"),
        "prev": __build__, "path": path, "boots": 0, "bad": _ota_bad_serials(), "heal": bool(heal),
    }, log)
    _write_file_atomic(path, incoming)
    try:
        _slot_store(current, {
            "role": SLOT_PREVIOUS, "version": __build__, "sha256": hashlib.sha256(current).hexdigest(),
            "size": len(current), "serial": data0.get("serial"),
        })
        os.remove(old)
    except OSError as exc:
        log(f"Prefixfy slot swap: finishing step failed, it is completed at the next start: {exc}")
    return meta


def _slot_housekeeping(log):
    """Начало запуска: достроить прерванную смену разделов и убрать повреждённое содержимое неактивного раздела."""
    if not _slot_exists():
        return
    try:
        meta = _slot_meta_read()
        old = os.path.join(_slot_dir(), OTA_SLOT_OLD)
        if os.path.isfile(old):
            main = _ota_own_path(_ota_read())
            done = False
            if main and meta.get("role") == SLOT_STAGED:
                with open(main, "rb") as handle:
                    done = hashlib.sha256(handle.read()).hexdigest() == meta.get("sha256")
            if done:
                with open(old, "rb") as handle:
                    previous = handle.read()
                _slot_store(previous, {
                    "role": SLOT_PREVIOUS, "version": as_text(_ota_read().get("prev")),
                    "sha256": hashlib.sha256(previous).hexdigest(), "size": len(previous), "serial": None,
                })
                log("Prefixfy: an interrupted slot swap was completed")
            discard_file(old)
            meta = _slot_meta_read()
        if not meta:
            _slot_clear(log)
            return
        try:
            _slot_verified_bytes(meta, meta["role"])
        except Exception as exc:
            log(f"Prefixfy: the inactive slot is damaged and was cleared: {exc}")
            _slot_clear(log)
            return
        if meta["role"] == SLOT_STAGED:
            version = parse_version(meta.get("version"))
            if not version or (version <= parse_version(__build__) and not meta.get("heal")):
                _slot_clear(log)
    except Exception as exc:
        log(f"Prefixfy slot check failed: {exc}")


def _ota_rollback(reason: str, log) -> bool:
    """Автоматический откат: прошлая версия из неактивного раздела возвращается в активный,
    неудачная сборка выбрасывается, её серия запоминается как «плохая»."""
    data = _ota_read()
    path = _ota_own_path(data)
    if not path:
        return False
    try:
        meta = _slot_meta_read()
        if meta.get("role") != SLOT_PREVIOUS:
            raise ValueError("no saved previous version")
        previous = _slot_verified_bytes(meta, SLOT_PREVIOUS)
        _write_file_atomic(path, previous)
    except Exception as exc:
        log(f"Prefixfy OTA rollback failed: {exc}")
        return False
    _slot_clear(log)
    bad = _ota_bad_serials()
    serial = data.get("serial")
    if isinstance(serial, int) and not isinstance(serial, bool) and serial not in bad:
        bad.append(serial)
    _ota_write({"bad": bad[-OTA_BAD_LIMIT:], "state": "rolled_back", "reason": as_text(reason)[:80]}, log)
    log(f"Prefixfy OTA rolled back: {reason}")
    return True


HOST_TOGGLE_TIMEOUT = 20.0


def _on_plugins_queue_thread() -> bool:
    try:
        from java.lang import Thread
        from org.telegram.messenger import Utilities
        queue = Utilities.pluginsQueue
        handler = queue.getHandler() if queue is not None else None
        return handler is not None and handler.getLooper().getThread() == Thread.currentThread()
    except Exception:
        return False


def _host_set_plugin_enabled(enabled: bool, log, wait: bool = True) -> bool:
    """Единственное место, привязанное к API хоста: включить или выключить этот плагин.

    52.0.0: PluginsController.setPluginEnabled(id, enabled, Callback<String>) выполняется асинхронно в pluginsQueue и
    сообщает результат в callback (null или текст ошибки). Раньше результат не ждали: выключение и включение
    разделяла пауза в 1.5 с, а ошибка включения новой сборки терялась. Теперь ждём ответа (кроме вызова из самой
    pluginsQueue - там ожидание заблокировало бы очередь) и возвращаем False при ошибке.
    """
    try:
        from java import dynamic_proxy
        from org.telegram.messenger import Utilities
        from com.exteragram.messenger.plugins import PluginsController
        controller = PluginsController.getInstance()
    except Exception as exc:
        log(f"Prefixfy OTA: plugin controller not available: {exc}")
        return False
    done = threading.Event()
    outcome: Dict[str, Any] = {"error": None}

    class _Done(dynamic_proxy(Utilities.Callback)):
        def run(self, error):
            outcome["error"] = as_text(error) if error is not None else None
            done.set()

    try:
        controller.setPluginEnabled(__id__, bool(enabled), _Done())
    except Exception as exc:
        log(f"Prefixfy OTA: setPluginEnabled call failed: {exc}")
        return False
    if not wait or _on_plugins_queue_thread():
        return True
    if not done.wait(HOST_TOGGLE_TIMEOUT):
        log(f"Prefixfy OTA: no answer to setPluginEnabled({bool(enabled)}) in {HOST_TOGGLE_TIMEOUT:.0f} s")
        return True
    if outcome["error"]:
        log(f"Prefixfy OTA: setPluginEnabled({bool(enabled)}) failed: {outcome['error'][:300]}")
        return False
    return True


def _host_restart_plugin(log) -> bool:
    if not _host_set_plugin_enabled(False, log):
        return False
    time.sleep(0.3)
    return _host_set_plugin_enabled(True, log)


def _self_file_digests() -> Optional[Tuple[str, str, int]]:
    path = globals().get("__file__")
    if not path:
        return None
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError:
        return None
    return hashlib.sha256(data).hexdigest(), hashlib.sha512(data).hexdigest(), len(data)


_WIPE_STATE_FILES = (
    "Prefixfy_remote.json", BLACKLIST_CACHE_FILE, FLAGS_CACHE_FILE, LEGACY_FLAGS_CACHE_FILE, AUTO_STATE_FILE,
    STORE_KEY_FILE, SERIALS_FILE, KNOWN_BUILDS_FILE, OTA_STATE_FILE, LEGACY_PREV_FILE, BLACKLIST_GUARD_FILE,
)
_WIPE_KEEP_ON_CLEAN = frozenset({STORE_KEY_FILE, SERIALS_FILE, KNOWN_BUILDS_FILE, OTA_STATE_FILE, BLACKLIST_GUARD_FILE})
_WIPE_DIRS = ("Prefixfy_media", ConfigurationsManager.MEDIA_DIR_NAME, ConfigurationsManager.STORE_DIR_NAME, ACCT_DIR_NAME,
              MEDIA_OUTBOX_DIR, DEBUG_DIR_NAME)
_WIPE_CACHE_DIRS = ("Prefixfy_tmp", "Prefixfy_imports", "Prefixfy_exports", "Prefixfy")
_WIPE_TEMP_SUFFIXES = (".tmp", ".ota", ".bak")
_WIPE_MEDIA_RESET = {
    "attached_media_path": "", "attached_media_name": "", "attached_media_mime": "", "attached_media_enabled": False,
}
_WIPE_INTERNAL_KEYS = {
    SCHEMA_KEY: SCHEMA_VERSION, CHAT_COUNTS_KEY: "", COUNTER_KEY: 0,
    SETUP_STAGE_KEY: 1, SETUP_SEEN_KEY: 1, WELCOME_UNTIL_KEY: 0, UPDATED_UNTIL_KEY: 0, UPDATED_NOTES_KEY: "",
    SETUP_UPDATE_AT_KEY: 0, DEBUG_ENABLED_KEY: False, DEBUG_RECORDING_KEY: False,
    "Prefixfy_markdown_style_pick": 0, "Prefixfy_text_style_pick": 0,
    CHAT_CONFIGS_KEY: "{}", SCHEDULE_KEY: "", ACCT_MODE_KEY: False, ACCT_TARGET_KEY: ACCT_AUTO, ACCT_LIVE_KEY: "", ACCT_PINS_KEY: "",
    **{key: "" for key in LEGACY_SETTING_KEYS},
}


def _plugins_path(name: str) -> str:
    return os.path.join(get_plugins_dir(), name)


def _own_fingerprint() -> Optional[List[int]]:
    """Отпечаток именно этой копии файла плагина. Переустановка даёт новый inode/ctime, поэтому отпечаток меняется."""
    path = globals().get("__file__")
    if not path:
        return None
    try:
        info = os.stat(path)
    except OSError:
        return None
    ctime = getattr(info, "st_ctime_ns", None)
    if ctime is None:
        ctime = int(info.st_ctime * 1e9)
    return [int(info.st_ino), int(info.st_size), int(ctime)]


def read_wipe_marker() -> Optional[Dict[str, Any]]:
    path = _plugins_path(WIPE_MARKER_FILE)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return None
    except (OSError, ValueError, RecursionError):
        discard_file(path)
        return None
    stamp = data.get("ts") if isinstance(data, dict) else None
    valid = (
        isinstance(data, dict) and isinstance(data.get("opt_out"), bool) and isinstance(data.get("need"), str)
        and isinstance(stamp, (int, float)) and not isinstance(stamp, bool) and math.isfinite(stamp)
        and -300.0 <= time.time() - float(stamp) <= WIPE_MARKER_TTL
    )
    if not valid:
        discard_file(path)
        return None
    return {"opt_out": data["opt_out"], "need": data["need"], "bl": data.get("bl") is True}


def write_wipe_marker(opt_out: bool, need: str = "", bl: bool = False) -> bool:
    try:
        _write_file_atomic(
            _plugins_path(WIPE_MARKER_FILE),
            json.dumps({"opt_out": bool(opt_out), "need": as_text(need), "bl": bool(bl), "ts": time.time()}).encode("utf-8"),
        )
        return True
    except OSError:
        return False


def clear_wipe_marker():
    discard_file(_plugins_path(WIPE_MARKER_FILE))


def write_wipe_final_marker() -> bool:
    """Данные стёрты, плагин перезапускается второй раз: метка нужна, чтобы после него показать «Данные очищены»."""
    try:
        _write_file_atomic(_plugins_path(WIPE_FINAL_FILE), json.dumps({"ts": time.time()}).encode("utf-8"))
        return True
    except OSError:
        return False


def take_wipe_final_marker() -> bool:
    path = _plugins_path(WIPE_FINAL_FILE)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            stamp = float(json.load(handle).get("ts", 0))
    except FileNotFoundError:
        return False
    except (OSError, ValueError, AttributeError, TypeError, RecursionError):
        discard_file(path)
        return False
    discard_file(path)
    return -300.0 <= time.time() - stamp <= WIPE_FINAL_TTL


def write_dormant_marker() -> bool:
    fingerprint = _own_fingerprint()
    if fingerprint is None:
        return False
    try:
        _write_file_atomic(_plugins_path(DORMANT_FILE), json.dumps({"fp": fingerprint}).encode("utf-8"))
        return True
    except OSError:
        return False


def clear_dormant_marker():
    discard_file(_plugins_path(DORMANT_FILE))


def dormant_active() -> bool:
    """True, если отказ от использования действует для ЭТОЙ копии файла. Для другой копии (переустановка) метка стирается."""
    path = _plugins_path(DORMANT_FILE)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return False
    except (OSError, ValueError, RecursionError):
        data = None
    fingerprint = _own_fingerprint()
    if isinstance(data, dict) and fingerprint is not None and data.get("fp") == fingerprint:
        return True
    discard_file(path)
    return False


def _wipe_files(opt_out: bool, log):
    base = get_plugins_dir()
    own = os.path.basename(as_text(globals().get("__file__")))
    skip = set() if opt_out else set(_WIPE_KEEP_ON_CLEAN)
    doomed = [name for name in _WIPE_STATE_FILES if name not in skip]
    try:
        entries = os.listdir(base)
    except OSError:
        entries = []
    for entry in entries:
        if entry != own and entry.endswith(_WIPE_TEMP_SUFFIXES) and any(
            entry.startswith(name + ".") for name in doomed
        ):
            doomed.append(entry)
    for name in doomed:
        if name != own:
            discard_file(os.path.join(base, name))
    for name in _WIPE_DIRS:
        shutil.rmtree(os.path.join(base, name), ignore_errors=True)
    _slot_clear(log)
    cache_dir = get_cache_dir()
    for name in _WIPE_CACHE_DIRS:
        shutil.rmtree(os.path.join(cache_dir, name), ignore_errors=True)
    log(f"Prefixfy: files removed ({'opt-out' if opt_out else 'clean'})")


def _wipe_settings(plugin, opt_out: bool):
    values: Dict[str, Any] = {**SETTING_DEFAULTS, **TRANSIENT_SETTING_DEFAULTS, **OTA_SETTING_DEFAULTS, **_WIPE_INTERNAL_KEYS}
    bulk_set_settings(plugin, values)
    plugin._counter_state = None
    for _attempt in range(3):
        try:
            if plugin.get_setting(SETUP_STAGE_KEY, None) == 1:
                break
            plugin.set_setting(SETUP_STAGE_KEY, 1)
        except Exception as exc:
            plugin.log(f"Prefixfy wipe: setup stage was not restored: {exc}")
    try:
        plugin._language_ui_invalidate()
    except Exception:
        pass


def wipe_blacklist_data(plugin):
    """Вход в режим ЧС: всё стирается как при отказе от использования, но подписанные ЧС и манифест остаются.

    Они лежат запечатанными ключом Keystore, а ключ при отказе уничтожается, поэтому перед удалением их расшифровывают
    и кладут обратно открытым текстом (время изменения сохраняется: возраст кэша не «молодеет»). При следующем запуске
    плагин запечатает их уже новым ключом. Плагин остаётся включённым и заблокированным, доступна «Проверить сейчас»."""
    VAULT.attach(plugin.log)
    kept: List[Tuple[str, bytes, Tuple[float, float]]] = []
    for name, limit in (("Prefixfy_remote.json", REMOTE_MAX_BYTES), (BLACKLIST_CACHE_FILE, BLACKLIST_MAX_BYTES)):
        path = _plugins_path(name)
        try:
            stat = os.stat(path)
            data = vault_read_bytes(path, limit)
            if len(data) > limit:
                raise ValueError("file is too large")
            kept.append((path, data, (stat.st_atime, stat.st_mtime)))
        except Exception as exc:
            plugin.log(f"Prefixfy blacklist mode: {name} was not kept: {exc}")
    wipe_plugin_data(plugin, True)
    for path, data, times in kept:
        try:
            _write_file_atomic(path, data)
            os.utime(path, times)
        except OSError as exc:
            plugin.log(f"Prefixfy blacklist mode: cannot restore {os.path.basename(path)}: {exc}")
    try:
        _write_file_atomic(_plugins_path(BLACKLIST_GUARD_FILE), json.dumps({"ts": time.time()}).encode("utf-8"))
    except OSError as exc:
        plugin.log(f"Prefixfy blacklist mode: guard not stored: {exc}")


def blacklist_guard_exists() -> bool:
    return os.path.exists(_plugins_path(BLACKLIST_GUARD_FILE))


def wipe_plugin_data(plugin, opt_out: bool):
    """Всегда глубокий сброс: все файлы (включая служебные), ключи хранилища и все настройки.
    opt_out влияет только на то, что делает вызывающий код дальше: усыпляет плагин или оставляет его работать
    (тогда он запускается как после первой установки). Обновление до последней сборки происходит ДО сброса (_start_wipe)."""
    _wipe_files(True, plugin.log)
    VAULT.attach(plugin.log)
    VAULT.destroy()
    _wipe_settings(plugin, True)
    plugin.log(f"Prefixfy: deep wipe done ({'opt-out' if opt_out else 'clean restart'})")


AUTO_RESET_MARKER_FILE = ".pfx_autoreset"
AUTO_RESET_COOLDOWN = 600.0


def _plain_json_bad(path: str) -> bool:
    try:
        with open(path, "rb") as handle:
            blob = handle.read(MAX_STORE_JSON_BYTES + 1)
    except OSError:
        return False
    if len(blob) > MAX_STORE_JSON_BYTES:
        return True
    try:
        return not isinstance(json.loads(blob.decode("utf-8")), dict)
    except (ValueError, RecursionError):
        return True


def integrity_scan(plugin) -> Tuple[List[str], bool]:
    """(список повреждённого, нужно ли пересоздавать ключ хранилища)."""
    problems: List[str] = []
    key_bad = False
    base = get_plugins_dir()
    try:
        with open(os.path.join(base, STORE_KEY_FILE), "rb") as handle:
            blob = handle.read(512)
    except OSError:
        blob = b""
    if blob and (not blob.startswith(VAULT.MAGIC) or len(blob) <= len(VAULT.MAGIC) + VAULT.IV_LEN + 16):
        problems.append(STORE_KEY_FILE)
        key_bad = True
    if _plain_json_bad(os.path.join(base, OTA_STATE_FILE)):
        problems.append(OTA_STATE_FILE)
    if not key_bad:
        VAULT.attach(plugin.log)
        VAULT.prepare()
        if VAULT.usable:
            for name in (SERIALS_FILE, KNOWN_BUILDS_FILE, AUTO_STATE_FILE):
                path = os.path.join(base, name)
                if not os.path.isfile(path):
                    continue
                try:
                    if not isinstance(vault_read_json(path, MAX_STORE_JSON_BYTES), dict):
                        problems.append(name)
                except OSError:
                    continue
                except Exception:
                    problems.append(name)
            for root_name in (ConfigurationsManager.STORE_DIR_NAME, ACCT_DIR_NAME):
                for folder, dirs, files in os.walk(os.path.join(base, root_name)):
                    dirs[:] = [item for item in dirs if not item.endswith(".deleted")]
                    for name in files:
                        if not name.endswith(".json"):
                            continue
                        path = os.path.join(folder, name)
                        try:
                            json.loads(store_read_text(path))
                        except OSError:
                            continue
                        except Exception:
                            if name == ConfigurationsManager.INDEX_NAME:
                                try:
                                    json.loads(store_read_text(path + ".bak"))
                                    continue
                                except Exception:
                                    pass
                            problems.append(os.path.relpath(path, base))
    try:
        raw = {}
        for key, default in SETTING_DEFAULTS.items():
            value = plugin.get_setting(key, default)
            if isinstance(default, str) and not isinstance(value, str):
                problems.append(f"setting:{key}")
            elif isinstance(default, (bool, int)) and isinstance(value, (list, dict)):
                problems.append(f"setting:{key}")
            raw[key] = value
        RuntimeSettings(raw)
    except Exception:
        problems.append("settings")
    return problems, key_bad


def _auto_reset_recent() -> bool:
    try:
        with open(_plugins_path(AUTO_RESET_MARKER_FILE), "r", encoding="utf-8") as handle:
            stamp = float(json.load(handle).get("ts", 0))
        return 0.0 <= time.time() - stamp < AUTO_RESET_COOLDOWN
    except (OSError, ValueError, AttributeError, TypeError, RecursionError):
        return False


def auto_reset_plugin(plugin, problems: List[str], key_bad: bool):
    """Полный сброс: данные пользователя, кэши, конфигурации, настройки. Подписанные служебные файлы защиты
    (серийные номера, известные сборки, состояние OTA, охранная метка ЧС) остаются, пока сами не повреждены."""
    guard_path = _plugins_path(BLACKLIST_GUARD_FILE)
    try:
        with open(guard_path, "rb") as handle:
            guard = handle.read()
    except OSError:
        guard = None
    full = key_bad or any(item in (SERIALS_FILE, KNOWN_BUILDS_FILE, AUTO_STATE_FILE) for item in problems)
    _wipe_files(full, plugin.log)
    if full:
        VAULT.attach(plugin.log)
        VAULT.destroy()
    else:
        for name in problems:
            if name in _WIPE_STATE_FILES:
                discard_file(_plugins_path(name))
    if guard is not None:
        try:
            _write_file_atomic(guard_path, guard)
        except OSError as exc:
            plugin.log(f"Prefixfy auto reset: guard not restored: {exc}")
    _wipe_settings(plugin, True)
    try:
        _write_file_atomic(_plugins_path(AUTO_RESET_MARKER_FILE), json.dumps({"ts": time.time()}).encode("utf-8"))
    except OSError:
        pass


class _NotModified(Exception):
    """Сервер ответил 304: сохранённая копия файла актуальна, тело не передавалось."""


class RemoteControl:

    def __init__(self, plugin):
        self.plugin = plugin
        self.enabled = bool(UPDATE_PUBLIC_KEYS)
        self._lock = threading.Lock()
        self._busy = threading.Lock()
        self._soft_lock = threading.Lock()
        self._stop = threading.Event()
        self._state: Optional[Dict[str, Any]] = None
        self._last_ok = float("-inf")
        self._last_request = -REMOTE_MANUAL_COOLDOWN
        self._notified = False
        self._soft_notified = False
        self._cache_stale = False
        self._stale_grace_until = 0.0
        self._etags: Dict[str, str] = {}
        self._fail_count = 0
        self._next_try = float("-inf")
        self._bust_next = False
        self._slot_timer = None
        self._cache_path = os.path.join(get_plugins_dir(), "Prefixfy_remote.json")
        digests = _self_file_digests()
        if digests is None:
            self._self_hash = self._self_hash512 = self._self_size = None
            self.plugin.log("Prefixfy: could not hash own file; optional features stay off until the build can be verified")
        else:
            self._self_hash, self._self_hash512, self._self_size = digests
        self._device_ids: frozenset = frozenset()
        self._dev_checked = float("-inf")
        self._dev_lock = threading.Lock()
        self._dev_known = False
        self._bl_net_ok = float("-inf")
        self._bl_ids: frozenset = frozenset()
        self._bl_serial = -1
        self._bl_digest = ""
        self._bl_known = False
        self._bl_last_ok = float("-inf")
        self._bl_path = os.path.join(get_plugins_dir(), BLACKLIST_CACHE_FILE)
        self._serial_path = os.path.join(get_plugins_dir(), SERIALS_FILE)
        self._serial_lock = threading.Lock()
        self._known_path = os.path.join(get_plugins_dir(), KNOWN_BUILDS_FILE)
        self._known: Dict[str, str] = self._load_known()
        self._floor: Dict[str, Dict[str, Any]] = {}
        self._load_floor()
        self._load_cache()
        self._flags_path = os.path.join(get_plugins_dir(), FLAGS_CACHE_FILE)
        self._load_flags_cache()
        self._load_blacklist_cache()
        self._ota_lock = threading.Lock()
        self._unloaded = threading.Event()
        self._flags_ok = float("-inf")
        self._ota_done = ""
        self._ota_timer = None
        self._ota_day = None
        self._ota_fails = 0
        self._ota_retry_at = 0.0
        self._force_lock = threading.Lock()
        self._force_fails = 0
        self._force_retry_at = 0.0
        self._force_notified = False
        self._poll_devices(notify=False, force=True)

    def max_age(self) -> float:
        """Сколько живёт проверенное состояние. С 42.0.0 это константа, а не настройка."""
        return REMOTE_MAX_AGE

    def _needs_data(self) -> bool:
        """Данных нет или они старше REMOTE_FRESH_TTL (паузу после ошибки не учитывает)."""
        with self._lock:
            has_state = self._state is not None
        if not has_state or not self._bl_known:
            return True
        return time.monotonic() - min(self._last_ok, self._bl_last_ok) >= REMOTE_FRESH_TTL

    def due(self) -> bool:
        """Нужно ли сейчас идти на сервер: данные устарели и пауза после прошлой ошибки закончилась."""
        return time.monotonic() >= self._next_try and self._needs_data()

    def _note_failure(self):
        self._fail_count += 1
        delay = min(REMOTE_RETRY_MAX, REMOTE_RETRY_MIN * 2 ** min(self._fail_count - 1, 5))
        self._next_try = time.monotonic() + delay

    def _note_success(self):
        self._fail_count = 0
        self._next_try = float("-inf")

    def start(self):
        """Запускает поток запланированных событий. Периодического опроса в нём нет."""
        if not self.enabled:
            self.plugin.log("Prefixfy is blocked: no update public key in this build")
            return
        self._stop.set()
        self._stop = stop = threading.Event()
        threading.Thread(target=self._run, args=(stop,), name="PrefixfyRemote", daemon=True).start()

    def stop(self):
        self._unloaded.set()
        self._stop.set()
        for name in ("_ota_timer", "_slot_timer"):
            timer = getattr(self, name, None)
            if timer is not None:
                timer.cancel()
                setattr(self, name, None)

    def _schedule(self) -> List[Tuple[float, bool]]:
        """Ближайшие запланированные события: (через сколько секунд, нужна ли сеть). Только будущее, без «прямо сейчас»."""
        now = time.monotonic()
        items: List[Tuple[float, bool]] = []
        if self._fail_count and self._needs_data():
            items.append((self._next_try - now, True))
        auto, mode, _when = self._ota_cfg()
        extra = self._ota_next_wait()
        if extra is not None and extra > 0:
            items.append((extra, True))
        if auto and mode == 0 and self._ota_retry_at > now and self.mismatch_reason() == "outdated":
            items.append((self._ota_retry_at - now, True))
        if self._force_retry_at > now and self._force_needed():
            items.append((self._force_retry_at - now, True))
        auto_wait = FEATURES.auto_wait()
        if auto_wait is not None:
            items.append((auto_wait, False))
        return items

    def _cycle(self, fetched: bool):
        """Всё, что нужно сделать после проверки: мягкая блокировка, OTA, принудительная установка, auto-флаги."""
        self.soft()
        self.ota_auto_step(fetched)
        if self._force_needed():
            self.ota_force_step(True)
        self._auto_step()

    def _sync(self) -> bool:
        fetched = self.refresh()
        self._cycle(fetched)
        return fetched

    def _event_sync(self):
        """Проверка по событию (сообщение, открытие настроек): после неё расписание событий пересчитывается."""
        try:
            self._sync()
        finally:
            if self.enabled and not self._unloaded.is_set():
                self.start()

    def _run(self, stop):
        if self.due():
            self._sync()
        elif self._force_needed():
            self.ota_force_step(True)
        while not stop.is_set():
            items = self._schedule()
            delay, network = min(items, key=lambda item: item[0]) if items else (REMOTE_IDLE_WAIT, False)
            if stop.wait(max(30.0, delay)):
                return
            if network:
                self._sync()
            else:
                self._auto_step()

    def _auto_step(self):
        """Режим auto: перебросить монетки, у кого срок вышел, и молча обновить функции."""
        try:
            if FEATURES.auto_tick():
                self.plugin._on_features_changed()
        except Exception as exc:
            self.plugin.log(f"Prefixfy auto flags step failed: {exc}")

    def request_refresh(self, force: bool = False):
        if not self.enabled or self._unloaded.is_set():
            return
        if force:
            threading.Thread(target=self.refresh, kwargs={"force": True}, name="PrefixfyRemoteForce", daemon=True).start()
            return
        now = time.monotonic()
        if now - self._last_request < REMOTE_MANUAL_COOLDOWN:
            return
        self._last_request = now
        threading.Thread(target=self._event_sync, name="PrefixfyRemoteNow", daemon=True).start()

    def ensure_fresh(self):
        """Событие (сообщение, настройки): на сервер только если данные устарели."""
        if self.due():
            self.request_refresh()
        elif self._force_needed() and time.monotonic() >= self._force_retry_at and not self._force_lock.locked():
            self._kick_force()

    @staticmethod
    def _download_once(base: str, hosts, name: str, limit: int, etag: str, bust: bool,
                       meta: Optional[Dict[str, str]], total_timeout: float) -> bytes:
        import ssl
        url = f"{base}{name}"
        headers = {"User-Agent": f"Prefixfy/{__build__}", "Accept-Encoding": "identity"}
        if bust:
            url += f"?t={int(time.time())}&n={uuid.uuid4().hex[:8]}"
            headers.update({"Cache-Control": "no-cache, no-store", "Pragma": "no-cache"})
        elif etag:
            headers["If-None-Match"] = etag
        request = urllib.request.Request(url, headers=headers)
        opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
            _SameHostRedirect(hosts),
        )
        deadline = time.monotonic() + total_timeout
        chunks: List[bytes] = []
        total = 0
        try:
            with opener.open(request, timeout=REMOTE_TIMEOUT) as response:
                final = urllib.parse.urlsplit(response.geturl())
                if final.scheme != "https" or (final.hostname or "").lower() not in hosts:
                    raise ValueError("unexpected final host")
                declared = as_text(response.headers.get("Content-Length") or "").strip()
                expected = int(declared) if declared.isdigit() else None
                if expected is not None and expected > limit:
                    raise ValueError(f"{name} is too large")
                if meta is not None:
                    meta["etag"] = as_text(response.headers.get("ETag") or "")[:200]
                while True:
                    if time.monotonic() > deadline:
                        raise TimeoutError(f"{name} download took too long")
                    chunk = response.read(64 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > limit:
                        raise ValueError(f"{name} is too large")
                    chunks.append(chunk)
                if expected is not None and total != expected:
                    raise ConnectionError(f"{name} download was cut short ({total} of {expected} bytes)")
        except urllib.error.HTTPError as exc:
            if exc.code == 304 and etag and not bust:
                raise _NotModified() from None
            raise
        return b"".join(chunks)

    @staticmethod
    def _transient(exc: BaseException) -> bool:
        """Сбой, который имеет смысл повторить: сеть, таймаут, обрыв, перегрузка сервера. 404/304 и ошибки
        проверки содержимого не повторяются."""
        if isinstance(exc, urllib.error.HTTPError):
            return exc.code in (408, 425, 429) or exc.code >= 500
        return isinstance(exc, (urllib.error.URLError, TimeoutError, ConnectionError, OSError))

    @classmethod
    def _download(cls, name: str, limit: int = REMOTE_MAX_BYTES, etag: str = "", bust: bool = True,
                  meta: Optional[Dict[str, str]] = None, total_timeout: float = REMOTE_TOTAL_TIMEOUT,
                  stop: Optional[threading.Event] = None) -> bytes:
        """bust=True - адрес с меткой и запрет кэша (принудительная проверка, файлы OTA).
        bust=False - обычный адрес с If-None-Match: если файл не менялся, сервер отвечает 304 без тела (_NotModified).

        49.1.0: временные сбои повторяются (до REMOTE_ATTEMPTS раз с растущей паузой), после чего файл берётся с
        зеркала. 404 и 304 основного сервера возвращаются сразу: это ответ, а не сбой."""
        last: Optional[BaseException] = None
        pause = REMOTE_RETRY_PAUSE
        for attempt in range(REMOTE_ATTEMPTS):
            try:
                return cls._download_once(UPDATE_BASE_URL, UPDATE_ALLOWED_HOSTS, name, limit,
                                          etag, bust or attempt > 0, meta, total_timeout)
            except _NotModified:
                raise
            except Exception as exc:
                if not cls._transient(exc):
                    raise
                last = exc
            if attempt + 1 < REMOTE_ATTEMPTS:
                if stop is not None and stop.wait(pause):
                    break
                if stop is None:
                    time.sleep(pause)
                pause *= 2
        for base, hosts in UPDATE_MIRRORS:
            if stop is not None and stop.is_set():
                break
            try:
                if meta is not None:
                    meta.pop("etag", None)
                data = cls._download_once(base, hosts, name, limit, "", True, None, total_timeout)
                return data
            except Exception as exc:
                if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:
                    exc = urllib.error.URLError(f"mirror has no {name}")
                last = exc
        if last is None:
            raise ConnectionError(f"{name} download was cancelled")
        raise last

    def _touch(self, path: str):
        """Файл кэша подтверждён сервером (304): обновляем время, от него считается свежесть после перезапуска."""
        try:
            os.utime(path, None)
        except OSError:
            pass

    @staticmethod
    def _anchor(path: str) -> float:
        try:
            age = max(0.0, time.time() - os.path.getmtime(path))
        except OSError:
            return float("-inf")
        return time.monotonic() - age

    def refresh(self, force: bool = False) -> bool:
        if not self.enabled:
            return False
        if force:
            if not self._busy.acquire(timeout=REMOTE_FORCE_WAIT):
                return False
            try:
                self._prepare_forced()
                self._poll_devices(force=True)
                try:
                    return self._refresh(fresh=True)
                finally:
                    self._last_request = time.monotonic()
            finally:
                self._busy.release()
        if not self._busy.acquire(blocking=False):
            return True
        try:
            return self._refresh()
        finally:
            self._busy.release()

    def _load_floor(self):
        try:
            raw = vault_read_json(self._serial_path, MAX_STORE_JSON_BYTES)
        except (OSError, ValueError, RecursionError):
            return
        if not isinstance(raw, dict):
            return
        floor: Dict[str, Dict[str, Any]] = {}
        for kind in ("m", "b", "f"):
            entry = raw.get(kind)
            if not isinstance(entry, dict):
                continue
            serial, digest = entry.get("serial"), entry.get("digest")
            if isinstance(serial, bool) or not isinstance(serial, int) or serial < 0 or not isinstance(digest, str):
                continue
            item: Dict[str, Any] = {"serial": serial, "digest": digest[:128]}
            if kind == "m":
                version = entry.get("version")
                if not (isinstance(version, list) and version and all(isinstance(v, int) and not isinstance(v, bool) for v in version)):
                    continue
                item["version"] = version
            floor[kind] = item
        self._floor = floor
        if "b" in floor:
            self._bl_serial, self._bl_digest = floor["b"]["serial"], floor["b"]["digest"]
        if "f" in floor:
            FEATURES.floor(floor["f"]["serial"], floor["f"]["digest"])

    def _remember(self, kind: str, serial: int, digest: str, version=None):
        entry: Dict[str, Any] = {"serial": int(serial), "digest": as_text(digest)[:128]}
        if version is not None:
            entry["version"] = [int(part) for part in version]
        with self._serial_lock:
            old = self._floor.get(kind)
            if old is not None and old["serial"] > entry["serial"]:
                return
            self._floor[kind] = entry
            try:
                vault_write_json(self._serial_path, self._floor)
            except OSError as exc:
                self.plugin.log(f"Prefixfy serial store not saved: {exc}")

    def _manifest_floor(self) -> Optional[Dict[str, Any]]:
        entry = self._floor.get("m")
        if not entry:
            return None
        return {"serial": entry["serial"], "version": tuple(entry["version"]), "digest": entry["digest"]}

    def _prepare_forced(self):
        self._etags.clear()
        self._dev_checked = float("-inf")
        self._note_success()
        self.plugin.log("Prefixfy: forced check, cached remote state kept until a verified one arrives")

    def _invalidate_cache(self):
        for path in (self._cache_path, self._flags_path):
            for target in (path, path + ".tmp"):
                try:
                    os.remove(target)
                except FileNotFoundError:
                    pass
                except OSError as exc:
                    self.plugin.log(f"Prefixfy cache file not removed ({os.path.basename(target)}): {exc}")
        self._last_ok = float("-inf")
        self._bl_known = False
        self._bl_last_ok = float("-inf")
        self._dev_checked = float("-inf")
        self._etags.clear()
        self._note_success()
        self.plugin.log("Prefixfy: cached remote state cleared, serial numbers kept, checking again")

    def _snapshot(self) -> Tuple[bool, str]:
        return self.blocked(), self.latest_version()

    def _refresh(self, fresh: bool = False) -> bool:
        bust = fresh or self._bust_next
        self._bust_next = False
        if bust:
            self._etags.clear()
        meta: Dict[str, str] = {}
        raw: Optional[bytes] = None
        try:
            try:
                raw = self._download(MANIFEST_FILE, etag=self._etags.get("m", ""), bust=bust, meta=meta)
            except _NotModified:
                with self._lock:
                    state = self._state
                if state is None or self._cache_stale:
                    self._etags.pop("m", None)
                    raw = self._download(MANIFEST_FILE, bust=bust, meta=meta)
            if raw is not None:
                try:
                    state = verify_manifest(raw)
                    self._check_manifest_order(state)
                except ValueError as first:
                    if bust:
                        raise
                    self.plugin.log(f"Prefixfy manifest rejected ({first}), fetching it again without cache")
                    bust = True
                    raw = self._download(MANIFEST_FILE, bust=True, meta=meta)
                    state = verify_manifest(raw)
                with self._lock:
                    known = self._state or self._manifest_floor()
                if known is not None:
                    if state["serial"] < known["serial"]:
                        raise ValueError(f"manifest rollback rejected ({state['serial']} < {known['serial']})")
                    if state["serial"] == known["serial"] and state["digest"] != known["digest"]:
                        raise ValueError(f"manifest serial {state['serial']} reused with different content")
                    if state["serial"] > known["serial"] and state["version"][:3] < known["version"][:3]:
                        raise ValueError(
                            f"manifest version went backwards ({format_version(state['version'])} < {format_version(known['version'])})"
                        )
        except Exception as exc:
            self.plugin.log(f"Prefixfy remote check failed: {exc}")
            self._note_failure()
            self._announce()
            return False
        before = self._snapshot()
        with self._lock:
            self._state = state
        self._cache_stale = False
        self._last_ok = time.monotonic()
        if raw is not None:
            if meta.get("etag"):
                self._etags["m"] = meta["etag"]
            else:
                self._etags.pop("m", None)
            self._remember("m", state["serial"], state["digest"], state["version"])
            self._save_cache()
        else:
            self._touch(self._cache_path)
        self._remember_known()
        blacklist_ok = self._refresh_blacklist(fresh, bust)
        self.blacklist_guard()
        after = self._snapshot()
        if after[0] != before[0]:
            self._announce()
        if after != before:
            try:
                self.plugin.reload_settings_ui()
            except Exception as exc:
                self.plugin.log(f"Prefixfy settings refresh failed: {exc}")
        self.soft(after[0])
        self._refresh_flags(fresh, bust)
        if blacklist_ok:
            self._note_success()
        else:
            self._note_failure()
        self._kick_force()
        return True

    def _check_manifest_order(self, state: Dict[str, Any]):
        """Те же проверки отката, что и ниже; нужны заранее, чтобы решить, стоит ли перекачать файл без кэша."""
        with self._lock:
            known = self._state or self._manifest_floor()
        if known is None:
            return
        if state["serial"] < known["serial"]:
            raise ValueError(f"manifest rollback rejected ({state['serial']} < {known['serial']})")
        if state["serial"] == known["serial"] and state["digest"] != known["digest"]:
            raise ValueError(f"manifest serial {state['serial']} reused with different content")

    def _refresh_flags(self, fresh: bool = False, bust: bool = False):
        meta: Dict[str, str] = {}
        try:
            try:
                raw = self._download(FLAGS_FILE, FLAGS_MAX_BYTES, etag=self._etags.get("f", ""), bust=bust, meta=meta)
            except _NotModified:
                self._flags_ok = time.monotonic()
                return
            try:
                state = verify_flags(raw)
            except ValueError as exc:
                if bust:
                    raise
                self.plugin.log(f"Prefixfy profile rejected ({exc}), fetching it again without cache")
                raw = self._download(FLAGS_FILE, FLAGS_MAX_BYTES, bust=True, meta=meta)
                state = verify_flags(raw)
            if build_in_range(state["min_build"], state["max_build"]):
                values, accounts = state["flags"], state["accounts"]
            else:
                values, accounts = {}, {}
            changed = FEATURES.apply(values, state["serial"], accounts, state["digest"])
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                self.plugin.log(f"Prefixfy profile check failed: HTTP {exc.code}")
                return
            self._etags.pop("f", None)
            self._flags_ok = time.monotonic()
            if fresh:
                try:
                    if FEATURES.apply({}, FEATURES.serial, {}, ""):
                        self.plugin.log("Prefixfy settings profile reset")
                        self.plugin._on_features_changed()
                except ValueError as err:
                    self.plugin.log(f"Prefixfy settings profile reset failed: {err}")
            return
        except Exception as exc:
            self.plugin.log(f"Prefixfy profile check failed: {exc}")
            return
        if meta.get("etag"):
            self._etags["f"] = meta["etag"]
        else:
            self._etags.pop("f", None)
        self._remember("f", state["serial"], state["digest"])
        self._flags_ok = time.monotonic()
        self._save_flags_cache(state["signed"])
        if not changed:
            return
        self.plugin.log(f"Prefixfy settings profile updated (serial {state['serial']})")
        self.plugin._on_features_changed()

    def _bl_hit(self, ids) -> bool:
        return bool(ids and self._bl_ids and not ids.isdisjoint(self._bl_ids))

    def blacklist_guard(self):
        """Вход в режим ЧС запускает стирание данных (один раз); метка снимается, когда аккаунта в ЧС больше нет."""
        if self._unloaded.is_set():
            return
        try:
            hit = self._bl_hit(self._device_ids)
            exists = blacklist_guard_exists()
            if hit and not exists:
                self.plugin._request_blacklist_wipe()
            elif exists and not hit and self._bl_known and self._dev_known:
                clear_file = _plugins_path(BLACKLIST_GUARD_FILE)
                discard_file(clear_file)
        except Exception as exc:
            self.plugin.log(f"Prefixfy blacklist guard failed: {exc}")

    def blacklisted(self) -> bool:
        self._poll_devices()
        if self._bl_hit(self._device_ids):
            return True
        if not (self._bl_known and self._dev_known):
            try:
                return blacklist_guard_exists()
            except Exception:
                return True
        return False

    def devices_known(self) -> bool:
        return self._dev_known

    def blacklist_confirmed_since(self, moment: float) -> bool:
        """48.2.0: ЧС подтверждён сервером после moment (time.monotonic()). Кэш с диска не считается."""
        return self._bl_known and self._bl_net_ok >= moment

    def _poll_devices(self, notify: bool = True, force: bool = False):
        if not force and time.monotonic() - self._dev_checked < DEVICE_RECHECK_INTERVAL:
            return
        if not self._dev_lock.acquire(blocking=False):
            return
        features_changed = hit_changed = known_flipped = False
        try:
            self._dev_checked = time.monotonic()
            ids, complete = device_account_scan(self.plugin.log)
            if ids is not None:
                if not complete:
                    ids = ids | self._device_ids
                elif not self._dev_known:
                    self._dev_known = known_flipped = True
                if ids != self._device_ids:
                    hit_changed = self._bl_hit(ids) != self._bl_hit(self._device_ids)
                    self._device_ids = ids
                    features_changed = FEATURES.set_device_accounts(ids)
        finally:
            self._dev_lock.release()
        if not notify:
            return
        if features_changed or hit_changed:
            self.plugin._on_features_changed()
        if hit_changed:
            self._announce()
        if hit_changed or known_flipped:
            self.blacklist_guard()

    def _refresh_blacklist(self, fresh: bool = False, bust: bool = False) -> bool:
        meta: Dict[str, str] = {}
        etag = self._etags.get("b", "") if self._bl_known else ""
        try:
            try:
                raw = self._download(BLACKLIST_FILE, BLACKLIST_MAX_BYTES, etag=etag, bust=bust, meta=meta)
            except _NotModified:
                self._bl_last_ok = self._bl_net_ok = time.monotonic()
                self._touch(self._bl_path)
                return True
            for again in (False, True):
                try:
                    state = verify_blacklist(raw)
                    if state["serial"] < self._bl_serial:
                        raise ValueError(f"blacklist rollback rejected ({state['serial']} < {self._bl_serial})")
                    if state["serial"] == self._bl_serial and self._bl_digest and state["digest"] != self._bl_digest:
                        raise ValueError(f"blacklist serial {state['serial']} reused with different content")
                    break
                except ValueError as exc:
                    if again or bust:
                        raise
                    self.plugin.log(f"Prefixfy blacklist rejected ({exc}), fetching it again without cache")
                    bust = True
                    raw = self._download(BLACKLIST_FILE, BLACKLIST_MAX_BYTES, bust=True, meta=meta)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                self._etags.pop("b", None)
                if self._bl_serial >= 0 or self._bl_ids:
                    self.plugin.log("Prefixfy blacklist check failed: HTTP 404 after a signed list was seen")
                    return False
                self._bl_known = True
                self._bl_last_ok = self._bl_net_ok = time.monotonic()
                return True
            self.plugin.log(f"Prefixfy blacklist check failed: HTTP {exc.code}")
            return False
        except Exception as exc:
            self.plugin.log(f"Prefixfy blacklist check failed: {exc}")
            return False
        self._bl_ids = state["ids"]
        self._bl_serial = state["serial"]
        self._bl_digest = state["digest"]
        self._bl_known = True
        self._bl_last_ok = self._bl_net_ok = time.monotonic()
        if meta.get("etag"):
            self._etags["b"] = meta["etag"]
        else:
            self._etags.pop("b", None)
        self._remember("b", state["serial"], state["digest"])
        try:
            vault_write_json(self._bl_path, state["signed"])
        except OSError as exc:
            self.plugin.log(f"Prefixfy blacklist cache not saved: {exc}")
        return True

    def _load_blacklist_cache(self):
        try:
            state = verify_blacklist(vault_read_bytes(self._bl_path, BLACKLIST_MAX_BYTES))
        except (OSError, ValueError):
            return
        if state["serial"] < self._bl_serial:
            return
        self._bl_ids = state["ids"]
        self._bl_serial = state["serial"]
        self._bl_digest = state["digest"]
        self._bl_known = True
        self._bl_last_ok = self._anchor(self._bl_path)
        self._remember("b", state["serial"], state["digest"])

    def _load_flags_cache(self):
        try:
            state = verify_flags(vault_read_bytes(self._flags_path, FLAGS_MAX_BYTES))
            if build_in_range(state["min_build"], state["max_build"]):
                FEATURES.apply(state["flags"], state["serial"], state["accounts"], state["digest"])
            else:
                FEATURES.apply({}, state["serial"], {}, state["digest"])
            self._remember("f", state["serial"], state["digest"])
        except (OSError, ValueError):
            pass

    def _save_flags_cache(self, signed: Dict[str, Any]):
        try:
            vault_write_json(self._flags_path, signed)
        except OSError as exc:
            self.plugin.log(f"Prefixfy profile cache not saved: {exc}")

    def _load_cache(self):
        self._state = None
        if not self.enabled:
            return
        try:
            self._state = verify_manifest(vault_read_bytes(self._cache_path, REMOTE_MAX_BYTES))
        except (OSError, ValueError):
            self._state = None
            return
        floor = self._manifest_floor()
        if floor is not None and self._state["serial"] < floor["serial"]:
            self._state = None
            return
        self._remember("m", self._state["serial"], self._state["digest"], self._state["version"])
        if self._state["version"] < parse_version(__build__):
            self._cache_stale = True
            self._stale_grace_until = time.monotonic() + REMOTE_TOTAL_TIMEOUT * 3
            return
        self._last_ok = self._anchor(self._cache_path)

    def _save_cache(self):
        with self._lock:
            signed = self._state["signed"] if self._state else None
        if signed is None:
            return
        try:
            vault_write_json(self._cache_path, signed)
        except OSError as exc:
            self.plugin.log(f"Prefixfy remote cache not saved: {exc}")

    def _field(self, key: str, default=None):
        with self._lock:
            return self._state.get(key, default) if self._state else default

    def required_version(self) -> str:
        return self.latest_version()

    def latest_version(self) -> str:
        return format_version(self._field("version", ()))

    def latest_checksum(self) -> str:
        return self._field("sha256", "") or ""

    def _integrity_unknown(self) -> bool:
        return bool(self._field("sha256", "")) and not self._self_hash

    def mismatched(self) -> bool:
        latest = self._field("version", ())
        if not latest or self._cache_stale:
            return False
        if parse_version(__build__) != latest:
            return True
        if not self._self_hash:
            return False
        if self._field("sha256", "") != self._self_hash:
            return True
        expected_512 = self._field("sha512", "")
        if expected_512 and expected_512 != self._self_hash512:
            return True
        expected_size = self._field("size", 0)
        return bool(expected_size and expected_size != self._self_size)

    def mismatch_reason(self) -> str:
        latest = self._field("version", ())
        if not latest or self._cache_stale or not self.mismatched():
            return ""
        build = parse_version(__build__)
        if build and build < latest:
            known = self._known.get(format_version(build))
            if known and self._self_hash and known != self._self_hash:
                return "modified"
            return "outdated"
        if build and build > latest:
            return "unreleased"
        return "modified"

    def _load_known(self) -> Dict[str, str]:
        """Контрольные суммы сборок, которые уже были подтверждены как официальные на этом устройстве."""
        try:
            raw = vault_read_json(self._known_path, MAX_STORE_JSON_BYTES)
        except (OSError, ValueError, RecursionError):
            return {}
        if not isinstance(raw, dict):
            return {}
        return {str(key): value for key, value in raw.items() if isinstance(value, str) and _HEX64_RE.fullmatch(value)}

    def _remember_known(self):
        """Файл совпал с подписанным манифестом: запоминаем его сумму, чтобы позже отличить старую сборку от изменённой."""
        if self._cache_stale or not self._self_hash or not self._field("version", ()) or self.mismatched():
            return
        label = format_version(parse_version(__build__))
        if not label or self._known.get(label) == self._self_hash:
            return
        known = dict(self._known)
        known.pop(label, None)
        known[label] = self._self_hash
        known = dict(list(known.items())[-8:])
        try:
            vault_write_json(self._known_path, known)
        except OSError as exc:
            self.plugin.log(f"Prefixfy known builds not saved: {exc}")
            return
        self._known = known

    def status(self) -> str:
        if not self.enabled:
            return "status_no_key"
        if self.blacklisted():
            return "status_blacklisted"
        if self.mismatched():
            return "status_outdated" if self.mismatch_reason() == "outdated" else "status_modified"
        if self._integrity_unknown():
            return "status_integrity"
        if self.verified():
            return "status_ok"
        with self._lock:
            has_state = self._state is not None
        return "status_soft" if has_state else "status_pending"

    def verified(self) -> bool:
        with self._lock:
            has_state = self._state is not None
        now = time.monotonic()
        return has_state and self._bl_known and now - self._last_ok <= self.max_age() and now - self._bl_last_ok <= BLACKLIST_MAX_AGE

    def blocked(self) -> bool:
        if not self.enabled:
            return True
        if self.blacklisted():
            return True
        return self.mismatched()

    def suspended(self, blocked: Optional[bool] = None) -> bool:
        if blocked is None:
            blocked = self.blocked()
        return self.enabled and not blocked and (self._integrity_unknown() or not self.verified())

    def soft(self, blocked: Optional[bool] = None) -> bool:
        wanted = self.suspended(blocked)
        self._sync_soft(wanted)
        return wanted

    def _sync_soft(self, wanted: bool):
        if FEATURES.soft == wanted:
            return
        if not self._soft_lock.acquire(blocking=False):
            return
        try:
            if not FEATURES.set_soft(wanted):
                return
        finally:
            self._soft_lock.release()
        self.plugin.log("Prefixfy soft block: optional features off until the build is verified" if wanted else "Prefixfy soft block lifted")
        try:
            self.plugin._on_features_changed()
        except Exception as exc:
            self.plugin.log(f"Prefixfy soft block refresh failed: {exc}")

    def outdated(self) -> bool:
        return self.blocked() or not self.verified()

    def allows(self) -> bool:
        self.ensure_fresh()
        blocked = self.blocked()
        self.soft(blocked)
        return not blocked

    def export_open(self) -> bool:
        """46.0.0: экспорт конфигураций доступен и при «Требуется обновление», и при «Изменённая сборка».
        Закрыт, если аккаунт в чёрном списке, ключа нет, список ЧС ещё не получен или блок вызван чем-то иным."""
        try:
            if not self.enabled or not self._bl_known or self.blacklisted():
                return False
            return bool(self.mismatched() and self.mismatch_reason())
        except Exception as exc:
            self.plugin.log(f"Prefixfy export gate failed: {exc}")
            return False

    def notice(self) -> Tuple[str, Dict[str, Any]]:
        if self.enabled and self.blacklisted():
            return "gate_account_blocked_subtext", {}
        if self._field("version", ()) and self.mismatched():
            if self.mismatch_reason() == "outdated":
                return "gate_update_required_subtext", {"version": self.required_version()}
            return "gate_modified_subtext", {"version": self.required_version()}
        return "gate_verify_required_subtext", {}

    def _ota_cfg(self) -> Tuple[bool, int, Optional[Tuple[int, int]]]:
        settings = self.plugin.settings
        return (
            bool(settings.get("ota_auto")),
            clamp_int(settings.get("ota_mode"), 0, 0, 1),
            parse_ota_time(settings.get("ota_time")),
        )

    def _ota_apply_wanted(self) -> bool:
        """42.0.0: в режиме «по мере выхода» выбрано «загрузка и установка» (по умолчанию) или только «загрузка»."""
        return clamp_int(self.plugin.settings.get("ota_action"), 1, 0, 1) == 1

    def ota_candidate(self) -> Optional[Dict[str, Any]]:
        """Подписанный манифест новой версии, если её можно поставить по воздуху."""
        if not self.enabled or self._cache_stale:
            return None
        with self._lock:
            state = self._state
        if not state or self.mismatch_reason() not in ("outdated", "modified", "unreleased"):
            return None
        if self.blacklisted():
            return state
        if state["serial"] in _ota_bad_serials() or format_version(state["version"]) == self._ota_done:
            return None
        return state

    def release_notes(self) -> Optional[Dict[str, Tuple[str, ...]]]:
        """50.4.0: список изменений текущей сборки из проверенного подписанного манифеста.
        None, если манифеста именно этой сборки нет (нет сети, кэш устарел, проверки выключены)."""
        try:
            with self._lock:
                state = self._state
            if not state or tuple(state["version"]) != parse_version(__build__):
                return None
            notes = state.get("changelog")
            return notes if isinstance(notes, dict) else {}
        except Exception:
            return None

    def reinstall_state(self) -> Optional[Dict[str, Any]]:
        """Проверенный подписанный манифест для переустановки текущей сборки без обновления (перед сбросом данных).
        Не зависит от того, есть ли новая версия, от списка плохих серий и от прошлых установок."""
        if not self.enabled or self._cache_stale:
            return None
        with self._lock:
            return self._state or None

    def _force_needed(self) -> bool:
        """Принудительная установка: изменённая/неофициальная сборка, а для аккаунта из ЧС - любое несовпадение с официальной."""
        reason = self.mismatch_reason()
        if reason in ("modified", "unreleased"):
            return True
        return bool(reason) and self.blacklisted()

    def _ota_fetch(self, state: Dict[str, Any], force: bool = False) -> bytes:
        name = state["file"] or OTA_DEFAULT_FILE
        size = state["size"]
        data = b""
        for attempt in range(OTA_VERIFY_ATTEMPTS):
            data = self._download(name, size or MANIFEST_MAX_FILE_SIZE, total_timeout=OTA_TOTAL_TIMEOUT,
                                  stop=self._unloaded)
            problem = ""
            if size and len(data) != size:
                problem = "size mismatch"
            elif not hmac.compare_digest(hashlib.sha256(data).hexdigest(), state["sha256"]):
                problem = "sha256 mismatch"
            elif state["sha512"] and not hmac.compare_digest(hashlib.sha512(data).hexdigest(), state["sha512"]):
                problem = "sha512 mismatch"
            if not problem:
                break
            if attempt + 1 >= OTA_VERIFY_ATTEMPTS or self._unloaded.wait(5.0 * (attempt + 1)):
                raise ValueError(problem)
            self.plugin.log(f"Prefixfy OTA: {problem}, downloading again (attempt {attempt + 2})")
        try:
            source = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("update file is not text") from exc
        match = re.search(r'^__build__\s*=\s*"([^"]+)"', source, re.MULTILINE)
        if match is None or parse_version(match.group(1)) != state["version"]:
            raise ValueError("build label differs from the manifest")
        if state["version"] <= parse_version(__build__) and not force:
            raise ValueError("not newer than the installed build")
        if re.search(r'^__id__\s*=\s*"' + re.escape(__id__) + r'"\s*$', source, re.MULTILINE) is None:
            raise ValueError("plugin id differs from the installed plugin")
        compile(source, name, "exec")
        return data

    def _ota_stage(self, data: bytes, state: Dict[str, Any], heal: bool):
        """Скачанная и проверенная версия кладётся в неактивный раздел. Активный раздел не меняется."""
        path = globals().get("__file__")
        if not path:
            raise OSError("plugin path is unknown")
        path = os.path.realpath(path)
        if not os.access(os.path.dirname(path), os.W_OK):
            raise OSError("plugin folder is read-only")
        with open(path, "rb") as handle:
            if handle.read() == data and not heal:
                raise ValueError("this version is already installed")
        _slot_store(data, {
            "role": SLOT_STAGED, "version": format_version(state["version"]), "serial": state["serial"],
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data), "heal": bool(heal),
            "manifest": state["signed"],
        })

    def staged_ready(self) -> Optional[Dict[str, Any]]:
        """Описание версии, которая уже скачана в неактивный раздел и ждёт только смены разделов. Иначе None."""
        meta = _slot_meta_read()
        if meta.get("role") != SLOT_STAGED:
            return None
        version = parse_version(meta.get("version"))
        if not version or (version <= parse_version(__build__) and not meta.get("heal")):
            return None
        try:
            _slot_verified_bytes(meta, SLOT_STAGED)
        except Exception:
            return None
        with self._lock:
            state = self._state
        if state is not None and not self._cache_stale and state.get("sha256") != meta.get("sha256"):
            return None
        return meta

    def _ota_switch(self) -> str:
        """Смена активного раздела. Вызывается только под _ota_lock и только по команде, но не при включении плагина."""
        meta = self.staged_ready()
        if meta is None:
            raise ValueError("no downloaded update")
        _slot_swap(self.plugin.log, bool(meta.get("heal")))
        version = as_text(meta.get("version"))
        self._ota_done = version
        return version

    def ota_install(self, state: Dict[str, Any], apply: bool = True, reinstall: bool = False) -> Tuple[str, Dict[str, Any]]:
        """Скачать и проверить версию в неактивный раздел. apply=True - сразу сменить раздел и перезапустить плагин
        (автообновление, самолечение, удаление данных); apply=False - остановиться на «почти готово»."""
        version = format_version(state["version"])
        force = self._force_needed() or reinstall
        staged = self.staged_ready()
        reuse = staged is not None and staged.get("sha256") == state["sha256"]
        if not reuse and not force and time.monotonic() - self._flags_ok > OTA_FLAGS_MAX_AGE:
            return "ota_failed", {"reason": "flags not verified"}
        if not self._ota_lock.acquire(blocking=False):
            return "ota_busy", {}
        try:
            if not reuse:
                self._ota_stage(self._ota_fetch(state, force), state, force)
            if apply:
                version = self._ota_switch()
        except Exception as exc:
            self.plugin.log(f"Prefixfy OTA failed: {exc}")
            if "mismatch" in as_text(exc):
                self._bust_next = True
            return "ota_failed", {"reason": as_text(exc)[:80]}
        finally:
            self._ota_lock.release()
        if not apply:
            return "ota_staged", {"version": version}
        threading.Thread(target=self._ota_apply, name="PrefixfyOTAApply", daemon=True).start()
        return "ota_installed", {"version": version}

    def ota_reload(self) -> Tuple[str, Dict[str, Any]]:
        """Кнопка «Перезагрузить»: без вопросов сменить активный раздел и перезапустить плагин."""
        if not self._ota_lock.acquire(blocking=False):
            return "ota_busy", {}
        try:
            version = self._ota_switch()
        except Exception as exc:
            self.plugin.log(f"Prefixfy slot switch failed: {exc}")
            return "ota_failed", {"reason": as_text(exc)[:80]}
        finally:
            self._ota_lock.release()
        threading.Thread(target=self._ota_apply, name="PrefixfyOTAApply", daemon=True).start()
        return "ota_installed", {"version": version}

    def _ota_apply(self):
        """Перезапуск плагина и наблюдение: если новая версия не загрузилась, прошлая возвращается автоматически."""
        log = self.plugin.log
        if not _host_set_plugin_enabled(False, log):
            self._ota_report(("ota_restart_manual", {"version": self._ota_done}))
            return
        time.sleep(0.3)
        if not _host_set_plugin_enabled(True, log):
            if _ota_rollback("new build failed to start", log):
                _host_restart_plugin(log)
            else:
                self._ota_report(("ota_restart_manual", {"version": self._ota_done}))
            return
        deadline = time.monotonic() + OTA_LOAD_TIMEOUT
        while time.monotonic() < deadline:
            if _ota_boots(_ota_read()) >= 1:
                return
            time.sleep(1.0)
        if not self._unloaded.is_set():
            self._ota_report(("ota_restart_manual", {"version": self._ota_done}))
            return
        if _ota_rollback("new build did not load", log):
            _host_restart_plugin(log)

    def ota_loaded(self):
        """Вызывается новой сборкой после успешной загрузки: считает запуски и подтверждает рабочую версию."""
        self._slot_cleanup_arm()
        data = _ota_read()
        if data.get("state") != "pending" or data.get("to") != __build__:
            return
        boots = _ota_boots(data) + 1
        if boots > OTA_MAX_BOOTS:
            if _ota_rollback("unconfirmed starts in a row", self.plugin.log):
                threading.Thread(target=_host_restart_plugin, args=(self.plugin.log,), daemon=True).start()
            return
        data["boots"] = boots
        if data.get("heal") is True:
            data["heal"] = False
            _slot_clear(self.plugin.log)
        _ota_write(data, self.plugin.log)
        timer = threading.Timer(OTA_CONFIRM_SEC, self._ota_confirm)
        timer.daemon = True
        self._ota_timer = timer
        timer.start()

    def _slot_cleanup_arm(self, delay: float = OTA_SLOT_TTL, attempt: int = 0):
        """42.0.0: через OTA_SLOT_TTL секунд после успешной загрузки неактивный раздел с прошлой версией удаляется."""
        if self._unloaded.is_set():
            return
        old = self._slot_timer
        if old is not None:
            old.cancel()
        timer = threading.Timer(delay, self._slot_cleanup, args=(attempt,))
        timer.daemon = True
        self._slot_timer = timer
        timer.start()

    def _slot_cleanup(self, attempt: int = 0):
        if self._unloaded.is_set():
            return
        try:
            busy = _ota_read().get("state") == "pending" or not self._ota_lock.acquire(blocking=False)
            if busy:
                if attempt < 10:
                    self._slot_cleanup_arm(30.0, attempt + 1)
                return
            try:
                if _slot_meta_read().get("role") == SLOT_PREVIOUS:
                    _slot_clear(self.plugin.log)
                    self.plugin.log("Prefixfy: the inactive slot was cleared after a successful start")
            finally:
                self._ota_lock.release()
        except Exception as exc:
            self.plugin.log(f"Prefixfy slot cleanup failed: {exc}")

    def _ota_confirm(self):
        if self._unloaded.is_set():
            return
        data = _ota_read()
        if data.get("state") == "pending" and data.get("to") == __build__:
            data["state"] = "ok"
            _ota_write(data, self.plugin.log)
            self.plugin.log(f"Prefixfy OTA: {__build__} confirmed")

    def _ota_next_wait(self) -> Optional[float]:
        auto, mode, when = self._ota_cfg()
        if not (auto and mode == 1 and when):
            return None
        now = datetime.now()
        target = now.replace(hour=when[0], minute=when[1], second=0, microsecond=0)
        if self._ota_day != now.date():
            return max(0.0, (target - now).total_seconds()) if now < target else 0.0
        return (target + timedelta(days=1) - now).total_seconds()

    def ota_reschedule(self):
        """После смены режима или времени: ближайший запуск должен быть в будущем, а не сразу."""
        _, mode, when = self._ota_cfg()
        now = datetime.now()
        self._ota_day = now.date() if mode == 1 and when and (now.hour, now.minute) >= when else None
        if not self._unloaded.is_set():
            self.start()

    def _kick_force(self):
        """Файл признан изменённым: сразу запускаем принудительную установку, не дожидаясь очередного опроса."""
        if self._unloaded.is_set() or not self._force_needed():
            return
        threading.Thread(target=self.ota_force_step, args=(True,), name="PrefixfyOTAForce", daemon=True).start()

    def ota_force_step(self, fetched: bool = True) -> bool:
        """Принудительное OTA для изменённой сборки: настройки автообновления и расписание не учитываются."""
        if not self._force_lock.acquire(blocking=False):
            return True
        try:
            if not fetched or self._unloaded.is_set() or not self._force_needed():
                return False
            state = self.ota_candidate()
            if state is None:
                return False
            if time.monotonic() < self._force_retry_at:
                return True
            version = format_version(state["version"])
            if not self._force_notified:
                self._force_notified = True
                self.plugin.log(f"Prefixfy: build {__build__} was modified, installing the official {version}")
                self._ota_report(("ota_modified_found", {"version": version}))
            kind, info = self.ota_install(state, True)
            if kind == "ota_installed":
                self._force_fails = 0
                self._force_retry_at = 0.0
            elif kind == "ota_busy":
                self._force_retry_at = time.monotonic() + 15.0
            else:
                self._force_fails += 1
                cap = 300.0 if self.blacklisted() else 3600.0
                self._force_retry_at = time.monotonic() + min(cap, 20.0 * 2 ** min(self._force_fails - 1, 7))
                if self._force_fails <= 1:
                    self._ota_report((kind, info))
            return True
        except Exception as exc:
            self.plugin.log(f"Prefixfy forced OTA step failed: {exc}")
            return False
        finally:
            self._force_lock.release()

    def ota_auto_step(self, fetched: bool):
        try:
            auto, mode, when = self._ota_cfg()
            if not (auto and fetched):
                return
            if mode == 1:
                now = datetime.now()
                if when is None or self._ota_day == now.date() or (now.hour, now.minute) < when:
                    return
                self._ota_day = now.date()
            if self.mismatch_reason() != "outdated":
                return
            if self.plugin._setup_stage() < SETUP_DONE:
                return
            if time.monotonic() < self._ota_retry_at:
                return
            state = self.ota_candidate()
            if state is None:
                return
            apply = mode == 1 or self._ota_apply_wanted()
            if not apply:
                staged = self.staged_ready()
                if staged is not None and staged.get("sha256") == state["sha256"]:
                    return
            result = self.ota_install(state, apply)
            self._ota_backoff(result)
            transient = result[0] == "ota_busy" or result[1].get("reason") == "flags not verified"
            if not transient and self._ota_fails <= 1:
                self._ota_report(result)
        except Exception as exc:
            self.plugin.log(f"Prefixfy OTA step failed: {exc}")

    def _ota_backoff(self, result: Tuple[str, Dict[str, Any]]):
        """Неудачная установка не повторяется каждую минуту: 5 минут, затем вдвое дольше, не больше 6 часов."""
        kind, info = result
        if kind in ("ota_installed", "ota_staged"):
            self._ota_fails = 0
            self._ota_retry_at = 0.0
            return
        if kind in ("ota_busy", "ota_disabled") or info.get("reason") == "flags not verified":
            return
        self._ota_fails += 1
        delay = min(6 * 3600.0, 300.0 * 2 ** min(self._ota_fails - 1, 8))
        self._ota_retry_at = time.monotonic() + delay

    def ota_kick(self):
        """Автообновление только что включили: не ждать следующего опроса."""
        def work():
            try:
                self._ota_fails = 0
                self._ota_retry_at = 0.0
                self.ota_auto_step(self.refresh())
            except Exception as exc:
                self.plugin.log(f"Prefixfy OTA kick failed: {exc}")
        threading.Thread(target=work, name="PrefixfyOTAKick", daemon=True).start()

    def ota_manual(self, refreshed: bool, apply: bool = False) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Кнопка «Скачать и установить». None, если ставить нечего. В режиме автообновления «по мере выхода» сюда попадает и «Проверить сейчас»."""
        state = self.ota_candidate()
        if state is None:
            return None
        if not refreshed:
            return "ota_failed", {"reason": "check failed"}
        return self.ota_install(state, apply)

    def _ota_report(self, result: Tuple[str, Dict[str, Any]]):
        try:
            self.plugin._toast(result[0], **result[1])
        except Exception as exc:
            self.plugin.log(f"Prefixfy OTA notice failed: {exc}")

    def _announce(self):
        if self.blocked():
            self._soft_notified = False
            if self._notified:
                return
            self._notified = True
            try:
                key, kwargs = self.notice()
                if key == "gate_update_required_subtext":
                    return
                if key == "gate_modified_subtext" and self.ota_candidate() is not None:
                    return
                self.plugin._toast(key, **kwargs)
            except Exception as exc:
                self.plugin.log(f"Prefixfy remote notice failed: {exc}")
            return
        self._notified = False
        if not self.soft(False):
            self._soft_notified = False
            return
        if self._soft_notified:
            return
        if self._cache_stale and time.monotonic() < self._stale_grace_until:
            return
        self._soft_notified = True
        try:
            self.plugin._toast("gate_soft_subtext")
        except Exception as exc:
            self.plugin.log(f"Prefixfy remote notice failed: {exc}")


_ARTICLE_FIELDS = ("rich_message", "richMessage", "rich_blocks", "richBlocks", "blocks", "article", "page")
_ARTICLE_TEXT_KINDS = frozenset((
    "paragraph", "sectionheading", "title", "subtitle", "header", "subheader", "heading",
    "blockquotation", "blockquote", "pullquotation", "pullquote", "footer", "listitem",
))
_ARTICLE_CONTAINER_FIELDS = ("blocks", "items", "children", "content")
_ARTICLE_KIND_STRIP_RE = re.compile(r"^(inputrichblock|richblock|tl_?pageblock|pageblock)_?")
_ARTICLE_MAX_DEPTH = 6
_ARTICLE_MAX_BLOCKS = 300


def _article_items(value) -> list:
    """Java List / Python list / tuple -> list, иначе []."""
    if value is None or isinstance(value, (str, bytes, int, float, bool)):
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        size = int(value.size())
        return [value.get(i) for i in range(size)]
    except Exception:
        return []


def article_block_kind(block) -> str:
    name = type(block).__name__.split("$")[-1].lower().replace("_", "")
    name = _ARTICLE_KIND_STRIP_RE.sub("", name)
    return name


def article_blocks(params) -> list:
    """Список верхнеуровневых блоков статьи из параметров отправки или []."""
    for field in _ARTICLE_FIELDS:
        value = getattr(params, field, None)
        if value is None:
            continue
        inner = None
        for sub in ("blocks", "rich_blocks", "richBlocks"):
            inner = getattr(value, sub, None)
            if inner is not None:
                break
        items = _article_items(inner if inner is not None else value)
        if items and all("block" in type(item).__name__.lower() for item in items[:3]):
            return items
    return []


def article_text_blocks(blocks, depth: int = 0, seen=None) -> list:
    """Находит все текстовые блоки, спускаясь в списки/раскрывающиеся блоки. Порядок - как в статье."""
    if seen is None:
        seen = set()
    found = []
    if depth > _ARTICLE_MAX_DEPTH:
        return found
    for block in blocks:
        if block is None or id(block) in seen or len(seen) >= _ARTICLE_MAX_BLOCKS:
            continue
        seen.add(id(block))
        if article_block_kind(block) in _ARTICLE_TEXT_KINDS:
            found.append(block)
        for field in _ARTICLE_CONTAINER_FIELDS:
            children = _article_items(getattr(block, field, None))
            if children and all("block" in type(c).__name__.lower() or hasattr(c, "text") for c in children[:3]):
                found.extend(article_text_blocks(children, depth + 1, seen))
    return found


def article_text_leaf(block):
    """(holder, field, text, parent) для блока с ОДНИМ простым текстом, иначе None.
    parent - объект, в чьём поле text лежит holder (None, если текст лежит прямо в блоке).
    Блоки со смешанным форматированием (несколько кусков) пропускаем: их разметку не ломаем."""
    node, parent = block, None
    for _ in range(_ARTICLE_MAX_DEPTH):
        value = getattr(node, "text", None)
        if isinstance(value, str):
            return node, "text", value, parent
        if value is None:
            return None
        parts = _article_items(getattr(value, "texts", None))
        if parts:
            return None
        parent, node = node, value
    return None


def article_holder_supports_entities(holder) -> bool:
    """40.1.0: у узла текста есть поле entities (как у TL_textWithEntities): в него можно положить Premium Emoji и Markdown."""
    try:
        return hasattr(holder, "entities")
    except Exception:
        return False


_IV_PACKAGE = "org.telegram.tgnet.tl.TL_iv$"
_ARTICLE_EMOJI = {"state": None, "warned": False}
_ARTICLE_EMOJI_IMAGE_SIZE = 20


def _iv_new(name: str):
    """Новый экземпляр узла TL_iv$<name> (textPlain, textConcat, textImage...)."""
    full = _IV_PACKAGE + name
    try:
        from java import jclass
        return jclass(full)()
    except Exception as exc:
        raise RuntimeError(f"{full} unavailable: {exc}") from None


def _article_emoji_kinds() -> list:
    """Имена узлов TL_iv, которыми статья может нести Premium Emoji: сначала «эмодзи», затем textImage."""
    names: list = []
    try:
        from java import jclass
        for cls in jclass("org.telegram.tgnet.tl.TL_iv").getClass().getDeclaredClasses():
            short = str(cls.getName()).split("$")[-1]
            if "emoji" in short.lower() and short not in names:
                names.append(short)
    except Exception:
        pass
    for short in ("textCustomEmoji", "textEmoji", "textImage"):
        if short not in names:
            names.append(short)
    return names


def article_emoji_kind() -> Optional[str]:
    """Имя подходящего узла (есть поле document_id) или None. Результат запоминается."""
    state = _ARTICLE_EMOJI
    if state["state"] is not None:
        return state["state"] or None
    for short in _article_emoji_kinds():
        try:
            probe = _iv_new(short)
            probe.document_id = 1
            if int(probe.document_id) == 1:
                state["state"] = short
                return short
        except Exception:
            continue
    state["state"] = ""
    return None


def article_emoji_node(kind: str, document_id: int, fallback: str):
    node = _iv_new(kind)
    node.document_id = int(document_id)
    if kind.lower().endswith("image"):
        node.w = _ARTICLE_EMOJI_IMAGE_SIZE
        node.h = _ARTICLE_EMOJI_IMAGE_SIZE
    elif fallback:
        try:
            node.text = fallback
        except Exception:
            pass
    return node


def article_plain_node(text: str):
    node = _iv_new("textPlain")
    node.text = text
    return node


def article_concat_node(children: list):
    from java.util import ArrayList
    node = _iv_new("textConcat")
    texts = ArrayList()
    for child in children:
        texts.add(child)
        try:
            child.parentRichText = node
        except Exception:
            pass
    node.texts = texts
    return node


_FRAME_NOISE_RE = re.compile("[\u200b-\u200d\u2060\ufeff\u00ad\ufe0e\ufe0f]")


def frame_key(text) -> str:
    """46.6.0: вид текста для сравнения префикса/суффикса. Без невидимых символов и служебных меток разметки,
    в NFC, а пробелы и переводы строк схлопнуты в один пробел: редактор статей мог обрезать или поменять пробелы."""
    cleaned = _FRAME_NOISE_RE.sub("", _MD_SENTINEL_RE.sub("", as_text(text)))
    return " ".join(unicodedata.normalize("NFC", cleaned).split())


def frame_has_head(key: str, head: str) -> bool:
    """Блок начинается с префикса маски. Граница слова учитывается: префикс «A» не найдётся в слове «Apple»."""
    if not head or not key.startswith(head):
        return False
    if len(key) == len(head):
        return True
    return not (head[-1].isalnum() and key[len(head)].isalnum())


def frame_has_tail(key: str, tail: str) -> bool:
    """Блок заканчивается суффиксом маски (с той же границей слова)."""
    if not tail or not key.endswith(tail):
        return False
    if len(key) == len(tail):
        return True
    return not (tail[0].isalnum() and key[-len(tail) - 1].isalnum())


def article_frame_plan(texts, left: str, right: str) -> List[bool]:
    """46.6.0: какие текстовые блоки статьи уже оформлены маской и трогать их не нужно (True = оставить как есть).
    left/right — то, что маска ставит над [text] и под [text]. texts — тексты блоков по порядку (None — блок, который
    не разобрать). Готовым считается блок, если:
      1) он сам и есть префикс или суффикс (блок-обрамление над или под текстом);
      2) внутри него стоит префикс в начале или суффикс в конце: хотя бы одна из сторон, остальное не дописывается;
      3) прямо над ним блок-префикс или прямо под ним блок-суффикс.
    Найденное считается целостным: ничего не дополняется, даже если маска задаёт обе стороны, а найдена одна."""
    count = len(texts)
    keep = [False] * count
    head, tail = frame_key(left), frame_key(right)
    if not head and not tail:
        return keep
    keys = [frame_key(text) if isinstance(text, str) else None for text in texts]
    roles: List[Optional[str]] = [None] * count
    opened = False
    for index, key in enumerate(keys):
        if key is None:
            continue
        is_head, is_tail = bool(head) and key == head, bool(tail) and key == tail
        if is_head and is_tail:
            is_head, is_tail = (False, True) if opened else (True, False)
        if is_head:
            roles[index], opened = "H", True
        elif is_tail:
            roles[index], opened = "T", False
    for index, key in enumerate(keys):
        if key is None:
            continue
        if roles[index] is not None or frame_has_head(key, head) or frame_has_tail(key, tail):
            keep[index] = True
    for index, role in enumerate(roles):
        if role == "T" and index > 0 and keys[index - 1] is not None:
            keep[index - 1] = True
        elif role == "H":
            closing = next((k for k in range(index + 1, count) if roles[k] == "T"), None)
            reopening = next((k for k in range(index + 1, count) if roles[k] == "H"), count)
            end = closing if closing is not None and closing < reopening else index + 2
            for k in range(index + 1, min(end, count)):
                if keys[k] is not None:
                    keep[k] = True
    return keep


_FALLBACK_NOISE = frozenset("\ufe0e\ufe0f\u200b\u200c\u2060\ufeff")


def _fallback_skippable(char: str) -> bool:
    return char.isspace() or char in _FALLBACK_NOISE


def mask_side_units(side: str, table) -> List[Tuple[str, int]]:
    """46.7.0: сторона скомпилированной маски как список кусков [(видимый текст, document_id)].
    document_id == 0 — обычный текст, иначе запасной эмодзи Premium Emoji."""
    units: List[Tuple[str, int]] = []
    plain: List[str] = []
    emoji: List[str] = []
    document = 0
    limit = _MD_BASE + 2 * len(table)
    for char in side:
        code = ord(char)
        if _MD_BASE <= code < limit:
            entity_id, closing = divmod(code - _MD_BASE, 2)
            if table[entity_id][0] != "CustomEmoji":
                continue
            if not closing:
                if plain:
                    units.append(("".join(plain), 0))
                    plain = []
                try:
                    document = int(table[entity_id][1])
                except (TypeError, ValueError):
                    document = 0
                emoji = []
            else:
                if document and emoji:
                    units.append(("".join(emoji), document))
                document, emoji = 0, []
            continue
        if _MD_SENTINEL_RE.match(char):
            continue
        (emoji if document else plain).append(char)
    if plain:
        units.append(("".join(plain), 0))
    return units


def fallback_side_spans(side: str, table, text: str, from_end: bool = False) -> Optional[List[Tuple[int, int, int]]]:
    """46.7.0: распознаёт сторону маски, которая лежит в тексте запасными эмодзи (Premium Emoji потерялись:
    правка, повторная отправка, пересланный или вставленный текст). Возвращает [(начало, конец, document_id)]
    по индексам строки text или None, если сторона не найдена целиком.
    Сравнение терпимо к пробелам и переводам строк (их может не быть или быть больше), к селекторам вариантов
    эмодзи (U+FE0E/FE0F) и невидимым символам. from_end=True — сторона должна стоять в конце текста."""
    units = mask_side_units(side, table)
    if not any(document for _, document in units):
        return None
    count = len(text)
    step = -1 if from_end else 1
    pos = count if from_end else 0
    if from_end:
        units = units[::-1]

    def at() -> str:
        index = pos - 1 if from_end else pos
        return text[index] if 0 <= index < count else ""

    while at() and _fallback_skippable(at()):
        pos += step
    spans: List[Tuple[int, int, int]] = []
    for chunk, document in units:
        chars = chunk[::-1] if from_end else chunk
        entry = pos
        for char in chars:
            if char in _FALLBACK_NOISE:
                continue
            if char.isspace():
                while at() and _fallback_skippable(at()):
                    pos += step
                continue
            while at() and at() in _FALLBACK_NOISE:
                pos += step
            if at() != char:
                return None
            pos += step
        if document:
            if not from_end:
                while at() and at() in _FALLBACK_NOISE:
                    pos += step
            spans.append((pos, entry, document) if from_end else (entry, pos, document))
    if from_end:
        spans.reverse()
    return spans


def fallback_emoji_entities(text: str, spans) -> List[Tuple[str, int, int, str]]:
    return [("CustomEmoji", utf16_length(text[:start]), utf16_length(text[start:end]), str(document)) for start, end, document in spans]


class DismissGuard:
    """50.2.0: замечает, что диалог закрыт не его кнопкой, а «назад» или касанием за окном.

    Кнопки диалога вызывают mark() до dismiss(); если окно закрылось, а mark() не звали, вызывается on_unanswered.
    Срабатывает не больше одного раза. Слушатель закрытия ставится через builder до show(), поэтому событие приходит
    при любом закрытии, а флаг отличает ответ пользователя от отмены.
    """

    def __init__(self, on_unanswered=None):
        self.on_unanswered = on_unanswered
        self.answered = False
        self.fired = False

    def mark(self):
        self.answered = True

    def _dismissed(self, log):
        if self.answered or self.fired:
            return
        self.fired = True
        if self.on_unanswered is None:
            return
        try:
            self.on_unanswered()
        except Exception as exc:
            log(f"Prefixfy: dialog dismissal handler failed: {exc}")

    def attach(self, builder, log) -> bool:
        """Ставит слушатель закрытия на builder. 52.0.0: вызывается ДО show() - AlertDialog.Builder передаёт
        слушатель диалогу при create(), а SDK сам оборачивает Python-функцию в OnDismissListener."""
        try:
            builder.set_on_dismiss_listener(lambda _bld: run_on_ui_thread(lambda: self._dismissed(log)))
            return True
        except Exception as exc:
            log(f"Prefixfy: dismiss listener unavailable: {exc}")
            return False


def _show_info_unbound(text: str, log):
    """Плашка в главном потоке без привязки к жизненному циклу плагина (для сообщений после самовыключения)."""
    try:
        from java import dynamic_proxy
        from java.lang import Runnable as JavaRunnable
        from org.telegram.messenger import AndroidUtilities, R as TelegramR

        class _Show(dynamic_proxy(JavaRunnable)):
            def run(self):
                try:
                    factory, _ = BulletinHelper._get_factory_and_provider(None)
                    factory.createSimpleBulletin(TelegramR.raw.info, text).show()
                except Exception as exc:
                    log(f"Prefixfy notice failed: {exc}")

        AndroidUtilities.runOnUIThread(_Show())
    except Exception as exc:
        log(f"Prefixfy notice failed: {exc}")


class DebugRecorder:
    """Журнал отладки: строки self.log() с отметкой времени, в файл в закрытой папке плагина.
    Запись переживает перезапуск плагина (OTA), размер ограничен DEBUG_MAX_BYTES."""

    def __init__(self, directory: str):
        self.directory = directory
        self.path = os.path.join(directory, DEBUG_LOG_NAME)
        self._lock = threading.Lock()
        self.active = False
        self._full = False

    def exists(self) -> bool:
        return os.path.isfile(self.path) and os.path.getsize(self.path) > 0

    def stats(self) -> Tuple[int, int]:
        try:
            size = os.path.getsize(self.path)
        except OSError:
            return 0, 0
        lines = 0
        try:
            with open(self.path, "rb") as handle:
                for chunk in iter(lambda: handle.read(65536), b""):
                    lines += chunk.count(b"\n")
        except OSError:
            pass
        return lines, size

    def start(self, header: str, resume: bool):
        with self._lock:
            os.makedirs(self.directory, exist_ok=True)
            mode = "a" if resume and os.path.isfile(self.path) else "w"
            with open(self.path, mode, encoding="utf-8") as handle:
                handle.write(header.rstrip("\n") + "\n")
            self._full = os.path.getsize(self.path) >= DEBUG_MAX_BYTES
            self.active = True

    def stop(self, note: str = ""):
        with self._lock:
            if self.active and note:
                self._append(note)
            self.active = False

    def write(self, message):
        if not self.active:
            return
        stamp = time.strftime("%H:%M:%S") + f".{int(time.time() * 1000) % 1000:03d}"
        text = as_text(message).replace("\r\n", "\n").replace("\n", "\n    ")
        with self._lock:
            if self.active:
                self._append(f"{stamp} [{threading.current_thread().name}] {text}")

    def _append(self, line: str):
        if self._full:
            return
        try:
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
                if handle.tell() >= DEBUG_MAX_BYTES:
                    handle.write("--- log size limit reached, further lines are dropped ---\n")
                    self._full = True
        except OSError:
            pass

    def delete(self):
        with self._lock:
            self.active = False
            self._full = False
            discard_file(self.path)

    def export_copy(self, directory: str) -> str:
        os.makedirs(directory, exist_ok=True)
        target = os.path.join(directory, time.strftime("Prefixfy_debug_%Y%m%d_%H%M%S.txt"))
        with self._lock:
            shutil.copyfile(self.path, target)
        return target


class _EntityCarrier:
    """Заменитель SendMessageParams для сборки сущностей подписи к прикреплённому медиа."""
    __slots__ = ("entities",)

    def __init__(self):
        self.entities = None


class PrefixfyPlugin(BasePlugin):
    @staticmethod
    def _debug_allowed() -> bool:
        return FEATURES.enabled("debug")

    def log(self, message: str):
        super().log(message)
        recorder = self.__dict__.get("_debug")
        if recorder is not None and recorder.active and self._debug_allowed():
            recorder.write(message)

    def _trace_sink(self, event: str, fields: Dict[str, Any]):
        recorder = self.__dict__.get("_debug")
        if recorder is None or not recorder.active or not self._debug_allowed():
            return
        parts = []
        for name, value in fields.items():
            if value is None:
                continue
            text = as_text(value) if not isinstance(value, (bool, int, float)) else repr(value)
            text = text.replace("\n", "\\n")
            if len(text) > 80:
                text = text[:77] + "…"
            parts.append(f"{name}={text}")
        recorder.write(f"ACTION {event}" + (" " + " ".join(parts) if parts else ""))

    def _debug_header(self, resumed: bool) -> str:
        lines = ["=== Prefixfy debug log " + ("(resumed after restart) " if resumed else "") + time.strftime("%Y-%m-%d %H:%M:%S %z") + " ==="]
        lines.append(f"plugin: {__version__} ({__build__})")
        try:
            import _sdk_version
            lines.append(f"sdk: {_sdk_version.__version__}{' beta' if getattr(_sdk_version, '__beta__', False) else ''}")
        except Exception:
            pass
        try:
            from org.telegram.messenger import BuildVars
            lines.append(f"app: {BuildVars.BUILD_VERSION_STRING} ({BuildVars.BUILD_VERSION})")
        except Exception:
            pass
        try:
            from android.os import Build
            lines.append(f"device: {Build.MANUFACTURER} {Build.MODEL}, Android {Build.VERSION.RELEASE} (API {Build.VERSION.SDK_INT})")
        except Exception:
            pass
        try:
            lines.append(f"language: {self.localization.language()}; vault: {'on' if VAULT.usable else 'off'}")
        except Exception:
            pass
        return "\n".join(lines)

    def _debug_init(self):
        try:
            self._debug = DebugRecorder(os.path.join(get_plugins_dir(), DEBUG_DIR_NAME))
            self._debug_taps = 0
            self._debug_tap_at = 0.0
            self._debug_tap_serial = 0
            global _TRACE_SINK
            _TRACE_SINK = self._trace_sink
            if self.get_setting(DEBUG_ENABLED_KEY, False) and self.get_setting(DEBUG_RECORDING_KEY, False):
                self._debug.start(self._debug_header(True), resume=True)
        except Exception as exc:
            self._debug = None
            super().log(f"Prefixfy debug init failed: {exc}")

    def on_plugin_load(self):
        self._debug_init()
        try:
            self._on_plugin_load_impl()
        except Exception:
            try:
                data = _ota_read()
                if data.get("state") == "pending" and data.get("to") == __build__ and _ota_rollback("load failed", self.log):
                    threading.Thread(target=_host_restart_plugin, args=(self.log,), daemon=True).start()
            except Exception:
                pass
            raise
        if self._dormant or self._wipe_halt:
            return
        try:
            self.remote.ota_loaded()
        except Exception as exc:
            self.log(f"Prefixfy OTA confirm failed: {exc}")
        self._updated_arm()
        if self._wiped_clean or self._auto_reset_done:
            notice = "wipe_auto_reset_done" if self._auto_reset_done else "wipe_done"
            self._wiped_clean = False
            self._auto_reset_done = False
            try:
                run_on_queue(lambda: self._toast(notice), PLUGINS_QUEUE, 2500)
            except Exception as exc:
                self.log(f"Prefixfy wipe notice failed: {exc}")

    _dormant = False
    _wiped_clean = False
    _wipe_running = False
    _wipe_halt = False

    def _enter_wipe_halt(self):
        """Между первым и вторым перезапуском плагин ничего не делает, кроме стирания, которое уже выполнено:
        ни настроек, ни хуков, ни удалённого модуля, ни OTA. Единственное действие - второй перезапуск."""
        self._wipe_halt = True
        self._prefixfy_hooks = []
        self.settings = PrefixfySettings(self)
        self.localization = LocalizationManager(self)
        self.log("Prefixfy: data wiped, the plugin does nothing until the second restart")
        threading.Thread(target=self._wipe_second_restart, name="PrefixfyWipeRestart", daemon=True).start()

    def _wipe_second_restart(self):
        """Второй перезапуск после очистки. Метка остаётся: если перезапуск не удался и плагин включат вручную,
        он загрузится чистым и покажет сообщение."""
        try:
            time.sleep(1.0)
            if _host_restart_plugin(self.log):
                return
            self._toast("wipe_restart_manual")
        except Exception as exc:
            self.log(f"Prefixfy second restart failed: {exc}")

    def _settings_wipe_halt(self) -> List[Any]:
        return [Text(text=self._tr("wipe_halt"), subtext=self._tr("wipe_halt_subtext"),
                     icon=self._icon("msg_retry", "msg_info"), on_click=lambda *_: None)]

    def _startup_gate(self) -> bool:
        """Отложенное удаление данных и режим отказа. True — плагин спит и остальное не загружается."""
        self._dormant = False
        self._wipe_halt = False
        self._wiped_clean = False
        marker = read_wipe_marker()
        if marker is not None:
            clear_wipe_marker()
            need = parse_version(marker["need"]) if marker["need"] else ()
            if need and parse_version(__build__) < need:
                self.log(f"Prefixfy: the update to {marker['need']} did not happen, data deletion cancelled")
            else:
                clear_dormant_marker()
                if marker["bl"]:
                    try:
                        wipe_blacklist_data(self)
                    except Exception as exc:
                        self.log(f"Prefixfy blacklist data deletion failed: {exc}")
                    return False
                try:
                    wipe_plugin_data(self, marker["opt_out"])
                except Exception as exc:
                    self.log(f"Prefixfy data deletion failed: {exc}")
                if marker["opt_out"]:
                    if not write_dormant_marker():
                        self.log("Prefixfy: could not store the opt-out marker, it holds until the next start only")
                    self._enter_dormant()
                    return True
                if write_wipe_final_marker():
                    self._enter_wipe_halt()
                    return True
                self._wiped_clean = True
                return False
        elif take_wipe_final_marker():
            self._wiped_clean = True
        if dormant_active():
            self._enter_dormant()
            return True
        self._auto_reset_check()
        return False

    _auto_reset_done = False

    def _auto_reset_check(self):
        """40.0.0: повреждённые данные или служебные файлы -> автоматический полный сброс."""
        try:
            problems, key_bad = integrity_scan(self)
            if not problems:
                return
            self.log(f"Prefixfy: damaged data found: {', '.join(problems[:12])}")
            if not key_bad and all(item == "settings" or item.startswith("setting:") for item in problems):
                if "settings" in problems:
                    values = dict(SETTING_DEFAULTS)
                else:
                    values = {item.split(":", 1)[1]: SETTING_DEFAULTS[item.split(":", 1)[1]]
                              for item in problems if item.split(":", 1)[1] in SETTING_DEFAULTS}
                bulk_set_settings(self, values)
                self.log(f"Prefixfy: {len(values)} damaged setting(s) reset to defaults, configurations kept")
                return
            if _auto_reset_recent():
                self.log("Prefixfy: automatic reset already ran recently, skipped")
                return
            auto_reset_plugin(self, problems, key_bad)
            self._auto_reset_done = True
            self.log("Prefixfy: automatic full reset done")
        except Exception as exc:
            self.log(f"Prefixfy automatic reset failed: {exc}")

    def _seal_legacy_media(self):
        try:
            count = seal_legacy_media(self.log)
            if count:
                self.log(f"Prefixfy: {count} media file(s) encrypted")
        except Exception as exc:
            self.log(f"Prefixfy media encryption failed: {exc}")

    def _request_blacklist_wipe(self):
        """Аккаунт устройства в ЧС: кладём метку и перезапускаем плагин, стирание выполнится в начале запуска."""
        if self._dormant or self._wipe_halt or self._wipe_running or blacklist_guard_exists():
            return
        self._wipe_running = True

        def work():
            try:
                if not write_wipe_marker(False, "", bl=True):
                    self.log("Prefixfy: cannot store the blacklist wipe marker")
                    return
                self.log("Prefixfy: an account on this device is blacklisted, data is removed on restart")
                if not _host_restart_plugin(self.log):
                    self.log("Prefixfy: plugin restart is unavailable, data is removed at the next start")
            except Exception as exc:
                self.log(f"Prefixfy blacklist wipe request failed: {exc}")
            finally:
                self._wipe_running = False

        threading.Thread(target=work, name="PrefixfyBlacklistWipe", daemon=True).start()

    def _enter_dormant(self):
        self._dormant = True
        self._prefixfy_hooks = []
        self.settings = PrefixfySettings(self)
        self.localization = LocalizationManager(self)
        self.log("Prefixfy is dormant: the plugin does nothing until it is resumed in its settings")

    def _on_plugin_load_impl(self):
        if self._startup_gate():
            return
        self._legacy = LegacyMigration(self)
        self._setup_init()
        _slot_housekeeping(self.log)
        self._legacy.migrate_files()
        VAULT.attach(self.log)
        VAULT.prepare()
        self.settings = PrefixfySettings(self)
        self.localization = LocalizationManager(self)
        self.runtime_manager = RuntimeManager(self)
        self.transfer = ConfigTransfer(self)
        self.remote = RemoteControl(self)
        self._weather = WeatherCache(self.log)
        try:
            run_on_queue(self._seal_legacy_media, PLUGINS_QUEUE, 1500)
        except Exception as exc:
            self.log(f"Prefixfy media encryption scheduling failed: {exc}")
        self._internal_sends: Dict[Tuple[Any, str], float] = {}
        self._internal_lock = threading.Lock()
        self._dialog_kinds: Dict[int, str] = {}
        self._chat_titles: Dict[Tuple[int, int], Tuple[float, str]] = {}
        self._skip_once = None
        self._chat_toggle_menu_id = None
        self._capture_menu_id = None
        self._chat_config_menu_id = None
        self._bindings_cache = None
        self._schedule_cache = None
        self._prefixfy_hooks = []
        self._edit_seen: Dict[int, float] = {}

        self._reset_transient_settings()
        self._remove_stale_files()
        self._legacy.migrate_settings()
        self.configurations = ConfigurationsManager(self)
        try:
            self.configurations.sync_target()
        except Exception as exc:
            self.log(f"Prefixfy account target sync failed: {exc}")
        try:
            self._seal_vault()
        except Exception as exc:
            self.log(f"Prefixfy vault sealing failed: {exc}")
        self._legacy.finish()
        self.runtime_manager.rebuild()

        self.transfer.register_file_handler()
        self.add_on_send_message_hook()
        for label, step in (
            ("chat menu", self.refresh_chat_menu_item),
            ("activity result hook", self._install_activity_result_hook),
            ("edit message hook", self._install_edit_message_hook),
        ):
            try:
                step()
            except Exception as exc:
                self.log(f"Prefixfy {label} failed: {exc}")
        self.remote.start()
        self.remote.blacklist_guard()
        self.log(f"Prefixfy {__build__} loaded ({self.localization.language()})")

    def on_plugin_unload(self):
        recorder = self.__dict__.get("_debug")
        if recorder is not None and recorder.active and self._debug_allowed():
            recorder.write("--- plugin unloaded ---")
        global _TRACE_SINK
        if _TRACE_SINK == self._trace_sink:
            _TRACE_SINK = None
        try:
            self._flush_counters()
        except Exception as exc:
            self.log(f"Prefixfy final counter save failed: {exc}")
        remote = getattr(self, "remote", None)
        if remote is not None:
            remote.stop()
        weather = getattr(self, "_weather", None)
        if weather is not None:
            weather.close()
        configurations = getattr(self, "configurations", None)
        if configurations is not None:
            try:
                configurations.shutdown()
            except Exception as exc:
                self.log(f"Prefixfy final save failed: {exc}")
        transfer = getattr(self, "transfer", None)
        if transfer is not None:
            transfer.unregister_file_handler()
        for hook in getattr(self, "_prefixfy_hooks", []):
            try:
                self.unhook_method(hook)
            except Exception:
                pass
        self._prefixfy_hooks = []
        self._skip_once = None
        self._bindings_cache = None
        self._schedule_cache = None
        for cache_name in ("_dialog_kinds", "_chat_titles"):
            cache = getattr(self, cache_name, None)
            if cache is not None:
                cache.clear()
        self._remove_chat_menu_item()
        lock = getattr(self, "_internal_lock", None)
        if lock is not None:
            with lock:
                self._internal_sends.clear()
                self._edit_seen = {}

    def _reset_transient_settings(self):
        changed = {key: default for key, default in TRANSIENT_SETTING_DEFAULTS.items()
                   if self.get_setting(key, default) != default}
        bulk_set_settings(self, changed)

    def _seal_vault(self):
        """Один раз запечатывает всё, что осталось открытым текстом, и только после этого включает строгий режим."""
        if not VAULT.usable or VAULT.strict:
            return
        complete = self.configurations.seal_files()
        state_files = ("Prefixfy_remote.json", BLACKLIST_CACHE_FILE, FLAGS_CACHE_FILE, SERIALS_FILE,
                       KNOWN_BUILDS_FILE, AUTO_STATE_FILE)
        for name in state_files:
            complete = seal_plain_file(os.path.join(get_plugins_dir(), name), self.log) and complete
        if complete:
            VAULT.finish_migration()

    def _remove_stale_files(self):
        cache_dir = get_cache_dir()
        for name in ("Prefixfy_tmp", "Prefixfy_imports", "Prefixfy_exports", "Prefixfy"):
            shutil.rmtree(os.path.join(cache_dir, name), ignore_errors=True)

    @staticmethod
    def _hookable_class(name: str):
        """52.0.0: java.lang.Class по имени через hook_utils.java_class (загрузчик приложения, вложенные классы
        через $). Раньше здесь перебирались find_class, .class_ и Class.forName по очереди."""
        return java_class(name)

    def _install_activity_result_hook(self):
        def after(param):
            self.transfer.handle_activity_result(param.args[0], param.args[1], param.args[2])

        launch_class = self._hookable_class("org.telegram.ui.LaunchActivity")
        if launch_class is None:
            self.log("LaunchActivity not found: file pickers are unavailable")
            return
        hooks = self.hook_all_methods(launch_class, "onActivityResult", after=after)
        if not hooks:
            self.log("LaunchActivity hook failed, file pickers are unavailable")
            return
        self._prefixfy_hooks.extend(hooks)

    def _install_edit_message_hook(self):
        edit_class = self._hookable_class("org.telegram.tgnet.TLRPC$TL_messages_editMessage")
        if edit_class is None:
            self.log("Prefixfy edit: TL_messages_editMessage not found, message editing is unavailable")
            return

        def before(param):
            request = param.args[0] if len(param.args) else None
            if request is not None and edit_class.isInstance(request):
                tracing = _TRACE_SINK is not None and self._debug_tracing()
                if tracing:
                    started = time.perf_counter()
                    before_text = as_text(getattr(request, "message", ""))
                self._on_edit_request(param, request)
                if tracing:
                    after_text = as_text(getattr(request, "message", ""))
                    trace_action("edit", changed=after_text != before_text, before=utf16_length(before_text),
                                 after=utf16_length(after_text), ms=round((time.perf_counter() - started) * 1000, 1))

        manager_class = self._hookable_class("org.telegram.tgnet.ConnectionsManager")
        if manager_class is None:
            self.log("Prefixfy edit: ConnectionsManager not found, message editing is unavailable")
            return
        hooks = self.hook_all_methods(
            manager_class, "sendRequest", before=before,
            before_filters=[HookFilter.ArgumentIsInstanceOf(0, edit_class)],
        )
        if not hooks:
            self.log("Prefixfy edit: Java-side hook filter unavailable, falling back to the Python check")
            hooks = self.hook_all_methods(manager_class, "sendRequest", before=before)
        if not hooks:
            self.log("Prefixfy edit: hooking sendRequest failed, message editing is unavailable")
            return
        self._prefixfy_hooks.extend(hooks)

    def handle_setting_changed(self, key):
        if key in TRANSIENT_SETTING_DEFAULTS or key in OTA_SETTING_DEFAULTS:
            return
        self.runtime_manager.on_setting_changed()
        configurations = getattr(self, "configurations", None)
        if configurations is not None and key in ConfigurationsManager.CONFIG_KEYS:
            configurations.schedule_autosave()

    def _tr(self, key, **kwargs):
        return self.localization.tr(key, **kwargs)

    def _toast(self, key, fragment=None, **kwargs):
        trace_action("toast", key=key)
        text = self._tr(key, **kwargs)
        stop = self.stop_event
        if stop is not None and stop.is_set():
            _show_info_unbound(text, self.log)
            return

        def show():
            try:
                BulletinHelper.show_info(text, fragment or get_last_fragment())
            except Exception as exc:
                self.log(f"Prefixfy notice failed: {exc}")

        run_on_ui_thread(show)

    def reload_settings_ui(self, delay_ms: int = 0):
        if delay_ms <= 0:
            self._reload_settings_now()
            return
        if getattr(self, "_reload_pending", False):
            return
        self._reload_pending = True
        ref = weakref.ref(self)

        def task():
            plugin = ref()
            if plugin is None:
                return
            plugin._reload_pending = False
            plugin._reload_settings_now()

        try:
            run_on_queue(task, PLUGINS_QUEUE, int(delay_ms))
        except Exception as exc:
            self._reload_pending = False
            self.log(f"Settings reload scheduling failed: {exc}")
            self._reload_settings_now()

    def _reload_settings_now(self):
        try:
            self.set_setting("language", self.settings.language_index(), reload_settings=True)
        except Exception as exc:
            self.log(f"Settings reload failed: {exc}")

    def _dialog_activity(self, fragment=None):
        for candidate in (fragment, get_last_fragment()):
            try:
                activity = candidate.getParentActivity() if candidate else None
            except Exception:
                activity = None
            if activity:
                return activity
        return None

    def _show_builder(self, builder, guard: Optional[DismissGuard] = None, *, red=(), cancelable: Optional[bool] = None) -> bool:
        if _TRACE_SINK is not None:
            caller = sys._getframe(1).f_code.co_name
            if caller in ("show_text_dialog", "show_checklist", "show_password_dialog"):
                caller = f"{caller}<-{sys._getframe(2).f_code.co_name}"
            trace_action("dialog", by=caller)
        """52.0.0: всё, что AlertDialogBuilder применяет при создании (красные кнопки, слушатель закрытия), ставится
        до show(); то, что SDK меняет только у готового диалога (cancelable), - после."""
        try:
            for kind in red:
                builder.make_button_red(self._BUTTON_CODES[kind])
            if guard is not None and not guard.attach(builder, self.log):
                self.log("Prefixfy: closing by back/outside tap cannot be detected for this dialog")
            builder.show()
            if builder.get_dialog() is None:
                return False
            if cancelable is not None:
                builder.set_cancelable(bool(cancelable))
                builder.set_canceled_on_touch_outside(bool(cancelable))
            return True
        except Exception as exc:
            self.log(f"Prefixfy dialog show failed: {exc}")
            return False

    def show_text_dialog(self, title, on_confirm, *, message=None, text="", hint="", multiline=False,
                         positive=None, fragment=None, on_cancel=None, neutral=None) -> bool:
        activity = self._dialog_activity(fragment)
        if not activity:
            return False
        editor = AndroidEditText(activity)
        if hint:
            editor.setHint(hint)
        if text:
            editor.setText(text)
        if multiline:
            editor.setSingleLine(False)
            editor.setGravity(0x30)
            editor.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE)
            editor.setMinLines(5)
            editor.setMaxLines(12)
        else:
            editor.setSingleLine(True)
            editor.setInputType(InputType.TYPE_CLASS_TEXT)

        builder = AlertDialogBuilder(activity)
        builder.set_title(title)
        guard = DismissGuard(on_cancel)
        if neutral:
            def reset(bld, which):
                if neutral[1](editor) is not False:
                    guard.mark()
                    bld.dismiss()
            builder.set_neutral_button(neutral[0], reset)
        if message:
            builder.set_message(message)
        builder.set_view(editor)

        def ok(bld, which):
            value = editor.getText().toString()
            if has_unsafe_text(value):
                editor.setError(self._tr("unsafe_text_rejected"))
                self._toast("unsafe_text_rejected", fragment)
                return
            if on_confirm(value, editor) is not False:
                guard.mark()
                bld.dismiss()

        def cancel(bld, which):
            guard.mark()
            bld.dismiss()
            if on_cancel:
                on_cancel()

        builder.set_positive_button(positive or self._tr("action_save"), ok)
        builder.set_negative_button(self._tr("action_cancel"), cancel)
        return self._show_builder(builder, guard if on_cancel else None)

    def show_password_dialog(self, title, message, on_password, *, confirm: bool, positive=None, fragment=None,
                             on_cancel=None) -> bool:
        """53.0.0: ввод пароля (скрытый текст). confirm=True - второе поле «Повторите пароль»."""
        activity = self._dialog_activity(fragment)
        if not activity:
            return False
        layout = LinearLayout(activity)
        layout.setOrientation(LinearLayout.VERTICAL)
        hidden = InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD
        fields = []
        for hint in (("password_hint", "password_repeat_hint") if confirm else ("password_hint",)):
            field = AndroidEditText(activity)
            field.setSingleLine(True)
            field.setInputType(hidden)
            field.setHint(self._tr(hint))
            layout.addView(field)
            fields.append(field)
        builder = AlertDialogBuilder(activity)
        builder.set_title(title)
        if message:
            builder.set_message(message)
        builder.set_view(layout)
        guard = DismissGuard(on_cancel)

        def ok(bld, which):
            password = fields[0].getText().toString()
            if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
                fields[0].setError(self._tr("password_length", min=PASSWORD_MIN_LENGTH, max=PASSWORD_MAX_LENGTH))
                return
            if confirm and fields[1].getText().toString() != password:
                fields[1].setError(self._tr("password_mismatch"))
                return
            guard.mark()
            bld.dismiss()
            on_password(password)

        def cancel(bld, which):
            guard.mark()
            bld.dismiss()
            if on_cancel:
                on_cancel()

        builder.set_positive_button(positive or self._tr("action_apply"), ok)
        builder.set_negative_button(self._tr("action_cancel"), cancel)
        return self._show_builder(builder, guard if on_cancel else None)

    def show_checklist(self, title, rows, on_confirm, *, message=None, extra=None, positive=None,
                       fragment=None, on_cancel=None, cooldown: int = 0, red: bool = False) -> bool:
        activity = self._dialog_activity(fragment)
        if not activity:
            return False
        layout = LinearLayout(activity)
        layout.setOrientation(LinearLayout.VERTICAL)
        boxes = []
        for label, checked, enabled in rows:
            box = CheckBox(activity)
            box.setText(label)
            box.setChecked(bool(checked))
            box.setEnabled(bool(enabled))
            layout.addView(box)
            boxes.append(box)
        extra_box = None
        if extra is not None:
            extra_box = CheckBox(activity)
            extra_box.setText(extra[0])
            extra_enabled = bool(extra[2]) if len(extra) > 2 else True
            extra_box.setChecked(bool(extra[1]) and extra_enabled)
            extra_box.setEnabled(extra_enabled)
            layout.addView(extra_box)

        builder = AlertDialogBuilder(activity)
        builder.set_title(title)
        if message:
            builder.set_message(message)
        builder.set_view(layout)

        label = positive or self._tr("action_save")
        shown_at = time.monotonic()
        guard = DismissGuard(on_cancel)

        def ok(bld, which):
            if cooldown and cooldown - (time.monotonic() - shown_at) > 0:
                return
            selected = [i for i, box in enumerate(boxes) if box.isChecked() and rows[i][2]]
            extra_checked = bool(extra_box and extra_box.isEnabled() and extra_box.isChecked())
            if on_confirm(selected, extra_checked) is not False:
                guard.mark()
                bld.dismiss()

        def cancel(bld, which):
            guard.mark()
            bld.dismiss()
            if on_cancel:
                on_cancel()

        builder.set_positive_button(f"{label} ({cooldown})" if cooldown else label, ok)
        builder.set_negative_button(self._tr("action_cancel"), cancel)
        shown = self._show_builder(builder, guard if on_cancel else None, red=("positive",) if red else ())
        if shown and cooldown:
            self._run_wipe_countdown(builder, label, shown_at)
        return shown

    def _current_dialog_id(self) -> Optional[int]:
        try:
            fragment = get_last_fragment()
            if fragment is None:
                return None
            method = getattr(fragment, "getDialogId", None)
            if callable(method):
                found = to_dialog_id(method())
                if found is not None:
                    return found
            for attr in ("dialog_id", "dialogId"):
                found = to_dialog_id(getattr(fragment, attr, None))
                if found is not None:
                    return found
        except Exception as exc:
            self.log(f"_current_dialog_id failed: {exc}")
        return None

    def _dialog_id_from_params(self, params, account=None) -> Optional[int]:
        peer = getattr(params, "peer", None)
        dialog_id = to_dialog_id(peer)
        if dialog_id is not None:
            return dialog_id
        if peer is not None and self._class_name(peer).endswith("InputPeerSelf"):
            try:
                own = get_user_config(None if account is None else int(account)).getClientUserId()
                found = java_int(own)
                if found:
                    return found
            except Exception as exc:
                self.log(f"Prefixfy self peer lookup failed: {exc}")
        return self._current_dialog_id()

    def _menu_dialog_id(self, context) -> Optional[int]:
        if isinstance(context, dict):
            for key in ("dialog_id", "dialogId"):
                found = to_dialog_id(context.get(key))
                if found is not None:
                    return found
        return self._current_dialog_id()

    _CHAT_MENU_ATTRS = ("_chat_toggle_menu_id", "_capture_menu_id", "_chat_config_menu_id",
                        "_skip_message_menu_id")

    def _update_blocked(self, context=None) -> bool:
        remote = getattr(self, "remote", None)
        if remote is None or remote.allows():
            return False
        fragment = context.get("fragment") if isinstance(context, dict) else None
        key, kwargs = remote.notice()
        self._toast(key, fragment, **kwargs)
        return True

    def _chat_menu_entries(self):
        return (
            ("_chat_toggle_menu_id", "exceptions_chat_menu", self._toggle_chat_from_menu, True),
            ("_capture_menu_id", "capture_custom_emoji", self._enable_capture_from_menu, FEATURES.on("premium_emoji")),
            ("_chat_config_menu_id", "chat_config_menu", self._show_chat_config_picker, FEATURES.on("chat_configs")),
            ("_skip_message_menu_id", "skip_once_menu", self._skip_one_message, True),
        )

    def refresh_chat_menu_item(self):
        entries = self._chat_menu_entries()
        signature = (self.localization.language(), tuple(enabled for *_, enabled in entries))
        if getattr(self, "_menu_language", None) == signature and all(getattr(self, attr, None) for attr, _k, _h, enabled in entries if enabled):
            return
        self._remove_chat_menu_item()
        for priority, (attr, key, handler, enabled) in enumerate(entries, start=10):
            if not enabled:
                continue
            setattr(self, attr, self.add_menu_item(MenuItemData(
                menu_type=MenuItemType.CHAT_ACTION_MENU, text=self._tr(key), on_click=_traced("menu", key, handler), priority=priority,
            )))
        self._menu_language = signature

    def _remove_chat_menu_item(self):
        self._menu_language = None
        for attr in self._CHAT_MENU_ATTRS:
            menu_id = getattr(self, attr, None)
            setattr(self, attr, None)
            if menu_id:
                try:
                    self.remove_menu_item(menu_id)
                except Exception:
                    pass

    def _enable_capture_from_menu(self, context):
        if self._update_blocked(context):
            return
        fragment = context.get("fragment") if isinstance(context, dict) else None
        try:
            enable = not bool(self.settings.get("capture_custom_emoji", False))
            self.settings.set("capture_custom_emoji", enable)
        except Exception as exc:
            self.log(f"Prefixfy capture toggle failed: {exc}")
            return
        BulletinHelper.show_info(self._tr("capture_custom_emoji_enabled" if enable else "capture_custom_emoji_disabled"), fragment)

    def _chat_bindings(self) -> Dict[str, str]:
        raw = as_text(self.get_setting(CHAT_CONFIGS_KEY, "{}"))
        cached = self._bindings_cache
        if cached is None or cached[0] != raw:
            cached = self._bindings_cache = (raw, parse_chat_configs(raw))
        return cached[1]

    def _schedule_rules(self):
        raw = as_text(self.get_setting(SCHEDULE_KEY, ""))
        cached = self._schedule_cache
        if cached is None or cached[0] != raw:
            try:
                parsed = parse_schedule(raw)[0]
            except Exception as exc:
                self.log(f"Prefixfy schedule parse failed: {exc}")
                parsed = []
            cached = self._schedule_cache = (raw, parsed)
        return cached[1]

    def prune_chat_bindings(self):
        configs = getattr(self, "configurations", None)
        bindings = self._chat_bindings()
        if configs is None or not bindings:
            return
        alive = {}
        for chat, cid in bindings.items():
            uid_text, sep, _rest = chat.partition(":")
            if self._binding_allowed(int(uid_text) if sep else None, cid):
                alive[chat] = cid
        if len(alive) != len(bindings):
            self.set_setting(CHAT_CONFIGS_KEY, dump_chat_configs(alive))

    def rename_in_schedule(self, old_name: str, new_name: str):
        text, changed = rename_schedule_target(as_text(self.get_setting(SCHEDULE_KEY, "")), old_name, new_name)
        if changed:
            self.set_setting(SCHEDULE_KEY, text)

    def export_schedule_section(self, config_id: Optional[str] = None) -> dict:
        configs = self.configurations
        chats = {}
        for dialog, config_id in self._chat_bindings().items():
            if ":" in dialog:
                continue
            record = configs.configurations.get(config_id)
            if record:
                chats[dialog] = as_text(record.get("name"))
        active = (configs._record(config_id) if config_id else None) or configs.configurations.get(configs.active_id) or {}
        return {"source": as_text(active.get("name")), "chats": chats, "rules": as_text(self.get_setting(SCHEDULE_KEY, ""))}

    def reset_schedule_section(self):
        """Сброс привязок чатов и расписания; привязки, заданные для отдельных аккаунтов, остаются."""
        kept = {chat: cid for chat, cid in self._chat_bindings().items() if ":" in chat}
        self.set_setting(CHAT_CONFIGS_KEY, dump_chat_configs(kept))
        self.set_setting(SCHEDULE_KEY, "")

    def import_schedule_section(self, section: dict, new_name: Optional[str] = None):
        configs = self.configurations
        if not isinstance(section, dict):
            return
        source = as_text(section.get("source")).strip()
        mapping = dict(self._chat_bindings())
        chats = section.get("chats")
        for dialog, name in (list(chats.items())[:MAX_IMPORTED_CHAT_BINDINGS] if isinstance(chats, dict) else ()):
            if not _CHAT_BIND_KEY_RE.fullmatch(str(dialog)) or ":" in str(dialog):
                continue
            name = as_text(name).strip()
            target = new_name if new_name and source and name.casefold() == source.casefold() else name
            config_id = configs.find_id_by_name(target)
            if config_id:
                mapping[str(dialog)] = config_id
        self.set_setting(CHAT_CONFIGS_KEY, dump_chat_configs(mapping))
        rules = as_text(section.get("rules", ""))
        if new_name and source:
            rules = rename_schedule_target(rules, source, new_name)[0]
        self.set_setting(SCHEDULE_KEY, clean_schedule_text(rules))

    _acc_cache = (0.0, {})

    def _accounts(self) -> Dict[int, int]:
        stamp, data = self._acc_cache
        now = time.monotonic()
        if stamp == 0.0 or now - stamp > DEVICE_RECHECK_INTERVAL:
            try:
                found = device_account_map(self.log)
            except Exception as exc:
                self.log(f"Prefixfy account map failed: {exc}")
                found = None
            if found is not None:
                data = found
            self._acc_cache = (now, data)
        return data

    def _acct_available(self) -> bool:
        return FEATURES.on("account_settings") and len(self._accounts()) >= 2

    def _acct_on(self) -> bool:
        return self._acct_available() and bool(self.get_setting(ACCT_MODE_KEY, False))

    @staticmethod
    def _current_account_slot() -> Optional[int]:
        try:
            return int(get_selected_account())
        except Exception:
            return None

    def _acct_name(self, slot) -> str:
        if slot is None:
            return ""
        try:
            user = get_user_config(int(slot)).getCurrentUser()
            full = f"{as_text(getattr(user, 'first_name', None))} {as_text(getattr(user, 'last_name', None))}".strip()
            return full or as_text(getattr(user, "username", None))
        except Exception:
            return ""

    def _acct_label(self, slot, uid, mark: bool = False) -> str:
        name = self._acct_name(slot)
        text = f"{name} • ID {uid}" if name else f"ID {uid}"
        configs = getattr(self, "configurations", None)
        if mark and configs is not None and configs.accounts.has(uid):
            text += " ✱"
        return text

    def _base_runtime(self, account) -> Optional["Runtime"]:
        """Базовый рантайм для аккаунта: свой набор, иначе общий. Без режима — как в 32.x."""
        live = self.runtime_manager.runtime
        configs = getattr(self, "configurations", None)
        if configs is None or live is None:
            return live
        on = self._acct_on()
        if configs.edit_uid is None and not on:
            return live
        if on:
            try:
                uid = self._accounts().get(int(account))
            except Exception:
                uid = None
            if uid is not None:
                if uid == configs.edit_uid:
                    return live
                own = configs.accounts.runtime_for(uid)
                if own is not None:
                    return own
        if configs.edit_uid is None:
            return live
        return configs.runtime_for(configs.active_id) or live

    @staticmethod
    def _section_body(items: List[Any]) -> List[Any]:
        """Содержимое раздела без его собственного заголовка: для объединения нескольких разделов под одним."""
        return items[1:] if items and isinstance(items[0], Header) else items

    def _settings_general(self) -> List[Any]:
        return [
            Header(text=self._tr("section_general")),
            self._switch("chat_scope_enabled", self._tr("plugin_enable"), self._tr("plugin_enable_subtext"), "msg_settings"),
        ] + self._section_body(self._settings_accounts())

    def _settings_appearance(self) -> List[Any]:
        items: List[Any] = [Header(text=self._tr("section_appearance"))]
        for part in (
            self._settings_mask, self._settings_separator, self._settings_style,
            self._settings_cute, self._settings_media,
        ):
            body = self._section_body(part())
            if not body:
                continue
            items += body
        return items

    def _settings_accounts(self) -> List[Any]:
        if not self._acct_available():
            return []
        tr = self._tr
        icon = self._icon("msg_contacts", "msg_info")
        items: List[Any] = [
            Header(text=tr("section_accounts")),
            Switch(key=ACCT_MODE_KEY, text=tr("account_mode"), default=False, subtext=tr("account_mode_subtext"),
                   icon=icon, on_change=self._on_acct_mode),
        ]
        if not bool(self.get_setting(ACCT_MODE_KEY, False)):
            return items
        configs = self.configurations
        accounts = self._accounts()
        uids = list(accounts.values())
        target = as_text(self.get_setting(ACCT_TARGET_KEY, ACCT_AUTO)).strip()
        if target == ACCT_AUTO:
            index = 0
        elif _ACCOUNT_ID_RE.fullmatch(target) and int(target) in uids:
            index = 2 + uids.index(int(target))
        else:
            index = 1
        names = [tr("account_auto"), tr("account_common")] + [self._acct_label(s, u, mark=True) for s, u in accounts.items()]
        key = configs.acct_selector_key
        try:
            self.set_setting(key, index)
        except Exception as exc:
            self.log(f"Prefixfy account selector state failed: {exc}")
        items.append(Selector(key=key, text=tr("account_target"), default=index, items=names, icon=icon,
                              on_change=self._on_acct_target))
        shown = configs.edit_uid
        if shown is None:
            configs._acct_reset_visible = None
        elif configs.account_reset_available(shown):
            items.append(Text(text=tr("account_reset"), subtext=tr("account_reset_subtext"), icon=self._icon("msg_retry"),
                              on_click=self._confirm_reset_account))
        return items

    def _acct_apply(self):
        try:
            self.configurations.sync_target()
        except Exception as exc:
            self.log(f"Prefixfy account target sync failed: {exc}")
        self.configurations._refresh_ui()

    def _on_acct_mode(self, enabled):
        self.set_setting(ACCT_MODE_KEY, bool(enabled))
        self._acct_apply()

    def _on_acct_target(self, index):
        uids = list(self._accounts().values())
        if index == 0:
            value = ACCT_AUTO
        elif index == 1:
            value = ACCT_COMMON
        elif isinstance(index, int) and 2 <= index < 2 + len(uids):
            value = str(uids[index - 2])
        else:
            return
        self.set_setting(ACCT_TARGET_KEY, value)
        self._acct_apply()

    def _confirm_reset_account(self, view=None):
        activity = self._dialog_activity()
        if not activity:
            return
        builder = AlertDialogBuilder(activity)
        builder.set_title(self._tr("account_reset_title"))
        builder.set_message(self._tr("account_reset_confirm"))

        def confirmed(bld, which):
            bld.dismiss()
            self.configurations.reset_account()

        builder.set_positive_button(self._tr("account_reset_button"), confirmed)
        builder.set_negative_button(self._tr("action_cancel"), lambda bld, which: bld.dismiss())
        self._show_builder(builder)

    def _chat_account_uid(self, account) -> Optional[int]:
        """uid аккаунта, чьи пресеты управляют чатами, — только при включённом режиме «Настройки по аккаунтам»."""
        if account is None or not self._acct_on():
            return None
        try:
            return self._accounts().get(int(account))
        except Exception:
            return None

    @staticmethod
    def _chat_binding_key(uid: Optional[int], dialog_id) -> str:
        return str(dialog_id) if uid is None else f"{uid}:{dialog_id}"

    def _binding_allowed(self, uid: Optional[int], config_id) -> bool:
        """Можно ли чату этого аккаунта указывать на такую конфигурацию. Аккаунт со своими пресетами берёт только их."""
        configs = getattr(self, "configurations", None)
        if configs is None or not isinstance(config_id, str):
            return False
        owner = configs._owner_of(config_id)
        if owner is None:
            if config_id not in configs.configurations:
                return False
            return uid is None or not configs.accounts.has(uid)
        return uid is not None and owner == uid and config_id in configs.accounts.bucket(uid)

    def _bound_config_id(self, uid: Optional[int], dialog_id) -> Optional[str]:
        config_id = self._chat_bindings().get(self._chat_binding_key(uid, dialog_id))
        return config_id if config_id is not None and self._binding_allowed(uid, config_id) else None

    def _runtime_for_chat(self, runtime, dialog_id, account=None):
        configs = getattr(self, "configurations", None)
        if configs is None:
            return runtime
        uid = self._chat_account_uid(account)
        config_id = self._bound_config_id(uid, dialog_id) if dialog_id is not None and FEATURES.on("chat_configs") else None
        if config_id is None:
            rules = self._schedule_rules() if FEATURES.on("schedule") else None
            if rules:
                config_id = schedule_match(rules, datetime.now(), configs.find_id_by_name, lambda: self._schedule_chat_info(account, dialog_id))
        if config_id is None or config_id == runtime.config_id:
            return runtime
        owner = configs._owner_of(config_id)
        if owner is None:
            return configs.runtime_for(config_id) or runtime
        return configs.accounts.runtime_for_preset(owner, config_id) or runtime

    def _schedule_chat_info(self, account, dialog_id):
        """Для условий расписания: (вид чата, id чата, id аккаунта). Неизвестное остаётся None."""
        kind = chat_id = uid = None
        try:
            if _is_int(dialog_id):
                chat_id = int(dialog_id)
                kind = self._dialog_kind(account, chat_id) if account is not None or chat_id > 0 else None
            if account is not None:
                uid = self._accounts().get(int(account))
        except Exception as exc:
            self.log(f"Prefixfy schedule chat info failed: {exc}")
        return kind, chat_id, uid

    def _show_chat_config_picker(self, context):
        if self._update_blocked(context):
            return
        dialog_id = self._menu_dialog_id(context)
        if dialog_id is None:
            self.log(f"Cannot pick chat configuration: no dialog_id in context {context}")
            return
        fragment = context.get("fragment") if isinstance(context, dict) else None
        activity = self._dialog_activity(fragment)
        configs = getattr(self, "configurations", None)
        if not activity or configs is None:
            return
        uid = self._chat_account_uid(self._current_account_slot())
        records = configs.accounts.bucket(uid) if uid is not None and configs.accounts.has(uid) else configs.configurations
        key = self._chat_binding_key(uid, dialog_id)
        ids = list(records)
        bound = self._bound_config_id(uid, dialog_id)
        items = [("✓ " if bound not in ids else "") + self._tr("chat_config_auto")]
        items += [("✓ " if config_id == bound else "") + as_text(records[config_id].get("name", config_id)) for config_id in ids]
        builder = AlertDialogBuilder(activity)
        builder.set_title(self._tr("chat_config_menu"))

        def selected(bld, which):
            bld.dismiss()
            mapping = dict(self._chat_bindings())
            if which == 0:
                mapping.pop(key, None)
            elif 0 < which <= len(ids):
                mapping[key] = ids[which - 1]
            else:
                return
            self.set_setting(CHAT_CONFIGS_KEY, dump_chat_configs(mapping))
            self._toast("chat_config_reset" if which == 0 else "chat_config_saved", fragment)

        builder.set_items(items, selected)
        builder.set_negative_button(self._tr("action_cancel"), lambda bld, which: bld.dismiss())
        self._show_builder(builder)

    def _show_schedule_editor(self, view=None):
        configs = self.configurations

        def save(value, editor):
            rules, errors = parse_schedule(value)
            problem = None
            if errors:
                number, code, detail = errors[0]
                problem = (number, self._tr(code, n=MAX_SCHEDULE_RULES, x=detail))
            else:
                for rule in rules:
                    if configs.find_id_by_name(rule.name) is None:
                        problem = (rule.line, self._tr("schedule_err_config", name=rule.name))
                        break
            if problem:
                editor.setError(self._tr("schedule_error", n=problem[0], reason=problem[1]))
                return False
            self.set_setting(SCHEDULE_KEY, "\n".join(line.strip() for line in as_text(value).splitlines() if line.strip()))
            self._toast("schedule_saved")
            self.reload_settings_ui()

        self.show_text_dialog(
            self._tr("schedule"), save, message=self._tr("schedule_message"),
            text=as_text(self.get_setting(SCHEDULE_KEY, "")), hint=self._tr("schedule_hint"), multiline=True,
        )

    def _schedule_subtext(self) -> str:
        count = len(self._schedule_rules())
        return self._tr("schedule_count", n=count) if count else self._tr("schedule_empty")

    def _skip_one_message(self, context):
        if self._update_blocked(context):
            return
        dialog_id = self._menu_dialog_id(context)
        if dialog_id is None:
            return
        fragment = context.get("fragment") if isinstance(context, dict) else None
        with self._skip_lock:
            pending = self._skip_once
            disarm = pending is not None and pending[0] == dialog_id and pending[1] > time.monotonic()
            if disarm:
                self._skip_once = None
            else:
                armed = (dialog_id, time.monotonic() + SKIP_ONCE_TTL)
                self._skip_once = armed
        if disarm:
            self._toast("skip_once_off", fragment)
        else:
            self._schedule_skip_expiry(armed)
            self._toast("skip_once_on", fragment)

    def _schedule_skip_expiry(self, armed):
        ref = weakref.ref(self)

        def task():
            plugin = ref()
            if plugin is None:
                return
            with plugin._skip_lock:
                if plugin._skip_once is not armed:
                    return
                plugin._skip_once = None
            try:
                plugin._toast("skip_once_expired")
            except Exception as exc:
                plugin.log(f"Prefixfy skip expiry notice failed: {exc}")

        try:
            run_on_queue(task, PLUGINS_QUEUE, int(SKIP_ONCE_TTL * 1000) + 250)
        except Exception as exc:
            self.log(f"Prefixfy skip expiry scheduling failed: {exc}")

    def _consume_skip_once(self, dialog_id) -> bool:
        with self._skip_lock:
            pending = self._skip_once
            if pending is None:
                return False
            if pending[1] <= time.monotonic():
                self._skip_once = None
                return False
            if pending[0] != dialog_id:
                return False
            self._skip_once = None
            return True

    def _toggle_chat_from_menu(self, context):
        if self._update_blocked(context):
            return
        dialog_id = self._menu_dialog_id(context)
        if dialog_id is None:
            self.log(f"Cannot toggle chat: no dialog_id in context {context}")
            return
        fragment = context.get("fragment") if isinstance(context, dict) else None
        ids = self.settings.disabled_chat_ids()
        if dialog_id in ids:
            ids.discard(dialog_id)
            message = "exceptions_chat_removed"
        else:
            ids.add(dialog_id)
            message = "exceptions_chat_added"
        self.settings.set_disabled_chat_ids(ids)
        try:
            account = self._current_account_slot()
            base = self._base_runtime(account)
            live = self.runtime_manager.runtime
            if base is not None and live is not None:
                governing = self._runtime_for_chat(base, dialog_id, account)
                allowed = (governing.settings.is_chat_allowed(dialog_id)
                           and self._chat_type_allowed(account, dialog_id, governing.settings.chat_type_rules))
                if governing.config_id != live.config_id:
                    message = "exceptions_chat_other_config"
                else:
                    message = "exceptions_chat_now_on" if allowed else "exceptions_chat_now_off"
        except Exception as exc:
            self.log(f"Prefixfy chat toggle state check failed: {exc}")
        BulletinHelper.show_info(self._tr(message), fragment)

    MARKDOWN_PICK_KEY = "Prefixfy_markdown_style_pick"
    STYLE_PICK_KEY = "Prefixfy_text_style_pick"
    LANGUAGE_RELOAD_DELAY_MS = 280

    def _bool_handler(self, key, reload_settings=False):
        return lambda enabled: self.settings.set(key, bool(enabled), reload_settings=reload_settings)

    def _schedule_menu_refresh(self, delay_ms: int):
        if getattr(self, "_menu_refresh_pending", False):
            return
        self._menu_refresh_pending = True
        ref = weakref.ref(self)

        def task():
            plugin = ref()
            if plugin is None:
                return
            plugin._menu_refresh_pending = False
            try:
                plugin.refresh_chat_menu_item()
            except Exception as exc:
                plugin.log(f"Prefixfy menu refresh failed: {exc}")

        try:
            run_on_queue(task, PLUGINS_QUEUE, int(delay_ms))
        except Exception as exc:
            self._menu_refresh_pending = False
            self.log(f"Menu refresh scheduling failed: {exc}")
            self.refresh_chat_menu_item()

    def _apply_language_index(self, index: int):
        if index == self.settings.language_index():
            return
        before = self.localization.language()
        self.set_setting("language", index)
        configurations = getattr(self, "configurations", None)
        if configurations is not None:
            configurations.schedule_autosave()
        self.localization.refresh()
        if self.localization.language() != before:
            self._schedule_menu_refresh(self.LANGUAGE_RELOAD_DELAY_MS + 250)
        self.reload_settings_ui(delay_ms=self.LANGUAGE_RELOAD_DELAY_MS)

    def _on_language_auto_change(self, enabled):
        current_index = self.settings.language_index()
        if bool(enabled) == (current_index == 0):
            return
        if enabled and not language_auto_enabled():
            return
        if enabled:
            index = 0
        else:
            current = self.localization.language()
            index = LANGUAGE_MODES.index(current) if current in LANGUAGE_MODES else LANGUAGE_MODES.index("ru")
        self._apply_language_index(index)

    def _on_language_select_change(self, new_index):
        if self.settings.language_index() == 0 and language_auto_enabled():
            return
        enabled = enabled_language_indices()
        if not (_is_int(new_index) and 0 <= new_index < len(enabled)):
            return
        self._apply_language_index(enabled[new_index])

    def _on_separator_count_change(self, new_value):
        value = clamp_int(new_value, 1, 1, MAX_SEPARATOR_COUNT)
        if self.settings.separator_count() != value or self.settings.get("emoji_count") != value:
            self.settings.set("emoji_count", value)

    def _on_media_enabled_change(self, enabled):
        enabled = bool(enabled)
        if enabled and not self.transfer.media_exists():
            self._toast("media_file_none")
            enabled = False
        self.settings.set("attached_media_enabled", enabled, reload_settings=True)

    def _delete_imported_media(self, view=None):
        """46.2.0: удаление импортированного медиа только после подтверждения."""
        activity = self._dialog_activity()
        if not activity:
            return
        name = as_text(self.settings.get("attached_media_name")) or os.path.basename(self.transfer.media_path())
        builder = AlertDialogBuilder(activity)
        builder.set_title(self._tr("media_delete"))
        builder.set_message(self._tr("media_delete_confirm", name=name))

        def confirmed(bld, which):
            bld.dismiss()
            self._do_delete_imported_media()

        builder.set_positive_button(self._tr("action_delete"), confirmed)
        builder.set_negative_button(self._tr("action_cancel"), lambda bld, which: bld.dismiss())
        self._show_builder(builder)

    def _do_delete_imported_media(self):
        try:
            self.transfer.delete_media()
            self._toast("media_deleted")
        except Exception as exc:
            self.log(f"Media deletion failed: {exc}")
            self._toast("media_delete_failed")

    def _show_mask_editor(self, view=None):
        def save(value, editor):
            if len(value) > MAX_MASK_LENGTH:
                editor.setError(self._tr("mask_too_long", n=MAX_MASK_LENGTH))
                return False
            if value and not is_valid_mask(value):
                editor.setError(self._tr("mask_invalid"))
                self._toast("mask_invalid")
                return False
            self.settings.set("mask", value, reload_settings=True)

        self.show_text_dialog(
            self._tr("mask_editor_title"), save,
            message=self._with_emoji_hint(self._tags_hint()),
            text=as_text(self.settings.get("mask")) or MASK_PLACEHOLDER,
            hint=self._tr("mask_editor_hint"), multiline=True,
        )

    def _tags_hint(self) -> str:
        return filter_tags_hint(self._tr("mask_tags_hint"))

    def _with_emoji_hint(self, text: str, first: bool = False) -> str:
        if not FEATURES.on("premium_emoji"):
            return text
        hint = self._tr("capture_custom_emoji_hint")
        return f"{text}\n\n{hint}" if first else f"{hint}\n\n{text}"

    def _show_separator_editor(self, view=None):
        def save(value, editor):
            separators = [item.strip() for item in value.split(",") if item.strip()]
            self.settings.set("custom_emojis", ", ".join(separators) if separators else DEFAULT_SEPARATORS, reload_settings=True)

        current = as_text(self.settings.get("custom_emojis"))
        self.show_text_dialog(
            self._tr("separator_custom_title"), save,
            message=self._with_emoji_hint(self._tr('separator_custom_message'), first=True),
            text=current if current.strip() else DEFAULT_SEPARATORS, hint=DEFAULT_SEPARATORS,
        )

    def _show_masks_list_editor(self, view=None):
        def save(value, editor):
            lines = parse_lines(value)
            if len(lines) > MAX_MASKS_IN_LIST:
                editor.setError(self._tr("masks_list_limit", n=MAX_MASKS_IN_LIST))
                return False
            if any(not is_valid_mask(line) for line in lines):
                editor.setError(self._tr("masks_list_invalid"))
                return False
            self.settings.set("masks_list", "\n".join(lines), reload_settings=True)

        self.show_text_dialog(
            self._tr("masks_list"), save,
            message=f"{self._tr('masks_list_hint')}\n\n{self._tags_hint()}".rstrip(),
            text="\n".join(parse_lines(self.settings.get("masks_list"))), multiline=True,
        )

    def _masks_list_subtext(self) -> str:
        count = len(RuntimeSettings(self.settings.raw()).masks_list)
        return self._tr("masks_list_count", n=count) if count else self._tr("masks_list_empty")

    def _on_rotation_mode_change(self, index):
        self.settings.set("mask_rotation_mode", clamp_int(index, 0, 0, 1), reload_settings=True)

    def _show_conditional_masks_editor(self, view=None):
        def save(value, editor):
            errors = parse_conditional_masks(value)[1]
            if errors:
                number, code = errors[0]
                if code == "limit":
                    editor.setError(self._tr("regex_exceptions_limit", n=MAX_CONDITIONAL_MASKS, m=MAX_REGEX_LENGTH))
                elif code == "format":
                    editor.setError(self._tr("conditional_masks_format", n=number))
                else:
                    reason = self._tr("masks_list_invalid") if code == "mask" else self._tr("regex_exceptions_invalid", error=code[len("regex:"):])
                    editor.setError(self._tr("schedule_error", n=number, reason=reason))
                return False
            cleaned = "\n".join(line.strip() for line in as_text(value).splitlines() if line.strip())
            self.settings.set("conditional_masks", cleaned, reload_settings=True)

        self.show_text_dialog(
            self._tr("conditional_masks"), save,
            message=f"{self._tr('conditional_masks_hint')}\n\n{self._tags_hint()}".rstrip(),
            text=as_text(self.settings.get("conditional_masks")), hint="(?i)hello => 👋 [text]", multiline=True,
        )

    def _conditional_masks_subtext(self) -> str:
        count = len(parse_conditional_masks(self.settings.get("conditional_masks"))[0])
        return self._tr("conditional_masks_count", n=count) if count else self._tr("conditional_masks_empty")

    def _show_regex_exceptions_editor(self, view=None):
        def save(value, editor):
            lines = parse_lines(value)
            if len(lines) > MAX_REGEX_EXCEPTIONS or any(len(line) > MAX_REGEX_LENGTH for line in lines):
                editor.setError(self._tr("regex_exceptions_limit", n=MAX_REGEX_EXCEPTIONS, m=MAX_REGEX_LENGTH))
                return False
            for line in lines:
                try:
                    re.compile(line)
                except re.error as exc:
                    editor.setError(self._tr("regex_exceptions_invalid", error=str(exc)))
                    return False
                if not regex_is_safe(line):
                    editor.setError(self._tr("regex_exceptions_invalid", error=REGEX_UNSAFE_REASON))
                    return False
            self.settings.set("regex_exceptions", "\n".join(lines), reload_settings=True)

        self.show_text_dialog(
            self._tr("regex_exceptions"), save, message=self._tr("regex_exceptions_hint"),
            text="\n".join(parse_lines(self.settings.get("regex_exceptions"))), multiline=True,
        )

    def _regex_subtext(self) -> str:
        count = len(parse_lines(self.settings.get("regex_exceptions")))
        return self._tr("regex_exceptions_count", n=count) if count else self._tr("regex_exceptions_empty")

    def _show_chat_types_editor(self, view=None):
        current = parse_chat_type_rules(self.settings.get("chat_type_rules"))
        rows = [(self._tr(f"chat_type_{kind}"), kind in current, True) for kind in CHAT_KINDS]

        def save(selected, extra):
            if not selected:
                self._toast("chat_types_none")
                return False
            self.settings.set("chat_type_rules", dump_chat_type_rules(CHAT_KINDS[index] for index in selected), reload_settings=True)

        self.show_checklist(self._tr("chat_types"), rows, save, message=self._tr("chat_types_hint"))

    def _chat_types_subtext(self) -> str:
        kinds = parse_chat_type_rules(self.settings.get("chat_type_rules"))
        if len(kinds) == len(CHAT_KINDS):
            return self._tr("chat_types_all")
        return ", ".join(self._tr(f"chat_type_{kind}") for kind in CHAT_KINDS if kind in kinds)

    def _on_markdown_style_change(self, index):
        values = getattr(self, "_markdown_pick_values", None) or list(MARKDOWN_STYLE_VALUES)
        if _is_int(index) and 0 <= index < len(values):
            self.settings.set("markdown_style", values[index], reload_settings=True)

    def _on_text_style_change(self, index):
        values = getattr(self, "_style_pick_values", None) or list(range(TEXT_STYLE_COUNT))
        if _is_int(index) and 0 <= index < len(values):
            self.settings.set("text_style", values[index], reload_settings=True)

    def _show_style_words_editor(self, view=None):
        def save(value, editor):
            words = list(parse_lines(value))
            if len(words) > MAX_STYLE_WORDS:
                editor.setError(self._tr("style_words_limit", n=MAX_STYLE_WORDS))
                return False
            self.settings.set("style_words", "\n".join(words), reload_settings=True)

        self.show_text_dialog(
            self._tr("style_words"), save, message=self._tr("style_words_hint"),
            text="\n".join(parse_lines(self.settings.get("style_words"))), multiline=True,
        )

    def _style_words_subtext(self) -> str:
        count = len(parse_lines(self.settings.get("style_words")))
        return self._tr("style_words_count", n=count) if count else self._tr("style_words_empty")

    def _show_tag_lines_editor(self, view=None):
        def save(value, editor):
            lines = list(parse_lines(value))
            if len(lines) > MAX_TAG_LINES:
                editor.setError(self._tr("tag_lines_limit", n=MAX_TAG_LINES))
                return False
            self.settings.set("tag_lines", "\n".join(lines), reload_settings=True)

        self.show_text_dialog(
            self._tr("tag_lines"), save, message=self._tr("tag_lines_hint"),
            text="\n".join(parse_lines(self.settings.get("tag_lines"))), multiline=True,
        )

    def _tag_lines_subtext(self) -> str:
        count = len(parse_lines(self.settings.get("tag_lines")))
        return self._tr("tag_lines_count", n=count) if count else self._tr("tag_lines_empty")

    def _show_exceptions_editor(self, view=None):
        def save(value, editor):
            self.settings.set("exceptions", "\n".join(parse_lines(value)), reload_settings=True)

        self.show_text_dialog(
            self._tr("exceptions"), save,
            message=self._tr("exceptions_hint"),
            text="\n".join(parse_lines(self.settings.get("exceptions"))), multiline=True,
        )

    def _mask_preview_text(self) -> str:
        mask = self._expand_mask_tags(self.settings.get("mask"), None, None, preview=True)
        if not mask:
            return ""
        markdown = self.settings.markdown_enabled()
        sample = self._tr("mask_preview_sample")
        if self.settings.get("text_style_enabled"):
            preview_settings = RuntimeSettings(self.settings.raw())
            sample = apply_text_style(
                sample, clamp_int(self.settings.get("text_style"), 0, 0, TEXT_STYLE_COUNT - 1),
                preview_settings.text_style_translit, preview_settings.style_only,
            )
        parts = split_mask(mask)
        if parts is None:
            return self._tr("mask_preview_invalid")
        left, right = parts
        compiled = compile_mask_markdown(mask, parse_markdown=markdown)
        if compiled is not None:
            left, right = (_MD_SENTINEL_RE.sub("", side) for side in compiled[:2])
        return f"{left}{sample}{right}"

    def _separator_preview_text(self) -> str:
        separators = parse_separators(self.settings.get("custom_emojis"))
        count = self.settings.separator_count()
        words = self._tr("separator_preview_sample").split()
        if len(words) < 2:
            words = ["Hello", "world"]
        snapshot = self.settings.snapshot()
        spaces, mode = snapshot.separator_spaces, snapshot.separator_space_mode
        out, index = words[0], 0
        for word in words[1:]:
            chosen = []
            for _ in range(count):
                chosen.append(separators[index % len(separators)])
                index += 1
            joined = (" " if spaces else "").join(chosen)
            if not spaces:
                out += joined + word
            elif mode == 1:
                out += " " + joined + word
            elif mode == 2:
                out += joined + " " + word
            else:
                out += " " + joined + " " + word
        return out

    def _exceptions_subtext(self) -> str:
        values = len(parse_lines(self.settings.get("exceptions")))
        chats = len(self.settings.disabled_chat_ids())
        if values == 0 and chats == 0:
            return self._tr("exceptions_hint")
        return self._tr("exceptions_count", n=values, m=chats)

    IGNORE_SEGMENT_KEYS = IGNORE_KEYS + ("ignore_emoji_only",)

    def _show_ignore_segments_editor(self, view=None):
        keys = self.IGNORE_SEGMENT_KEYS
        rows = [(self._tr(key), bool(self.settings.get(key)), True) for key in keys]

        def save(selected, extra):
            chosen = set(selected)
            last = len(keys) - 1
            for index, key in enumerate(keys):
                self.settings.set(key, index in chosen, reload_settings=(index == last))

        self.show_checklist(self._tr("ignore_segments"), rows, save, message=self._tr("ignore_segments_hint"))

    def _ignore_segments_subtext(self) -> str:
        keys = self.IGNORE_SEGMENT_KEYS
        enabled = sum(1 for key in keys if bool(self.settings.get(key)))
        return self._tr("ignore_segments_count", n=enabled, total=len(keys))

    _ICON_KNOWN: Dict[str, bool] = {}

    @staticmethod
    def _icon(name: str, fallback: str = "msg_settings") -> str:
        known = PrefixfyPlugin._ICON_KNOWN
        if name in known:
            return name if known[name] else fallback
        try:
            holder = find_class("org.telegram.messenger.R$drawable")
        except Exception:
            holder = None
        if holder is None:
            return fallback
        found = None
        for probe in (getattr(holder, "class_", None), holder):
            getter = getattr(probe, "getField", None) if probe is not None else None
            if getter is None:
                continue
            try:
                getter(name)
                found = True
            except Exception:
                found = False
            break
        if found is None:
            try:
                found = hasattr(holder, name)
            except Exception:
                found = False
        known[name] = bool(found)
        return name if found else fallback

    def _switch(self, key: str, text: str, subtext: str, icon: str, reload_settings: bool = False):
        return Switch(
            key=key, text=text, default=PrefixfySettings.DEFAULTS[key], subtext=subtext, icon=icon,
            on_change=self._bool_handler(key, reload_settings),
        )

    def _settings_configurations(self) -> List[Any]:
        tr, transfer = self._tr, self.transfer
        items: List[Any] = []
        self.configurations.append_settings(items)
        short = tr("config_actions_subtext")
        if FEATURES.on("config_import"):
            items.append(Text(text=tr("config_import"), subtext=short, icon="msg_download", on_click=transfer.request_import))
        items += [
            Text(text=tr("config_export"), subtext=short, icon="msg_share", on_click=transfer.request_export),
            Text(text=tr("config_reset"), subtext=short, icon=self._icon("msg_retry"), on_click=transfer.request_reset),
        ]
        if FEATURES.on("schedule"):
            items.append(Text(text=tr("schedule"), subtext=self._schedule_subtext(), icon=self._icon("msg_calendar", "msg_recent"), on_click=self._show_schedule_editor))
        return items

    def _scope_target_keys(self) -> Tuple[str, ...]:
        keys = ["process_message", "process_media"]
        if FEATURES.on("articles"):
            keys.append("process_article")
        return tuple(keys)

    _SCOPE_TARGET_LABELS = {"process_message": "scope_message", "process_media": "scope_media", "process_article": "scope_article"}

    def _show_scope_targets_editor(self, view=None):
        keys = self._scope_target_keys()
        rows = [(self._tr(self._SCOPE_TARGET_LABELS[key]), bool(self.settings.get(key)), True) for key in keys]

        def save(selected, extra):
            chosen = set(selected)
            last = len(keys) - 1
            for index, key in enumerate(keys):
                self.settings.set(key, index in chosen, reload_settings=(index == last))

        self.show_checklist(self._tr("scope_targets"), rows, save, message=self._tr("scope_targets_hint"))

    def _scope_targets_subtext(self) -> str:
        keys = self._scope_target_keys()
        enabled = sum(1 for key in keys if bool(self.settings.get(key)))
        return self._tr("ignore_segments_count", n=enabled, total=len(keys))

    def _scope_edit_keys(self) -> Tuple[str, ...]:
        keys = ["process_edit_message", "process_edit_media"]
        if FEATURES.on("articles"):
            keys.append("process_edit_article")
        keys.append("skip_once_on_edit")
        return tuple(keys)

    _SCOPE_EDIT_LABELS = {"process_edit_message": "scope_edit_message", "process_edit_media": "scope_edit_media", "process_edit_article": "scope_edit_article", "skip_once_on_edit": "skip_once_on_edit"}

    def _show_scope_edit_editor(self, view=None):
        keys = self._scope_edit_keys()
        rows = [(self._tr(self._SCOPE_EDIT_LABELS[key]), bool(self.settings.get(key)), True) for key in keys]

        def save(selected, extra):
            chosen = set(selected)
            last = len(keys) - 1
            for index, key in enumerate(keys):
                self.settings.set(key, index in chosen, reload_settings=(index == last))

        self.show_checklist(self._tr("scope_edit_targets"), rows, save, message=self._tr("scope_edit_targets_hint"))

    def _scope_edit_subtext(self) -> str:
        keys = self._scope_edit_keys()
        enabled = sum(1 for key in keys if bool(self.settings.get(key)))
        return self._tr("ignore_segments_count", n=enabled, total=len(keys))

    def _settings_scope(self) -> List[Any]:
        tr = self._tr
        items: List[Any] = [
            Header(text=tr("section_scope")),
            Text(text=tr("scope_targets"), subtext=self._scope_targets_subtext(), icon=self._icon("msg_text", "msg_info"), on_click=self._show_scope_targets_editor),
        ]
        articles_on = FEATURES.on("articles")
        edit_on = FEATURES.on("edit_processing")
        if edit_on:
            items.append(self._switch("process_edit", tr("scope_edit"), tr("scope_edit_subtext"), "msg_edit", True))
        if edit_on and self.settings.get("process_edit"):
            items.append(Text(text=tr("scope_edit_targets"), subtext=self._scope_edit_subtext(), icon=self._icon("msg_edit", "msg_info"), on_click=self._show_scope_edit_editor))
        if FEATURES.on("chat_type_rules"):
            items.append(Text(text=tr("chat_types"), subtext=self._chat_types_subtext(), icon=self._icon("msg_groups", "msg_info"), on_click=self._show_chat_types_editor))
        return items + self._section_body(self._settings_exceptions())

    def _settings_mask(self) -> List[Any]:
        tr = self._tr
        items: List[Any] = [
            Header(text=tr("mask")),
            Text(text=tr("mask_text"), subtext=self._mask_preview_text(), icon="msg_edit", on_click=self._show_mask_editor),
        ]
        if FEATURES.on("conditional_masks"):
            items.append(Text(text=tr("conditional_masks"), subtext=self._conditional_masks_subtext(), icon=self._icon("msg_filter", "msg_settings"), on_click=self._show_conditional_masks_editor))
        if FEATURES.on("tag_line"):
            items.append(Text(text=tr("tag_lines"), subtext=self._tag_lines_subtext(), icon="msg_edit", on_click=self._show_tag_lines_editor))
        markdown_on = FEATURES.on("markdown")
        if markdown_on:
            items.append(self._switch("markdown_enabled", tr("markdown_style"), tr("markdown_style_subtext"), "msg_text", True))
        if markdown_on and self.settings.markdown_enabled():
            picks = [(value, key) for value, key, flag in MARKDOWN_PICKS if flag is None or FEATURES.on(flag)]
            self._markdown_pick_values = [value for value, _ in picks]
            current_markdown = self.settings.markdown_style_value()
            pick_index = self._markdown_pick_values.index(current_markdown) if current_markdown in self._markdown_pick_values else 0
            try:
                self.set_setting(self.MARKDOWN_PICK_KEY, pick_index)
            except Exception as exc:
                self.log(f"Prefixfy markdown widget state failed: {exc}")
            items.append(Selector(
                key=self.MARKDOWN_PICK_KEY, text=tr("markdown_style_pick"),
                default=pick_index,
                items=[tr(key) for _, key in picks],
                icon="msg_text", on_change=self._on_markdown_style_change,
            ))
        rotation_on = FEATURES.on("mask_rotation")
        if rotation_on:
            items.append(self._switch("mask_rotation_enabled", tr("mask_rotation"), tr("mask_rotation_subtext"), "msg_edit", True))
        if rotation_on and self.settings.get("mask_rotation_enabled"):
            items += [
                Text(text=tr("masks_list"), subtext=self._masks_list_subtext(), icon="msg_edit", on_click=self._show_masks_list_editor),
                Selector(
                    key="mask_rotation_mode", text=tr("mask_rotation_mode"),
                    default=clamp_int(self.settings.get("mask_rotation_mode"), 0, 0, 1),
                    items=[tr("mask_rotation_mode_random"), tr("mask_rotation_mode_sequential")], icon="msg_edit",
                    on_change=self._on_rotation_mode_change,
                ),
            ]
        return items

    def _settings_style(self) -> List[Any]:
        if not FEATURES.on("text_styles"):
            return []
        tr = self._tr
        items: List[Any] = [
            Header(text=tr("text_style")),
            self._switch("text_style_enabled", tr("text_style_enable"), tr("text_style_subtext"), "msg_palette", True),
        ]
        if self.settings.get("text_style_enabled"):
            items.append(self._switch("text_style_random", tr("text_style_random"), tr("text_style_random_subtext"), "msg_palette", True))
            values = available_styles()
            if not self.settings.get("text_style_random") and values:
                self._style_pick_values = values
                current_style = clamp_int(self.settings.get("text_style"), 0, 0, TEXT_STYLE_COUNT - 1)
                pick_index = values.index(current_style) if current_style in values else 0
                try:
                    self.set_setting(self.STYLE_PICK_KEY, pick_index)
                except Exception as exc:
                    self.log(f"Prefixfy style widget state failed: {exc}")
                items.append(Selector(
                    key=self.STYLE_PICK_KEY, text=tr("text_style"), default=pick_index,
                    items=[TEXT_STYLE_ITEMS[style] for style in values], icon="msg_palette",
                    on_change=self._on_text_style_change,
                ))
            items.append(self._switch("text_style_translit", tr("text_style_translit"), tr("text_style_translit_subtext"), "msg_text", True))
            items.append(Text(text=tr("style_words"), subtext=self._style_words_subtext(), icon="msg_edit", on_click=self._show_style_words_editor))
        return items

    def _frequency_handler(self, key: str, default: int):
        high = len(FREQUENCY_STEPS) - 1
        return lambda index: self.settings.set(key, clamp_int(index, default, 0, high))

    def _frequency_selector(self, key: str, text: str, default: int) -> Any:
        high = len(FREQUENCY_STEPS) - 1
        return Selector(
            key=key, text=text, default=clamp_int(self.settings.get(key), default, 0, high),
            items=list(FREQUENCY_ITEMS), icon=self._icon("msg_timer", "msg_edit"),
            on_change=self._frequency_handler(key, default),
        )

    def _cute_switch(self, key: str, text: str, subtext: str = "", icon: str = "msg_palette", reload_settings: bool = False):
        options = dict(
            key=key, text=text, default=PrefixfySettings.DEFAULTS[key], icon=icon,
            on_change=self._bool_handler(key, reload_settings),
        )
        if subtext:
            options["subtext"] = subtext
        return Switch(**options)

    def _cute_preview_text(self) -> str:
        tr = self._tr
        try:
            snapshot = self.settings.snapshot()
            if not any(getattr(snapshot.cute, key[5:]) for key in CUTE_EFFECT_KEYS):
                return tr("cute_preview_none")
            sample = tr("cute_preview_sample")
            result = CuteTransformation(snapshot).transform(sample)
            return f"{result}\n{tr('cute_preview_tap')}"
        except Exception as exc:
            self.log(f"Prefixfy cute preview failed: {exc}")
            return tr("cute_preview_none")

    def _on_preview_tap(self, *_):
        now = time.monotonic()
        if now - getattr(self, "_debug_tap_at", 0.0) <= DEBUG_TAP_GAP:
            self._debug_taps = getattr(self, "_debug_taps", 0) + 1
        else:
            self._debug_taps = 1
        self._debug_tap_at = now
        self._debug_tap_serial = serial = getattr(self, "_debug_tap_serial", 0) + 1
        if self._debug_taps >= DEBUG_TAP_COUNT and self._debug_allowed():
            self._debug_taps = 0
            if self.get_setting(DEBUG_ENABLED_KEY, False):
                self._debug_turn_off("debug_disabled")
            else:
                self._debug_unlock()
            return

        def refresh():
            if self._debug_tap_serial == serial:
                self.reload_settings_ui()

        run_on_ui_thread(refresh, int(DEBUG_TAP_GAP * 1000) + 30)

    def _debug_unlock(self):
        try:
            self.set_setting(DEBUG_ENABLED_KEY, True, reload_settings=False)
        except Exception as exc:
            self.log(f"Prefixfy debug unlock failed: {exc}")
            return
        self._toast("debug_enabled")
        self.reload_settings_ui()

    def _settings_debug(self) -> List[Any]:
        recorder = self.__dict__.get("_debug")
        if recorder is None or not self.get_setting(DEBUG_ENABLED_KEY, False):
            return []
        if not self._debug_allowed():
            if recorder.active:
                recorder.stop()
                self.set_setting(DEBUG_RECORDING_KEY, False, reload_settings=False)
            return []
        tr = self._tr
        items: List[Any] = [Header(text=tr("section_debug"))]
        lines, size = recorder.stats()
        amount = tr("debug_amount", lines=lines, size=self._debug_size(size))
        if recorder.active:
            items.append(Text(text=tr("debug_stop"), subtext=tr("debug_recording", amount=amount),
                              icon=self._icon("msg_check", "msg_info"), on_click=self._debug_stop_click))
        elif recorder.exists():
            items.append(Text(text=tr("debug_log"), subtext=tr("debug_log_subtext", amount=amount),
                              icon=self._icon("msg_document", "msg_info"), on_click=lambda *_: self._debug_actions()))
        else:
            items.append(Text(text=tr("debug_start"), subtext=tr("debug_start_subtext"),
                              icon=self._icon("msg_timer", "msg_info"), on_click=self._debug_start_click))
        items.append(Text(text=tr("debug_hide"), subtext=tr("debug_hide_subtext"),
                          icon=self._icon("msg_delete", "msg_info"), on_click=self._debug_hide_click))
        return items

    def _debug_size(self, size: int) -> str:
        tr = self._tr
        if size >= 1048576:
            return f"{size / 1048576:.1f} {tr('ota_unit_mb')}"
        return f"{max(1, round(size / 1024)) if size else 0} {tr('ota_unit_kb')}"

    def _debug_start_click(self, *_, resume: bool = False):
        recorder = self.__dict__.get("_debug")
        if recorder is None:
            return
        try:
            recorder.start(self._debug_header(False), resume=resume)
            self.set_setting(DEBUG_RECORDING_KEY, True, reload_settings=False)
            self._toast("debug_started")
        except Exception as exc:
            self.log(f"Prefixfy debug start failed: {exc}")
            self._toast("debug_failed")
        self.reload_settings_ui()

    def _debug_stop_click(self, *_):
        recorder = self.__dict__.get("_debug")
        if recorder is None:
            return
        recorder.stop("--- recording stopped ---")
        self.set_setting(DEBUG_RECORDING_KEY, False, reload_settings=False)
        self.reload_settings_ui()
        self._debug_actions()

    def _debug_actions(self):
        recorder = self.__dict__.get("_debug")
        if recorder is None or not recorder.exists():
            return
        activity = self._dialog_activity(None)
        if not activity:
            return
        tr = self._tr
        lines, size = recorder.stats()
        builder = AlertDialogBuilder(activity)
        builder.set_title(tr("debug_log"))
        builder.set_message(tr("debug_actions_message", amount=tr("debug_amount", lines=lines, size=self._debug_size(size))))
        actions = (self._debug_to_saved, self._debug_to_device, self._debug_delete, self._debug_continue)

        def picked(bld, which):
            bld.dismiss()
            if 0 <= which < len(actions):
                actions[which]()

        builder.set_items([tr("debug_to_saved"), tr("debug_to_device"), tr("debug_delete"), tr("debug_continue")], picked)
        builder.set_negative_button(tr("action_cancel"), lambda bld, which: bld.dismiss())
        self._show_builder(builder)

    def _debug_to_saved(self):
        recorder = self.__dict__.get("_debug")

        def work():
            try:
                account, user_id = self.transfer._saved_messages_target()
                path = recorder.export_copy(temp_dir("exports"))
                send_document(user_id, path, caption="", account=account)
                self._toast("debug_exported")
            except Exception as exc:
                self.log(f"Prefixfy debug export failed: {exc}")
                self._toast("debug_failed")

        threading.Thread(target=work, name="PrefixfyDebugExport", daemon=True).start()

    def _debug_to_device(self):
        recorder = self.__dict__.get("_debug")
        try:
            path = recorder.export_copy(temp_dir("exports"))
            self.transfer.request_debug_export(path)
        except Exception as exc:
            self.log(f"Prefixfy debug export failed: {exc}")
            self._toast("debug_failed")

    def _debug_delete(self):
        recorder = self.__dict__.get("_debug")
        if recorder is not None:
            recorder.delete()
        self.set_setting(DEBUG_RECORDING_KEY, False, reload_settings=False)
        self._toast("debug_deleted")
        self.reload_settings_ui()

    def _debug_continue(self):
        self._debug_start_click(resume=True)

    def _debug_hide_click(self, *_):
        self._debug_turn_off("debug_hidden")

    def _debug_turn_off(self, notice: str):
        recorder = self.__dict__.get("_debug")
        if recorder is not None:
            recorder.delete()
        self.set_setting(DEBUG_RECORDING_KEY, False, reload_settings=False)
        self.set_setting(DEBUG_ENABLED_KEY, False, reload_settings=False)
        self._toast(notice)
        self.reload_settings_ui()

    def _settings_cute(self) -> List[Any]:
        if not FEATURES.on("cute_effects"):
            return []
        tr, get = self._tr, self.settings.get
        items: List[Any] = [
            Header(text=tr("section_cute")),
            self._cute_switch("cute_enabled", tr("cute_enabled"), tr("cute_enabled_subtext"),
                              self._icon("menu_premium_effects", "msg_palette"), True),
        ]
        if not get("cute_enabled"):
            return items
        items.append(Text(text=tr("cute_preview"), subtext=self._cute_preview_text(),
                          icon=self._icon("msg_emoji_cat", "msg_edit"), on_click=self._on_preview_tap))
        for key in ("cute_kaomoji", "cute_sparkles", "cute_exclamations", "cute_punctuation", "cute_uwu_suffixes", "cute_actions"):
            items.append(self._cute_switch(key, tr(key), "", "msg_palette", True))
        if get("cute_actions"):
            items.append(self._cute_switch("cute_actions_newline", tr("cute_actions_newline"), "", "msg_reorder", True))
        if any(get(key) for key in ("cute_kaomoji", "cute_sparkles", "cute_exclamations", "cute_punctuation", "cute_uwu_suffixes", "cute_actions")):
            items += [
                self._frequency_selector("cute_sentence_frequency", tr("cute_sentence_frequency"), CUTE_SENTENCE_FREQUENCY_DEFAULT),
                Divider(text=tr("cute_sentence_frequency_subtext")),
            ]
        items += [
            self._cute_switch("cute_lowercase", tr("cute_lowercase"), "", "msg_text", True),
            self._cute_switch("cute_uwu_speak", tr("cute_uwu_speak"), "", "msg_text", True),
            self._cute_switch("cute_stutter", tr("cute_stutter"), "", "msg_text", True),
            self._cute_switch("cute_stretch", tr("cute_stretch"), "", "msg_text", True),
        ]
        if get("cute_stretch"):
            items.append(Selector(
                key="cute_stretch_max", text=tr("cute_stretch_max"),
                default=clamp_int(get("cute_stretch_max"), 0, 0, 1),
                items=[tr("cute_stretch_2x"), tr("cute_stretch_3x")], icon=self._icon("msg_noise_on", "msg_edit"),
                on_change=lambda index: self.settings.set("cute_stretch_max", clamp_int(index, 0, 0, 1), reload_settings=True),
            ))
        items.append(self._cute_switch("cute_soft_sign", tr("cute_soft_sign"), tr("cute_soft_sign_subtext"), "msg_text", True))
        if any(get(key) for key in ("cute_stutter", "cute_stretch", "cute_soft_sign")):
            items += [
                self._frequency_selector("cute_word_frequency", tr("cute_word_frequency"), CUTE_WORD_FREQUENCY_DEFAULT),
                Divider(text=tr("cute_word_frequency_subtext")),
            ]
        return items

    def _settings_separator(self) -> List[Any]:
        tr = self._tr
        items: List[Any] = [
            Header(text=tr("separator")),
            self._switch("separator_enabled", tr("separator_enable"), tr("separator_enable_subtext"), "msg_palette", True),
        ]
        if self.settings.get("separator_enabled"):
            items += [
                Text(text=tr("separator_set"), subtext=self._separator_preview_text(), icon="msg_edit", on_click=self._show_separator_editor),
                Input(
                    key="emoji_count", text=tr("separator_count"), default=str(self.settings.separator_count()),
                    subtext=tr("separator_count_subtext"), icon="msg_palette",
                    on_change=self._on_separator_count_change,
                ),
                self._frequency_selector("separator_frequency", tr("separator_frequency"), SEPARATOR_FREQUENCY_DEFAULT),
                Divider(text=tr("separator_frequency_subtext")),
            ]
            if FEATURES.on("separator_spaces"):
                items.insert(3, self._switch("separator_spaces", tr("separator_spaces"), tr("separator_spaces_subtext"), "msg_edit", True))
            if FEATURES.on("separator_spaces") and self.settings.get("separator_spaces"):
                items.insert(4, Selector(
                    key="separator_space_mode", text=tr("separator_space_mode"),
                    default=clamp_int(self.settings.get("separator_space_mode"), 0, 0, 2),
                    items=[tr("separator_space_both"), tr("separator_space_left"), tr("separator_space_right")],
                    icon="msg_edit",
                    on_change=lambda index: self.settings.set("separator_space_mode", clamp_int(index, 0, 0, 2)),
                ))
        return items

    def _settings_exceptions(self) -> List[Any]:
        tr = self._tr
        items: List[Any] = [
            Header(text=tr("exceptions")),
            Text(text=tr("exceptions"), subtext=self._exceptions_subtext(), icon="msg_info", on_click=self._show_exceptions_editor),
        ]
        if FEATURES.on("regex_exceptions"):
            items.append(Text(text=tr("regex_exceptions"), subtext=self._regex_subtext(), icon=self._icon("msg_text", "msg_info"), on_click=self._show_regex_exceptions_editor))
        items += [
            Text(text=tr("ignore_segments"), subtext=self._ignore_segments_subtext(), icon="msg_info", on_click=self._show_ignore_segments_editor),
        ]
        return items

    def _settings_media(self) -> List[Any]:
        if not FEATURES.on("attached_media"):
            return []
        tr, transfer = self._tr, self.transfer
        items: List[Any] = [Header(text=tr("media_attachment"))]
        if not transfer.media_exists():
            items.append(Text(text=tr("media_import"), subtext=tr("media_file_none"), icon="msg_download", on_click=transfer.request_media_import))
            return items
        name = as_text(self.settings.get("attached_media_name")) or os.path.basename(transfer.media_path())
        items += [
            Switch(
                key="attached_media_enabled", text=tr("media_attachment_enable"),
                default=PrefixfySettings.DEFAULTS["attached_media_enabled"],
                subtext=tr("media_attachment_enable_subtext"), icon="msg_image",
                on_change=self._on_media_enabled_change,
            ),
            Text(text=tr("media_file"), subtext=name or tr("media_file_none"), icon="msg_document", on_click=transfer.request_media_import),
            Text(text=tr("media_delete"), subtext=tr("media_delete_subtext"), icon="msg_delete", on_click=self._delete_imported_media),
        ]
        return items

    def _settings_language(self) -> List[Any]:
        if not has_language_choice():
            return []
        tr = self._tr
        language_index = self.settings.language_index()
        enabled = enabled_language_indices()
        auto_on = language_auto_enabled()
        if (language_index == 0 and not auto_on) or (language_index != 0 and language_index not in enabled):
            language_index = LANGUAGE_MODES.index("ru")
        position = enabled.index(language_index) if language_index in enabled else 0
        ui_state = (language_index, tuple(enabled), auto_on)
        if ui_state != getattr(self, "_language_ui_index", None):
            self._language_ui_index = ui_state
            self._language_ui_revision = self._next_language_ui_revision()
        auto_value = language_index == 0
        for attempt in range(2):
            revision = self._language_ui_revision
            auto_key = f"Prefixfy_language_auto_{revision}"
            select_key = f"Prefixfy_language_select_{revision}"
            if self._write_language_widgets(auto_key, auto_value, select_key, position):
                break
            if attempt == 0:
                self._language_ui_revision = self._next_language_ui_revision()
        icon = self._icon("msg_language")
        items: List[Any] = [
            Header(text=tr("language")),
        ]
        if auto_on:
            items.append(Switch(
                key=auto_key, text=tr("language_auto"), default=language_index == 0,
                subtext=tr("language_auto_subtext"), icon=icon, on_change=self._on_language_auto_change,
            ))
        if language_index != 0:
            items.append(Selector(
                key=select_key, text=tr("section_language"), default=position,
                items=self.localization.language_items(), icon=icon,
                on_change=self._on_language_select_change,
            ))
        return items

    def _next_language_ui_revision(self) -> int:
        """48.0.0: ключи виджетов языка не повторяются между запусками. Раньше счётчик после перезапуска (а сброс данных
        перезапускает плагин) шёл с единицы и брал уже занятые ключи, где оставалось прежнее «выключено»."""
        return max(int(time.time()), getattr(self, "_language_ui_revision", 0) + 1)

    def _write_language_widgets(self, auto_key: str, auto_value: bool, select_key: str, position: int) -> bool:
        """Пишет состояние виджетов языка и сразу проверяет, что оно прочиталось. False — не совпало."""
        verified = True
        for key, value in ((auto_key, auto_value), (select_key, position)):
            try:
                self.set_setting(key, value)
                stored = self.get_setting(key, None)
                if stored is None or (bool(stored) != bool(value) if isinstance(value, bool) else stored != value):
                    verified = False
            except Exception as exc:
                self.log(f"Prefixfy language widget state failed: {exc}")
                verified = False
        return verified

    def _language_ui_invalidate(self):
        """47.1.0: следующая отрисовка раздела языка берёт новые ключи виджетов (сброс, смена этапа мастера, флаги)."""
        self._language_ui_index = None

    def _on_features_changed(self):
        self._language_ui_invalidate()
        configurations = getattr(self, "configurations", None)
        if configurations is not None:
            try:
                configurations.accounts.invalidate()
                configurations.sync_target()
            except Exception as exc:
                self.log(f"Prefixfy account target sync failed: {exc}")
        try:
            self.runtime_manager.rebuild()
        except Exception as exc:
            self.log(f"Prefixfy features rebuild failed: {exc}")
        try:
            self.localization.invalidate()
        except Exception as exc:
            self.log(f"Prefixfy features language reset failed: {exc}")
        ref = weakref.ref(self)

        def task():
            plugin = ref()
            if plugin is None:
                return
            try:
                plugin._schedule_menu_refresh(250)
                plugin.reload_settings_ui()
            except Exception as exc:
                plugin.log(f"Prefixfy features UI refresh failed: {exc}")

        try:
            run_on_queue(task, PLUGINS_QUEUE, 1)
        except Exception as exc:
            self.log(f"Prefixfy features UI scheduling failed: {exc}")

    def _settings_export_blocked(self) -> List[Any]:
        """46.0.0: при «Требуется обновление» / «Изменённая сборка» оставляем только экспорт конфигураций."""
        remote = getattr(self, "remote", None)
        if remote is None or not remote.export_open():
            return []
        tr = self._tr
        return [
            Header(text=tr("section_configurations")),
            Text(
                text=tr("config_export"), subtext=tr("config_actions_subtext"),
                icon="msg_share", on_click=self.transfer.request_export,
            ),
        ]

    def _remote_notice(self) -> List[Any]:
        remote = getattr(self, "remote", None)
        if remote is None:
            return []
        tr = self._tr
        icon = self._icon("msg_report", "msg_info")
        if remote.blocked():
            key, kwargs = remote.notice()
            subtext = tr(key, **kwargs)
            checksum = remote.latest_checksum()
            if checksum and key in ("gate_update_required_subtext", "gate_modified_subtext"):
                subtext += f"\nSHA-256 {checksum[:12]}…"
            if key == "gate_account_blocked_subtext":
                return [Text(text=tr("gate_account_blocked"), subtext=subtext, icon=icon,
                             on_click=lambda *_: self._show_notice_dialog("account"))]
            if key == "gate_modified_subtext":
                rows = [Text(text=tr("gate_modified"), subtext=subtext, icon=icon)]
                candidate = remote.ota_candidate()
                if candidate is not None:
                    rows.append(Text(
                        text=tr("ota_download"),
                        subtext=tr("ota_download_subtext", version=format_version(candidate["version"])),
                        icon=self._icon("msg_download", "msg_retry"), on_click=self._show_ota_download_dialog,
                    ))
                return rows
            if key == "gate_update_required_subtext":
                staged = remote.staged_ready()
                if staged is not None:
                    return [Text(
                        text=tr("ota_almost_ready"),
                        subtext=tr("ota_almost_ready_subtext", version=as_text(staged.get("version"))),
                        icon=icon,
                    ), Text(
                        text=tr("ota_reload"), subtext=tr("ota_reload_subtext"),
                        icon=self._icon("msg_retry", "msg_download"), on_click=self._ota_reload_now,
                    )]
                rows = [Text(text=tr("gate_update_required"), subtext=subtext, icon=icon)]
                candidate = remote.ota_candidate()
                if candidate is not None:
                    rows.append(Text(
                        text=tr("ota_download"),
                        subtext=tr("ota_download_subtext", version=format_version(candidate["version"])),
                        icon=self._icon("msg_download", "msg_retry"), on_click=self._show_ota_download_dialog,
                    ))
                return rows
            return [Text(text=tr("gate_verify_required"), subtext=subtext, icon=icon,
                         on_click=lambda *_: self._show_notice_dialog("verify"))]
        if remote.suspended(False):
            return [
                Text(text=tr("gate_soft"), subtext=tr("gate_soft_subtext"), icon=icon,
                     on_click=lambda *_: self._show_notice_dialog("soft")),
            ]
        return []

    def _notice_dialog_text(self, kind: str) -> str:
        tr = self._tr
        if kind == "account":
            return tr("notice_account_body")
        if kind == "verify":
            return tr("notice_verify_body")
        if kind == "soft":
            return tr("notice_soft_body")
        return tr("notice_verify_body")

    def _show_notice_dialog(self, kind: str):
        tr = self._tr
        activity = self._dialog_activity()
        if not activity:
            return
        titles = {"verify": "gate_verify_required", "soft": "gate_soft", "account": "gate_account_blocked"}
        builder = AlertDialogBuilder(activity)
        builder.set_title(tr(titles.get(kind, "gate_verify_required")))
        try:
            message = self._notice_dialog_text(kind)
        except Exception as exc:
            self.log(f"Prefixfy notice text failed: {exc}")
            message = tr("notice_verify_body")
        builder.set_message(message)
        builder.set_positive_button(tr("notice_ok"), lambda bld, which: bld.dismiss())
        if kind == "soft":
            def check(bld, which):
                bld.dismiss()
                self._check_now()
            builder.set_negative_button(tr("check_now"), check)
        self._show_builder(builder)

    def _about_status_key(self) -> str:
        remote = getattr(self, "remote", None)
        return remote.status() if remote is not None else "status_pending"

    def _about_text(self) -> str:
        tr = self._tr
        unknown = tr("about_unknown")
        parts = parse_version(__build__)
        main = date_text = number = serial = unknown
        if len(parts) >= 3:
            main = f"{parts[0]}.{parts[1]}.{parts[2]}"
        if len(parts) == 6:
            raw_date = f"{parts[3]:08d}"
            try:
                date_text = datetime.strptime(raw_date, "%Y%m%d").strftime("%Y-%m-%d")
            except ValueError:
                date_text = raw_date
            number, serial = str(parts[4]), str(parts[5])
        lines = [
            f"{tr('about_version')}: {main}",
            f"{tr('about_build_date')}: {date_text}",
            f"{tr('about_build_number')}: {number}",
            f"{tr('about_serial')}: {serial}",
            f"{tr('about_build_label')}: {__build__ or unknown}",
        ]
        remote = getattr(self, "remote", None)
        status_key = self._about_status_key()
        latest = remote.latest_version() if remote is not None and status_key == "status_outdated" else ""
        if latest:
            lines.append(f"{tr('about_latest')}: {latest}")
        lines.append(f"{tr('about_status')}: {tr(status_key)}")
        text = "\n".join(lines)
        notes = self._about_changelog_block()
        if notes:
            text += "\n\n" + notes
        return text + "\n\n" + tr("about_note")

    def _about_changelog_block(self) -> str:
        """50.4.1: «Что нового» для текущей сборки в сведениях о плагине. Сначала проверенный манифест, затем список,
        сохранённый при обновлении. Если пунктов нет, блока нет вовсе. Ошибка здесь не должна ломать окно."""
        try:
            remote = getattr(self, "remote", None)
            notes = (remote.release_notes() if remote is not None else None) or {}
            if not notes and as_text(self.get_setting(UPDATED_BUILD_KEY, "")) == __build__:
                raw = self.get_setting(UPDATED_NOTES_KEY, "")
                notes = parse_changelog(json.loads(raw)) if isinstance(raw, str) and raw else {}
            if not changelog_for_language(notes, self.localization.language()):
                return ""
            return self._changelog_block(notes)
        except Exception as exc:
            self.log(f"Prefixfy about changelog failed: {exc}")
            return ""

    def _show_about(self, *_):
        activity = self._dialog_activity()
        if not activity:
            return
        builder = AlertDialogBuilder(activity)
        builder.set_title(self._tr("about_title"))
        builder.set_message(self._about_text())
        builder.set_positive_button(self._tr("notice_ok"), lambda bld, which: bld.dismiss())

        def open_wipe(bld, which):
            bld.dismiss()

            def later():
                run_on_ui_thread(self._show_wipe_dialog)
            run_on_queue(later, PLUGINS_QUEUE, 250)

        builder.set_neutral_button(self._tr("wipe_row"), open_wipe)
        self._show_builder(builder, red=("neutral",))

    def _settings_about(self) -> List[Any]:
        return [
            Header(text=self._tr("section_about")),
            Text(
                text=self._tr("about_plugin"), subtext=self._tr("about_plugin_subtext"),
                icon=self._icon("msg_info"), on_click=self._show_about,
            ),
        ]

    def _bypass_note(self) -> str:
        """Пояснение про блокировку: только если плагин остановлен из-за аккаунта в чёрном списке."""
        remote = getattr(self, "remote", None)
        try:
            if remote is not None and remote.enabled and remote.blacklisted():
                return "\n\n" + self._tr("gate_bypass_note")
        except Exception as exc:
            self.log(f"Prefixfy bypass note failed: {exc}")
        return ""

    def _show_wipe_dialog(self, *_):
        """Диалог 1: пояснение и чекбокс «Отказаться от использования» (по умолчанию снят). Кнопка «Далее» красная и WIPE_COOLDOWN_SEC секунд неактивна."""
        tr = self._tr

        def next_step(selected, opt_out):
            def later():
                run_on_ui_thread(lambda: self._show_wipe_confirm(bool(opt_out)))
            run_on_queue(later, PLUGINS_QUEUE, 250)

        self.show_checklist(
            tr("wipe_title"), [], next_step, message=tr("wipe_body"),
            extra=(tr("wipe_opt_out"), False, True), positive=tr("action_next"),
            cooldown=WIPE_COOLDOWN_SEC, red=True,
        )

    def _show_wipe_confirm(self, opt_out: bool):
        """Диалог 2: подтверждение. Кнопка «Очистить» красная и WIPE_COOLDOWN_SEC секунд неактивна; кулдаун проверяется и в обработчике."""
        activity = self._dialog_activity()
        if not activity:
            return
        tr = self._tr
        label = tr("wipe_confirm_btn")
        shown_at = time.monotonic()
        builder = AlertDialogBuilder(activity)
        builder.set_title(tr("wipe_confirm_title"))
        builder.set_message(tr("wipe_confirm_out" if opt_out else "wipe_confirm_clean") + self._bypass_note())

        def confirm(bld, which):
            if WIPE_COOLDOWN_SEC - (time.monotonic() - shown_at) > 0:
                return
            bld.dismiss()
            self._start_wipe(opt_out)

        builder.set_positive_button(f"{label} ({WIPE_COOLDOWN_SEC})", confirm)
        builder.set_negative_button(tr("action_cancel"), lambda bld, which: bld.dismiss())
        if self._show_builder(builder, red=("positive",)):
            self._run_wipe_countdown(builder, label, shown_at)

    _BUTTON_CODES = {
        "positive": AlertDialogBuilder.BUTTON_POSITIVE,
        "negative": AlertDialogBuilder.BUTTON_NEGATIVE,
        "neutral": AlertDialogBuilder.BUTTON_NEUTRAL,
    }
    _RED = 0xFFE53935 - (1 << 32)

    @staticmethod
    def _style_button(button, text: str, enabled: bool):
        try:
            button.setText(text)
            button.setEnabled(bool(enabled))
            button.setAlpha(1.0 if enabled else 0.4)
            button.setTextColor(PrefixfyPlugin._RED)
        except Exception:
            pass

    def _run_wipe_countdown(self, builder, label: str, shown_at: float):
        def tick():
            button = None
            while True:
                left = WIPE_COOLDOWN_SEC - (time.monotonic() - shown_at)
                if self.stop_event is not None and self.stop_event.is_set():
                    return
                if button is None:
                    button = builder.get_button(AlertDialogBuilder.BUTTON_POSITIVE)
                if button is not None:
                    text = label if left <= 0 else f"{label} ({int(math.ceil(left))})"
                    run_on_ui_thread(lambda b=button, t=text, e=left <= 0: self._style_button(b, t, e))
                if left <= 0:
                    return
                time.sleep(0.25)

        threading.Thread(target=tick, name="PrefixfyWipeCountdown", daemon=True).start()

    def _start_wipe(self, opt_out: bool):
        if self._wipe_running:
            return
        self._wipe_running = True
        self._toast("wipe_started" if opt_out else "wipe_started_multi")

        def work():
            try:
                remote = getattr(self, "remote", None)
                state = None
                reinstall = False
                if not opt_out and remote is not None:
                    remote.refresh(force=True)
                    state = remote.ota_candidate()
                    if state is None:
                        state = remote.reinstall_state()
                        reinstall = state is not None
                    if state is None:
                        self.log("Prefixfy wipe: no verified manifest, the build is not reinstalled before the reset")
                need = format_version(state["version"]) if state is not None else ""
                if not write_wipe_marker(opt_out, need):
                    self._toast("wipe_failed")
                    return
                if state is not None:
                    self._toast("wipe_reinstalling" if reinstall else "wipe_updating", version=need)
                    kind, info = "ota_failed", {}
                    for attempt in range(4):
                        kind, info = remote.ota_install(state, True, reinstall=True)
                        if kind == "ota_installed":
                            break
                        if kind == "ota_busy":
                            time.sleep(5.0)
                            continue
                        if attempt >= 1:
                            break
                        time.sleep(2.0)
                        try:
                            remote.refresh(force=True)
                            state = remote.ota_candidate() or remote.reinstall_state() or state
                        except Exception as exc:
                            self.log(f"Prefixfy wipe: manifest refresh before retry failed: {exc}")
                    if kind != "ota_installed":
                        clear_wipe_marker()
                        self._toast("wipe_update_failed", reason=as_text(info.get("reason") or kind)[:80])
                    return
                if not _host_restart_plugin(self.log):
                    self._toast("wipe_restart_manual")
            except Exception as exc:
                self.log(f"Prefixfy wipe request failed: {exc}")
                clear_wipe_marker()
                self._toast("wipe_failed")
            finally:
                self._wipe_running = False

        threading.Thread(target=work, name="PrefixfyWipe", daemon=True).start()

    def _settings_dormant(self) -> List[Any]:
        return [
            Text(
                text=self._tr("resume_title"), subtext=self._tr("resume_subtext"),
                icon=self._icon("msg_retry", "msg_info"), on_click=self._show_resume_dialog,
            ),
        ]

    def _show_resume_dialog(self, *_):
        activity = self._dialog_activity()
        if not activity:
            return
        tr = self._tr
        builder = AlertDialogBuilder(activity)
        builder.set_title(tr("resume_confirm_title"))
        builder.set_message(tr("resume_confirm_body"))

        def confirm(bld, which):
            bld.dismiss()
            self._resume_now()

        builder.set_positive_button(tr("resume_btn"), confirm)
        builder.set_negative_button(tr("action_cancel"), lambda bld, which: bld.dismiss())
        self._show_builder(builder)

    def _resume_now(self):
        """Выход из сна без перезапуска: метка стирается, плагин загружается заново, как при первой установке."""
        clear_dormant_marker()
        self._dormant = False
        try:
            self._on_plugin_load_impl()
        except Exception as exc:
            self.log(f"Prefixfy resume failed: {exc}")
            self._toast("resume_failed")
            threading.Thread(target=_host_restart_plugin, args=(self.log,), daemon=True).start()
            return
        self._toast("resume_done")
        self.reload_settings_ui(200)

    def _check_items(self) -> List[Any]:
        return [
            Text(
                text=self._tr("check_now"), subtext=self._tr("check_now_subtext"),
                icon=self._icon("msg_retry"), on_click=self._check_now,
            ),
        ]

    def _on_ota_auto_change(self, enabled):
        enabled = bool(enabled)
        self.settings.set("ota_auto", enabled, reload_settings=True)
        self.remote.ota_reschedule()
        if enabled:
            self.remote.ota_kick()

    def _on_ota_action_change(self, index):
        self.settings.set("ota_action", clamp_int(index, 1, 0, 1), reload_settings=True)

    def _on_ota_mode_change(self, index):
        self.settings.set("ota_mode", clamp_int(index, 0, 0, 1), reload_settings=True)
        self.remote.ota_reschedule()

    def _on_ota_time_change(self, value):
        parsed = parse_ota_time(value)
        if parsed is None:
            self._toast("ota_time_invalid")
            self.reload_settings_ui(250)
            return
        self.settings.set("ota_time", f"{parsed[0]:02d}:{parsed[1]:02d}", reload_settings=True)
        self.remote.ota_reschedule()

    def _ota_size_text(self, size) -> str:
        tr = self._tr
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            return tr("about_unknown")
        value = f"{size / 1048576:.1f} {tr('ota_unit_mb')}" if size >= 1048576 else f"{max(1, round(size / 1024))} {tr('ota_unit_kb')}"
        return value.replace(".", ",") if self.localization.language() in ("ru", "fr") else value

    def _ota_changelog_text(self, state) -> str:
        """«Что нового» только для действительно более новой версии (та же проверка, что в mismatch_reason).
        Для переустановки текущей или изменённой сборки блока нет. Ошибка здесь не должна ломать окно обновления."""
        try:
            build = parse_version(__build__)
            if not build or not build < tuple(state["version"]):
                return ""
            return self._changelog_block(state.get("changelog"))
        except Exception:
            return ""

    def _changelog_block(self, changelog) -> str:
        """Блок «Что нового» с пунктами на языке плагина, либо с пометкой, что разработчик ничего не указал."""
        lines = changelog_for_language(changelog, self.localization.language())
        body = "\n".join(lines) if lines else self._tr("ota_dl_changelog_none")
        return self._tr("ota_dl_changelog") + ":\n" + body

    def _ota_info_text(self, state) -> str:
        tr = self._tr
        unknown = tr("about_unknown")
        parts = tuple(state["version"])
        main = date_text = number = serial = unknown
        if len(parts) >= 3:
            main = f"{parts[0]}.{parts[1]}.{parts[2]}"
        if len(parts) == 6:
            raw_date = f"{parts[3]:08d}"
            try:
                date_text = datetime.strptime(raw_date, "%Y%m%d").strftime("%Y-%m-%d")
            except ValueError:
                date_text = raw_date
            number, serial = str(parts[4]), str(parts[5])
        lines = [
            f"{tr('about_version')}: {main}",
            f"{tr('about_build_date')}: {date_text}",
            f"{tr('about_build_number')}: {number}",
            f"{tr('about_serial')}: {serial}",
            f"{tr('about_build_label')}: {format_version(parts) or unknown}",
            f"{tr('ota_dl_size')}: {self._ota_size_text(state.get('size'))}",
        ]
        notes = self._ota_changelog_text(state)
        return "\n".join(lines) + ("\n\n" + notes if notes else "") + "\n\n" + tr("ota_dl_warning")

    def _show_ota_download_dialog(self, *_):
        remote = getattr(self, "remote", None)
        state = remote.ota_candidate() if remote is not None else None
        if state is None:
            return
        activity = self._dialog_activity()
        if not activity:
            return
        tr = self._tr
        builder = AlertDialogBuilder(activity)
        builder.set_title(tr("ota_dl_title"))
        builder.set_message(self._ota_info_text(state))

        def confirm(bld, which):
            bld.dismiss()
            self._ota_update_now()

        builder.set_positive_button(tr("ota_dl_confirm"), confirm)
        builder.set_negative_button(tr("action_cancel"), lambda bld, which: bld.dismiss())
        self._show_builder(builder)

    def _ota_update_now(self, *_):
        self._run_check(install=True)

    _reload_running = False

    def _ota_reload_now(self, *_):
        """«Перезагрузить»: без диалога сменить активный раздел и перезапустить плагин."""
        remote = getattr(self, "remote", None)
        if remote is None or self._reload_running:
            return
        self._reload_running = True

        def work():
            try:
                kind, info = remote.ota_reload()
                self._toast(kind, **info)
                if kind == "ota_failed":
                    self.reload_settings_ui()
            except Exception as exc:
                self.log(f"Prefixfy slot reload failed: {exc}")
                self._toast("ota_failed", reason=as_text(exc)[:80])
            finally:
                self._reload_running = False

        threading.Thread(target=work, name="PrefixfyOTAReload", daemon=True).start()

    def _settings_ota(self) -> List[Any]:
        return [Header(text=self._tr("section_updates"))] + self._ota_auto_items() + self._check_items()

    def _ota_auto_items(self) -> List[Any]:
        tr = self._tr
        remote = getattr(self, "remote", None)
        icon = self._icon("msg_download", "msg_retry")
        items: List[Any] = []
        items.append(Switch(
            key="ota_auto", text=tr("ota_auto"), default=PrefixfySettings.DEFAULTS["ota_auto"],
            subtext=tr("ota_auto_subtext"), icon=icon, on_change=self._on_ota_auto_change,
        ))
        if not self.settings.get("ota_auto"):
            return items
        mode = clamp_int(self.settings.get("ota_mode"), 0, 0, 1)
        items.append(Selector(
            key="ota_mode", text=tr("ota_mode"), default=mode,
            items=[tr("ota_mode_available"), tr("ota_mode_time")], icon=icon,
            on_change=self._on_ota_mode_change,
        ))
        if mode == 0:
            action = clamp_int(self.settings.get("ota_action"), 1, 0, 1)
            items.append(Selector(
                key="ota_action", text=tr("ota_action"), default=action,
                items=[tr("ota_action_download"), tr("ota_action_install")], icon=icon,
                on_change=self._on_ota_action_change,
            ))
        if mode == 1:
            when = parse_ota_time(self.settings.get("ota_time")) or parse_ota_time(OTA_SETTING_DEFAULTS["ota_time"])
            items.append(Input(
                key="ota_time", text=tr("ota_time"), default=f"{when[0]:02d}:{when[1]:02d}",
                subtext=tr("ota_time_subtext"), icon=self._icon("msg_calendar", "msg_recent"),
                on_change=self._on_ota_time_change,
            ))
        return items

    def _check_now(self, *_):
        remote = getattr(self, "remote", None)
        if remote is None or getattr(self, "_check_running", False):
            return
        activity = self._dialog_activity()
        if not activity:
            return
        tr = self._tr
        builder = AlertDialogBuilder(activity)
        builder.set_title(tr("check_confirm_title"))
        builder.set_message(tr("check_confirm_body") + self._bypass_note())

        def start(bld, which):
            bld.dismiss()
            self._run_check()

        builder.set_positive_button(tr("check_confirm_yes"), start)
        builder.set_negative_button(tr("action_cancel"), lambda bld, which: bld.dismiss())
        self._show_builder(builder)

    def _ota_on_check(self) -> bool:
        if not self.settings.get("ota_auto"):
            return False
        return clamp_int(self.settings.get("ota_mode"), 0, 0, 1) == 0

    def _run_check(self, install: bool = False):
        remote = getattr(self, "remote", None)
        if remote is None or getattr(self, "_check_running", False):
            return
        auto = self._ota_on_check()
        install = install or auto
        apply = auto and clamp_int(self.settings.get("ota_action"), 1, 0, 1) == 1
        self._check_running = True
        self._toast("check_started")

        def work():
            try:
                refreshed = remote.refresh(force=True)
                outcome = None
                if install:
                    outcome = remote.ota_manual(refreshed, apply=apply)
                elif refreshed:
                    found = remote.ota_candidate()
                    staged = remote.staged_ready()
                    if staged is not None:
                        outcome = ("ota_staged", {"version": as_text(staged.get("version"))})
                    elif found is not None:
                        outcome = ("check_update_found", {"version": format_version(found["version"])})
                if outcome is not None:
                    self._toast(outcome[0], **outcome[1])
                elif remote.blocked():
                    key, kwargs = remote.notice()
                    self._toast(key, **kwargs)
                elif remote.soft():
                    self._toast("check_failed")
                else:
                    self._toast("check_ok")
                self.reload_settings_ui()
            except Exception as exc:
                self.log(f"Prefixfy manual check failed: {exc}")
                self._toast("check_failed")
                try:
                    self.reload_settings_ui()
                except Exception:
                    pass
            finally:
                self._check_running = False

        threading.Thread(target=work, name="PrefixfyCheckNow", daemon=True).start()

    def _open_repo(self, *_):
        try:
            fragment = get_last_fragment()
            activity = fragment.getParentActivity() if fragment else None
            if activity is not None:
                activity.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(REPO_URL)))
        except Exception as exc:
            self.log(f"Prefixfy repo link failed: {exc}")

    _setup_busy = False
    _setup_gate_state = ""

    @staticmethod
    def _setup_valid_stage(raw) -> bool:
        return not isinstance(raw, bool) and isinstance(raw, int) and 1 <= raw <= SETUP_DONE

    def _setup_init(self):
        """Первичное состояние мастера.

        «Старой установкой» (мастера ещё не было, сразу «завершено») считается только та, у которой нет метки
        SETUP_SEEN_KEY: версия схемы переписывается при каждой загрузке и сама по себе ничего не доказывает.
        Если этап потерян (сброс настроек хоста, порча), а метка есть, это не старая установка: мастер начинается заново."""
        try:
            raw = self.get_setting(SETUP_STAGE_KEY, None)
            seen = self.get_setting(SETUP_SEEN_KEY, None) is not None
            if self._setup_valid_stage(raw):
                if not seen:
                    self.set_setting(SETUP_SEEN_KEY, 1, reload_settings=False)
                return
            legacy = (
                not seen and LegacyMigration.preexisting_install(self)
                and os.path.isdir(os.path.join(get_plugins_dir(), ConfigurationsManager.STORE_DIR_NAME))
            )
            self.set_setting(SETUP_STAGE_KEY, SETUP_DONE if legacy else 1, reload_settings=False)
            self.set_setting(SETUP_SEEN_KEY, 1, reload_settings=False)
        except Exception as exc:
            self.log(f"Prefixfy setup state init failed: {exc}")

    def _setup_stage(self) -> int:
        """Этап мастера. Отсутствующее или битое значение (системный сброс настроек хоста стирает ключи) — это этап 1,
        а не «завершено»: иначе кнопка сброса в шапке настроек позволяет обойти мастер и проверку аккаунта."""
        try:
            raw = self.get_setting(SETUP_STAGE_KEY, None)
        except Exception as exc:
            self.log(f"Prefixfy setup stage read failed: {exc}")
            raw = None
        if not self._setup_valid_stage(raw):
            self._setup_gate_state = ""
            self._language_ui_invalidate()
            try:
                self.set_setting(SETUP_STAGE_KEY, 1, reload_settings=False)
            except Exception as exc:
                self.log(f"Prefixfy setup stage restore failed: {exc}")
            return 1
        return raw

    def _setup_set_stage(self, stage: int, reload_settings: bool = True):
        """Этапы 1..SETUP_STAGE_COUNT. «Завершено» пишет только _setup_complete после проверки аккаунта."""
        stage = clamp_int(stage, 1, 1, SETUP_STAGE_COUNT)
        self.set_setting(SETUP_STAGE_KEY, stage, reload_settings=reload_settings)

    def _setup_complete(self):
        self.set_setting(SETUP_STAGE_KEY, SETUP_DONE, reload_settings=False)

    def _setup_gate_start(self):
        if self._setup_gate_state in ("checking", "done"):
            return
        remote = getattr(self, "remote", None)
        if remote is None or not remote.enabled:
            self._setup_gate_state = "done"
            return
        self._setup_gate_state = "checking"

        def work():
            try:
                remote.refresh(force=True)
            except Exception as exc:
                self.log(f"Prefixfy setup account check failed: {exc}")
            finally:
                self._setup_gate_state = "done"
                self._language_ui_invalidate()
                try:
                    self.reload_settings_ui()
                except Exception as exc:
                    self.log(f"Prefixfy setup settings refresh failed: {exc}")

        threading.Thread(target=work, name="PrefixfySetupGate", daemon=True).start()

    def _welcome_start(self):
        try:
            self.set_setting(WELCOME_UNTIL_KEY, time.time() + WELCOME_SECONDS, reload_settings=False)
        except Exception as exc:
            self.log(f"Prefixfy welcome start failed: {exc}")

    def _welcome_items(self) -> List[Any]:
        """Кнопка-благодарность в самом верху настроек: WELCOME_SECONDS (4 часа) после успешного завершения мастера или до нажатия «Понятно»."""
        try:
            until = float(self.get_setting(WELCOME_UNTIL_KEY, 0) or 0)
        except Exception:
            return []
        if until <= 0:
            return []
        if time.time() >= until:
            try:
                self.set_setting(WELCOME_UNTIL_KEY, 0, reload_settings=False)
            except Exception as exc:
                self.log(f"Prefixfy welcome clear failed: {exc}")
            return []
        tr = self._tr
        return [self._setup_button(
            tr("welcome_banner"), tr("welcome_banner_subtext"), self._icon("msg_info"),
            self._show_welcome_dialog, accent=True,
        )]

    def _show_welcome_dialog(self, *_):
        activity = self._dialog_activity()
        if not activity:
            return
        builder = AlertDialogBuilder(activity)
        builder.set_title(self._tr("welcome_title"))
        builder.set_message(self._tr("welcome_body"))
        def understood(bld, which):
            bld.dismiss()
            try:
                self.set_setting(WELCOME_UNTIL_KEY, 0, reload_settings=False)
                self.reload_settings_ui()
            except Exception as exc:
                self.log(f"Prefixfy welcome dismiss failed: {exc}")

        builder.set_positive_button(self._tr("welcome_ok"), understood)
        self._show_builder(builder)

    def _updated_arm(self):
        """50.4.0: включает плашку «Обновление завершено», если эту сборку поставил модуль OTA со старой версии.
        Признак: файл состояния OTA, который пишет установщик (старая версия) при смене разделов: state=pending,
        to равен нашей сборке, prev старше её, это не самолечение (heal). Повторные загрузки той же сборки плашку не включают."""
        try:
            data = _ota_read()
            build = parse_version(__build__)
            previous = parse_version(data.get("prev"))
            if (data.get("state") != "pending" or data.get("to") != __build__ or data.get("heal") is True
                    or not build or not previous or not previous < build):
                return
            if as_text(self.get_setting(UPDATED_BUILD_KEY, "")) == __build__:
                return
            try:
                started = float(self.get_setting(SETUP_UPDATE_AT_KEY, 0) or 0)
            except (TypeError, ValueError):
                started = 0.0
            if started:
                self.set_setting(SETUP_UPDATE_AT_KEY, 0, reload_settings=False)
                if 0 <= time.time() - started < SETUP_UPDATE_WINDOW:
                    self.set_setting(UPDATED_BUILD_KEY, __build__, reload_settings=False)
                    return
            remote = getattr(self, "remote", None)
            notes = remote.release_notes() if remote is not None else None
            packed = json.dumps({code: list(lines) for code, lines in notes.items()}, ensure_ascii=False) if notes else ""
            self.set_setting(UPDATED_BUILD_KEY, __build__, reload_settings=False)
            self.set_setting(UPDATED_NOTES_KEY, packed, reload_settings=False)
            self.set_setting(UPDATED_UNTIL_KEY, time.time() + WELCOME_SECONDS, reload_settings=False)
        except Exception as exc:
            self.log(f"Prefixfy update notice failed: {exc}")

    def _updated_items(self) -> List[Any]:
        """Плашка «Обновление завершено» вверху настроек: те же правила, что у плашки-благодарности."""
        try:
            until = float(self.get_setting(UPDATED_UNTIL_KEY, 0) or 0)
        except Exception:
            return []
        if until <= 0:
            return []
        if time.time() >= until:
            try:
                self.set_setting(UPDATED_UNTIL_KEY, 0, reload_settings=False)
            except Exception as exc:
                self.log(f"Prefixfy update notice clear failed: {exc}")
            return []
        tr = self._tr
        return [self._setup_button(
            tr("updated_banner"), tr("updated_banner_subtext"), self._icon("msg_download", "msg_info"),
            self._show_updated_dialog, accent=True,
        )]

    def _updated_text(self) -> str:
        tr = self._tr
        parts = parse_version(__build__)
        lines = []
        if len(parts) >= 3:
            lines.append(f"{tr('about_version')}: {parts[0]}.{parts[1]}.{parts[2]}")
        label = format_version(parts) if parts else ""
        if label:
            lines.append(f"{tr('about_build_label')}: {label}")
        notes: Dict[str, Tuple[str, ...]] = {}
        try:
            raw = self.get_setting(UPDATED_NOTES_KEY, "")
            notes = parse_changelog(json.loads(raw)) if isinstance(raw, str) and raw else {}
        except Exception:
            notes = {}
        if not notes:
            remote = getattr(self, "remote", None)
            notes = (remote.release_notes() if remote is not None else None) or {}
        return "\n".join(lines) + ("\n\n" if lines else "") + self._changelog_block(notes)

    def _show_updated_dialog(self, *_):
        activity = self._dialog_activity()
        if not activity:
            return
        builder = AlertDialogBuilder(activity)
        builder.set_title(self._tr("updated_banner"))
        try:
            message = self._updated_text()
        except Exception as exc:
            self.log(f"Prefixfy update notice text failed: {exc}")
            message = self._tr("ota_dl_changelog") + ":\n" + self._tr("ota_dl_changelog_none")
        builder.set_message(message)

        def understood(bld, which):
            bld.dismiss()
            try:
                self.set_setting(UPDATED_UNTIL_KEY, 0, reload_settings=False)
                self.reload_settings_ui()
            except Exception as exc:
                self.log(f"Prefixfy update notice dismiss failed: {exc}")

        builder.set_positive_button(self._tr("welcome_ok"), understood)
        self._show_builder(builder)

    def _setup_button(self, text, subtext, icon, on_click, accent=False):
        if accent:
            try:
                return Text(text=text, subtext=subtext, icon=icon, on_click=on_click, accent=True)
            except TypeError:
                pass
        return Text(text=text, subtext=subtext, icon=icon, on_click=on_click)

    def _setup_go(self, stage: int):
        self._language_ui_invalidate()
        if self._setup_busy:
            return
        try:
            current = self._setup_stage()
            if current >= SETUP_DONE:
                return
            stage = clamp_int(stage, 1, 1, SETUP_STAGE_COUNT)
            if stage > current + 1:
                return
            self._setup_set_stage(stage)
        except Exception as exc:
            self.log(f"Prefixfy setup stage change failed: {exc}")

    def _setup_update_deferred(self) -> bool:
        """Мастер не прерывается: единственная причина блокировки - вышла новая версия."""
        remote = getattr(self, "remote", None)
        try:
            return bool(remote is not None and remote.enabled and not remote.blacklisted()
                        and remote.mismatch_reason() == "outdated")
        except Exception as exc:
            self.log(f"Prefixfy setup update state failed: {exc}")
            return False

    def _setup_pending_update(self) -> Optional[str]:
        """Версия, которую «Завершить настройку» поставит после проверки, или None."""
        if not self._setup_update_deferred():
            return None
        try:
            state = self.remote.ota_candidate()
        except Exception:
            state = None
        return format_version(state["version"]) if state else None

    def _setup_finish(self, *_):
        if self._setup_busy:
            return
        if self._setup_stage() != SETUP_STAGE_COUNT:
            return
        remote = getattr(self, "remote", None)
        if remote is None:
            self._toast("check_failed")
            return
        self._setup_busy = True
        self._toast("check_started")
        started = time.monotonic()

        def work():
            try:
                try:
                    refreshed = remote.refresh(force=True)
                except Exception as exc:
                    self.log(f"Prefixfy setup refresh failed: {exc}")
                    refreshed = None
                if remote.blacklisted():
                    self.reload_settings_ui()
                    return
                if remote.enabled and not (remote.blacklist_confirmed_since(started) and remote.devices_known()):
                    self._toast("check_failed")
                    self.reload_settings_ui()
                    return
                if self._setup_stage() != SETUP_STAGE_COUNT:
                    self.reload_settings_ui()
                    return
                self._setup_complete()
                if (not remote.blocked() or self._setup_update_deferred()) and not remote.soft():
                    self._welcome_start()
                if getattr(self, "_check_running", False):
                    self._toast("setup_done")
                    self.reload_settings_ui()
                    return
                deferred = refreshed and self._setup_pending_update() is not None
                if deferred:
                    self._toast("setup_almost_update")
                    self.set_setting(SETUP_UPDATE_AT_KEY, time.time(), reload_settings=False)
                outcome = remote.ota_manual(refreshed, apply=True)
                if deferred and (not outcome or outcome[0] != "ota_installed"):
                    self.set_setting(SETUP_UPDATE_AT_KEY, 0, reload_settings=False)
                if outcome is not None:
                    self._toast(outcome[0], **outcome[1])
                elif remote.blocked():
                    key, kwargs = remote.notice()
                    self._toast(key, **kwargs)
                elif remote.soft():
                    self._toast("check_failed")
                else:
                    self._toast("setup_done")
                self.reload_settings_ui()
            except Exception as exc:
                self.log(f"Prefixfy setup finish failed: {exc}")
                try:
                    self.reload_settings_ui()
                except Exception:
                    pass
            finally:
                self._setup_busy = False

        threading.Thread(target=work, name="PrefixfySetupFinish", daemon=True).start()

    def _settings_setup(self, stage: int) -> List[Any]:
        tr = self._tr
        if self._setup_gate_state != "done":
            self._setup_gate_start()
            if self._setup_gate_state == "checking":
                return [Text(
                    text=tr("setup_checking"), subtext=tr("setup_checking_subtext"),
                    icon=self._icon("msg_retry"), on_click=lambda *_: None,
                )]
        language_choice = has_language_choice()
        if stage <= 1 and not language_choice:
            stage = 2
            try:
                self._setup_set_stage(2, reload_settings=False)
            except Exception as exc:
                self.log(f"Prefixfy setup stage change failed: {exc}")
        stage = max(1, min(SETUP_STAGE_COUNT, stage))
        if stage == 1:
            body = self._section_body(self._settings_language())
        elif stage == 2:
            body = self._section_body(self._settings_appearance())
        else:
            body = self._ota_auto_items()
        items: List[Any] = [Header(text=tr(f"setup_step_{stage}"))] + list(body) + [Divider()]
        forward = self._icon("msg_arrowright", self._icon("msg_forward", "msg_retry"))
        backward = self._icon("msg_back", self._icon("msg_go_up", "msg_retry"))
        if stage < SETUP_STAGE_COUNT:
            next_stage = stage + 1
            items.append(self._setup_button(
                tr("setup_next"), tr("setup_next_subtext", step=next_stage), forward,
                lambda *_, _to=next_stage: self._setup_go(_to), accent=True,
            ))
        else:
            pending = self._setup_pending_update()
            finish_subtext = (tr("setup_finish_update_subtext", version=pending) if pending
                              else tr("setup_finish_subtext"))
            items.append(self._setup_button(
                tr("setup_finish"), finish_subtext, self._icon("msg_check", self._icon("msg_retry")),
                self._setup_finish, accent=True,
            ))
        if stage > 1 and not (stage == 2 and not language_choice):
            back_stage = stage - 1
            items.append(Divider())
            items.append(self._setup_button(
                tr("setup_back"), tr("setup_back_subtext", step=back_stage), backward,
                lambda *_, _to=back_stage: self._setup_go(_to),
            ))
        return items

    def create_settings(self) -> List[Any]:
        if self._wipe_halt:
            return self._settings_wipe_halt()
        if self._dormant:
            return self._settings_dormant()
        self.localization.refresh()
        self.remote.ensure_fresh()
        in_setup = self._setup_stage() < SETUP_DONE
        setup_defers_update = in_setup and self._setup_update_deferred()
        notice = [] if setup_defers_update else self._remote_notice()
        if notice and self.remote.blocked():
            if self.remote.blacklisted():
                return (notice + [Header(text=self._tr("section_updates"))] + self._check_items()[:1] + self._settings_about()
                        + self._settings_debug())
            return notice + self._settings_export_blocked() + self._settings_ota() + self._settings_about() + self._settings_debug()
        if in_setup:
            wizard = self._settings_setup(self._setup_stage())
            if wizard:
                return wizard
        settings: List[Any] = self._welcome_items() + self._updated_items() + list(notice)
        try:
            self.configurations.sync_target()
        except Exception as exc:
            self.log(f"Prefixfy account target sync failed: {exc}")
        for section in (
            self._settings_general, self._settings_configurations, self._settings_scope,
            self._settings_appearance,
            self._settings_language, self._settings_ota, self._settings_about, self._settings_debug,
        ):
            settings += section()
        return settings

    _MEDIA_FIELDS = ("photo", "document", "video", "media", "path")
    INTERNAL_SENDS_MAX = 128
    _skip_once = None
    _mask_rotation_index = 0
    _last_random_mask = None
    _last_random_style = None
    _rotation_lock = threading.Lock()
    _counter_lock = threading.Lock()
    _tls = threading.local()
    _skip_lock = threading.Lock()

    @property
    def _count_used(self) -> bool:
        return getattr(self._tls, "count_used", False)

    @_count_used.setter
    def _count_used(self, value):
        self._tls.count_used = bool(value)

    @property
    def _chat_count_key(self):
        return getattr(self._tls, "chat_count_key", None)

    @_chat_count_key.setter
    def _chat_count_key(self, value):
        self._tls.chat_count_key = value

    @classmethod
    def _params_have_media(cls, params) -> bool:
        for name in cls._MEDIA_FIELDS:
            try:
                value = getattr(params, name, None)
            except Exception:
                continue
            if value is not None and value != "":
                return True
        return False

    @staticmethod
    def _carry_over_options(params) -> Dict[str, Any]:
        options: Dict[str, Any] = {}
        for name in ("replyToMsg", "replyToTopMsg"):
            try:
                value = getattr(params, name, None)
            except Exception:
                value = None
            if value is not None:
                options[name] = value
        try:
            schedule = java_int(getattr(params, "scheduleDate", None))
        except Exception:
            schedule = None
        if schedule and schedule > 0:
            options["scheduleDate"] = schedule
        try:
            if getattr(params, "notify", True) is False:
                options["notify"] = False
        except Exception:
            pass
        return options

    def _remember_internal_send(self, dialog_id, caption: str):
        now = time.time()
        with self._internal_lock:
            sends = {key: expiry for key, expiry in self._internal_sends.items() if expiry > now}
            sends[(dialog_id, caption)] = now + INTERNAL_SEND_TTL
            while len(sends) > self.INTERNAL_SENDS_MAX:
                sends.pop(next(iter(sends)))
            self._internal_sends = sends

    def _forget_internal_send(self, dialog_id, caption: str):
        with self._internal_lock:
            self._internal_sends.pop((dialog_id, caption), None)

    def _is_internal_send(self, dialog_id, caption: str) -> bool:
        with self._internal_lock:
            expiry = self._internal_sends.pop((dialog_id, caption), 0)
        return expiry > time.time()

    @staticmethod
    def _pick_media_sender(name: str, mime: str):
        name = as_text(name).lower()
        mime = as_text(mime).lower()
        if mime == "image/gif" or name.endswith(".gif"):
            return send_document
        if mime.startswith("image/"):
            return send_document if mime in ("image/svg+xml", "image/heic", "image/heif", "image/tiff") else send_photo
        if mime.startswith("video/"):
            return send_video
        return send_document

    def _call_sender(self, sender, dialog_id, path: str, caption: str, account: int, options: Dict[str, Any]):
        if options:
            try:
                sender(dialog_id, path, caption=caption, account=account, **options)
                return
            except Exception as exc:
                self.log(f"Prefixfy send with carried-over options failed, retrying without them: {exc}")
                keep = {key: options[key] for key in ("scheduleDate", "entities") if key in options}
                if keep:
                    try:
                        sender(dialog_id, path, caption=caption, account=account, **keep)
                        return
                    except Exception as retry_exc:
                        self.log(f"Prefixfy send with caption entities failed, sending plain caption: {retry_exc}")
                        if "scheduleDate" in keep:
                            sender(dialog_id, path, caption=caption, account=account, scheduleDate=keep["scheduleDate"])
                            return
        sender(dialog_id, path, caption=caption, account=account)

    def _send_attached_media(self, dialog_id, media, caption: str, account: int, options: Optional[Dict[str, Any]] = None):
        path, name, mime = media
        options = dict(options or {})
        if caption:
            self._remember_internal_send(dialog_id, caption)
        try:
            path = media_plain_copy(path, name)
            self._call_sender(self._pick_media_sender(name, mime), dialog_id, path, caption, account, options)
        except Exception as exc:
            self.log(f"Prefixfy attached media send failed: {exc}")
            if caption:
                self._forget_internal_send(dialog_id, caption)
            self._send_plain_fallback(dialog_id, caption, account, options)

    def _send_plain_fallback(self, dialog_id, text: str, account: int, options: Optional[Dict[str, Any]] = None):
        if not text:
            return
        self._remember_internal_send(dialog_id, text)
        attempts = []
        if options:
            attempts.append({"peer": dialog_id, "message": text, **options})
        base = {"peer": dialog_id, "message": text}
        if options and "scheduleDate" in options:
            base["scheduleDate"] = options["scheduleDate"]
        attempts.append(base)
        for index, payload in enumerate(attempts):
            try:
                _send_message(payload, account=account)
                return
            except Exception as exc:
                self.log(f"Prefixfy plain fallback send failed (attempt {index + 1}): {exc}")
        self._forget_internal_send(dialog_id, text)

    def on_send_message_hook(self, account: int, params: Any) -> HookResult:
        tracing = _TRACE_SINK is not None and self._debug_tracing()
        if tracing:
            started = time.perf_counter()
            before = self._trace_lengths(params)
        try:
            result = self._process_outgoing(account, params)
        except Exception as exc:
            import traceback
            self.log(f"Prefixfy send hook failed: {exc}\n{traceback.format_exc()}")
            result = HookResult()
        if tracing:
            trace_action("send", account=account, peer=getattr(params, "peer", None), before=before,
                         after=self._trace_lengths(params), result=result.strategy.name,
                         ms=round((time.perf_counter() - started) * 1000, 1))
        return result

    def _debug_tracing(self) -> bool:
        recorder = self.__dict__.get("_debug")
        return recorder is not None and recorder.active and self._debug_allowed()

    @staticmethod
    def _trace_lengths(params) -> str:
        parts = []
        for field in ("message", "caption"):
            value = getattr(params, field, None)
            if isinstance(value, str):
                parts.append(f"{field}:{utf16_length(value)}")
        entities = getattr(params, "entities", None)
        try:
            parts.append(f"entities:{len(entities) if entities is not None else 0}")
        except Exception:
            pass
        return ",".join(parts) or "-"

    def _capture_custom_emoji(self, params, account: int) -> bool:
        entities = [entity for _, items in entity_sources(params) for entity in items]
        markers = []
        for field in ("message", "caption"):
            markers = custom_emoji_markers(getattr(params, field, None), entities)
            if markers:
                break
        if not markers:
            markers = custom_emoji_markers_from_input()
        dialog_id = self._dialog_id_from_params(params, account)
        if not markers or dialog_id is None:
            return False
        try:
            self.set_setting("capture_custom_emoji", False)
        except Exception as exc:
            self.log(f"Prefixfy capture flag reset failed: {exc}")
            return False
        text = " ".join(markers)
        options = self._carry_over_options(params)
        run_on_queue(lambda: self._send_plain_fallback(dialog_id, text, account, options), PLUGINS_QUEUE, 350)
        return True

    @staticmethod
    def _account_is_premium(account, default: bool = True) -> bool:
        try:
            return bool(get_user_config(int(account)).isPremium())
        except Exception:
            return default

    def _caption_limit(self, account: int) -> int:
        return PREMIUM_CAPTION_LIMIT if self._account_is_premium(account, default=False) else CAPTION_LIMIT

    @staticmethod
    def _select_field(settings: RuntimeSettings, message, caption, has_media: bool = False) -> Tuple[Optional[str], str]:
        if has_media:
            if not settings.process_media:
                return None, ""
            if isinstance(caption, str) and caption.strip():
                return "caption", caption
            if isinstance(message, str) and message.strip():
                return "message", message
            return None, ""
        if settings.process_message and isinstance(message, str) and message.strip():
            return "message", message
        return None, ""

    def _try_attach_media(self, runtime: Runtime, dialog_id, params, message, has_media: bool, account: int) -> bool:
        settings = runtime.settings
        if has_media or dialog_id is None or not settings.process_message:
            return False
        if not (isinstance(message, str) and message.strip()):
            return False
        if runtime.pipeline.ignores(message):
            return False
        media = runtime.attached_media()
        if media is None:
            return False
        options = self._carry_over_options(params)
        if "scheduleDate" in options or self._existing_entity_count(params) > 0:
            return False
        limit = self._caption_limit(account)
        outgoing, entities, body_offset = self._transform_text(runtime, message)
        entities = self._finalize_entities(account, params, entities, body_offset)
        if utf16_length(outgoing) > limit:
            return False
        if entities:
            carrier = _EntityCarrier()
            outgoing = self._apply_entities(runtime, carrier, message, outgoing, entities, body_offset)
            if utf16_length(outgoing) > limit:
                return False
            built = carrier.entities
            if built is not None:
                try:
                    built = list(built)
                except Exception:
                    built = [built.get(index) for index in range(int(built.size()))]
                if built:
                    options["entities"] = built
        run_on_queue(lambda: self._send_attached_media(dialog_id, media, outgoing, account, options), PLUGINS_QUEUE, 350)
        return True

    def _transform_text(self, runtime: Runtime, text: str):
        pipeline = runtime.pipeline
        if runtime.settings.markdown_enabled or pipeline.markdown_table:
            try:
                transformed, entities, body_offset = pipeline.transform_rich(text)
                if entities and pipeline.has_special(text):
                    entities = [item for item in entities if item[0] not in MARKDOWN_ENTITY_KINDS]
                return transformed, entities, body_offset
            except Exception as exc:
                self.log(f"Prefixfy rich-text parse failed: {exc}")
        return pipeline.transform(text), [], None

    @staticmethod
    def _existing_entity_count(params) -> int:
        existing = getattr(params, "entities", None)
        if existing is None:
            return 0
        try:
            return len(existing)
        except Exception:
            pass
        try:
            return int(existing.size())
        except Exception:
            return 0

    def _finalize_entities(self, account: int, params, entities, body_offset):
        if not entities:
            return entities
        reserved = self._existing_entity_count(params) if body_offset is not None else 0
        if any(item[0] == "CustomEmoji" for item in entities):
            if not FEATURES.on("premium_emoji") or not self._account_is_premium(account):
                entities = [item for item in entities if item[0] != "CustomEmoji"]
            else:
                entities = limit_custom_emoji(entities, reserved)
        return entities[:max(0, MAX_MESSAGE_ENTITIES - reserved)]

    @staticmethod
    def _realign_args(pipeline, text: str, transformed: str):
        prefix = pipeline.mask_prefix(text)
        start = utf16_length(prefix) if prefix and transformed.startswith(prefix) else 0
        return text, transformed, start

    def _apply_entities(self, runtime: Runtime, params, text: str, transformed: str, entities, body_offset) -> str:
        existing = getattr(params, "entities", None)
        snapshot = self._snapshot_entities(existing)
        if not entities:
            if existing is not None and snapshot:
                try:
                    pipeline = runtime.pipeline
                    shifted = body_offset_in(pipeline.expected_body(text), transformed, pipeline.mask_prefix(text))
                    params.entities = _make_tg_entities([], existing, shifted, pipeline.entity_mapper(text),
                                                        self._realign_args(pipeline, text, transformed))
                except Exception as exc:
                    self.log(f"Prefixfy entity shift failed: {exc}")
                    self._restore_entities(snapshot, existing)
                    try:
                        params.entities = existing
                    except Exception:
                        pass
            return transformed
        try:
            params.entities = _make_tg_entities(entities, existing, body_offset, runtime.pipeline.entity_mapper(text),
                                                self._realign_args(runtime.pipeline, text, transformed))
        except Exception as exc:
            self.log(f"Prefixfy Markdown entities unavailable: {exc}")
            plain = runtime.pipeline.transform(text)
            self._restore_entities(snapshot, existing)
            try:
                params.entities = existing
            except Exception:
                pass
            if existing is not None and snapshot:
                try:
                    pipeline = runtime.pipeline
                    shifted = body_offset_in(pipeline.expected_body(text), plain, pipeline.mask_prefix(text))
                    params.entities = _make_tg_entities([], existing, shifted, pipeline.entity_mapper(text),
                                                        self._realign_args(pipeline, text, plain))
                except Exception as shift_exc:
                    self.log(f"Prefixfy entity shift failed: {shift_exc}")
                    self._restore_entities(snapshot, existing)
            return plain
        return transformed

    @staticmethod
    def _snapshot_entities(existing) -> list:
        if existing is None:
            return []
        try:
            return [(entity, int(entity.offset), int(entity.length)) for entity in list(existing)]
        except Exception:
            return []

    @staticmethod
    def _restore_entities(snapshot, existing=None) -> None:
        for entity, offset, length in snapshot:
            try:
                entity.offset = offset
                entity.length = length
            except Exception:
                pass
        if existing is not None and snapshot:
            try:
                existing.clear()
                for entity, _, _ in snapshot:
                    existing.add(entity)
            except Exception:
                pass

    def _dialog_kind(self, account: int, dialog_id) -> Optional[str]:
        if dialog_id is None or not _is_int(dialog_id):
            return None
        if dialog_id > 0:
            return "private"
        kinds = self._dialog_kinds
        cached = kinds.get(dialog_id)
        if cached is not None:
            return cached
        try:
            controller = get_messages_controller(int(account))
            chat = controller.getChat(find_class("java.lang.Long").valueOf(-int(dialog_id)))
        except Exception as exc:
            self.log(f"Prefixfy chat kind lookup failed: {exc}")
            return None
        if chat is None:
            return None
        kind = "channel" if getattr(chat, "broadcast", False) else "group"
        try:
            while len(kinds) >= DIALOG_KINDS_MAX:
                kinds.pop(next(iter(kinds)), None)
        except (RuntimeError, StopIteration):
            kinds.clear()
        kinds[dialog_id] = kind
        return kind

    def _chat_type_allowed(self, account: int, dialog_id, kinds) -> bool:
        if len(kinds) >= len(CHAT_KINDS):
            return True
        kind = self._dialog_kind(account, dialog_id)
        if kind is None:
            if _is_int(dialog_id) and dialog_id < 0:
                return "group" in kinds or "channel" in kinds
            return True
        return kind in kinds

    def _chat_title(self, account: int, dialog_id) -> str:
        if dialog_id is None:
            return ""
        key = (account, dialog_id)
        now = time.monotonic()
        cached = self._chat_titles.get(key)
        if cached is not None and cached[0] > now:
            return cached[1]
        title = self._lookup_chat_title(account, dialog_id)
        if title:
            titles = self._chat_titles
            try:
                while len(titles) >= CHAT_TITLE_CACHE_MAX:
                    titles.pop(next(iter(titles)), None)
            except (RuntimeError, StopIteration):
                titles.clear()
            titles[key] = (now + CHAT_TITLE_TTL, title)
        return title

    def _lookup_chat_title(self, account: int, dialog_id) -> str:
        title = ""
        try:
            fragment = get_last_fragment()
            if (fragment is not None and self._current_dialog_id() == dialog_id
                    and self._current_account_slot() == int(account)):
                if dialog_id < 0:
                    chat = fragment.getCurrentChat()
                    title = as_text(chat.title) if chat is not None else ""
                else:
                    user = fragment.getCurrentUser()
                    if user is not None:
                        title = as_text(find_class("org.telegram.messenger.UserObject").getUserName(user))
        except Exception as exc:
            self.log(f"Prefixfy chat title (screen) lookup failed: {exc}")
        if title:
            return title
        try:
            controller = get_messages_controller(int(account))
            boxed = find_class("java.lang.Long").valueOf(abs(int(dialog_id)))
            if dialog_id < 0:
                chat = controller.getChat(boxed)
                return as_text(chat.title) if chat is not None else ""
            user = controller.getUser(boxed)
            return as_text(find_class("org.telegram.messenger.UserObject").getUserName(user)) if user is not None else ""
        except Exception as exc:
            self.log(f"Prefixfy chat title lookup failed: {exc}")
            return ""

    def _own_username(self, account) -> str:
        try:
            user = get_user_config(int(account)).getCurrentUser()
            name = as_text(getattr(user, "username", None))
            if not name:
                for item in list(getattr(user, "usernames", None) or []):
                    if bool(getattr(item, "active", False)) and as_text(getattr(item, "username", None)):
                        name = as_text(getattr(item, "username", None))
                        break
            return name or as_text(getattr(user, "first_name", None))
        except Exception as exc:
            self.log(f"Prefixfy username lookup failed: {exc}")
            return ""

    COUNTER_FLUSH_MS = 3000
    _counter_state: Optional[Dict[str, Any]] = None
    _counter_flush_armed = False

    def _counter_data(self) -> Dict[str, Any]:
        """Вызывать под _counter_lock."""
        state = self._counter_state
        if state is None:
            try:
                chats = json.loads(as_text(self.get_setting(CHAT_COUNTS_KEY, "")) or "{}")
            except (ValueError, TypeError):
                chats = {}
            if not isinstance(chats, dict):
                chats = {}
            state = {
                "total": clamp_int(self.get_setting(COUNTER_KEY, 0), 0, 0, 10 ** 9),
                "chats": {str(key): value for key, value in chats.items()
                          if len(str(key)) <= 48 and _is_int(value) and 0 <= value <= 10 ** 9},
                "dirty": False,
            }
            self._counter_state = state
        return state

    def _message_number(self) -> int:
        self._count_used = True
        with self._counter_lock:
            return self._counter_data()["total"] + 1

    def _commit_message_counter(self):
        used, chat_key = self._count_used, self._chat_count_key
        self._count_used = False
        self._chat_count_key = None
        if not used and not chat_key:
            return
        with self._counter_lock:
            state = self._counter_data()
            if used:
                state["total"] = min(state["total"] + 1, 10 ** 9)
            if chat_key:
                counts = state["chats"]
                current = counts.pop(chat_key, 0)
                counts[chat_key] = min(current + 1, 10 ** 9)
                while len(counts) > MAX_CHAT_COUNTS:
                    counts.pop(next(iter(counts)), None)
            state["dirty"] = True
            arm = not self._counter_flush_armed
            self._counter_flush_armed = True
        if arm:
            try:
                run_on_queue(self._flush_counters, PLUGINS_QUEUE, self.COUNTER_FLUSH_MS)
            except Exception as exc:
                self.log(f"Prefixfy counter flush scheduling failed: {exc}")
                self._flush_counters()

    def _flush_counters(self):
        with self._counter_lock:
            self._counter_flush_armed = False
            state = self._counter_state
            if state is None or not state["dirty"]:
                return
            values = {COUNTER_KEY: state["total"], CHAT_COUNTS_KEY: json.dumps(state["chats"])}
            state["dirty"] = False
        if not bulk_set_settings(self, values):
            self.log("Prefixfy counter save failed")

    def _chat_counts(self) -> Dict[str, int]:
        with self._counter_lock:
            return dict(self._counter_data()["chats"])

    def _chat_message_number(self, account, dialog_id) -> int:
        if dialog_id is None:
            return 1
        key = f"{account}:{dialog_id}"
        self._chat_count_key = key
        with self._counter_lock:
            return self._counter_data()["chats"].get(key, 0) + 1

    def _reply_name(self, account, params) -> str:
        try:
            message = getattr(params, "replyToMsg", None)
            if message is None:
                return ""
            owner = getattr(message, "messageOwner", None)
            controller = get_messages_controller(int(account))
            boxed = find_class("java.lang.Long")
            for field in ("from_id", "peer_id"):
                peer = getattr(owner, field, None)
                if peer is None:
                    continue
                if field == "from_id":
                    user_id = java_int(getattr(peer, "user_id", 0)) or 0
                    if user_id:
                        user = controller.getUser(boxed.valueOf(abs(int(user_id))))
                        if user is not None:
                            return as_text(find_class("org.telegram.messenger.UserObject").getUserName(user))
                chat_id = java_int(getattr(peer, "channel_id", 0)) or java_int(getattr(peer, "chat_id", 0)) or 0
                if chat_id:
                    chat = controller.getChat(boxed.valueOf(abs(int(chat_id))))
                    if chat is not None:
                        return as_text(chat.title)
                if field == "from_id":
                    return ""
        except Exception as exc:
            self.log(f"Prefixfy reply name lookup failed: {exc}")
        return ""

    def _reply_quote(self, params) -> str:
        try:
            message = getattr(params, "replyToMsg", None)
            owner = getattr(message, "messageOwner", None) if message is not None else None
            text = as_text(getattr(owner, "message", "")) if owner is not None else ""
        except Exception as exc:
            self.log(f"Prefixfy reply quote lookup failed: {exc}")
            return ""
        text = " ".join(text.split())
        return text[:REPLY_QUOTE_LIMIT] + ("…" if len(text) > REPLY_QUOTE_LIMIT else "")

    def _weather_text(self, city: str) -> str:
        weather = getattr(self, "_weather", None)
        return weather.get(city) if weather is not None else ""

    def _battery_text(self) -> str:
        try:
            from android.content import IntentFilter
            context = find_class("org.telegram.messenger.ApplicationLoader").applicationContext
            status = context.registerReceiver(None, IntentFilter("android.intent.action.BATTERY_CHANGED"))
            if status is None:
                return ""
            level, scale = int(status.getIntExtra("level", -1)), int(status.getIntExtra("scale", -1))
            if level >= 0 and scale > 0:
                return f"{max(0, min(100, level * 100 // scale))}%"
        except Exception as exc:
            self.log(f"Prefixfy battery lookup failed: {exc}")
        return ""

    def _random_line(self, preview: bool = False) -> str:
        try:
            lines = [line for line in parse_lines(self.settings.get("tag_lines"))[:MAX_TAG_LINES] if line.strip()]
        except Exception as exc:
            self.log(f"Prefixfy tag lines failed: {exc}")
            lines = []
        if not lines:
            return "\u2026" if preview else ""
        return lines[0] if preview else random.choice(lines)

    def _expand_mask_tags(self, mask, account, dialog_id, preview: bool = False, params=None) -> str:
        mask = as_text(mask)
        if "[" not in mask or not MASK_TAG_RE.search(mask):
            return mask
        now = datetime.now()
        values: Dict[str, str] = {}

        def value(tag: str) -> str:
            if tag not in values:
                if tag == "date":
                    raw = now.strftime("%Y-%m-%d")
                elif tag == "time":
                    raw = now.strftime("%H:%M")
                elif tag == "datetime":
                    raw = now.strftime("%Y-%m-%d %H:%M")
                elif tag == "year":
                    raw = now.strftime("%Y")
                elif tag == "month":
                    raw = now.strftime("%m")
                elif tag == "day":
                    raw = now.strftime("%d")
                elif tag in ("weekday", "weekday_short"):
                    language = self.localization.language()
                    if tag == "weekday_short" and language in WEEKDAY_SHORT:
                        raw = WEEKDAY_SHORT[language][now.weekday()]
                    else:
                        names = WEEKDAY_NAMES.get(language, WEEKDAY_NAMES["ru"])
                        raw = names[now.weekday()]
                        if tag == "weekday_short":
                            raw = raw[:3]
                elif tag == "year_short":
                    raw = now.strftime("%y")
                elif tag == "time12":
                    raw = now.strftime("%I:%M")
                elif tag == "ampm":
                    raw = "AM" if now.hour < 12 else "PM"
                elif tag == "hour":
                    raw = now.strftime("%H")
                elif tag == "minute":
                    raw = now.strftime("%M")
                elif tag == "second":
                    raw = now.strftime("%S")
                elif tag == "week":
                    raw = str(now.isocalendar()[1])
                elif tag == "yearday":
                    raw = str(now.timetuple().tm_yday)
                elif tag == "monthname":
                    names = MONTH_NAMES.get(self.localization.language(), MONTH_NAMES["ru"])
                    raw = names[now.month - 1]
                elif tag == "daypart":
                    names = DAYPART_NAMES.get(self.localization.language(), DAYPART_NAMES["ru"])
                    raw = names[daypart_index(now.hour * 60 + now.minute)]
                elif tag == "timestamp":
                    raw = str(int(time.time()))
                elif tag == "tz":
                    offset = now.astimezone().utcoffset()
                    minutes = int(offset.total_seconds() // 60) if offset is not None else 0
                    sign = "+" if minutes >= 0 else "-"
                    raw = f"UTC{sign}{abs(minutes) // 60:02d}:{abs(minutes) % 60:02d}"
                elif tag == "chattype":
                    raw = "private" if preview else (self._dialog_kind(account, dialog_id) or "")
                elif tag == "dice":
                    raw = str(random.randint(1, 6))
                elif tag == "id":
                    raw = ("12345" if preview else "") if dialog_id is None else str(dialog_id)
                elif tag == "username":
                    raw = "username" if preview else self._own_username(account)
                elif tag == "count":
                    raw = "1" if preview else str(self._message_number())
                elif tag in ("random_emoji", "emoji"):
                    raw = random.choice(RANDOM_EMOJI)
                elif tag == "reply":
                    raw = "Name" if preview else self._reply_name(account, params)
                elif tag == "chatcount":
                    raw = "1" if preview else str(self._chat_message_number(account, dialog_id))
                elif tag == "battery":
                    raw = "100%" if preview else self._battery_text()
                elif tag == "moon":
                    raw = moon_phase_emoji()
                elif tag == "line":
                    raw = self._random_line(preview)
                elif tag.startswith(("since:", "until:")):
                    raw = days_tag_value(tag, now.date())
                elif tag.startswith("countdown:"):
                    raw = countdown_tag_value(tag, now, self.localization.language())
                elif tag == "quote":
                    raw = "…" if preview else self._reply_quote(params)
                elif tag == "weather" or tag.startswith("weather:"):
                    raw = "☀ +20°C" if preview else self._weather_text(tag.partition(":")[2])
                else:
                    raw = self._chat_title(account, dialog_id) or ("…" if preview else "")
                values[tag] = sanitize_tag_value(raw)
            return values[tag]

        dropped = []

        def replace(match) -> str:
            tag = match.group(1).lower()
            flag = "tag_" + tag.split(":", 1)[0]
            if FEATURES.on(flag):
                return value(tag)
            dropped.append(tag)
            return ""

        result = MASK_TAG_RE.sub(replace, mask)
        if dropped:
            result = re.sub(r"(?<=\S)[ \t]{2,}", " ", result).strip(" \t")
        return result

    def _runtime_for_message(self, runtime, account: int, dialog_id, text: str = "", params=None):
        settings = runtime.settings
        mask = settings.mask
        rotation_next = None
        self._count_used = False
        self._chat_count_key = None
        matched = None
        if text and settings.conditional_rules:
            sample = text[:REGEX_TEXT_LIMIT]
            matched = next((candidate for pattern, candidate in settings.conditional_rules if pattern.search(sample)), None)
        masks = settings.masks_list
        if matched is not None:
            mask = matched
        elif settings.mask_rotation_enabled and masks:
            if settings.mask_rotation_mode == 0:
                mask = self._pick_fresh(masks, self._last_random_mask)
                self._last_random_mask = mask
            else:
                with self._rotation_lock:
                    index = self._mask_rotation_index % len(masks)
                mask = masks[index]
                rotation_next = (index + 1) % len(masks)
        volatile = MASK_TAG_RE.search(mask) is not None
        mask = self._expand_mask_tags(mask, account, dialog_id, params=params)
        style = settings.text_style
        if settings.text_style_enabled and settings.text_style_random:
            pool = random_style_pool()
            if pool:
                style = self._pick_fresh(pool, self._last_random_style)
                self._last_random_style = style
        if mask == settings.mask and style == settings.text_style:
            return runtime, rotation_next
        try:
            derived = runtime.derived(mask, style, cache=not volatile)
        except Exception as exc:
            self.log(f"Prefixfy per-message runtime failed: {exc}")
            self._count_used = False
            self._chat_count_key = None
            return runtime, None
        return derived, rotation_next

    @staticmethod
    def _pick_fresh(pool, last):
        choices = [item for item in pool if item != last] or list(pool)
        return random.choice(choices)

    def _advance_rotation(self, next_index):
        if next_index is not None:
            with self._rotation_lock:
                self._mask_rotation_index = next_index
        self._commit_message_counter()

    def _process_outgoing(self, account: int, params: Any) -> HookResult:
        if not self.remote.allows():
            return HookResult()
        dialog_id = self._dialog_id_from_params(params, account)
        message = getattr(params, "message", None)
        caption = getattr(params, "caption", None)
        has_media = self._params_have_media(params)

        already_styled = caption if has_media else message
        if isinstance(already_styled, str) and already_styled and self._is_internal_send(dialog_id, already_styled):
            return HookResult()
        if FEATURES.on("premium_emoji") and self.settings.get("capture_custom_emoji", False) and self._capture_custom_emoji(params, account):
            return HookResult(strategy=HookStrategy.CANCEL)

        runtime = self._base_runtime(account)
        if runtime is None:
            return HookResult()

        runtime = self._runtime_for_chat(runtime, dialog_id, account)
        settings = runtime.settings
        if not self._chat_type_allowed(account, dialog_id, settings.chat_type_rules):
            return HookResult()
        if not settings.is_chat_allowed(dialog_id):
            return HookResult()

        if self._skip_once is not None and self._is_article(params) and self._consume_skip_once(dialog_id):
            return HookResult()
        article = self._decorate_article(runtime, params, account)
        if article is not None:
            return article

        field, text = self._select_field(settings, message, caption, has_media)
        if field is None:
            return HookResult()
        if has_media:
            runtime = runtime.for_caption()
            settings = runtime.settings
        resent = self._handle_resend(runtime, account, params, text)
        if resent is not None:
            return resent
        if self._skip_once is not None and not runtime.pipeline.ignores(text) and self._consume_skip_once(dialog_id):
            return HookResult()
        runtime, rotation_next = self._runtime_for_message(runtime, account, dialog_id, text, params)
        if field == "message" and self._try_attach_media(runtime, dialog_id, params, message, has_media, account):
            self._advance_rotation(rotation_next)
            return HookResult(strategy=HookStrategy.CANCEL)

        transformed = self._decorate_text(runtime, account, params, text, field == "caption", rotation_next)
        if transformed is None:
            return HookResult()
        setattr(params, field, transformed)
        return HookResult(strategy=HookStrategy.MODIFY, params=params)

    @staticmethod
    def _is_article(params) -> bool:
        try:
            return bool(FEATURES.on("articles") and article_blocks(params))
        except Exception:
            return False

    def _decorate_article(self, runtime: Runtime, params, account: int = 0, editing: bool = False) -> Optional[HookResult]:
        """40.0.0: оформление текстовых блоков статьи. None - это не статья (обычный путь).
        40.1.0: если у узла текста есть поле entities, маска ставится так же, как в обычном сообщении:
        Premium Emoji (и Markdown маски) уходят сущностями. Иначе остаётся прежний путь: обычный текст,
        а Premium Emoji заменяются своими обычными эмодзи."""
        if not FEATURES.on("articles"):
            return None
        blocks = article_blocks(params)
        if not blocks:
            return None
        settings = runtime.settings
        if not (settings.process_edit_article if editing else settings.process_article):
            return HookResult()
        pipeline = runtime.pipeline
        changed = 0
        try:
            targets = article_text_blocks(blocks)
        except Exception as exc:
            self.log(f"Prefixfy article blocks lookup failed: {exc}")
            return HookResult()
        leaves = []
        for block in targets:
            try:
                leaves.append(article_text_leaf(block))
            except Exception:
                leaves.append(None)
        keep = [False] * len(targets)
        mask = pipeline._mask()
        if mask is not None:
            try:
                keep = article_frame_plan([leaf[2] if leaf else None for leaf in leaves], mask.left, mask.right)
            except Exception as exc:
                self.log(f"Prefixfy article frame check failed: {exc}")
        for block, leaf, ready in zip(targets, leaves, keep):
            if ready:
                if leaf is not None and mask is not None and mask.table:
                    try:
                        self._article_restore_emoji(runtime, account, leaf)
                    except Exception as exc:
                        self.log(f"Prefixfy article fallback emoji failed: {exc}")
                continue
            try:
                if leaf is None:
                    continue
                holder, field, text, parent = leaf
                if not text.strip() or pipeline.ignores(text):
                    continue
                if self._decorate_article_leaf(runtime, account, holder, field, text, parent):
                    changed += 1
            except Exception as exc:
                self.log(f"Prefixfy article block skipped after an error: {exc}")
        if not changed:
            return HookResult()
        return HookResult(strategy=HookStrategy.MODIFY, params=params)

    def _decorate_article_leaf(self, runtime: Runtime, account: int, holder, field: str, text: str, parent=None) -> bool:
        pipeline = runtime.pipeline
        wants_entities = bool(runtime.settings.markdown_enabled or pipeline.markdown_table)
        if wants_entities and article_holder_supports_entities(holder):
            existing = getattr(holder, "entities", None)
            snapshot = self._snapshot_entities(existing)
            try:
                transformed, entities, body_offset = self._transform_text(runtime, text)
                entities = self._finalize_entities(account, holder, entities, body_offset)
                if transformed == text and not entities:
                    return False
                transformed = self._apply_entities(runtime, holder, text, transformed, entities, body_offset)
                setattr(holder, field, transformed)
                return True
            except Exception as exc:
                import traceback
                self.log(f"Prefixfy article entities failed, using plain text: {exc}\n{traceback.format_exc()}")
                self._restore_entities(snapshot, existing)
                try:
                    holder.entities = existing
                except Exception:
                    pass
        elif wants_entities and parent is not None and FEATURES.on("premium_emoji"):
            if self._decorate_article_emoji(runtime, account, parent, text):
                return True
        transformed = pipeline.transform(text)
        if transformed == text:
            return False
        setattr(holder, field, transformed)
        return True

    def _decorate_article_emoji(self, runtime: Runtime, account: int, parent, text: str) -> bool:
        """Заменяет parent.text на textConcat: обычный текст + узлы Premium Emoji. False - обычный путь."""
        try:
            transformed, entities, body_offset = self._transform_text(runtime, text)
            entities = self._finalize_entities(account, parent, entities, body_offset)
            spans = sorted((item for item in entities if item[0] == "CustomEmoji"), key=lambda item: item[1])
            if not spans:
                return False
            return self._article_emoji_concat(parent, transformed, spans)
        except Exception as exc:
            import traceback
            self.log(f"Prefixfy article Premium Emoji failed, using plain text: {exc}\n{traceback.format_exc()}")
            return False

    def _article_emoji_concat(self, parent, text: str, spans) -> bool:
        """parent.text = textConcat: обычный текст + узлы Premium Emoji по spans [(CustomEmoji, смещение, длина, id)]."""
        kind = article_emoji_kind()
        if kind is None:
            if not _ARTICLE_EMOJI["warned"]:
                _ARTICLE_EMOJI["warned"] = True
                self.log("Prefixfy articles: no Premium Emoji node in TL_iv " + ", ".join(_article_emoji_kinds()))
            return False
        children = []
        emoji_nodes = 0
        pos = 0
        for _, offset, length, document_id in spans:
            start = _utf16_index(text, offset)
            end = _utf16_index(text, offset + length)
            if start < pos or end <= start:
                continue
            if start > pos:
                children.append(article_plain_node(text[pos:start]))
            children.append(article_emoji_node(kind, int(document_id), text[start:end]))
            emoji_nodes += 1
            pos = end
        if not emoji_nodes:
            return False
        if pos < len(text):
            children.append(article_plain_node(text[pos:]))
        parent.text = article_concat_node(children)
        return True

    def _decorate_text(self, runtime: Runtime, account: int, params, text: str, is_caption: bool, rotation_next) -> Optional[str]:
        transformed, entities, body_offset = self._transform_text(runtime, text)
        entities = self._finalize_entities(account, params, entities, body_offset)
        if transformed == text and not entities:
            return None
        limit = self._caption_limit(account) if is_caption else MESSAGE_LIMIT
        if utf16_length(transformed) > limit:
            return None
        original_entities = getattr(params, "entities", None)
        snapshot = self._snapshot_entities(original_entities)
        transformed = self._apply_entities(runtime, params, text, transformed, entities, body_offset)
        if utf16_length(transformed) > limit:
            self._restore_entities(snapshot, original_entities)
            try:
                params.entities = original_entities
            except Exception:
                pass
            return None
        self._advance_rotation(rotation_next)
        return transformed

    EDIT_FLAG_ENTITIES = 1 << 3
    EDIT_FLAG_MESSAGE = 1 << 11

    @staticmethod
    def _class_name(value) -> str:
        try:
            return str(value.getClass().getName())
        except Exception:
            return type(value).__name__

    def _edit_request_seen(self, request) -> bool:
        try:
            key = int(find_class("java.lang.System").identityHashCode(request))
        except Exception:
            return False
        now = time.monotonic()
        with self._internal_lock:
            seen = {k: expiry for k, expiry in self._edit_seen.items() if expiry > now}
            found = key in seen
            seen[key] = now + 10
            while len(seen) > 256:
                seen.pop(next(iter(seen)))
            self._edit_seen = seen
        return found

    def _resend_mask_match(self, runtime: Runtime, text: str):
        """46.7.0: маска с Premium Emoji уже стоит в тексте запасными эмодзи. Возвращает описания Premium Emoji
        [(CustomEmoji, смещение, длина, document_id)] для найденных сторон или None, если маски в тексте нет.
        Найденная сторона считается целостной: вторая сторона не дописывается."""
        settings = runtime.settings
        masks = [settings.mask]
        if settings.mask_rotation_enabled:
            masks.extend(settings.masks_list)
        masks.extend(candidate for _, candidate in settings.conditional_rules)
        for mask in dict.fromkeys(masks):
            if MASK_TAG_RE.search(mask) is not None:
                continue
            try:
                probe = runtime if mask == settings.mask else runtime.derived(mask, settings.text_style)
                part = probe.pipeline._mask()
            except Exception as exc:
                self.log(f"Prefixfy fallback emoji: mask check failed: {exc}")
                continue
            if part is None or not part.table:
                continue
            left = fallback_side_spans(part.left, part.table, text, False) if part._has_custom_emoji(part.left) else None
            right = fallback_side_spans(part.right, part.table, text, True) if part._has_custom_emoji(part.right) else None
            if left and right and left[-1][1] > right[0][0]:
                right = None
            spans = (left or []) + (right or [])
            if spans:
                return fallback_emoji_entities(text, spans)
        return None

    @staticmethod
    def _custom_emoji_have(existing) -> set:
        have = set()
        for entity in _iter_entities(existing):
            if _is_custom_emoji_entity(entity):
                try:
                    have.add((int(entity.offset), _entity_document_id(entity)))
                except Exception:
                    continue
        return have

    def _missing_mask_emoji(self, account: int, params, wanted) -> list:
        """Какие Premium Emoji маски ещё нужно добавить (пусто, если Premium недоступен или всё уже на месте)."""
        if not wanted or not FEATURES.on("premium_emoji") or not self._account_is_premium(account):
            return []
        have = self._custom_emoji_have(getattr(params, "entities", None))
        missing = [item for item in wanted if (item[1], int(item[3])) not in have]
        return limit_custom_emoji(missing, self._existing_entity_count(params)) if missing else []

    def _handle_resend(self, runtime: Runtime, account: int, params, text: str) -> Optional[HookResult]:
        """Маска уже нанесена (повторная отправка, вставленный или пересланный текст с запасными эмодзи):
        второй раз её не добавляем, а запасные эмодзи маски превращаем в Premium Emoji."""
        wanted = self._resend_mask_match(runtime, text)
        if wanted is None:
            return None
        missing = self._missing_mask_emoji(account, params, wanted)
        if not missing:
            return HookResult()
        try:
            params.entities = _make_tg_entities(missing, getattr(params, "entities", None), 0)
        except Exception as exc:
            self.log(f"Prefixfy resend: Premium Emoji restore failed: {exc}")
            return HookResult()
        return HookResult(strategy=HookStrategy.MODIFY, params=params)

    def _edit_restore_mask_emoji(self, runtime: Runtime, account: int, request, text: str) -> bool:
        """46.7.0: при правке запасные эмодзи маски возвращаются в Premium Emoji. True — маска уже в тексте."""
        try:
            wanted = self._resend_mask_match(runtime, text)
        except Exception as exc:
            self.log(f"Prefixfy edit: fallback emoji check failed: {exc}")
            return False
        if wanted is None:
            return False
        missing = self._missing_mask_emoji(account, request, wanted)
        if missing:
            try:
                request.entities = _make_tg_entities(missing, getattr(request, "entities", None), 0)
                request.flags = int(request.flags) | self.EDIT_FLAG_ENTITIES
            except Exception as exc:
                self.log(f"Prefixfy edit: Premium Emoji restore failed: {exc}")
        return True

    def _article_restore_emoji(self, runtime: Runtime, account: int, leaf) -> None:
        """46.7.0: в готовом блоке статьи запасные эмодзи маски становятся Premium Emoji."""
        holder, field, text, parent = leaf
        wanted = self._resend_mask_match(runtime, text)
        if not wanted or not FEATURES.on("premium_emoji") or not self._account_is_premium(account):
            return
        if article_holder_supports_entities(holder):
            missing = self._missing_mask_emoji(account, holder, wanted)
            if missing:
                holder.entities = _make_tg_entities(missing, getattr(holder, "entities", None), 0)
        elif parent is not None:
            self._article_emoji_concat(parent, text, sorted(wanted, key=lambda item: item[1]))

    def _edit_is_decorated(self, runtime: Runtime, text: str) -> bool:
        settings = runtime.settings
        if settings.cute.active and cute_already_applied(text):
            return True
        masks = [settings.mask]
        if settings.mask_rotation_enabled:
            masks.extend(settings.masks_list)
        masks.extend(candidate for _, candidate in settings.conditional_rules)
        for mask in dict.fromkeys(masks):
            tagged = MASK_TAG_RE.search(mask) is not None
            probe = MASK_TAG_RE.sub(TAG_GAP, mask) if tagged else mask
            try:
                probe_runtime = runtime if probe == settings.mask else runtime.derived(probe, settings.text_style)
                mask_part = probe_runtime.pipeline._mask()
            except Exception as exc:
                self.log(f"Prefixfy edit: mask check failed: {exc}")
                continue
            if mask_part is None:
                continue
            if not tagged:
                if mask_part.has_mask(text):
                    return True
                continue
            left = mask_side_matcher(mask_part.left_plain, False)
            right = mask_side_matcher(mask_part.right_plain, True)
            if (left is not None and left(text)) or (right is not None and right(text)):
                return True
        return False

    @staticmethod
    def _message_in_dialog(message, dialog_id) -> bool:
        if message is None:
            return False
        if dialog_id is None:
            return True
        try:
            found = java_int(message.getDialogId())
        except Exception:
            return False
        return not found or found == dialog_id

    def _find_message_object(self, account, message_id, dialog_id=None):
        try:
            fragment = get_last_fragment()
            view = fragment.getChatActivityEnterView() if fragment is not None else None
            editing = view.getEditingMessageObject() if view is not None else None
            if editing is not None and java_int(editing.getId()) == message_id and self._message_in_dialog(editing, dialog_id):
                return editing
        except Exception:
            pass
        try:
            controller = get_messages_controller(int(account))
            found = controller.dialogMessagesByIds.get(message_id)
            return found if self._message_in_dialog(found, dialog_id) else None
        except Exception:
            return None

    def _edit_is_caption(self, request, account) -> Optional[bool]:
        try:
            if getattr(request, "media", None) is not None:
                return True
        except Exception:
            pass
        message_id = java_int(getattr(request, "id", None))
        dialog_id = self._dialog_id_from_params(request, account)
        message = self._find_message_object(account, message_id, dialog_id) if message_id is not None else None
        if message is None:
            return None
        try:
            return not bool(message.isMediaEmpty())
        except Exception:
            return None

    def _on_edit_request(self, param, request):
        runtime = self.runtime_manager.runtime
        if runtime is None or self._edit_request_seen(request):
            return
        try:
            flags = int(request.flags)
            text = as_text(request.message) if flags & self.EDIT_FLAG_MESSAGE else ""
        except Exception as exc:
            self.log(f"Prefixfy edit: unknown request layout: {exc}")
            return
        is_article = False
        if not text.strip():
            try:
                is_article = bool(FEATURES.on("articles") and article_blocks(request))
            except Exception:
                is_article = False
            if not is_article:
                return
        try:
            account = int(param.thisObject.currentAccount)
        except Exception:
            account = get_hook_account()
            if account is None:
                account = get_selected_account()
        dialog_id = self._dialog_id_from_params(request, account)

        if not self.remote.allows():
            return
        runtime = self._base_runtime(account) or runtime
        runtime = self._runtime_for_chat(runtime, dialog_id, account)
        settings = runtime.settings
        if not settings.process_edit:
            return
        if not is_article:
            try:
                is_article = bool(FEATURES.on("articles") and article_blocks(request))
            except Exception:
                is_article = False
        if is_article:
            if not settings.process_edit_article:
                return
            if not self._chat_type_allowed(account, dialog_id, settings.chat_type_rules) or not settings.is_chat_allowed(dialog_id):
                return
            if settings.skip_once_on_edit and self._skip_once is not None and self._consume_skip_once(dialog_id):
                return
            runtime, rotation_next = self._runtime_for_message(runtime, account, dialog_id, text)
            if self._decorate_article(runtime, request, account, editing=True) is not None:
                self._advance_rotation(rotation_next)
            return
        caption = self._edit_is_caption(request, account)
        if caption is None:
            if not (settings.process_edit_message or settings.process_edit_media):
                return
        elif not (settings.process_edit_media if caption else settings.process_edit_message):
            return
        if not self._chat_type_allowed(account, dialog_id, settings.chat_type_rules) or not settings.is_chat_allowed(dialog_id):
            return
        if caption:
            runtime = runtime.for_caption()
            settings = runtime.settings
        if self._edit_restore_mask_emoji(runtime, account, request, text):
            return
        if runtime.pipeline.ignores(text) or self._edit_is_decorated(runtime, text):
            return
        if settings.skip_once_on_edit and self._skip_once is not None and self._consume_skip_once(dialog_id):
            return
        runtime, rotation_next = self._runtime_for_message(runtime, account, dialog_id, text)
        holder = types.SimpleNamespace(entities=getattr(request, "entities", None))
        transformed = self._decorate_text(runtime, account, holder, text, bool(caption), rotation_next)
        if transformed is None:
            return
        request.message = transformed
        if holder.entities is None:
            return
        try:
            request.entities = holder.entities
            if int(holder.entities.size()) > 0:
                request.flags = int(request.flags) | self.EDIT_FLAG_ENTITIES
        except Exception as exc:
            self.log(f"Prefixfy edit: entities were not applied: {exc}")
