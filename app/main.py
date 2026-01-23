from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.api import products, scorecards, config, supply_chain, auth
from app.core.config import get_settings
from app.core.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    init_db()
    yield


app = FastAPI(
    title="EcoFashion Scorecard API",
    description="Backend API for sustainability scoring of fashion products",
    version="0.1.0",
    lifespan=lifespan,
)

# Add session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(scorecards.router)
app.include_router(config.router)
app.include_router(supply_chain.router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}

