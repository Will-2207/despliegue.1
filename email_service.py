import os
import requests


class EmailService:
    API_URL = "https://api.brevo.com/v3/smtp/email"
    API_KEY = os.environ.get("MAIL_PASSWORD")
    SENDER_EMAIL = "cartuji7@gmail.com"
    SENDER_NAME = "Red Solidaria"

    @staticmethod
    def enviar_notificacion(email_destino, nombre_destino, asunto, html_content):
        if not EmailService.API_KEY:
            print("Brevo no configurado: falta MAIL_PASSWORD (API key de Brevo).")
            return False, "Brevo no configurado."

        if not email_destino:
            print("No se envio correo: email_destino vacio.")
            return False, "Email de destino vacio."

        headers = {
            "api-key": EmailService.API_KEY,
            "content-type": "application/json"
        }
        payload = {
            "sender": {"name": EmailService.SENDER_NAME, "email": EmailService.SENDER_EMAIL},
            "to": [{"email": email_destino, "name": nombre_destino or "Usuario"}],
            "subject": asunto,
            "htmlContent": html_content
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