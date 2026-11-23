from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from persistencia.base import Base


class CambioEstadoBolsin(Base):
    __tablename__ = "cambio_estado_bolsin"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero_bolsin: Mapped[int] = mapped_column(ForeignKey("bolsin.numero_bolsin"))
    estado_id: Mapped[int] = mapped_column(ForeignKey("estado.id"))
    fecha_hora_inicio: Mapped[datetime]
    fecha_hora_fin: Mapped[datetime | None]
    responsable_ce_id: Mapped[int | None] = mapped_column(ForeignKey("empleado.id"))

    estado: Mapped["Estado"] = relationship()
    responsable_ce: Mapped["Empleado"] = relationship()

    def sos_actual(self):
        return self.fecha_hora_fin is None

    def sos_enviado(self):
        return self.estado.es_enviado()

    def get_estado(self):
        return self.estado

    def set_fecha_hora_fin(self, fecha):
        self.fecha_hora_fin = fecha

    def get_fecha_hora_inicio(self):
        return self.fecha_hora_inicio
