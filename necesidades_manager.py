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
            # 1. SEGURIDAD: Evitar que el dueño de la fundación done a su propia causa
            # Suponemos que en tu tabla 'fundaciones' tienes un campo 'usuario_id' que es el dueño
            cur.execute("SELECT usuario_id FROM fundaciones WHERE id = %s", (fundacion_id,))
            dueño_fundacion = cur.fetchone()
            
            if dueño_fundacion and dueño_fundacion[0] == donante_id:
                return False, "¡Seguridad! No puedes donar a tus propias causas."

            # 2. Validación: Verificar cuánto queda pendiente
            cur.execute("""
                SELECT cantidad_requerida - cantidad_comprometida as pendiente 
                FROM necesidades WHERE id = %s
            """, (necesidad_id,))
            resultado = cur.fetchone()
            
            if not resultado or cantidad > resultado[0]:
                return False, "La cantidad excede lo necesario o la necesidad no existe."

            # 3. Registrar la trazabilidad
            cur.execute("""
                INSERT INTO donaciones_fisicas (necesidad_id, donante_id, fundacion_id, articulo, cantidad, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (necesidad_id, donante_id, fundacion_id, articulo, cantidad, datetime.utcnow()))
            
            # 4. Actualizar la cantidad comprometida
            cur.execute("""
                UPDATE necesidades 
                SET cantidad_comprometida = cantidad_comprometida + %s 
                WHERE id = %s
            """, (cantidad, necesidad_id))
            
            # 5. Marcar como finalizada si se cumplió la meta
            cur.execute("""
                UPDATE necesidades 
                SET estado = 'finalizada' 
                WHERE id = %s AND cantidad_comprometida >= cantidad_requerida
            """, (necesidad_id,))
            
            conn.commit()
            return True, "Donación realizada correctamente."
        except Exception as e:
            conn.rollback()
            print(f"Error en transacción: {e}")
            return False, "Error interno al procesar la donación."
        finally:
            cur.close()
            conn.close()

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