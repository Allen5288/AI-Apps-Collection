from  fastapi  import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middlewares.exception_handlers import catch_exception_middleware

app=FastAPI(title="Medical Assistant API",description="API for Medical AI Assistant",version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# middleware exception handlers
app.middleware("http")(catch_exception_middleware)

# routers
# 1. upload pdf document
# 2. asking query