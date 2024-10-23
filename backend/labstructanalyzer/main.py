import uvicorn
from fastapi import FastAPI
from .routers.test_router import router as test_router

app = FastAPI()
app.include_router(test_router)


def start_dev():
    uvicorn.run(app="labstructanalyzer.main:app", reload=True)
