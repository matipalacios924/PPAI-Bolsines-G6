# Consistencia entre el diagrama de secuencia (draw.io) y el código – CU 28

Comparamos el diagrama de secuencia de diseño (`PPAI2.drawio`) con la implementación y aplicamos las observaciones del docente. Para que los dos muestren lo mismo:

1. **Se modificó el código** para que siga al diagrama en todo lo posible (nombres de clases y métodos, orden de los mensajes y responsabilidades) y para resolver las observaciones del docente.
2. **Hay que corregir el diagrama** en los puntos donde copiarlo al pie de la letra dejaba el código incorrecto o incompleto, y donde el docente marcó errores.

La versión del diagrama que ya coincide con el código es [`diagramas/secuencia_diseno.puml`](diagramas/secuencia_diseno.puml). Sirve de referencia para corregir el draw.io.

---

## 0. Observaciones del docente y cómo se resolvieron

| Observación | Solución | Dónde se ve |
|---|---|---|
| Las llamadas que populan los atributos del gestor desde la BD debiesen llamarse en el constructor | El constructor de `GestorRegRecepBolsin` busca la CM del usuario logueado, los bolsines enviados y los tres estados de la recepción. Se eliminó `nuevaRecepcionBolsin()`. | Punto 1.1 |
| Faltan retornos y parámetros en el diagrama de secuencia | Todos los mensajes llevan sus parámetros y tienen su flecha de retorno (punteada). | Punto 1.3 |
| No necesitan el ID en la clase Bolsin | Se quitó `id`: el bolsín se identifica por `numeroBolsin`. | Punto 2 |
| No agregan el nuevo CE de Bolsin en la secuencia | Después del `new()` del `CambioEstadoBolsin` se agrega `agregarCambioEstado(nuevoCEB)`. | Punto 1.4 |
| Aparece ACEPTADA en el método de transición | Se eliminó `actualizarEstadoDoc(ACEPTADA, ...)` y el enum `SituacionRecepcion`. El mensaje es el evento: `aceptarDocumentacion()` → `aceptar()`. | Punto 1.5 |
| En la búsqueda de la flexibilización acoplan la decisión de transición al parámetro | Ningún método recibe la situación ni el estado destino para decidir con `if`. El próximo estado lo decide el estado concreto actual (patrón State). | Punto 1.5 |

---

## 1. Qué hay que cambiar en el diagrama de secuencia

### 1.1 Mover las búsquedas al constructor del gestor (obs. docente)
Agregar al principio un tramo **"Pasos 1 a 3"**:
- `:PantallaRegRecBolsin → :GestorRegRecepBolsin : new(sesionId, interfazNotificacion)` (mensaje de creación).
- Dentro del gestor recién creado:
  - `buscarCMUsuarioLogueado()` → `sesionActual:Sesion : obtenerEmpleado()` (retorna `empleadoLogueado`) → `empleadoLogueado:Empleado : getCM()` (retorna `cmUsuarioLogueado`).
  - `buscarBolsinesEnviados()` con un bucle `[mientras haya bolsines]`: `esTuCMDestino(cmUsuarioLogueado)` y `estaEnviado()`, cada uno con retorno `boolean`.
  - `buscarEstadoRecibidoEnCMDestino(estados)`, `buscarEstadoRecibidoYAceptadoRemito(estados)` y `buscarEstadoRecibidoYAceptadoParcialRemito(estados)` con sus bucles `[mientras haya estados]`.
- **Sacar** estas tres búsquedas de estados de `tomarConfirmacion()`: ahí ya no se buscan, se usan los atributos cargados en el constructor.

Se mantienen los nombres corregidos en la revisión anterior:
- `buscarEstadoRecibidoEnCMDestino()` (no `...Remito()`): "Recibido en CM destino" es del ámbito **Bolsín**.
- Hace falta la búsqueda de *Recibido y aceptado parcial*: sin ella no funcionan los flujos alternativos.

