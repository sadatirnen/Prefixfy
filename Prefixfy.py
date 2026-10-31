import base64
import hashlib
import hmac
import json
import mimetypes
import os
import random
import re
import shutil
import threading
import time
import types
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
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from base_plugin import BasePlugin, HookResult, HookStrategy, MenuItemData, MenuItemType, MethodHook
from ui.settings import Header, Input, Selector, Switch, Text
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
    get_last_fragment,
    get_selected_account,
    get_user_config,
    run_on_queue,
    send_document,
    send_photo,
    send_video,
)
from hook_utils import find_class

try:
    from client_utils import send_message as _send_message
except ImportError:
    _send_message = None

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
__description__ = (
    "Prefixfy — стильное оформление исходящих сообщений: разделители между словами, маска-шаблон с гиперссылкой, 35+ тегов, 30 стилей текста (L33T, vaporwave, готика, морзе, пузыри, индекс, подчёркивания и др.), маски для отдельных чатов с ротацией, правилами по содержимому и тегами [date], [time], [hour], [daypart], [week], [monthname], [chattype], [dice], [chat], [username], [count] и др., гибкие и regex-исключения, оформление при редактировании сообщений (отдельно для текста и подписей), цитата в маске, расписание по датам и времени суток и вложение медиа. Premium Emoji в маске и разделителях. Конфигурации с импортом и экспортом, интерфейс на 9 языках."
)
__author__ = "@Prefixfy"
__version__ = "30.8.0"
__icon__ = "http_Prefixfy_by_fStikBot/0"
__app_version__ = ">=12.10.6"
__sdk_version__ = ">=1.4.5.0"


REPO_URL = "https://github.com/sadatirnen/Prefixfy"
UPDATE_BASE_URL = "https://raw.githubusercontent.com/sadatirnen/Prefixfy/main/"
MANIFEST_FILE = "version.json"
MANIFEST_FORMAT = 1
MANIFEST_DOMAIN = b"Prefixfy-manifest-v1\n"
FLAGS_FILE = "flags.json"
FLAGS_FORMAT = 1
FLAGS_DOMAIN = b"Prefixfy-flags-v1\n"
FLAGS_CACHE_FILE = "Prefixfy_flags.json"
FLAGS_MAX_COUNT = 128
FLAGS_MAX_ACCOUNTS = 1024
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
UPDATE_PUBLIC_KEYS: Tuple[str, ...] = (
    "MIIBojANBgkqhkiG9w0BAQEFAAOCAY8AMIIBigKCAYEAnCpVgdegnDqZoaOi5H5EOpHiwY8jhprNdIT3jGVauC0Nijz2L/iauWaVxnEOwDT2tqp1tJQ6CrdQxOS/PKV/7QLtGtAseKdpo/4tZjHgx2N9TAPMVb+zK3oWYk+0+OcLFIUoczCa1aZuwaScBqQchmgTj4sQwIbhWDhquE2EtyiF1+6S6GCgV5KyJrqylt2pAcif5z3ixUV27MPzaPbQmuyU+3amsIXDxGcdTFwlHMg/ThFVz77bwV5fkfaNdJrZGDp3+FKSIfjN68v2scL6O9oYHhkDg4AEPUYQkJmNTMnqc0ABFSW9MGuGsMTa0MKNDMaBY5iP2aQmfzLddorBP4ovfOZRzZguFVltFGd44xVOE1w5ceL1WVH+pW+4HX0Ck5FWnHbttaQiLoxXuiIK+F927LLM0yCmKLZC9tcIfMdBXgcaHp1ZaKGOIVvRs8SRaVnQ2z51v3NtjHbakGKwcXit2JlgyKvrHPG2AQj8ci7tApB6BWYffsNkFM4bCBIlAgMBAAE=",
)
REMOTE_CHECK_INTERVAL = 15 * 60
REMOTE_RETRY_INTERVAL = 60
REMOTE_MANUAL_COOLDOWN = 10.0
REMOTE_TIMEOUT = 10
REMOTE_TOTAL_TIMEOUT = 20
REMOTE_MAX_AGE = 60 * 60
REMOTE_MAX_BYTES = 64 * 1024
MASK_PLACEHOLDER = "[text]"
DEFAULT_SEPARATORS = "•, ·, —, ~, |"
LANGUAGE_MODES = (None, "ru", "en", "ja", "ko", "ar", "fr", "pl", "de", "uk")
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
REGEX_TEXT_LIMIT = 4096
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
    r"hour|minute|second|ampm|daypart|timestamp|tz|chattype|username|count|dice|random_emoji|emoji|reply|chatcount|battery|moon|line|(?:since|until):\d{4}-\d{2}-\d{2})\]",
    re.IGNORECASE,
)
_TAG_UNSAFE_RE = re.compile(r"[\[\]*_~|`\\\uE000-\uF8FF\s]+")
WEEKDAY_NAMES = {
    "ru": ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"),
    "en": ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
    "ja": ("月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"),
    "ko": ("월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"),
    "ar": ("الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"),
    "fr": ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"),
    "pl": ("poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"),
    "de": ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"),
    "uk": ("Понеділок", "Вівторок", "Середа", "Четвер", "Пʼятниця", "Субота", "Неділя"),
}

MONTH_NAMES = {
    "ru": ("Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"),
    "en": ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"),
    "ja": tuple(f"{n}月" for n in range(1, 13)),
    "ko": tuple(f"{n}월" for n in range(1, 13)),
    "ar": ("يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"),
    "fr": ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"),
    "pl": ("styczeń", "luty", "marzec", "kwiecień", "maj", "czerwiec", "lipiec", "sierpień", "wrzesień", "październik", "listopad", "grudzień"),
    "de": ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"),
    "uk": ("Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"),
}
DAYPART_NAMES = {
    "ru": ("Утро", "День", "Вечер", "Ночь"),
    "en": ("Morning", "Afternoon", "Evening", "Night"),
    "ja": ("朝", "昼", "夕方", "夜"),
    "ko": ("아침", "낮", "저녁", "밤"),
    "ar": ("الصباح", "النهار", "المساء", "الليل"),
    "fr": ("Matin", "Après-midi", "Soir", "Nuit"),
    "pl": ("Rano", "Dzień", "Wieczór", "Noc"),
    "de": ("Morgen", "Tag", "Abend", "Nacht"),
    "uk": ("Ранок", "День", "Вечір", "Ніч"),
}
DAYPART_BOUNDS = ((5 * 60, 12 * 60), (12 * 60, 17 * 60), (17 * 60, 23 * 60), (23 * 60, 5 * 60))
DAYPART_ALIASES = {
    0: ("morning", "утро", "ранок", "matin", "rano", "morgen", "朝", "아침", "الصباح", "صباح"),
    1: ("afternoon", "day", "день", "dzień", "tag", "après-midi", "昼", "낮", "النهار", "ظهر"),
    2: ("evening", "вечер", "вечір", "soir", "wieczór", "abend", "夕方", "저녁", "المساء", "مساء"),
    3: ("night", "ночь", "ніч", "nuit", "noc", "nacht", "夜", "밤", "الليل", "ليل"),
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
    "process_edit": False,
    "process_edit_message": True,
    "process_edit_media": True,
    "skip_once_on_edit": True,
    "mask": MASK_PLACEHOLDER,
    "markdown_enabled": True,
    "markdown_style": 0,
    "separator_enabled": False,
    "custom_emojis": DEFAULT_SEPARATORS,
    "emoji_count": 1,
    "exceptions": "",
    "ignore_special": True,
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
}

TRANSIENT_SETTING_DEFAULTS = {
    "capture_custom_emoji": False,
}

MEDIA_EXTENSIONS = frozenset({
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic", ".heif", ".avif",
    ".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v", ".3gp", ".mpeg", ".mpg",
})


