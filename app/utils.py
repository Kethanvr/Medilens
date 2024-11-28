import re
from deep_translator import GoogleTranslator

def parse_ocr_text(ocr_text):
    data = {
        "name": re.search(r"(Name|Product Name):\s*(.+)", ocr_text, re.IGNORECASE),
        "manufacturer": re.search(r"(Manufacturer|Mfg. by):\s*(.+)", ocr_text, re.IGNORECASE),
        "composition": re.search(r"(Composition|Ingredients):\s*(.+)", ocr_text, re.IGNORECASE),
        "expiry_date": re.search(r"(Expiry Date|Exp. Date):\s*(.+)", ocr_text, re.IGNORECASE),
    }
    return {key: match.group(2).strip() if match else "No Information" for key, match in data.items()}

def translate_text(text, target_language):
    try:
        return GoogleTranslator(source='auto', target=target_language).translate(text)
    except Exception:
        return text
