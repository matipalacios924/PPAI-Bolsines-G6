# Consistencia entre el diagrama de secuencia (draw.io) y el código – CU 28

Comparamos el diagrama de secuencia de diseño (`PPAI2.drawio`) con la implementación. Para que los dos muestren lo mismo:

1. **Se modificó el código** para que siga al diagrama en todo lo posible (nombres de clases y métodos, orden de los mensajes y responsabilidades).
2. **Hay que corregir el diagrama** en los puntos donde copiarlo al pie de la letra dejaba el código incorrecto o incompleto.

La versión del diagrama que ya coincide con el código es [`diagramas/secuencia_diseno.puml`](diagramas/secuencia_diseno.puml). Sirve de referencia para corregir el draw.io.

---

## 1. Qué hay que cambiar en el diagrama de secuencia

### 1.1 Nombre de la búsqueda del estado del bolsín
- **Dice:** `buscarEstadoRecibidoEnCMDestinoRemito()`
- **Debe decir:** `buscarEstadoRecibidoEnCMDestino()`
- **Motivo:** "Recibido en CM destino" es un estado del ámbito **Bolsín**, no del Remito. Lo confirma el propio bucle, que pregunta `esAmbitoBolsin()`.

### 1.2 Agregar la búsqueda del estado "Recibido y aceptado parcial"
- Después de `buscarEstadoRecibidoYAceptadoRemito()` y su bucle, agregar:
  - `buscarEstadoRecibidoYAceptadoParcialRemito()`
  - un bucle `[Mientras haya estados]` con `esAmbitoRemito()` y `esRecibidoYAceptadoParcial()` (o una nota que diga "mismo recorrido con esRecibidoYAceptadoParcial()").
- **Motivo:** si falta documentación o hay documentación que no corresponde al destino, el remito queda en *Recibido y aceptado parcial*. Sin esta búsqueda no funcionan los flujos alternativos.

### 1.3 Agregar parámetros a los mensajes
| Mensaje en el diagrama | Cómo debe quedar |
|---|---|
| `recibirBolsin()` | `recibirBolsin(estadoRecibido, situaciones, areas, fechaHora, empleado, estAceptado, estParcial)` |
| `setBolsinEstadoRecibido()` (en Bolsín) | `setBolsinEstadoRecibido(estadoRecibido, fechaHora, empleado)` |
| `new()` del CambioEstadoBolsin | `new(estadoRecibido, fechaHora, empleado)` |
| `recibirYAceptar()` | `recibirYAceptar(situaciones, areas, fechaHora, empleado, estAceptado, estParcial)` |
| `setEstadoRecibidaYAceptada()` | `setEstadoRecibidaYAceptada(situaciones, estAceptado, estParcial)` |
| `actualizarEstadoDoc(ACEPTADA, fechaHora, empleado)` | `actualizarEstadoDoc(ACEPTADA, area, fechaHora, empleado)` (en el flujo básico, `area` = null) |
| `cambiarEstado(doc, aceptada, fechaHora, empleado)` | `cambiarEstado(doc, RecibidaYAceptada, fechaHora, empleado)`: recibe la **clase** del siguiente estado, porque el objeto todavía no existe |
| `crearSigEstado()` | `crearSigEstado(RecibidaYAceptada)` |
| `crearCambioEstado()` | `crearCambioEstado(aceptada, fechaHora, empleado)` |
| `new(fechaHoraInicio, e:Estado)` del nuevo CED | `new(aceptada, fechaHora, empleado)` |
| `setFechaHoraFin(fechaHora):DateTime` | `setFechaHoraFin(fechaHora)`: es un parámetro, no un tipo de retorno |

**Motivo:** el Bolsín, el Remito y los estados no tienen forma de obtener por sí mismos la fecha/hora, el empleado ni los estados buscados por el Gestor. Además, sin el `empleado` el cambio de estado queda sin responsable.

### 1.4 Nombre del setter de Documentación
- **Dice:** `setEstadoActual(e:Estado)`. Se mantiene el nombre, pero el parámetro es `e:EstadoDocumentacion`, es decir, el objeto `aceptada`.

