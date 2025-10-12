from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routers.general import router as general_router
from server.routers.statements import router as statements_router
from server.routers.transactions import router as transactions_router
from server.routers.formulas import router as formulas_router
from server.routers.rules import router as rules_router
from server.routers.reports import router as reports_router

def create_app() -> FastAPI:
    app = FastAPI()
    
    # CORS settings - MUST be added before routers
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Adjust as needed for security
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(general_router, prefix="/api")
    app.include_router(statements_router, prefix="/api")
    app.include_router(transactions_router, prefix="/api")
    app.include_router(formulas_router, prefix="/api")
    app.include_router(rules_router, prefix="/api")
    app.include_router(reports_router, prefix="/api")

    return app

# Create app instance for uvicorn
app = create_app()

def main():
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)

if __name__ == "__main__":
    main()