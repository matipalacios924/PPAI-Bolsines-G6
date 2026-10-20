from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from persistencia.base import Base


class Rol(Base):
    __tablename__ = "rol"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60))
    descripcion: Mapped[str] = mapped_column(String(200), default="")

    def get_nombre(self):
        return self.nombre

    def es_gcm(self):
        return self.nombre == "Gerente de Comisión Médica"
