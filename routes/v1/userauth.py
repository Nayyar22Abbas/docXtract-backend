# all user related functions, authentication etc

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models.authmodel import UserCreate, UserLogin, Token
from config.db import authconn
import os
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from utilities.utils import hash_password, verify_password, create_access_token

authuser = APIRouter()
load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

templates = Jinja2Templates(directory="templates")

# -----------------------------------------------
# OAuth Setup
# -----------------------------------------------
oauth = OAuth()

oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)


# -----------------------------------------------
# Test Login Page (remove in production)
# -----------------------------------------------

@authuser.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# -----------------------------------------------
# Signup Route
# -----------------------------------------------
@authuser.post("/signup", summary="Create a new user", tags=["Authentication"])
def signup(user: UserCreate):
    """
    Create a new user.

    **Request body JSON must contain:**
    - `username`: string
    - `password`: string
    """
    
    if authconn.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = hash_password(user.password)
    authconn.insert_one({
        "username": user.username,
        "hashed_password": hashed_pw,
        "provider": "local"
    })
    return {"message": "User created successfully"}

# -----------------------------------------------
# Login Route    Local user 
# -----------------------------------------------
@authuser.post("/login", response_model=Token, summary="Login and get JWT", tags=["Authentication"])
def login(user: UserLogin):
    db_user = authconn.find_one({"username": user.username})

    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if db_user.get("provider") != "local":
        raise HTTPException(
            status_code=403,
            detail=f"Use {db_user['provider']} login instead"
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# -----------------------------------------------
# Google OAuth
# -----------------------------------------------
@authuser.get("/login/google", tags=["Authentication"])
async def login_google(request: Request):
    redirect_uri = f"{BACKEND_URL}/authuser/auth/google"
    return await oauth.google.authorize_redirect(request, redirect_uri)  # type: ignore



@authuser.get("/auth/google", tags=["Authentication"])
async def auth_google(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google OAuth failed: {str(e)}")

    user_info = token.get("userinfo")
    if not user_info or not user_info.get("email"):
        raise HTTPException(status_code=400, detail="Could not retrieve email from Google")

    email = user_info["email"]

    db_user = authconn.find_one({"username": email})
    if not db_user:
        authconn.insert_one({
            "username": email,
            "hashed_password": None,
            "provider": "google"
        })
    else:
        # if user exists but signed up locally, block oauth login
        if db_user.get("provider") == "local":
            raise HTTPException(
                status_code=403,
                detail="This email is registered with a password. Please log in normally."
            )

    access_token = create_access_token(data={"sub": email})
    redirect_url = f"{FRONTEND_URL}/oauth/callback?token={access_token}&provider=google"
    return RedirectResponse(url=redirect_url)

 
# -----------------------------------------------
# GitHub OAuth
# -----------------------------------------------
@authuser.get("/login/github", tags=["Authentication"])
async def login_github(request: Request):
    redirect_uri = f"{BACKEND_URL}/authuser/auth/github"
    return await oauth.github.authorize_redirect(request, redirect_uri)  # type: ignore


@authuser.get("/auth/github", tags=["Authentication"])
async def auth_github(request: Request):
    try:
        token = await oauth.github.authorize_access_token(request)  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"GitHub OAuth failed: {str(e)}")

    user = await oauth.github.get("user", token=token)  # type: ignore
    profile = user.json()
    email = profile.get("email")

    # GitHub may hide email, fetch from /user/emails
    if not email:
        emails_resp = await oauth.github.get("user/emails", token=token)  # type: ignore
        emails = emails_resp.json()
        email = next((e["email"] for e in emails if e.get("primary") and e.get("verified")), None)

    if not email:
        raise HTTPException(status_code=400, detail="Could not retrieve email from GitHub")

    db_user = authconn.find_one({"username": email})
    if not db_user:
        authconn.insert_one({
            "username": email,
            "hashed_password": None,
            "provider": "github"
        })
    else:
        if db_user.get("provider") == "local":
            raise HTTPException(
                status_code=403,
                detail="This email is registered with a password. Please log in normally."
            )

    access_token = create_access_token(data={"sub": email})
    redirect_url = f"{FRONTEND_URL}/oauth/callback?token={access_token}&provider=github"
    return RedirectResponse(url=redirect_url)





# @authuser.get("/dashboard", response_class=HTMLResponse, tags=["Authentication"])
# async def dashboard(request: Request, token: str = None): #type:ignore
#     return templates.TemplateResponse(
#         "dashboard.html",
#         {"request": request, "token": token}
#     )
