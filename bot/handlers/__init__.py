from .common import router as common_router
from .test_runner import router as test_runner_router
from .open_question import router as open_question_router
from .history import router as history_router
from .admin import router as admin_router

__all__ = [
    "common_router",
    "test_runner_router",
    "open_question_router",
    "history_router",
    "admin_router",
]
