import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.jwt_router import router as jwt_router
from .routers.lti_router import router as lti_router
from .routers.template_router import router as template_router
from .routers.file_router import router as file_router
from .routers.users_router import router as users_router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.include_router(jwt_router, prefix='/api/v1/jwt')
app.include_router(lti_router, prefix='/api/v1/lti')
app.include_router(template_router, prefix='/api/v1/template')
app.include_router(users_router, prefix='/api/v1/users')
app.include_router(file_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL"), "localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def start_dev():
    uvicorn.run(
        app="labstructanalyzer.main:app",
        reload=True,
        ssl_certfile="../cert.pem",
        ssl_keyfile="../key.pem"
    )

def start_prod():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("labstructanalyzer.main:app", host="0.0.0.0", port=port)
