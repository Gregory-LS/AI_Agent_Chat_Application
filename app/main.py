from fastapi import FastAPI
from app.routes.export import router as export_router

app = FastAPI()

app.include_router(export_router)

@app.get("/")
async def root():
    return {"message": "Conversation Export API"}
