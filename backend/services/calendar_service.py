import httpx
import os
from dotenv import load_dotenv

load_dotenv()

CALENDARIFIC_API_KEY = os.environ.get("CALENDARIFIC_API_KEY", "")
CALENDARIFIC_COUNTRY = os.environ.get("CALENDARIFIC_COUNTRY", "IN")
CALENDARIFIC_STATE = os.environ.get("CALENDARIFIC_STATE", "in-ka")
CALENDARIFIC_YEAR = os.environ.get("CALENDARIFIC_YEAR", "2025")

CALENDARIFIC_URL = "https://calendarific.com/api/v2/holidays"


async def get_holidays(year: str = None, month: int = None):
    if not CALENDARIFIC_API_KEY:
        return {"error": "CALENDARIFIC_API_KEY not configured", "holidays": []}

    params = {
        "api_key": CALENDARIFIC_API_KEY,
        "country": CALENDARIFIC_COUNTRY,
        "year": year or CALENDARIFIC_YEAR,
    }
    if CALENDARIFIC_STATE:
        params["location"] = CALENDARIFIC_STATE
    if month:
        params["month"] = month

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(CALENDARIFIC_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    holidays = data.get("response", {}).get("holidays", [])
    result = []
    for h in holidays:
        result.append({
            "name": h.get("name"),
            "date": h.get("date", {}).get("iso"),
            "type": h.get("type", []),
            "description": h.get("description", ""),
        })
    return {"holidays": result, "count": len(result), "year": params["year"]}
