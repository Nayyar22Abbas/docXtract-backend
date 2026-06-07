# all user related functions , authentication etc


# from fastapi import FastAPI
from fastapi import APIRouter,Request
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from models.authmodel import UserCreate, UserLogin, Token
from config.db import authconn
import os
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from utilities.utils import hash_password, verify_password, create_access_token

authuser=APIRouter()
load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

templates = Jinja2Templates(directory="templates")


# google and github login procedure 
oauth=OAuth()
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




# remove in future its just for testing the login setup(below code)

@authuser.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# -------------------------------
# Signup Route
# -------------------------------
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
        "provider":"local"
    })
    return {"message": "User created successfully"}

# -------------------------------
# Login Route    Local user 
# -------------------------------
@authuser.post("/login", response_model=Token, summary="Login and get JWT", tags=["Authentication"])
def login(user: UserLogin):
    db_user = authconn.find_one({"username": user.username})

    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if db_user.get("provider")!="local":
        raise HTTPException(
            status_code=403,
            detail=f"use{db_user['provider']} Login instead"
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# google login


# OAuth always sends get request as it redirects the user 
@authuser.get("/login/google")
async def login_google(request: Request):
    return await oauth.google.authorize_redirect(request)  #type:ignore



@authuser.get("/auth/google")
async def auth_google(request:Request):
        # google sends code and state which is used by the backend to extract useremail to user as a token and then token is created
        token=await oauth.google.authorize_access_token(request)  #type:ignore
        user_info=token.get("userinfo")
        email=user_info["email"]
       # in below code the user will be searched such that if usrname contains the valid emaiol received from backend here in data base in place of user name we save email recieved from google 
        db_user=authconn.find_one({"username":email})
        if not db_user:
             authconn.insert_one({
                  "username":email,
                  "hashed-password":None,
                  "provider":"google"
             })

        access_token=create_access_token(data={"sub":email})

        redirect_url = f"{FRONTEND_URL}/oauth/callback?token={access_token}&provider=google"
        return RedirectResponse(url=redirect_url)
 
   

# github OAuth2

@authuser.get("/login/github")
async def login_github(request:Request):
     return await oauth.github.authorize_redirect(request) #type:ignore
     



@authuser.get("/auth/github")
async def auth_github(request:Request):
     token=await oauth.github.authorize_access_token(request)  #type:ignore
     user= await oauth.github.get("user",token=token)#type:ignore
     profile=user.json()
     email=profile.get("email")


     if not email:
          emails_resp= await oauth.github.get("user/emails",token=token)#type:ignore
          emails=emails_resp.json()
          email=next((e["email"] for e in emails if e["primary"]),None)

     if not email:
          raise HTTPException(status_code=400 ,detail="could not retrieve  emaui from Github ")
     
     db_user= authconn.find_one({"username":email})
     if not db_user:
          authconn.insert_one({
               "username":email,
               "hashed_password":None,
               "provider":"github"
               

          })

     access_token=create_access_token(data={"sub":email})

     redirect_url = f"{FRONTEND_URL}/oauth/callback?token={access_token}&provider=github"
     return RedirectResponse(url=redirect_url)





# @authuser.get("/dashboard", response_class=HTMLResponse, tags=["Authentication"])
# async def dashboard(request: Request, token: str = None): #type:ignore
#     return templates.TemplateResponse(
#         "dashboard.html",
#         {"request": request, "token": token}
#     )
