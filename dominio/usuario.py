from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from persistencia.base import Base


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), unique=True)
    contrasenia: Mapped[str] = mapped_column(String(120))
    empleado_id: Mapped[int] = mapped_column(ForeignKey("empleado.id"))

    empleado: Mapped["Empleado"] = relationship()

    def get_nombre(self):
        return self.nombre

    def get_empleado(self):
        return self.empleado

    def validar_contrasenia(self, contrasenia):
        return self.contrasenia == contrasenia
