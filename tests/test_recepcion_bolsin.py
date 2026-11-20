import tempfile
import unittest
from datetime import datetime

from persistencia.base import SessionLocal, configurar_bd, reiniciar_bd
from persistencia.datosPrueba import cargar_datos_prueba

configurar_bd("sqlite://")

from dominio import Bolsin, Documentacion, Sesion, Usuario  # noqa: E402
from dominio.estadoDocumentacion import (EnBolsinEnviado, NoRecibida, ParaRedirigir,  # noqa: E402
                                         RecibidaYAceptada, RecibidaYRechazada, Registrada,
                                         TransicionNoPermitidaError)
from gestor.gestorRecepcionBolsin import GestorRegRecepBolsin  # noqa: E402
from interfaz.interfazNotificacion import InterfazNotificacion  # noqa: E402
from pantalla.app import create_app  # noqa: E402


class BaseRecepcion(unittest.TestCase):
    def setUp(self):
        reiniciar_bd()
        cargar_datos_prueba()
        self.carpeta_mails = tempfile.mkdtemp()

    def crear_gestor(self, usuario):
        with SessionLocal() as db:
            u = db.query(Usuario).filter_by(nombre=usuario).one()
            sesion = Sesion(usuario=u, fecha_hora_inicio=datetime.now())
            db.add(sesion)
            db.commit()
            sesion_id = sesion.id
        gestor = GestorRegRecepBolsin(SessionLocal(), sesion_id, InterfazNotificacion(self.carpeta_mails))
        gestor.nueva_recepcion_bolsin()
        return gestor

    def docs_del_bolsin(self, gestor):
        return [d["id"] for r in gestor.buscar_remitos_y_documentacion() for d in r["documentacion"]]

    def estado_doc(self, doc_id):
        with SessionLocal() as db:
            return db.get(Documentacion, doc_id).get_estado()


class TestPatronState(BaseRecepcion):
    def test_transiciones_validas_e_historial(self):
        with SessionLocal() as db:
            doc = db.query(Documentacion).first()
            self.assertEqual(doc.get_estado(), EnBolsinEnviado())
            self.assertEqual(len(doc.get_cambios_estado()), 4)
            doc.asignar_no_recibida(datetime.now(), None)
            doc.reasignar(datetime.now(), None)
            self.assertEqual(doc.get_estado(), Registrada())
            actuales = [ce for ce in doc.get_cambios_estado() if ce.sos_actual()]
            self.assertEqual(len(actuales), 1)
            self.assertEqual(actuales[0].get_estado(), Registrada())

    def test_transicion_no_permitida(self):
        with SessionLocal() as db:
            doc = db.query(Documentacion).first()
            with self.assertRaises(TransicionNoPermitidaError):
                doc.incluir_en_remito(datetime.now(), None)


