import requests
import os

class EmailService:
    API_URL = "https://api.brevo.com/v3/smtp/email"
    API_KEY = os.environ.get("BREVO_API_KEY") # Configura esta variable en Render

    @staticmethod
    def enviar_notificacion(email_destino, nombre_destino, asunto, mensaje):
        headers = {
            "api-key": EmailService.API_KEY,
            "content-type": "application/json"
        }
        payload = {
            "sender": {"name": "Red Solidaria", "email": "tu_correo@dominio.com"},
            "to": [{"email": email_destino, "name": nombre_destino}],
            "subject": asunto,
            "htmlContent": f"<html><body><h3>Hola, {nombre_destino}</h3><p>{mensaje}</p></body></html>"
        }
        try:
            requests.post(EmailService.API_URL, json=payload, headers=headers)
        except Exception as e:
            print(f"Error enviando correo: {e}")