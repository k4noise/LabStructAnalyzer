import uvicorn
from fastapi import FastAPI
from .routers.test_router import router as test_router
from .routers.jwt_router import router as jwt_router
from .routers.lti_router import router as lti_router

app = FastAPI()
app.include_router(test_router)
app.include_router(jwt_router)
app.include_router(lti_router)

def start_dev():
    uvicorn.run(app="labstructanalyzer.main:app", reload=True)
