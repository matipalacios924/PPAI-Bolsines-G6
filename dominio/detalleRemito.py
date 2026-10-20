from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dominio.situacionRecepcion import SituacionRecepcion
from persistencia.base import Base


class DetalleRemito(Base):
    __tablename__ = "detalle_remito"

    id: Mapped[int] = mapped_column(primary_key=True)
    remito_id: Mapped[int] = mapped_column(ForeignKey("remito.id"))
    documentacion_id: Mapped[int] = mapped_column(ForeignKey("documentacion.id"))
    area_cmc_destino: Mapped[str | None] = mapped_column(String(80))

    documentacion: Mapped["Documentacion"] = relationship()

    def get_documentacion(self):
        return self.documentacion

    def get_area_cmc_destino(self):
        return self.area_cmc_destino

    def actualizar_estado_doc(self, situacion, area, fecha_hora, responsable):
        doc = self.documentacion
        if situacion is SituacionRecepcion.ACEPTADA:
            doc.aceptar(fecha_hora, responsable)
        elif situacion is SituacionRecepcion.NO_RECIBIDA:
            doc.asignar_no_recibida(fecha_hora, responsable)
        elif situacion is SituacionRecepcion.RECHAZADA:
            doc.rechazar(fecha_hora, responsable)
        elif situacion is SituacionRecepcion.REDIRIGIR:
            self.area_cmc_destino = area
            doc.redirigir(fecha_hora, responsable)
