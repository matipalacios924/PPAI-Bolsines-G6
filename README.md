# PPAI 2026 – Bolsines – G6

Implementación del **CU 28 Registrar recepción de bolsín** con el patrón **State** aplicado a la Documentación.
Python + Flask + SQLAlchemy + SQLite.

## Cómo ejecutar

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py            # http://127.0.0.1:5000
python main.py --reset    # vuelve a cargar los datos de prueba
```

Usuarios de prueba (contraseña `1234`):

| Usuario | Rol / CM | Para probar |
|---|---|---|
| `eb.cordoba` | EB – CM Córdoba | Flujo principal, A1, A2, A3, A4, A6 |
| `eb.cmc` | EB – Comisión Médica Central | A5 (redirigir a un área) |
| `eb.parana` | EB – CM Paraná | CM sin bolsines enviados |

Las notificaciones (CU 29) se simulan y se guardan en `notificaciones/notificaciones.log`.

## Tests

```powershell
python -m unittest discover -s tests -t . -v
```

## Estructura

```
main.py                         arranque de la app
pantalla/                       boundary (Flask + plantillas)
gestor/gestorRecepcionBolsin.py control del CU 28
interfaz/interfazNotificacion.py interfaz con el servidor de correo (CU 29)
dominio/                        entidades (SQLAlchemy)
dominio/estadoDocumentacion.py  patrón State
persistencia/                   configuración de BD y datos de prueba
docs/                           documento de la entrega y diagramas PlantUML
```
