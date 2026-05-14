import re
from datetime import date, datetime, timedelta
from typing import Optional

import dateparser
import parsedatetime
from dateutil.relativedelta import relativedelta


def parse(s: str, today: Optional[date] = None) -> date:
    """
    Parses natural language into a date using cumulative delta logic.
    """
    # 1. Reference point setup
    ref_date = today if today else date.today()
    ref_dt = datetime.combine(ref_date, datetime.min.time())
    s_lower = s.lower().strip()

    # 2. Weekday Handler (next/last [weekday])
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
        target = weekdays[words[1]]
        current = ref_date.weekday()
        diff = (target - current) % 7
        if diff == 0:
            diff = 7
        if words[0] in ("next", "this"):
            return ref_date + timedelta(days=diff)
        if words[0] == "last":
            back = (current - target) % 7
            if back == 0:
                back = 7
            return ref_date - timedelta(days=back)

    # 3. Cumulative Relative Math
    # We identify the 'anchor shift' separately to prevent leap-day/month-end drift.
    anchor_shift = relativedelta()
    s_temp = s_lower
    if "yesterday" in s_temp:
        anchor_shift = relativedelta(days=-1)
        s_temp = s_temp.replace("yesterday", "today")
    elif "tomorrow" in s_temp:
        anchor_shift = relativedelta(days=1)
        s_temp = s_temp.replace("tomorrow", "today")

    keywords = r"\b(before|after|from)\b"
    if re.search(keywords, s_temp):
        parts = re.split(keywords, s_temp, maxsplit=1)
        if len(parts) == 3:
            offset_part, rel, base_part = [p.strip() for p in parts]

            # Parse the base date (e.g., 'today' or an explicit date)
            anchor_dt: Optional[datetime] = (
                ref_dt
                if base_part in ("today", "now")
                else dateparser.parse(base_part, settings={"RELATIVE_BASE": ref_dt})
            )

            if anchor_dt is not None:
                matches = re.findall(r"(\d+)\s+(year|month|week|day)s?", offset_part)
                if matches:
                    delta_args = {f"{u}s": int(v) for v, u in matches}
                    offset_delta = relativedelta(**delta_args)  # type: ignore[arg-type]

                    # Combine the offset with the yesterday/tomorrow shift
                    if rel == "before":
                        total_delta = anchor_shift - offset_delta
                    else:
                        total_delta = anchor_shift + offset_delta

                    return (anchor_dt + total_delta).date()

    # 4. Fallbacks
    cal = parsedatetime.Calendar(version=parsedatetime.VERSION_CONTEXT_STYLE)
    time_struct, status = cal.parse(s, ref_dt)

    # Use accuracy to avoid the TypeError found in image_b11c3b.png
    if status.accuracy > 0:
        return date(*time_struct[:3])

    dt = dateparser.parse(
        s, settings={"RELATIVE_BASE": ref_dt, "PREFER_DATES_FROM": "future"}
    )
    if dt:
        return dt.date()

    raise ValueError(f"Could not parse: {s}")
