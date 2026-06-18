import os
import requests

class EmailService:
    API_URL = "https://api.brevo.com/v3/smtp/email"
    API_KEY = os.environ.get("BREVO_API_KEY")
    SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL")
    SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "Red Solidaria")

    @staticmethod
    def enviar_notificacion(email_destino, nombre_destino, asunto, mensaje):
        if not EmailService.API_KEY or not EmailService.SENDER_EMAIL:
            print("Brevo no configurado: faltan BREVO_API_KEY o BREVO_SENDER_EMAIL.")
            return False, "Brevo no configurado."

        headers = {
            "api-key": EmailService.API_KEY,
            "content-type": "application/json"
        }
        payload = {
            "sender": {"name": EmailService.SENDER_NAME, "email": EmailService.SENDER_EMAIL},
            "to": [{"email": email_destino, "name": nombre_destino}],
            "subject": asunto,
            "htmlContent": f"<html><body><h3>Hola, {nombre_destino}</h3><p>{mensaje}</p></body></html>"
        }
        try:
            response = requests.post(
                EmailService.API_URL,
                json=payload,
                headers=headers,
                timeout=10
            )
            if response.status_code >= 400:
                print(f"Brevo respondio con error {response.status_code}: {response.text}")
                return False, "Brevo rechazo el envio."

            return True, "Correo enviado correctamente."
        except Exception as e:
            print(f"Error enviando correo: {e}")
            return False, str(e)