class LocalizationManager:
    LANGUAGE_ITEMS = {
        "ru": ["Русский", "Английский", "Японский", "Корейский", "Арабский", "Французский", "Польский", "Немецкий", "Украинский"],
        "en": ["Russian", "English", "Japanese", "Korean", "Arabic", "French", "Polish", "German", "Ukrainian"],
        "ja": ["ロシア語", "英語", "日本語", "韓国語", "アラビア語", "フランス語", "ポーランド語", "ドイツ語", "ウクライナ語"],
        "ko": ["러시아어", "영어", "일본어", "한국어", "아랍어", "프랑스어", "폴란드어", "독일어", "우크라이나어"],
        "ar": ["الروسية", "الإنجليزية", "اليابانية", "الكورية", "العربية", "الفرنسية", "البولندية", "الألمانية", "الأوكرانية"],
        "fr": ["Russe", "Anglais", "Japonais", "Coréen", "Arabe", "Français", "Polonais", "Allemand", "Ukrainien"],
        "pl": ["Rosyjski", "Angielski", "Japoński", "Koreański", "Arabski", "Francuski", "Polski", "Niemiecki", "Ukraiński"],
        "de": ["Russisch", "Englisch", "Japanisch", "Koreanisch", "Arabisch", "Französisch", "Polnisch", "Deutsch", "Ukrainisch"],
        "uk": ["Російська", "Англійська", "Японська", "Корейська", "Арабська", "Французька", "Польська", "Німецька", "Українська"],
    }

    STRINGS = {
        "ru": {
            "enable_plugin": "Включить плагин",
            "enable_plugin_subtext": "Вкл: везде, кроме выбранных чатов. Выкл: только в выбранных.",
            "language": "Язык",
            "update_required": "Требуется обновление",
            "update_required_subtext": "Установите Prefixfy {version} (официальная сборка). Пока плагин не оформляет сообщения.",
            "verify_required": "Проверка не пройдена",
            "verify_required_subtext": "Не удалось подтвердить подлинность сборки Prefixfy. Пока плагин не оформляет сообщения; проверьте подключение к интернету.",
            "account_blocked": "Доступ запрещён",
            "account_blocked_subtext": "Один из аккаунтов на этом устройстве внесён в чёрный список Prefixfy. Плагин не работает.",
            "section_scope": "Где работает",
            "plugin_language": "Язык плагина",
            "language_auto": "Автоопределение языка",
            "language_auto_subtext": "Использовать язык интерфейса Telegram. Выключите, чтобы выбрать язык вручную.",
            "message": "Сообщение",
            "message_subtext": "Использовать плагин для обычных текстовых сообщений.",
            "media": "Медиа",
            "media_subtext": "Использовать плагин для подписей к медиа.",
            "edit_message": "Редактирование сообщений",
            "edit_message_subtext": "Оформлять сообщения при редактировании. Уже оформленный текст не трогается.",
            "mask": "Маска",
            "mask_text": "Текст маски",
            "text_style": "Стиль текста",
            "skip_once_expired": "Пропуск оформления истёк: следующее сообщение будет оформлено",
            "empty_means_default": "Чтобы вернуть значение по умолчанию, очистите поле и нажмите «Сохранить».",
            "markdown_style": "Стиль Markdown",
            "markdown_style_subtext": "Маркеры в маске или оформление всей маски",
            "markdown_style_pick": "Стиль",
            "md_manual": "Маркеры вручную",
            "md_bold": "Вся маска: жирный",
            "md_italic": "Вся маска: курсив",
            "md_strike": "Вся маска: зачёркнутый",
            "md_spoiler": "Вся маска: спойлер",
            "md_mono": "Вся маска: моно",
            "chat_config_menu": "Конфигурация для этого чата",
            "chat_config_auto": "Основная (и расписание)",
            "chat_config_saved": "Конфигурация чата сохранена",
            "chat_config_reset": "Чат использует основную конфигурацию",
            "schedule": "Расписание конфигураций",
            "schedule_empty": "Не задано",
            "schedule_count": "Правил: {n}",
            "schedule_message": "Одно правило в строке: [дата] [ЧЧ:ММ-ЧЧ:ММ] [дни] = название конфигурации.\nДата: ГГГГ-ММ-ДД, ДД.ММ.ГГГГ или ДД.ММ (каждый год); диапазон через «..». Без времени — весь день. Дни: пн-пт, сб,вс или mon-fri; без дней — каждый день. Правила с датой важнее правил по дням недели, из остальных побеждает первое подходящее. Чат со своей конфигурацией расписание не меняет. Вместо времени можно указать часть суток: утро (05–12), день (12–17), вечер (17–23), ночь (23–05) или диапазон «утро-вечер».",
            "schedule_hint": "22:00-07:00 = Ночная\n09:00-18:00 пн-пт = Рабочая\n31.12 = Праздничная\n2026-12-28..2027-01-10 = Отпуск\nутро пн-пт = Рабочая\nночь = Ночная",
            "schedule_saved": "Расписание сохранено",
            "schedule_error": "Строка {n}: {reason}",
            "schedule_err_format": "ожидается «[дата] [ЧЧ:ММ-ЧЧ:ММ] [дни] = конфигурация»",
            "schedule_err_time": "неверное время",
            "schedule_err_days": "неверные дни",
            "schedule_err_config": "нет конфигурации «{name}»",
            "schedule_err_limit": "не больше {n} правил",
            "skip_once_menu": "Пропустить оформление один раз",
            "skip_once_on": "Следующее сообщение уйдёт без оформления",
            "skip_once_off": "Пропуск отменён",
            "random_style": "Случайный стиль",
            "random_style_subtext": "Для каждого сообщения выбирается случайный стиль (кроме перевёрнутого текста).",
            "mask_rotation": "Ротация масок",
            "mask_rotation_subtext": "Вместо основной маски берутся маски из списка. Маска чата важнее.",
            "masks_list": "Список масок",
            "masks_list_count": "Масок: {n}",
            "masks_list_empty": "По одной маске в строке",
            "masks_list_hint": "По одной маске в строке, в каждой ровно один [text].",
            "masks_list_invalid": "В каждой маске должен быть ровно один [text]",
            "masks_list_limit": "Не больше {n} масок",
            "mask_tags_hint": "Теги: [date], [time], [datetime], [chat], [id], [weekday], [year], [month], [day], [username], [count], [random_emoji], [hour], [minute], [second], [time12], [ampm], [daypart], [week], [yearday], [monthname], [weekday_short], [year_short], [timestamp], [tz], [chattype], [dice].",
            "mask_rotation_mode": "Порядок ротации",
            "rotation_random": "Случайная",
            "rotation_sequential": "По кругу",
            "regex_exceptions": "Regex-исключения",
            "regex_exceptions_hint": "По одному регулярному выражению в строке. Сообщение, подходящее под любое из них, остаётся без оформления.",
            "regex_exceptions_count": "Правил: {n}",
            "regex_exceptions_empty": "Для продвинутых пользователей",
            "regex_invalid": "Некорректное выражение: {error}",
            "regex_limit": "Не больше {n} выражений, до {m} символов каждое",
            "chat_types": "Типы чатов",
            "chat_types_hint": "Оформление работает только в выбранных типах чатов.",
            "chat_types_all": "Все чаты",
            "chat_types_none": "Выберите хотя бы один тип",
            "chat_type_private": "Личные",
            "chat_type_group": "Группы",
            "chat_type_channel": "Каналы",
            "separator": "Разделитель",
            "enable_separator": "Включить разделитель",
            "enable_separator_subtext": "Добавлять собственные разделители между словами.",
            "separator_set": "Набор разделителей",
            "separator_count": "Количество разделителей между словами",
            "separator_count_subtext": "Нажмите, чтобы изменить.",
            "exceptions": "Исключения",
            "ignore_emoji_only": "Игнорировать сообщения только из эмодзи",
            "ignore_emoji_only_subtext": "Не изменять сообщения, состоящие только из одного или нескольких эмодзи.",
            "exceptions_hint": "Сообщения, которые начинаются или заканчиваются указанным значением, не изменяются. Каждое значение — с новой строки.",
            "ignore_special": "Не трогать код, команды, упоминания и ссылки",
            "ignore_special_subtext": "Команды, @упоминания, ссылки и код остаются как есть. В таких сообщениях Markdown маски не применяется.",
            "chat_menu": "Добавить/удалить чат в/из списка исключений",
            "chat_added": "Чат добавлен в список исключений",
            "chat_removed": "Чат удалён из списка исключений",
            "mask_editor_title": "Настройка маски",
            "mask_editor_hint": "Введите маску. Используйте [text] для текста сообщения или [text: ссылка], чтобы сделать его гиперссылкой.",
            "custom_separator_title": "Своя",
            "custom_separator_message": "Введите разделители через запятую, например:\n•, ·, —, ~, |",
            "save": "Сохранить",
            "delete": "Удалить",
            "cancel": "Отмена",
            "capture_custom_emoji": "Захват Premium Emoji",
            "capture_enabled": "Захват Premium Emoji включён: отправьте сообщение с Premium Emoji",
            "capture_disabled": "Захват Premium Emoji выключен",
            "custom_emoji_hint": "Premium Emoji: маркер (id|🙂), где 🙂 — обычный эмодзи для тех, у кого нет Premium. Получить маркер можно через пункт «Захват Premium Emoji» в меню чата.",
            "mask_invalid": "Маска должна содержать ровно один [text]",
            "mask_too_long": "Маска слишком длинная: не больше {n} символов",
            "mask_preview_sample": "Пример сообщения",
            "mask_preview_invalid": "Маска повреждена: нужен ровно один [text]",
            "separator_preview_words": "Пример текста для превью",
            "exceptions_count": "Исключений: {n}, чатов: {m}",
            "configuration_import_cancelled": "Импорт отменён",
            "import_configuration": "Импортировать",
            "export_configuration": "Экспортировать",
            "reset_configuration": "Восстановить значения по умолчанию",
            "reset_to_plugin_defaults": "Игнорировать импортированные значения: вернуть настройки по умолчанию плагина",
            "reset_to_plugin_defaults_unavailable": "Недоступно: конфигурация создана плагином, поэтому сброс возвращает её к состоянию на момент создания.",
            "configurations": "Конфигурации",
            "active_configuration": "Активная конфигурация",
            "add_configuration": "Создать новую конфигурацию",
            "add_configuration_subtext": "Отдельный набор настроек, который сразу станет активным.",
            "configuration_name_hint": "Название конфигурации",
            "new_configuration_source_title": "Настройки новой конфигурации",
            "new_configuration_source_message": "Что взять за основу? Если ничего не отмечено, будут настройки по умолчанию.",
            "new_configuration_copy_current": "Скопировать настройки текущей конфигурации",
            "create": "Создать",
            "delete_configuration": "Удалить конфигурацию",
            "delete_configuration_confirm": "Удалить конфигурацию «{name}»?",
            "no_inactive_configurations": "Нет неактивных конфигураций для удаления",
            "imported_configuration": "Импортированная конфигурация",
            "rename_configuration": "Переименовать конфигурацию",
            "rename_configuration_subtext": "Изменить название текущей конфигурации.",
            "configuration_name_invalid": "Введите уникальное название конфигурации.",
            "configuration_name_taken": "Конфигурация с таким названием уже существует.",
            "configuration_deleted": "Удалено конфигураций: {n}",
            "delete_configurations": "Удалить конфигурации",
            "delete_configurations_subtext": "Удалить неактивные конфигурации. Активная останется.",
            "delete_configurations_select": "Выберите неактивные конфигурации, которые нужно удалить.",
            "import_new_configuration_name": "Название новой конфигурации",
            "select_configuration": "Выберите конфигурацию",
            "select_configuration_subtext": "Можно выбрать любые части конфигурации — от одной до шести.",
            "config_mask": "Маска",
            "config_separator": "Разделители",
            "config_exceptions": "Исключения и чаты",
            "config_language": "Выбранный язык",
            "config_media": "Медиа",
            "media_attachment": "Медиа",
            "enable_media_attachment": "Включить медиа",
            "enable_media_attachment_subtext": "Автоматически прикладывать импортированный файл к отправкам.",
            "media_file": "Выбранный файл",
            "media_file_none": "Файл не выбран",
            "import_media": "Импортировать медиа",
            "delete_media": "Удалить медиа",
            "delete_media_subtext": "Удалить импортированный файл из Prefixfy.",
            "media_imported": "Медиа импортировано",
            "media_deleted": "Медиа удалено",
            "media_import_failed": "Не удалось импортировать медиа",
            "media_delete_failed": "Не удалось удалить медиа",
            "apply": "Применить",
            "configuration_imported": "Конфигурация импортирована",
            "configuration_import_failed": "Не удалось импортировать конфигурацию",
            "configuration_save_failed": "Не удалось сохранить текущую конфигурацию",
            "configuration_exported": "Конфигурация экспортирована",
            "configuration_export_failed": "Не удалось экспортировать конфигурацию",
            "configuration_export_destination_title": "Куда экспортировать?",
            "configuration_export_to_saved": "В Избранные активного аккаунта",
            "configuration_export_to_device": "В память устройства",
            "configuration_restored": "Выбранные значения восстановлены",
            "configuration_nothing_selected": "Выберите хотя бы одну часть конфигурации",
            "config_found_title": "Найдена конфигурация",
            "config_found_contains": "Содержит",
            "config_import_as_new": "Импортировать как новую конфигурацию",
            "config_found_import": "Импортировать",
            "config_file_open_failed": "Не удалось открыть файл конфигурации",
            "invalid_configuration": "Файл не содержит выбранной конфигурации или имеет неверный формат.",
            "default_configuration_name": "Конфигурация по умолчанию",
            "configuration_n": "Конфигурация {n}",
            "operation_failed": "Не удалось выполнить действие",
            "text_style_subtext": "Меняет только текст сообщения. Fancy, Bold, Gothic и Circled — только латиница; L33T затрагивает и кириллицу.",
            "enable_text_style": "Включить стиль текста",
            "configuration_short": "Выбрать части конфигурации",
            "edit_text_toggle": "Правка текста",
            "edit_text_toggle_subtext": "Оформлять обычные текстовые сообщения при редактировании.",
            "edit_media_toggle": "Правка подписей",
            "edit_media_toggle_subtext": "Оформлять подписи к медиа при редактировании.",
            "skip_once_on_edit": "«Пропустить один раз» при правке",
            "skip_once_on_edit_subtext": "Если пропуск включён, следующая правка в этом чате останется без оформления.",
            "conditional_masks": "Маски по содержимому",
            "conditional_masks_hint": "По одному правилу в строке: регулярное выражение => маска. Если текст подходит под выражение, берётся эта маска; побеждает первая подходящая строка. В каждой маске ровно один [text].",
            "conditional_masks_count": "Правил: {n}",
            "conditional_masks_empty": "Если в тексте есть…",
            "conditional_masks_format": "Строка {n}: ожидается «выражение => маска»",
            "md_quote": "Вся маска: цитата",
            "config_schedule": "Привязки чатов и расписание",
            "schedule_err_date": "неверная дата",
        },
        "en": {
            "enable_plugin": "Enable plugin",
            "enable_plugin_subtext": "On: everywhere except the listed chats. Off: only in the listed chats.",
            "language": "Language",
            "update_required": "Update required",
            "update_required_subtext": "Install Prefixfy {version} (official build). Until then the plugin won’t format messages.",
            "verify_required": "Verification failed",
            "verify_required_subtext": "Couldn’t verify this Prefixfy build. Until then the plugin won’t format messages; check your internet connection.",
            "account_blocked": "Access denied",
            "account_blocked_subtext": "One of the accounts on this device is on the Prefixfy blacklist. The plugin is disabled.",
            "section_scope": "Where it works",
            "plugin_language": "Plugin language",
            "language_auto": "Detect language automatically",
            "language_auto_subtext": "Use the Telegram interface language. Turn off to choose a language manually.",
            "message": "Message",
            "message_subtext": "Use the plugin for regular text messages.",
            "media": "Media",
            "media_subtext": "Use the plugin for media captions.",
            "edit_message": "Message editing",
            "edit_message_subtext": "Style messages when you edit them. Text that already has the mask is left as is.",
            "mask": "Mask",
            "mask_text": "Mask text",
            "text_style": "Text style",
            "skip_once_expired": "Skip expired: the next message will be styled",
            "empty_means_default": "To restore the default, clear the field and tap “Save”.",
            "markdown_style": "Markdown style",
            "markdown_style_subtext": "Markers in the mask or formatting for the whole mask",
            "markdown_style_pick": "Style",
            "md_manual": "Manual markers",
            "md_bold": "Whole mask: bold",
            "md_italic": "Whole mask: italic",
            "md_strike": "Whole mask: strikethrough",
            "md_spoiler": "Whole mask: spoiler",
            "md_mono": "Whole mask: monospace",
            "chat_config_menu": "Configuration for this chat",
            "chat_config_auto": "Main (and schedule)",
            "chat_config_saved": "Chat configuration saved",
            "chat_config_reset": "This chat uses the main configuration",
            "schedule": "Configuration schedule",
            "schedule_empty": "Not set",
            "schedule_count": "Rules: {n}",
            "schedule_message": "One rule per line: [date] [HH:MM-HH:MM] [days] = configuration name.\nDate: YYYY-MM-DD, DD.MM.YYYY or DD.MM (every year); ranges use “..”. No time means all day. Days: mon-fri, sat,sun or пн-пт; no days means every day. Rules with a date beat weekday rules; among the rest the first match wins. A chat with its own configuration ignores the schedule. Instead of a time you can use a part of the day: morning (05–12), afternoon/day (12–17), evening (17–23), night (23–05) or a range like “morning-evening”.",
            "schedule_hint": "22:00-07:00 = Night\n09:00-18:00 mon-fri = Work\n31.12 = Holiday\n2026-12-28..2027-01-10 = Vacation\nmorning mon-fri = Work\nnight = Night",
            "schedule_saved": "Schedule saved",
            "schedule_error": "Line {n}: {reason}",
            "schedule_err_format": "expected “[date] [HH:MM-HH:MM] [days] = configuration”",
            "schedule_err_time": "invalid time",
            "schedule_err_days": "invalid days",
            "schedule_err_config": "no configuration “{name}”",
            "schedule_err_limit": "no more than {n} rules",
            "skip_once_menu": "Skip styling once",
            "skip_once_on": "The next message will be sent without styling",
            "skip_once_off": "Skip cancelled",
            "random_style": "Random style",
            "random_style_subtext": "Picks a random style for every message (except upside-down text).",
            "mask_rotation": "Mask rotation",
            "mask_rotation_subtext": "Uses the masks from the list instead of the main one. A chat mask takes priority.",
            "masks_list": "Mask list",
            "masks_list_count": "Masks: {n}",
            "masks_list_empty": "One mask per line",
            "masks_list_hint": "One mask per line, each with exactly one [text].",
            "masks_list_invalid": "Each mask needs exactly one [text]",
            "masks_list_limit": "At most {n} masks",
            "mask_tags_hint": "Tags: [date], [time], [datetime], [chat], [id], [weekday], [year], [month], [day], [username], [count], [random_emoji], [hour], [minute], [second], [time12], [ampm], [daypart], [week], [yearday], [monthname], [weekday_short], [year_short], [timestamp], [tz], [chattype], [dice].",
            "mask_rotation_mode": "Rotation order",
            "rotation_random": "Random",
            "rotation_sequential": "In turn",
            "regex_exceptions": "Regex exceptions",
            "regex_exceptions_hint": "One regular expression per line. A message matching any of them is left unstyled.",
            "regex_exceptions_count": "Rules: {n}",
            "regex_exceptions_empty": "For advanced users",
            "regex_invalid": "Invalid expression: {error}",
            "regex_limit": "Up to {n} expressions, {m} characters each",
            "chat_types": "Chat types",
            "chat_types_hint": "Styling works only in the selected chat types.",
            "chat_types_all": "All chats",
            "chat_types_none": "Choose at least one type",
            "chat_type_private": "Private chats",
            "chat_type_group": "Groups",
            "chat_type_channel": "Channels",
            "separator": "Separator",
            "enable_separator": "Enable separator",
            "enable_separator_subtext": "Add your custom separators between words.",
            "separator_set": "Separator set",
            "separator_count": "Separators between words",
            "separator_count_subtext": "Tap to change.",
            "exceptions": "Exceptions",
            "ignore_emoji_only": "Ignore emoji-only messages",
            "ignore_emoji_only_subtext": "Do not modify messages consisting only of one or more emojis.",
            "exceptions_hint": "Messages that start or end with the specified value are not changed. Enter each value on a new line.",
            "ignore_special": "Skip code, commands, mentions and links",
            "ignore_special_subtext": "Commands, @mentions, links and code stay as they are. Mask Markdown is not applied to such messages.",
            "chat_menu": "Add/remove chat to/from the exception list",
            "chat_added": "Chat added to the exception list",
            "chat_removed": "Chat removed from the exception list",
            "mask_editor_title": "Mask settings",
            "mask_editor_hint": "Enter a mask. Use [text] for the message text, or [text: link] to turn it into a hyperlink.",
            "custom_separator_title": "Custom",
            "custom_separator_message": "Enter separators separated by commas, for example:\n•, ·, —, ~, |",
            "save": "Save",
            "delete": "Delete",
            "cancel": "Cancel",
            "capture_custom_emoji": "Capture Premium Emoji",
            "capture_enabled": "Premium Emoji capture is on: send a message with Premium Emoji",
            "capture_disabled": "Premium Emoji capture is off",
            "custom_emoji_hint": "Premium Emoji: the marker (id|🙂), where 🙂 is a regular emoji shown to people without Premium. Get a marker with “Capture Premium Emoji” in the chat menu.",
            "mask_invalid": "The mask must contain exactly one [text]",
            "mask_too_long": "The mask is too long: {n} characters at most",
            "mask_preview_sample": "Sample message",
            "mask_preview_invalid": "Mask is invalid: exactly one [text] is required",
            "separator_preview_words": "Sample text for preview",
            "exceptions_count": "Exceptions: {n}, chats: {m}",
            "configuration_import_cancelled": "Import cancelled",
            "import_configuration": "Import",
            "export_configuration": "Export",
            "reset_configuration": "Restore defaults",
            "reset_to_plugin_defaults": "Ignore imported values: restore the plugin's defaults",
            "reset_to_plugin_defaults_unavailable": "Unavailable: this configuration was created by the plugin, so a reset returns it to the state it was created in.",
            "configurations": "Configurations",
            "active_configuration": "Active configuration",
            "add_configuration": "Create new configuration",
            "add_configuration_subtext": "A separate set of settings that becomes active right away.",
            "configuration_name_hint": "Configuration name",
            "new_configuration_source_title": "New configuration settings",
            "new_configuration_source_message": "What should it start from? If nothing is checked, default settings are used.",
            "new_configuration_copy_current": "Copy settings of the current configuration",
            "create": "Create",
            "delete_configuration": "Delete configuration",
            "delete_configuration_confirm": "Delete configuration “{name}”?",
            "no_inactive_configurations": "No inactive configurations to delete",
            "imported_configuration": "Imported configuration",
            "rename_configuration": "Rename configuration",
            "rename_configuration_subtext": "Change the name of the current configuration.",
            "configuration_name_invalid": "Enter a unique configuration name.",
            "configuration_name_taken": "A configuration with this name already exists.",
            "configuration_deleted": "Configurations deleted: {n}",
            "delete_configurations": "Delete configurations",
            "delete_configurations_subtext": "Delete inactive configurations. The active one stays.",
            "delete_configurations_select": "Select the inactive configurations to delete.",
            "import_new_configuration_name": "New configuration name",
            "select_configuration": "Select configuration",
            "select_configuration_subtext": "You can select anywhere from one to all six parts.",
            "config_mask": "Mask",
            "config_separator": "Separators",
            "config_exceptions": "Exceptions and chats",
            "config_language": "Selected language",
            "config_media": "Media",
            "media_attachment": "Media",
            "enable_media_attachment": "Enable media",
            "enable_media_attachment_subtext": "Automatically attach the imported file to outgoing messages.",
            "media_file": "Selected file",
            "media_file_none": "No file selected",
            "import_media": "Import media",
            "delete_media": "Delete media",
            "delete_media_subtext": "Delete the imported file from Prefixfy.",
            "media_imported": "Media imported",
            "media_deleted": "Media deleted",
            "media_import_failed": "Could not import media",
            "media_delete_failed": "Could not delete media",
            "apply": "Apply",
            "configuration_imported": "Configuration imported",
            "configuration_import_failed": "Could not import configuration",
            "configuration_save_failed": "Could not save the current configuration",
            "configuration_exported": "Configuration exported",
            "configuration_export_failed": "Could not export configuration",
            "configuration_export_destination_title": "Where to export?",
            "configuration_export_to_saved": "Active account's Saved Messages",
            "configuration_export_to_device": "Device storage",
            "configuration_restored": "Selected values restored",
            "configuration_nothing_selected": "Select at least one configuration part",
            "config_found_title": "Configuration found",
            "config_found_contains": "Contains",
            "config_import_as_new": "Import as a new configuration",
            "config_found_import": "Import",
            "config_file_open_failed": "Could not open configuration file",
            "invalid_configuration": "The file does not contain the selected configuration or has an invalid format.",
            "default_configuration_name": "Default configuration",
            "configuration_n": "Configuration {n}",
            "operation_failed": "Action failed",
            "text_style_subtext": "Changes only the message text. Fancy, Bold, Gothic and Circled need Latin letters; L33T also covers Cyrillic.",
            "enable_text_style": "Enable text style",
            "configuration_short": "Choose configuration parts",
            "edit_text_toggle": "Edit text messages",
            "edit_text_toggle_subtext": "Style regular text messages when you edit them.",
            "edit_media_toggle": "Edit captions",
            "edit_media_toggle_subtext": "Style media captions when you edit them.",
            "skip_once_on_edit": "“Skip once” when editing",
            "skip_once_on_edit_subtext": "If a skip is armed, the next edit in this chat stays unstyled.",
            "conditional_masks": "Content-based masks",
            "conditional_masks_hint": "One rule per line: regular expression => mask. If the text matches the expression, that mask is used; the first matching line wins. Each mask needs exactly one [text].",
            "conditional_masks_count": "Rules: {n}",
            "conditional_masks_empty": "If the text contains…",
            "conditional_masks_format": "Line {n}: expected “expression => mask”",
            "md_quote": "Whole mask: quote",
            "config_schedule": "Chat bindings and schedule",
            "schedule_err_date": "invalid date",
        },
        "ja": {
            "enable_plugin": "プラグインを有効にする",
            "enable_plugin_subtext": "オン: リスト以外のすべてのチャット。オフ: リストのチャットのみ。",
            "language": "言語",
            "update_required": "アップデートが必要です",
            "update_required_subtext": "Prefixfy {version}（公式ビルド）をインストールしてください。それまでメッセージの装飾は行われません。",
            "verify_required": "検証に失敗しました",
            "verify_required_subtext": "このPrefixfyビルドを検証できませんでした。それまでメッセージの装飾は行われません。インターネット接続を確認してください。",
            "account_blocked": "アクセスが拒否されました",
            "account_blocked_subtext": "この端末のアカウントの1つがPrefixfyのブラックリストに登録されています。プラグインは無効です。",
            "section_scope": "適用範囲",
            "plugin_language": "プラグインの言語",
            "language_auto": "言語を自動検出",
            "language_auto_subtext": "Telegramのインターフェース言語を使用します。オフにすると手動で選択できます。",
            "message": "メッセージ",
            "message_subtext": "通常のテキストメッセージにプラグインを使用します。",
            "media": "メディア",
            "media_subtext": "メディアのキャプションにプラグインを使用します。",
            "edit_message": "メッセージの編集",
            "edit_message_subtext": "編集時にもメッセージを装飾します。すでにマスクが付いているテキストは変更しません。",
            "mask": "マスク",
            "mask_text": "マスクテキスト",
            "text_style": "テキストスタイル",
            "skip_once_expired": "スキップの期限が切れました。次のメッセージは装飾されます",
            "empty_means_default": "デフォルトに戻すには、入力欄を空にして「保存」を押してください。",
            "markdown_style": "Markdownスタイル",
            "markdown_style_subtext": "マスク内のマーカー、またはマスク全体の装飾",
            "markdown_style_pick": "スタイル",
            "md_manual": "手動マーカー",
            "md_bold": "マスク全体: 太字",
            "md_italic": "マスク全体: 斜体",
            "md_strike": "マスク全体: 取り消し線",
            "md_spoiler": "マスク全体: スポイラー",
            "md_mono": "マスク全体: 等幅",
            "chat_config_menu": "このチャットの設定",
            "chat_config_auto": "メイン（スケジュール適用）",
            "chat_config_saved": "チャットの設定を保存しました",
            "chat_config_reset": "このチャットはメイン設定を使用します",
            "schedule": "設定のスケジュール",
            "schedule_empty": "未設定",
            "schedule_count": "ルール: {n}",
            "schedule_message": "1行に1ルール: [日付] [HH:MM-HH:MM] [曜日] = 設定名\n日付: YYYY-MM-DD、DD.MM.YYYY、DD.MM（毎年）。範囲は「..」で指定。時刻を省略すると終日。曜日: mon-fri、sat,sun（省略で毎日）。日付付きルールは曜日ルールより優先され、それ以外は最初に一致したルールが適用されます。専用の設定があるチャットはスケジュールの影響を受けません。 時刻の代わりに時間帯も指定できます: 朝(05–12)、昼(12–17)、夕方(17–23)、夜(23–05)、または「朝-夕方」のような範囲。",
            "schedule_hint": "22:00-07:00 = 夜\n09:00-18:00 mon-fri = 仕事\n31.12 = 祝日\n2026-12-28..2027-01-10 = 休暇\n朝 mon-fri = 仕事\n夜 = 夜",
            "schedule_saved": "スケジュールを保存しました",
            "schedule_error": "{n}行目: {reason}",
            "schedule_err_format": "形式は「[日付] [HH:MM-HH:MM] [曜日] = 設定名」",
            "schedule_err_time": "時刻が正しくありません",
            "schedule_err_days": "曜日が正しくありません",
            "schedule_err_config": "設定「{name}」がありません",
            "schedule_err_limit": "ルールは最大{n}件",
            "skip_once_menu": "今回だけ装飾しない",
            "skip_once_on": "次のメッセージは装飾なしで送信されます",
            "skip_once_off": "スキップを取り消しました",
            "random_style": "ランダムスタイル",
            "random_style_subtext": "メッセージごとにランダムなスタイルを選びます（上下反転テキストを除く）。",
            "mask_rotation": "マスクのローテーション",
            "mask_rotation_subtext": "メインのマスクの代わりにリストのマスクを使います。チャットのマスクが優先されます。",
            "masks_list": "マスク一覧",
            "masks_list_count": "マスク数: {n}",
            "masks_list_empty": "1行に1つのマスク",
            "masks_list_hint": "1行に1つのマスク。各マスクに [text] を1つだけ含めてください。",
            "masks_list_invalid": "各マスクには [text] がちょうど1つ必要です",
            "masks_list_limit": "マスクは最大{n}個までです",
            "mask_tags_hint": "タグ: [date], [time], [datetime], [chat], [id], [weekday], [year], [month], [day], [username], [count], [random_emoji], [hour], [minute], [second], [time12], [ampm], [daypart], [week], [yearday], [monthname], [weekday_short], [year_short], [timestamp], [tz], [chattype], [dice]",
            "mask_rotation_mode": "ローテーションの順序",
            "rotation_random": "ランダム",
            "rotation_sequential": "順番",
            "regex_exceptions": "正規表現の除外",
            "regex_exceptions_hint": "1行に1つの正規表現。いずれかに一致するメッセージは装飾されません。",
            "regex_exceptions_count": "ルール数: {n}",
            "regex_exceptions_empty": "上級者向け",
            "regex_invalid": "無効な式です: {error}",
            "regex_limit": "式は最大{n}個、各{m}文字までです",
            "chat_types": "チャットの種類",
            "chat_types_hint": "選択した種類のチャットでのみ装飾します。",
            "chat_types_all": "すべてのチャット",
            "chat_types_none": "少なくとも1つ選択してください",
            "chat_type_private": "個人チャット",
            "chat_type_group": "グループ",
            "chat_type_channel": "チャンネル",
            "separator": "区切り文字",
            "enable_separator": "区切り文字を有効にする",
            "enable_separator_subtext": "単語の間にカスタム区切り文字を追加します。",
            "separator_set": "区切り文字セット",
            "separator_count": "単語間の区切り文字数",
            "separator_count_subtext": "タップして変更します。",
            "exceptions": "例外",
            "ignore_emoji_only": "絵文字だけのメッセージを無視",
            "ignore_emoji_only_subtext": "1つ以上の絵文字だけで構成されたメッセージを変更しません。",
            "exceptions_hint": "指定した値で始まる、または終わるメッセージは変更しません。値は1行ずつ入力します。",
            "ignore_special": "コード・コマンド・メンション・リンクを除外",
            "ignore_special_subtext": "コマンド、@メンション、リンク、コードはそのまま残します。このようなメッセージではマスクのMarkdownは適用されません。",
            "chat_menu": "例外リストにチャットを追加または削除",
            "chat_added": "チャットを例外リストに追加しました",
            "chat_removed": "チャットを例外リストから削除しました",
            "mask_editor_title": "マスク設定",
            "mask_editor_hint": "マスクを入力してください。メッセージ本文には [text] を使用します。[text: リンク] でリンクにできます。",
            "custom_separator_title": "カスタム",
            "custom_separator_message": "区切り文字をカンマで区切って入力してください。例:\n•, ·, —, ~, |",
            "save": "保存",
            "delete": "削除",
            "cancel": "キャンセル",
            "capture_custom_emoji": "プレミアム絵文字を取得",
            "capture_enabled": "プレミアム絵文字の取得をオンにしました。プレミアム絵文字を含むメッセージを送ってください",
            "capture_disabled": "プレミアム絵文字の取得をオフにしました",
            "custom_emoji_hint": "プレミアム絵文字はマーカー (id|🙂) で指定します。🙂 はプレミアムを使っていない人に表示される通常の絵文字です。マーカーはチャットメニューの「プレミアム絵文字を取得」で取得できます。",
            "mask_invalid": "マスクには [text] をちょうど1つ含めてください",
            "mask_too_long": "マスクが長すぎます（最大{n}文字）",
            "mask_preview_sample": "メッセージの例",
            "mask_preview_invalid": "マスクが無効です。[text] を1つだけ指定してください",
            "separator_preview_words": "プレビュー用のサンプルテキスト",
            "exceptions_count": "除外: {n}、チャット: {m}",
            "configuration_import_cancelled": "インポートをキャンセルしました",
            "import_configuration": "インポート",
            "export_configuration": "エクスポート",
            "reset_configuration": "デフォルト値に戻す",
            "reset_to_plugin_defaults": "インポート時の値を無視してプラグインの初期設定に戻す",
            "reset_to_plugin_defaults_unavailable": "利用できません：この設定はプラグインで作成されたため、リセットすると作成時の状態に戻ります。",
            "configurations": "設定",
            "active_configuration": "設定",
            "add_configuration": "新しい設定を作成",
            "add_configuration_subtext": "独立した設定を作成し、すぐに有効にします。",
            "configuration_name_hint": "設定名",
            "new_configuration_source_title": "新しい設定の内容",
            "new_configuration_source_message": "何を元にしますか？ 何も選択しない場合は初期設定になります。",
            "new_configuration_copy_current": "現在の設定の内容をコピー",
            "create": "作成",
            "delete_configuration": "設定を削除",
            "delete_configuration_confirm": "設定「{name}」を削除しますか？",
            "no_inactive_configurations": "削除できる非アクティブな設定がありません",
            "imported_configuration": "インポートした設定",
            "rename_configuration": "設定の名前を変更",
            "rename_configuration_subtext": "現在の設定の名前を変更します。",
            "configuration_name_invalid": "一意の設定名を入力してください。",
            "configuration_name_taken": "同じ名前の設定がすでに存在します。",
            "configuration_deleted": "削除した設定: {n}",
            "delete_configurations": "設定を削除",
            "delete_configurations_subtext": "非アクティブな設定を削除します。アクティブな設定は残ります。",
            "delete_configurations_select": "削除する非アクティブな設定を選択してください。",
            "import_new_configuration_name": "新しい設定の名前",
            "select_configuration": "設定を選択",
            "select_configuration_subtext": "1つから6つすべてまで、項目を選択できます。",
            "config_mask": "マスク",
            "config_separator": "区切り文字",
            "config_exceptions": "例外とチャット",
            "config_language": "選択した言語",
            "config_media": "メディア",
            "media_attachment": "メディア",
            "enable_media_attachment": "メディアを有効にする",
            "enable_media_attachment_subtext": "インポートしたファイルを送信時に自動的に添付します。",
            "media_file": "選択したファイル",
            "media_file_none": "ファイルが選択されていません",
            "import_media": "メディアをインポート",
            "delete_media": "メディアを削除",
            "delete_media_subtext": "Prefixfyからインポートしたファイルを削除します。",
            "media_imported": "メディアをインポートしました",
            "media_deleted": "メディアを削除しました",
            "media_import_failed": "メディアをインポートできませんでした",
            "media_delete_failed": "メディアを削除できませんでした",
            "apply": "適用",
            "configuration_imported": "設定をインポートしました",
            "configuration_import_failed": "設定をインポートできませんでした",
            "configuration_save_failed": "現在の設定を保存できませんでした",
            "configuration_exported": "設定をエクスポートしました",
            "configuration_export_failed": "設定をエクスポートできませんでした",
            "configuration_export_destination_title": "エクスポート先",
            "configuration_export_to_saved": "アクティブなアカウントの保存メッセージ",
            "configuration_export_to_device": "端末のストレージ",
            "configuration_restored": "選択した設定を復元しました",
            "configuration_nothing_selected": "少なくとも1つの設定項目を選択してください",
            "config_found_title": "設定が見つかりました",
            "config_found_contains": "内容",
            "config_import_as_new": "新しい設定としてインポート",
            "config_found_import": "インポート",
            "config_file_open_failed": "設定ファイルを開けませんでした",
            "invalid_configuration": "ファイルに選択した設定が含まれていないか、形式が正しくありません。",
            "default_configuration_name": "デフォルト設定",
            "configuration_n": "設定 {n}",
            "operation_failed": "操作に失敗しました",
            "text_style_subtext": "メッセージ本文のみを変換します。Fancy・Bold・Gothic・Circled はラテン文字のみ、L33T はキリル文字にも対応します。",
            "enable_text_style": "テキストスタイルを有効にする",
            "configuration_short": "対象の設定項目を選択",
            "edit_text_toggle": "テキストの編集",
            "edit_text_toggle_subtext": "通常のテキストメッセージの編集時に装飾します。",
            "edit_media_toggle": "キャプションの編集",
            "edit_media_toggle_subtext": "メディアのキャプションの編集時に装飾します。",
            "skip_once_on_edit": "編集時も「今回だけ装飾しない」",
            "skip_once_on_edit_subtext": "スキップが有効なら、このチャットの次の編集は装飾されません。",
            "conditional_masks": "内容別マスク",
            "conditional_masks_hint": "1行に1ルール: 正規表現 => マスク。テキストが式に一致するとそのマスクを使用し、最初に一致した行が優先されます。各マスクには [text] を1つだけ含めてください。",
            "conditional_masks_count": "ルール数: {n}",
            "conditional_masks_empty": "テキストに…が含まれる場合",
            "conditional_masks_format": "{n}行目: 「式 => マスク」の形式で入力してください",
            "md_quote": "マスク全体: 引用",
            "config_schedule": "チャット設定とスケジュール",
            "schedule_err_date": "日付が正しくありません",
        },
        "ko": {
            "enable_plugin": "플러그인 사용",
            "enable_plugin_subtext": "켜짐: 목록의 채팅을 제외한 전체. 꺼짐: 목록의 채팅에서만.",
            "language": "언어",
            "update_required": "업데이트 필요",
            "update_required_subtext": "Prefixfy {version}(공식 빌드)를 설치하세요. 그때까지 플러그인은 메시지를 꾸미지 않습니다.",
            "verify_required": "검증 실패",
            "verify_required_subtext": "이 Prefixfy 빌드를 검증하지 못했습니다. 그때까지 플러그인은 메시지를 꾸미지 않습니다. 인터넷 연결을 확인하세요.",
            "account_blocked": "접근이 거부되었습니다",
            "account_blocked_subtext": "이 기기의 계정 중 하나가 Prefixfy 블랙리스트에 등록되어 있습니다. 플러그인이 비활성화되었습니다.",
            "section_scope": "적용 범위",
            "plugin_language": "플러그인 언어",
            "language_auto": "언어 자동 감지",
            "language_auto_subtext": "Telegram 인터페이스 언어를 사용합니다. 끄면 언어를 직접 선택할 수 있습니다.",
            "message": "메시지",
            "message_subtext": "일반 텍스트 메시지에 플러그인을 사용합니다.",
            "media": "미디어",
            "media_subtext": "미디어 캡션에 플러그인을 사용합니다.",
            "edit_message": "메시지 수정",
            "edit_message_subtext": "메시지를 수정할 때도 꾸밉니다. 이미 마스크가 있는 텍스트는 바꾸지 않습니다.",
            "mask": "마스크",
            "mask_text": "마스크 텍스트",
            "text_style": "텍스트 스타일",
            "skip_once_expired": "건너뛰기가 만료되었습니다. 다음 메시지는 꾸며서 전송됩니다",
            "empty_means_default": "기본값으로 되돌리려면 입력란을 비우고 “저장”을 누르세요.",
            "markdown_style": "Markdown 스타일",
            "markdown_style_subtext": "마스크의 마커 또는 마스크 전체 서식",
            "markdown_style_pick": "스타일",
            "md_manual": "수동 마커",
            "md_bold": "마스크 전체: 굵게",
            "md_italic": "마스크 전체: 기울임",
            "md_strike": "마스크 전체: 취소선",
            "md_spoiler": "마스크 전체: 스포일러",
            "md_mono": "마스크 전체: 고정폭",
            "chat_config_menu": "이 채팅의 구성",
            "chat_config_auto": "기본(및 일정)",
            "chat_config_saved": "채팅 구성을 저장했습니다",
            "chat_config_reset": "이 채팅은 기본 구성을 사용합니다",
            "schedule": "구성 일정",
            "schedule_empty": "설정 안 됨",
            "schedule_count": "규칙: {n}",
            "schedule_message": "한 줄에 규칙 하나: [날짜] [HH:MM-HH:MM] [요일] = 구성 이름\n날짜: YYYY-MM-DD, DD.MM.YYYY 또는 DD.MM(매년), 범위는 “..” 사용. 시간을 생략하면 하루 종일. 요일: mon-fri, sat,sun (생략하면 매일). 날짜가 있는 규칙이 요일 규칙보다 우선하며, 나머지는 처음 일치하는 규칙이 적용됩니다. 자체 구성이 있는 채팅에는 일정이 적용되지 않습니다. 시간 대신 시간대도 쓸 수 있습니다: 아침(05–12), 낮(12–17), 저녁(17–23), 밤(23–05) 또는 “아침-저녁” 같은 범위.",
            "schedule_hint": "22:00-07:00 = 밤\n09:00-18:00 mon-fri = 업무\n31.12 = 휴일\n2026-12-28..2027-01-10 = 휴가\n아침 mon-fri = 업무\n밤 = 밤",
            "schedule_saved": "일정을 저장했습니다",
            "schedule_error": "{n}번째 줄: {reason}",
            "schedule_err_format": "형식: “[날짜] [HH:MM-HH:MM] [요일] = 구성”",
            "schedule_err_time": "잘못된 시간",
            "schedule_err_days": "잘못된 요일",
            "schedule_err_config": "“{name}” 구성이 없습니다",
            "schedule_err_limit": "규칙은 최대 {n}개",
            "skip_once_menu": "한 번만 꾸미기 건너뛰기",
            "skip_once_on": "다음 메시지는 꾸밈 없이 전송됩니다",
            "skip_once_off": "건너뛰기를 취소했습니다",
            "random_style": "랜덤 스타일",
            "random_style_subtext": "메시지마다 무작위 스타일을 고릅니다(뒤집힌 텍스트 제외).",
            "mask_rotation": "마스크 순환",
            "mask_rotation_subtext": "기본 마스크 대신 목록의 마스크를 사용합니다. 채팅별 마스크가 우선합니다.",
            "masks_list": "마스크 목록",
            "masks_list_count": "마스크 수: {n}",
            "masks_list_empty": "한 줄에 마스크 하나",
            "masks_list_hint": "한 줄에 마스크 하나, 각 마스크에는 [text]가 정확히 하나 있어야 합니다.",
            "masks_list_invalid": "각 마스크에는 [text]가 정확히 하나 있어야 합니다",
            "masks_list_limit": "마스크는 최대 {n}개입니다",
            "mask_tags_hint": "태그: [date], [time], [datetime], [chat], [id], [weekday], [year], [month], [day], [username], [count], [random_emoji], [hour], [minute], [second], [time12], [ampm], [daypart], [week], [yearday], [monthname], [weekday_short], [year_short], [timestamp], [tz], [chattype], [dice]",
            "mask_rotation_mode": "순환 순서",
            "rotation_random": "무작위",
            "rotation_sequential": "순서대로",
            "regex_exceptions": "정규식 예외",
            "regex_exceptions_hint": "한 줄에 정규식 하나. 하나라도 일치하는 메시지는 꾸미지 않습니다.",
            "regex_exceptions_count": "규칙 수: {n}",
            "regex_exceptions_empty": "고급 사용자용",
            "regex_invalid": "잘못된 식: {error}",
            "regex_limit": "식은 최대 {n}개, 각 {m}자까지입니다",
            "chat_types": "채팅 유형",
            "chat_types_hint": "선택한 유형의 채팅에서만 꾸밉니다.",
            "chat_types_all": "모든 채팅",
            "chat_types_none": "하나 이상 선택하세요",
            "chat_type_private": "개인 채팅",
            "chat_type_group": "그룹",
            "chat_type_channel": "채널",
            "separator": "구분자",
            "enable_separator": "구분자 사용",
            "enable_separator_subtext": "단어 사이에 사용자 지정 구분자를 추가합니다.",
            "separator_set": "구분자 세트",
            "separator_count": "단어 사이 구분자 개수",
            "separator_count_subtext": "눌러서 변경하세요.",
            "exceptions": "예외",
            "ignore_emoji_only": "이모지만 있는 메시지 무시",
            "ignore_emoji_only_subtext": "하나 이상의 이모지로만 이루어진 메시지는 변경하지 않습니다.",
            "exceptions_hint": "지정한 값으로 시작하거나 끝나는 메시지는 변경되지 않습니다. 값은 한 줄에 하나씩 입력하세요.",
            "ignore_special": "코드, 명령어, 멘션, 링크 제외",
            "ignore_special_subtext": "명령어, @멘션, 링크, 코드는 그대로 유지합니다. 이런 메시지에는 마스크의 Markdown이 적용되지 않습니다.",
            "chat_menu": "예외 목록에 채팅 추가/제거",
            "chat_added": "채팅이 예외 목록에 추가되었습니다",
            "chat_removed": "채팅이 예외 목록에서 제거되었습니다",
            "mask_editor_title": "마스크 설정",
            "mask_editor_hint": "마스크를 입력하세요. 메시지 텍스트는 [text]로 표시하며, [text: 링크]를 쓰면 하이퍼링크가 됩니다.",
            "custom_separator_title": "사용자 지정",
            "custom_separator_message": "구분자를 쉼표로 구분하여 입력하세요. 예:\n•, ·, —, ~, |",
            "save": "저장",
            "delete": "삭제",
            "cancel": "취소",
            "capture_custom_emoji": "프리미엄 이모지 캡처",
            "capture_enabled": "프리미엄 이모지 캡처를 켰습니다. 프리미엄 이모지가 포함된 메시지를 보내세요",
            "capture_disabled": "프리미엄 이모지 캡처를 껐습니다",
            "custom_emoji_hint": "프리미엄 이모지는 (id|🙂) 마커로 지정합니다. 🙂는 프리미엄이 없는 사람에게 보이는 일반 이모지입니다. 마커는 채팅 메뉴의 '프리미엄 이모지 캡처'로 얻을 수 있습니다.",
            "mask_invalid": "마스크에는 [text]가 정확히 하나 있어야 합니다",
            "mask_too_long": "마스크가 너무 깁니다(최대 {n}자)",
            "mask_preview_sample": "메시지 예시",
            "mask_preview_invalid": "마스크가 올바르지 않습니다: [text]가 정확히 하나 필요합니다",
            "separator_preview_words": "미리보기용 예시 텍스트",
            "exceptions_count": "예외: {n}, 채팅: {m}",
            "configuration_import_cancelled": "가져오기가 취소되었습니다",
            "import_configuration": "가져오기",
            "export_configuration": "내보내기",
            "reset_configuration": "기본값 복원",
            "reset_to_plugin_defaults": "가져온 값을 무시하고 플러그인 기본값으로 복원",
            "reset_to_plugin_defaults_unavailable": "사용할 수 없음: 이 구성은 플러그인에서 만들어졌으므로 초기화하면 생성 당시 상태로 돌아갑니다.",
            "configurations": "구성",
            "active_configuration": "활성 구성",
            "add_configuration": "새 구성 만들기",
            "add_configuration_subtext": "별도의 설정 세트를 만들고 바로 활성화합니다.",
            "configuration_name_hint": "구성 이름",
            "new_configuration_source_title": "새 구성 설정",
            "new_configuration_source_message": "무엇을 기준으로 시작할까요? 아무것도 선택하지 않으면 기본 설정이 사용됩니다.",
            "new_configuration_copy_current": "현재 구성의 설정 복사",
            "create": "만들기",
            "delete_configuration": "구성 삭제",
            "delete_configuration_confirm": "구성 “{name}”을(를) 삭제할까요?",
            "no_inactive_configurations": "삭제할 비활성 구성이 없습니다",
            "imported_configuration": "가져온 구성",
            "rename_configuration": "구성 이름 변경",
            "rename_configuration_subtext": "현재 구성의 이름을 변경합니다.",
            "configuration_name_invalid": "고유한 구성 이름을 입력하세요.",
            "configuration_name_taken": "같은 이름의 구성이 이미 있습니다.",
            "configuration_deleted": "삭제된 구성: {n}",
            "delete_configurations": "구성 삭제",
            "delete_configurations_subtext": "비활성 구성을 삭제합니다. 활성 구성은 유지됩니다.",
            "delete_configurations_select": "삭제할 비활성 구성을 선택하세요.",
            "import_new_configuration_name": "새 구성 이름",
            "select_configuration": "구성 선택",
            "select_configuration_subtext": "항목을 하나부터 여섯 개 모두까지 선택할 수 있습니다.",
            "config_mask": "마스크",
            "config_separator": "구분자",
            "config_exceptions": "예외 및 채팅",
            "config_language": "선택한 언어",
            "config_media": "미디어",
            "media_attachment": "미디어",
            "enable_media_attachment": "미디어 사용",
            "enable_media_attachment_subtext": "가져온 파일을 보내는 메시지에 자동으로 첨부합니다.",
            "media_file": "선택한 파일",
            "media_file_none": "선택한 파일 없음",
            "import_media": "미디어 가져오기",
            "delete_media": "미디어 삭제",
            "delete_media_subtext": "Prefixfy에서 가져온 파일을 삭제합니다.",
            "media_imported": "미디어를 가져왔습니다",
            "media_deleted": "미디어를 삭제했습니다",
            "media_import_failed": "미디어를 가져오지 못했습니다",
            "media_delete_failed": "미디어를 삭제하지 못했습니다",
            "apply": "적용",
            "configuration_imported": "구성을 가져왔습니다",
            "configuration_import_failed": "구성을 가져오지 못했습니다",
            "configuration_save_failed": "현재 구성을 저장하지 못했습니다",
            "configuration_exported": "구성을 내보냈습니다",
            "configuration_export_failed": "구성을 내보내지 못했습니다",
            "configuration_export_destination_title": "어디로 내보낼까요?",
            "configuration_export_to_saved": "활성 계정의 저장된 메시지",
            "configuration_export_to_device": "기기 저장공간",
            "configuration_restored": "선택한 값을 복원했습니다",
            "configuration_nothing_selected": "구성 항목을 하나 이상 선택하세요",
            "config_found_title": "구성을 찾았습니다",
            "config_found_contains": "포함 내용",
            "config_import_as_new": "새 구성으로 가져오기",
            "config_found_import": "가져오기",
            "config_file_open_failed": "구성 파일을 열 수 없습니다",
            "invalid_configuration": "파일에 선택한 구성이 없거나 형식이 올바르지 않습니다.",
            "default_configuration_name": "기본 구성",
            "configuration_n": "구성 {n}",
            "operation_failed": "작업을 수행하지 못했습니다",
            "text_style_subtext": "메시지 본문만 변환합니다. Fancy, Bold, Gothic, Circled는 라틴 문자만, L33T는 키릴 문자도 지원합니다.",
            "enable_text_style": "텍스트 스타일 사용",
            "configuration_short": "구성 항목 선택",
            "edit_text_toggle": "텍스트 수정",
            "edit_text_toggle_subtext": "일반 텍스트 메시지를 수정할 때 꾸밉니다.",
            "edit_media_toggle": "캡션 수정",
            "edit_media_toggle_subtext": "미디어 캡션을 수정할 때 꾸밉니다.",
            "skip_once_on_edit": "수정 시에도 ‘한 번만 건너뛰기’",
            "skip_once_on_edit_subtext": "건너뛰기가 켜져 있으면 이 채팅의 다음 수정은 꾸미지 않습니다.",
            "conditional_masks": "내용별 마스크",
            "conditional_masks_hint": "한 줄에 규칙 하나: 정규식 => 마스크. 텍스트가 식과 일치하면 해당 마스크를 사용하며, 처음 일치한 줄이 적용됩니다. 각 마스크에는 [text]가 정확히 하나 있어야 합니다.",
            "conditional_masks_count": "규칙 수: {n}",
            "conditional_masks_empty": "텍스트에 …가 있으면",
            "conditional_masks_format": "{n}번째 줄: ‘식 => 마스크’ 형식이어야 합니다",
            "md_quote": "마스크 전체: 인용",
            "config_schedule": "채팅 구성과 일정",
            "schedule_err_date": "잘못된 날짜",
        },
        "ar": {
            "enable_plugin": "تفعيل الإضافة",
            "enable_plugin_subtext": "مفعّل: كل المحادثات عدا القائمة. معطّل: محادثات القائمة فقط.",
            "language": "اللغة",
            "update_required": "التحديث مطلوب",
            "update_required_subtext": "ثبّت Prefixfy {version} (النسخة الرسمية). إلى ذلك الحين لن تنسّق الإضافة الرسائل.",
            "verify_required": "فشل التحقق",
            "verify_required_subtext": "تعذّر التحقق من نسخة Prefixfy هذه. إلى ذلك الحين لن تنسّق الإضافة الرسائل؛ تحقّق من اتصالك بالإنترنت.",
            "account_blocked": "تم رفض الوصول",
            "account_blocked_subtext": "أحد الحسابات على هذا الجهاز في القائمة السوداء لـ Prefixfy. الإضافة معطّلة.",
            "section_scope": "نطاق العمل",
            "plugin_language": "لغة الإضافة",
            "language_auto": "الكشف التلقائي عن اللغة",
            "language_auto_subtext": "استخدام لغة واجهة Telegram. أوقف الخيار لاختيار اللغة يدويًا.",
            "message": "الرسالة",
            "message_subtext": "استخدام الإضافة للرسائل النصية العادية.",
            "media": "الوسائط",
            "media_subtext": "استخدام الإضافة لتعليقات الوسائط.",
            "edit_message": "تعديل الرسائل",
            "edit_message_subtext": "تنسيق الرسائل عند تعديلها. النص الذي يحتوي على القناع بالفعل لا يتغيّر.",
            "mask": "القناع",
            "mask_text": "نص القناع",
            "text_style": "نمط النص",
            "skip_once_expired": "انتهت مدة التخطي: ستُنسَّق الرسالة التالية",
            "empty_means_default": "لاستعادة الإعداد الافتراضي، امسح الحقل ثم اضغط «حفظ».",
            "markdown_style": "نمط Markdown",
            "markdown_style_subtext": "علامات داخل القناع أو تنسيق القناع كله",
            "markdown_style_pick": "النمط",
            "md_manual": "علامات يدوية",
            "md_bold": "القناع كله: عريض",
            "md_italic": "القناع كله: مائل",
            "md_strike": "القناع كله: يتوسطه خط",
            "md_spoiler": "القناع كله: إخفاء",
            "md_mono": "القناع كله: أحادي المسافة",
            "chat_config_menu": "إعدادات هذه المحادثة",
            "chat_config_auto": "الأساسية (والجدول)",
            "chat_config_saved": "تم حفظ إعدادات المحادثة",
            "chat_config_reset": "تستخدم المحادثة الإعدادات الأساسية",
            "schedule": "جدول الإعدادات",
            "schedule_empty": "غير محدد",
            "schedule_count": "القواعد: {n}",
            "schedule_message": "قاعدة واحدة في كل سطر: [التاريخ] [HH:MM-HH:MM] [الأيام] = اسم الإعدادات\nالتاريخ: YYYY-MM-DD أو DD.MM.YYYY أو DD.MM (كل سنة)، والنطاق بـ «..». بدون وقت = اليوم كله. الأيام: mon-fri أو sat,sun (بدونها = كل يوم). قواعد التاريخ لها الأولوية على قواعد الأيام، وفي الباقي تُطبَّق أول قاعدة مطابقة. المحادثة ذات الإعدادات الخاصة تتجاهل الجدول. يمكن استخدام جزء من اليوم بدل الوقت: الصباح (05–12)، النهار (12–17)، المساء (17–23)، الليل (23–05) أو نطاق مثل «الصباح-المساء».",
            "schedule_hint": "22:00-07:00 = ليلي\n09:00-18:00 mon-fri = عمل\n31.12 = عطلة\n2026-12-28..2027-01-10 = إجازة\nالصباح mon-fri = عمل\nالليل = ليل",
            "schedule_saved": "تم حفظ الجدول",
            "schedule_error": "السطر {n}: {reason}",
            "schedule_err_format": "الصيغة: «[التاريخ] [HH:MM-HH:MM] [الأيام] = الإعدادات»",
            "schedule_err_time": "وقت غير صالح",
            "schedule_err_days": "أيام غير صالحة",
            "schedule_err_config": "لا توجد إعدادات «{name}»",
            "schedule_err_limit": "الحد الأقصى {n} قاعدة",
            "skip_once_menu": "تخطي التنسيق مرة واحدة",
            "skip_once_on": "ستُرسل الرسالة التالية بدون تنسيق",
            "skip_once_off": "تم إلغاء التخطي",
            "random_style": "نمط عشوائي",
            "random_style_subtext": "يختار نمطًا عشوائيًا لكل رسالة (باستثناء النص المقلوب).",
            "mask_rotation": "تدوير الأقنعة",
            "mask_rotation_subtext": "تُستخدم أقنعة القائمة بدلًا من القناع الأساسي. قناع الدردشة له الأولوية.",
            "masks_list": "قائمة الأقنعة",
            "masks_list_count": "عدد الأقنعة: {n}",
            "masks_list_empty": "قناع واحد في كل سطر",
            "masks_list_hint": "قناع واحد في كل سطر، ويجب أن يحتوي كل قناع على [text] واحد بالضبط.",
            "masks_list_invalid": "يجب أن يحتوي كل قناع على [text] واحد بالضبط",
            "masks_list_limit": "الحد الأقصى {n} قناعًا",
            "mask_tags_hint": "الوسوم: [date] و[time] و[datetime] و[chat] و[id] و[weekday] و[year] و[month] و[day] و[username] و[count] و[random_emoji], [hour], [minute], [second], [time12], [ampm], [daypart], [week], [yearday], [monthname], [weekday_short], [year_short], [timestamp], [tz], [chattype], [dice]",
            "mask_rotation_mode": "ترتيب التدوير",
            "rotation_random": "عشوائي",
            "rotation_sequential": "بالتتابع",
            "regex_exceptions": "استثناءات Regex",
            "regex_exceptions_hint": "تعبير نمطي واحد في كل سطر. الرسالة المطابقة لأي منها تبقى بدون تنسيق.",
            "regex_exceptions_count": "القواعد: {n}",
            "regex_exceptions_empty": "للمستخدمين المتقدمين",
            "regex_invalid": "تعبير غير صالح: {error}",
            "regex_limit": "حتى {n} تعبيرًا، وبحد أقصى {m} حرفًا لكل تعبير",
            "chat_types": "أنواع الدردشات",
            "chat_types_hint": "يعمل التنسيق فقط في أنواع الدردشات المحددة.",
            "chat_types_all": "كل الدردشات",
            "chat_types_none": "اختر نوعًا واحدًا على الأقل",
            "chat_type_private": "الخاصة",
            "chat_type_group": "المجموعات",
            "chat_type_channel": "القنوات",
            "separator": "الفاصل",
            "enable_separator": "تفعيل الفاصل",
            "enable_separator_subtext": "إضافة فواصل مخصصة بين الكلمات.",
            "separator_set": "مجموعة الفواصل",
            "separator_count": "عدد الفواصل بين الكلمات",
            "separator_count_subtext": "اضغط للتغيير.",
            "exceptions": "الاستثناءات",
            "ignore_emoji_only": "تجاهل الرسائل المكوّنة من إيموجي فقط",
            "ignore_emoji_only_subtext": "عدم تعديل الرسائل المكوّنة من إيموجي واحد أو أكثر فقط.",
            "exceptions_hint": "لا تُعدَّل الرسائل التي تبدأ أو تنتهي بالقيمة المحددة. اكتب كل قيمة في سطر جديد.",
            "ignore_special": "استثناء الأكواد والأوامر والإشارات والروابط",
            "ignore_special_subtext": "تبقى الأوامر والإشارات والروابط والأكواد كما هي. لا يُطبَّق Markdown القناع على هذه الرسائل.",
            "chat_menu": "إضافة/إزالة المحادثة إلى/من قائمة الاستثناءات",
            "chat_added": "تمت إضافة المحادثة إلى قائمة الاستثناءات",
            "chat_removed": "تمت إزالة المحادثة من قائمة الاستثناءات",
            "mask_editor_title": "إعدادات القناع",
            "mask_editor_hint": "أدخل القناع. استخدم [text] لنص الرسالة، أو [text: رابط] لتحويله إلى رابط.",
            "custom_separator_title": "مخصص",
            "custom_separator_message": "أدخل الفواصل مفصولة بفواصل، مثلًا:\n•, ·, —, ~, |",
            "save": "حفظ",
            "delete": "حذف",
            "cancel": "إلغاء",
            "capture_custom_emoji": "التقاط إيموجي بريميوم",
            "capture_enabled": "تم تفعيل التقاط إيموجي بريميوم: أرسل رسالة تحتوي على إيموجي بريميوم",
            "capture_disabled": "تم إيقاف التقاط إيموجي بريميوم",
            "custom_emoji_hint": "إيموجي بريميوم: العلامة (id|🙂)، حيث 🙂 إيموجي عادي يراه من لا يملك بريميوم. يمكنك الحصول على العلامة عبر «التقاط إيموجي بريميوم» في قائمة المحادثة.",
            "mask_invalid": "يجب أن يحتوي القناع على [text] واحد بالضبط",
            "mask_too_long": "القناع طويل جدًا: {n} حرفًا كحد أقصى",
            "mask_preview_sample": "رسالة تجريبية",
            "mask_preview_invalid": "القناع غير صالح: مطلوب [text] واحد بالضبط",
            "separator_preview_words": "نص تجريبي للمعاينة",
            "exceptions_count": "الاستثناءات: {n}، المحادثات: {m}",
            "configuration_import_cancelled": "تم إلغاء الاستيراد",
            "import_configuration": "استيراد",
            "export_configuration": "تصدير",
            "reset_configuration": "استعادة القيم الافتراضية",
            "reset_to_plugin_defaults": "تجاهل القيم المستوردة واستعادة الإعدادات الافتراضية للإضافة",
            "reset_to_plugin_defaults_unavailable": "غير متاح: تم إنشاء هذا التكوين بواسطة الإضافة، لذا تعيده إعادة الضبط إلى حالته وقت الإنشاء.",
            "configurations": "التكوينات",
            "active_configuration": "التكوين النشط",
            "add_configuration": "إنشاء تكوين جديد",
            "add_configuration_subtext": "مجموعة إعدادات منفصلة تصبح نشطة فورًا.",
            "configuration_name_hint": "اسم التكوين",
            "new_configuration_source_title": "إعدادات التكوين الجديد",
            "new_configuration_source_message": "ما الأساس الذي سيبدأ منه؟ إذا لم تحدد شيئًا فستُستخدم الإعدادات الافتراضية.",
            "new_configuration_copy_current": "نسخ إعدادات التكوين الحالي",
            "create": "إنشاء",
            "delete_configuration": "حذف التكوين",
            "delete_configuration_confirm": "هل تريد حذف التكوين «{name}»؟",
            "no_inactive_configurations": "لا توجد تكوينات غير نشطة للحذف",
            "imported_configuration": "تكوين مستورد",
            "rename_configuration": "إعادة تسمية التكوين",
            "rename_configuration_subtext": "تغيير اسم التكوين الحالي.",
            "configuration_name_invalid": "أدخل اسمًا فريدًا للتكوين.",
            "configuration_name_taken": "يوجد تكوين بهذا الاسم بالفعل.",
            "configuration_deleted": "التكوينات المحذوفة: {n}",
            "delete_configurations": "حذف التكوينات",
            "delete_configurations_subtext": "حذف التكوينات غير النشطة. يبقى التكوين النشط.",
            "delete_configurations_select": "اختر التكوينات غير النشطة المراد حذفها.",
            "import_new_configuration_name": "اسم التكوين الجديد",
            "select_configuration": "اختيار التكوين",
            "select_configuration_subtext": "يمكنك اختيار جزء واحد أو أكثر حتى الأجزاء الستة جميعها.",
            "config_mask": "القناع",
            "config_separator": "الفواصل",
            "config_exceptions": "الاستثناءات والمحادثات",
            "config_language": "اللغة المختارة",
            "config_media": "الوسائط",
            "media_attachment": "الوسائط",
            "enable_media_attachment": "تفعيل الوسائط",
            "enable_media_attachment_subtext": "إرفاق الملف المستورد تلقائيًا بالرسائل الصادرة.",
            "media_file": "الملف المختار",
            "media_file_none": "لم يتم اختيار ملف",
            "import_media": "استيراد وسائط",
            "delete_media": "حذف الوسائط",
            "delete_media_subtext": "حذف الملف المستورد من Prefixfy.",
            "media_imported": "تم استيراد الوسائط",
            "media_deleted": "تم حذف الوسائط",
            "media_import_failed": "تعذّر استيراد الوسائط",
            "media_delete_failed": "تعذّر حذف الوسائط",
            "apply": "تطبيق",
            "configuration_imported": "تم استيراد التكوين",
            "configuration_import_failed": "تعذّر استيراد التكوين",
            "configuration_save_failed": "تعذّر حفظ التكوين الحالي",
            "configuration_exported": "تم تصدير التكوين",
            "configuration_export_failed": "تعذّر تصدير التكوين",
            "configuration_export_destination_title": "إلى أين تريد التصدير؟",
            "configuration_export_to_saved": "الرسائل المحفوظة للحساب النشط",
            "configuration_export_to_device": "مساحة تخزين الجهاز",
            "configuration_restored": "تمت استعادة القيم المحددة",
            "configuration_nothing_selected": "اختر جزءًا واحدًا على الأقل من الإعدادات",
            "config_found_title": "تم العثور على تكوين",
            "config_found_contains": "يحتوي على",
            "config_import_as_new": "استيراد كتكوين جديد",
            "config_found_import": "استيراد",
            "config_file_open_failed": "تعذّر فتح ملف التكوين",
            "invalid_configuration": "لا يحتوي الملف على التكوين المحدد أو أن تنسيقه غير صالح.",
            "default_configuration_name": "التكوين الافتراضي",
            "configuration_n": "التكوين {n}",
            "operation_failed": "تعذّرت العملية",
            "text_style_subtext": "يحوّل نص الرسالة فقط. أنماط Fancy وBold وGothic وCircled للأحرف اللاتينية فقط، ويشمل L33T الأحرف السيريلية أيضًا.",
            "enable_text_style": "تفعيل نمط النص",
            "configuration_short": "اختر أجزاء الإعدادات",
            "edit_text_toggle": "تعديل النصوص",
            "edit_text_toggle_subtext": "تنسيق الرسائل النصية العادية عند تعديلها.",
            "edit_media_toggle": "تعديل التعليقات",
            "edit_media_toggle_subtext": "تنسيق تعليقات الوسائط عند تعديلها.",
            "skip_once_on_edit": "«تخطي مرة واحدة» عند التعديل",
            "skip_once_on_edit_subtext": "إذا كان التخطي مفعّلًا، يبقى التعديل التالي في هذه المحادثة بدون تنسيق.",
            "conditional_masks": "أقنعة حسب المحتوى",
            "conditional_masks_hint": "قاعدة واحدة في كل سطر: تعبير نمطي => قناع. إذا طابق النص التعبير يُستخدم هذا القناع، وتُطبَّق أول قاعدة مطابقة. يجب أن يحتوي كل قناع على [text] واحد بالضبط.",
            "conditional_masks_count": "القواعد: {n}",
            "conditional_masks_empty": "إذا احتوى النص على…",
            "conditional_masks_format": "السطر {n}: الصيغة «تعبير => قناع»",
            "md_quote": "القناع كله: اقتباس",
            "config_schedule": "ربط المحادثات والجدول",
            "schedule_err_date": "تاريخ غير صالح",
        },
        "fr": {
            "enable_plugin": "Activer le plugin",
            "enable_plugin_subtext": "Activé : partout sauf les chats de la liste. Désactivé : seulement dans la liste.",
            "language": "Langue",
            "update_required": "Mise à jour requise",
            "update_required_subtext": "Installez Prefixfy {version} (version officielle). D’ici là, le plugin ne met pas en forme les messages.",
            "verify_required": "Échec de la vérification",
            "verify_required_subtext": "Impossible de vérifier cette version de Prefixfy. D’ici là, le plugin ne met pas en forme les messages ; vérifiez votre connexion Internet.",
            "account_blocked": "Accès refusé",
            "account_blocked_subtext": "L’un des comptes de cet appareil figure sur la liste noire de Prefixfy. Le plugin est désactivé.",
            "section_scope": "Où ça s’applique",
            "plugin_language": "Langue du plugin",
            "language_auto": "Détection automatique de la langue",
            "language_auto_subtext": "Utiliser la langue de l’interface Telegram. Désactivez pour choisir la langue manuellement.",
            "message": "Message",
            "message_subtext": "Utiliser le plugin pour les messages texte ordinaires.",
            "media": "Médias",
            "media_subtext": "Utiliser le plugin pour les légendes des médias.",
            "edit_message": "Modification des messages",
            "edit_message_subtext": "Appliquer le style lors de la modification d’un message. Un texte déjà masqué reste tel quel.",
            "mask": "Masque",
            "mask_text": "Texte du masque",
            "text_style": "Style du texte",
            "skip_once_expired": "Le saut a expiré : le prochain message sera mis en forme",
            "empty_means_default": "Pour revenir à la valeur par défaut, videz le champ et appuyez sur « Enregistrer ».",
            "markdown_style": "Style Markdown",
            "markdown_style_subtext": "Marqueurs dans le masque ou mise en forme du masque entier",
            "markdown_style_pick": "Style",
            "md_manual": "Marqueurs manuels",
            "md_bold": "Masque entier : gras",
            "md_italic": "Masque entier : italique",
            "md_strike": "Masque entier : barré",
            "md_spoiler": "Masque entier : spoiler",
            "md_mono": "Masque entier : monospace",
            "chat_config_menu": "Configuration de ce chat",
            "chat_config_auto": "Principale (et planning)",
            "chat_config_saved": "Configuration du chat enregistrée",
            "chat_config_reset": "Ce chat utilise la configuration principale",
            "schedule": "Planning des configurations",
            "schedule_empty": "Non défini",
            "schedule_count": "Règles : {n}",
            "schedule_message": "Une règle par ligne : [date] [HH:MM-HH:MM] [jours] = nom de la configuration.\nDate : YYYY-MM-DD, DD.MM.YYYY ou DD.MM (chaque année) ; plage avec « .. ». Sans heure = toute la journée. Jours : mon-fri, sat,sun (sans jours = tous les jours). Les règles avec date l’emportent sur celles par jours ; pour les autres, la première correspondance s’applique. Un chat avec sa propre configuration ignore le planning. À la place de l’heure, on peut indiquer un moment de la journée : matin (05–12), après-midi (12–17), soir (17–23), nuit (23–05) ou une plage comme « matin-soir ».",
            "schedule_hint": "22:00-07:00 = Nuit\n09:00-18:00 mon-fri = Travail\n31.12 = Fête\n2026-12-28..2027-01-10 = Vacances\nmatin mon-fri = Travail\nnuit = Nuit",
            "schedule_saved": "Planning enregistré",
            "schedule_error": "Ligne {n} : {reason}",
            "schedule_err_format": "format attendu : « [date] [HH:MM-HH:MM] [jours] = configuration »",
            "schedule_err_time": "heure invalide",
            "schedule_err_days": "jours invalides",
            "schedule_err_config": "configuration « {name} » introuvable",
            "schedule_err_limit": "pas plus de {n} règles",
            "skip_once_menu": "Ignorer le style une fois",
            "skip_once_on": "Le prochain message sera envoyé sans style",
            "skip_once_off": "Ignorance annulée",
            "random_style": "Style aléatoire",
            "random_style_subtext": "Choisit un style aléatoire pour chaque message (sauf le texte à l’envers).",
            "mask_rotation": "Rotation des masques",
            "mask_rotation_subtext": "Utilise les masques de la liste à la place du masque principal. Le masque du chat est prioritaire.",
            "masks_list": "Liste des masques",
            "masks_list_count": "Masques : {n}",
            "masks_list_empty": "Un masque par ligne",
            "masks_list_hint": "Un masque par ligne, chacun avec exactement un [text].",
            "masks_list_invalid": "Chaque masque doit contenir exactement un [text]",
            "masks_list_limit": "{n} masques maximum",
            "mask_tags_hint": "Balises : [date], [time], [datetime], [chat], [id], [weekday], [year], [month], [day], [username], [count], [random_emoji], [hour], [minute], [second], [time12], [ampm], [daypart], [week], [yearday], [monthname], [weekday_short], [year_short], [timestamp], [tz], [chattype], [dice].",
            "mask_rotation_mode": "Ordre de rotation",
            "rotation_random": "Aléatoire",
            "rotation_sequential": "À tour de rôle",
            "regex_exceptions": "Exceptions regex",
            "regex_exceptions_hint": "Une expression régulière par ligne. Un message qui en correspond à une reste sans style.",
            "regex_exceptions_count": "Règles : {n}",
            "regex_exceptions_empty": "Pour utilisateurs avancés",
            "regex_invalid": "Expression invalide : {error}",
            "regex_limit": "{n} expressions maximum, {m} caractères chacune",
            "chat_types": "Types de chats",
            "chat_types_hint": "Le style ne s’applique que dans les types de chats choisis.",
            "chat_types_all": "Tous les chats",
            "chat_types_none": "Choisissez au moins un type",
            "chat_type_private": "Privés",
            "chat_type_group": "Groupes",
            "chat_type_channel": "Canaux",
            "separator": "Séparateur",
            "enable_separator": "Activer le séparateur",
            "enable_separator_subtext": "Ajouter vos séparateurs personnalisés entre les mots.",
            "separator_set": "Jeu de séparateurs",
            "separator_count": "Nombre de séparateurs entre les mots",
            "separator_count_subtext": "Appuyez pour modifier.",
            "exceptions": "Exceptions",
            "ignore_emoji_only": "Ignorer les messages composés uniquement d’émojis",
            "ignore_emoji_only_subtext": "Ne pas modifier les messages composés uniquement d’un ou plusieurs émojis.",
            "exceptions_hint": "Les messages commençant ou se terminant par la valeur indiquée ne sont pas modifiés. Une valeur par ligne.",
            "ignore_special": "Ignorer code, commandes, mentions et liens",
            "ignore_special_subtext": "Commandes, @mentions, liens et code restent intacts. Le Markdown du masque n'est pas appliqué à ces messages.",
            "chat_menu": "Ajouter/retirer le chat à/de la liste d’exceptions",
            "chat_added": "Chat ajouté à la liste d’exceptions",
            "chat_removed": "Chat retiré de la liste d’exceptions",
            "mask_editor_title": "Réglages du masque",
            "mask_editor_hint": "Saisissez un masque. Utilisez [text] pour le texte du message, ou [text: lien] pour en faire un lien.",
            "custom_separator_title": "Personnalisé",
            "custom_separator_message": "Saisissez les séparateurs séparés par des virgules, par exemple :\n•, ·, —, ~, |",
            "save": "Enregistrer",
            "delete": "Supprimer",
            "cancel": "Annuler",
            "capture_custom_emoji": "Capturer un émoji Premium",
            "capture_enabled": "Capture d’émoji Premium activée : envoyez un message avec des émojis Premium",
            "capture_disabled": "Capture d’émoji Premium désactivée",
            "custom_emoji_hint": "Émoji Premium : le marqueur (id|🙂), où 🙂 est un émoji ordinaire affiché aux personnes sans Premium. Obtenez un marqueur avec « Capturer un émoji Premium » dans le menu du chat.",
            "mask_invalid": "Le masque doit contenir exactement un [text]",
            "mask_too_long": "Le masque est trop long : {n} caractères maximum",
            "mask_preview_sample": "Exemple de message",
            "mask_preview_invalid": "Masque invalide : exactement un [text] est requis",
            "separator_preview_words": "Exemple de texte pour l’aperçu",
            "exceptions_count": "Exceptions : {n}, chats : {m}",
            "configuration_import_cancelled": "Importation annulée",
            "import_configuration": "Importer",
            "export_configuration": "Exporter",
            "reset_configuration": "Restaurer les valeurs par défaut",
            "reset_to_plugin_defaults": "Ignorer les valeurs importées : restaurer les valeurs par défaut du plugin",
            "reset_to_plugin_defaults_unavailable": "Indisponible : cette configuration a été créée par le plugin ; la réinitialisation la remet dans son état de création.",
            "configurations": "Configurations",
            "active_configuration": "Configuration active",
            "add_configuration": "Créer une nouvelle configuration",
            "add_configuration_subtext": "Un ensemble de réglages distinct qui devient actif immédiatement.",
            "configuration_name_hint": "Nom de la configuration",
            "new_configuration_source_title": "Réglages de la nouvelle configuration",
            "new_configuration_source_message": "Sur quelle base démarrer ? Si rien n’est coché, les réglages par défaut sont utilisés.",
            "new_configuration_copy_current": "Copier les réglages de la configuration actuelle",
            "create": "Créer",
            "delete_configuration": "Supprimer la configuration",
            "delete_configuration_confirm": "Supprimer la configuration « {name} » ?",
            "no_inactive_configurations": "Aucune configuration inactive à supprimer",
            "imported_configuration": "Configuration importée",
            "rename_configuration": "Renommer la configuration",
            "rename_configuration_subtext": "Modifier le nom de la configuration actuelle.",
            "configuration_name_invalid": "Saisissez un nom de configuration unique.",
            "configuration_name_taken": "Une configuration portant ce nom existe déjà.",
            "configuration_deleted": "Configurations supprimées : {n}",
            "delete_configurations": "Supprimer des configurations",
            "delete_configurations_subtext": "Supprimer les configurations inactives. La configuration active est conservée.",
            "delete_configurations_select": "Sélectionnez les configurations inactives à supprimer.",
            "import_new_configuration_name": "Nom de la nouvelle configuration",
            "select_configuration": "Sélectionner la configuration",
            "select_configuration_subtext": "Vous pouvez sélectionner de une à six parties.",
            "config_mask": "Masque",
            "config_separator": "Séparateurs",
            "config_exceptions": "Exceptions et chats",
            "config_language": "Langue choisie",
            "config_media": "Médias",
            "media_attachment": "Médias",
            "enable_media_attachment": "Activer les médias",
            "enable_media_attachment_subtext": "Joindre automatiquement le fichier importé aux messages envoyés.",
            "media_file": "Fichier choisi",
            "media_file_none": "Aucun fichier sélectionné",
            "import_media": "Importer un média",
            "delete_media": "Supprimer le média",
            "delete_media_subtext": "Supprimer le fichier importé de Prefixfy.",
            "media_imported": "Média importé",
            "media_deleted": "Média supprimé",
            "media_import_failed": "Impossible d’importer le média",
            "media_delete_failed": "Impossible de supprimer le média",
            "apply": "Appliquer",
            "configuration_imported": "Configuration importée",
            "configuration_import_failed": "Impossible d’importer la configuration",
            "configuration_save_failed": "Impossible d’enregistrer la configuration actuelle",
            "configuration_exported": "Configuration exportée",
            "configuration_export_failed": "Impossible d’exporter la configuration",
            "configuration_export_destination_title": "Où exporter ?",
            "configuration_export_to_saved": "Messages enregistrés du compte actif",
            "configuration_export_to_device": "Stockage de l’appareil",
            "configuration_restored": "Valeurs sélectionnées restaurées",
            "configuration_nothing_selected": "Sélectionnez au moins une partie de la configuration",
            "config_found_title": "Configuration trouvée",
            "config_found_contains": "Contient",
            "config_import_as_new": "Importer comme nouvelle configuration",
            "config_found_import": "Importer",
            "config_file_open_failed": "Impossible d’ouvrir le fichier de configuration",
            "invalid_configuration": "Le fichier ne contient pas la configuration choisie ou son format est invalide.",
            "default_configuration_name": "Configuration par défaut",
            "configuration_n": "Configuration {n}",
            "operation_failed": "Échec de l’action",
            "text_style_subtext": "Ne modifie que le texte du message. Fancy, Bold, Gothic et Circled : alphabet latin uniquement ; L33T couvre aussi le cyrillique.",
            "enable_text_style": "Activer le style du texte",
            "configuration_short": "Choisir les parties",
            "edit_text_toggle": "Modification du texte",
            "edit_text_toggle_subtext": "Appliquer le style aux messages texte lors de leur modification.",
            "edit_media_toggle": "Modification des légendes",
            "edit_media_toggle_subtext": "Appliquer le style aux légendes des médias lors de leur modification.",
            "skip_once_on_edit": "« Ignorer une fois » à la modification",
            "skip_once_on_edit_subtext": "Si l’ignorance est armée, la prochaine modification dans ce chat reste sans style.",
            "conditional_masks": "Masques selon le contenu",
            "conditional_masks_hint": "Une règle par ligne : expression régulière => masque. Si le texte correspond, ce masque est utilisé ; la première ligne correspondante l’emporte. Chaque masque doit contenir exactement un [text].",
            "conditional_masks_count": "Règles : {n}",
            "conditional_masks_empty": "Si le texte contient…",
            "conditional_masks_format": "Ligne {n} : format attendu « expression => masque »",
            "md_quote": "Masque entier : citation",
            "config_schedule": "Liaisons de chats et planning",
            "schedule_err_date": "date invalide",
        },
        "pl": {
            "enable_plugin": "Włącz plugin",
            "enable_plugin_subtext": "Włączone: wszędzie oprócz czatów z listy. Wyłączone: tylko w czatach z listy.",
            "language": "Język",
            "update_required": "Wymagana aktualizacja",
            "update_required_subtext": "Zainstaluj Prefixfy {version} (oficjalna wersja). Do tego czasu plugin nie formatuje wiadomości.",
            "verify_required": "Weryfikacja nie powiodła się",
            "verify_required_subtext": "Nie udało się zweryfikować tej wersji Prefixfy. Do tego czasu plugin nie formatuje wiadomości; sprawdź połączenie z internetem.",
            "account_blocked": "Odmowa dostępu",
            "account_blocked_subtext": "Jedno z kont na tym urządzeniu znajduje się na czarnej liście Prefixfy. Plugin jest wyłączony.",
            "section_scope": "Gdzie działa",
            "plugin_language": "Język pluginu",
            "language_auto": "Automatyczne wykrywanie języka",
            "language_auto_subtext": "Używaj języka interfejsu Telegram. Wyłącz, aby wybrać język ręcznie.",
            "message": "Wiadomość",
            "message_subtext": "Używaj pluginu dla zwykłych wiadomości tekstowych.",
            "media": "Multimedia",
            "media_subtext": "Używaj pluginu dla podpisów do multimediów.",
            "edit_message": "Edycja wiadomości",
            "edit_message_subtext": "Stylizuj wiadomości podczas edycji. Tekst, który już ma maskę, pozostaje bez zmian.",
            "mask": "Maska",
            "mask_text": "Tekst maski",
            "text_style": "Styl tekstu",
            "skip_once_expired": "Pominięcie wygasło: następna wiadomość zostanie sformatowana",
            "empty_means_default": "Aby przywrócić domyślną wartość, wyczyść pole i dotknij „Zapisz”.",
            "markdown_style": "Styl Markdown",
            "markdown_style_subtext": "Znaczniki w masce lub formatowanie całej maski",
            "markdown_style_pick": "Styl",
            "md_manual": "Znaczniki ręczne",
            "md_bold": "Cała maska: pogrubienie",
            "md_italic": "Cała maska: kursywa",
            "md_strike": "Cała maska: przekreślenie",
            "md_spoiler": "Cała maska: spoiler",
            "md_mono": "Cała maska: monospace",
            "chat_config_menu": "Konfiguracja tego czatu",
            "chat_config_auto": "Główna (i harmonogram)",
            "chat_config_saved": "Zapisano konfigurację czatu",
            "chat_config_reset": "Ten czat używa konfiguracji głównej",
            "schedule": "Harmonogram konfiguracji",
            "schedule_empty": "Nie ustawiono",
            "schedule_count": "Reguł: {n}",
            "schedule_message": "Jedna reguła w wierszu: [data] [GG:MM-GG:MM] [dni] = nazwa konfiguracji.\nData: RRRR-MM-DD, DD.MM.RRRR lub DD.MM (co roku); zakres przez „..”. Bez godzin = cały dzień. Dni: mon-fri, sat,sun (bez dni = codziennie). Reguły z datą mają pierwszeństwo przed regułami dni tygodnia; wśród pozostałych działa pierwsza pasująca. Czat z własną konfiguracją pomija harmonogram. Zamiast godzin można podać porę dnia: rano (05–12), dzień (12–17), wieczór (17–23), noc (23–05) albo zakres, np. „rano-wieczór”.",
            "schedule_hint": "22:00-07:00 = Noc\n09:00-18:00 mon-fri = Praca\n31.12 = Święto\n2026-12-28..2027-01-10 = Urlop\nrano mon-fri = Praca\nnoc = Noc",
            "schedule_saved": "Zapisano harmonogram",
            "schedule_error": "Wiersz {n}: {reason}",
            "schedule_err_format": "oczekiwano „[data] [GG:MM-GG:MM] [dni] = konfiguracja”",
            "schedule_err_time": "nieprawidłowy czas",
            "schedule_err_days": "nieprawidłowe dni",
            "schedule_err_config": "brak konfiguracji „{name}”",
            "schedule_err_limit": "maksymalnie {n} reguł",
            "skip_once_menu": "Pomiń stylizację jeden raz",
            "skip_once_on": "Następna wiadomość zostanie wysłana bez stylizacji",
            "skip_once_off": "Anulowano pominięcie",
            "random_style": "Losowy styl",
            "random_style_subtext": "Wybiera losowy styl dla każdej wiadomości (oprócz tekstu do góry nogami).",
            "mask_rotation": "Rotacja masek",
            "mask_rotation_subtext": "Zamiast głównej maski używa masek z listy. Maska czatu ma pierwszeństwo.",
            "masks_list": "Lista masek",
            "masks_list_count": "Masek: {n}",
            "masks_list_empty": "Jedna maska w wierszu",
            "masks_list_hint": "Jedna maska w wierszu, każda z dokładnie jednym [text].",
            "masks_list_invalid": "Każda maska musi zawierać dokładnie jeden [text]",
            "masks_list_limit": "Maksymalnie {n} masek",
            "mask_tags_hint": "Tagi: [date], [time], [datetime], [chat], [id], [weekday], [year], [month], [day], [username], [count], [random_emoji], [hour], [minute], [second], [time12], [ampm], [daypart], [week], [yearday], [monthname], [weekday_short], [year_short], [timestamp], [tz], [chattype], [dice].",
            "mask_rotation_mode": "Kolejność rotacji",
            "rotation_random": "Losowa",
            "rotation_sequential": "Po kolei",
            "regex_exceptions": "Wyjątki regex",
            "regex_exceptions_hint": "Jedno wyrażenie regularne w wierszu. Wiadomość pasująca do któregokolwiek zostaje bez stylizacji.",
            "regex_exceptions_count": "Reguł: {n}",
            "regex_exceptions_empty": "Dla zaawansowanych",
            "regex_invalid": "Nieprawidłowe wyrażenie: {error}",
            "regex_limit": "Maksymalnie {n} wyrażeń, po {m} znaków każde",
            "chat_types": "Typy czatów",
            "chat_types_hint": "Stylizacja działa tylko w wybranych typach czatów.",
            "chat_types_all": "Wszystkie czaty",
            "chat_types_none": "Wybierz co najmniej jeden typ",
            "chat_type_private": "Prywatne",
            "chat_type_group": "Grupy",
            "chat_type_channel": "Kanały",
            "separator": "Separator",
            "enable_separator": "Włącz separator",
            "enable_separator_subtext": "Dodawaj własne separatory między słowami.",
            "separator_set": "Zestaw separatorów",
            "separator_count": "Liczba separatorów między słowami",
            "separator_count_subtext": "Dotknij, aby zmienić.",
            "exceptions": "Wyjątki",
            "ignore_emoji_only": "Ignoruj wiadomości złożone tylko z emoji",
            "ignore_emoji_only_subtext": "Nie zmieniaj wiadomości składających się wyłącznie z jednego lub kilku emoji.",
            "exceptions_hint": "Wiadomości zaczynające się lub kończące podaną wartością nie są zmieniane. Każda wartość w nowej linii.",
            "ignore_special": "Pomijaj kod, polecenia, wzmianki i linki",
            "ignore_special_subtext": "Polecenia, @wzmianki, linki i kod pozostają bez zmian. Markdown maski nie jest stosowany w takich wiadomościach.",
            "chat_menu": "Dodaj/usuń czat do/z listy wyjątków",
            "chat_added": "Czat dodany do listy wyjątków",
            "chat_removed": "Czat usunięty z listy wyjątków",
            "mask_editor_title": "Ustawienia maski",
            "mask_editor_hint": "Wpisz maskę. Użyj [text] dla treści wiadomości lub [text: link], aby zamienić ją w hiperłącze.",
            "custom_separator_title": "Własne",
            "custom_separator_message": "Wpisz separatory oddzielone przecinkami, na przykład:\n•, ·, —, ~, |",
            "save": "Zapisz",
            "delete": "Usuń",
            "cancel": "Anuluj",
            "capture_custom_emoji": "Przechwyć emoji Premium",
            "capture_enabled": "Przechwytywanie emoji Premium włączone: wyślij wiadomość z emoji Premium",
            "capture_disabled": "Przechwytywanie emoji Premium wyłączone",
            "custom_emoji_hint": "Emoji Premium: znacznik (id|🙂), gdzie 🙂 to zwykłe emoji widoczne dla osób bez Premium. Znacznik uzyskasz przez „Przechwyć emoji Premium” w menu czatu.",
            "mask_invalid": "Maska musi zawierać dokładnie jeden [text]",
            "mask_too_long": "Maska jest za długa: maksymalnie {n} znaków",
            "mask_preview_sample": "Przykładowa wiadomość",
            "mask_preview_invalid": "Nieprawidłowa maska: wymagany jest dokładnie jeden [text]",
            "separator_preview_words": "Przykładowy tekst do podglądu",
            "exceptions_count": "Wyjątki: {n}, czaty: {m}",
            "configuration_import_cancelled": "Import anulowany",
            "import_configuration": "Importuj",
            "export_configuration": "Eksportuj",
            "reset_configuration": "Przywróć ustawienia domyślne",
            "reset_to_plugin_defaults": "Ignoruj zaimportowane wartości: przywróć ustawienia domyślne wtyczki",
            "reset_to_plugin_defaults_unavailable": "Niedostępne: ta konfiguracja została utworzona przez wtyczkę, więc reset przywraca jej stan z chwili utworzenia.",
            "configurations": "Konfiguracje",
            "active_configuration": "Aktywna konfiguracja",
            "add_configuration": "Utwórz nową konfigurację",
            "add_configuration_subtext": "Osobny zestaw ustawień, który od razu staje się aktywny.",
            "configuration_name_hint": "Nazwa konfiguracji",
            "new_configuration_source_title": "Ustawienia nowej konfiguracji",
            "new_configuration_source_message": "Od czego zacząć? Jeśli nic nie zaznaczono, użyte zostaną ustawienia domyślne.",
            "new_configuration_copy_current": "Skopiuj ustawienia bieżącej konfiguracji",
            "create": "Utwórz",
            "delete_configuration": "Usuń konfigurację",
            "delete_configuration_confirm": "Usunąć konfigurację „{name}”?",
            "no_inactive_configurations": "Brak nieaktywnych konfiguracji do usunięcia",
            "imported_configuration": "Zaimportowana konfiguracja",
            "rename_configuration": "Zmień nazwę konfiguracji",
            "rename_configuration_subtext": "Zmień nazwę bieżącej konfiguracji.",
            "configuration_name_invalid": "Wpisz unikalną nazwę konfiguracji.",
            "configuration_name_taken": "Konfiguracja o tej nazwie już istnieje.",
            "configuration_deleted": "Usunięte konfiguracje: {n}",
            "delete_configurations": "Usuń konfiguracje",
            "delete_configurations_subtext": "Usuń nieaktywne konfiguracje. Aktywna zostanie zachowana.",
            "delete_configurations_select": "Wybierz nieaktywne konfiguracje do usunięcia.",
            "import_new_configuration_name": "Nazwa nowej konfiguracji",
            "select_configuration": "Wybierz konfigurację",
            "select_configuration_subtext": "Możesz wybrać od jednej do wszystkich sześciu części.",
            "config_mask": "Maska",
            "config_separator": "Separatory",
            "config_exceptions": "Wyjątki i czaty",
            "config_language": "Wybrany język",
            "config_media": "Multimedia",
            "media_attachment": "Multimedia",
            "enable_media_attachment": "Włącz multimedia",
            "enable_media_attachment_subtext": "Automatycznie dołączaj zaimportowany plik do wysyłanych wiadomości.",
            "media_file": "Wybrany plik",
            "media_file_none": "Nie wybrano pliku",
            "import_media": "Importuj multimedia",
            "delete_media": "Usuń multimedia",
            "delete_media_subtext": "Usuń zaimportowany plik z Prefixfy.",
            "media_imported": "Multimedia zaimportowane",
            "media_deleted": "Multimedia usunięte",
            "media_import_failed": "Nie udało się zaimportować multimediów",
            "media_delete_failed": "Nie udało się usunąć multimediów",
            "apply": "Zastosuj",
            "configuration_imported": "Konfiguracja zaimportowana",
            "configuration_import_failed": "Nie udało się zaimportować konfiguracji",
            "configuration_save_failed": "Nie udało się zapisać bieżącej konfiguracji",
            "configuration_exported": "Konfiguracja wyeksportowana",
            "configuration_export_failed": "Nie udało się wyeksportować konfiguracji",
            "configuration_export_destination_title": "Dokąd wyeksportować?",
            "configuration_export_to_saved": "Zapisane wiadomości aktywnego konta",
            "configuration_export_to_device": "Pamięć urządzenia",
            "configuration_restored": "Przywrócono wybrane wartości",
            "configuration_nothing_selected": "Wybierz co najmniej jedną część konfiguracji",
            "config_found_title": "Znaleziono konfigurację",
            "config_found_contains": "Zawiera",
            "config_import_as_new": "Importuj jako nową konfigurację",
            "config_found_import": "Importuj",
            "config_file_open_failed": "Nie udało się otworzyć pliku konfiguracji",
            "invalid_configuration": "Plik nie zawiera wybranej konfiguracji lub ma nieprawidłowy format.",
            "default_configuration_name": "Konfiguracja domyślna",
            "configuration_n": "Konfiguracja {n}",
            "operation_failed": "Nie udało się wykonać działania",
            "text_style_subtext": "Zmienia tylko tekst wiadomości. Fancy, Bold, Gothic i Circled działają tylko z łaciną; L33T obejmuje też cyrylicę.",
            "enable_text_style": "Włącz styl tekstu",
            "configuration_short": "Wybierz części konfiguracji",
            "edit_text_toggle": "Edycja tekstu",
            "edit_text_toggle_subtext": "Stylizuj zwykłe wiadomości tekstowe podczas edycji.",
            "edit_media_toggle": "Edycja podpisów",
            "edit_media_toggle_subtext": "Stylizuj podpisy do multimediów podczas edycji.",
            "skip_once_on_edit": "„Pomiń raz” przy edycji",
            "skip_once_on_edit_subtext": "Jeśli pominięcie jest włączone, następna edycja w tym czacie zostanie bez stylizacji.",
            "conditional_masks": "Maski według treści",
            "conditional_masks_hint": "Jedna reguła w wierszu: wyrażenie regularne => maska. Jeśli tekst pasuje, używana jest ta maska; działa pierwszy pasujący wiersz. Każda maska musi zawierać dokładnie jeden [text].",
            "conditional_masks_count": "Reguł: {n}",
            "conditional_masks_empty": "Jeśli tekst zawiera…",
            "conditional_masks_format": "Wiersz {n}: oczekiwano „wyrażenie => maska”",
            "md_quote": "Cała maska: cytat",
            "config_schedule": "Powiązania czatów i harmonogram",
            "schedule_err_date": "nieprawidłowa data",
        },
        "de": {
            "enable_plugin": "Plugin aktivieren",
            "enable_plugin_subtext": "Ein: überall außer in den gelisteten Chats. Aus: nur in den gelisteten Chats.",
            "language": "Sprache",
            "update_required": "Update erforderlich",
            "update_required_subtext": "Installiere Prefixfy {version} (offizieller Build). Bis dahin formatiert das Plugin keine Nachrichten.",
            "verify_required": "Überprüfung fehlgeschlagen",
            "verify_required_subtext": "Dieser Prefixfy-Build konnte nicht verifiziert werden. Bis dahin formatiert das Plugin keine Nachrichten; prüfe deine Internetverbindung.",
            "account_blocked": "Zugriff verweigert",
            "account_blocked_subtext": "Eines der Konten auf diesem Gerät steht auf der Prefixfy-Sperrliste. Das Plugin ist deaktiviert.",
            "section_scope": "Wo es wirkt",
            "plugin_language": "Plugin-Sprache",
            "language_auto": "Sprache automatisch erkennen",
            "language_auto_subtext": "Sprache der Telegram-Oberfläche verwenden. Ausschalten, um die Sprache manuell zu wählen.",
            "message": "Nachricht",
            "message_subtext": "Plugin für normale Textnachrichten verwenden.",
            "media": "Medien",
            "media_subtext": "Plugin für Medienbeschriftungen verwenden.",
            "edit_message": "Nachrichten bearbeiten",
            "edit_message_subtext": "Nachrichten beim Bearbeiten gestalten. Text, der die Maske bereits hat, bleibt unverändert.",
            "mask": "Maske",
            "mask_text": "Maskentext",
            "text_style": "Textstil",
            "skip_once_expired": "Überspringen abgelaufen: Die nächste Nachricht wird formatiert",
            "empty_means_default": "Zum Zurücksetzen auf den Standard das Feld leeren und „Speichern“ tippen.",
            "markdown_style": "Markdown-Stil",
            "markdown_style_subtext": "Marker in der Maske oder Formatierung der ganzen Maske",
            "markdown_style_pick": "Stil",
            "md_manual": "Manuelle Marker",
            "md_bold": "Ganze Maske: fett",
            "md_italic": "Ganze Maske: kursiv",
            "md_strike": "Ganze Maske: durchgestrichen",
            "md_spoiler": "Ganze Maske: Spoiler",
            "md_mono": "Ganze Maske: Monospace",
            "chat_config_menu": "Konfiguration für diesen Chat",
            "chat_config_auto": "Haupt (und Zeitplan)",
            "chat_config_saved": "Chat-Konfiguration gespeichert",
            "chat_config_reset": "Dieser Chat nutzt die Hauptkonfiguration",
            "schedule": "Konfigurations-Zeitplan",
            "schedule_empty": "Nicht festgelegt",
            "schedule_count": "Regeln: {n}",
            "schedule_message": "Eine Regel pro Zeile: [Datum] [HH:MM-HH:MM] [Tage] = Konfigurationsname.\nDatum: JJJJ-MM-TT, TT.MM.JJJJ oder TT.MM (jedes Jahr); Bereiche mit „..“. Ohne Uhrzeit = ganzer Tag. Tage: mon-fri, sat,sun (ohne Tage = täglich). Regeln mit Datum haben Vorrang vor Wochentagsregeln, unter den übrigen gilt die erste passende. Ein Chat mit eigener Konfiguration ignoriert den Zeitplan. Statt einer Uhrzeit kann eine Tageszeit stehen: Morgen (05–12), Tag (12–17), Abend (17–23), Nacht (23–05) oder ein Bereich wie „morgen-abend“.",
            "schedule_hint": "22:00-07:00 = Nacht\n09:00-18:00 mon-fri = Arbeit\n31.12 = Feiertag\n2026-12-28..2027-01-10 = Urlaub\nmorgen mon-fri = Arbeit\nnacht = Nacht",
            "schedule_saved": "Zeitplan gespeichert",
            "schedule_error": "Zeile {n}: {reason}",
            "schedule_err_format": "erwartet „[Datum] [HH:MM-HH:MM] [Tage] = Konfiguration“",
            "schedule_err_time": "ungültige Zeit",
            "schedule_err_days": "ungültige Tage",
            "schedule_err_config": "Konfiguration „{name}“ nicht gefunden",
            "schedule_err_limit": "höchstens {n} Regeln",
            "skip_once_menu": "Formatierung einmal überspringen",
            "skip_once_on": "Die nächste Nachricht wird ohne Formatierung gesendet",
            "skip_once_off": "Überspringen abgebrochen",
            "random_style": "Zufälliger Stil",
            "random_style_subtext": "Wählt für jede Nachricht einen zufälligen Stil (außer kopfstehendem Text).",
            "mask_rotation": "Masken-Rotation",
            "mask_rotation_subtext": "Statt der Hauptmaske werden die Masken aus der Liste verwendet. Die Chat-Maske hat Vorrang.",
            "masks_list": "Maskenliste",
            "masks_list_count": "Masken: {n}",
            "masks_list_empty": "Eine Maske pro Zeile",
            "masks_list_hint": "Eine Maske pro Zeile, jede mit genau einem [text].",
            "masks_list_invalid": "Jede Maske braucht genau ein [text]",
            "masks_list_limit": "Höchstens {n} Masken",
            "mask_tags_hint": "Tags: [date], [time], [datetime], [chat], [id], [weekday], [year], [month], [day], [username], [count], [random_emoji], [hour], [minute], [second], [time12], [ampm], [daypart], [week], [yearday], [monthname], [weekday_short], [year_short], [timestamp], [tz], [chattype], [dice].",
            "mask_rotation_mode": "Reihenfolge der Rotation",
            "rotation_random": "Zufällig",
            "rotation_sequential": "Der Reihe nach",
            "regex_exceptions": "Regex-Ausnahmen",
            "regex_exceptions_hint": "Ein regulärer Ausdruck pro Zeile. Nachrichten, die auf einen passen, bleiben unformatiert.",
            "regex_exceptions_count": "Regeln: {n}",
            "regex_exceptions_empty": "Für fortgeschrittene Nutzer",
            "regex_invalid": "Ungültiger Ausdruck: {error}",
            "regex_limit": "Höchstens {n} Ausdrücke mit je {m} Zeichen",
            "chat_types": "Chat-Typen",
            "chat_types_hint": "Die Formatierung wirkt nur in den gewählten Chat-Typen.",
            "chat_types_all": "Alle Chats",
            "chat_types_none": "Wähle mindestens einen Typ",
            "chat_type_private": "Private Chats",
            "chat_type_group": "Gruppen",
            "chat_type_channel": "Kanäle",
            "separator": "Trennzeichen",
            "enable_separator": "Trennzeichen aktivieren",
            "enable_separator_subtext": "Eigene Trennzeichen zwischen Wörtern einfügen.",
            "separator_set": "Trennzeichen-Set",
            "separator_count": "Trennzeichen zwischen Wörtern",
            "separator_count_subtext": "Zum Ändern tippen.",
            "exceptions": "Ausnahmen",
            "ignore_emoji_only": "Nachrichten nur aus Emojis ignorieren",
            "ignore_emoji_only_subtext": "Nachrichten, die nur aus einem oder mehreren Emojis bestehen, nicht ändern.",
            "exceptions_hint": "Nachrichten, die mit dem angegebenen Wert beginnen oder enden, werden nicht geändert. Ein Wert pro Zeile.",
            "ignore_special": "Code, Befehle, Erwähnungen und Links auslassen",
            "ignore_special_subtext": "Befehle, @Erwähnungen, Links und Code bleiben unverändert. Das Markdown der Maske wird auf solche Nachrichten nicht angewendet.",
            "chat_menu": "Chat zur Ausnahmeliste hinzufügen/entfernen",
            "chat_added": "Chat zur Ausnahmeliste hinzugefügt",
            "chat_removed": "Chat aus der Ausnahmeliste entfernt",
            "mask_editor_title": "Maskeneinstellungen",
            "mask_editor_hint": "Maske eingeben. Verwende [text] für den Nachrichtentext oder [text: Link], um ihn zu einem Link zu machen.",
            "custom_separator_title": "Eigene",
            "custom_separator_message": "Trennzeichen durch Kommas getrennt eingeben, zum Beispiel:\n•, ·, —, ~, |",
            "save": "Speichern",
            "delete": "Löschen",
            "cancel": "Abbrechen",
            "capture_custom_emoji": "Premium-Emoji erfassen",
            "capture_enabled": "Premium-Emoji-Erfassung ist an: Sende eine Nachricht mit Premium-Emoji",
            "capture_disabled": "Premium-Emoji-Erfassung ist aus",
            "custom_emoji_hint": "Premium-Emoji: der Marker (id|🙂), wobei 🙂 ein normales Emoji für Nutzer ohne Premium ist. Einen Marker erhältst du über „Premium-Emoji erfassen“ im Chat-Menü.",
            "mask_invalid": "Die Maske muss genau einen [text] enthalten",
            "mask_too_long": "Die Maske ist zu lang: höchstens {n} Zeichen",
            "mask_preview_sample": "Beispielnachricht",
            "mask_preview_invalid": "Maske ungültig: genau ein [text] erforderlich",
            "separator_preview_words": "Beispieltext für die Vorschau",
            "exceptions_count": "Ausnahmen: {n}, Chats: {m}",
            "configuration_import_cancelled": "Import abgebrochen",
            "import_configuration": "Importieren",
            "export_configuration": "Exportieren",
            "reset_configuration": "Standardwerte wiederherstellen",
            "reset_to_plugin_defaults": "Importierte Werte ignorieren: Standardwerte des Plugins wiederherstellen",
            "reset_to_plugin_defaults_unavailable": "Nicht verfügbar: Diese Konfiguration wurde vom Plugin erstellt; ein Zurücksetzen stellt den Zustand bei der Erstellung wieder her.",
            "configurations": "Konfigurationen",
            "active_configuration": "Aktive Konfiguration",
            "add_configuration": "Neue Konfiguration erstellen",
            "add_configuration_subtext": "Ein separater Satz von Einstellungen, der sofort aktiv wird.",
            "configuration_name_hint": "Name der Konfiguration",
            "new_configuration_source_title": "Einstellungen der neuen Konfiguration",
            "new_configuration_source_message": "Wovon soll sie ausgehen? Ist nichts markiert, werden die Standardeinstellungen verwendet.",
            "new_configuration_copy_current": "Einstellungen der aktuellen Konfiguration kopieren",
            "create": "Erstellen",
            "delete_configuration": "Konfiguration löschen",
            "delete_configuration_confirm": "Konfiguration „{name}“ löschen?",
            "no_inactive_configurations": "Keine inaktiven Konfigurationen zum Löschen",
            "imported_configuration": "Importierte Konfiguration",
            "rename_configuration": "Konfiguration umbenennen",
            "rename_configuration_subtext": "Den Namen der aktuellen Konfiguration ändern.",
            "configuration_name_invalid": "Gib einen eindeutigen Konfigurationsnamen ein.",
            "configuration_name_taken": "Eine Konfiguration mit diesem Namen existiert bereits.",
            "configuration_deleted": "Gelöschte Konfigurationen: {n}",
            "delete_configurations": "Konfigurationen löschen",
            "delete_configurations_subtext": "Inaktive Konfigurationen löschen. Die aktive bleibt erhalten.",
            "delete_configurations_select": "Wähle die inaktiven Konfigurationen zum Löschen aus.",
            "import_new_configuration_name": "Name der neuen Konfiguration",
            "select_configuration": "Konfiguration auswählen",
            "select_configuration_subtext": "Du kannst einen bis alle sechs Teile auswählen.",
            "config_mask": "Maske",
            "config_separator": "Trennzeichen",
            "config_exceptions": "Ausnahmen und Chats",
            "config_language": "Gewählte Sprache",
            "config_media": "Medien",
            "media_attachment": "Medien",
            "enable_media_attachment": "Medien aktivieren",
            "enable_media_attachment_subtext": "Die importierte Datei automatisch an ausgehende Nachrichten anhängen.",
            "media_file": "Gewählte Datei",
            "media_file_none": "Keine Datei ausgewählt",
            "import_media": "Medien importieren",
            "delete_media": "Medien löschen",
            "delete_media_subtext": "Die importierte Datei aus Prefixfy löschen.",
            "media_imported": "Medien importiert",
            "media_deleted": "Medien gelöscht",
            "media_import_failed": "Medien konnten nicht importiert werden",
            "media_delete_failed": "Medien konnten nicht gelöscht werden",
            "apply": "Anwenden",
            "configuration_imported": "Konfiguration importiert",
            "configuration_import_failed": "Konfiguration konnte nicht importiert werden",
            "configuration_save_failed": "Die aktuelle Konfiguration konnte nicht gespeichert werden",
            "configuration_exported": "Konfiguration exportiert",
            "configuration_export_failed": "Konfiguration konnte nicht exportiert werden",
            "configuration_export_destination_title": "Wohin exportieren?",
            "configuration_export_to_saved": "Gespeicherte Nachrichten des aktiven Kontos",
            "configuration_export_to_device": "Gerätespeicher",
            "configuration_restored": "Ausgewählte Werte wiederhergestellt",
            "configuration_nothing_selected": "Wähle mindestens einen Konfigurationsteil aus",
            "config_found_title": "Konfiguration gefunden",
            "config_found_contains": "Enthält",
            "config_import_as_new": "Als neue Konfiguration importieren",
            "config_found_import": "Importieren",
            "config_file_open_failed": "Konfigurationsdatei konnte nicht geöffnet werden",
            "invalid_configuration": "Die Datei enthält die gewählte Konfiguration nicht oder hat ein ungültiges Format.",
            "default_configuration_name": "Standardkonfiguration",
            "configuration_n": "Konfiguration {n}",
            "operation_failed": "Aktion fehlgeschlagen",
            "text_style_subtext": "Ändert nur den Nachrichtentext. Fancy, Bold, Gothic und Circled nur mit lateinischen Buchstaben; L33T erfasst auch Kyrillisch.",
            "enable_text_style": "Textstil aktivieren",
            "configuration_short": "Konfigurationsteile wählen",
            "edit_text_toggle": "Text bearbeiten",
            "edit_text_toggle_subtext": "Normale Textnachrichten beim Bearbeiten gestalten.",
            "edit_media_toggle": "Beschriftungen bearbeiten",
            "edit_media_toggle_subtext": "Medienbeschriftungen beim Bearbeiten gestalten.",
            "skip_once_on_edit": "„Einmal überspringen“ beim Bearbeiten",
            "skip_once_on_edit_subtext": "Ist das Überspringen aktiv, bleibt die nächste Bearbeitung in diesem Chat unformatiert.",
            "conditional_masks": "Masken nach Inhalt",
            "conditional_masks_hint": "Eine Regel pro Zeile: regulärer Ausdruck => Maske. Passt der Text zum Ausdruck, wird diese Maske verwendet; die erste passende Zeile gilt. Jede Maske braucht genau ein [text].",
            "conditional_masks_count": "Regeln: {n}",
            "conditional_masks_empty": "Wenn der Text … enthält",
            "conditional_masks_format": "Zeile {n}: erwartet „Ausdruck => Maske“",
            "md_quote": "Ganze Maske: Zitat",
            "config_schedule": "Chat-Zuordnungen und Zeitplan",
            "schedule_err_date": "ungültiges Datum",
        },
        "uk": {
            "enable_plugin": "Увімкнути плагін",
            "enable_plugin_subtext": "Увімкнено: усюди, крім чатів зі списку. Вимкнено: лише у чатах зі списку.",
            "language": "Мова",
            "update_required": "Потрібне оновлення",
            "update_required_subtext": "Встановіть Prefixfy {version} (офіційна збірка). Доти плагін не оформлює повідомлення.",
            "verify_required": "Перевірку не пройдено",
            "verify_required_subtext": "Не вдалося підтвердити цю збірку Prefixfy. Доти плагін не оформлює повідомлення; перевірте підключення до інтернету.",
            "account_blocked": "Доступ заборонено",
            "account_blocked_subtext": "Один з акаунтів на цьому пристрої внесено до чорного списку Prefixfy. Плагін не працює.",
            "section_scope": "Де працює",
            "plugin_language": "Мова плагіна",
            "language_auto": "Автовизначення мови",
            "language_auto_subtext": "Використовувати мову інтерфейсу Telegram. Вимкніть, щоб вибрати мову вручну.",
            "message": "Повідомлення",
            "message_subtext": "Використовувати плагін для звичайних текстових повідомлень.",
            "media": "Медіа",
            "media_subtext": "Використовувати плагін для підписів до медіа.",
            "edit_message": "Редагування повідомлень",
            "edit_message_subtext": "Оформлювати повідомлення під час редагування. Уже оформлений текст не змінюється.",
            "mask": "Маска",
            "mask_text": "Текст маски",
            "text_style": "Стиль тексту",
            "skip_once_expired": "Пропуск оформлення минув: наступне повідомлення буде оформлено",
            "empty_means_default": "Щоб повернути значення за замовчуванням, очистіть поле й натисніть «Зберегти».",
            "markdown_style": "Стиль Markdown",
            "markdown_style_subtext": "Маркери в масці або оформлення всієї маски",
            "markdown_style_pick": "Стиль",
            "md_manual": "Маркери вручну",
            "md_bold": "Уся маска: жирний",
            "md_italic": "Уся маска: курсив",
            "md_strike": "Уся маска: закреслений",
            "md_spoiler": "Уся маска: спойлер",
            "md_mono": "Уся маска: моно",
            "chat_config_menu": "Конфігурація для цього чату",
            "chat_config_auto": "Основна (і розклад)",
            "chat_config_saved": "Конфігурацію чату збережено",
            "chat_config_reset": "Чат використовує основну конфігурацію",
            "schedule": "Розклад конфігурацій",
            "schedule_empty": "Не задано",
            "schedule_count": "Правил: {n}",
            "schedule_message": "Одне правило в рядку: [дата] [ГГ:ХХ-ГГ:ХХ] [дні] = назва конфігурації.\nДата: РРРР-ММ-ДД, ДД.ММ.РРРР або ДД.ММ (щороку); діапазон через «..». Без часу — увесь день. Дні: пн-пт, сб,нд або mon-fri; без днів — щодня. Правила з датою важливіші за правила за днями тижня, з решти діє перше підходяще. Чат зі своєю конфігурацією розклад не змінює. Замість часу можна вказати частину доби: ранок (05–12), день (12–17), вечір (17–23), ніч (23–05) або діапазон «ранок-вечір».",
            "schedule_hint": "22:00-07:00 = Нічна\n09:00-18:00 пн-пт = Робоча\n31.12 = Святкова\n2026-12-28..2027-01-10 = Відпустка\nранок пн-пт = Робоча\nніч = Нічна",
            "schedule_saved": "Розклад збережено",
            "schedule_error": "Рядок {n}: {reason}",
            "schedule_err_format": "очікується «[дата] [ГГ:ХХ-ГГ:ХХ] [дні] = конфігурація»",
            "schedule_err_time": "неправильний час",
            "schedule_err_days": "неправильні дні",
            "schedule_err_config": "немає конфігурації «{name}»",
            "schedule_err_limit": "не більше {n} правил",
            "skip_once_menu": "Пропустити оформлення один раз",
            "skip_once_on": "Наступне повідомлення піде без оформлення",
            "skip_once_off": "Пропуск скасовано",
            "random_style": "Випадковий стиль",
            "random_style_subtext": "Для кожного повідомлення обирається випадковий стиль (крім перевернутого тексту).",
            "mask_rotation": "Ротація масок",
            "mask_rotation_subtext": "Замість основної маски беруться маски зі списку. Маска чату важливіша.",
            "masks_list": "Список масок",
            "masks_list_count": "Масок: {n}",
            "masks_list_empty": "По одній масці в рядку",
            "masks_list_hint": "По одній масці в рядку, у кожній рівно один [text].",
            "masks_list_invalid": "У кожній масці має бути рівно один [text]",
            "masks_list_limit": "Не більше {n} масок",
            "mask_tags_hint": "Теги: [date], [time], [datetime], [chat], [id], [weekday], [year], [month], [day], [username], [count], [random_emoji], [hour], [minute], [second], [time12], [ampm], [daypart], [week], [yearday], [monthname], [weekday_short], [year_short], [timestamp], [tz], [chattype], [dice].",
            "mask_rotation_mode": "Порядок ротації",
            "rotation_random": "Випадкова",
            "rotation_sequential": "По колу",
            "regex_exceptions": "Regex-винятки",
            "regex_exceptions_hint": "По одному регулярному виразу в рядку. Повідомлення, що підходить під будь-який із них, лишається без оформлення.",
            "regex_exceptions_count": "Правил: {n}",
            "regex_exceptions_empty": "Для досвідчених користувачів",
            "regex_invalid": "Некоректний вираз: {error}",
            "regex_limit": "Не більше {n} виразів, до {m} символів кожен",
            "chat_types": "Типи чатів",
            "chat_types_hint": "Оформлення працює лише у вибраних типах чатів.",
            "chat_types_all": "Усі чати",
            "chat_types_none": "Виберіть хоча б один тип",
            "chat_type_private": "Особисті",
            "chat_type_group": "Групи",
            "chat_type_channel": "Канали",
            "separator": "Роздільник",
            "enable_separator": "Увімкнути роздільник",
            "enable_separator_subtext": "Додавати власні роздільники між словами.",
            "separator_set": "Набір роздільників",
            "separator_count": "Кількість роздільників між словами",
            "separator_count_subtext": "Натисніть, щоб змінити.",
            "exceptions": "Винятки",
            "ignore_emoji_only": "Ігнорувати повідомлення лише з емодзі",
            "ignore_emoji_only_subtext": "Не змінювати повідомлення, що складаються лише з одного або кількох емодзі.",
            "exceptions_hint": "Повідомлення, що починаються або закінчуються вказаним значенням, не змінюються. Кожне значення — з нового рядка.",
            "ignore_special": "Не чіпати код, команди, згадки та посилання",
            "ignore_special_subtext": "Команди, @згадки, посилання та код лишаються як є. У таких повідомленнях Markdown маски не застосовується.",
            "chat_menu": "Додати/видалити чат до/зі списку винятків",
            "chat_added": "Чат додано до списку винятків",
            "chat_removed": "Чат видалено зі списку винятків",
            "mask_editor_title": "Налаштування маски",
            "mask_editor_hint": "Введіть маску. Використовуйте [text] для тексту повідомлення або [text: посилання], щоб зробити його гіперпосиланням.",
            "custom_separator_title": "Власний",
            "custom_separator_message": "Введіть роздільники через кому, наприклад:\n•, ·, —, ~, |",
            "save": "Зберегти",
            "delete": "Видалити",
            "cancel": "Скасувати",
            "capture_custom_emoji": "Захоплення Premium Emoji",
            "capture_enabled": "Захоплення Premium Emoji увімкнено: надішліть повідомлення з Premium Emoji",
            "capture_disabled": "Захоплення Premium Emoji вимкнено",
            "custom_emoji_hint": "Premium Emoji: маркер (id|🙂), де 🙂 — звичайний емодзі для тих, у кого немає Premium. Отримати маркер можна через пункт «Захоплення Premium Emoji» у меню чату.",
            "mask_invalid": "Маска має містити рівно один [text]",
            "mask_too_long": "Маска задовга: не більше {n} символів",
            "mask_preview_sample": "Приклад повідомлення",
            "mask_preview_invalid": "Маску пошкоджено: потрібен рівно один [text]",
            "separator_preview_words": "Приклад тексту для перегляду",
            "exceptions_count": "Винятків: {n}, чатів: {m}",
            "configuration_import_cancelled": "Імпорт скасовано",
            "import_configuration": "Імпортувати",
            "export_configuration": "Експортувати",
            "reset_configuration": "Відновити значення за замовчуванням",
            "reset_to_plugin_defaults": "Ігнорувати імпортовані значення: повернути налаштування плагіна за замовчуванням",
            "reset_to_plugin_defaults_unavailable": "Недоступно: конфігурацію створено плагіном, тому скидання повертає її до стану на момент створення.",
            "configurations": "Конфігурації",
            "active_configuration": "Активна конфігурація",
            "add_configuration": "Створити нову конфігурацію",
            "add_configuration_subtext": "Окремий набір налаштувань, який одразу стане активним.",
            "configuration_name_hint": "Назва конфігурації",
            "new_configuration_source_title": "Налаштування нової конфігурації",
            "new_configuration_source_message": "Що взяти за основу? Якщо нічого не позначено, будуть налаштування за замовчуванням.",
            "new_configuration_copy_current": "Скопіювати налаштування поточної конфігурації",
            "create": "Створити",
            "delete_configuration": "Видалити конфігурацію",
            "delete_configuration_confirm": "Видалити конфігурацію «{name}»?",
            "no_inactive_configurations": "Немає неактивних конфігурацій для видалення",
            "imported_configuration": "Імпортована конфігурація",
            "rename_configuration": "Перейменувати конфігурацію",
            "rename_configuration_subtext": "Змінити назву поточної конфігурації.",
            "configuration_name_invalid": "Введіть унікальну назву конфігурації.",
            "configuration_name_taken": "Конфігурація з такою назвою вже існує.",
            "configuration_deleted": "Видалено конфігурацій: {n}",
            "delete_configurations": "Видалити конфігурації",
            "delete_configurations_subtext": "Видалити неактивні конфігурації. Активна залишиться.",
            "delete_configurations_select": "Виберіть неактивні конфігурації, які потрібно видалити.",
            "import_new_configuration_name": "Назва нової конфігурації",
            "select_configuration": "Виберіть конфігурацію",
            "select_configuration_subtext": "Можна вибрати від однієї до шести частин.",
            "config_mask": "Маска",
            "config_separator": "Роздільники",
            "config_exceptions": "Винятки та чати",
            "config_language": "Вибрана мова",
            "config_media": "Медіа",
            "media_attachment": "Медіа",
            "enable_media_attachment": "Увімкнути медіа",
            "enable_media_attachment_subtext": "Автоматично додавати імпортований файл до надсилань.",
            "media_file": "Вибраний файл",
            "media_file_none": "Файл не вибрано",
            "import_media": "Імпортувати медіа",
            "delete_media": "Видалити медіа",
            "delete_media_subtext": "Видалити імпортований файл із Prefixfy.",
            "media_imported": "Медіа імпортовано",
            "media_deleted": "Медіа видалено",
            "media_import_failed": "Не вдалося імпортувати медіа",
            "media_delete_failed": "Не вдалося видалити медіа",
            "apply": "Застосувати",
            "configuration_imported": "Конфігурацію імпортовано",
            "configuration_import_failed": "Не вдалося імпортувати конфігурацію",
            "configuration_save_failed": "Не вдалося зберегти поточну конфігурацію",
            "configuration_exported": "Конфігурацію експортовано",
            "configuration_export_failed": "Не вдалося експортувати конфігурацію",
            "configuration_export_destination_title": "Куди експортувати?",
            "configuration_export_to_saved": "До Збереженого активного акаунта",
            "configuration_export_to_device": "У пам’ять пристрою",
            "configuration_restored": "Вибрані значення відновлено",
            "configuration_nothing_selected": "Виберіть принаймні одну частину конфігурації",
            "config_found_title": "Знайдено конфігурацію",
            "config_found_contains": "Містить",
            "config_import_as_new": "Імпортувати як нову конфігурацію",
            "config_found_import": "Імпортувати",
            "config_file_open_failed": "Не вдалося відкрити файл конфігурації",
            "invalid_configuration": "Файл не містить вибраної конфігурації або має неправильний формат.",
            "default_configuration_name": "Конфігурація за замовчуванням",
            "configuration_n": "Конфігурація {n}",
            "operation_failed": "Не вдалося виконати дію",
            "text_style_subtext": "Змінює лише текст повідомлення. Fancy, Bold, Gothic і Circled — лише латиниця; L33T охоплює й кирилицю.",
            "enable_text_style": "Увімкнути стиль тексту",
            "configuration_short": "Вибрати частини конфігурації",
            "edit_text_toggle": "Правка тексту",
            "edit_text_toggle_subtext": "Оформлювати звичайні текстові повідомлення під час редагування.",
            "edit_media_toggle": "Правка підписів",
            "edit_media_toggle_subtext": "Оформлювати підписи до медіа під час редагування.",
            "skip_once_on_edit": "«Пропустити один раз» під час правки",
            "skip_once_on_edit_subtext": "Якщо пропуск увімкнено, наступна правка в цьому чаті залишиться без оформлення.",
            "conditional_masks": "Маски за вмістом",
            "conditional_masks_hint": "По одному правилу в рядку: регулярний вираз => маска. Якщо текст підходить під вираз, береться ця маска; діє перший підходящий рядок. У кожній масці рівно один [text].",
            "conditional_masks_count": "Правил: {n}",
            "conditional_masks_empty": "Якщо в тексті є…",
            "conditional_masks_format": "Рядок {n}: очікується «вираз => маска»",
            "md_quote": "Уся маска: цитата",
            "config_schedule": "Прив’язки чатів і розклад",
            "schedule_err_date": "неправильна дата",
        },
    }

    SUPPORTED_AUTO = frozenset(("ru", "ja", "ko", "ar", "fr", "pl", "de", "uk", "en"))
    LANGUAGE_ALIASES = {
        "ua": "uk", "jp": "ja", "kr": "ko",
        "russian": "ru", "english": "en", "japanese": "ja", "korean": "ko", "arabic": "ar",
        "french": "fr", "polish": "pl", "german": "de", "deutsch": "de", "ukrainian": "uk",
    }
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
        return "en" if readable else None

    def language(self) -> str:
        forced = LANGUAGE_MODES[self.plugin.settings.language_index()]
        if forced and language_enabled(forced):
            return forced
        now = time.monotonic()
        if self._auto_language is None or now - self._auto_checked > self.AUTO_LANGUAGE_TTL:
            detected = self._detect_interface_language()
            self._auto_checked = now
            if detected is not None:
                self._auto_language = detected
            elif self._auto_language is None:
                self._auto_language = "en"
        return self._auto_language

    def tr(self, key: str, **kwargs) -> str:
        table = self.STRINGS.get(self.language(), self.STRINGS["en"])
        value = table.get(key) or self.STRINGS["en"].get(key, key)
        if kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, IndexError, ValueError):
                pass
        return value

    def language_items(self) -> List[str]:
        names = self.LANGUAGE_ITEMS.get(self.language(), self.LANGUAGE_ITEMS["en"])
        return [names[index - 1] for index in enabled_language_indices()]

    def invalidate(self):
        self._auto_language = None
        self._auto_checked = 0.0


