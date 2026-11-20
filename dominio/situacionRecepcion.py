from enum import Enum


class SituacionRecepcion(Enum):
    """Situación de cada documentación al controlar un bolsín recibido."""
    ACEPTADA = "Recibida y aceptada"
    NO_RECIBIDA = "No recibida"
    RECHAZADA = "No corresponde al destino"
    REDIRIGIR = "Para redirigir a otra área"

    def es_recibida_correctamente(self):
        """Coincide con EstadoDocumentacion.es_recibida_correctamente del estado resultante."""
        return self in (SituacionRecepcion.ACEPTADA, SituacionRecepcion.REDIRIGIR)
