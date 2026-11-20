"""Control del CU 28 Registrar recepción de bolsín."""
from datetime import datetime

from sqlalchemy import select

from dominio import Bolsin, Estado, Sesion
from dominio.estadoDocumentacion import TransicionNoPermitidaError
from dominio.situacionRecepcion import SituacionRecepcion

OPCION_CONTENIDO_IGUAL = 1
OPCION_DOC_NO_RECIBIDA = 2
OPCION_DOC_NO_CORRESPONDE = 3
OPCION_DOC_REDIRIGIR = 4

OPCIONES_RECEPCION = {
    OPCION_CONTENIDO_IGUAL: "El contenido del bolsín es igual al registrado",
    OPCION_DOC_NO_RECIBIDA: "No se recibe toda la documentación asociada a los remitos que contiene el bolsín",
    OPCION_DOC_NO_CORRESPONDE: "Existe documentación que no corresponde al destino",
    OPCION_DOC_REDIRIGIR: "La documentación se debe redirigir a otra área",
}

SITUACION_POR_OPCION = {
    OPCION_DOC_NO_RECIBIDA: SituacionRecepcion.NO_RECIBIDA,
    OPCION_DOC_NO_CORRESPONDE: SituacionRecepcion.RECHAZADA,
    OPCION_DOC_REDIRIGIR: SituacionRecepcion.REDIRIGIR,
}