_NEW_STRINGS = {
    "en": {
        "style_translit": "Transliterate Cyrillic",
        "style_translit_subtext": "Latin-only styles will also work with Russian and Ukrainian text.",
        "style_words": "Style only these words",
        "style_words_hint": "One word per line. If the list is empty, the style applies to the whole text.",
        "style_words_count": "Words: {n}",
        "style_words_empty": "Whole text",
        "style_words_limit": "At most {n} words",
        "tag_lines": "Lines for [line]",
        "tag_lines_hint": "One line per row. The [line] tag inserts a random one (up to 64 characters each).",
        "tag_lines_count": "Lines: {n}",
        "tag_lines_empty": "No lines yet",
        "tag_lines_limit": "At most {n} lines",
        "tags_more": "[reply] \u2014 name of the person you reply to; [chatcount] \u2014 your message number in this chat; [battery] \u2014 battery level; [moon] \u2014 moon phase; [line] \u2014 random line from your list; [since:2026-12-31] / [until:2026-12-31] \u2014 days passed / left.",
    },
    "ru": {
        "style_translit": "Транслитерировать кириллицу",
        "style_translit_subtext": "Латинские стили будут работать и с русским, и с украинским текстом.",
        "style_words": "Стиль только для слов",
        "style_words_hint": "Одно слово в строке. Если список пуст, стиль применяется ко всему тексту.",
        "style_words_count": "Слов: {n}",
        "style_words_empty": "Весь текст",
        "style_words_limit": "Не больше {n} слов",
        "tag_lines": "Строки для [line]",
        "tag_lines_hint": "Одна строка в ряд. Тег [line] подставит случайную (до 64 символов каждая).",
        "tag_lines_count": "Строк: {n}",
        "tag_lines_empty": "Строк пока нет",
        "tag_lines_limit": "Не больше {n} строк",
        "tags_more": "[reply] \u2014 имя того, кому отвечаете; [chatcount] \u2014 номер вашего сообщения в этом чате; [battery] \u2014 заряд батареи; [moon] \u2014 фаза луны; [line] \u2014 случайная строка из списка; [since:2026-12-31] / [until:2026-12-31] \u2014 дней прошло / осталось.",
    },
    "uk": {
        "style_translit": "Транслітерувати кирилицю",
        "style_translit_subtext": "Латинські стилі працюватимуть і з російським, і з українським текстом.",
        "style_words": "Стиль лише для слів",
        "style_words_hint": "Одне слово в рядку. Якщо список порожній, стиль застосовується до всього тексту.",
        "style_words_count": "Слів: {n}",
        "style_words_empty": "Весь текст",
        "style_words_limit": "Не більше {n} слів",
        "tag_lines": "Рядки для [line]",
        "tag_lines_hint": "Один рядок у ряд. Тег [line] підставить випадковий (до 64 символів кожен).",
        "tag_lines_count": "Рядків: {n}",
        "tag_lines_empty": "Рядків поки немає",
        "tag_lines_limit": "Не більше {n} рядків",
        "tags_more": "[reply] \u2014 імʼя того, кому відповідаєте; [chatcount] \u2014 номер вашого повідомлення в цьому чаті; [battery] \u2014 заряд батареї; [moon] \u2014 фаза місяця; [line] \u2014 випадковий рядок зі списку; [since:2026-12-31] / [until:2026-12-31] \u2014 днів минуло / залишилось.",
    },
}
for _code, _table in LocalizationManager.STRINGS.items():
    _extra = _NEW_STRINGS.get(_code, _NEW_STRINGS["en"])
    _base = _NEW_STRINGS["en"]
    for _key, _value in _base.items():
        _table.setdefault(_key, _extra.get(_key, _value))
    if _table.get("mask_tags_hint"):
        _table["mask_tags_hint"] = _table["mask_tags_hint"] + "\n" + _extra.get("tags_more", _base["tags_more"])


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


