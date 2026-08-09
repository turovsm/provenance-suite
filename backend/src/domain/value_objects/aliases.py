MAX_ALIASES_PER_ENTITY = 50
MAX_ALIAS_LENGTH = 512


def normalize_aliases(values: list[str] | None) -> list[str]:
    """Trim, drop empties, dedupe case-insensitively (first wins), cap count."""
    if not values:
        return []
    seen: set[str] = set()
    cleaned: list[str] = []
    for raw in values:
        if not isinstance(raw, str):
            continue
        item = raw.strip()
        if not item:
            continue
        marker = item.casefold()
        if marker in seen:
            continue
        seen.add(marker)
        cleaned.append(item[:MAX_ALIAS_LENGTH])
        if len(cleaned) >= MAX_ALIASES_PER_ENTITY:
            break
    return cleaned
