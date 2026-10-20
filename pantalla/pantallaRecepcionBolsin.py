"""Boundary del CU 28 Registrar recepción de bolsín."""
import uuid

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from dominio.estadoDocumentacion import TransicionNoPermitidaError
from gestor.gestorRecepcionBolsin import OPCION_CONTENIDO_IGUAL, GestorRecepcionBolsin
from interfaz.interfazNotificacion import InterfazNotificacion
from pantalla.app import login_requerido
from persistencia.base import SessionLocal

bp = Blueprint("recepcion", __name__, url_prefix="/recepcion-bolsin")

# Un gestor por ejecución del caso de uso (vive entre requests HTTP).
_gestores: dict[str, GestorRecepcionBolsin] = {}


class PantallaRecepcionBolsin:
    # ---------------------------------------------------------------- auxiliares
    def _gestor(self):
        return _gestores.get(session.get("cu28_id"))

    def _finalizar_gestor(self):
        gestor = _gestores.pop(session.pop("cu28_id", None), None)
        if gestor:
            gestor.fin_cu()

    def _sin_gestor(self):
        flash("La operación expiró. Vuelva a iniciar la recepción.", "error")
        return redirect(url_for("inicio"))

    # -------------------------------------------------------------- paso 1
    def opcion_registrar_recepcion_bolsin(self):
        self._finalizar_gestor()
        gestor = GestorRecepcionBolsin(SessionLocal(), session["sesion_id"], InterfazNotificacion())
        gestor.nueva_recepcion_bolsin()
        session["cu28_id"] = uuid.uuid4().hex
        _gestores[session["cu28_id"]] = gestor
        return redirect(url_for("recepcion.mostrar_bolsines"))

    # -------------------------------------------------------------- pasos 2 a 4
    def mostrar_bolsines(self):
        gestor = self._gestor()
        if gestor is None:
            return self._sin_gestor()
        precinto = request.args.get("precinto", "").strip()
        cm_origen = request.args.get("cm_origen", type=int)
        bolsines = gestor.obtener_datos_bolsines(precinto, cm_origen)
        return render_template(
            "recepcion_bolsines.html",
            cm=gestor.cm_usuario_logueado.get_nombre(),
            hay_enviados=gestor.hay_bolsines_enviados(),
            bolsines=bolsines,
            cms_origen=gestor.obtener_cms_origen(),
            filtro_precinto=precinto,
            filtro_cm=cm_origen,
        )

    # -------------------------------------------------------------- paso 5
    def tomar_seleccion_bolsin(self):
        gestor = self._gestor()
        if gestor is None:
            return self._sin_gestor()
        try:
            gestor.tomar_seleccion_bolsin(request.form.get("bolsin_id", type=int))
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("recepcion.mostrar_bolsines"))
        return redirect(url_for("recepcion.mostrar_contenido"))

    # -------------------------------------------------------------- pasos 6 a 8
    def mostrar_contenido(self, errores=(), opcion=None, marcados=(), areas=None):
        gestor = self._gestor()
        if gestor is None or gestor.bolsin_seleccionado is None:
            return self._sin_gestor()
        return render_template(
            "recepcion_contenido.html",
            cm=gestor.cm_usuario_logueado.get_nombre(),
            bolsin=gestor.obtener_datos_bolsin_seleccionado(),
            remitos=gestor.buscar_remitos_y_documentacion(),
            opciones=gestor.obtener_opciones_recepcion(),
            errores=errores,
            opcion_elegida=opcion or gestor.opcion_recepcion,
            marcados=set(marcados),
            areas=areas or {},
        )

    def tomar_opcion_recepcion(self):
        gestor = self._gestor()
        if gestor is None or gestor.bolsin_seleccionado is None:
            return self._sin_gestor()
        opcion = request.form.get("opcion", type=int)
        marcados = [int(d) for d in request.form.getlist("docs")]
        areas = {int(clave[5:]): valor for clave, valor in request.form.items()
                 if clave.startswith("area_") and clave[5:].isdigit()}
        if opcion == OPCION_CONTENIDO_IGUAL:
            marcados = []
        errores = gestor.tomar_opcion_recepcion(opcion, marcados, areas)
        if errores:
            return self.mostrar_contenido(errores, opcion, marcados, areas)
        return redirect(url_for("recepcion.solicitar_confirmacion"))

    # -------------------------------------------------------------- pasos 9 y 10
    def solicitar_confirmacion(self):
        gestor = self._gestor()
        if gestor is None or gestor.opcion_recepcion is None:
            return self._sin_gestor()
        return render_template("recepcion_confirmar.html", resumen=gestor.obtener_resumen_confirmacion())

    def tomar_confirmacion(self):
        gestor = self._gestor()
        if gestor is None or gestor.opcion_recepcion is None:
            return self._sin_gestor()
        if request.form.get("confirma") != "si":
            gestor.tomar_confirmacion(False)
            flash("No se registró la recepción. Puede elegir nuevamente la opción.", "info")
            return redirect(url_for("recepcion.mostrar_contenido"))
        try:
            resultado = gestor.tomar_confirmacion(True)
        except TransicionNoPermitidaError as error:
            flash(f"No se pudo registrar la recepción: {error}", "error")
            self._finalizar_gestor()
            return redirect(url_for("inicio"))
        self._finalizar_gestor()
        return render_template("recepcion_resultado.html", resultado=resultado)

    # -------------------------------------------------------------- Obs. 1
    def cancelar(self):
        self._finalizar_gestor()
        flash("Se canceló el registro de recepción de bolsín.", "info")
        return redirect(url_for("inicio"))


pantalla = PantallaRecepcionBolsin()
bp.add_url_rule("/", "opcion_registrar_recepcion_bolsin",
                login_requerido(pantalla.opcion_registrar_recepcion_bolsin))
bp.add_url_rule("/bolsines", "mostrar_bolsines", login_requerido(pantalla.mostrar_bolsines))
bp.add_url_rule("/bolsines", "tomar_seleccion_bolsin",
                login_requerido(pantalla.tomar_seleccion_bolsin), methods=["POST"])
bp.add_url_rule("/contenido", "mostrar_contenido", login_requerido(pantalla.mostrar_contenido))
bp.add_url_rule("/contenido", "tomar_opcion_recepcion",
                login_requerido(pantalla.tomar_opcion_recepcion), methods=["POST"])
bp.add_url_rule("/confirmar", "solicitar_confirmacion", login_requerido(pantalla.solicitar_confirmacion))
bp.add_url_rule("/confirmar", "tomar_confirmacion",
                login_requerido(pantalla.tomar_confirmacion), methods=["POST"])
bp.add_url_rule("/cancelar", "cancelar", login_requerido(pantalla.cancelar), methods=["POST"])