MASK_TOKEN_RE = re.compile(r"\[text(?:[ \t]*:[ \t]*([^\[\]\r\n]*?))?[ \t]*\]")
_LINK_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:(?://|[^\s/])")


def normalize_link(raw) -> Optional[str]:
    link = as_text(raw).strip()
    if not link or any(ch.isspace() for ch in link):
        return None
    if link.startswith("@") and len(link) > 1:
        return "https://t.me/" + link[1:]
    if not _LINK_SCHEME_RE.match(link):
        link = "https://" + link
    return link


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
RANDOM_STYLE_POOL = tuple(style for style in range(TEXT_STYLE_COUNT) if style not in _RANDOM_EXCLUDED)


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
    atoms: List[Tuple[str, str]] = []
    upper = False
    convert = style == STYLE_TRANSLIT or (translit and style not in _CYRILLIC_STYLES)
    index, size = 0, len(text)
    while index < size:
        end = protected.get(index)
        if end is not None:
            atoms.append((text[index:end], text[index:end]))
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


def parse_chat_ids(raw) -> frozenset:
    result = set()
    for token in re.split(r"[\s,;]+", as_text(raw)):
        if not token:
            continue
        try:
            result.add(int(token))
        except ValueError:
            continue
    return frozenset(result)


def parse_chat_type_rules(raw) -> frozenset:
    parts = {part.strip().lower() for part in as_text(raw).split(",")}
    kinds = frozenset(part for part in parts if part in CHAT_KINDS)
    return frozenset(CHAT_KINDS) if not kinds or "all" in parts else kinds


def dump_chat_type_rules(kinds) -> str:
    chosen = [kind for kind in CHAT_KINDS if kind in set(kinds)]
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


def _regex_ambiguous_body(items) -> bool:
    carriers, delimiter = 0, False
    for op, av in _regex_seq(items):
        if op in (_re_constants.AT, _re_constants.ASSERT, _re_constants.ASSERT_NOT):
            continue
        if _regex_is_repeat(op):
            if av[1] == _re_constants.MAXREPEAT or _regex_has_unbounded(av[2]):
                carriers += 1
            elif av[0] > 0:
                delimiter = True
        elif op == _re_constants.SUBPATTERN:
            if _regex_has_unbounded(av[-1]):
                carriers += 1
            else:
                delimiter = True
        elif op == _re_constants.BRANCH:
            if any(_regex_has_unbounded(branch) for branch in av[1]):
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


@lru_cache(maxsize=256)
def regex_is_safe(pattern: str) -> bool:
    if _re_parser is None:
        return True
    try:
        tree = _re_parser.parse(pattern)
        return _regex_count_unbounded(tree) <= MAX_REGEX_REPEATS and not _regex_nested_repeat(tree)
    except Exception:
        return True


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
    return _TAG_UNSAFE_RE.sub(" ", as_text(value)).strip()[:TAG_VALUE_LIMIT]


CHAT_CONFIGS_KEY = "Prefixfy_chat_configs"
SCHEDULE_KEY = "Prefixfy_schedule"
MAX_SCHEDULE_RULES = 24
_SCHEDULE_DAYS = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
    "пн": 0, "вт": 1, "ср": 2, "чт": 3, "пт": 4, "сб": 5, "вс": 6, "нд": 6,
    "1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6,
}
_SCHEDULE_DATE = r"(\d{4}-\d{2}-\d{2}|\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})"
_SCHEDULE_LEFT_RE = re.compile(
    r"^(?:" + _SCHEDULE_DATE + r"(?:\s*\.\.\s*" + _SCHEDULE_DATE + r")?\s*)?"
    r"(?:(\d{1,2}):(\d{2})\s*[-–—]\s*(\d{1,2}):(\d{2})"
    r"|(" + _DAYPART_PATTERN + r")(?:\s*[-–—]\s*(" + _DAYPART_PATTERN + r"))?(?![^\W\d_]))?(.*)$",
    re.IGNORECASE,
)


