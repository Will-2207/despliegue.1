

class SoporteManager:
    @staticmethod
    def procesar_soporte(datos):
        """
        Recibe los datos del formulario de soporte.
        Puedes expandir esto para enviar un email o guardar en BD.
        """
        nombre = datos.get('nombre', '').strip()
        email = datos.get('email', '').strip()
        mensaje = datos.get('mensaje', '').strip()

        # Validación básica
        if not nombre or not email or not mensaje:
            return {'tipo': 'error', 'mensaje': 'Por favor, completa todos los campos.'}

        try:
            # Aquí podrías agregar lógica para guardar en la base de datos:
            # conn = get_db_connection()
            # cur = conn.cursor()
            # cur.execute("INSERT INTO tickets_soporte ...")
            # conn.commit()
            
            # Por ahora, simulamos el éxito
            print(f"Soporte recibido de {nombre} ({email}): {mensaje}")
            
            return {
                'tipo': 'success', 
                'mensaje': '¡Gracias, ' + nombre + '! Tu solicitud de soporte ha sido enviada.'
            }
            
        except Exception as e:
            return {'tipo': 'error', 'mensaje': f'Error al procesar soporte: {str(e)}'}
