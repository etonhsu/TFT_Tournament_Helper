import os
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

from app.endpoints import auth, create_tournament

app = FastAPI(title='TFT Tournament Helper API', version='1.0', description='API for managing TFT tournaments')

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://yourdomain.com",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allowing all methods
    allow_headers=["*"],  # Allowing all headers
)


app.include_router(auth.router)
app.include_router(create_tournament.router)


@app.on_event('startup')
async def startup_event():
    print('Starting up...')


@app.on_event('shutdown')
async def shutdown_event():
    print('Shutting down...')

# Run the app with Uvicorn if this file is executed directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
