from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from persistencia.base import Base

AMBITO_BOLSIN = "Bolsin"
AMBITO_REMITO = "Remito"


class Estado(Base):
    """Estados de Bolsín y Remito (los de Documentación se modelan con el patrón State)."""
    __tablename__ = "estado"

    id: Mapped[int] = mapped_column(primary_key=True)
    ambito: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(60))
    descripcion: Mapped[str] = mapped_column(String(200), default="")

    def es_ambito_bolsin(self):
        return self.ambito == AMBITO_BOLSIN

    def es_ambito_remito(self):
        return self.ambito == AMBITO_REMITO

    def es_creado(self):
        return self.nombre == "Creado"

    def es_cerrado(self):
        return self.nombre == "Cerrado"

    def es_enviado(self):
        return self.nombre == "Enviado"

    def es_en_bolsin_saliente(self):
        return self.nombre == "En bolsín saliente"

    def es_en_bolsin_enviado(self):
        return self.nombre == "En bolsín enviado"

    def es_recibido_en_cm_destino(self):
        return self.nombre == "Recibido en CM destino"

    def es_recibido_y_aceptado(self):
        return self.nombre == "Recibido y aceptado"

    def es_recibido_y_aceptado_parcial(self):
        return self.nombre == "Recibido y aceptado parcial"

    def get_ambito(self):
        return self.ambito

    def get_nombre(self):
        return self.nombre

    def get_descripcion(self):
        return self.descripcion
