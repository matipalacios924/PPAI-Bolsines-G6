from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from persistencia.base import Base


class TipoDocumento(Base):
    __tablename__ = "tipo_documento"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60))
    descripcion: Mapped[str] = mapped_column(String(200), default="")

    def get_nombre(self):
        return self.nombre

    def get_descripcion(self):
        return self.descripcion
