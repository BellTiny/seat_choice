import httpx
from sqlalchemy.orm import Session

from app.models.models import SiteSetting


async def send_webhook_if_configured(db: Session, payload: dict) -> None:
    settings = db.query(SiteSetting).filter(SiteSetting.id == 1).first()
    if not settings or not settings.webhook_url:
        return

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(settings.webhook_url, json=payload)
    except httpx.HTTPError:
        return
