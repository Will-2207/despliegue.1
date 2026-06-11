import stripe
import os
from database import get_db_connection
from datetime import datetime
from pymongo import MongoClient

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class PaymentManager:
    @staticmethod
    def get_mongo_db():
        # Usa serverSelectionTimeoutMS para que no se quede colgado si Mongo falla
        client = MongoClient(os.getenv('MONGO_URI'), connect=False, serverSelectionTimeoutMS=5000)
        return client['prueba1']

    @staticmethod
    def registrar_transaccion(usuario_id, session_id):
        try:
            # 1. Recuperar info desde Stripe
            stripe_session = stripe.checkout.Session.retrieve(session_id)
            
            if stripe_session.payment_status != 'paid':
                return False

            intent = stripe.PaymentIntent.retrieve(stripe_session.payment_intent)
            method = stripe.PaymentMethod.retrieve(intent.payment_method)
            
            ultimos_cuatro = method.card.last4
            marca = method.card.brand
            monto = intent.amount_received / 100

            # 2. Guardar en PostgreSQL
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO transacciones (usuario_id, monto, metodo_pago, ultimos_cuatro, transaccion_token, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (usuario_id, monto, marca, ultimos_cuatro, session_id, datetime.utcnow()))
            conn.commit()
            cur.close()
            conn.close()

            # 3. Guardar en MongoDB
            db = PaymentManager.get_mongo_db()
            print(f"DEBUG: Intentando insertar en MongoDB: {db.name}")
            
            db.donaciones.insert_one({
                'usuario_id': int(usuario_id),
                'monto': float(monto),
                'metodo': marca,
                'ultimos_cuatro': ultimos_cuatro,
                'fecha': datetime.utcnow()
            })
            print("DEBUG: Inserción en MongoDB exitosa")
            
            return True
        except Exception as e:
            print(f"Error crítico en PaymentManager: {e}")
            return False
