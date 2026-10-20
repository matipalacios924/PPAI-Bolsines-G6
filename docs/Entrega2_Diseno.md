# PPAI 2026 – Bolsines – Entrega 2: Diseño

**Caso de uso:** CU 28 Registrar recepción de bolsín
**Máquina de estados asignada:** Documentación
**Grupo:** G6 (grupo par)

> Completar la carátula con los datos de la sección 1 de las consignas (curso, fecha, docentes, docente tutor e integrantes con legajo y mail).

---

## 1. Identificación del patrón implementado

**Patrón:** State (GoF, de comportamiento).

### Problema

En el modelo de análisis, `Documentacion` conoce su situación a través de `CambioEstadoDocumentacion` → `Estado`, y la clase `Estado` resuelve las preguntas con métodos booleanos (`esEnviado()`, `esRecibidaYAceptada()`, …). Esto trae tres problemas:

1. **Lógica condicional dispersa.** Cada operación sobre la documentación (aceptar, rechazar, marcar como no recibida, redirigir, reasignar, dar de baja…) tiene que preguntar primero en qué estado está la documentación y decidir si la transición es válida y cuál es el estado siguiente. Esto lleva a cadenas de `if/else` repetidas en el gestor y en las entidades.
2. **La máquina de estados de Documentación es la más grande del dominio.** Tiene 9 estados y 11 eventos, y la usan varios casos de uso (7, 9, 15, 16, 17, 19, 20, 21, 27, 28 y 31). Cada estado nuevo o regla nueva obligaría a tocar todos esos condicionales.
3. **Hay transiciones inválidas que deben impedirse.** Por ejemplo, aceptar una documentación que todavía está *En remito*, o redirigir una que no viene en un bolsín enviado. Con condicionales, controlarlo depende de que cada caso de uso lo verifique.

### Solución y justificación

Se aplica **State**: el comportamiento que depende del estado se delega en un objeto estado.

| Rol del patrón | Clase |
|---|---|
| Context | `Documentacion` |
| State (abstracto) | `EstadoDocumentacion` |
| ConcreteState | `Registrada`, `EnRemito`, `EnBolsinSaliente`, `EnBolsinEnviado`, `ParaRedirigir`, `RecibidaYAceptada`, `NoRecibida`, `RecibidaYRechazada`, `DeBaja` |

- `Documentacion` tiene una referencia a su estado actual y **delega** cada evento: `documentacion.aceptar(fh, resp)` → `estado.aceptar(self, fh, resp)`.
- `EstadoDocumentacion` declara **todas** las transiciones de la máquina de estados. Su implementación por defecto lanza `TransicionNoPermitidaError`. Cada estado concreto **redefine sólo las transiciones permitidas** según el diagrama de máquina de estados, así que las transiciones inválidas quedan impedidas por diseño.
- El estado concreto que ejecuta la transición:
  1. busca el `CambioEstadoDocumentacion` actual y le asigna `fechaHoraFin`;
  2. crea el próximo estado (por ejemplo, `RecibidaYAceptada`);
  3. crea el nuevo `CambioEstadoDocumentacion` con el empleado responsable (requisito de trazabilidad);
  4. lo agrega a la documentación y actualiza su estado actual.
- Además, el estado responde preguntas que dependen de él. Por ejemplo, `esRecibidaCorrectamente()` vale *true* en `RecibidaYAceptada` y `ParaRedirigir`. `Remito` lo usa para decidir entre *Recibido y aceptado* y *Recibido y aceptado parcial* sin preguntar por nombres de estado.

**Beneficios en este CU:** el gestor ya no decide estados de la documentación. Sólo traduce la opción que elige el EB a una `SituacionRecepcion` por documento, y `DetalleRemito` invoca el evento correspondiente (`aceptar`, `asignarNoRecibida`, `rechazar` o `redirigir`). Agregar un estado o una transición nueva implica agregar o modificar una sola clase, lo que cumple con el principio abierto/cerrado.

**Alcance:** los estados de `Bolsin` y `Remito` se siguen modelando con la entidad `Estado` del modelo de dominio, ya que su máquina de estados corresponde a los grupos impares.

---

## 2. Vista estática (diagrama de clases de diseño)

Fuente: [`diagramas/clases_diseno.puml`](diagramas/clases_diseno.puml). Incluye tipos de datos, tipos de retorno, parámetros y visibilidad (`+` público, `-` privado, `#` protegido).

## 3. Vista dinámica (diagrama de secuencia de diseño)