def parse_chat_configs(raw) -> Dict[str, str]:
    try:
        data = json.loads(as_text(raw).strip() or "{}")
    except (ValueError, RecursionError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): v for k, v in data.items() if str(k).lstrip("-").isdigit() and isinstance(v, str) and v}


def dump_chat_configs(mapping: Dict[str, str]) -> str:
    return json.dumps(mapping, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _parse_schedule_days(text: str) -> Optional[frozenset]:
    tokens = [t for t in re.split(r"[,\s]+", text.strip().lower().rstrip(".")) if t]
    if not tokens:
        return frozenset(range(7))
    days = set()
    for token in tokens:
        first, dash, last = token.partition("-")
        if first not in _SCHEDULE_DAYS or (dash and last not in _SCHEDULE_DAYS):
            return None
        a = _SCHEDULE_DAYS[first]
        b = _SCHEDULE_DAYS[last] if dash else a
        while True:
            days.add(a)
            if a == b:
                break
            a = (a + 1) % 7
    return frozenset(days)


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
    except ValueError:
        return None


def _schedule_dates_hit(dates, day) -> bool:
    (y1, m1, d1), (y2, m2, d2) = dates
    if y1 is not None:
        return _date(y1, m1, d1) <= day <= _date(y2, m2, d2)
    first, last, today = (m1, d1), (m2, d2), (day.month, day.day)
    return first <= today <= last if first <= last else (today >= first or today <= last)


def parse_schedule(raw):
    rules, errors = [], []
    number = 0
    for line in as_text(raw).splitlines():
        number += 1
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        left, separator, name = line.partition("=")
        name = name.strip()
        match = _SCHEDULE_LEFT_RE.match(left.strip()) if separator and name else None
        if match is None:
            errors.append((number, "schedule_err_format"))
            continue
        first, last, h1, m1, h2, m2, part_a, part_b, rest = match.groups()
        if first is None and h1 is None and part_a is None:
            errors.append((number, "schedule_err_format"))
            continue
        dates = None
        if first is not None:
            start_date = _parse_schedule_date(first)
            end_date = _parse_schedule_date(last) if last is not None else start_date
            if (start_date is None or end_date is None or (start_date[0] is None) != (end_date[0] is None)
                    or (start_date[0] is not None and _date(*start_date) > _date(*end_date))):
                errors.append((number, "schedule_err_date"))
                continue
            dates = (start_date, end_date)
        if part_a is not None:
            first_part = DAYPART_BY_ALIAS[part_a.casefold()]
            last_part = DAYPART_BY_ALIAS[part_b.casefold()] if part_b is not None else first_part
            start, end = DAYPART_BOUNDS[first_part][0], DAYPART_BOUNDS[last_part][1]
            if start == end:
                errors.append((number, "schedule_err_time"))
                continue
        elif h1 is None:
            start, end = 0, 24 * 60
        else:
            h1, m1, h2, m2 = int(h1), int(m1), int(h2), int(m2)
            if not (0 <= h1 <= 23 and 0 <= h2 <= 23 and 0 <= m1 <= 59 and 0 <= m2 <= 59) or (h1, m1) == (h2, m2):
                errors.append((number, "schedule_err_time"))
                continue
            start, end = h1 * 60 + m1, h2 * 60 + m2
        days = _parse_schedule_days(rest)
        if days is None:
            errors.append((number, "schedule_err_days"))
            continue
        rules.append((start, end, days, name, number, dates))
    if len(rules) > MAX_SCHEDULE_RULES:
        errors.append((number, "schedule_err_limit"))
    return rules[:MAX_SCHEDULE_RULES], errors


def schedule_match(rules, now, resolve=None):
    minutes = now.hour * 60 + now.minute
    today = now.date()
    yesterday = today - timedelta(days=1)

    def day_ok(days, dates, day):
        return day.weekday() in days and (dates is None or _schedule_dates_hit(dates, day))

    for dated in (True, False):
        for start, end, days, name, _line, dates in rules:
            if (dates is not None) != dated:
                continue
            if start < end:
                hit = start <= minutes < end and day_ok(days, dates, today)
            elif minutes >= start:
                hit = day_ok(days, dates, today)
            else:
                hit = minutes < end and day_ok(days, dates, yesterday)
            if not hit:
                continue
            if resolve is None:
                return name
            target = resolve(name)
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
            line, changed = f"{head}= {new_name}", True
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
    except (TypeError, ValueError, AttributeError):
        return None


def to_dialog_id(value) -> Optional[int]:
    if value is None:
        return None
    direct = java_int(value)
    if direct is not None:
        return direct
    for attr in ("dialog_id", "dialogId", "did"):
        found = java_int(getattr(value, attr, None))
        if found is not None:
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


def safe_extension(name) -> str:
    ext = os.path.splitext(as_text(name))[1].lower()
    return ext if re.fullmatch(r"\.[a-z0-9]{1,8}", ext) else ""


def temp_dir(name: str) -> str:
    path = os.path.join(get_cache_dir(), "Prefixfy_tmp", name)
    ensure_dir_exists(path)
    return path


def unique_name(base: str, taken, ignore: str = "") -> str:
    used = {as_text(item).strip().casefold() for item in taken}
    used.discard(as_text(ignore).strip().casefold())
    name, number = base, 2
    while name.strip().casefold() in used:
        name = f"{base} {number}"
        number += 1
    return name


FEATURE_FLAGS: Dict[str, bool] = {
    "markdown": True,
    "text_styles": True,
    "mask_rotation": True,
    "conditional_masks": True,
    "regex_exceptions": True,
    "chat_type_rules": True,
    "edit_processing": True,
    "attached_media": True,
    "premium_emoji": True,
    "schedule": True,
    "chat_configs": True,
    "config_import": True,
    "lang_ru": True,
    "lang_ja": True,
    "lang_ko": True,
    "lang_ar": True,
    "lang_fr": True,
    "lang_pl": True,
    "lang_de": True,
    "lang_uk": True,
}
FEATURE_FLAGS.update({"style_" + _key: True for _key in STYLE_KEYS})
MASK_TAG_NAMES = ("date", "time", "datetime", "time12", "chat", "id", "weekday", "weekday_short", "year", "year_short", "month", "monthname", "day", "week", "yearday", "hour", "minute", "second", "ampm", "daypart", "timestamp", "tz", "chattype", "username", "count", "dice", "random_emoji", "emoji", "reply", "chatcount", "battery", "moon", "line", "since", "until")
FEATURE_FLAGS.update({"tag_" + _tag: True for _tag in MASK_TAG_NAMES})
FEATURE_FLAGS.update({"md_bold": True, "md_italic": True, "md_strike": True, "md_spoiler": True, "md_mono": True, "md_quote": True})
_FLAG_NAME_RE = re.compile(r"[a-z][a-z0-9_]{0,31}")


class FeatureFlags:
    """Remote on/off switches for optional features; the user's own settings are never touched.

    Global values come from flags.json; the "accounts" section can override them for specific
    account IDs. Overrides apply when any such account is signed in on this device. If several
    matching accounts disagree about a flag, "off" wins.
    Reads take no lock: every change swaps in a whole new dict.
    """

    def __init__(self, defaults: Dict[str, bool]):
        self._defaults = dict(defaults)
        self._global = dict(defaults)
        self._values = dict(defaults)
        self._accounts: Dict[int, Dict[str, bool]] = {}
        self._ids: frozenset = frozenset()
        self._serial = -1
        self._lock = threading.Lock()

    def on(self, name: str) -> bool:
        return self._values.get(name, True)

    def _compose(self) -> Dict[str, bool]:
        merged = dict(self._global)
        matched = [self._accounts[i] for i in sorted(self._ids) if i in self._accounts]
        for name in merged:
            votes = [item[name] for item in matched if name in item]
            if votes:
                merged[name] = all(votes)
        return merged

    def _swap(self) -> bool:
        merged = self._compose()
        changed = merged != self._values
        self._values = merged
        return changed

    def apply(self, flags: Dict[str, bool], serial: int, accounts: Optional[Dict[int, Dict[str, bool]]] = None) -> bool:
        base = dict(self._defaults)
        for name, value in flags.items():
            if name in base and isinstance(value, bool):
                base[name] = value
        cleaned: Dict[int, Dict[str, bool]] = {}
        for account_id, overrides in (accounts or {}).items():
            if isinstance(account_id, int) and not isinstance(account_id, bool) and isinstance(overrides, dict):
                cleaned[account_id] = {n: v for n, v in overrides.items() if n in self._defaults and isinstance(v, bool)}
        with self._lock:
            if serial < self._serial:
                raise ValueError(f"flags rollback rejected ({serial} < {self._serial})")
            self._global = base
            self._accounts = cleaned
            self._serial = serial
            return self._swap()

    def set_device_accounts(self, ids) -> bool:
        with self._lock:
            self._ids = frozenset(ids)
            return self._swap()

    def overridden(self) -> List[str]:
        values = self._values
        return sorted(f"{name}={'on' if value else 'off'}" for name, value in values.items() if value != self._defaults[name])


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
    """English is the mandatory base pack; every other pack can be switched off remotely."""
    return code == "en" or FEATURES.on("lang_" + as_text(code))


def enabled_language_indices() -> List[int]:
    """Indices into LANGUAGE_MODES (skipping 'auto') of the packs that are currently available."""
    return [index for index in range(1, len(LANGUAGE_MODES)) if language_enabled(LANGUAGE_MODES[index])]


def has_language_choice() -> bool:
    return any(LANGUAGE_MODES[index] != "en" for index in enabled_language_indices())


class RuntimeSettings:
    __slots__ = (
        "language", "chat_scope_enabled", "process_message", "process_media", "process_edit",
        "process_edit_message", "process_edit_media", "skip_once_on_edit",
        "mask", "mask_parts", "mask_link", "markdown_enabled", "markdown_style", "markdown_wrap", "text_style_enabled", "text_style",
        "text_style_random", "text_style_translit", "style_only", "mask_rotation_enabled", "masks_list", "mask_rotation_mode", "regex_exceptions", "conditional_rules", "chat_type_rules",
        "separator_enabled", "separators", "separator_count",
        "exceptions", "ignore_special", "ignore_emoji_only", "disabled_chats",
        "media_enabled", "media_path", "media_name", "media_mime", "raw",
    )

    def __init__(self, raw: Dict[str, Any]):
        self.raw = dict(raw)

        def get(key):
            return raw.get(key, SETTING_DEFAULTS[key])

        self.language = clamp_int(get("language"), 0, 0, len(LANGUAGE_MODES) - 1)
        self.chat_scope_enabled = bool(get("chat_scope_enabled"))
        self.process_message = bool(get("process_message"))
        self.process_media = bool(get("process_media"))
        self.process_edit = bool(get("process_edit")) and FEATURES.on("edit_processing")
        self.process_edit_message = bool(get("process_edit_message"))
        self.process_edit_media = bool(get("process_edit_media"))
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
        self.masks_list = [item.strip() for item in as_text(get("masks_list")).splitlines() if item.strip() and is_valid_mask(item.strip())][:MAX_MASKS_IN_LIST]
        self.mask_rotation_mode = clamp_int(get("mask_rotation_mode"), 0, 0, 1)
        self.regex_exceptions = compile_regex_exceptions(get("regex_exceptions")) if FEATURES.on("regex_exceptions") else ()
        self.conditional_rules = parse_conditional_masks(get("conditional_masks"))[0] if FEATURES.on("conditional_masks") else ()
        self.chat_type_rules = parse_chat_type_rules(get("chat_type_rules")) if FEATURES.on("chat_type_rules") else frozenset(CHAT_KINDS)
        self.mask_parts = split_mask(self.mask)
        if self.mask_parts is None and not self.mask.strip():
            self.mask_parts = ("", "")
        self.mask_link = mask_link(self.mask)
        self.separator_enabled = bool(get("separator_enabled"))
        self.separators = parse_separators(get("custom_emojis"))
        self.separator_count = clamp_int(get("emoji_count"), 1, 1, MAX_SEPARATOR_COUNT)
        self.exceptions = parse_lines(get("exceptions"))
        self.ignore_special = bool(get("ignore_special"))
        self.ignore_emoji_only = bool(get("ignore_emoji_only"))
        self.disabled_chats = parse_chat_ids(get("disabled_chats"))
        self.media_enabled = bool(get("attached_media_enabled")) and FEATURES.on("attached_media")
        self.media_path = as_text(get("attached_media_path"))
        self.media_name = as_text(get("attached_media_name"))
        self.media_mime = as_text(get("attached_media_mime"))

    def is_chat_allowed(self, dialog_id: Optional[int]) -> bool:
        if dialog_id is None:
            return self.chat_scope_enabled
        listed = dialog_id in self.disabled_chats
        return not listed if self.chat_scope_enabled else listed

    @property
    def mask_is_active(self) -> bool:
        return self.mask_parts is not None and bool(
            self.mask_parts[0] or self.mask_parts[1] or self.mask_link or self.text_style_enabled or self.markdown_wrap
        )


class PrefixfySettings:
    DEFAULTS = {**SETTING_DEFAULTS, **TRANSIENT_SETTING_DEFAULTS}

    def __init__(self, plugin):
        self.plugin = plugin

    def get(self, key, default=None):
        if default is None:
            default = self.DEFAULTS.get(key)
        return self.plugin.get_setting(key, default)

    def set(self, key, value, reload_settings=False):
        self.plugin.set_setting(key, value, reload_settings=reload_settings)
        self.plugin.handle_setting_changed(key)

    def raw(self) -> Dict[str, Any]:
        return {key: self.plugin.get_setting(key, default) for key, default in SETTING_DEFAULTS.items()}

    def snapshot(self) -> RuntimeSettings:
        return RuntimeSettings(self.raw())

    def language_index(self) -> int:
        return clamp_int(self.get("language"), 0, 0, len(LANGUAGE_MODES) - 1)

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


_EMOJI_SYMBOL = r"[\u00A9\u00AE\u203C\u2049\u2122\u2139\u2194-\u2199\u21A9-\u21AA\u231A-\u231B\u2328\u23CF\u23E9-\u23F3\u23F8-\u23FA\u24C2\u25AA-\u25AB\u25B6\u25C0\u25FB-\u25FE\u2600-\u2604\u260E\u2611\u2614-\u2615\u2618\u261D\u2620\u2622-\u2623\u2626\u262A\u262E-\u262F\u2638-\u263A\u2640\u2642\u2648-\u2653\u265F-\u2660\u2663\u2665-\u2666\u2668\u267B\u267E-\u267F\u2692-\u2697\u2699\u269B-\u269C\u26A0\u26A7\u26AA-\u26AB\u26B0-\u26B1\u26BD-\u26BE\u26C4-\u26C5\u26C8\u26CE-\u26CF\u26D1\u26D3-\u26D4\u26E9-\u26EA\u26F0-\u26F5\u26F7-\u26FA\u26FD\u2702\u2705\u2708-\u270D\u270F\u2712\u2714\u2716\u271D\u2721\u2728\u2733-\u2734\u2744\u2747\u274C\u274E\u2753-\u2755\u2757\u2763-\u2764\u2795-\u2797\u27A1\u27B0\u27BF\u2934-\u2935\u2B05-\u2B07\u2B1B-\u2B1C\u2B50\u2B55\u3030\u303D\u3297\u3299\U0001F000-\U0001FAFF]"
_EMOJI_ELEMENT = (
    r"(?:[\U0001F1E6-\U0001F1FF]{2}|[#*0-9]\uFE0F?\u20E3|" + _EMOJI_SYMBOL + r")"
    r"\uFE0F?[\U0001F3FB-\U0001F3FF]?"
    r"[\U000E0020-\U000E007E]*\U000E007F?"
)
_EMOJI_TOKEN = _EMOJI_ELEMENT + r"(?:\u200D" + _EMOJI_ELEMENT + r")*"


@lru_cache(maxsize=1)
def _emoji_only_regex():
    return re.compile(_EMOJI_TOKEN + r"(?:\s*" + _EMOJI_TOKEN + r")*")


@lru_cache(maxsize=1)
def _emoji_token_regex():
    return re.compile(_EMOJI_TOKEN)


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
            for pattern in self.regex_exceptions:
                if pattern.search(sample):
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
        if self.text_style_enabled:
            text = apply_text_style(text, self.text_style, self.text_style_translit, self.style_only)
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
        self._gap = self._WORD_GAP if settings.text_style_enabled and settings.text_style == STYLE_VAPORWAVE else self._WHITESPACE

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
                chosen = []
                for _ in range(self.count):
                    chosen.append(pool[position % len(pool)])
                    position += 1
                parts.append(gap + " ".join(chosen) + gap)
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
_PROTECTED_RE = re.compile(
    r"```[\s\S]*?```"
    r"|`[^`\n]+`"
    r"|(?<![\w@])@[A-Za-z][A-Za-z0-9_]{2,31}"
    r"|(?<!\S)/[A-Za-z][A-Za-z0-9_]*(?:@[A-Za-z][A-Za-z0-9_]*)?(?![\w/])"
    r"|" + _LINK_PATTERN
    + r"|(?<![\w&/#])#(?!\d+(?!\w))\w{1,64}(?:@[A-Za-z][A-Za-z0-9_]{2,31})?"
    + r"|(?<![\w$])\$[A-Za-z]{1,8}(?!\w)"
)
_LEADING_SPECIAL_RE = re.compile(
    r"\s*(?:"
    r"[/!.][A-Za-z][A-Za-z0-9_]*(?:@[A-Za-z][A-Za-z0-9_]*)?"
    r"|@[A-Za-z][A-Za-z0-9_]{2,31}"
    r")(?![A-Za-z0-9_@])"
)
_PLACEHOLDER_RE = re.compile("\uE000(\\d+)\uE001")


def has_marker_chars(text: str) -> bool:
    return "\uE000" in text or "\uE001" in text or _MD_SENTINEL_RE.search(text) is not None


def protect_special(text: str) -> Tuple[str, List[str]]:
    if has_marker_chars(text):
        return text, []
    spans: List[str] = []

    def stash(match):
        spans.append(match.group(0))
        return f"\uE000{len(spans) - 1}\uE001"

    return _PROTECTED_RE.sub(stash, text), spans


def _is_link_span(spans: List[str], match) -> bool:
    index = int(match.group(1))
    return index < len(spans) and not spans[index].startswith(("`", "@", "/"))


def restore_special(text: str, spans: List[str]) -> str:
    def restore(match):
        index = int(match.group(1))
        return spans[index] if index < len(spans) else match.group(0)

    return _PLACEHOLDER_RE.sub(restore, text)


class TransformationPipeline:
    def __init__(self, settings: RuntimeSettings, logger=None):
        self.filter = TextFilter(settings)
        self.protect_special = settings.ignore_special
        self.logger = logger
        self.transformations: List[Transformation] = []
        self.markdown_table: List[Tuple[str, str]] = []
        self.text_style = settings.text_style
        self.text_style_translit = settings.text_style_translit
        self.style_only = settings.style_only
        self.styling = False
        self._prepared_memo = None
        self._layout_memo = None
        if settings.mask_is_active:
            mask = MaskTransformation(settings)
            self.transformations.append(mask)
            self.markdown_table = mask.table
            self.styling = mask.text_style_enabled
        if settings.separator_enabled:
            self.transformations.append(SeparatorTransformation(settings, self.markdown_table))

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
        if _LEADING_SPECIAL_RE.match(text):
            return None
        if has_marker_chars(text):
            return None
        protected, spans = protect_special(text)
        visible = _PLACEHOLDER_RE.sub(lambda match: "x" if _is_link_span(spans, match) else "", protected)
        if spans and not visible.strip():
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
        return restore_special(protected, spans)


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
    try:
        cls = find_class(name)
        if cls is not None:
            try:
                return cls.newInstance()
            except Exception as exc:
                errors.append(f"newInstance: {exc}")
            return cls()
    except Exception as exc:
        errors.append(f"find_class: {exc}")
    raise RuntimeError(f"Telegram entity {kind} unavailable ({'; '.join(errors)})")


def _realign_entities(kept, original: str, final_text: str, start: int):
    result = []
    cursor = _utf16_index(final_text, start) if start else 0
    for entity in sorted(kept, key=lambda item: int(item.offset)):
        try:
            offset, length = int(entity.offset), int(entity.length)
            piece = original[_utf16_index(original, offset):_utf16_index(original, offset + length)]
            if not piece:
                continue
            found = final_text.find(piece, cursor)
            if found < 0:
                continue
            entity.offset = utf16_length(final_text[:found])
            cursor = found + len(piece)
            result.append(entity)
        except Exception:
            continue
    return result


ENTITY_TRACE: List[str] = []


def _make_tg_entities(descriptions, existing=None, body_offset=None, remap=None, realign=None):
    del ENTITY_TRACE[:]
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
            ENTITY_TRACE.append(f"kept via list(): {len(kept)}")
        except Exception as exc:
            ENTITY_TRACE.append(f"list(existing) failed: {exc!r} ({type(existing).__name__})")
            kept = _iter_entities(existing)
            ENTITY_TRACE.append(f"kept via fallback iteration: {len(kept)}")
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
            ENTITY_TRACE.append(f"realigned: {len(kept)} of {len(source)}")
        except Exception as exc:
            ENTITY_TRACE.append(f"realign failed: {exc!r}")
            kept = []
    else:
        ENTITY_TRACE.append(f"no kept: existing={existing is not None} body_offset={body_offset!r}")
    combined = sorted(kept + created, key=lambda entity: (int(entity.offset), -int(entity.length)))
    ENTITY_TRACE.append(f"combined: kept={len(kept)} created={len(created)}")
    if existing is not None:
        try:
            existing.clear()
            for entity in combined:
                existing.add(entity)
            return existing
        except Exception as exc:
            ENTITY_TRACE.append(f"existing.clear/add failed: {exc!r}")
    try:
        from java.util import ArrayList
        java_entities = ArrayList()
        for entity in combined:
            java_entities.add(entity)
        return java_entities
    except Exception:
        return combined


DEBUG_SEND = False


def describe_entities(entities) -> str:
    try:
        items = _iter_entities(entities)
    except Exception as exc:
        return f"<unreadable: {exc}>"
    parts = []
    for entity in items[:40]:
        try:
            name = _entity_name(entity).replace("TL_messageEntity", "")
            doc = _entity_document_id(entity)
            parts.append(f"{name}@{int(entity.offset)}+{int(entity.length)}" + (f"#{doc}" if doc else ""))
        except Exception:
            parts.append("?")
    extra = f" (+{len(items) - 40} more)" if len(items) > 40 else ""
    return f"[{len(items)}] " + ", ".join(parts) + extra


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
        if not s.media_enabled or not s.media_path or not is_plugin_file(s.media_path) or not os.path.isfile(s.media_path):
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
                config_id = configurations.active_id if configurations is not None else "default"
                self.runtime = Runtime(self.plugin.settings.snapshot(), config_id, self.plugin.log)
            except Exception as exc:
                self.plugin.log(f"Prefixfy runtime rebuild failed: {exc}")

    def on_setting_changed(self):
        if not self._suspend:
            self.rebuild()

    @contextmanager
    def bulk(self):
        with self._lock:
            self._suspend += 1
        try:
            yield
        finally:
            with self._lock:
                self._suspend -= 1
                idle = self._suspend == 0
            if idle:
                self.rebuild()


class ConfigurationError(ValueError):
    pass


class ConfigurationSaveError(RuntimeError):
    pass


CONFIG_FORMAT = "Prefixfy-config"
LEGACY_CONFIG_FORMATS = ("maskify-config",)
CONFIG_VERSION = 14
COMPONENTS = ("mask", "separator", "exceptions", "language", "media", "schedule")
COMPONENT_ALIASES = {
    "mask": ("mask",),
    "separator": ("separator", "separators"),
    "exceptions": ("exceptions",),
    "language": ("language",),
    "media": ("media", "attached_media"),
    "schedule": ("schedule",),
}
COMPONENT_KEYS = {
    "language": ("language",),
    "mask": ("mask", "markdown_enabled", "markdown_style", "text_style_enabled", "text_style", "text_style_random", "mask_rotation_enabled", "masks_list", "mask_rotation_mode", "conditional_masks", "text_style_translit", "style_words", "tag_lines"),
    "separator": ("separator_enabled", "custom_emojis", "emoji_count"),
    "exceptions": ("exceptions", "ignore_special", "ignore_emoji_only", "disabled_chats", "chat_scope_enabled", "regex_exceptions", "chat_type_rules"),
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
                           "ignore_special")
    if component == "exceptions" and any(k in settings for k in flat_exception_keys):
        return {
            "values": settings.get("exceptions", ""),
            "disabled_chats": settings.get("disabled_chats", ""),
            "chat_scope_enabled": settings.get("chat_scope_enabled", True),
            "chat_scope": settings.get("chat_scope"),
            "ignore_emoji_only": settings.get("ignore_emoji_only", SETTING_DEFAULTS["ignore_emoji_only"]),
            "ignore_special": settings.get("ignore_special", True),
        }
    return None


def extract_component(data: dict, component: str):
    section = None
    for key in COMPONENT_ALIASES[component]:
        if key in data:
            section = data[key]
            break
    else:
        return _section_from_flat_settings(data.get("settings"), component)
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
            if len(value) > MAX_SETTING_TEXT:
                return False
        elif isinstance(value, dict) and not _texts_within_limit(value, depth + 1):
            return False
    return True


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
        return (
            isinstance(values, str) and bool(values.strip())
            and _is_int(count) and 1 <= count <= MAX_SEPARATOR_COUNT
            and isinstance(enabled, bool)
        )
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
        if not isinstance(section.get("ignore_special", True), bool):
            return False
        if scope is None:
            return True
        if not isinstance(scope, dict):
            return False
        expected_mode = "exceptions" if enabled else "included"
        return scope.get("mode") == expected_mode and scope.get("chats", chats) == chats
    if component == "schedule":
        chats, rules = section.get("chats", {}), section.get("rules", "")
        return (
            isinstance(chats, dict) and len(chats) <= 4096
            and all(isinstance(k, str) and k.lstrip("-").isdigit() and isinstance(v, str) for k, v in chats.items())
            and isinstance(rules, str) and len(rules) <= 64 * 1024 and isinstance(section.get("source", ""), str)
        )
    if component == "media":
        return isinstance(section.get("enabled", False), bool) and isinstance(section.get("file", ""), str)
    return False


def detect_components(data: dict) -> Tuple[str, ...]:
    found = []
    for component in COMPONENTS:
        section = extract_component(data, component)
        if section is not None and validate_component(component, section):
            found.append(component)
    return tuple(found)


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
    CONFIG_EXTENSION = ".prefixfy"

    def __init__(self, plugin):
        self.plugin = plugin
        self.settings = plugin.settings
        self.localization = plugin.localization
        self.pending_components: Tuple[str, ...] = ()
        self.pending_import_as_new = False
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


    def media_path(self) -> str:
        return as_text(self.settings.get("attached_media_path", ""))

    def media_exists(self) -> bool:
        path = self.media_path()
        return bool(path and is_plugin_file(path) and os.path.isfile(path))

    def media_info(self) -> Dict[str, str]:
        name = as_text(self.settings.get("attached_media_name", "")) or os.path.basename(self.media_path())
        mime = as_text(self.settings.get("attached_media_mime", "")) or mimetypes.guess_type(name)[0] or "application/octet-stream"
        return {"name": name, "mime": mime}

    def _prepare_media_target(self, name, mime):
        name = os.path.basename(as_text(name) or "attached_media.bin")
        ext = safe_extension(name)
        mime = as_text(mime) or mimetypes.guess_type(name)[0] or ""
        if not (mime.startswith(("image/", "video/")) or ext in MEDIA_EXTENSIONS):
            raise ValueError("unsupported media format")
        return name, mime, os.path.join(self.media_data_dir, "attached_media" + (ext or ".bin"))

    def _commit_media(self, temp_path, target, name, mime):
        old = self.media_path()
        os.replace(temp_path, target)
        if old and old != target and is_plugin_file(old) and os.path.isfile(old):
            delete_file(old)
        with self.plugin.runtime_manager.bulk():
            self.settings.set("attached_media_path", target)
            self.settings.set("attached_media_name", name)
            self.settings.set("attached_media_mime", mime)
            self.settings.set("attached_media_enabled", True)

    def store_media_file(self, source_path, name, mime=None):
        name, mime, target = self._prepare_media_target(name, mime)
        if os.path.getsize(source_path) > MAX_MEDIA_BYTES:
            raise ValueError("media is too large")
        temp = target + ".tmp"
        try:
            shutil.copyfile(source_path, temp)
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
        temp = target + ".tmp"
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
        if path and is_plugin_file(path) and os.path.isfile(path):
            delete_file(path)
        with self.plugin.runtime_manager.bulk():
            self.settings.set("attached_media_path", "")
            self.settings.set("attached_media_name", "")
            self.settings.set("attached_media_mime", "")
            self.settings.set("attached_media_enabled", False, reload_settings=True)

    def _blocked(self, fragment=None) -> bool:
        remote = getattr(self.plugin, "remote", None)
        if remote is None or remote.allows():
            return False
        key, kwargs = remote.notice()
        self._toast(key, fragment, **kwargs)
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

    def _component_label(self, component):
        return self._tr("config_" + component)

    def request_import(self, view=None):
        self._show_selection("import")

    def request_export(self, view=None):
        self._show_selection("export")

    def request_reset(self, view=None):
        self._show_selection("reset")

    def _show_selection(self, operation):
        if self._blocked():
            return
        fragment, _ = self._activity()
        available = tuple(c for c in self.visible_components() if operation != "reset" or COMPONENT_KEYS.get(c))
        rows = [(self._component_label(component), True, True) for component in available]
        extra = None
        message = self._tr("select_configuration_subtext")
        imported = False
        if operation == "import":
            extra = (self._tr("config_import_as_new"), False)
        elif operation == "reset":
            imported = self.plugin.configurations.is_imported()
            extra = (self._tr("reset_to_plugin_defaults"), False, imported)
            if not imported:
                message += "\n\n" + self._tr("reset_to_plugin_defaults_unavailable")

        def confirm(selected, extra_checked):
            if not selected:
                self._toast("configuration_nothing_selected", fragment)
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
            self._tr("select_configuration"), rows, confirm,
            message=message,
            extra=extra, positive=self._tr("apply"), fragment=fragment,
        )


    def _request_import(self, components, as_new=False):
        _, activity = self._activity()
        if not activity:
            return
        self.pending_components = tuple(components)
        self.pending_import_as_new = bool(as_new)
        intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType("application/octet-stream")
        activity.startActivityForResult(intent, self.CONFIG_IMPORT_REQUEST_CODE)

    def read_container(self, path: str) -> dict:
        try:
            with zipfile.ZipFile(path, "r") as archive:
                try:
                    info = archive.getinfo("config.json")
                except KeyError:
                    raise ConfigurationError("config.json missing")
                if info.file_size > MAX_CONFIG_JSON_BYTES:
                    raise ConfigurationError("config.json is too large")
                try:
                    data = json.loads(_read_zip_member(archive, info, MAX_CONFIG_JSON_BYTES).decode("utf-8"))
                except (ValueError, RecursionError) as exc:
                    raise ConfigurationError("invalid config.json") from exc
                if not isinstance(data, dict):
                    raise ConfigurationError("root is not an object")
                if data.get("format") not in (None, CONFIG_FORMAT) + LEGACY_CONFIG_FORMATS:
                    raise ConfigurationError("unknown configuration format")

                media = data.get("media")
                if isinstance(media, dict):
                    media.pop("_media_path", None)
                    entry = as_text(media.get("file")).replace("\\", "/")
                    if entry:
                        if entry.startswith("/") or ".." in entry.split("/"):
                            raise ConfigurationError("invalid media path")
                        try:
                            media_info = archive.getinfo(entry)
                        except KeyError:
                            media_info = None
                        if media_info is not None:
                            if media_info.is_dir() or media_info.flag_bits & 0x1:
                                raise ConfigurationError("invalid media entry")
                            if media_info.file_size > MAX_MEDIA_BYTES:
                                raise ConfigurationError("media is too large")
                            extracted = os.path.join(temp_dir("imports"), uuid.uuid4().hex + safe_extension(entry))
                            _extract_zip_member(archive, media_info, extracted, MAX_MEDIA_BYTES)
                            media["_media_path"] = extracted
                return data
        except zipfile.BadZipFile as exc:
            raise ConfigurationError("not a .prefixfy container") from exc
        except (RuntimeError, NotImplementedError, EOFError, zlib.error, zipfile.LargeZipFile) as exc:
            raise ConfigurationError("unreadable .prefixfy container") from exc

    @staticmethod
    def discard_container_media(data):
        media = data.get("media") if isinstance(data, dict) else None
        path = media.get("_media_path") if isinstance(media, dict) else None
        if path and os.path.isfile(path):
            delete_file(path)

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
            self._file_handler_secret = FilesController.register(
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
                FilesController.unregister("prefixfy", secret)
            except Exception as exc:
                self.plugin.log(f"Prefixfy file handler unregistration failed (attempt {attempt}): {exc}")
                continue
            self._file_handler_secret = None
            return

    def _on_config_file_click(self, args):
        fragment = getattr(args, "parent_fragment", None) or get_last_fragment()
        if self._blocked(fragment):
            return
        try:
            data = self.read_container(args.file.getAbsolutePath())
            visible = self.visible_components()
            detected = tuple(c for c in detect_components(data) if c in visible)
            if not detected:
                self.discard_container_media(data)
                raise ConfigurationError("configuration has no valid components")

            rows = [(self._component_label(c), c in detected, c in detected) for c in visible]

            def confirm(selected, as_new):
                chosen = tuple(visible[i] for i in selected if visible[i] in detected)
                if not chosen:
                    self._toast("configuration_nothing_selected", fragment)
                    return False
                self._import_opened_data(data, fragment, chosen, as_new)
                return True

            def on_dismiss_without_import():
                self.discard_container_media(data)

            shown = self.plugin.show_checklist(
                self._tr("config_found_title"), rows, confirm,
                message=self._tr("config_found_contains"),
                extra=(self._tr("config_import_as_new"), False),
                positive=self._tr("config_found_import"), fragment=fragment,
                on_cancel=on_dismiss_without_import,
            )
            if not shown:
                self.discard_container_media(data)
        except Exception as exc:
            self.plugin.log(f"Prefixfy file open failed: {exc}")
            if fragment:
                self._toast("config_file_open_failed", fragment)

    def _import_opened_data(self, data, fragment, components, as_new):
        if as_new:
            self._prompt_import_name(data, fragment, components)
            return
        self._finish_import(data, components, False, None, fragment)

    def _prompt_import_name(self, data, fragment, components):
        configurations = self.plugin.configurations

        def confirm(value, editor):
            name = ConfigurationsManager.normalize_name(value)
            error = self.plugin.configurations.name_error(name)
            if error:
                editor.setError(self._tr(error))
                return False
            self._finish_import(data, components, True, name, fragment)
            return True

        def cancelled():
            self.discard_container_media(data)
            self._toast("configuration_import_cancelled", fragment)

        if not self.plugin.show_text_dialog(
            self._tr("import_new_configuration_name"), confirm,
            text=unique_name(self._tr("imported_configuration"), configurations.selector_items()),
            hint=self._tr("configuration_name_hint"),
            positive=self._tr("config_found_import"), fragment=fragment, on_cancel=cancelled,
        ):
            self.discard_container_media(data)

    def _finish_import(self, data, components, as_new, name, fragment):
        try:
            self.plugin.configurations.import_data(data, components, as_new=as_new, name=name)
            self.plugin.reload_settings_ui()
            self._toast("configuration_imported", fragment)
        except ConfigurationError as exc:
            self.plugin.log(f"Prefixfy import rejected: {exc}")
            self._toast("invalid_configuration", fragment)
        except ConfigurationSaveError as exc:
            self.plugin.log(f"Prefixfy import aborted: {exc}")
            self._toast("configuration_save_failed", fragment)
        except Exception as exc:
            self.plugin.log(f"Prefixfy import failed: {exc}")
            self._toast("configuration_import_failed", fragment)
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
                    if not path or not os.path.isfile(path):
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
                    self.settings.set("ignore_special", section.get("ignore_special", True))
                    if "regex_exceptions" in section:
                        self.settings.set("regex_exceptions", section["regex_exceptions"])
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


    def _request_export(self, components):
        _, activity = self._activity()
        if not activity or not components:
            return
        builder = AlertDialogBuilder(activity)
        builder.set_title(self._tr("configuration_export_destination_title"))
        builder.set_items(
            [self._tr("configuration_export_to_saved"), self._tr("configuration_export_to_device")],
            lambda bld, which: self._on_export_destination(bld, which, tuple(components)),
        )
        builder.set_negative_button(self._tr("cancel"), lambda bld, which: bld.dismiss())
        self.plugin._show_builder(builder)

    def _on_export_destination(self, builder, which, components):
        builder.dismiss()
        if which == 0:
            self._export_to_saved_messages(components)
        elif which == 1:
            self._request_export_to_device(components)

    def _request_export_to_device(self, components):
        _, activity = self._activity()
        if not activity:
            return
        self.pending_components = components
        intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType("application/octet-stream")
        name = (components[0] if len(components) == 1 else "Prefixfy_config") + self.CONFIG_EXTENSION
        intent.putExtra(Intent.EXTRA_TITLE, name)
        activity.startActivityForResult(intent, self.CONFIG_EXPORT_REQUEST_CODE)

    def _export_to_saved_messages(self, components):
        fragment, _ = self._activity()
        try:
            account = get_selected_account()
            if account is None:
                raise RuntimeError("active account is not available")
            user_config = get_user_config(account)
            current_user = user_config.getCurrentUser() if user_config else None
            user_id = java_int(getattr(current_user, "id", None)) if current_user is not None else None
            if not user_id or user_id <= 0:
                raise RuntimeError("active account user id is not available")
            path = self.build_config_file(components, temp_dir("exports"))
            send_document(user_id, path, caption="", account=account)
            self._toast("configuration_exported", fragment)
        except Exception as exc:
            self.plugin.log(f"Saved Messages export failed: {exc}")
            self._toast("configuration_export_failed", fragment)

    def selected_data(self, components) -> dict:
        s = self.settings
        data = {"format": CONFIG_FORMAT, "version": CONFIG_VERSION}
        if "language" in components:
            data["language"] = {"value": s.language_index()}
        if "mask" in components:
            data["mask"] = {
                "value": as_text(s.get("mask")),
                "markdown": self.settings.markdown_enabled(),
                "markdown_enabled": self.settings.markdown_enabled(),
                "markdown_style": self.settings.markdown_style_value(),
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
                "ignore_special": bool(s.get("ignore_special")),
                "regex_exceptions": as_text(s.get("regex_exceptions")),
                "chat_type_rules": dump_chat_type_rules(parse_chat_type_rules(s.get("chat_type_rules"))),
            }
        if "schedule" in components:
            data["schedule"] = self.plugin.export_schedule_section()
        if "media" in components:
            exists = self.media_exists()
            info = self.media_info() if exists else {"name": "", "mime": ""}
            data["media"] = {
                "enabled": bool(s.get("attached_media_enabled")) and exists,
                "file": "",
                "name": info["name"],
                "mime": info["mime"],
            }
        return data

    def build_config_file(self, components, directory: str) -> str:
        if not components:
            raise ValueError("no components selected")
        ensure_dir_exists(directory)
        self._prune_old_exports(directory)
        config = self.selected_data(components)
        path = os.path.join(directory, f"Prefixfy_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}{self.CONFIG_EXTENSION}")
        temp = path + ".tmp"
        try:
            with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                if "media" in components and self.media_exists():
                    entry = "media/attached_media" + safe_extension(config["media"]["name"])
                    config["media"]["file"] = entry
                    archive.write(self.media_path(), entry, compress_type=zipfile.ZIP_STORED)
                archive.writestr("config.json", json.dumps(config, ensure_ascii=False, indent=2).encode("utf-8"))
            os.replace(temp, path)
        except BaseException:
            discard_file(temp)
            raise
        return path

    @staticmethod
    def _prune_old_exports(directory: str):
        deadline = time.time() - EXPORT_TEMP_TTL
        try:
            for entry in os.listdir(directory):
                path = os.path.join(directory, entry)
                if os.path.isfile(path) and os.path.getmtime(path) < deadline:
                    discard_file(path)
        except OSError:
            pass

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
        if request_code not in (self.MEDIA_IMPORT_REQUEST_CODE, self.CONFIG_IMPORT_REQUEST_CODE, self.CONFIG_EXPORT_REQUEST_CODE):
            return False
        if self._blocked():
            self.pending_components, self.pending_import_as_new = (), False
            return True
        fragment, _ = self._activity()
        components, as_new = self.pending_components, self.pending_import_as_new
        if request_code != self.MEDIA_IMPORT_REQUEST_CODE:
            self.pending_components, self.pending_import_as_new = (), False
        uri = data.getData() if (result_code == Activity.RESULT_OK and data is not None) else None
        if uri is None:
            return True

        if request_code == self.MEDIA_IMPORT_REQUEST_CODE:
            try:
                _, activity = self._activity()
                mime = ""
                try:
                    mime = as_text(activity.getContentResolver().getType(uri))
                except Exception:
                    pass
                self.store_media_uri(uri, self._uri_display_name(uri) or "attached_media.bin", mime)
                self._toast("media_imported", fragment)
            except Exception as exc:
                self.plugin.log(f"Media import failed: {exc}")
                self._toast("media_import_failed", fragment)
            self.plugin.reload_settings_ui()
        elif request_code == self.CONFIG_EXPORT_REQUEST_CODE:
            path = None
            try:
                path = self.build_config_file(components, temp_dir("exports"))
                self._write_file_to_uri(uri, path)
                self._toast("configuration_exported", fragment)
            except Exception as exc:
                self.plugin.log(f"Configuration export failed: {exc}")
                self._toast("configuration_export_failed", fragment)
            finally:
                if path and os.path.isfile(path):
                    delete_file(path)
        else:
            temp_path = None
            try:
                temp_path = self._copy_uri_to_temp_file(uri)
                parsed = self.read_container(temp_path)
            except Exception as exc:
                self.plugin.log(f"Configuration read failed: {exc}")
                self._toast("invalid_configuration" if isinstance(exc, ConfigurationError) else "configuration_import_failed", fragment)
                return True
            finally:
                if temp_path and os.path.isfile(temp_path):
                    delete_file(temp_path)
            if as_new:
                self._prompt_import_name(parsed, fragment, components)
            else:
                self._finish_import(parsed, components, False, None, fragment)
        return True


class ConfigurationsManager:
    LEGACY_SETTING_KEY = "Prefixfy_experimental_configurations"
    LEGACY_ACTIVE_KEY = "Prefixfy_experimental_active_configuration"
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
        self._migrated_legacy = False
        self.media_dir = os.path.join(get_plugins_dir(), self.MEDIA_DIR_NAME)
        self.store_dir = os.path.join(get_plugins_dir(), self.STORE_DIR_NAME)
        ensure_dir_exists(self.media_dir)
        ensure_dir_exists(self.store_dir)
        self.active_id = ""
        self.configurations: Dict[str, dict] = {}
        self._load_store()
        if not self.configurations:
            self._migrate_legacy_setting()
        if not self.configurations:
            baseline = self._snapshot_with_media("default", "baseline")
            self._store_record("default", {
                "name": plugin._tr("default_configuration_name"),
                "current": self._clone_with_media(baseline, "default", "current"),
                "baseline": baseline,
            })
            self.active_id = "default"
        elif self.active_id not in self.configurations:
            self.active_id = next(iter(self.configurations))
        self._dedupe_names()
        self._collect_orphan_media()
        self._write_index()
        if self._migrated_legacy:
            self.plugin.set_setting(self.LEGACY_SETTING_KEY, "", reload_settings=False)


    @classmethod
    def _valid_id(cls, config_id) -> bool:
        return isinstance(config_id, str) and cls._ID_RE.fullmatch(config_id) is not None

    def _config_dir(self, config_id: str) -> str:
        return os.path.join(self.store_dir, config_id)

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
        temp = path + ".tmp"
        with open(temp, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        os.replace(temp, path)

    @staticmethod
    def _json_valid(path: str) -> bool:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                json.load(handle)
            return True
        except Exception:
            return False

    def _read_json(self, path: str):
        if not os.path.isfile(path):
            return False, None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return True, json.load(handle)
        except Exception as exc:
            self.plugin.log(f"Prefixfy store: cannot read {path}: {exc}")
            self._degraded = True
            return False, None

    def _read_index(self) -> Optional[dict]:
        path = os.path.join(self.store_dir, self.INDEX_NAME)
        for candidate in (path, path + ".bak"):
            ok, data = self._read_json(candidate)
            if ok and isinstance(data, dict) and isinstance(data.get("order"), list):
                return data
        return None

    def _write_index(self):
        path = os.path.join(self.store_dir, self.INDEX_NAME)
        payload = json.dumps(
            {"version": 1, "active": self.active_id, "order": list(self.configurations)},
            ensure_ascii=False, separators=(",", ":"),
        )
        try:
            if self._json_valid(path):
                with open(path, "r", encoding="utf-8") as handle:
                    self._atomic_write(path + ".bak", handle.read())
            self._atomic_write(path, payload)
        except Exception as exc:
            self.plugin.log(f"Prefixfy store: index write failed: {exc}")

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
        return {"name": as_text(name) if name_ok else "", "current": current, "baseline": baseline, "origin": origin}

    def _load_store(self):
        index = self._read_index()
        ids: List[str] = []
        if index:
            for config_id in index["order"]:
                if self._valid_id(config_id) and config_id not in ids:
                    ids.append(config_id)
        try:
            entries = sorted(os.listdir(self.store_dir))
        except OSError as exc:
            self.plugin.log(f"Prefixfy store: listing failed: {exc}")
            entries = []
        for entry in entries:
            path = os.path.join(self.store_dir, entry)
            if not os.path.isdir(path):
                continue
            if entry.endswith(".deleted"):
                shutil.rmtree(path, ignore_errors=True)
            elif entry in ids:
                continue
            elif self._valid_id(entry) and os.path.isfile(os.path.join(path, "name.json")):
                ids.append(entry)
            else:
                shutil.rmtree(path, ignore_errors=True)
        for config_id in ids:
            record = self._read_record(config_id)
            if record is not None:
                self.configurations[config_id] = record
        active = as_text(index.get("active")) if index else ""
        self.active_id = active if active in self.configurations else ""

    def _sync_params(self, config_id: str, role: str, new: dict) -> bool:
        record = self.configurations[config_id]
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
        self.generation += 1
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

    def _write_name(self, config_id: str):
        try:
            self._atomic_write(
                self._name_path(config_id),
                json.dumps(self.configurations[config_id]["name"], ensure_ascii=False),
            )
        except Exception as exc:
            self.plugin.log(f"Prefixfy store: name write failed ({config_id}): {exc}")

    def _store_record(self, config_id: str, record: dict):
        origin = record.get("origin", self.ORIGIN_CREATED)
        self.configurations[config_id] = {"name": as_text(record["name"]), "current": {}, "baseline": {}, "origin": origin}
        self._sync_params(config_id, "current", record["current"])
        self._sync_params(config_id, "baseline", record["baseline"])
        try:
            self._atomic_write(self._origin_path(config_id), json.dumps(origin))
        except Exception as exc:
            self.plugin.log(f"Prefixfy store: origin write failed ({config_id}): {exc}")
        self._write_name(config_id)

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

    def _migrate_legacy_setting(self):
        raw = self.plugin.get_setting(self.LEGACY_SETTING_KEY, "")
        if not (isinstance(raw, str) and raw):
            return
        try:
            data = json.loads(raw)
        except Exception as exc:
            self.plugin.log(f"Configurations legacy load failed: {exc}")
            self._degraded = True
            return
        if not isinstance(data, dict):
            return
        legacy_active = as_text(self.plugin.get_setting(self.LEGACY_ACTIVE_KEY, ""))
        for old_id, record in data.items():
            if not isinstance(record, dict):
                continue
            if "current" not in record or "baseline" not in record:
                flat = dict(record)
                name = flat.pop("name", old_id)
                record = {"name": name, "current": dict(flat), "baseline": dict(flat)}
            config_id = str(old_id) if self._valid_id(str(old_id)) else self._new_id()
            self._store_record(config_id, {
                "name": as_text(record.get("name", old_id)),
                "current": record.get("current") if isinstance(record.get("current"), dict) else {},
                "baseline": record.get("baseline") if isinstance(record.get("baseline"), dict) else {},
            })
            if str(old_id) == legacy_active:
                self.active_id = config_id
        self._migrated_legacy = bool(self.configurations)

    def _dedupe_names(self):
        seen: List[str] = []
        for config_id, record in self.configurations.items():
            base = self.normalize_name(record.get("name")) or self.plugin._tr("default_configuration_name")
            name = unique_name(base, seen)
            if name != record.get("name"):
                record["name"] = name
                self._write_name(config_id)
            seen.append(name)

    def _collect_orphan_media(self):
        if self._degraded:
            return
        referenced = {os.path.abspath(as_text(self.settings.get("attached_media_path")))}
        for data in self.configurations.values():
            for snapshot in (data.get("current", {}), data.get("baseline", {})):
                referenced.add(os.path.abspath(as_text(snapshot.get("attached_media_path"))))
        directories = [self.media_dir]
        transfer = getattr(self.plugin, "transfer", None)
        if transfer is not None:
            directories.append(transfer.media_data_dir)
        for directory in directories:
            try:
                for entry in os.listdir(directory):
                    path = os.path.abspath(os.path.join(directory, entry))
                    if path not in referenced and not entry.endswith(".tmp") and os.path.isfile(path):
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
        return value if isinstance(value, str) and len(value) <= MAX_SETTING_TEXT else default

    def _snapshot(self) -> Dict[str, Any]:
        return {key: self._coerce(key, self.settings.get(key, SETTING_DEFAULTS[key])) for key in self.CONFIG_KEYS}

    def _copy_media(self, source: str, config_id: str, role: str) -> Optional[str]:
        if not source or not is_plugin_file(source) or not os.path.isfile(source):
            return None
        suffix = "-baseline" if role == "baseline" else ""
        target = os.path.join(self.media_dir, f"{config_id}{suffix}{safe_extension(source) or '.bin'}")
        if os.path.abspath(source) != os.path.abspath(target) and not self._is_fresh_copy(source, target):
            try:
                shutil.copy2(source, target)
            except OSError:
                shutil.copyfile(source, target)
        return target

    @staticmethod
    def _is_fresh_copy(source: str, target: str) -> bool:
        try:
            return (os.path.isfile(target)
                    and os.path.getsize(target) == os.path.getsize(source)
                    and int(os.path.getmtime(target)) == int(os.path.getmtime(source)))
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
        for snapshot in (record.get("current", {}), record.get("baseline", {})):
            path = as_text(snapshot.get("attached_media_path"))
            if path and is_plugin_file(path) and os.path.isfile(path):
                delete_file(path)

    def _current(self, config_id=None) -> dict:
        return self.configurations.get(config_id or self.active_id, {}).get("current", {})

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
            if self.active_id not in self.configurations:
                return True
            saved = self._sync_params(self.active_id, "current", self._snapshot_with_media(self.active_id, "current"))
            if not saved:
                self._autosave_dirty = True
            return saved

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

        run_on_queue(task, PLUGINS_QUEUE, max(1, int(delay_ms)))

    def _autosave_tick(self):
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


    @property
    def selector_key(self) -> str:
        return f"{self.SELECTOR_KEY}_{self._ui_revision}"

    def _refresh_ui(self):
        self._ui_revision += 1
        self.plugin.reload_settings_ui()

    def selector_items(self) -> List[str]:
        return [as_text(data.get("name", key)) for key, data in self.configurations.items()]

    def selector_index(self) -> int:
        keys = list(self.configurations)
        return keys.index(self.active_id) if self.active_id in keys else 0

    def _activate(self, config_id: str):
        with self._lock:
            self._autosave_dirty = False
            self.active_id = config_id
            self._load_snapshot(self._current(config_id))
            self._write_index()
            self._collect_orphan_media()
        self.plugin.refresh_chat_menu_item()
        self._refresh_ui()

    def switch(self, index):
        with self._lock:
            keys = list(self.configurations)
            if not _is_int(index) or not 0 <= index < len(keys) or keys[index] == self.active_id:
                return
            if not self._save_active_checked():
                self.plugin._toast("configuration_save_failed")
                self._refresh_ui()
                return
            self._activate(keys[index])

    def _new_id(self) -> str:
        while True:
            config_id = "config_" + uuid.uuid4().hex[:8]
            if config_id not in self.configurations and not os.path.exists(self._config_dir(config_id)):
                return config_id


    @staticmethod
    def normalize_name(name) -> str:
        return " ".join(as_text(name).split())[:MAX_CONFIG_NAME_LENGTH].strip()

    def is_name_taken(self, name, ignore_id=None) -> bool:
        key = self.normalize_name(name).casefold()
        return any(
            as_text(data.get("name", config_id)).strip().casefold() == key
            for config_id, data in self.configurations.items()
            if config_id != ignore_id
        )

    def name_error(self, name, ignore_id=None) -> Optional[str]:
        name = self.normalize_name(name)
        if not name:
            return "configuration_name_invalid"
        if self.is_name_taken(name, ignore_id):
            return "configuration_name_taken"
        return None


    def add(self, name: str, copy_current: bool = False):
        with self._lock:
            taken = self.selector_items()
            name = self.normalize_name(name)
            if name:
                if self.is_name_taken(name):
                    raise ConfigurationError("configuration name is already taken")
            else:
                name = unique_name(self.plugin._tr("configuration_n", n=len(taken) + 1), taken)
            self._require_saved()
            config_id = self._new_id()
            if copy_current:
                source = self._current()
                record = {
                    "name": name,
                    "current": self._clone_with_media(source, config_id, "current"),
                    "baseline": self._clone_with_media(source, config_id, "baseline"),
                }
            else:
                record = {"name": name, "current": dict(SETTING_DEFAULTS), "baseline": dict(SETTING_DEFAULTS)}
            self._store_record(config_id, record)
            self._activate(config_id)

    def create_from_import(self, data, components, name=None):
        with self._lock:
            name = self.normalize_name(name)
            if name and self.is_name_taken(name):
                raise ConfigurationError("configuration name is already taken")
            if not name:
                name = unique_name(self.plugin._tr("imported_configuration"), self.selector_items())
            self._require_saved()
            previous = dict(self._current())
            try:
                self._load_snapshot(SETTING_DEFAULTS)
                self.plugin.transfer.apply_components(data, components)
            except Exception:
                self._load_snapshot(previous)
                raise
            config_id = self._new_id()
            baseline = self._snapshot_with_media(config_id, "baseline")
            self._store_record(config_id, {
                "name": name,
                "current": self._clone_with_media(baseline, config_id, "current"),
                "baseline": baseline,
                "origin": self.ORIGIN_IMPORTED,
            })
            self._activate(config_id)

    def is_imported(self, config_id: Optional[str] = None) -> bool:
        record = self.configurations.get(config_id or self.active_id) or {}
        return record.get("origin") == self.ORIGIN_IMPORTED

    def import_data(self, data, components, as_new=False, name=None):
        remote = getattr(self.plugin, "remote", None)
        if remote is not None and not remote.allows():
            raise ConfigurationError("plugin update required")
        if not FEATURES.on("config_import"):
            raise ConfigurationError("configuration import is switched off")
        if as_new:
            self.create_from_import(data, components, name=name)
        else:
            with self._lock:
                self.plugin.transfer.apply_components(data, components)
                if not self._save_active_checked():
                    self.plugin.log("Prefixfy import applied but not yet saved: retry scheduled")
        if "schedule" in components:
            section = extract_component(data, "schedule")
            if section is not None:
                new_name = as_text(self.configurations[self.active_id].get("name")) if as_new else None
                self.plugin.import_schedule_section(section, new_name)


    def rename(self, config_id, name) -> bool:
        with self._lock:
            config_id = str(config_id)
            if config_id not in self.configurations or self.name_error(name, ignore_id=config_id):
                return False
            old_name = as_text(self.configurations[config_id].get("name"))
            self.configurations[config_id]["name"] = self.normalize_name(name)
            self._write_name(config_id)
            self.generation += 1
        self.plugin.rename_in_schedule(old_name, self.configurations[config_id]["name"])
        self._refresh_ui()
        return True

    def inactive_ids(self) -> List[str]:
        return [config_id for config_id in self.configurations if config_id != self.active_id]

    def delete_many(self, config_ids) -> int:
        with self._lock:
            selected = [cid for cid in dict.fromkeys(str(c) for c in config_ids)
                        if cid in self.configurations and cid != self.active_id]
            if not selected:
                return 0
            removed = []
            tombs = []
            for config_id in selected:
                tomb = self._bury(config_id)
                if tomb:
                    tombs.append(tomb)
                removed.append(self.configurations.pop(config_id))
            self._failed_writes = {m for m in self._failed_writes if m[0] not in selected}
            self._write_index()
            for tomb in tombs:
                shutil.rmtree(tomb, ignore_errors=True)
            for record in removed:
                self._remove_media_of(record)
        self.generation += 1
        self.plugin.prune_chat_bindings()
        self._refresh_ui()
        self.plugin._toast("configuration_deleted", n=len(selected))
        return len(selected)

    def reset_active_components(self, components, plugin_defaults: bool = False):
        self._save_active_checked()
        config = self.configurations.get(self.active_id)
        if not config:
            return
        baseline = config.get("baseline", {})
        if plugin_defaults and self.is_imported(self.active_id):
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
                    {"attached_media_path": baseline_media}, self.active_id, "current"
                ).get("attached_media_path", "")
            elif not baseline.get("attached_media_enabled", False):
                current["attached_media_path"] = ""
        with self._lock:
            if not self._sync_params(self.active_id, "current", current):
                self._retry_later()
            self._load_snapshot(current)
        self.plugin.refresh_chat_menu_item()
        self._refresh_ui()
        self.plugin._toast("configuration_restored")


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
            self.plugin._tr("add_configuration"), confirm,
            hint=self.plugin._tr("configuration_name_hint"),
        )

    def _ask_add_source(self, name: str):
        def confirm(_selected, copy_current):
            self._create(name, copy_current)
            return True

        shown = self.plugin.show_checklist(
            self.plugin._tr("new_configuration_source_title"), [], confirm,
            message=self.plugin._tr("new_configuration_source_message"),
            extra=(self.plugin._tr("new_configuration_copy_current"), False),
            positive=self.plugin._tr("create"),
        )
        if not shown:
            self._create(name, False)

    def _create(self, name: str, copy_current: bool):
        try:
            self.add(name, copy_current)
        except ConfigurationSaveError as exc:
            self.plugin.log(f"Configuration creation aborted: {exc}")
            self.plugin._toast("configuration_save_failed")
        except Exception as exc:
            self.plugin.log(f"Configuration creation failed: {exc}")
            self.plugin._toast("operation_failed")

    def request_rename(self, view=None):
        current = self.configurations.get(self.active_id, {})
        current_name = as_text(current.get("name", self.active_id))

        def confirm(value, editor):
            if self.normalize_name(value) == current_name:
                return True
            error = self.name_error(value, ignore_id=self.active_id)
            if error:
                editor.setError(self.plugin._tr(error))
                return False
            return self.rename(self.active_id, value)

        self.plugin.show_text_dialog(
            self.plugin._tr("rename_configuration"), confirm, text=current_name,
        )

    def request_delete(self, view=None):
        ids = self.inactive_ids()
        if not ids:
            self.plugin._toast("no_inactive_configurations")
            return
        if len(ids) == 1:
            self._confirm_delete_single(ids[0])
            return
        rows = [(as_text(self.configurations[cid].get("name", cid)), False, True) for cid in ids]

        def confirm(selected, _extra):
            chosen = [ids[index] for index in selected]
            if not chosen:
                self.plugin._toast("configuration_nothing_selected")
                return False
            self.delete_many(chosen)
            return True

        self.plugin.show_checklist(
            self.plugin._tr("delete_configurations"), rows, confirm,
            message=self.plugin._tr("delete_configurations_select"), positive=self.plugin._tr("delete"),
        )

    def _confirm_delete_single(self, config_id: str):
        activity = self.plugin._dialog_activity()
        if not activity:
            return
        name = self.configurations.get(config_id, {}).get("name", config_id)
        builder = AlertDialogBuilder(activity)
        builder.set_title(self.plugin._tr("delete_configuration"))
        builder.set_message(self.plugin._tr("delete_configuration_confirm", name=name))

        def confirm(bld, which):
            bld.dismiss()
            self.delete_many([config_id])

        builder.set_positive_button(self.plugin._tr("delete"), confirm)
        builder.set_negative_button(self.plugin._tr("cancel"), lambda b, w: b.dismiss())
        self.plugin._show_builder(builder)

    def append_settings(self, settings: list):
        tr = self.plugin._tr
        settings.append(Header(text=tr("configurations")))
        has_several = len(self.configurations) >= 2
        if has_several:
            selector_key, selector_index = self.selector_key, self.selector_index()
            try:
                self.plugin.set_setting(selector_key, selector_index)
            except Exception as exc:
                self.plugin.log(f"Prefixfy configuration selector state failed: {exc}")
            settings.append(Selector(
                key=selector_key,
                text=tr("active_configuration"),
                default=selector_index,
                items=self.selector_items(),
                icon="msg_settings",
                on_change=self.switch,
            ))
        settings.append(Text(
            text=tr("add_configuration"),
            subtext=tr("add_configuration_subtext"),
            icon="msg_add",
            on_click=self.request_add,
        ))
        settings.append(Text(
            text=tr("rename_configuration"),
            subtext=tr("rename_configuration_subtext"),
            icon="msg_edit",
            on_click=self.request_rename,
        ))
        if has_several:
            settings.append(Text(
                text=tr("delete_configurations"),
                subtext=tr("delete_configurations_subtext"),
                icon="msg_delete",
                on_click=self.request_delete,
            ))


