"""Interfaz con el Servidor de Correo (CU 29 Notificar recepción de bolsín).

El RNF 5 pide usar la API de Outlook (Microsoft Graph). Para la demo el envío
se simula: cada mail queda registrado en notificaciones/notificaciones.log.
"""
from datetime import datetime
from pathlib import Path

CARPETA_NOTIFICACIONES = Path(__file__).resolve().parent.parent / "notificaciones"


class InterfazNotificacion:
    def __init__(self, carpeta=CARPETA_NOTIFICACIONES):
        self.carpeta = Path(carpeta)

    def enviar_notificacion(self, destinatario, asunto, cuerpo):
        self.carpeta.mkdir(parents=True, exist_ok=True)
        enviado = datetime.now()
        with open(self.carpeta / "notificaciones.log", "a", encoding="utf-8") as log:
            log.write(
                f"=== {enviado:%d/%m/%Y %H:%M:%S}\n"
                f"Para: {destinatario}\nAsunto: {asunto}\n\n{cuerpo}\n\n"
            )
        return {"destinatario": destinatario, "asunto": asunto, "cuerpo": cuerpo,
                "fecha_hora": enviado}
