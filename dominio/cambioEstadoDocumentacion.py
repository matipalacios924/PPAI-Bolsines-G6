from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dominio.estadoDocumentacion import EstadoDocumentacionType
from persistencia.base import Base


class CambioEstadoDocumentacion(Base):
    __tablename__ = "cambio_estado_documentacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    documentacion_id: Mapped[int] = mapped_column(ForeignKey("documentacion.id"))
    estado = mapped_column(EstadoDocumentacionType, nullable=False)
    fecha_hora_inicio: Mapped[datetime]
    fecha_hora_fin: Mapped[datetime | None]
    responsable_ce_id: Mapped[int | None] = mapped_column(ForeignKey("empleado.id"))

    responsable_ce: Mapped["Empleado"] = relationship()

    def sos_actual(self):
        return self.fecha_hora_fin is None

    def get_estado(self):
        return self.estado

    def set_fecha_hora_fin(self, fecha):
        self.fecha_hora_fin = fecha

    def get_fecha_hora_fin(self):
        return self.fecha_hora_fin

    def get_fecha_hora_inicio(self):
        return self.fecha_hora_inicio
