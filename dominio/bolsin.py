from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dominio.cambioEstadoBolsin import CambioEstadoBolsin
from persistencia.base import Base


class Bolsin(Base):
    __tablename__ = "bolsin"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero_bolsin: Mapped[int] = mapped_column(unique=True)
    numero_precinto: Mapped[str | None] = mapped_column(String(30))
    fecha: Mapped[date]
    peso: Mapped[int]
    origen_id: Mapped[int] = mapped_column(ForeignKey("comision_medica.id"))
    destino_id: Mapped[int] = mapped_column(ForeignKey("comision_medica.id"))

    origen: Mapped["ComisionMedica"] = relationship(foreign_keys=[origen_id])
    destino: Mapped["ComisionMedica"] = relationship(foreign_keys=[destino_id])
    remitos: Mapped[list["Remito"]] = relationship(order_by="Remito.numero")
    cambios_estado: Mapped[list["CambioEstadoBolsin"]] = relationship(
        cascade="all, delete-orphan", order_by="CambioEstadoBolsin.id"
    )

    def es_tu_cm_destino(self, cm):
        return self.destino is cm

    def esta_enviado(self):
        actual = self.obtener_cambio_estado_actual()
        return actual is not None and actual.sos_enviado()

    def obtener_cambio_estado_actual(self):
        for cambio_estado in self.cambios_estado:
            if cambio_estado.sos_actual():
                return cambio_estado
        return None

    def obtener_estado_actual(self):
        actual = self.obtener_cambio_estado_actual()
        return actual.get_estado() if actual else None

    def get_numero_bolsin(self):
        return self.numero_bolsin

    def get_nro_precinto(self):
        return self.numero_precinto

    def get_fecha(self):
        return self.fecha

    def get_cm_origen(self):
        return self.origen

    def obtener_remitos(self):
        return self.remitos

    def asociar_remito(self, remito):
        self.remitos.append(remito)

    def recibir(self, estado_recibido, fecha_hora, responsable):
        self.cambiar_estado(estado_recibido, fecha_hora, responsable)

    def cambiar_estado(self, estado, fecha_hora, responsable):
        actual = self.obtener_cambio_estado_actual()
        if actual is not None:
            actual.set_fecha_hora_fin(fecha_hora)
        self.crear_cambio_estado_bolsin(estado, fecha_hora, responsable)

    def crear_cambio_estado_bolsin(self, estado, fecha_hora, responsable):
        self.cambios_estado.append(
            CambioEstadoBolsin(estado=estado, fecha_hora_inicio=fecha_hora, responsable_ce=responsable)
        )