### 1.2 Nuevo orden de `tomarConfirmacion(confirma = true)`
1. `obtenerFechaHoraActual()` → retorna `fechaHoraActual`
2. `setBolsinEstadoRecibido()` → `seleccionado:Bolsin : recibirBolsin(...)` (recorre los remitos y acepta la documentación)
3. *(sólo flujos A3, A4 y A5)* `registrarDocumentacionAfectada()`; en el flujo básico no se ejecuta, conviene indicarlo con una nota
4. `seleccionado:Bolsin : actualizarEstadoRemitos(estadoRemAceptado, estadoRemParcial)` → por cada remito `setEstadoRecibidaYAceptada(...)`
5. `notificarRecepcion()` (CU 29) → `obtenerResultado()` → `mostrarResultado(resultado)` → `finCU()`

El estado del remito ahora se decide **después** de las transiciones, preguntándole a cada documentación `fueRecibidaCorrectamente()` (que delega en `esRecibidaCorrectamente()` de su estado), y no a partir de la situación elegida.

### 1.3 Parámetros y retornos de los mensajes (obs. docente)
| Mensaje en el diagrama | Cómo debe quedar |
|---|---|
| `recibirBolsin(...)` | `recibirBolsin(estadoRecibido, documentacionAfectada, fechaHoraActual, empleadoLogueado)` |
| `setBolsinEstadoRecibido()` (en Bolsín) | `setBolsinEstadoRecibido(estadoRecibido, fechaHoraActual, empleadoLogueado)` |
| `new()` del CambioEstadoBolsin | `new(estadoRecibido, fechaHoraActual, empleadoLogueado)` |
| `recibirYAceptar(...)` | `recibirYAceptar(documentacionAfectada, fechaHoraActual, empleadoLogueado)` |
| `setEstadoRecibidaYAceptada(...)` | `setEstadoRecibidaYAceptada(estadoRemAceptado, estadoRemParcial)`: lo envía `seleccionado:Bolsin` desde `actualizarEstadoRemitos()` |
| `actualizarEstadoDoc(ACEPTADA, ...)` | **Se reemplaza** por `aceptarDocumentacion(fechaHoraActual, empleadoLogueado)` (ver 1.5) |
| `cambiarEstado(doc, aceptada, ...)` | `cambiarEstado(documentacion, RecibidaYAceptada, fechaHoraActual, empleadoLogueado)`: recibe la **clase** del siguiente estado |
| `crearSigEstado()` | `crearSigEstado(RecibidaYAceptada)` |
| `crearCambioEstado()` | `crearCambioEstado(aceptada, fechaHoraActual, empleadoLogueado)` |
| `new(fechaHoraInicio, e:Estado)` del nuevo CED | `new(aceptada, fechaHoraActual, empleadoLogueado)` |
| `setFechaHoraFin(fechaHora):DateTime` | `setFechaHoraFin(fechaHoraActual)`: es un parámetro, no un tipo de retorno |
| `tomarConfirmacion()` (Pantalla → Gestor) | `tomarConfirmacion(confirma = true)` |
| `mostrarResultado()` | `mostrarResultado(resultado)` |

Retornos que hay que dibujar (flecha punteada):

| Mensaje | Retorno |
|---|---|
| `obtenerEmpleado()` | `empleadoLogueado` |
| `getCM()` | `cmUsuarioLogueado` |
| `esTuCMDestino()`, `estaEnviado()`, `esAmbito...()`, `es...()`, `sosActual()` | `boolean` |
| `buscarBolsinesEnviados()` / `buscarEstado...()` | `bolsinesEnviados` / `estadoRecibido`, `estadoRemAceptado`, `estadoRemParcial` |
| `obtenerFechaHoraActual()` | `fechaHoraActual` |
| `obtenerCambioEstadoActual()` / `buscarCambioEstadoActual()` | `actualCEB` / `actualCED` |
| `getDocumentacion()` | `documentacion` |
| `getCambiosEstado()` | `cambiosEstado` |
| `crearSigEstado()` / `crearCambioEstado()` | `aceptada` / `nuevoCED` |
| `fueRecibidaCorrectamente()` / `esRecibidaCorrectamente()` | `true` |
| `enviarNotificacion()` | `notificacion` |
| `obtenerResultado()` y `tomarConfirmacion()` | `resultado` |

