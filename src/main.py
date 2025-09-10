from fastapi import FastAPI, Request, Response, status
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
from datetime import datetime
from datetime import timedelta
from src.presentation.routes.api.auth.auth_router import router as auth_router
from src.presentation.routes.api.settings.settings_router import router as settings_router
from src.presentation.routes.api.chats.chat_router import router as chat_router
from src.presentation.routes.api.clinics.clinic_router import router as clinic_router
from src.presentation.routes.api.orders.order_router import router as order_router
from src.presentation.routes.api.responses.response_router import router as response_router
from src.presentation.routes.api.reviews.reviews_router import router as reviews_router
from src.presentation.routes.api.users.user_router import router as user_router
from src.presentation.routes.api.users.admin_router import router as admin_router
from src.presentation.routes.api.users.organization_router import router as organization_router
from src.presentation.routes.api.users.patient_router import router as patient_router
from src.presentation.routes.api.users.specialist_router import router as specialist_router
from src.infrastructure.repository.database import init_db
from pathlib import Path
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
import os
import dotenv

dotenv.load_dotenv()
if os.getenv("PYTEST_CURRENT_TEST") != "PYTEST_CURRENT_TEST":
    sentry_sdk.init(
        dsn="https://b206bbba03bb59a27df8b3f39893979a@o4509976777981952.ingest.de.sentry.io/4509976967512144",
        integrations=[
            FastApiIntegration(),
            StarletteIntegration(),
        ],
        send_default_pii=True,
    )


app = FastAPI(docs_url='/doc', redoc_url='/redoc', openapi_url='/openapi')
app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(chat_router)
app.include_router(clinic_router)
app.include_router(order_router)
app.include_router(response_router)
app.include_router(reviews_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(organization_router)
app.include_router(patient_router)
app.include_router(specialist_router)


@app.get("/test-sentry-error")
async def trigger_error():
    division_by_zero = 1 / 0
    return {"message": "Этот код никогда не выполнится"}

@app.get('/health')
async def hcheck():
    return 200


class RateLimitMiddleware(BaseHTTPMiddleware):
    RATE_LIMIT = 60
    TIME_WINDOW = timedelta(minutes=1)
    BAN_TIME = timedelta(minutes=5)

    def __init__(self, app):
        super().__init__(app)
        self.requests = {}
        self.banned_until = {}

    async def dispatch(self, request: Request, call_next):
        if "PYTEST_CURRENT_TEST" in os.environ:
            return await call_next(request)

        client_ip = request.client.host
        now = datetime.now()

        if client_ip in self.banned_until:
            if now < self.banned_until[client_ip]:
                retry_after = (self.banned_until[client_ip] - now).seconds
                headers = {"Retry-After": str(retry_after)}
                return Response("Too many requests", status_code=status.HTTP_429_TOO_MANY_REQUESTS, headers=headers)
            else:
                del self.banned_until[client_ip]

        if client_ip not in self.requests:
            self.requests[client_ip] = []

        self.requests[client_ip] = [req_time for req_time in self.requests[client_ip]
                                    if now - req_time < self.TIME_WINDOW]

        if len(self.requests[client_ip]) >= self.RATE_LIMIT:
            self.banned_until[client_ip] = now + self.BAN_TIME
            headers = {"Retry-After": str(self.BAN_TIME.seconds)}
            return Response("Too many requests", status_code=status.HTTP_429_TOO_MANY_REQUESTS, headers=headers)

        self.requests[client_ip].append(now)

        return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os

app.add_middleware(RateLimitMiddleware)


@app.on_event("startup")
async def startup_event():
    await init_db()


@app.get("/")
async def root():
    html_file = Path("templates/docs.html")
    if not html_file.exists():
        return HTMLResponse(content="Documentation not found", status_code=404)

    return FileResponse(html_file)


@app.get("/api-docs-config.json")
async def get_config():
    BASE_DIR = Path(__file__).resolve().parent.parent
    config_path = BASE_DIR / "src/templates/api-docs-config.json"
    return FileResponse(config_path)
