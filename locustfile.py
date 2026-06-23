"""
Pruebas de carga para Red Solidaria con Locust.

ANTES DE CORRER:
1. Reemplaza las credenciales de los 3 usuarios de prueba abajo
   (busca "REEMPLAZAR" en este archivo) con las que ya registraste
   en tu base de datos para donante, fundación y admin.
2. Cambia 'host' si pruebas en local (http://localhost:5001) o en
   Render (tu URL real desplegada).
3. Corre con: locust -f locustfile.py

Cada clase HttpUser representa un ROL distinto del sistema. Locust
reparte usuarios virtuales entre las 3 clases automáticamente. El
peso (weight) controla qué proporción de tráfico simula cada rol.
"""

import random
from locust import HttpUser, task, between


# ── CREDENCIALES DE PRUEBA: REEMPLAZAR con tus usuarios reales ──
DONANTE_EMAIL = "cartuji7@correo.com"      # REEMPLAZAR
DONANTE_PASSWORD = "77777"              # REEMPLAZAR

FUNDACION_EMAIL = "esperenza@gmail.com"  # REEMPLAZAR
FUNDACION_PASSWORD = "00000"            # REEMPLAZAR

ADMIN_EMAIL = "admin@redsolidaria.com"          # REEMPLAZAR
ADMIN_PASSWORD = "admin123"                # REEMPLAZAR


class DonanteUser(HttpUser):
    """
    Simula a un donante navegando el panel, buscando con filtros,
    y ocasionalmente registrando una donación física real.
    """
    host = "https://despliegue-1-1.onrender.com"  # Cambia a tu URL de Render si pruebas en producción
    wait_time = between(1, 3)
    weight = 5  # los donantes son el rol con más tráfico esperado

    def on_start(self):
        """Se ejecuta una sola vez por usuario virtual: hace login."""
        self.client.post("/", data={
            "email": DONANTE_EMAIL,
            "pass": DONANTE_PASSWORD
        })

    @task(5)
    def ver_panel_donante(self):
        self.client.get("/donaciones/panel-donante")

    @task(3)
    def buscar_por_categoria(self):
        self.client.get("/donaciones/panel-donante", params={"categoria": "alimentos"})

    @task(3)
    def buscar_por_estado(self):
        self.client.get("/donaciones/panel-donante", params={"est": "recibida"})

    @task(2)
    def buscar_texto_libre(self):
        self.client.get("/donaciones/panel-donante", params={"q": "kit"})

    @task(2)
    def buscar_causa_social(self):
        self.client.get("/donaciones/panel-donante", params={"categoria": "Causa Social (Monetaria)"})

    @task(1)
    def registrar_donacion_fisica(self):
        """
        Crea un registro REAL en donaciones_fisicas. necesidad_id=1 es
        un placeholder -- ajusta al ID real de una necesidad física
        activa en tu base de datos de pruebas.
        """
        self.client.post("/donaciones/donar/1", data={
            "tipo": "fisico",
            "nombre_producto": "Producto de prueba Locust",
            "cantidad": random.randint(1, 5)
        })


class FundacionUser(HttpUser):
    """
    Simula a una fundación revisando su dashboard, buscando en su
    trazabilidad, y ocasionalmente publicando una nueva necesidad.
    """
    host = "https://despliegue-1-1.onrender.com"
    wait_time = between(1, 3)
    weight = 3

    def on_start(self):
        self.client.post("/", data={
            "email": FUNDACION_EMAIL,
            "pass": FUNDACION_PASSWORD
        })

    @task(5)
    def ver_dashboard(self):
        self.client.get("/fundacion/dashboard-fundacion")

    @task(2)
    def buscar_por_donante(self):
        self.client.get("/fundacion/dashboard-fundacion", params={"donante": "a"})

    @task(2)
    def buscar_por_categoria(self):
        self.client.get("/fundacion/dashboard-fundacion", params={"categoria": "ropa"})

    @task(2)
    def buscar_por_estado(self):
        self.client.get("/fundacion/dashboard-fundacion", params={"est": "pendiente"})

    @task(1)
    def ver_form_publicar_necesidad(self):
        self.client.get("/fundacion/publicar-necesidad")

    @task(1)
    def publicar_necesidad_fisica(self):
        """Crea una Necesidad REAL en la base de datos."""
        self.client.post("/fundacion/publicar-necesidad", data={
            "titulo": "Necesidad de prueba Locust",
            "descripcion": "Generada automaticamente durante pruebas de carga",
            "cantidad_requerida": "50",
            "categoria": "otros"
        })


class AdminUser(HttpUser):
    """
    Simula a un administrador revisando el dashboard y las distintas
    pestañas (donantes, fundaciones, donaciones, pagos, pendientes).
    No incluye tareas que eliminen datos (eliminar_fundacion /
    eliminar_donante), porque borrarían usuarios reales de prueba.
    """
    host = "https://despliegue-1-1.onrender.com"
    wait_time = between(1, 3)
    weight = 1  # normalmente hay muy pocos administradores activos a la vez

    def on_start(self):
        self.client.post("/", data={
            "email": ADMIN_EMAIL,
            "pass": ADMIN_PASSWORD
        })

    @task(5)
    def ver_dashboard_admin(self):
        self.client.get("/admin/dashboard")

    @task(2)
    def ver_tabla_donantes(self):
        self.client.get("/admin/get_donantes")

    @task(2)
    def ver_tabla_fundaciones(self):
        self.client.get("/admin/get_fundaciones")

    @task(2)
    def ver_tabla_donaciones(self):
        self.client.get("/admin/get_donaciones")

    @task(2)
    def ver_tabla_pagos(self):
        self.client.get("/admin/get_pagos")

    @task(1)
    def descargar_reporte_donaciones(self):
        self.client.get("/admin/api/reporte_admin", params={"seccion": "donaciones"})