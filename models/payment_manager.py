import stripe
import os
from datetime import datetime
from pymongo import MongoClient
from models.models import db, Transaccion # Asegúrate de que este modelo exista en models.py

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class PaymentManager:
    @staticmethod
    def get_mongo_db():
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

            # 2. Guardar en PostgreSQL usando SQLAlchemy
            nueva_transaccion = Transaccion(
                usuario_id=usuario_id,
                monto=monto,
                metodo_pago=marca,
                ultimos_cuatro=ultimos_cuatro,
                transaccion_token=session_id,
                created_at=datetime.utcnow()
            )
            db.session.add(nueva_transaccion)
            db.session.commit()

            # 3. Guardar en MongoDB (esto se mantiene igual)
            db_mongo = PaymentManager.get_mongo_db()
            db_mongo.donaciones.insert_one({
                'usuario_id': int(usuario_id),
                'monto': float(monto),
                'metodo': marca,
                'ultimos_cuatro': ultimos_cuatro,
                'fecha': datetime.utcnow()
            })
            
            return True
        except Exception as e:
            db.session.rollback() # Limpiamos en caso de error en Postgres
            print(f"Error crítico en PaymentManager: {e}")
            return False