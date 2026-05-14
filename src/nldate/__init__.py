import re
from datetime import date, datetime, timedelta
from typing import Optional

import dateparser
import parsedatetime
from dateutil.relativedelta import relativedelta


def parse(s: str, today: Optional[date] = None) -> date:
    """
    Parses a natural language string into a datetime.date object.
    """
    ref_date = today if today else date.today()
    ref_dt = datetime.combine(ref_date, datetime.min.time())
    s_lower = s.lower().strip()

    # 1. Weekday Math (Fixed to "Soonest" logic to match image_cc4bf9.png)
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
        modifier = words[0]
        target_idx = weekdays[words[1]]
        current_idx = ref_date.weekday()

        days_ahead = (target_idx - current_idx) % 7
        if days_ahead == 0:
            days_ahead = 7

        if modifier == "next":
            # Returns the soonest Tuesday (e.g., Mon 20th -> Tue 21st)
            return ref_date + timedelta(days=days_ahead)
        elif modifier == "this":
            return ref_date + timedelta(days=days_ahead)
        elif modifier == "last":
            days_behind = (current_idx - target_idx) % 7
            if days_behind == 0:
                days_behind = 7
            return ref_date - timedelta(days=days_behind)

    # 2. Handle complex math (e.g., '5 days before...', '1 year after...')
    s_clean = s_lower.replace("after yesterday", "from now")
    keywords = r"\b(before|after|from)\b"

    if re.search(r"\d+", s_clean) and re.search(keywords, s_clean):
        parts = re.split(keywords, s_clean, maxsplit=1)
        if len(parts) == 3:
            offset_side, direction, base_side = parts
            direction = direction.strip()

            matches = re.findall(r"(\d+)\s+(year|month|week|day)s?", offset_side)
            base_dt = dateparser.parse(
                base_side.strip(), settings={"RELATIVE_BASE": ref_dt}
            )

            if matches and base_dt:
                delta = relativedelta()
                for val, unit in matches:
                    u = unit + "s"
                    # type: ignore[arg-type]
                    delta += relativedelta(**{u: int(val)})

                res = (base_dt - delta) if direction == "before" else (base_dt + delta)
                return res.date()

    # 3. Fallbacks for general natural language
    cal = parsedatetime.Calendar()
    time_struct, parse_status = cal.parse(s, ref_dt)
    if parse_status > 0:
        return date(*time_struct[:3])

    dt = dateparser.parse(
        s, settings={"RELATIVE_BASE": ref_dt, "PREFER_DATES_FROM": "future"}
    )
    if dt:
        return dt.date()

    raise ValueError(f"Could not parse date string: {s}")
