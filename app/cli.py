import typer

from .config import settings
from .database import Base, SessionLocal, engine
from .services.known_tags import persist_db_to_json, sync_json_to_db
from .services.users import create_user, ensure_admin_exists

app = typer.Typer(help="nixstrav-mng management CLI")


@app.command("init-db")
def init_db(create_default_admin: bool = typer.Option(False, help="Create admin:admin if DB empty")):
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        sync_json_to_db(session, settings.nixstrav_known_tags_json)
        if create_default_admin:
            ensure_admin_exists(session)
    finally:
        session.close()
    typer.echo("DB initialized")


@app.command("create-user")
def cli_create_user(
    username: str,
    password: str,
    role: str = typer.Option("viewer", help="Role: admin/operator/viewer"),
):
    from .models import UserRole

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        user = create_user(session, username=username, password=password, role=UserRole(role))
        persist_db_to_json(session, settings.nixstrav_known_tags_json)
        typer.echo(f"Created user {user.username} ({user.role})")
    finally:
        session.close()


if __name__ == "__main__":
    app()
