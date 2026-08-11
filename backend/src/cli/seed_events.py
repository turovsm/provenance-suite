import argparse
import asyncio
import json
import re
import sys
import uuid
from datetime import date
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select

from src.infrastructure.db.models.music import EventModel
from src.infrastructure.db.session import async_session_factory
from src.presentation.api.v1.entities import compute_event_sort_date, normalize_date_string


EventParsedTuple = tuple[
    str | None,
    str | None,
    str | None,
    str | None,
    list[dict[str, str | None]],
    list[dict[str, str | None]],
    str,
    date | None,
]

STATUS_TAG_REGEX = re.compile(r"\s*\((?i:skipped|cancelled|canceled|postponed)\)")
STATUS_TAG_OPT_REGEX = re.compile(
    r"\s*\((?i:skipped|cancelled|canceled|postponed)\)|\s*(?i:skipped|cancelled|canceled|postponed)"
)


def parse_date_component(part: str) -> tuple[str | None, str | None, date | None]:
    part = part.strip()

    if "xx" in part.lower():
        parts = re.split(r"[./-]", part)
        y = parts[0]
        m = parts[1] if len(parts) > 1 else "xx"
        d = parts[2] if len(parts) > 2 else "xx"
        norm_str = f"{y}-{m.lower()}-{d.lower()}"
        sort_d = compute_event_sort_date(norm_str)
        return norm_str, norm_str, sort_d

    m_compact = re.match(r"^(\d{4})[./-](\d{1,2})\.(\d{2})(\d{2})$", part)
    if m_compact:
        y, mo, d1, d2 = map(int, m_compact.groups())
        s_str = f"{y}-{mo:02d}-{d1:02d}"
        e_str = f"{y}-{mo:02d}-{d2:02d}"
        return s_str, e_str, date(y, mo, d1)

    m_range_full = re.match(
        r"^(\d{4})[./-](\d{1,2})[./-](\d{1,2})\s*[-–]\s*(\d{4})[./-](\d{1,2})[./-](\d{1,2})$",
        part,
    )
    if m_range_full:
        y1, mo1, d1, y2, mo2, d2 = map(int, m_range_full.groups())
        return f"{y1}-{mo1:02d}-{d1:02d}", f"{y2}-{mo2:02d}-{d2:02d}", date(y1, mo1, d1)

    m_cross_month = re.match(r"^(\d{4})[./-](\d{1,2})[./-](\d{1,2})-(\d{1,2})[./-](\d{1,2})$", part)
    if m_cross_month:
        y, m1, d1, m2, d2 = map(int, m_cross_month.groups())
        return f"{y}-{m1:02d}-{d1:02d}", f"{y}-{m2:02d}-{d2:02d}", date(y, m1, d1)

    m_range_days = re.match(r"^(\d{4})[./-](\d{1,2})[./-](\d{1,2})-(\d{1,2})$", part)
    if m_range_days:
        y, mo, d1, d2 = map(int, m_range_days.groups())
        return f"{y}-{mo:02d}-{d1:02d}", f"{y}-{mo:02d}-{d2:02d}", date(y, mo, d1)

    m_single = re.match(r"^(\d{4})[./-](\d{1,2})[./-](\d{1,2})$", part)
    if m_single:
        y, mo, d = map(int, m_single.groups())
        s_str = f"{y}-{mo:02d}-{d:02d}"
        return s_str, s_str, date(y, mo, d)

    raise ValueError(f"Unrecognized date format: '{part}'")


def _range_to_dict(s: str | None, e: str | None) -> dict[str, str | None]:
    return {
        "start_date": normalize_date_string(s),
        "end_date": normalize_date_string(e),
    }


def _parse_non_numeric_event(val: str) -> EventParsedTuple | None:
    val_lower = val.lower()
    if any(kw in val_lower for kw in ["unknown", "missing", "tba", "all dates"]):
        return None, None, None, None, [], [], "UNKNOWN", None

    if not any(char.isdigit() for char in val):
        is_cancelled = any(kw in val_lower for kw in ["cancel", "skip"])
        status = "CANCELLED" if is_cancelled else "UNKNOWN"
        return None, None, None, None, [], [], status, None
    return None


def _parse_arrow_timeline(val: str) -> EventParsedTuple | None:
    if "→" not in val and "->" not in val:
        return None

    parts = [p.strip() for p in re.split(r"→|->", val) if p.strip()]
    last_part = parts[-1].lower() if parts else ""

    status = "HELD"
    step_parts = parts
    if any(kw in last_part for kw in ["cancel", "skip"]):
        status = "CANCELLED"
        step_parts = parts[:-1]
    elif "postponed" in last_part:
        status = "POSTPONED"
        step_parts = parts[:-1]

    history: list[dict[str, str | None]] = []
    parsed_steps: list[tuple[str | None, str | None, date | None]] = []

    for p in step_parts:
        p_clean = STATUS_TAG_REGEX.sub("", p).strip()
        try:
            s_str, e_str, sort_d = parse_date_component(p_clean)
            parsed_steps.append((s_str, e_str, sort_d))
            history.append(_range_to_dict(s_str, e_str))
        except ValueError:
            continue

    if not parsed_steps:
        return None, None, None, None, [], [], status, None

    orig_start, orig_end = (None, None)
    if len(parsed_steps) >= 2:
        orig_start, orig_end, _ = parsed_steps[0]

    final_start, final_end, final_sort = parsed_steps[-1]
    return final_start, final_end, orig_start, orig_end, history, [], status, final_sort


