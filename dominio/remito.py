from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dominio.situacionRecepcion import SituacionRecepcion
from persistencia.base import Base


class Remito(Base):
    __tablename__ = "remito"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int] = mapped_column(unique=True)
    fecha: Mapped[date]
    estado_id: Mapped[int] = mapped_column(ForeignKey("estado.id"))
    origen_id: Mapped[int] = mapped_column(ForeignKey("comision_medica.id"))
    destino_id: Mapped[int] = mapped_column(ForeignKey("comision_medica.id"))
    bolsin_id: Mapped[int | None] = mapped_column(ForeignKey("bolsin.id"))

    estado: Mapped["Estado"] = relationship()
    origen: Mapped["ComisionMedica"] = relationship(foreign_keys=[origen_id])
    destino: Mapped["ComisionMedica"] = relationship(foreign_keys=[destino_id])
    detalles_remito: Mapped[list["DetalleRemito"]] = relationship(
        cascade="all, delete-orphan", order_by="DetalleRemito.id"
    )

    def get_numero(self):
        return self.numero

    def get_estado(self):
        return self.estado

    def set_estado(self, estado):
        self.estado = estado

    def buscar_documentacion(self):
        return [detalle.get_documentacion() for detalle in self.detalles_remito]

    def get_detalles_remito(self):
        return self.detalles_remito

    def tenes_esta_cm_destino(self, cm):
        return self.destino is cm

    def tenes_esta_cm_origen(self, cm):
        return self.origen is cm

    def tomar_documentacion(self, detalle):
        self.detalles_remito.append(detalle)

    def recibir_y_aceptar(self, situaciones, areas, fecha_hora, responsable,
                          estado_aceptado, estado_aceptado_parcial):
        self.set_estado_recibida_y_aceptada(situaciones, estado_aceptado, estado_aceptado_parcial)
        for detalle in self.detalles_remito:
            doc = detalle.get_documentacion()
            situacion = situaciones.get(doc.id, SituacionRecepcion.ACEPTADA)
            detalle.actualizar_estado_doc(situacion, areas.get(doc.id), fecha_hora, responsable)

    def set_estado_recibida_y_aceptada(self, situaciones, estado_aceptado, estado_aceptado_parcial):
        """Recibido y aceptado si toda su documentación llega bien; si no, aceptado parcial."""
        todas_ok = all(
            situaciones.get(doc.id, SituacionRecepcion.ACEPTADA).es_recibida_correctamente()
            for doc in self.buscar_documentacion()
        )
        self.set_estado(estado_aceptado if todas_ok else estado_aceptado_parcial)
