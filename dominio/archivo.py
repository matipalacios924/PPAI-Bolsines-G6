from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from persistencia.base import Base


class Archivo(Base):
    __tablename__ = "archivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_archivo: Mapped[str] = mapped_column(String(120))
    titulo_documento: Mapped[str] = mapped_column(String(120))
    documentacion_id: Mapped[int] = mapped_column(ForeignKey("documentacion.id"))