class TestGestorRecepcion(BaseRecepcion):
    def test_flujo_principal_contenido_igual(self):
        gestor = self.crear_gestor("eb.cordoba")
        self.assertEqual(len(gestor.bolsines_enviados), 3)
        gestor.tomar_seleccion_bolsin(gestor.bolsines_enviados[0].id)
        docs = self.docs_del_bolsin(gestor)
        self.assertEqual(gestor.tomar_opcion_recepcion(1), [])
        resultado = gestor.tomar_confirmacion(True)

        self.assertEqual(resultado["estado_bolsin"], "Recibido en CM destino")
        self.assertTrue(all(r["estado"] == "Recibido y aceptado" for r in resultado["remitos"]))
        for doc_id in docs:
            self.assertEqual(self.estado_doc(doc_id), RecibidaYAceptada())
        self.assertEqual(len(resultado["notificaciones"]), 1)
        with SessionLocal() as db:
            self.assertFalse(db.get(Bolsin, gestor.bolsin_seleccionado.id).esta_enviado())

    def test_a3_documentacion_no_recibida(self):
        gestor = self.crear_gestor("eb.cordoba")
        gestor.tomar_seleccion_bolsin(gestor.bolsines_enviados[0].id)
        faltante = self.docs_del_bolsin(gestor)[0]
        self.assertEqual(gestor.tomar_opcion_recepcion(2, [faltante]), [])
        resultado = gestor.tomar_confirmacion(True)
        self.assertEqual(self.estado_doc(faltante), NoRecibida())
        self.assertEqual(resultado["remitos"][0]["estado"], "Recibido y aceptado parcial")
        self.assertEqual(resultado["remitos"][1]["estado"], "Recibido y aceptado")

    def test_a4_documentacion_no_corresponde(self):
        gestor = self.crear_gestor("eb.cordoba")
        gestor.tomar_seleccion_bolsin(gestor.bolsines_enviados[1].id)
        rechazada = self.docs_del_bolsin(gestor)[1]
        self.assertEqual(gestor.tomar_opcion_recepcion(3, [rechazada]), [])
        gestor.tomar_confirmacion(True)
        self.assertEqual(self.estado_doc(rechazada), RecibidaYRechazada())

    def test_a5_redirigir_solo_cmc(self):
        gestor = self.crear_gestor("eb.cordoba")
        gestor.tomar_seleccion_bolsin(gestor.bolsines_enviados[0].id)
        doc = self.docs_del_bolsin(gestor)[0]
        self.assertTrue(gestor.tomar_opcion_recepcion(4, [doc], {doc: "Legales"}))

        gestor = self.crear_gestor("eb.cmc")
        gestor.tomar_seleccion_bolsin(gestor.bolsines_enviados[0].id)
        doc = self.docs_del_bolsin(gestor)[0]
        self.assertTrue(gestor.tomar_opcion_recepcion(4, [doc], {}))  # falta el área
        self.assertEqual(gestor.tomar_opcion_recepcion(4, [doc], {doc: "Asuntos Legales"}), [])
        resultado = gestor.tomar_confirmacion(True)
        self.assertEqual(self.estado_doc(doc), ParaRedirigir())
        self.assertEqual(resultado["remitos"][0]["estado"], "Recibido y aceptado")

    def test_a6_no_confirma(self):
        gestor = self.crear_gestor("eb.cordoba")
        gestor.tomar_seleccion_bolsin(gestor.bolsines_enviados[0].id)
        docs = self.docs_del_bolsin(gestor)
        gestor.tomar_opcion_recepcion(1)
        self.assertIsNone(gestor.tomar_confirmacion(False))
        self.assertIsNone(gestor.opcion_recepcion)
        self.assertEqual(self.estado_doc(docs[0]), EnBolsinEnviado())

    def test_cm_sin_bolsines_enviados(self):
        gestor = self.crear_gestor("eb.parana")
        self.assertFalse(gestor.hay_bolsines_enviados())

    def test_a1_a2_filtros(self):
        gestor = self.crear_gestor("eb.cordoba")
        self.assertEqual(len(gestor.obtener_datos_bolsines("PR-50177")), 1)
        self.assertEqual(gestor.obtener_datos_bolsines("NO-EXISTE"), [])
        cm_id = gestor.bolsines_enviados[0].get_cm_origen().id
        self.assertEqual(len(gestor.obtener_datos_bolsines("", cm_id)), 1)


class TestPantalla(BaseRecepcion):
    def test_flujo_web_completo(self):
        cliente = create_app().test_client()
        r = cliente.post("/login", data={"usuario": "eb.cordoba", "contrasenia": "1234"})
        self.assertEqual(r.status_code, 302)
        cliente.get("/recepcion-bolsin/")
        r = cliente.get("/recepcion-bolsin/bolsines")
        self.assertIn("PR-48213", r.get_data(as_text=True))
        r = cliente.get("/recepcion-bolsin/bolsines?precinto=XYZ")
        self.assertIn("No se encuentra bolsín con el número de precinto", r.get_data(as_text=True))
        cliente.post("/recepcion-bolsin/bolsines", data={"bolsin_id": 1})
        r = cliente.post("/recepcion-bolsin/contenido", data={"opcion": 2})
        self.assertIn("Marque la documentación afectada", r.get_data(as_text=True))
        r = cliente.post("/recepcion-bolsin/contenido", data={"opcion": 2, "docs": ["1"]})
        self.assertEqual(r.status_code, 302)
        r = cliente.post("/recepcion-bolsin/confirmar", data={"confirma": "si"})
        texto = r.get_data(as_text=True)
        self.assertIn("Recepción registrada", texto)
        self.assertIn("cm.ros@organismo.gob.ar", texto)
        self.assertEqual(self.estado_doc(1), NoRecibida())


if __name__ == "__main__":
    unittest.main()
