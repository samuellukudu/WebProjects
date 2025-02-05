from fastapi import FastAPI
from src.api.routes import users, assessments, curriculum, onboarding, auth
from src.api.db.database import engine, Base

# Base.metadata.create_all(bind=engine)

app = FastAPI()

# Include API routes
# app.include_router(auth.router)
app.include_router(users.router)
app.include_router(assessments.router)
app.include_router(curriculum.router)
app.include_router(onboarding.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Language Learning AI API!"}