### 1.5 Ubicación del bucle de remitos
- El mensaje `recibirYAceptar(...)` lo envía **`seleccionado:Bolsin`** a `:Remito`, dentro de `recibirBolsin`, tal como está dibujado. No cambia nada; solo se deja constancia de que el código ahora hace lo mismo.

### 1.6 Agregar el final del flujo (CU 29 incluido)
Después del bucle de remitos, agregar en el Gestor:
- `notificarRecepcion()`, con una nota: *"se incluye CU 29 Notificar recepción de bolsín"*
- bucle `[por cada CM de origen]`: `:GestorRegRecepBolsin → :InterfazNotificacion : enviarNotificacion(email, asunto, cuerpo)`
- `obtenerResultado()`
- `:PantallaRegRecBolsin → mostrarResultado()`
- `finCU()`

### 1.7 Detalles de forma
- Corregir el error de tipeo **"RebibidoEnCMDestino"** → `recibido:CambioEstadoBolsin`.
- La lifeline `Estado` debe llamarse `:Estado`.
- Agregar una nota general: *"Se muestra el flujo básico: opción 1 – el contenido del bolsín es igual al registrado"*.

---

## 2. Qué se modificó en el código

| Archivo | Cambio |
|---|---|
| `gestor/gestorRecepcionBolsin.py` | La clase pasa a llamarse **`GestorRegRecepBolsin`**. Se eliminaron `registrarRecepcion()` y `_buscar_estado()`. `tomarConfirmacion()` ahora sigue el orden del diagrama: `obtenerFechaHoraActual()` → `buscarEstadoRecibidoEnCMDestino()` → `buscarEstadoRecibidoYAceptadoRemito()` → `buscarEstadoRecibidoYAceptadoParcialRemito()` (cada una recorre los estados con `esAmbito...()` / `es...()`) → `setBolsinEstadoRecibido()` → `notificarRecepcion()` → `obtenerResultado()`. |
| `pantalla/pantallaRecepcionBolsin.py` | La clase pasa a llamarse **`PantallaRegRecBolsin`**. |
| `dominio/bolsin.py` | `recibir()` se reemplazó por **`recibirBolsin(...)`**: busca el cambio de estado actual, le pone `setFechaHoraFin`, llama a **`setBolsinEstadoRecibido()`** (que crea el nuevo `CambioEstadoBolsin`) y **recorre los remitos** enviando `recibirYAceptar()`. Antes este recorrido lo hacía el Gestor. Se conserva `cambiarEstado()` genérico porque lo usa la carga de datos de prueba. |
| `dominio/remito.py` | `registrarRecepcion()` se reemplazó por **`recibirYAceptar(...)`**: primero llama a **`setEstadoRecibidaYAceptada()`** y después recorre los detalles con `actualizarEstadoDoc()`, como en el diagrama. El estado del remito (aceptado o parcial) se decide a partir de la situación elegida para cada documentación. |
| `dominio/situacionRecepcion.py` | Nuevo método `esRecibidaCorrectamente()`, que usa el Remito para decidir entre aceptado y aceptado parcial antes de recorrer los detalles. |
| `dominio/estadoDocumentacion.py` (State) | Los métodos auxiliares privados pasan a ser los del diagrama: **`cambiarEstado` → `buscarCambioEstadoActual` → `setFechaHoraFin` → `crearSigEstado` → `crearCambioEstado` → `agregarCambioEstado` → `setEstadoActual`**. Ahora el siguiente estado se crea dentro de `crearSigEstado()`, igual que en el diagrama. |
| `dominio/documentacion.py` | `setEstado()` pasa a llamarse **`setEstadoActual()`**. |
| `tests/test_recepcion_bolsin.py` | Se actualizó el nombre del Gestor. Los 10 tests pasan. |
| `docs/diagramas/*.puml`, `docs/Entrega2_Diseno.md` | Se actualizaron los nombres de clases y métodos en el diagrama de clases y en el de secuencia de referencia. |

---

## 3. Pendiente en el documento de la entrega

- En "Identificación del patrón implementado" dice *"los diferentes comportamientos que presenta **el Bolsín**"*. Debe decir **la Documentación**, que es el contexto del patrón State.
- En "Detalles de implementación" dice **Flask 2**. El proyecto usa **Flask 3** (`requirements.txt`).
- Completar las secciones 2 (vista estática) y 3 (vista dinámica) con los diagramas.
