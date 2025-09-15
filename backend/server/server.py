from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routers.general import router

def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    
    # CORS settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Adjust as needed for security
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app

if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="localhost", port=8000)