def test_import_main_app():
    from app.main import app

    assert app is not None