class GestorRegRecepBolsin:
    def __init__(self, db, sesion_id, interfaz_notificacion):
        self.db = db
        self.sesion_actual = db.get(Sesion, sesion_id)
        self.interfaz_notificacion = interfaz_notificacion
        self.empleado_logueado = None
        self.cm_usuario_logueado = None
        self.bolsines_enviados = []
        self.bolsin_seleccionado = None
        self.opcion_recepcion = None
        self.situaciones = {}
        self.areas = {}
        self.fecha_hora_actual = None
        self.estado_recibido = None
        self.estado_rem_aceptado = None
        self.estado_rem_parcial = None
        self.notificaciones_enviadas = []

    # ------------------------------------------------------------- pasos 1 a 4
    def nueva_recepcion_bolsin(self):
        self.buscar_cm_usuario_logueado()
        self.buscar_bolsines_enviados()

    def buscar_cm_usuario_logueado(self):
        self.empleado_logueado = self.sesion_actual.obtener_empleado()
        self.cm_usuario_logueado = self.empleado_logueado.get_cm()
        return self.cm_usuario_logueado.get_nombre()

    def buscar_bolsines_enviados(self):
        bolsines = self.db.scalars(select(Bolsin)).all()
        self.bolsines_enviados = sorted(
            (b for b in bolsines
             if b.es_tu_cm_destino(self.cm_usuario_logueado) and b.esta_enviado()),
            key=lambda b: b.get_numero_bolsin(),
        )
        return self.bolsines_enviados

    def hay_bolsines_enviados(self):
        return len(self.bolsines_enviados) > 0

    def obtener_datos_bolsines(self, nro_precinto="", cm_origen_id=None):
        """Datos a mostrar de cada bolsín, aplicando los filtros opcionales (A1 / A2)."""
        nro_precinto = (nro_precinto or "").strip().lower()
        datos = []
        for bolsin in self.bolsines_enviados:
            cm_origen = bolsin.get_cm_origen()
            if nro_precinto and nro_precinto not in bolsin.get_nro_precinto().lower():
                continue
            if cm_origen_id and cm_origen.id != cm_origen_id:
                continue
            datos.append({
                "id": bolsin.id,
                "numero": bolsin.get_numero_bolsin(),
                "precinto": bolsin.get_nro_precinto(),
                "cm_origen": cm_origen.get_nombre(),
                "fecha": bolsin.get_fecha(),
                "cantidad_remitos": len(bolsin.obtener_remitos()),
            })
        return datos

    def obtener_cms_origen(self):
        cms = {b.get_cm_origen().id: b.get_cm_origen().get_nombre() for b in self.bolsines_enviados}
        return sorted(cms.items(), key=lambda item: item[1])

    # ------------------------------------------------------------- pasos 5 a 7
    def tomar_seleccion_bolsin(self, bolsin_id):
        seleccionado = next((b for b in self.bolsines_enviados if b.id == bolsin_id), None)
        if seleccionado is None:
            raise ValueError("El bolsín seleccionado no está disponible para recepción.")
        self.bolsin_seleccionado = seleccionado
        self._limpiar_opcion()

    def obtener_datos_bolsin_seleccionado(self):
        bolsin = self.bolsin_seleccionado
        return {
            "numero": bolsin.get_numero_bolsin(),
            "precinto": bolsin.get_nro_precinto(),
            "cm_origen": bolsin.get_cm_origen().get_nombre(),
            "fecha": bolsin.get_fecha(),
        }

    def buscar_remitos_y_documentacion(self):
        datos = []
        for remito in self.bolsin_seleccionado.obtener_remitos():
            documentacion = [{
                "id": doc.id,
                "numero": doc.get_numero(),
                "asunto": doc.get_asunto(),
                "tipo": doc.mostrar_tipo_documentacion(),
                "situacion": self.situaciones.get(doc.id),
                "area": self.areas.get(doc.id, ""),
            } for doc in remito.buscar_documentacion()]
            datos.append({"numero": remito.get_numero(), "documentacion": documentacion})
        return datos

    def obtener_opciones_recepcion(self):
        es_cmc = self.cm_usuario_logueado.es_central()
        return [{
            "numero": numero,
            "descripcion": descripcion,
            "habilitada": numero != OPCION_DOC_REDIRIGIR or es_cmc,
        } for numero, descripcion in OPCIONES_RECEPCION.items()]

    # ------------------------------------------------------------- pasos 8 y 9
    def tomar_opcion_recepcion(self, opcion, docs_seleccionados=(), areas=None):
        """Valida la opción elegida y arma la situación de cada documentación.

        Devuelve la lista de errores de validación (vacía si es correcta)."""
        areas = areas or {}
        docs_del_bolsin = {doc.id for remito in self.bolsin_seleccionado.obtener_remitos()
                           for doc in remito.buscar_documentacion()}
        docs_seleccionados = {d for d in docs_seleccionados if d in docs_del_bolsin}

        if opcion not in OPCIONES_RECEPCION:
            return ["Seleccione una opción de recepción."]
        if opcion == OPCION_DOC_REDIRIGIR and not self.cm_usuario_logueado.es_central():
            return ["Sólo la Comisión Médica Central puede redirigir documentación a un área."]

        errores = []
        if opcion != OPCION_CONTENIDO_IGUAL and not docs_seleccionados:
            errores.append("Marque la documentación afectada por la opción seleccionada.")
        if opcion == OPCION_DOC_REDIRIGIR:
            sin_area = [d for d in docs_seleccionados if not areas.get(d, "").strip()]
            if sin_area:
                errores.append("Indique el área de destino de cada documentación a redirigir.")
        if errores:
            return errores

        self.opcion_recepcion = opcion
        self.situaciones = {doc_id: SituacionRecepcion.ACEPTADA for doc_id in docs_del_bolsin}
        self.areas = {}
        for doc_id in docs_seleccionados:
            self.situaciones[doc_id] = SITUACION_POR_OPCION[opcion]
            if opcion == OPCION_DOC_REDIRIGIR:
                self.areas[doc_id] = areas[doc_id].strip()
        return []

    def obtener_resumen_confirmacion(self):
        return {
            "bolsin": self.obtener_datos_bolsin_seleccionado(),
            "opcion": OPCIONES_RECEPCION[self.opcion_recepcion],
            "remitos": self.buscar_remitos_y_documentacion(),
            "responsable": self.empleado_logueado.get_nombre_completo(),
        }

    # ----------------------------------------------------------- pasos 10 a 12
    def tomar_confirmacion(self, confirma):
        if not confirma:  # A6: el EB no confirma, vuelve a elegir la opción
            self._limpiar_opcion()
            return None
        self.fecha_hora_actual = self.obtener_fecha_hora_actual()
        estados = self.db.scalars(select(Estado)).all()
        self.estado_recibido = self.buscar_estado_recibido_en_cm_destino(estados)
        self.estado_rem_aceptado = self.buscar_estado_recibido_y_aceptado_remito(estados)
        self.estado_rem_parcial = self.buscar_estado_recibido_y_aceptado_parcial_remito(estados)
        try:
            self.set_bolsin_estado_recibido()
            self.db.commit()
        except TransicionNoPermitidaError:
            self.db.rollback()
            raise
        self.notificar_recepcion()
        return self.obtener_resultado()

    def buscar_estado_recibido_en_cm_destino(self, estados):
        for estado in estados:
            if estado.es_ambito_bolsin() and estado.es_recibido_en_cm_destino():
                return estado
        return None

    def buscar_estado_recibido_y_aceptado_remito(self, estados):
        for estado in estados:
            if estado.es_ambito_remito() and estado.es_recibido_y_aceptado():
                return estado
        return None

    def buscar_estado_recibido_y_aceptado_parcial_remito(self, estados):
        for estado in estados:
            if estado.es_ambito_remito() and estado.es_recibido_y_aceptado_parcial():
                return estado
        return None

    def set_bolsin_estado_recibido(self):
        self.bolsin_seleccionado.recibir_bolsin(
            self.estado_recibido, self.situaciones, self.areas, self.fecha_hora_actual,
            self.empleado_logueado, self.estado_rem_aceptado, self.estado_rem_parcial,
        )

    def notificar_recepcion(self):
        """Incluye al CU 29: un mail a cada CM de origen de la documentación recibida."""
        docs_por_cm = {}
        for remito in self.bolsin_seleccionado.obtener_remitos():
            for detalle in remito.get_detalles_remito():
                doc = detalle.get_documentacion()
                docs_por_cm.setdefault(doc.get_cm_origen(), []).append((remito, detalle, doc))

        bolsin = self.bolsin_seleccionado
        self.notificaciones_enviadas = []
        for cm_origen, items in docs_por_cm.items():
            lineas = [
                f"Bolsín N° {bolsin.get_numero_bolsin()} (precinto {bolsin.get_nro_precinto()}) "
                f"recibido en {self.cm_usuario_logueado.get_nombre()} "
                f"el {self.fecha_hora_actual:%d/%m/%Y %H:%M}.",
                f"Responsable: {self.empleado_logueado.get_nombre_completo()}",
                "",
                "Situación de la documentación:",
            ]
            for remito, detalle, doc in items:
                area = f" -> área {detalle.get_area_cmc_destino()}" if detalle.get_area_cmc_destino() else ""
                lineas.append(f"  - Remito {remito.get_numero()} | Doc. N° {doc.get_numero()} "
                              f"({doc.mostrar_tipo_documentacion()}): {doc.get_asunto()} "
                              f"=> {doc.get_estado().get_nombre()}{area}")
            self.notificaciones_enviadas.append(self.interfaz_notificacion.enviar_notificacion(
                cm_origen.get_email(),
                f"Recepción del bolsín N° {bolsin.get_numero_bolsin()}",
                "\n".join(lineas),
            ))

    def obtener_resultado(self):
        bolsin = self.bolsin_seleccionado
        return {
            "bolsin": self.obtener_datos_bolsin_seleccionado(),
            "estado_bolsin": bolsin.obtener_estado_actual().get_nombre(),
            "fecha_hora": self.fecha_hora_actual,
            "remitos": [{
                "numero": remito.get_numero(),
                "estado": remito.get_estado().get_nombre(),
                "documentacion": [{
                    "numero": doc.get_numero(),
                    "asunto": doc.get_asunto(),
                    "estado": doc.get_estado().get_nombre(),
                } for doc in remito.buscar_documentacion()],
            } for remito in bolsin.obtener_remitos()],
            "notificaciones": self.notificaciones_enviadas,
        }

    # ------------------------------------------------------------- auxiliares
    def obtener_fecha_hora_actual(self):
        return datetime.now()

    def fin_cu(self):
        self.db.close()

    def _limpiar_opcion(self):
        self.opcion_recepcion = None
        self.situaciones = {}
        self.areas = {}
