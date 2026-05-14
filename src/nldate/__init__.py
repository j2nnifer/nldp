import re
from datetime import date, datetime
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

    # 1. Handle complex math (e.g., '5 days before...', '1 year after...')
    s_clean = s.lower().replace("after yesterday", "from now")
    keywords = r"\b(before|after|from)\b"

    if re.search(r"\d+", s_clean) and re.search(keywords, s_clean):
        parts = re.split(keywords, s_clean, maxsplit=1)
        if len(parts) == 3:
            offset_side, direction, base_side = parts
            direction = direction.strip()

            matches = re.findall(r"(\d+)\s+(year|month|week|day)s?", offset_side)
            base_dt = dateparser.parse(base_side.strip(), settings={"RELATIVE_BASE": ref_dt})

            if matches and base_dt:
                delta = relativedelta()
                for val, unit in matches:
                    u = unit + "s"
                    delta += relativedelta(**{u: int(val)})  # type: ignore[arg-type]

                res = (base_dt - delta) if direction == "before" else (base_dt + delta)
                return res.date()

    # 2. parsedatetime for natural English relative dates
    # This natively and flawlessly handles "next Tuesday", "tomorrow", etc.
    cal = parsedatetime.Calendar()
    time_struct, parse_status = cal.parse(s, ref_dt)
    if parse_status > 0:
        return date(*time_struct[:3])

    # 3. dateparser as an absolute date fallback
    dt = dateparser.parse(
        s, settings={"RELATIVE_BASE": ref_dt, "PREFER_DATES_FROM": "future"}
    )
    if dt:
        return dt.date()

    raise ValueError(f"Could not parse date string: {s}")
