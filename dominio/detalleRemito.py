from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    def set_area_cmc_destino(self, area):
        self.area_cmc_destino = area

    def aceptar_documentacion(self, fecha_hora, responsable):
        self.documentacion.aceptar(fecha_hora, responsable)

    def asignar_no_recibida_documentacion(self, fecha_hora, responsable):
        self.documentacion.asignar_no_recibida(fecha_hora, responsable)

    def rechazar_documentacion(self, fecha_hora, responsable):
        self.documentacion.rechazar(fecha_hora, responsable)

    def redirigir_documentacion(self, area, fecha_hora, responsable):
        self.set_area_cmc_destino(area)
        self.documentacion.redirigir(fecha_hora, responsable)