_VERSION_RE = re.compile(r"[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4}")
_HEX64_RE = re.compile(r"[0-9a-f]{64}")
_HEX128_RE = re.compile(r"[0-9a-f]{128}")
_MANIFEST_FILE_RE = re.compile(r"[A-Za-z0-9._\-]{1,80}")


def parse_version(value) -> Tuple[int, ...]:
    text = as_text(value).strip()
    if not _VERSION_RE.fullmatch(text):
        return ()
    return tuple(int(part) for part in text.split("."))


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


def _verify_signed(raw: bytes, domain: bytes, what: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if not UPDATE_PUBLIC_KEYS:
        raise ValueError("no update public key configured")
    signed = json.loads(raw.decode("utf-8"))
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
    if name and not _MANIFEST_FILE_RE.fullmatch(name):
        raise ValueError("manifest: bad file name")
    return {
        "serial": _manifest_int(body, "serial"),
        "issued_at": _manifest_int(body, "issued_at"),
        "version": version,
        "sha256": sha256,
        "sha512": sha512,
        "file": name,
        "signed": signed,
    }


def verify_flags(raw: bytes) -> Dict[str, Any]:
    signed, body = _verify_signed(raw, FLAGS_DOMAIN, "flags")
    if _manifest_int(body, "format") != FLAGS_FORMAT:
        raise ValueError("unsupported flags format")
    values = body.get("flags")
    if not isinstance(values, dict) or len(values) > FLAGS_MAX_COUNT:
        raise ValueError("flags: bad flags object")
    known: Dict[str, bool] = {}
    for name, value in values.items():
        if name in FEATURE_FLAGS and isinstance(value, bool) and _FLAG_NAME_RE.fullmatch(name):
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
        "issued_at": _manifest_int(body, "issued_at"),
        "flags": known,
        "accounts": accounts,
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
    """ids_enc = base64(nonce[16] + XOR(zlib(json ids), HMAC-SHA256 keystream)). Подлинность даёт подпись файла."""
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
    values = json.loads(plain.decode("utf-8"))
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
        except (ValueError, zlib.error, UnicodeDecodeError) as exc:
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
    return {
        "serial": _manifest_int(body, "serial"),
        "issued_at": _manifest_int(body, "issued_at"),
        "ids": frozenset(ids),
        "signed": signed,
    }


def device_account_ids(logger=None) -> Optional[frozenset]:
    """IDs of every Telegram account signed in on this device, or None if they can't be read."""
    try:
        config_class = find_class("org.telegram.messenger.UserConfig")
        try:
            count = int(config_class.MAX_ACCOUNT_COUNT)
        except Exception:
            count = 16
        ids = set()
        for index in range(max(1, min(count, 32))):
            config = config_class.getInstance(index)
            if config is None or not bool(config.isClientActivated()):
                continue
            user_id = java_int(config.getClientUserId())
            if user_id and user_id > 0:
                ids.add(user_id)
        return frozenset(ids)
    except Exception as exc:
        if logger:
            logger(f"Prefixfy device accounts lookup failed: {exc}")
        return None


class _SameHostRedirect(urllib.request.HTTPRedirectHandler):

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parts = urllib.parse.urlsplit(newurl)
        if parts.scheme != "https" or (parts.hostname or "").lower() not in UPDATE_ALLOWED_HOSTS:
            raise urllib.error.URLError("redirect to a foreign host blocked")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _self_file_sha256() -> Optional[str]:
    path = globals().get("__file__")
    if not path:
        return None
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        return None


class RemoteControl:

    def __init__(self, plugin):
        self.plugin = plugin
        self.enabled = bool(UPDATE_PUBLIC_KEYS)
        self._lock = threading.Lock()
        self._busy = threading.Lock()
        self._stop = threading.Event()
        self._state: Optional[Dict[str, Any]] = None
        self._last_ok = float("-inf")
        self._last_request = -REMOTE_MANUAL_COOLDOWN
        self._notified = False
        self._cache_path = os.path.join(get_plugins_dir(), "Prefixfy_remote.json")
        self._self_hash = _self_file_sha256()
        if self._self_hash is None:
            self.plugin.log("Prefixfy: could not hash own file; falling back to version-only integrity check")
        self._device_ids: frozenset = frozenset()
        self._dev_checked = float("-inf")
        self._dev_lock = threading.Lock()
        self._bl_ids: frozenset = frozenset()
        self._bl_serial = -1
        self._bl_known = False
        self._bl_path = os.path.join(get_plugins_dir(), BLACKLIST_CACHE_FILE)
        self._load_cache()
        self._flags_path = os.path.join(get_plugins_dir(), FLAGS_CACHE_FILE)
        self._load_flags_cache()
        self._load_blacklist_cache()
        self._poll_devices(notify=False, force=True)

    def start(self):
        if not self.enabled:
            self.plugin.log("Prefixfy is blocked: no update public key in this build")
            return
        self._stop.set()
        self._stop = stop = threading.Event()
        threading.Thread(target=self._run, args=(stop,), name="PrefixfyRemote", daemon=True).start()

    def stop(self):
        self._stop.set()

    def _run(self, stop):
        while not stop.is_set():
            fetched = self.refresh()
            stop.wait(REMOTE_CHECK_INTERVAL if fetched and not self.outdated() else REMOTE_RETRY_INTERVAL)

    def request_refresh(self):
        if not self.enabled:
            return
        now = time.monotonic()
        if now - self._last_request < REMOTE_MANUAL_COOLDOWN:
            return
        self._last_request = now
        threading.Thread(target=self.refresh, name="PrefixfyRemoteNow", daemon=True).start()

    def ensure_fresh(self):
        if time.monotonic() - self._last_ok >= REMOTE_CHECK_INTERVAL:
            self.request_refresh()

    @staticmethod
    def _download(name: str, limit: int = REMOTE_MAX_BYTES) -> bytes:
        import ssl
        request = urllib.request.Request(
            f"{UPDATE_BASE_URL}{name}?t={int(time.time())}",
            headers={"User-Agent": f"Prefixfy/{__version__}", "Cache-Control": "no-cache"},
        )
        opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
            _SameHostRedirect(),
        )
        deadline = time.monotonic() + REMOTE_TOTAL_TIMEOUT
        chunks: List[bytes] = []
        total = 0
        with opener.open(request, timeout=REMOTE_TIMEOUT) as response:
            final = urllib.parse.urlsplit(response.geturl())
            if final.scheme != "https" or (final.hostname or "").lower() not in UPDATE_ALLOWED_HOSTS:
                raise ValueError("unexpected final host")
            while True:
                if time.monotonic() > deadline:
                    raise TimeoutError(f"{name} download took too long")
                chunk = response.read(8192)
                if not chunk:
                    break
                total += len(chunk)
                if total > limit:
                    raise ValueError(f"{name} is too large")
                chunks.append(chunk)
        return b"".join(chunks)

    def refresh(self) -> bool:
        if not self.enabled:
            return False
        if not self._busy.acquire(blocking=False):
            return True
        try:
            return self._refresh()
        finally:
            self._busy.release()

    def _snapshot(self) -> Tuple[bool, str]:
        return self.blocked(), self.latest_version()

    def _refresh(self) -> bool:
        try:
            state = verify_manifest(self._download(MANIFEST_FILE))
            with self._lock:
                known = self._state["serial"] if self._state else -1
            if state["serial"] < known:
                raise ValueError(f"manifest rollback rejected ({state['serial']} < {known})")
        except Exception as exc:
            self.plugin.log(f"Prefixfy remote check failed: {exc}")
            self._announce()
            return False
        before = self._snapshot()
        with self._lock:
            self._state = state
        self._last_ok = time.monotonic()
        self._save_cache()
        self._refresh_blacklist()
        after = self._snapshot()
        if after[0] != before[0]:
            self._announce()
        if after != before:
            try:
                self.plugin.reload_settings_ui()
            except Exception as exc:
                self.plugin.log(f"Prefixfy settings refresh failed: {exc}")
        self._refresh_flags()
        return True

    def _refresh_flags(self):
        try:
            state = verify_flags(self._download(FLAGS_FILE))
            changed = FEATURES.apply(state["flags"], state["serial"], state["accounts"])
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                self.plugin.log(f"Prefixfy flags check failed: HTTP {exc.code}")
            return
        except Exception as exc:
            self.plugin.log(f"Prefixfy flags check failed: {exc}")
            return
        self._save_flags_cache(state["signed"])
        if not changed:
            return
        self.plugin.log(f"Prefixfy flags updated (serial {state['serial']}): {', '.join(FEATURES.overridden()) or 'defaults'}")
        self.plugin._on_features_changed()

    def _bl_hit(self, ids) -> bool:
        return bool(ids and self._bl_ids and not ids.isdisjoint(self._bl_ids))

    def blacklisted(self) -> bool:
        self._poll_devices()
        return self._bl_hit(self._device_ids)

    def _poll_devices(self, notify: bool = True, force: bool = False):
        if not force and time.monotonic() - self._dev_checked < DEVICE_RECHECK_INTERVAL:
            return
        if not self._dev_lock.acquire(blocking=False):
            return
        features_changed = hit_changed = False
        try:
            self._dev_checked = time.monotonic()
            ids = device_account_ids(self.plugin.log)
            if ids is None or ids == self._device_ids:
                return
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

    def _refresh_blacklist(self):
        try:
            state = verify_blacklist(self._download(BLACKLIST_FILE, BLACKLIST_MAX_BYTES))
            if state["serial"] < self._bl_serial:
                raise ValueError(f"blacklist rollback rejected ({state['serial']} < {self._bl_serial})")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                self._bl_known = True
            else:
                self.plugin.log(f"Prefixfy blacklist check failed: HTTP {exc.code}")
            return
        except Exception as exc:
            self.plugin.log(f"Prefixfy blacklist check failed: {exc}")
            return
        self._bl_ids = state["ids"]
        self._bl_serial = state["serial"]
        self._bl_known = True
        try:
            temp = self._bl_path + ".tmp"
            with open(temp, "w", encoding="utf-8") as handle:
                json.dump(state["signed"], handle)
            os.replace(temp, self._bl_path)
        except OSError as exc:
            self.plugin.log(f"Prefixfy blacklist cache not saved: {exc}")

    def _load_blacklist_cache(self):
        try:
            with open(self._bl_path, "rb") as handle:
                state = verify_blacklist(handle.read(BLACKLIST_MAX_BYTES + 1))
        except (OSError, ValueError):
            return
        self._bl_ids = state["ids"]
        self._bl_serial = state["serial"]
        self._bl_known = True

    def _load_flags_cache(self):
        try:
            with open(self._flags_path, "rb") as handle:
                state = verify_flags(handle.read(REMOTE_MAX_BYTES + 1))
            FEATURES.apply(state["flags"], state["serial"], state["accounts"])
        except (OSError, ValueError):
            pass

    def _save_flags_cache(self, signed: Dict[str, Any]):
        try:
            temp = self._flags_path + ".tmp"
            with open(temp, "w", encoding="utf-8") as handle:
                json.dump(signed, handle)
            os.replace(temp, self._flags_path)
        except OSError as exc:
            self.plugin.log(f"Prefixfy flags cache not saved: {exc}")

    def _load_cache(self):
        self._state = None
        if not self.enabled:
            return
        try:
            with open(self._cache_path, "rb") as handle:
                self._state = verify_manifest(handle.read(REMOTE_MAX_BYTES + 1))
        except (OSError, ValueError):
            self._state = None

    def _save_cache(self):
        with self._lock:
            signed = self._state["signed"] if self._state else None
        if signed is None:
            return
        try:
            temp = self._cache_path + ".tmp"
            with open(temp, "w", encoding="utf-8") as handle:
                json.dump(signed, handle)
            os.replace(temp, self._cache_path)
        except OSError as exc:
            self.plugin.log(f"Prefixfy remote cache not saved: {exc}")

    def _field(self, key: str, default=None):
        with self._lock:
            return self._state.get(key, default) if self._state else default

    def required_version(self) -> str:
        return self.latest_version()

    def latest_version(self) -> str:
        return ".".join(map(str, self._field("version", ())))

    def latest_checksum(self) -> str:
        return self._field("sha256", "") or ""

    def mismatched(self) -> bool:
        latest = self._field("version", ())
        if not latest:
            return False
        if parse_version(__version__) != latest:
            return True
        expected_sha = self._field("sha256", "")
        if expected_sha and not self._self_hash:
            return True
        if expected_sha and self._self_hash and expected_sha != self._self_hash:
            return True
        return False

    def verified(self) -> bool:
        with self._lock:
            has_state = self._state is not None
        return has_state and self._bl_known and time.monotonic() - self._last_ok <= REMOTE_MAX_AGE

    def blocked(self) -> bool:
        if not self.enabled or not self.verified():
            return True
        if self.blacklisted():
            return True
        return self.mismatched()

    def outdated(self) -> bool:
        return self.blocked()

    def allows(self, account=None) -> bool:
        self.ensure_fresh()
        return not self.blocked()

    def notice(self) -> Tuple[str, Dict[str, Any]]:
        if self.enabled and self.verified() and self.blacklisted():
            return "account_blocked_subtext", {}
        if self._field("version", ()) and self.mismatched():
            return "update_required_subtext", {"version": self.required_version()}
        return "verify_required_subtext", {}

    def _announce(self):
        if not self.blocked():
            self._notified = False
            return
        if self._notified:
            return
        self._notified = True
        try:
            key, kwargs = self.notice()
            self.plugin._toast(key, **kwargs)
        except Exception as exc:
            self.plugin.log(f"Prefixfy remote notice failed: {exc}")


