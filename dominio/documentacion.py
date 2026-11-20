from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dominio.estadoDocumentacion import EstadoDocumentacionType, Registrada
from persistencia.base import Base


class Documentacion(Base):
    """Contexto del patrón State: delega cada transición en su estado actual."""
    __tablename__ = "documentacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int] = mapped_column(unique=True)
    asunto: Mapped[str] = mapped_column(String(200))
    fecha_pase: Mapped[date]
    tipo_documento_id: Mapped[int] = mapped_column(ForeignKey("tipo_documento.id"))
    cm_origen_id: Mapped[int] = mapped_column(ForeignKey("comision_medica.id"))
    estado = mapped_column(EstadoDocumentacionType, nullable=False)

    tipo_documento: Mapped["TipoDocumento"] = relationship()
    cm_origen: Mapped["ComisionMedica"] = relationship()
    archivos_adjuntos: Mapped[list["Archivo"]] = relationship(cascade="all, delete-orphan")
    cambios_estado: Mapped[list["CambioEstadoDocumentacion"]] = relationship(
        cascade="all, delete-orphan", order_by="CambioEstadoDocumentacion.id"
    )

    def registrar(self, fecha_hora, responsable):
        Registrada().registrar(self, fecha_hora, responsable)

    # ------------------------------------------------------------ getters / setters
    def get_numero(self):
        return self.numero

    def get_asunto(self):
        return self.asunto

    def get_cm_origen(self):
        return self.cm_origen

    def mostrar_tipo_documentacion(self):
        return self.tipo_documento.get_nombre()

    def get_estado(self):
        return self.estado

    def set_estado_actual(self, estado):
        self.estado = estado

    def get_cambios_estado(self):
        return self.cambios_estado

    def agregar_cambio_estado(self, cambio_estado):
        self.cambios_estado.append(cambio_estado)

    def fue_recibida_correctamente(self):
        return self.estado.es_recibida_correctamente()

    # --------------------------------------------- transiciones (delegan en State)
    def incluir_en_remito(self, fecha_hora, responsable):
        self.estado.incluir_en_remito(self, fecha_hora, responsable)

    def quitar_de_remito(self, fecha_hora, responsable):
        self.estado.quitar_de_remito(self, fecha_hora, responsable)

    def asignar_a_bolsin(self, fecha_hora, responsable):
        self.estado.asignar_a_bolsin(self, fecha_hora, responsable)

    def quitar_de_bolsin(self, fecha_hora, responsable):
        self.estado.quitar_de_bolsin(self, fecha_hora, responsable)

    def comenzar_traslado(self, fecha_hora, responsable):
        self.estado.comenzar_traslado(self, fecha_hora, responsable)

    def aceptar(self, fecha_hora, responsable):
        self.estado.aceptar(self, fecha_hora, responsable)

    def asignar_no_recibida(self, fecha_hora, responsable):
        self.estado.asignar_no_recibida(self, fecha_hora, responsable)

    def rechazar(self, fecha_hora, responsable):
        self.estado.rechazar(self, fecha_hora, responsable)

    def redirigir(self, fecha_hora, responsable):
        self.estado.redirigir(self, fecha_hora, responsable)

    def reasignar(self, fecha_hora, responsable):
        self.estado.reasignar(self, fecha_hora, responsable)

    def dar_de_baja(self, fecha_hora, responsable):
        self.estado.dar_de_baja(self, fecha_hora, responsable)
