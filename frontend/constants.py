from pathlib import Path

DEFAULT_STT_CONFIG_PATH = Path("modules/stt_whisper/config/settings.yaml")
STT_UI_OVERRIDE_PATH = Path("modules/stt_whisper/config/ui_override.yaml")
DEFAULT_TEXT_CONFIG_PATH = Path("modules/text_processor/config/settings.yaml")

LANGUAGE_OPTIONS = [
    ("auto", "자동 감지"),
    ("ko", "한국어"),
    ("en", "영어"),
    ("ja", "일본어"),
    ("zh", "중국어"),
    ("es", "스페인어"),
    ("fr", "프랑스어"),
    ("de", "독일어"),
]

LANGUAGE_LABEL = dict(LANGUAGE_OPTIONS)
