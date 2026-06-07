from fastapi import APIRouter, Depends
from utilities.verifyJWTprotectedRoute import get_current_user
protected_router = APIRouter()

@protected_router.get("/protected")
def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello {current_user}, you accessed a protected route!"}
