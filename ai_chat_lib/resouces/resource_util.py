import locale
from .string_resources import StringResources
from .string_resources_ja import StringResourcesJa

def get_string_resources() -> StringResources: 
    # OSのロケールを取得
    try:
        lang, _ = locale.getlocale()
    except Exception as e:
        print(f"Error getting locale: {e}")
        lang = "en_US"  # Default to English if locale cannot be determined
    # ロケールに基づいて適切なリソースを返す
    if lang:
        if lang.startswith("ja"):
            return StringResourcesJa()

    return StringResources()
