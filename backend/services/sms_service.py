import httpx
import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")
ALERT_PHONE_NUMBERS = os.environ.get("ALERT_PHONE_NUMBERS", "")

TWILIO_URL = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"


async def send_sms(message: str, phone_numbers: str = None):
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return {"error": "Twilio credentials not configured", "sent": False}

    numbers = phone_numbers or ALERT_PHONE_NUMBERS
    if not numbers:
        return {"error": "No phone numbers configured", "sent": False}

    results = []
    for number in numbers.split(","):
        number = number.strip()
        if not number:
            continue

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                TWILIO_URL,
                data={
                    "To": number,
                    "From": TWILIO_PHONE_NUMBER,
                    "Body": message,
                },
                auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            )

            if resp.status_code == 201:
                data = resp.json()
                results.append({
                    "sent": True,
                    "to": number,
                    "sid": data.get("sid"),
                    "status": data.get("status"),
                })
            else:
                results.append({
                    "sent": False,
                    "to": number,
                    "error": resp.text[:200],
                })

    return {
        "sent": all(r["sent"] for r in results),
        "message_sent": message[:50],
        "results": results,
    }


async def send_alert(case_id: str, meter_id: str, priority: str, reason: str):
    message = (
        f"ALETHEON ALERT [{priority}] Case {case_id}: "
        f"Meter {meter_id} - {reason[:80]}"
    )
    return await send_sms(message)