### 1.4 Agregar el nuevo CambioEstadoBolsin al bolsín (obs. docente)
Después de `crearCambioEstadoBolsin(...)` y `nuevoCEB:CambioEstadoBolsin : new(...)`, agregar:
- `seleccionado:Bolsin → seleccionado:Bolsin : agregarCambioEstado(nuevoCEB)`

Así queda igual que en la Documentación, donde el estado ya envía `agregarCambioEstado(nuevoCED)`.

### 1.5 Quitar la situación del método de transición (obs. docente)
- **Dice:** `:Remito → :DetalleRemito : actualizarEstadoDoc(ACEPTADA, area, fechaHora, empleado)`, y adentro el detalle decide con `if` qué evento llamar según el parámetro.
- **Debe decir:** `:Remito → :DetalleRemito : aceptarDocumentacion(fechaHoraActual, empleadoLogueado)` → `:Documentacion : aceptar(fechaHoraActual, empleadoLogueado)` → `enviado:EnBolsinEnviado : aceptar(documentacion, fechaHoraActual, empleadoLogueado)`.
- El bucle del remito pasa a ser `[por cada DetalleRemito no afectado]`.
- **Motivo:** con `actualizarEstadoDoc(ACEPTADA, ...)` la decisión de la transición dependía de un parámetro, que es justo lo que el patrón State evita. Ahora cada mensaje **es** el evento de la máquina de estados y el estado concreto decide a qué estado pasa. Para los flujos alternativos hay un mensaje por evento: `asignarNoRecibidaDocumentacion`, `rechazarDocumentacion` y `redirigirDocumentacion(area, ...)`.

### 1.6 Nombre del setter de Documentación
- `setEstadoActual(aceptada)`: el parámetro es de tipo `EstadoDocumentacion`, no `Estado`.

### 1.7 Ubicación del bucle de remitos
- `recibirYAceptar(...)` lo sigue enviando **`seleccionado:Bolsin`** a `:Remito`, dentro de `recibirBolsin`.
- `setEstadoRecibidaYAceptada(...)` ya **no** va al principio de `recibirYAceptar`: va en un segundo bucle de remitos, dentro de `actualizarEstadoRemitos(...)` (ver 1.2).

### 1.8 Final del flujo (CU 29 incluido)
Después de actualizar los remitos, en el Gestor:
- `notificarRecepcion()`, con la nota *"se incluye CU 29 Notificar recepción de bolsín"*
- bucle `[por cada CM de origen]`: `:GestorRegRecepBolsin → :InterfazNotificacion : enviarNotificacion(emailCMOrigen, asunto, cuerpo)`, con retorno `notificacion`
- `obtenerResultado()` → retorno `resultado` a la pantalla
- `:PantallaRegRecBolsin → mostrarResultado(resultado)`
- `:PantallaRegRecBolsin → :GestorRegRecepBolsin : finCU()`

### 1.9 Detalles de forma
- Corregir el error de tipeo **"RebibidoEnCMDestino"** → `recibido:CambioEstadoBolsin`.
- La lifeline `Estado` debe llamarse `:Estado`.
- Agregar las lifelines `sesionActual:Sesion`, `empleadoLogueado:Empleado` y `:Bolsin` (para el tramo del constructor).
- Agregar una nota general: *"Se muestra el flujo básico: opción 1 – el contenido del bolsín es igual al registrado"*.

---

## 2. Qué se modificó en el código

