from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.containers import router as containers_router
from config import docker_client

app = FastAPI()

# Allow requests from all origins (for testing). Restrict in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific frontend URLs in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include the containers router
app.include_router(containers_router, prefix="/api", tags=["containers"])

@app.get("/")
async def root():
    print("LIst containers",docker_client.containers.list())
    return {"message": "Welcome to the Container Management API!"}
