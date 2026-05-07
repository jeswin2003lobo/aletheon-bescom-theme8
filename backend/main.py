import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def validate_data_env():
    required = ["DATA_BASE_PATH", "FEEDBACK_DB_PATH", "KANNADA_CACHE_PATH"]
    for key in required:
        val = os.environ.get(key)
        if not val:
            raise RuntimeError(f"Missing required env var: {key}")
    data_path = Path(os.environ["DATA_BASE_PATH"])
    if not data_path.exists():
        raise RuntimeError(f"DATA_BASE_PATH does not exist: {data_path}")


def validate_all_env():
    validate_data_env()
    optional_warn = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "CALENDARIFIC_API_KEY", "ALERT_PHONE_NUMBERS"]
    for key in optional_warn:
        if not os.environ.get(key):
            logger.warning(f"  {key} not set — related features will be limited")


validate_all_env()

app = FastAPI(
    title="Aletheon BESCOM Smart Meter Intelligence",
    description="AI-powered anomaly detection, demand forecasting, and grid stress monitoring for BESCOM smart meters",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes import grid, anomaly, evidence, forecast, kpi, map_api, calendar_api, notify, feedback, translations, demo

app.include_router(grid.router)
app.include_router(anomaly.router)
app.include_router(evidence.router)
app.include_router(forecast.router)
app.include_router(kpi.router)
app.include_router(map_api.router)
app.include_router(calendar_api.router)
app.include_router(notify.router)
app.include_router(feedback.router)
app.include_router(translations.router)
app.include_router(demo.router)


@app.get("/")
def root():
    return {
        "name": "Aletheon BESCOM Smart Meter Intelligence",
        "version": "4.0.0",
        "theme": "Theme 8: AI for Smart Meter Intelligence & Loss Detection",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup():
    from services import data_loader
    start = time.time()
    logger.info("Loading all data files...")
    summary = data_loader.load_all_data()
    logger.info(f"  Loaded {summary['files_loaded']}/{summary['total_files']} files, "
                f"{summary['total_records']:,} records in {summary['load_time_seconds']}s")
    if summary["errors"]:
        for err in summary["errors"]:
            logger.warning(f"  Load error: {err}")


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("BACKEND_HOST", "0.0.0.0")
    port = int(os.environ.get("BACKEND_PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
