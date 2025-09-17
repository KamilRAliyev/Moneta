from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routers.general import router as general_router
from server.routers.statements import router as statements_router

def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(general_router, prefix="/api")
    app.include_router(statements_router, prefix="/api")
    
    # CORS settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Adjust as needed for security
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app

def main():
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="localhost", port=8000)

if __name__ == "__main__":
    main()