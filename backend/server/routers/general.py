from fastapi import APIRouter
from server.services import health

router = APIRouter()

@router.get("/health")
def health_check():
    return health.get_health_info()