def _parse_cancelled_or_postponed_event(val: str) -> EventParsedTuple | None:
    val_lower = val.lower()
    if not any(kw in val_lower for kw in ["cancel", "skip", "postponed"]):
        return None

    status = "POSTPONED" if "postponed" in val_lower else "CANCELLED"
    date_part = STATUS_TAG_OPT_REGEX.sub("", val).strip(" -/>()")
    try:
        s_str, e_str, sort_d = parse_date_component(date_part)
        return s_str, e_str, None, None, [_range_to_dict(s_str, e_str)], [], status, sort_d
    except ValueError:
        return None, None, None, None, [], [], status, None


def _parse_slash_or_plus_sessions(val: str) -> EventParsedTuple | None:
    if "/" not in val and "+" not in val:
        return None

    parts = [p.strip() for p in re.split(r"[/+]", val) if p.strip()]
    parsed_sessions: list[tuple[str | None, str | None, date | None]] = []

    for p in parts:
        try:
            s_str, e_str, sort_d = parse_date_component(p)
            parsed_sessions.append((s_str, e_str, sort_d))
        except ValueError:
            continue

    if parsed_sessions:
        primary_start, primary_end, primary_sort = parsed_sessions[0]
        add_dates = [_range_to_dict(s, e) for s, e, _ in parsed_sessions[1:]]
        return primary_start, primary_end, None, None, [], add_dates, "HELD", primary_sort
    return None


def _parse_hyphenated_date_range(val: str) -> EventParsedTuple | None:
    if " - " not in val:
        return None

    parts = val.split(" - ")
    if len(parts) == 2:
        try:
            s_str, _, sort_d = parse_date_component(parts[0])
            _, e_str, _ = parse_date_component(parts[1])
            return s_str, e_str, None, None, [], [], "HELD", sort_d
        except ValueError:
            pass
    return None


def parse_event_value(raw_val: str) -> EventParsedTuple:
    val = raw_val.strip().lstrip(":").replace(r"\-", "-")

    non_numeric = _parse_non_numeric_event(val)
    if non_numeric is not None:
        return non_numeric

    arrow_res = _parse_arrow_timeline(val)
    if arrow_res is not None:
        return arrow_res

    status_res = _parse_cancelled_or_postponed_event(val)
    if status_res is not None:
        return status_res

    session_res = _parse_slash_or_plus_sessions(val)
    if session_res is not None:
        return session_res

    hyphen_res = _parse_hyphenated_date_range(val)
    if hyphen_res is not None:
        return hyphen_res

    start_str, end_str, sort_d = parse_date_component(val)
    return start_str, end_str, None, None, [], [], "HELD", sort_d


def derive_full_name(series_key: str, item_key: str) -> str:
    primary_series_name = series_key.split("/")[0].strip().replace("\\-", "-")
    clean_item_key = item_key.split("(")[0].strip()

    if clean_item_key not in primary_series_name:
        return f"{primary_series_name} ({clean_item_key})"

    return primary_series_name


async def seed_events(json_path: Path) -> None:
    content = await asyncio.to_thread(json_path.read_text, encoding="utf-8")
    data = json.loads(content)

    inserted = 0
    updated = 0
    skipped = 0

    async with async_session_factory() as session:
        for series_key, events_map in data.items():
            for raw_short_name, raw_date_val in events_map.items():
                short_name = raw_short_name.strip().replace("  ", " ")
                full_name = derive_full_name(series_key, short_name)

                try:
                    parsed_event = parse_event_value(raw_date_val)
                    (
                        start_date,
                        end_date,
                        orig_start,
                        orig_end,
                        history,
                        add_dates,
                        status,
                        start_date_sort,
                    ) = parsed_event
                except Exception as err:
                    print(f"[SKIP] Failed parsing date for {short_name}: '{raw_date_val}' ({err})")
                    skipped += 1
                    continue

                stmt = select(EventModel).where(EventModel.short_name == short_name)
                res = await session.execute(stmt)
                existing = res.scalars().first()

                if existing:
                    existing.full_name = full_name
                    existing.start_date = start_date
                    existing.end_date = end_date
                    existing.original_start_date = orig_start
                    existing.original_end_date = orig_end
                    existing.start_date_sort = start_date_sort
                    existing.date_history = history
                    existing.additional_dates = add_dates
                    existing.status = status
                    updated += 1
                else:
                    new_event = EventModel(
                        id=uuid.uuid4(),
                        short_name=short_name,
                        full_name=full_name,
                        start_date=start_date,
                        end_date=end_date,
                        original_start_date=orig_start,
                        original_end_date=orig_end,
                        start_date_sort=start_date_sort,
                        date_history=history,
                        additional_dates=add_dates,
                        status=status,
                    )
                    session.add(new_event)
                    inserted += 1

        await session.commit()

    print("EVENT SEED COMPLETE")
    print(f" New Events Inserted : {inserted}")
    print(f" Existing Updated    : {updated}")
    print(f" Skipped / Unparsed  : {skipped}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed PostgreSQL database from events.json")
    parser.add_argument("json_file", type=Path, help="Path to events.json file")
    args = parser.parse_args()

    if not args.json_file.exists():
        print(f"Error: File '{args.json_file}' does not exist.", file=sys.stderr)
        sys.exit(1)

    asyncio.run(seed_events(args.json_file))


if __name__ == "__main__":
    main()
