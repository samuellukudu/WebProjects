from fastapi import APIRouter, HTTPException
from src.models.user import User
from src.schemas.user import UserSchema

router = APIRouter()

# In-memory user storage for demonstration purposes
fake_users_db = {}

@router.post("/users/", response_model=UserSchema)
async def create_user(user: UserSchema):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    fake_users_db[user.username] = User(**user.dict())
    return fake_users_db[user.username]

@router.get("/users/{username}", response_model=UserSchema)
async def read_user(username: str):
    user = fake_users_db.get(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{username}", response_model=UserSchema)
async def update_user(username: str, user: UserSchema):
    if username not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not found")
    fake_users_db[username] = User(**user.dict())
    return fake_users_db[username]

@router.delete("/users/{username}")
async def delete_user(username: str):
    if username not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not found")
    del fake_users_db[username]
    return {"detail": "User deleted"}