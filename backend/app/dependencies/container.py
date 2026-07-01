from typing import cast

from app.core.container import Container
from fastapi import Request


def get_container(request: Request) -> Container:
    """
    FastAPI dependency provider to retrieve the current container
    instance associated with the application state.
    """
    return cast(Container, request.app.state.container)
