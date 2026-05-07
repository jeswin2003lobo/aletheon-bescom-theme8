from fastapi import APIRouter
from pydantic import BaseModel
from services import kannada_service

router = APIRouter(prefix="/api/translations", tags=["Translations"])


class TranslateRequest(BaseModel):
    text: str


class BatchTranslateRequest(BaseModel):
    texts: list[str]


@router.post("/kannada")
def translate_to_kannada(req: TranslateRequest):
    return {
        "english": req.text,
        "kannada": kannada_service.translate_to_kannada(req.text),
    }


@router.post("/kannada/batch")
def translate_batch(req: BatchTranslateRequest):
    return kannada_service.translate_batch(req.texts)


@router.get("/cache-stats")
def cache_stats():
    return kannada_service.get_cache_stats()
