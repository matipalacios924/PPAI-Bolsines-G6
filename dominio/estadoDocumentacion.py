"""Patrón State (GoF) aplicado a la Documentación.

Contexto:        Documentacion
Estado:          EstadoDocumentacion (abstracto)
Estados concr.:  Registrada, EnRemito, EnBolsinSaliente, EnBolsinEnviado,
                 RecibidaYAceptada, NoRecibida, RecibidaYRechazada,
                 ParaRedirigir, DeBaja

Cada estado concreto sólo redefine las transiciones que le están permitidas
según la máquina de estados de Documentación; el resto lanza
TransicionNoPermitidaError (comportamiento heredado de la clase abstracta).
"""
from abc import ABC

from sqlalchemy import String
from sqlalchemy.types import TypeDecorator


class TransicionNoPermitidaError(Exception):
    pass


class EstadoDocumentacion(ABC):
    nombre: str = ""
    _registro: dict[str, type["EstadoDocumentacion"]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        EstadoDocumentacion._registro[cls.nombre] = cls

    @staticmethod
    def desde_nombre(nombre: str) -> "EstadoDocumentacion":
        return EstadoDocumentacion._registro[nombre]()

    def get_nombre(self) -> str:
        return self.nombre

    def es_recibida_correctamente(self) -> bool:
        """La documentación llegó a destino y fue aceptada (o derivada a un área)."""
        return False

    # ---------------------------------------------------------------- transiciones
    def incluir_en_remito(self, documentacion, fecha_hora, responsable):
        self._no_permitida("incluir en un remito")

    def quitar_de_remito(self, documentacion, fecha_hora, responsable):
        self._no_permitida("quitar de un remito")

    def asignar_a_bolsin(self, documentacion, fecha_hora, responsable):
        self._no_permitida("asignar a un bolsín")

    def quitar_de_bolsin(self, documentacion, fecha_hora, responsable):
        self._no_permitida("quitar de un bolsín")

    def comenzar_traslado(self, documentacion, fecha_hora, responsable):
        self._no_permitida("enviar")

    def aceptar(self, documentacion, fecha_hora, responsable):
        self._no_permitida("aceptar")

    def asignar_no_recibida(self, documentacion, fecha_hora, responsable):
        self._no_permitida("marcar como no recibida")

    def rechazar(self, documentacion, fecha_hora, responsable):
        self._no_permitida("rechazar")

    def redirigir(self, documentacion, fecha_hora, responsable):
        self._no_permitida("redirigir")

    def reasignar(self, documentacion, fecha_hora, responsable):
        self._no_permitida("volver a registrar")

    def dar_de_baja(self, documentacion, fecha_hora, responsable):
        self._no_permitida("dar de baja")

    # ------------------------------------------------------------------ auxiliares
    def _no_permitida(self, accion):
        raise TransicionNoPermitidaError(
            f"No se puede {accion} una documentación en estado '{self.nombre}'."
        )

    def cambiar_estado(self, documentacion, clase_sig_estado, fecha_hora, responsable):
        """Cierra el cambio de estado actual, crea el siguiente estado y su cambio de estado."""
        cambio_estado_actual = self.buscar_cambio_estado_actual(documentacion)
        if cambio_estado_actual is not None:
            cambio_estado_actual.set_fecha_hora_fin(fecha_hora)
        sig_estado = self.crear_sig_estado(clase_sig_estado)
        nuevo_cambio_estado = self.crear_cambio_estado(sig_estado, fecha_hora, responsable)
        documentacion.agregar_cambio_estado(nuevo_cambio_estado)
        documentacion.set_estado_actual(sig_estado)

    def buscar_cambio_estado_actual(self, documentacion):
        for cambio_estado in documentacion.get_cambios_estado():
            if cambio_estado.sos_actual():
                return cambio_estado
        return None

    def crear_sig_estado(self, clase_sig_estado):
        return clase_sig_estado()

    def crear_cambio_estado(self, estado, fecha_hora, responsable):
        from dominio.cambioEstadoDocumentacion import CambioEstadoDocumentacion

        return CambioEstadoDocumentacion(
            estado=estado, fecha_hora_inicio=fecha_hora, responsable_ce=responsable
        )

    def __eq__(self, other):
        return type(self) is type(other)

    def __hash__(self):
        return hash(type(self))

    def __repr__(self):
        return f"<{type(self).__name__}>"


class Registrada(EstadoDocumentacion):
    nombre = "Registrada"

    def registrar(self, documentacion, fecha_hora, responsable):
        """Estado inicial: se crea el primer cambio de estado."""
        self.cambiar_estado(documentacion, Registrada, fecha_hora, responsable)

    def incluir_en_remito(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, EnRemito, fecha_hora, responsable)

    def dar_de_baja(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, DeBaja, fecha_hora, responsable)


class EnRemito(EstadoDocumentacion):
    nombre = "En remito"

    def quitar_de_remito(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, Registrada, fecha_hora, responsable)

    def asignar_a_bolsin(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, EnBolsinSaliente, fecha_hora, responsable)


class EnBolsinSaliente(EstadoDocumentacion):
    nombre = "En bolsín saliente"

    def quitar_de_bolsin(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, EnRemito, fecha_hora, responsable)

    def comenzar_traslado(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, EnBolsinEnviado, fecha_hora, responsable)


class EnBolsinEnviado(EstadoDocumentacion):
    nombre = "En bolsín enviado"

    def aceptar(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, RecibidaYAceptada, fecha_hora, responsable)

    def asignar_no_recibida(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, NoRecibida, fecha_hora, responsable)

    def rechazar(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, RecibidaYRechazada, fecha_hora, responsable)

    def redirigir(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, ParaRedirigir, fecha_hora, responsable)


class ParaRedirigir(EstadoDocumentacion):
    """El área de la CMC verifica la documentación recibida internamente."""
    nombre = "Para redirigir"

    def es_recibida_correctamente(self):
        return True

    def aceptar(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, RecibidaYAceptada, fecha_hora, responsable)

    def rechazar(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, RecibidaYRechazada, fecha_hora, responsable)


class RecibidaYAceptada(EstadoDocumentacion):
    nombre = "Recibida y aceptada"

    def es_recibida_correctamente(self):
        return True


class NoRecibida(EstadoDocumentacion):
    nombre = "No recibida"

    def reasignar(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, Registrada, fecha_hora, responsable)

    def dar_de_baja(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, DeBaja, fecha_hora, responsable)


class RecibidaYRechazada(EstadoDocumentacion):
    nombre = "Recibida y rechazada"

    def reasignar(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, Registrada, fecha_hora, responsable)

    def dar_de_baja(self, documentacion, fecha_hora, responsable):
        self.cambiar_estado(documentacion, DeBaja, fecha_hora, responsable)


class DeBaja(EstadoDocumentacion):
    nombre = "De baja"


class EstadoDocumentacionType(TypeDecorator):
    """Persiste el estado como su nombre y lo reconstruye como objeto State."""
    impl = String(40)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else value.get_nombre()

    def process_result_value(self, value, dialect):
        return None if value is None else EstadoDocumentacion.desde_nombre(value)
