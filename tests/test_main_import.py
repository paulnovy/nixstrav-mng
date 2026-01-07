def test_import_main_app():
    from app.main import app
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.middleware.sessions import SessionMiddleware

    assert app is not None
    middleware_classes = [mw.cls for mw in app.user_middleware]
    assert middleware_classes[:2] == [TrustedHostMiddleware, CORSMiddleware]
    assert SessionMiddleware in middleware_classes
    assert middleware_classes[-1] is BaseHTTPMiddleware
