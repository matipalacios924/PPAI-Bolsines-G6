from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from persistencia.base import Base


class Remito(Base):
    __tablename__ = "remito"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int] = mapped_column(unique=True)
    fecha: Mapped[date]
    estado_id: Mapped[int] = mapped_column(ForeignKey("estado.id"))
    origen_id: Mapped[int] = mapped_column(ForeignKey("comision_medica.id"))
    destino_id: Mapped[int] = mapped_column(ForeignKey("comision_medica.id"))
    numero_bolsin: Mapped[int | None] = mapped_column(ForeignKey("bolsin.numero_bolsin"))

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

    # ------------------------------------------- recepción (CU 28)
    # Cada método dispara un evento concreto de la documentación. El próximo
    # estado lo decide el estado actual de cada documentación (patrón State),
    # no un parámetro que indique la situación.
    def recibir_y_aceptar(self, excepto, fecha_hora, responsable):
        """Acepta toda la documentación del remito salvo la afectada por la opción del EB."""
        for detalle in self._detalles_de(excepto, incluidos=False):
            detalle.aceptar_documentacion(fecha_hora, responsable)

    def asignar_no_recibida_documentacion(self, documentacion, fecha_hora, responsable):
        for detalle in self._detalles_de(documentacion):
            detalle.asignar_no_recibida_documentacion(fecha_hora, responsable)

    def rechazar_documentacion(self, documentacion, fecha_hora, responsable):
        for detalle in self._detalles_de(documentacion):
            detalle.rechazar_documentacion(fecha_hora, responsable)

    def redirigir_documentacion(self, documentacion, areas, fecha_hora, responsable):
        for detalle in self._detalles_de(documentacion):
            detalle.redirigir_documentacion(areas[detalle.get_documentacion()], fecha_hora, responsable)

    def set_estado_recibida_y_aceptada(self, estado_aceptado, estado_aceptado_parcial):
        """Recibido y aceptado si toda su documentación llegó bien (lo responde su estado)."""
        if all(doc.fue_recibida_correctamente() for doc in self.buscar_documentacion()):
            self.set_estado(estado_aceptado)
        else:
            self.set_estado(estado_aceptado_parcial)

    def _detalles_de(self, documentacion, incluidos=True):
        return [d for d in self.detalles_remito if (d.get_documentacion() in documentacion) is incluidos]