| Archivo | Cambio |
|---|---|
| `gestor/gestorRecepcionBolsin.py` | La clase se llama **`GestorRegRecepBolsin`**. **El constructor** llama a `buscarCMUsuarioLogueado()`, `buscarBolsinesEnviados()` y a las tres `buscarEstado...()`; se eliminó `nuevaRecepcionBolsin()`. `tomarConfirmacion()` sigue el orden del punto 1.2. Se reemplazaron `situaciones` por `documentacionAfectada` (la documentación que marcó el EB) y se agregó `registrarDocumentacionAfectada()` para los flujos A3, A4 y A5. El bolsín se selecciona por `numeroBolsin` y el filtro de CM de origen usa su código. |
| `pantalla/pantallaRecepcionBolsin.py` | La clase se llama **`PantallaRegRecBolsin`**. Sólo crea el gestor (ya no llama a `nuevaRecepcionBolsin()`) y envía `numero_bolsin` en lugar del id. |
| `dominio/bolsin.py` | **Sin atributo `id`**: `numeroBolsin` es el identificador (clave primaria). `recibirBolsin(estadoRecibido, documentacionAfectada, fechaHora, empleado)` cierra el cambio de estado actual, llama a `setBolsinEstadoRecibido()` y recorre los remitos con `recibirYAceptar()`. `crearCambioEstadoBolsin()` ahora llama a **`agregarCambioEstado(nuevoCEB)`**. Nuevo `actualizarEstadoRemitos()`. |
| `dominio/remito.py`, `dominio/cambioEstadoBolsin.py` | La clave foránea al bolsín pasa a ser `numero_bolsin`. `recibirYAceptar(excepto, fechaHora, empleado)` envía `aceptarDocumentacion()` a cada detalle no afectado. Métodos por evento: `asignarNoRecibidaDocumentacion`, `rechazarDocumentacion` y `redirigirDocumentacion`. `setEstadoRecibidaYAceptada()` decide entre aceptado y parcial preguntando `fueRecibidaCorrectamente()` a cada documentación. |
| `dominio/detalleRemito.py` | Se eliminó `actualizarEstadoDoc(situacion, ...)` con su `if/elif`. Hay un método por evento: `aceptarDocumentacion`, `asignarNoRecibidaDocumentacion`, `rechazarDocumentacion` y `redirigirDocumentacion(area, ...)`. |
| `dominio/situacionRecepcion.py` | **Eliminado.** |
| `dominio/estadoDocumentacion.py` (State) | Sin cambios en esta revisión: `cambiarEstado` → `buscarCambioEstadoActual` → `setFechaHoraFin` → `crearSigEstado` → `crearCambioEstado` → `agregarCambioEstado` → `setEstadoActual`. |
| `pantalla/templates/recepcion_*.html` | Usan el número de bolsín y de documentación en lugar del id. La vista previa de la confirmación ya no depende de `SituacionRecepcion`. |
| `tests/test_recepcion_bolsin.py` | Adaptados a los cambios, más un test nuevo que verifica que el constructor carga los atributos desde la BD. Los 11 tests pasan. |
| `docs/diagramas/*.puml`, `docs/Entrega2_Diseno.md` | Actualizados con todos los cambios anteriores. |

> Como cambió el esquema de la base (Bolsín sin id), la primera vez hay que ejecutar `python main.py --reset`.

---

## 3. Pendiente en el documento de la entrega

- Pasar al draw.io y al `.docx` de la entrega los cambios del punto 1.
- En el diagrama de clases del `.docx`: quitar el `id` de Bolsín, el enum `SituacionRecepcion` y `actualizarEstadoDoc()`, y agregar los métodos nuevos de `Bolsin`, `Remito` y `DetalleRemito` (ver [`diagramas/clases_diseno.puml`](diagramas/clases_diseno.puml)).
- En "Identificación del patrón implementado" dice *"los diferentes comportamientos que presenta **el Bolsín**"*. Debe decir **la Documentación**, que es el contexto del patrón State.
- En "Detalles de implementación" dice **Flask 2**. El proyecto usa **Flask 3** (`requirements.txt`).
- Completar las secciones 2 (vista estática) y 3 (vista dinámica) con los diagramas.
