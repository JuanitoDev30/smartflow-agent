


"""Puerto de entrada de la app"""


import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import build_container
from app.api.routes import chat
from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s %(name)s  %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.container = build_container(settings)
    logging.getLogger(__name__).info(
      "Asistente listo | modelo=%s | repositorio=%s",
      settings.llm_model,
      settings.repository_backend,
    )
    yield
    
    closer = getattr(app.state.container, "aclose", None)
    if closer is not None and hasattr(closer, "aclose"):
        await closer.aclose()
        
        
app = FastAPI(title="Asistente de pedidos", version="1.0.0", lifespan=lifespan)


#Ajustar a los orgenes del chat web

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat.router)


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    """Endpoint de salud de la app"""
    return {"status": "ok"}