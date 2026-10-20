"""PPAI 2026 - Bolsines - CU 28 Registrar recepción de bolsín.

Uso:
    python main.py            inicia la aplicación web en http://127.0.0.1:5000
    python main.py --reset    borra la base y vuelve a cargar los datos de prueba
"""
import sys

from persistencia.base import RUTA_BD, configurar_bd, reiniciar_bd
from persistencia.datosPrueba import cargar_datos_prueba


def main():
    bd_nueva = not RUTA_BD.exists()
    configurar_bd()
    if "--reset" in sys.argv:
        reiniciar_bd()
        bd_nueva = True
    if bd_nueva:
        cargar_datos_prueba()
        print("Base de datos inicializada con datos de prueba.")

    from pantalla.app import create_app
    create_app().run(debug=True, use_reloader=False, threaded=False)


if __name__ == "__main__":
    main()
