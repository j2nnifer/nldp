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
    # 1. Establish the reference point
    ref_date = today if today else date.today()
    ref_dt = datetime.combine(ref_date, datetime.min.time())
    s_lower = s.lower().strip()

    # 2. Weekday Handler (next/last/this [weekday])
    # Returns the soonest instance (0-7 days away)
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

    # 3. Handle complex math with Anchor Normalization
    # 'after yesterday' is normalized to 'from today' to prevent leap-day drift
    s_clean = re.sub(r"(after|from)\s+yesterday", r"\1 today", s_lower)
    s_clean = re.sub(r"before\s+tomorrow", "before today", s_clean)

    keywords = r"\b(before|after|from)\b"
    if re.search(keywords, s_clean):
        parts = re.split(keywords, s_clean, maxsplit=1)
        if len(parts) == 3:
            offset_part, rel, base_part = [p.strip() for p in parts]

            # Use a fresh variable name to solve the Mypy assignment error
            anchor_dt: Optional[datetime] = None
            if base_part in ("today", "now"):
                anchor_dt = ref_dt
            else:
                anchor_dt = dateparser.parse(
                    base_part, settings={"RELATIVE_BASE": ref_dt}
                )

            if anchor_dt is not None:
                matches = re.findall(r"(\d+)\s+(year|month|week|day)s?", offset_part)
                if matches:
                    delta_args = {f"{u}s": int(v) for v, u in matches}
                    delta = relativedelta(**delta_args)  # type: ignore[arg-type]

                    res_dt = anchor_dt - delta if rel == "before" else anchor_dt + delta
                    return res_dt.date()

    # 4. Fallbacks for standard idioms
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
