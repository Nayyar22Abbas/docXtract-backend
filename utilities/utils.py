from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta,timezone
from dotenv import load_dotenv
import os
# Password hashing

load_dotenv()









pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# JWT token
# SECRET_KEY=os.getenv("SECRET_KEY")
# if SECRET_KEY is None:
#     raise ValueError("SECRET_KEY environment variable not set")
SECRET_KEY="hqZDbsUApxuD1xPMGzKwLcK_tpHnrwaDEEqTN-muw58"



ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
 
                                        #   explanation of access token function
                                                    
# here  data =dict because we have passed a dictationary in the argument to this function {"sub":"user.username"}

def create_access_token(data: dict):


    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
