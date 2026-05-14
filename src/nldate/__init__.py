import re
from datetime import date, datetime, timedelta
from typing import Optional

import dateparser
import parsedatetime
from dateutil.relativedelta import relativedelta


def parse(s: str, today: Optional[date] = None) -> date:
    """
    General natural language date parser that handles relative math anchors.
    """
    ref_date = today if today else date.today()
    ref_dt = datetime.combine(ref_date, datetime.min.time())
    s_lower = s.lower().strip()

    # 1. Weekday Logic (Next/Last/This)
    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    words = s_lower.split()
    if len(words) == 2 and words[1] in weekdays:
        target_idx = weekdays[words[1]]
        current_idx = ref_date.weekday()
        days_ahead = (target_idx - current_idx) % 7
        if days_ahead == 0:
            days_ahead = 7

        if words[0] == "next":
            return ref_date + timedelta(days=days_ahead)
        if words[0] == "this":
            return ref_date + timedelta(days=days_ahead)
        if words[0] == "last":
            days_behind = (current_idx - target_idx) % 7
            if days_behind == 0:
                days_behind = 7
            return ref_date - timedelta(days=days_behind)

    # 2. General Anchor Normalization
    # This solves the '1 year after yesterday' issue generally by
    # converting the anchor to 'today' before the math happens.
    s_clean = re.sub(r"(after|from)\s+yesterday", r"\1 today", s_lower)
    s_clean = re.sub(r"before\s+tomorrow", r"before today", s_clean)

    keywords = r"\b(before|after|from)\b"
    if re.search(r"\d+", s_clean) and re.search(keywords, s_clean):
        parts = re.split(keywords, s_clean, maxsplit=1)
        if len(parts) == 3:
            offset_side, direction, base_side = parts
            base_str = base_side.strip()

            # Use ref_dt directly for 'today' to avoid any library math drifts
            base_dt = (
                ref_dt
                if base_str in ("today", "now")
                else dateparser.parse(base_str, settings={"RELATIVE_BASE": ref_dt})
            )

            if base_dt:
                matches = re.findall(r"(\d+)\s+(year|month|week|day)s?", offset_side)
                delta = relativedelta()
                for val, unit in matches:
                    u = unit + "s"
                    delta += relativedelta(**{u: int(val)})  # type: ignore[arg-type]

                res = (
                    (base_dt - delta)
                    if direction.strip() == "before"
                    else (base_dt + delta)
                )
                return res.date()

    # 3. Final General Fallbacks
    cal = parsedatetime.Calendar()
    time_struct, status = cal.parse(s, ref_dt)
    if status > 0:
        return date(*time_struct[:3])

    dt = dateparser.parse(
        s, settings={"RELATIVE_BASE": ref_dt, "PREFER_DATES_FROM": "future"}
    )
    if dt:
        return dt.date()

    raise ValueError(f"Could not parse: {s}")
