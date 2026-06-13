import json
from datetime import datetime
from database import get_db_connection
from psycopg2.extras import RealDictCursor

class NecesidadesManager:

    @staticmethod
    def crear_necesidad(fundacion_id, titulo, descripcion, cantidad_requerida, categoria, fecha_limite, detalles_dict):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            detalles_json = json.dumps(detalles_dict)
            cur.execute("""
                INSERT INTO necesidades 
                (fundacion_id, titulo, descripcion, cantidad_requerida, categoria, fecha_limite, detalles_json, cantidad_comprometida, estado, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, 0, 'activa', %s)
            """, (fundacion_id, titulo, descripcion, cantidad_requerida, categoria, fecha_limite, detalles_json, datetime.utcnow()))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creando necesidad física: {e}")
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def obtener_necesidades_activas():
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM necesidades 
            WHERE estado = 'activa' 
            AND cantidad_comprometida < cantidad_requerida 
            ORDER BY created_at DESC
        """)
        necesidades = cur.fetchall()
        cur.close()
        conn.close()
        return necesidades

    @staticmethod
    def registrar_donacion_fisica(necesidad_id, donante_id, fundacion_id, articulo, cantidad):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # 1. SEGURIDAD: Evitar que el dueño done a su propia causa
            cur.execute("""
                SELECT f.usuario_id 
                FROM fundaciones f 
                WHERE f.id = %s
            """, (fundacion_id,))
            
            row = cur.fetchone()
            
            # Si encontramos al dueño, verificamos que no sea el mismo donante
            if row and row[0] == donante_id:
                return False, "No puedes realizar una donación a tus propias necesidades."

            # 2. VALIDACIÓN: Verificar necesidad
            cur.execute("SELECT cantidad_requerida, cantidad_comprometida FROM necesidades WHERE id = %s", (necesidad_id,))
            resultado = cur.fetchone()
            
            if not resultado:
                return False, "Error: La necesidad no existe en el sistema."
            
            req, comp = resultado
            pendiente = req - comp
            
            if cantidad > pendiente:
                return False, f"La cantidad excede lo necesario. Solo faltan {pendiente} unidades."

            # 3. Registrar trazabilidad
            cur.execute("""
                INSERT INTO donaciones_fisicas (necesidad_id, donante_id, fundacion_id, articulo, cantidad, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (necesidad_id, donante_id, fundacion_id, articulo, cantidad, datetime.utcnow()))
            
            # 4. Actualizar cantidad comprometida
            cur.execute("""
                UPDATE necesidades 
                SET cantidad_comprometida = cantidad_comprometida + %s 
                WHERE id = %s
            """, (cantidad, necesidad_id))
            
            # 5. Marcar finalizada si se cumplió la meta
            cur.execute("""
                UPDATE necesidades 
                SET estado = 'finalizada' 
                WHERE id = %s AND cantidad_comprometida >= cantidad_requerida
            """, (necesidad_id,))
            
            conn.commit()
            return True, "¡Donación realizada correctamente!"
            
        except Exception as e:
            conn.rollback()
            # Esto imprimirá el error real y la línea donde ocurre
            import traceback
            error_msg = traceback.format_exc()
            print(f"--- ERROR CRÍTICO DETALLADO ---")
            print(error_msg)
            return False, "Error interno. Revisa los logs de Render para detalles."
            
            
    @staticmethod
    def obtener_donaciones_por_fundacion(fundacion_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT d.*, n.titulo as titulo_necesidad 
            FROM donaciones_fisicas d 
            JOIN necesidades n ON d.necesidad_id = n.id 
            WHERE n.fundacion_id = %s 
            ORDER BY d.created_at DESC
        """, (fundacion_id,))
        donaciones = cur.fetchall()
        cur.close()
        conn.close()
        return donaciones

    @staticmethod
    def obtener_mis_donaciones(donante_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT d.*, n.titulo as titulo_necesidad 
            FROM donaciones_fisicas d
            JOIN necesidades n ON d.necesidad_id = n.id
            WHERE d.donante_id = %s
            ORDER BY d.created_at DESC
        """, (donante_id,))
        data = cur.fetchall()
        cur.close()
        conn.close()
        return data