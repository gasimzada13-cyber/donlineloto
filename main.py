from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exception_handlers import http_exception_handler
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import datetime
import random
from db import (
    add_history,
    get_all_users,
    get_history as db_get_history,
    get_or_create_user,
    init_db,
    reset_all_coins,
    set_user_coin,
)

app = FastAPI()

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"
DEFAULT_USER_ID = "user1"
ADMIN_TOKEN = "12345"

STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class PlayRequest(BaseModel):
    user_id: str | None = None
    bet: int


class ResetRequest(BaseModel):
    user_id: str | None = None


class AdminSetCoinRequest(BaseModel):
    user_id: str
    coin: int


init_db()


def require_admin(token: str | None):
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    return await http_exception_handler(request, exc)


@app.get("/")
def home():
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))
    return {"status": "ok", "message": "Loto demo server is running"}


@app.get("/balance")
def get_balance(user_id: str = DEFAULT_USER_ID):
    coin = get_or_create_user(user_id)
    return {"user_id": user_id, "coin": coin}


@app.post("/play")
def play(data: PlayRequest):
    user_id = data.user_id or DEFAULT_USER_ID
    bet = data.bet
    coin = get_or_create_user(user_id)
    coin_before = coin

    if bet <= 0:
        return {"error": "Bet 0-dan boyuk olmalidir", "balance": coin}

    if coin < bet:
        return {"error": "Balans kifayet deyil", "balance": coin}

    coin -= bet

    numbers = random.sample(range(1, 91), 6)
    win = random.random() < 0.3

    if win:
        coin += bet * 2

    set_user_coin(user_id, coin)
    add_history(
        ts=datetime.datetime.utcnow().isoformat() + "Z",
        user_id=user_id,
        bet=bet,
        numbers=numbers,
        win=win,
        coin_before=coin_before,
        coin_after=coin,
    )

    return {"numbers": numbers, "win": win, "coin": coin}


@app.post("/reset")
def reset_balance(data: ResetRequest):
    user_id = data.user_id or DEFAULT_USER_ID
    coin = set_user_coin(user_id, 1000)
    return {"user_id": user_id, "coin": coin}


@app.get("/admin/users")
def admin_users(admin_token: str | None = Header(None, alias="X-Admin-Token")):
    require_admin(admin_token)
    return {"users": get_all_users()}


@app.post("/admin/set_coin")
def admin_set_coin(
    payload: AdminSetCoinRequest,
    admin_token: str | None = Header(None, alias="X-Admin-Token"),
):
    require_admin(admin_token)
    coin = set_user_coin(payload.user_id, payload.coin)
    return {"user_id": payload.user_id, "coin": coin}


@app.post("/admin/reset_all")
def admin_reset_all(admin_token: str | None = Header(None, alias="X-Admin-Token")):
    require_admin(admin_token)
    return {"users": reset_all_coins()}


@app.get("/history")
def history(user_id: str | None = None, limit: int = 20):
    return db_get_history(user_id=user_id, limit=limit)
