from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from persistencia.base import Base


class Empleado(Base):
    __tablename__ = "empleado"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60))
    apellido: Mapped[str] = mapped_column(String(60))
    email: Mapped[str] = mapped_column(String(120))
    rol_id: Mapped[int] = mapped_column(ForeignKey("rol.id"))
    comision_medica_id: Mapped[int] = mapped_column(ForeignKey("comision_medica.id"))

    rol: Mapped["Rol"] = relationship()
    comision_medica: Mapped["ComisionMedica"] = relationship()

    def get_cm(self):
        return self.comision_medica

    def es_tu_cm(self, cm):
        return self.comision_medica is cm

    def get_email(self):
        return self.email

    def get_nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def sos_gcm(self):
        return self.rol.es_gcm()
