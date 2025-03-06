import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_another_jwt_auth.exceptions import AuthJWTException
from pylti1p3.exception import LtiException
from sqlalchemy.exc import SQLAlchemyError

from .core.exception_handlers import invalid_jwt_state, invalid_lti_state, no_lis_service_access, \
    invalid_oidc_state, os_error_handler, database_error, no_entity_error, access_denied
from pylti1p3.oidc_login import OIDCException

from .exceptions.access_denied import AccessDeniedException
from .exceptions.no_entity import EntityNotFoundException
from .exceptions.lis_service_no_access import AgsNotSupportedException, NrpsNotSupportedException
from .routers.jwt_router import router as jwt_router
from .routers.lti_router import router as lti_router
from .routers.template_router import router as template_router
from .routers.file_router import router as file_router
from .routers.users_router import router as users_router
from .routers.report_router import router as report_router
from dotenv import load_dotenv
from labstructanalyzer.core.database import close_db

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_db()


app = FastAPI(lifespan=lifespan)

app.add_exception_handler(OIDCException, invalid_oidc_state)
app.add_exception_handler(AuthJWTException, invalid_jwt_state)
app.add_exception_handler(LtiException, invalid_lti_state)
app.add_exception_handler(OSError, os_error_handler)
app.add_exception_handler(SQLAlchemyError, database_error)
app.add_exception_handler(EntityNotFoundException, no_entity_error)
app.add_exception_handler(AgsNotSupportedException, no_lis_service_access)
app.add_exception_handler(NrpsNotSupportedException, no_lis_service_access)
app.add_exception_handler(AccessDeniedException, access_denied)

app.include_router(jwt_router, prefix='/api/v1/jwt')
app.include_router(lti_router, prefix='/api/v1/lti')
app.include_router(template_router, prefix='/api/v1/templates')
app.include_router(users_router, prefix='/api/v1/users')
app.include_router(report_router, prefix='/api/v1/reports')
app.include_router(file_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL"), "localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def start_dev():
    uvicorn.run(app="labstructanalyzer.main:app", reload=True, host="0.0.0.0")


def start_prod():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("labstructanalyzer.main:app", host="0.0.0.0", port=port)
