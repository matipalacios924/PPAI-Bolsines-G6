from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from persistencia.base import Base

CODIGO_CMC = "CMC"


class ComisionMedica(Base):
    __tablename__ = "comision_medica"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(10), unique=True)
    nombre: Mapped[str] = mapped_column(String(80))
    direccion: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120))
    telefono: Mapped[str] = mapped_column(String(30))
    localidad_id: Mapped[int] = mapped_column(ForeignKey("localidad.id"))

    localidad: Mapped["Localidad"] = relationship()

    def get_nombre(self):
        return self.nombre

    def get_email(self):
        return self.email

    def get_codigo(self):
        return self.codigo

    def es_central(self):
        return self.codigo == CODIGO_CMC
