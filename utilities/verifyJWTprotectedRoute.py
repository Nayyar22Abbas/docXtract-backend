from jose import JWTError, jwt
from typing import Optional
from fastapi import Depends, HTTPException, status
from schemas.securitySchema import oauth2_scheme
SECRET_KEY = "hqZDbsUApxuD1xPMGzKwLcK_tpHnrwaDEEqTN-muw58" # must be same as used in create_access_token
ALGORITHM = "HS256"

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Decode and verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extract "sub" (username) from payload
        username: Optional[str ] = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
