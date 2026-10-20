from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from persistencia.base import Base


class Sesion(Base):
    __tablename__ = "sesion"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    fecha_hora_inicio: Mapped[datetime]
    fecha_hora_fin: Mapped[datetime | None]

    usuario: Mapped["Usuario"] = relationship()

    def get_usuario(self):
        return self.usuario

    def obtener_empleado(self):
        return self.usuario.get_empleado()

    def set_fecha_hora_fin(self, fecha):
        self.fecha_hora_fin = fecha
