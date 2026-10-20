"""Carga datos de prueba para el CU 28.

Usuarios (contraseña 1234):
  eb.cordoba  -> Encargado de Bolsines de CM Córdoba (3 bolsines enviados hacia ella)
  eb.cmc      -> Encargado de Bolsines de la CMC (habilita la opción "redirigir")
  eb.parana   -> Encargado de Bolsines de CM Paraná (sin bolsines enviados)
"""
from datetime import date, datetime, timedelta

from dominio import (Archivo, Bolsin, ComisionMedica, DetalleRemito, Documentacion, Empleado,
                     Estado, Localidad, Provincia, Remito, Rol, TipoDocumento, Usuario)
from dominio.estado import AMBITO_BOLSIN, AMBITO_REMITO
from persistencia.base import SessionLocal

ESTADOS_BOLSIN = ["Creado", "Cerrado", "Enviado", "Recibido en CM destino", "De baja"]
ESTADOS_REMITO = ["Creado", "En bolsín saliente", "En bolsín enviado", "Recibido y aceptado",
                  "Recibido y aceptado parcial", "Cancelado"]


def cargar_datos_prueba():
    db = SessionLocal()
    estados = {}
    for nombre in ESTADOS_BOLSIN:
        estados[(AMBITO_BOLSIN, nombre)] = Estado(ambito=AMBITO_BOLSIN, nombre=nombre)
    for nombre in ESTADOS_REMITO:
        estados[(AMBITO_REMITO, nombre)] = Estado(ambito=AMBITO_REMITO, nombre=nombre)
    db.add_all(estados.values())

    provincias = {n: Provincia(nombre=n) for n in
                  ["C.A.B.A.", "Córdoba", "Santa Fe", "Mendoza", "Entre Ríos"]}
    localidades = {
        "C.A.B.A.": Localidad(nombre="C.A.B.A.", provincia=provincias["C.A.B.A."]),
        "Córdoba": Localidad(nombre="Córdoba", provincia=provincias["Córdoba"]),
        "Villa María": Localidad(nombre="Villa María", provincia=provincias["Córdoba"]),
        "Rosario": Localidad(nombre="Rosario", provincia=provincias["Santa Fe"]),
        "Mendoza": Localidad(nombre="Mendoza", provincia=provincias["Mendoza"]),
        "Paraná": Localidad(nombre="Paraná", provincia=provincias["Entre Ríos"]),
    }

    def cm(codigo, nombre, localidad, direccion, telefono):
        return ComisionMedica(codigo=codigo, nombre=nombre, localidad=localidades[localidad],
                              direccion=direccion, telefono=telefono,
                              email=f"cm.{codigo.lower()}@organismo.gob.ar")

    cms = {
        "CMC": cm("CMC", "Comisión Médica Central", "C.A.B.A.", "Av. Belgrano 1250", "011-4320-1000"),
        "CBA": cm("CBA", "Comisión Médica Córdoba", "Córdoba", "Bv. San Juan 455", "0351-422-1100"),
        "VMA": cm("VMA", "Comisión Médica Villa María", "Villa María", "Bv. España 210", "0353-452-3300"),
        "ROS": cm("ROS", "Comisión Médica Rosario", "Rosario", "Córdoba 1452", "0341-421-7700"),
        "MZA": cm("MZA", "Comisión Médica Mendoza", "Mendoza", "San Martín 1020", "0261-425-6600"),
        "PRN": cm("PRN", "Comisión Médica Paraná", "Paraná", "Urquiza 780", "0343-431-2200"),
    }
    db.add_all(cms.values())

    rol_eb = Rol(nombre="Encargado de Bolsines")
    rol_ed = Rol(nombre="Encargado de Documentación")
    rol_gcm = Rol(nombre="Gerente de Comisión Médica")

    def empleado(nombre, apellido, rol, codigo_cm):
        return Empleado(nombre=nombre, apellido=apellido, rol=rol, comision_medica=cms[codigo_cm],
                        email=f"{nombre.lower()}.{apellido.lower()}@organismo.gob.ar")

    eb = {
        "CBA": empleado("Lucía", "Ferreyra", rol_eb, "CBA"),
        "CMC": empleado("Martín", "Gómez", rol_eb, "CMC"),
        "PRN": empleado("Sofía", "Benítez", rol_eb, "PRN"),
    }
    ed = {c: empleado(n, a, rol_ed, c) for c, n, a in [
        ("ROS", "Pablo", "Acosta"), ("MZA", "Carla", "Quiroga"), ("CMC", "Diego", "Paz"),
        ("CBA", "Ana", "Molina"), ("VMA", "Jorge", "Sosa")]}
    db.add_all([empleado("Laura", "Vélez", rol_gcm, "CBA")])
    db.add_all([
        Usuario(nombre="eb.cordoba", contrasenia="1234", empleado=eb["CBA"]),
        Usuario(nombre="eb.cmc", contrasenia="1234", empleado=eb["CMC"]),
        Usuario(nombre="eb.parana", contrasenia="1234", empleado=eb["PRN"]),
    ])

    tipos = {n: TipoDocumento(nombre=n, descripcion=d) for n, d in [
        ("Expediente", "Expediente administrativo"), ("Dictamen", "Dictamen médico"),
        ("Estudio médico", "Estudios complementarios"), ("Carta documento", "Comunicación fehaciente")]}

    contador = {"doc": 5000, "remito": 300, "bolsin": 1000}
    inicio = datetime.now() - timedelta(days=3)

    def armar_bolsin(origen, destino, remitos, precinto, peso, enviar=True):
        """remitos: lista de listas de (tipo, asunto)."""
        responsable = ed[origen]
        fh = inicio
        bolsin = Bolsin(numero_bolsin=contador["bolsin"], numero_precinto=precinto, peso=peso,
                        fecha=fh.date(), origen=cms[origen], destino=cms[destino])
        contador["bolsin"] += 1
        bolsin.cambiar_estado(estados[(AMBITO_BOLSIN, "Creado")], fh, responsable)
        for docs in remitos:
            remito = Remito(numero=contador["remito"], fecha=fh.date(), origen=cms[origen],
                            destino=cms[destino], estado=estados[(AMBITO_REMITO, "Creado")])
            contador["remito"] += 1
            for tipo, asunto in docs:
                doc = Documentacion(numero=contador["doc"], asunto=asunto, tipo_documento=tipos[tipo],
                                    fecha_pase=date.today(), cm_origen=cms[origen])
                contador["doc"] += 1
                doc.archivos_adjuntos.append(Archivo(nombre_archivo=f"doc_{doc.numero}.pdf",
                                                     titulo_documento=asunto))
                doc.registrar(fh, responsable)
                doc.incluir_en_remito(fh + timedelta(hours=1), responsable)
                remito.tomar_documentacion(DetalleRemito(documentacion=doc))
            bolsin.asociar_remito(remito)
            remito.set_estado(estados[(AMBITO_REMITO, "En bolsín saliente")])
            for doc in remito.buscar_documentacion():
                doc.asignar_a_bolsin(fh + timedelta(hours=2), responsable)
        bolsin.cambiar_estado(estados[(AMBITO_BOLSIN, "Cerrado")], fh + timedelta(hours=3), responsable)
        if enviar:
            fh_envio = fh + timedelta(days=1)
            bolsin.cambiar_estado(estados[(AMBITO_BOLSIN, "Enviado")], fh_envio, responsable)
            for remito in bolsin.obtener_remitos():
                remito.set_estado(estados[(AMBITO_REMITO, "En bolsín enviado")])
                for doc in remito.buscar_documentacion():
                    doc.comenzar_traslado(fh_envio, responsable)
        db.add(bolsin)

    # Hacia CM Córdoba
    armar_bolsin("ROS", "CBA", [
        [("Expediente", "Expediente 1532/26 - Incapacidad laboral"),
         ("Dictamen", "Dictamen médico trabajador Pérez")],
        [("Estudio médico", "Resonancia magnética columna lumbar"),
         ("Carta documento", "Notificación de audiencia")],
    ], "PR-48213", 1250)
    armar_bolsin("MZA", "CBA", [
        [("Expediente", "Expediente 877/26 - Reapertura"),
         ("Estudio médico", "Electromiografía miembros superiores")],
    ], "PR-50177", 640)
    armar_bolsin("CMC", "CBA", [
        [("Dictamen", "Dictamen CMC - Recurso apelación 45/26"),
         ("Expediente", "Expediente 2210/26 - Revisión"),
         ("Carta documento", "Intimación a presentar estudios")],
    ], "PR-51002", 980)
    armar_bolsin("VMA", "CBA", [[("Expediente", "Expediente 120/26 - Aún sin enviar")]],
                 "PR-51888", 300, enviar=False)

    # Hacia la CMC (permite probar "redirigir a otra área")
    armar_bolsin("CBA", "CMC", [
        [("Expediente", "Expediente 3301/26 - Para Asuntos Legales"),
         ("Dictamen", "Dictamen divergencia - Para Auditoría Médica"),
         ("Estudio médico", "Tomografía computada de tórax")],
    ], "PR-52440", 1100)
    armar_bolsin("VMA", "CMC", [
        [("Carta documento", "Carta documento ART La Segunda"),
         ("Expediente", "Expediente 415/26 - Homologación")],
    ], "PR-52519", 720)

    # Hacia CM Rosario (no debe aparecerle a Córdoba)
    armar_bolsin("CBA", "ROS", [[("Dictamen", "Dictamen trabajador Gutiérrez")]], "PR-53001", 410)

    db.commit()
    db.close()
