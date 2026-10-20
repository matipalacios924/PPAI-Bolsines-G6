"""Importa todas las entidades para que SQLAlchemy resuelva las relaciones."""
from dominio.provincia import Provincia
from dominio.localidad import Localidad
from dominio.comisionMedica import ComisionMedica
from dominio.rol import Rol
from dominio.empleado import Empleado
from dominio.usuario import Usuario
from dominio.sesion import Sesion
from dominio.tipoDocumento import TipoDocumento
from dominio.archivo import Archivo
from dominio.estado import Estado
from dominio.cambioEstadoDocumentacion import CambioEstadoDocumentacion
from dominio.documentacion import Documentacion
from dominio.detalleRemito import DetalleRemito
from dominio.remito import Remito
from dominio.cambioEstadoBolsin import CambioEstadoBolsin
from dominio.bolsin import Bolsin

__all__ = [
    "Provincia", "Localidad", "ComisionMedica", "Rol", "Empleado", "Usuario", "Sesion",
    "TipoDocumento", "Archivo", "Estado", "CambioEstadoDocumentacion", "Documentacion",
    "DetalleRemito", "Remito", "CambioEstadoBolsin", "Bolsin",
]
