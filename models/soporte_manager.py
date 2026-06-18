from models.models import db

class SoporteManager:
    @staticmethod
    def procesar_soporte(datos):
        """
        Procesa el formulario de soporte.
        """
        nombre = datos.get('nombre', '').strip()
        email = datos.get('email', '').strip()
        mensaje = datos.get('mensaje', '').strip()

        # Validación básica
        if not nombre or not email or not mensaje:
            return {'tipo': 'error', 'mensaje': 'Por favor, completa todos los campos.'}

        try:
            # Aquí tienes la estructura lista para cuando decidas guardar en DB:
            # nuevo_ticket = TicketSoporte(nombre=nombre, email=email, mensaje=mensaje)
            # db.session.add(nuevo_ticket)
            # db.session.commit()
            
            print(f"Soporte recibido de {nombre} ({email}): {mensaje}")
            
            return {
                'tipo': 'success', 
                'mensaje': f'¡Gracias, {nombre}! Tu solicitud de soporte ha sido enviada.'
            }
            
        except Exception as e:
            # db.session.rollback() # Si usas DB, esto es vital
            print(f"Error al procesar soporte: {e}")
            return {'tipo': 'error', 'mensaje': 'Error al procesar tu solicitud. Intenta más tarde.'}