Fuente: [`diagramas/secuencia_diseno.puml`](diagramas/secuencia_diseno.puml). Modela los pasos 10 a 12 del flujo descripto, que es la parte del escenario que cambia por aplicar el patrón: el gestor registra la recepción y la documentación transiciona de `EnBolsinEnviado` a `RecibidaYAceptada` delegando en el objeto estado.

Como referencia, la máquina de estados de Documentación en la que se basa la jerarquía State está en [`diagramas/maquina_estados_documentacion.puml`](diagramas/maquina_estados_documentacion.puml).

> Para exportar los diagramas a imagen: extensión *PlantUML* de VS Code (Alt+D para previsualizar y luego *Export*), o pegar el código en https://www.plantuml.com/plantuml.

---

## 4. Detalles de implementación

| Aspecto | Elección |
|---|---|
| Lenguaje | Python 3.13 |
| Framework | Flask 3 (web, patrón MVC: rutas y plantillas Jinja2) |
| Tecnología | Web (RNF 1) |
| Base de datos | SQLite (archivo `bolsines.db`) |
| Persistencia | SQLAlchemy 2 (ORM, mapeo declarativo) |

### Correspondencia modelo ↔ código

| Modelo | Código |
|---|---|
| Boundary `PantallaRecepcionBolsin` | `pantalla/pantallaRecepcionBolsin.py` + plantillas `pantalla/templates/recepcion_*.html` |
| Control `GestorRecepcionBolsin` | `gestor/gestorRecepcionBolsin.py` |
| Boundary `InterfazNotificacion` (CU 29) | `interfaz/interfazNotificacion.py` |
| Entidades | `dominio/*.py` |
| Patrón State | `dominio/estadoDocumentacion.py` (contexto en `dominio/documentacion.py`) |

### Persistencia del patrón State

Los objetos estado no tienen atributos propios, así que se persisten por su **nombre**. Un `TypeDecorator` de SQLAlchemy (`EstadoDocumentacionType`) guarda el nombre del estado en la columna y, al leer, reconstruye la instancia del estado concreto que corresponde. Gracias a eso, `Documentacion.estado` y `CambioEstadoDocumentacion.estado` siempre son objetos `EstadoDocumentacion` con comportamiento, nunca cadenas de texto.

### Flujos implementados

| Flujo | Cómo probarlo |
|---|---|
| Flujo descripto (opción 1: contenido igual) | `eb.cordoba` → cualquier bolsín → opción 1 → Confirmar |
| A1 Precinto no encontrado | Filtrar por un precinto inexistente |
| A2 CM de origen sin bolsines | Filtro por CM de origen |
| A3 Documentación no recibida | Opción 2 y marcar los documentos faltantes → doc. *No recibida*, remito *Recibido y aceptado parcial* |
| A4 Documentación que no corresponde | Opción 3 y marcar documentos → *Recibida y rechazada* |
| A5 Redirigir a otra área | Con `eb.cmc`, opción 4, marcar e indicar área → *Para redirigir* (en otra CM la opción aparece deshabilitada) |
| A6 No confirma | En la confirmación, *Volver y cambiar opción* |
| Obs. 1 Cancelar | Botón *Cancelar recepción* en cualquier paso |
| CU 29 (include) | Al confirmar se envía un mail a cada CM de origen (simulado en `notificaciones/notificaciones.log` y visible en la pantalla de resultado) |

---

## 5. Diseño de interfaz (patrones de GUI aplicados)

- **Wizard / asistente por pasos** con indicador de progreso: Seleccionar bolsín → Controlar contenido → Confirmar → Resultado.
- **Búsqueda con filtros** por número de precinto y CM de origen. Los resultados vacíos muestran mensajes específicos (A1 y A2).
- **Tarjetas** para el listado de bolsines, con el precinto destacado porque es el dato que el EB lee del bolsín físico.
- **Divulgación progresiva:** las casillas para marcar documentación y el campo de área sólo aparecen cuando la opción elegida los necesita.
- **Prevención de errores:** la opción *redirigir* aparece deshabilitada fuera de la CMC y hay validaciones con mensajes junto al formulario.
- **Confirmación con vista previa:** antes de guardar se muestra el estado en que quedará cada documento.
- **Feedback del sistema:** la pantalla de resultado muestra los nuevos estados y las notificaciones enviadas.
- **Salida de emergencia:** *Cancelar recepción* en todos los pasos, con confirmación.
- Diseño *responsive*, foco visible para teclado y estados con color y texto.

> El MoodBoard, el mapa de empatía y el user journey se hicieron en clase. Conviene relacionar estas decisiones con lo que surgió ahí; por ejemplo, el precinto destacado y la confirmación previa responden a la necesidad del EB de controlar rápido y sin errores.
