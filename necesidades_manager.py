from database import get_db_connection
from psycopg2.extras import RealDictCursor

class NecesidadesManager:
    @staticmethod
    def crear_necesidad(fundacion_id, titulo, descripcion, monto_objetivo):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO necesidades (fundacion_id, titulo, descripcion, monto_objetivo) VALUES (%s, %s, %s, %s)",
                (fundacion_id, titulo, descripcion, monto_objetivo)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creando necesidad: {e}")
            return False
        finally:
            cur.close()
            conn.close()

    # Dentro de necesidades_manager.py
    @staticmethod
    def obtener_necesidades_activas():
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # La consulta filtrada va AQUÍ dentro del Manager
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
    
    # Agregar a necesidades_manager.py
    @staticmethod
    def obtener_donaciones_por_fundacion(fundacion_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Asumiendo que tienes una tabla donaciones que se vincula a necesidades
        cur.execute("""
            SELECT d.*, n.titulo as titulo_necesidad 
            FROM donaciones d 
            JOIN necesidades n ON d.necesidad_id = n.id 
            WHERE n.fundacion_id = %s 
            ORDER BY d.created_at DESC
        """, (fundacion_id,))
        donaciones = cur.fetchall()
        cur.close()
        conn.close()
        return donaciones
    
    
    @staticmethod
    def crear_necesidad(fundacion_id, titulo, descripcion, cantidad_requerida, categoria, fecha_limite, detalles_dict):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Guardamos los detalles específicos (alimentos/ropa/otros) como JSON
            detalles_json = json.dumps(detalles_dict)
            
            cur.execute("""
                INSERT INTO necesidades 
                (fundacion_id, titulo, descripcion, cantidad_requerida, categoria, fecha_limite, detalles_json) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (fundacion_id, titulo, descripcion, cantidad_requerida, categoria, fecha_limite, detalles_json))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creando necesidad física: {e}")
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def registrar_donacion_fisica(necesidad_id, donante_id, fundacion_id, articulo, cantidad):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # 1. Verificar disponibilidad y bloquear la fila (FOR UPDATE) 
            # Esto evita que dos personas donen lo mismo al mismo tiempo
            cur.execute("""
                SELECT cantidad_requerida, cantidad_comprometida 
                FROM necesidades 
                WHERE id = %s AND estado = 'activa' 
                FOR UPDATE
            """, (necesidad_id,))
            
            nec = cur.fetchone()
            if not nec:
                return False # La necesidad no existe o ya no está activa
            
            req, comp = nec
            if (comp + cantidad) > req:
                return False # Intentaron donar más de lo que hace falta

            # 2. Registrar la trazabilidad
            cur.execute("""
                INSERT INTO donaciones_fisicas (necesidad_id, donante_id, fundacion_id, articulo, cantidad_comprometida)
                VALUES (%s, %s, %s, %s, %s)
            """, (necesidad_id, donante_id, fundacion_id, articulo, cantidad))
            
            # 3. Actualizar la cantidad comprometida
            cur.execute("""
                UPDATE necesidades 
                SET cantidad_comprometida = cantidad_comprometida + %s 
                WHERE id = %s
            """, (cantidad, necesidad_id))
            
            # 4. Cierre automático si se alcanza la meta
            cur.execute("""
                UPDATE necesidades 
                SET estado = 'finalizada' 
                WHERE id = %s AND cantidad_comprometida >= cantidad_requerida
            """, (necesidad_id,))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error crítico en transaccion de donacion: {e}")
            return False
        finally:
            cur.close()
            conn.close()
            
        # En necesidades_manager.py
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