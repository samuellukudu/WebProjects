from fastapi import FastAPI
from .api.routes import users, assessments, curriculum, onboarding

app = FastAPI()

# Include API routes
app.include_router(users.router)
app.include_router(assessments.router)
app.include_router(curriculum.router)
app.include_router(onboarding.router)
# app.include_router(analytics.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Language Learning AI API!"}