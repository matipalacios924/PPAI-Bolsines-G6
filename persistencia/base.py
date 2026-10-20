from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

RUTA_BD = Path(__file__).resolve().parent.parent / "bolsines.db"


class Base(DeclarativeBase):
    pass


engine = None
SessionLocal = sessionmaker(expire_on_commit=False)


def configurar_bd(url=None):
    """Crea el engine (SQLite por defecto) y las tablas del modelo."""
    global engine
    import dominio  # noqa: F401  registra todas las entidades mapeadas

    engine = create_engine(
        url or f"sqlite:///{RUTA_BD}",
        connect_args={"check_same_thread": False},
    )
    SessionLocal.configure(bind=engine)
    Base.metadata.create_all(engine)
    return engine


def reiniciar_bd():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
