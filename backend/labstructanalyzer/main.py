import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.test_router import router as test_router
from .routers.jwt_router import router as jwt_router
from .routers.lti_router import router as lti_router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.include_router(test_router)
app.include_router(jwt_router)
app.include_router(lti_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def start_dev():
    uvicorn.run(app="labstructanalyzer.main:app", reload=True)

def start_prod():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("labstructanalyzer.main:app", host="0.0.0.0", port=port)
