from typing import Optional
from endstone import Player

def replace_placeholders(api, player: Optional[Player], text: str, open_char: str, close_char: str) -> str:
    result = ""
    i = 0
    length = len(text)

    while i < length:
        if text[i] != open_char:
            result += text[i]
            i += 1
            continue

        start = i
        end = text.find(close_char, i + 1)
        if end == -1 or end == start + 1:
            result += text[i]
            i += 1
            continue

        inner = text[start + 1:end]

        if ' ' in inner:
            result += text[i]
            i += 1
            continue

        sep = inner.find('_')
        if sep == -1:
            result += text[i]
            i += 1
            continue

        identifier = inner[:sep].lower()
        params = inner[sep + 1:]

        exp = api.get_expansion(identifier)
        if not exp:
            result += text[start:end + 1]
            i = end + 1
            continue

        val = exp.on_request(player, params)
        if val is not None:
            result += str(val)
        else:
            result += text[start:end + 1]
        
        i = end + 1

    return result

def contains_delimiters(text: str, open_char: str, close_char: str) -> bool:
    pos = 0
    while True:
        pos = text.find(open_char, pos)
        if pos == -1:
            break
        end = text.find(close_char, pos + 1)
        if end == -1:
            break
        inner = text[pos + 1:end]
        if ' ' not in inner and '_' in inner:
            return True
        pos = end + 1
    return False
