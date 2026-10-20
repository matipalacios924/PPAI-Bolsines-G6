import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from sqlalchemy import select

from dominio import Sesion, Usuario
from persistencia.base import SessionLocal


def login_requerido(vista):
    @wraps(vista)
    def envoltorio(*args, **kwargs):
        if "sesion_id" not in session:
            return redirect(url_for("iniciar_sesion"))
        return vista(*args, **kwargs)
    return envoltorio


def create_app():
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(16)

    from pantalla.pantallaRecepcionBolsin import bp as bp_recepcion
    app.register_blueprint(bp_recepcion)

    @app.template_filter("fecha")
    def formatear_fecha(valor, con_hora=False):
        return valor.strftime("%d/%m/%Y %H:%M" if con_hora else "%d/%m/%Y")

    @app.route("/login", methods=["GET", "POST"])
    def iniciar_sesion():
        if request.method == "POST":
            nombre = request.form.get("usuario", "").strip()
            contrasenia = request.form.get("contrasenia", "")
            with SessionLocal() as db:
                usuario = db.scalar(select(Usuario).where(Usuario.nombre == nombre))
                if usuario is None or not usuario.validar_contrasenia(contrasenia):
                    flash("Usuario o contraseña incorrectos.", "error")
                    return render_template("login.html", usuario=nombre)
                sesion = Sesion(usuario=usuario, fecha_hora_inicio=datetime.now())
                db.add(sesion)
                db.commit()
                empleado = usuario.get_empleado()
                session.clear()
                session["sesion_id"] = sesion.id
                session["empleado"] = empleado.get_nombre_completo()
                session["rol"] = empleado.rol.get_nombre()
                session["cm"] = empleado.get_cm().get_nombre()
            return redirect(url_for("inicio"))
        return render_template("login.html")

    @app.route("/logout")
    def cerrar_sesion():
        if "sesion_id" in session:
            with SessionLocal() as db:
                sesion = db.get(Sesion, session["sesion_id"])
                if sesion:
                    sesion.set_fecha_hora_fin(datetime.now())
                    db.commit()
        session.clear()
        return redirect(url_for("iniciar_sesion"))

    @app.route("/")
    @login_requerido
    def inicio():
        return render_template("inicio.html")

    return app
