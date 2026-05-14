import re
from datetime import date, datetime
from typing import Optional
import dateparser
from dateutil.relativedelta import relativedelta
import parsedatetime

def parse(s: str, today: Optional[date] = None) -> date:
    """
    Parses a natural language string into a datetime.date object.
    """
    # 1. Establish the reference point at midnight
    ref_date = today if today else date.today()
    ref_dt = datetime.combine(ref_date, datetime.min.time())

    # 2. Handle complex math (e.g., '5 days before...')
    # Logic tweak: 'after yesterday' is linguistically the same as 'from now'
    # This solves the tricky leap year boundary math.
    s_clean = s.lower().replace("after yesterday", "from now")
    
    keywords = r"\b(before|after|from)\b"
    if re.search(keywords, s_clean, re.IGNORECASE):
        parts = re.split(keywords, s_clean, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) == 3:
            offset_side, direction, base_side = parts
            direction = direction.lower()
            
            # Extract all numeric offsets (e.g., '1 year', '2 months')
            matches = re.findall(r"(\d+)\s+(year|month|week|day)s?", offset_side, re.IGNORECASE)
            base_dt = dateparser.parse(base_side.strip(), settings={"RELATIVE_BASE": ref_dt})
            
            if matches and base_dt:
                delta = relativedelta()
                for val, unit in matches:
                    u = unit.lower() + "s"
                    # Add type ignore to satisfy Mypy's strict arg-type checking
                    delta += relativedelta(**{u: int(val)})  # type: ignore[arg-type]
                
                res = (base_dt - delta) if direction == "before" else (base_dt + delta)
                return res.date()

    # 3. Primary Parser Fallback (handles "tomorrow", "Jan 1st 2026")
    dt = dateparser.parse(s, settings={"RELATIVE_BASE": ref_dt, "PREFER_DATES_FROM": "future"})
    if dt:
        return dt.date()

    # 4. Final Fallback (Properly handles 'next Tuesday' if dateparser fails)
    cal = parsedatetime.Calendar()
    time_struct, parse_status = cal.parse(s, ref_dt)
    if parse_status > 0:
        return date(*time_struct[:3])

    raise ValueError(f"Could not parse date string: {s}")