class PrefixfyPlugin(BasePlugin):
    def on_plugin_load(self):
        self.settings = PrefixfySettings(self)
        self.localization = LocalizationManager(self)
        self.runtime_manager = RuntimeManager(self)
        self.transfer = ConfigTransfer(self)
        self.remote = RemoteControl(self)
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
        self.configurations = ConfigurationsManager(self)
        self.runtime_manager.rebuild()

        self.transfer.register_file_handler()
        self.add_on_send_message_hook()
        self.refresh_chat_menu_item()
        self._install_activity_result_hook()
        self._install_edit_message_hook()
        self.remote.start()
        self.log(f"Prefixfy {__version__} loaded ({self.localization.language()})")
        self._dbg(f"{__version__} loaded, debug logging on")

    def on_plugin_unload(self):
        remote = getattr(self, "remote", None)
        if remote is not None:
            remote.stop()
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
                hook.unhook()
            except Exception:
                pass
        self._prefixfy_hooks = []
        self._skip_once = None
        self._dialog_kinds.clear()
        self._chat_titles.clear()
        self._remove_chat_menu_item()
        lock = getattr(self, "_internal_lock", None)
        if lock is not None:
            with lock:
                self._internal_sends.clear()
                self._edit_seen = {}

    def _reset_transient_settings(self):
        for key, default in TRANSIENT_SETTING_DEFAULTS.items():
            try:
                self.set_setting(key, default)
            except Exception as exc:
                self.log(f"Prefixfy transient setting reset failed ({key}): {exc}")

    def _remove_stale_files(self):
        cache_dir = get_cache_dir()
        for name in ("Prefixfy_tmp", "Prefixfy_imports", "Prefixfy_exports", "Prefixfy"):
            shutil.rmtree(os.path.join(cache_dir, name), ignore_errors=True)

    def _install_activity_result_hook(self):
        plugin = self

        class ActivityResultHook(MethodHook):
            def after_hooked_method(self, param):
                try:
                    plugin.transfer.handle_activity_result(param.args[0], param.args[1], param.args[2])
                except Exception as exc:
                    plugin.log(f"Activity result handling failed: {exc}")

        launch_class = find_class("org.telegram.ui.LaunchActivity")
        if launch_class is None:
            self.log("LaunchActivity not found: file pickers are unavailable")
            return
        hooks = self.hook_all_methods(launch_class, "onActivityResult", ActivityResultHook())
        if hooks:
            self._prefixfy_hooks.extend(hooks)

    def _install_edit_message_hook(self):
        plugin = self

        edit_class = find_class("org.telegram.tgnet.TLRPC$TL_messages_editMessage")

        def is_edit_request(request) -> bool:
            if edit_class is not None:
                try:
                    return bool(edit_class.isInstance(request))
                except Exception:
                    pass
            return plugin._class_name(request).endswith("TL_messages_editMessage")

        class EditRequestHook(MethodHook):
            def before_hooked_method(self, param):
                try:
                    if len(param.args) and param.args[0] is not None and is_edit_request(param.args[0]):
                        plugin._on_edit_request(param, param.args[0])
                except Exception as exc:
                    plugin.log(f"Prefixfy edit hook failed: {exc}")

        manager_class = find_class("org.telegram.tgnet.ConnectionsManager")
        if manager_class is None:
            self.log("Prefixfy edit: ConnectionsManager not found, message editing is unavailable")
            return
        try:
            hooks = self.hook_all_methods(manager_class, "sendRequest", EditRequestHook())
            hooks = list(hooks) if hooks else []
        except Exception as exc:
            self.log(f"Prefixfy edit: hooking sendRequest failed: {exc}")
            return
        self._prefixfy_hooks.extend(hooks)

    def handle_setting_changed(self, key):
        if key in TRANSIENT_SETTING_DEFAULTS:
            return
        self.runtime_manager.on_setting_changed()
        configurations = getattr(self, "configurations", None)
        if configurations is not None and key in ConfigurationsManager.CONFIG_KEYS:
            configurations.schedule_autosave()

    def _tr(self, key, **kwargs):
        return self.localization.tr(key, **kwargs)

    def _toast(self, key, fragment=None, **kwargs):
        BulletinHelper.show_info(self._tr(key, **kwargs), fragment or get_last_fragment())

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
        fragment = fragment or get_last_fragment()
        return fragment.getParentActivity() if fragment else None

    def _show_builder(self, builder) -> bool:
        try:
            builder.show()
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
        neutral_ready = False
        if neutral:
            set_neutral = getattr(builder, "set_neutral_button", None)
            if set_neutral is None:
                self.log("Prefixfy: set_neutral_button is not supported by this SDK, using the empty-field fallback")
            else:
                try:
                    set_neutral(neutral[0], lambda bld, which: neutral[1](editor) is not False and bld.dismiss())
                    neutral_ready = True
                except Exception as exc:
                    self.log(f"Prefixfy: neutral button failed ({exc}), using the empty-field fallback")
        if neutral and not neutral_ready:
            message = f"{message}\n\n{self._tr('empty_means_default')}" if message else self._tr("empty_means_default")
        if message:
            builder.set_message(message)
        builder.set_view(editor)

        def ok(bld, which):
            value = editor.getText().toString()
            if neutral and not neutral_ready and not value.strip():
                if neutral[1](editor) is not False:
                    bld.dismiss()
                return
            if on_confirm(value, editor) is not False:
                bld.dismiss()

        def cancel(bld, which):
            bld.dismiss()
            if on_cancel:
                on_cancel()

        builder.set_positive_button(positive or self._tr("save"), ok)
        builder.set_negative_button(self._tr("cancel"), cancel)
        return self._show_builder(builder)

    def show_checklist(self, title, rows, on_confirm, *, message=None, extra=None, positive=None,
                       fragment=None, on_cancel=None) -> bool:
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

        def ok(bld, which):
            selected = [i for i, box in enumerate(boxes) if box.isChecked() and rows[i][2]]
            extra_checked = bool(extra_box and extra_box.isEnabled() and extra_box.isChecked())
            if on_confirm(selected, extra_checked) is not False:
                bld.dismiss()

        def cancel(bld, which):
            bld.dismiss()
            if on_cancel:
                on_cancel()

        builder.set_positive_button(positive or self._tr("save"), ok)
        builder.set_negative_button(self._tr("cancel"), cancel)
        return self._show_builder(builder)


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

    def _dialog_id_from_params(self, params) -> Optional[int]:
        dialog_id = to_dialog_id(getattr(params, "peer", None))
        return dialog_id if dialog_id is not None else self._current_dialog_id()

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
            ("_chat_toggle_menu_id", "chat_menu", self._toggle_chat_from_menu, True),
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
                menu_type=MenuItemType.CHAT_ACTION_MENU, text=self._tr(key), on_click=handler, priority=priority,
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
        BulletinHelper.show_info(self._tr("capture_enabled" if enable else "capture_disabled"), fragment)


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
            cached = self._schedule_cache = (raw, parse_schedule(raw)[0])
        return cached[1]

    def prune_chat_bindings(self):
        configs = getattr(self, "configurations", None)
        bindings = self._chat_bindings()
        if configs is None or not bindings:
            return
        alive = {chat: cid for chat, cid in bindings.items() if cid in configs.configurations}
        if len(alive) != len(bindings):
            self.set_setting(CHAT_CONFIGS_KEY, dump_chat_configs(alive))

    def rename_in_schedule(self, old_name: str, new_name: str):
        text, changed = rename_schedule_target(as_text(self.get_setting(SCHEDULE_KEY, "")), old_name, new_name)
        if changed:
            self.set_setting(SCHEDULE_KEY, text)

    def export_schedule_section(self) -> dict:
        configs = self.configurations
        chats = {}
        for dialog, config_id in self._chat_bindings().items():
            record = configs.configurations.get(config_id)
            if record:
                chats[dialog] = as_text(record.get("name"))
        active = configs.configurations.get(configs.active_id) or {}
        return {"source": as_text(active.get("name")), "chats": chats, "rules": as_text(self.get_setting(SCHEDULE_KEY, ""))}

    def import_schedule_section(self, section: dict, new_name: Optional[str] = None):
        configs = self.configurations
        source = as_text(section.get("source")).strip()
        mapping = dict(self._chat_bindings())
        for dialog, name in section.get("chats", {}).items():
            name = as_text(name).strip()
            target = new_name if new_name and source and name.casefold() == source.casefold() else name
            config_id = configs.find_id_by_name(target)
            if config_id:
                mapping[str(dialog)] = config_id
        self.set_setting(CHAT_CONFIGS_KEY, dump_chat_configs(mapping))
        rules = as_text(section.get("rules", ""))
        if new_name and source:
            rules = rename_schedule_target(rules, source, new_name)[0]
        self.set_setting(SCHEDULE_KEY, rules)

    def _runtime_for_chat(self, runtime, dialog_id):
        configs = getattr(self, "configurations", None)
        if configs is None:
            return runtime
        config_id = self._chat_bindings().get(str(dialog_id)) if dialog_id is not None and FEATURES.on("chat_configs") else None
        if config_id is not None and config_id not in configs.configurations:
            config_id = None
        if config_id is None:
            rules = self._schedule_rules() if FEATURES.on("schedule") else None
            if rules:
                config_id = schedule_match(rules, datetime.now(), configs.find_id_by_name)
        if config_id is None or config_id == configs.active_id:
            return runtime
        return configs.runtime_for(config_id) or runtime

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
        key = str(dialog_id)
        ids = list(configs.configurations)
        bound = self._chat_bindings().get(key)
        items = [("✓ " if bound not in ids else "") + self._tr("chat_config_auto")]
        items += [("✓ " if config_id == bound else "") + as_text(configs.configurations[config_id].get("name", config_id)) for config_id in ids]
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
        builder.set_negative_button(self._tr("cancel"), lambda bld, which: bld.dismiss())
        self._show_builder(builder)

    def _show_schedule_editor(self, view=None):
        configs = self.configurations

        def save(value, editor):
            rules, errors = parse_schedule(value)
            problem = None
            if errors:
                number, code = errors[0]
                problem = (number, self._tr(code, n=MAX_SCHEDULE_RULES))
            else:
                for rule in rules:
                    if configs.find_id_by_name(rule[3]) is None:
                        problem = (rule[4], self._tr("schedule_err_config", name=rule[3]))
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
        pending = self._skip_once
        if pending is not None and pending[0] == dialog_id and pending[1] > time.monotonic():
            self._skip_once = None
            self._toast("skip_once_off", fragment)
        else:
            armed = (dialog_id, time.monotonic() + SKIP_ONCE_TTL)
            self._skip_once = armed
            self._schedule_skip_expiry(armed)
            self._toast("skip_once_on", fragment)

    def _schedule_skip_expiry(self, armed):
        ref = weakref.ref(self)

        def task():
            plugin = ref()
            if plugin is None or plugin._skip_once is not armed:
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
            message = "chat_removed"
        else:
            ids.add(dialog_id)
            message = "chat_added"
        self.settings.set_disabled_chat_ids(ids)
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
        if enabled:
            index = 0
        else:
            current = self.localization.language()
            index = LANGUAGE_MODES.index(current) if current in LANGUAGE_MODES else LANGUAGE_MODES.index("en")
        self._apply_language_index(index)

    def _on_language_select_change(self, new_index):
        if self.settings.language_index() == 0:
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
        hint = self._tr("custom_emoji_hint")
        return f"{text}\n\n{hint}" if first else f"{hint}\n\n{text}"

    def _show_separator_editor(self, view=None):
        def save(value, editor):
            separators = [item.strip() for item in value.split(",") if item.strip()]
            if not separators:
                return None
            self.settings.set("custom_emojis", ", ".join(separators), reload_settings=True)

        current = as_text(self.settings.get("custom_emojis"))
        self.show_text_dialog(
            self._tr("custom_separator_title"), save,
            message=self._with_emoji_hint(self._tr('custom_separator_message'), first=True),
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
            rules, errors = parse_conditional_masks(value)
            if errors:
                number, code = errors[0]
                if code == "limit":
                    editor.setError(self._tr("regex_limit", n=MAX_CONDITIONAL_MASKS, m=MAX_REGEX_LENGTH))
                elif code == "format":
                    editor.setError(self._tr("conditional_masks_format", n=number))
                else:
                    reason = self._tr("masks_list_invalid") if code == "mask" else self._tr("regex_invalid", error=code[len("regex:"):])
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
                editor.setError(self._tr("regex_limit", n=MAX_REGEX_EXCEPTIONS, m=MAX_REGEX_LENGTH))
                return False
            for line in lines:
                try:
                    re.compile(line)
                except re.error as exc:
                    editor.setError(self._tr("regex_invalid", error=str(exc)))
                    return False
                if not regex_is_safe(line):
                    editor.setError(self._tr("regex_invalid", error=REGEX_UNSAFE_REASON))
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
        words = self._tr("separator_preview_words").split()
        if len(words) < 2:
            words = ["Hello", "world"]
        parts, index = [], 0
        for position, word in enumerate(words):
            parts.append(word)
            if position < len(words) - 1:
                for _ in range(count):
                    parts.append(separators[index % len(separators)])
                    index += 1
        return " ".join(parts)

    def _exceptions_subtext(self) -> str:
        values = len(parse_lines(self.settings.get("exceptions")))
        chats = len(self.settings.disabled_chat_ids())
        if values == 0 and chats == 0:
            return self._tr("exceptions_hint")
        return self._tr("exceptions_count", n=values, m=chats)

    @staticmethod
    @lru_cache(maxsize=32)
    def _icon(name: str, fallback: str = "msg_settings") -> str:
        try:
            find_class("org.telegram.messenger.R$drawable").getField(name)
            return name
        except Exception:
            return fallback

    def _switch(self, key: str, text: str, subtext: str, icon: str, reload_settings: bool = False):
        return Switch(
            key=key, text=text, default=PrefixfySettings.DEFAULTS[key], subtext=subtext, icon=icon,
            on_change=self._bool_handler(key, reload_settings),
        )

    def _settings_configurations(self) -> List[Any]:
        tr, transfer = self._tr, self.transfer
        items: List[Any] = []
        self.configurations.append_settings(items)
        short = tr("configuration_short")
        if FEATURES.on("config_import"):
            items.append(Text(text=tr("import_configuration"), subtext=short, icon="msg_download", on_click=transfer.request_import))
        items += [
            Text(text=tr("export_configuration"), subtext=short, icon=self._icon("msg_upload", "msg_document"), on_click=transfer.request_export),
            Text(text=tr("reset_configuration"), subtext=short, icon=self._icon("msg_retry"), on_click=transfer.request_reset),
        ]
        if FEATURES.on("schedule"):
            items.append(Text(text=tr("schedule"), subtext=self._schedule_subtext(), icon=self._icon("msg_calendar", "msg_recent"), on_click=self._show_schedule_editor))
        return items

    def _settings_scope(self) -> List[Any]:
        tr = self._tr
        items: List[Any] = [
            Header(text=tr("section_scope")),
            self._switch("process_message", tr("message"), tr("message_subtext"), "msg_text"),
            self._switch("process_media", tr("media"), tr("media_subtext"), "msg_image"),
        ]
        edit_on = FEATURES.on("edit_processing")
        if edit_on:
            items.append(self._switch("process_edit", tr("edit_message"), tr("edit_message_subtext"), "msg_edit", True))
        if edit_on and self.settings.get("process_edit"):
            items += [
                self._switch("process_edit_message", tr("edit_text_toggle"), tr("edit_text_toggle_subtext"), "msg_text"),
                self._switch("process_edit_media", tr("edit_media_toggle"), tr("edit_media_toggle_subtext"), "msg_image"),
                self._switch("skip_once_on_edit", tr("skip_once_on_edit"), tr("skip_once_on_edit_subtext"), "msg_edit"),
            ]
        if FEATURES.on("chat_type_rules"):
            items.append(Text(text=tr("chat_types"), subtext=self._chat_types_subtext(), icon=self._icon("msg_groups", "msg_info"), on_click=self._show_chat_types_editor))
        return items

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
                    items=[tr("rotation_random"), tr("rotation_sequential")], icon="msg_edit",
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
            self._switch("text_style_enabled", tr("enable_text_style"), tr("text_style_subtext"), "msg_palette", True),
        ]
        if self.settings.get("text_style_enabled"):
            items.append(self._switch("text_style_random", tr("random_style"), tr("random_style_subtext"), "msg_palette", True))
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
            items.append(self._switch("text_style_translit", tr("style_translit"), tr("style_translit_subtext"), "msg_text", True))
            items.append(Text(text=tr("style_words"), subtext=self._style_words_subtext(), icon="msg_edit", on_click=self._show_style_words_editor))
        return items

    def _settings_separator(self) -> List[Any]:
        tr = self._tr
        items: List[Any] = [
            Header(text=tr("separator")),
            self._switch("separator_enabled", tr("enable_separator"), tr("enable_separator_subtext"), "msg_palette", True),
        ]
        if self.settings.get("separator_enabled"):
            items += [
                Text(text=tr("separator_set"), subtext=self._separator_preview_text(), icon="msg_edit", on_click=self._show_separator_editor),
                Input(
                    key="emoji_count", text=tr("separator_count"), default=str(self.settings.separator_count()),
                    subtext=tr("separator_count_subtext"), icon="msg_palette",
                    on_change=self._on_separator_count_change,
                ),
            ]
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
            self._switch("ignore_special", tr("ignore_special"), tr("ignore_special_subtext"), "msg_info"),
            self._switch("ignore_emoji_only", tr("ignore_emoji_only"), tr("ignore_emoji_only_subtext"), "msg_info"),
        ]
        return items

    def _settings_media(self) -> List[Any]:
        if not FEATURES.on("attached_media"):
            return []
        tr, transfer = self._tr, self.transfer
        items: List[Any] = [Header(text=tr("media_attachment"))]
        if not transfer.media_exists():
            items.append(Text(text=tr("import_media"), subtext=tr("media_file_none"), icon="msg_download", on_click=transfer.request_media_import))
            return items
        name = as_text(self.settings.get("attached_media_name")) or os.path.basename(transfer.media_path())
        items += [
            Switch(
                key="attached_media_enabled", text=tr("enable_media_attachment"),
                default=PrefixfySettings.DEFAULTS["attached_media_enabled"],
                subtext=tr("enable_media_attachment_subtext"), icon="msg_image",
                on_change=self._on_media_enabled_change,
            ),
            Text(text=tr("media_file"), subtext=name or tr("media_file_none"), icon="msg_document", on_click=transfer.request_media_import),
            Text(text=tr("delete_media"), subtext=tr("delete_media_subtext"), icon="msg_delete", on_click=self._delete_imported_media),
        ]
        return items

    def _settings_language(self) -> List[Any]:
        if not has_language_choice():
            return []
        tr = self._tr
        language_index = self.settings.language_index()
        enabled = enabled_language_indices()
        if language_index != 0 and language_index not in enabled:
            language_index = LANGUAGE_MODES.index("en")
        position = enabled.index(language_index) if language_index in enabled else 0
        ui_state = (language_index, tuple(enabled))
        if ui_state != getattr(self, "_language_ui_index", None):
            self._language_ui_index = ui_state
            self._language_ui_revision = getattr(self, "_language_ui_revision", 0) + 1
        revision = self._language_ui_revision
        auto_key = f"Prefixfy_language_auto_{revision}"
        select_key = f"Prefixfy_language_select_{revision}"
        for key, value in ((auto_key, language_index == 0), (select_key, position)):
            try:
                self.set_setting(key, value)
            except Exception as exc:
                self.log(f"Prefixfy language widget state failed: {exc}")
        icon = self._icon("msg_language")
        items: List[Any] = [
            Header(text=tr("language")),
            Switch(
                key=auto_key, text=tr("language_auto"), default=language_index == 0,
                subtext=tr("language_auto_subtext"), icon=icon, on_change=self._on_language_auto_change,
            ),
        ]
        if language_index != 0:
            items.append(Selector(
                key=select_key, text=tr("plugin_language"), default=position,
                items=self.localization.language_items(), icon=icon,
                on_change=self._on_language_select_change,
            ))
        return items

    def _on_features_changed(self):
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

    def _remote_notice(self) -> List[Any]:
        remote = getattr(self, "remote", None)
        if remote is None:
            return []
        tr = self._tr
        icon = self._icon("msg_report", "msg_info")
        if remote.outdated():
            key, kwargs = remote.notice()
            subtext = tr(key, **kwargs)
            checksum = remote.latest_checksum()
            if checksum and key == "update_required_subtext":
                subtext += f"\nSHA-256 {checksum[:12]}…"
            if key == "account_blocked_subtext":
                return [Text(text=tr("account_blocked"), subtext=subtext, icon=icon, on_click=lambda *_: None)]
            title = tr("update_required" if key == "update_required_subtext" else "verify_required")
            return [Text(text=title, subtext=subtext, icon=icon, on_click=self._open_repo)]
        return []

    def _open_repo(self, *_):
        try:
            fragment = get_last_fragment()
            activity = fragment.getParentActivity() if fragment else None
            if activity is not None:
                activity.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(REPO_URL)))
        except Exception as exc:
            self.log(f"Prefixfy repo link failed: {exc}")

    def create_settings(self) -> List[Any]:
        self.localization.refresh()
        self.remote.request_refresh()
        notice = self._remote_notice()
        if notice:
            return notice
        settings: List[Any] = []
        settings.append(
            self._switch("chat_scope_enabled", self._tr("enable_plugin"), self._tr("enable_plugin_subtext"), "msg_settings"),
        )
        for section in (
            self._settings_configurations, self._settings_scope, self._settings_mask, self._settings_style,
            self._settings_separator, self._settings_exceptions, self._settings_media, self._settings_language,
        ):
            settings += section()
        return settings


    _MEDIA_FIELDS = ("photo", "document", "video", "media", "path")
    INTERNAL_SENDS_MAX = 128
    _skip_once = None
    _dialog_kinds: Dict[int, str] = {}
    _chat_titles: Dict[Tuple[int, int], Tuple[float, str]] = {}
    _mask_rotation_index = 0
    _last_random_mask = None
    _last_random_style = None
    _rotation_lock = threading.Lock()
    _counter_lock = threading.Lock()
    _count_used = False
    _chat_count_key = None

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
        if mime == "image/gif" or name.lower().endswith(".gif"):
            return send_document
        if mime.startswith("image/"):
            return send_photo
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
        sender(dialog_id, path, caption=caption, account=account)

    def _send_attached_media(self, dialog_id, media, caption: str, account: int, options: Optional[Dict[str, Any]] = None):
        path, name, mime = media
        options = dict(options or {})
        if caption:
            self._remember_internal_send(dialog_id, caption)
        try:
            self._call_sender(self._pick_media_sender(name, mime), dialog_id, path, caption, account, options)
        except Exception as exc:
            self.log(f"Prefixfy attached media send failed: {exc}")
            if caption:
                self._forget_internal_send(dialog_id, caption)
            self._send_plain_fallback(dialog_id, caption, account, options)

    def _send_plain_fallback(self, dialog_id, text: str, account: int, options: Optional[Dict[str, Any]] = None):
        if not text or _send_message is None:
            return
        self._remember_internal_send(dialog_id, text)
        attempts = []
        if options:
            attempts.append({"peer": dialog_id, "message": text, **options})
        attempts.append({"peer": dialog_id, "message": text})
        for index, payload in enumerate(attempts):
            try:
                _send_message(payload, account=account)
                return
            except Exception as exc:
                self.log(f"Prefixfy plain fallback send failed (attempt {index + 1}): {exc}")
        self._forget_internal_send(dialog_id, text)

    def on_send_message_hook(self, account: int, params: Any) -> HookResult:
        try:
            return self._process_outgoing(account, params)
        except Exception as exc:
            import traceback
            self.log(f"Prefixfy send hook failed: {exc}\n{traceback.format_exc()}")
            return HookResult()


    def _capture_custom_emoji(self, params, account: int) -> bool:
        entities = [entity for _, items in entity_sources(params) for entity in items]
        markers = []
        for field in ("message", "caption"):
            markers = custom_emoji_markers(getattr(params, field, None), entities)
            if markers:
                break
        if not markers:
            markers = custom_emoji_markers_from_input()
        dialog_id = self._dialog_id_from_params(params)
        if not markers or dialog_id is None or _send_message is None:
            return False
        try:
            self.set_setting("capture_custom_emoji", False)
        except Exception as exc:
            self.log(f"Prefixfy capture flag reset failed: {exc}")
        text = " ".join(markers)
        options = self._carry_over_options(params)
        run_on_queue(lambda: self._send_plain_fallback(dialog_id, text, account, options), PLUGINS_QUEUE, 350)
        return True

    @staticmethod
    def _account_is_premium(account, default: bool = True) -> bool:
        try:
            user_config = find_class("org.telegram.messenger.UserConfig")
            return bool(user_config.getInstance(int(account)).isPremium())
        except Exception:
            return default

    def _caption_limit(self, account: int) -> int:
        return PREMIUM_CAPTION_LIMIT if self._account_is_premium(account, default=False) else CAPTION_LIMIT


    @staticmethod
    def _select_field(settings: RuntimeSettings, message, caption) -> Tuple[Optional[str], str]:
        if settings.process_message and isinstance(message, str) and message:
            return "message", message
        if settings.process_media and isinstance(caption, str) and caption:
            return "caption", caption
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
        if "scheduleDate" in options:
            return False
        outgoing = runtime.pipeline.transform(message)
        if utf16_length(outgoing) > self._caption_limit(account):
            return False
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
        if not entities:
            if existing is not None and self._existing_entity_count(params) > 0:
                try:
                    pipeline = runtime.pipeline
                    shifted = body_offset_in(pipeline.expected_body(text), transformed, pipeline.mask_prefix(text))
                    params.entities = _make_tg_entities([], existing, shifted, pipeline.entity_mapper(text),
                                                        self._realign_args(pipeline, text, transformed))
                except Exception as exc:
                    self.log(f"Prefixfy entity shift failed: {exc}")
            return transformed
        snapshot = self._snapshot_entities(existing)
        try:
            params.entities = _make_tg_entities(entities, existing, body_offset, runtime.pipeline.entity_mapper(text),
                                                self._realign_args(runtime.pipeline, text, transformed))
        except Exception as exc:
            self.log(f"Prefixfy Markdown entities unavailable: {exc}")
            plain = runtime.pipeline.transform(text)
            self._restore_entities(snapshot)
            if existing is not None and snapshot:
                try:
                    pipeline = runtime.pipeline
                    shifted = body_offset_in(pipeline.expected_body(text), plain, pipeline.mask_prefix(text))
                    params.entities = _make_tg_entities([], existing, shifted, pipeline.entity_mapper(text))
                except Exception as shift_exc:
                    self.log(f"Prefixfy entity shift failed: {shift_exc}")
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
    def _restore_entities(snapshot) -> None:
        for entity, offset, length in snapshot:
            try:
                entity.offset = offset
                entity.length = length
            except Exception:
                pass

    def _dialog_kind(self, account: int, dialog_id) -> Optional[str]:
        if dialog_id is None:
            return None
        if dialog_id > 0:
            return "private"
        kinds = self._dialog_kinds
        cached = kinds.get(dialog_id)
        if cached is not None:
            return cached
        try:
            controller = find_class("org.telegram.messenger.MessagesController").getInstance(int(account))
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
        return kind is None or kind in kinds

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
        try:
            fragment = get_last_fragment()
            if fragment is not None and self._current_dialog_id() == dialog_id:
                chat = fragment.getCurrentChat() if dialog_id < 0 else None
                if chat is not None:
                    return as_text(chat.title)
                user = fragment.getCurrentUser() if dialog_id > 0 else None
                if user is not None:
                    return as_text(find_class("org.telegram.messenger.UserObject").getUserName(user))
            controller = find_class("org.telegram.messenger.MessagesController").getInstance(int(account))
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
            user = find_class("org.telegram.messenger.UserConfig").getInstance(int(account)).getCurrentUser()
            return as_text(getattr(user, "username", None)) or as_text(getattr(user, "first_name", None))
        except Exception as exc:
            self.log(f"Prefixfy username lookup failed: {exc}")
            return ""

    def _message_number(self) -> int:
        with self._counter_lock:
            self._count_used = True
            return clamp_int(self.get_setting(COUNTER_KEY, 0), 0, 0, 10 ** 9) + 1

    def _commit_message_counter(self):
        number = None
        counts = None
        with self._counter_lock:
            used, chat_key = self._count_used, self._chat_count_key
            self._count_used = False
            self._chat_count_key = None
            if used:
                number = clamp_int(self.get_setting(COUNTER_KEY, 0), 0, 0, 10 ** 9) + 1
            if chat_key:
                counts = self._chat_counts()
                current = counts.pop(chat_key, 0)
                counts[chat_key] = min(current + 1, 10 ** 9)
                while len(counts) > MAX_CHAT_COUNTS:
                    counts.pop(next(iter(counts)), None)
        if number is not None:
            try:
                self.set_setting(COUNTER_KEY, number)
            except Exception as exc:
                self.log(f"Prefixfy counter save failed: {exc}")
        if counts is not None:
            try:
                self.set_setting(CHAT_COUNTS_KEY, json.dumps(counts))
            except Exception as exc:
                self.log(f"Prefixfy chat counter save failed: {exc}")

    def _chat_counts(self) -> Dict[str, int]:
        try:
            data = json.loads(as_text(self.get_setting(CHAT_COUNTS_KEY, "")) or "{}")
        except (ValueError, TypeError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(key): value for key, value in data.items() if _is_int(value) and 0 <= value <= 10 ** 9}

    def _chat_message_number(self, account, dialog_id) -> int:
        if dialog_id is None:
            return 1
        key = f"{account}:{dialog_id}"
        with self._counter_lock:
            self._chat_count_key = key
            return self._chat_counts().get(key, 0) + 1

    def _reply_name(self, account, params) -> str:
        try:
            message = getattr(params, "replyToMsg", None)
            if message is None:
                return ""
            owner = getattr(message, "messageOwner", None)
            controller = find_class("org.telegram.messenger.MessagesController").getInstance(int(account))
            boxed = find_class("java.lang.Long")
            for field in ("from_id", "peer_id"):
                peer = getattr(owner, field, None)
                if peer is None:
                    continue
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
        except Exception as exc:
            self.log(f"Prefixfy reply name lookup failed: {exc}")
        return ""

    def _battery_text(self) -> str:
        try:
            from android.content import IntentFilter
            context = find_class("org.telegram.messenger.ApplicationLoader").applicationContext
            status = context.registerReceiver(None, IntentFilter("android.intent.action.BATTERY_CHANGED"))
            if status is None:
                return ""
            level, scale = int(status.getIntExtra("level", -1)), int(status.getIntExtra("scale", -1))
            if level >= 0 and scale > 0:
                return f"{level * 100 // scale}%"
        except Exception as exc:
            self.log(f"Prefixfy battery lookup failed: {exc}")
        return ""

    def _random_line(self, preview: bool = False) -> str:
        lines = parse_lines(self.settings.get("tag_lines"))[:MAX_TAG_LINES]
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
                    names = WEEKDAY_NAMES.get(self.localization.language(), WEEKDAY_NAMES["en"])
                    raw = names[now.weekday()]
                    if tag == "weekday_short":
                        raw = raw[:3] if raw.isascii() else raw[:2]
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
                    names = MONTH_NAMES.get(self.localization.language(), MONTH_NAMES["en"])
                    raw = names[now.month - 1]
                elif tag == "daypart":
                    names = DAYPART_NAMES.get(self.localization.language(), DAYPART_NAMES["en"])
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
                else:
                    raw = self._chat_title(account, dialog_id) or ("…" if preview else "")
                values[tag] = sanitize_tag_value(raw)
            return values[tag]

        def replace(match) -> str:
            tag = match.group(1).lower()
            flag = "tag_" + (tag.split(":", 1)[0] if tag.startswith(("since:", "until:")) else tag)
            return value(tag) if FEATURES.on(flag) else match.group(0)

        return MASK_TAG_RE.sub(replace, mask)

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
        if not self.remote.allows(account):
            self._dbg("skip: remote.allows() is False")
            return HookResult()
        if FEATURES.on("premium_emoji") and self.settings.get("capture_custom_emoji", False) and self._capture_custom_emoji(params, account):
            return HookResult(strategy=HookStrategy.CANCEL)

        runtime = self.runtime_manager.runtime
        if runtime is None:
            self._dbg("skip: runtime is None")
            return HookResult()

        dialog_id = self._dialog_id_from_params(params)
        runtime = self._runtime_for_chat(runtime, dialog_id)
        settings = runtime.settings
        if not self._chat_type_allowed(account, dialog_id, settings.chat_type_rules):
            self._dbg(f"skip: chat type not allowed (dialog {dialog_id})")
            return HookResult()
        if not settings.is_chat_allowed(dialog_id):
            self._dbg(f"skip: chat not allowed (dialog {dialog_id})")
            return HookResult()

        message = getattr(params, "message", None)
        caption = getattr(params, "caption", None)
        has_media = self._params_have_media(params)

        self._dbg(f"incoming: dialog={dialog_id} media={has_media} message={message!r} caption={caption!r} "
                  f"entities={describe_entities(getattr(params, 'entities', None))} "
                  f"mask={settings.mask!r} separators={settings.separator_enabled} "
                  f"style={settings.text_style if settings.text_style_enabled else None}")
        already_styled = caption if has_media else message
        if isinstance(already_styled, str) and already_styled and self._is_internal_send(dialog_id, already_styled):
            self._dbg("skip: internal send (already styled)")
            return HookResult()

        field, text = self._select_field(settings, message, caption)
        if field is None:
            self._dbg("skip: no field selected (disabled for this message type)")
            return HookResult()
        if self._skip_once is not None and not runtime.pipeline.ignores(text) and self._consume_skip_once(dialog_id):
            self._dbg("skip: skip_once consumed")
            return HookResult()
        runtime, rotation_next = self._runtime_for_message(runtime, account, dialog_id, text, params)
        if field == "message" and self._try_attach_media(runtime, dialog_id, params, message, has_media, account):
            self._advance_rotation(rotation_next)
            return HookResult(strategy=HookStrategy.CANCEL)

        transformed = self._decorate_text(runtime, account, params, text, field == "caption", rotation_next)
        if transformed is None:
            self._dbg(f"skip: nothing to apply (ignored={runtime.pipeline.ignores(text)})")
            return HookResult()
        setattr(params, field, transformed)
        return HookResult(strategy=HookStrategy.MODIFY, params=params)

    def _dbg(self, message: str) -> None:
        if not DEBUG_SEND:
            return
        line = f"Prefixfy[debug] {message}"
        sent = False
        for loader in (lambda: find_class("org.telegram.messenger.FileLog"), lambda: find_class("android.util.Log")):
            try:
                target = loader()
                if target is None:
                    continue
                if hasattr(target, "d"):
                    try:
                        target.d(line)
                    except Exception:
                        target.d("tmessages", line)
                    sent = True
                    break
            except Exception:
                continue
        try:
            self.log(line)
        except Exception:
            if not sent:
                print(line)

    def _decorate_text(self, runtime: Runtime, account: int, params, text: str, is_caption: bool, rotation_next) -> Optional[str]:
        transformed, entities, body_offset = self._transform_text(runtime, text)
        self._dbg(f"transform: body_offset={body_offset!r} new_entities={[item[:3] for item in entities][:12]} "
                  f"existing={describe_entities(getattr(params, 'entities', None))}")
        entities = self._finalize_entities(account, params, entities, body_offset)
        if transformed == text and not entities:
            self._dbg("decorate: nothing changed, skipped")
            return None
        limit = self._caption_limit(account) if is_caption else MESSAGE_LIMIT
        if utf16_length(transformed) > limit:
            self._dbg(f"decorate: too long ({utf16_length(transformed)} > {limit}), skipped")
            return None
        transformed = self._apply_entities(runtime, params, text, transformed, entities, body_offset)
        self._dbg(f"entity trace: {'; '.join(ENTITY_TRACE)}")
        self._dbg(f"result: text={transformed!r} entities={describe_entities(getattr(params, 'entities', None))}")
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
            seen[key] = now + 30
            self._edit_seen = seen
        return found

    def _edit_is_decorated(self, runtime: Runtime, text: str) -> bool:
        settings = runtime.settings
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

    def _find_message_object(self, account, message_id):
        try:
            fragment = get_last_fragment()
            view = fragment.getChatActivityEnterView() if fragment is not None else None
            editing = view.getEditingMessageObject() if view is not None else None
            if editing is not None and java_int(editing.getId()) == message_id:
                return editing
        except Exception:
            pass
        try:
            controller = find_class("org.telegram.messenger.MessagesController").getInstance(int(account))
            return controller.dialogMessagesByIds.get(message_id)
        except Exception:
            return None

    def _edit_is_caption(self, request, account, dialog_id) -> Optional[bool]:
        try:
            if getattr(request, "media", None) is not None:
                return True
        except Exception:
            pass
        message_id = java_int(getattr(request, "id", None))
        message = self._find_message_object(account, message_id) if message_id is not None else None
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
        if not text.strip():
            return
        dialog_id = self._dialog_id_from_params(request)
        try:
            account = int(param.thisObject.currentAccount)
        except Exception:
            account = get_selected_account()

        if not self.remote.allows(account):
            return
        runtime = self._runtime_for_chat(runtime, dialog_id)
        settings = runtime.settings
        if not settings.process_edit:
            return
        caption = self._edit_is_caption(request, account, dialog_id)
        if caption is None:
            if not (settings.process_edit_message or settings.process_edit_media):
                return
        elif not (settings.process_edit_media if caption else settings.process_edit_message):
            return
        if not self._chat_type_allowed(account, dialog_id, settings.chat_type_rules) or not settings.is_chat_allowed(dialog_id):
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
