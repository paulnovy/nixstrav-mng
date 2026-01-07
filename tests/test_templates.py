def test_templates_have_settings():
    from app.routers import views

    assert views.templates.env.globals.get("settings") is not None
