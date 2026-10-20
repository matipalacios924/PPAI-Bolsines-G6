from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from persistencia.base import Base


class Localidad(Base):
    __tablename__ = "localidad"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60))
    descripcion: Mapped[str] = mapped_column(String(200), default="")
    provincia_id: Mapped[int] = mapped_column(ForeignKey("provincia.id"))

    provincia: Mapped["Provincia"] = relationship()

    def get_nombre(self):
        return self.nombre
