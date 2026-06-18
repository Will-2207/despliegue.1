from models.models import db, Usuario, Fundacion, Necesidad, DonacionFisica, DonacionMonetaria
from models.necesidades_manager import NecesidadesManager
from services.auth_service import AuthService


class FundacionService:
    @staticmethod
    def puede_acceder(usuario_id):
        return AuthService.fundacion_activa(usuario_id)

    @staticmethod
    def obtener_dashboard(usuario_id):
        try:
            if not AuthService.fundacion_activa(usuario_id):
                return False, "Tu fundacion aun no esta aprobada para ingresar.", None

            db.session.expire_all()

            usuario = Usuario.query.get(usuario_id)
            fundacion = Fundacion.query.filter_by(usuario_id=usuario_id).first()

            if not usuario or not fundacion:
                return False, "No fue posible encontrar la fundacion.", None

            fisicas = (
                db.session.query(
                    DonacionFisica.created_at,
                    DonacionFisica.cantidad_comprometida.label('monto'),
                    DonacionFisica.articulo.label('titulo_necesidad'),
                    Usuario.nombre.label('nombre_donante'),
                    db.literal('Fisica').label('tipo'),
                    DonacionFisica.estado.label('estado_donante')
                )
                .outerjoin(Usuario, DonacionFisica.donante_id == Usuario.id)
                .filter(DonacionFisica.fundacion_id == fundacion.id)
                .all()
            )

            monetarias = (
                db.session.query(
                    DonacionMonetaria.created_at,
                    DonacionMonetaria.monto,
                    Necesidad.titulo.label('titulo_necesidad'),
                    Usuario.nombre.label('nombre_donante'),
                    db.literal('Monetaria').label('tipo'),
                    db.literal('pagada').label('estado_donante')
                )
                .outerjoin(Necesidad, DonacionMonetaria.necesidad_id == Necesidad.id)
                .outerjoin(Usuario, DonacionMonetaria.usuario_id == Usuario.id)
                .filter(Necesidad.fundacion_id == fundacion.id)
                .all()
            )

            donaciones = sorted(fisicas + monetarias, key=lambda x: x.created_at, reverse=True)
            solicitudes_ayuda = Necesidad.query.filter_by(fundacion_id=fundacion.id, estado='activa').all()

            return True, "Dashboard cargado.", {
                "usuario": usuario,
                "fundacion": fundacion,
                "donaciones": donaciones,
                "stats": {"total_donaciones": len(donaciones)},
                "solicitudes_ayuda": solicitudes_ayuda
            }
        except Exception as e:
            print(f"Error cargando dashboard de fundacion: {e}")
            return False, "Error en carga.", None

    @staticmethod
    def publicar_necesidad(usuario_id, form):
        try:
            if not AuthService.fundacion_activa(usuario_id):
                return False, "Tu fundacion aun no esta aprobada para publicar necesidades."

            fundacion = Fundacion.query.filter_by(usuario_id=usuario_id).first()
            if not fundacion:
                return False, "Solo las fundaciones pueden publicar necesidades."

            titulo = form.get('titulo')
            descripcion = form.get('descripcion')
            cantidad = form.get('cantidad_requerida')
            categoria = form.get('categoria')
            fecha_limite = form.get('fecha_limite')

            if not titulo or not descripcion or not cantidad or not categoria:
                return False, "Completa los campos obligatorios de la necesidad."

            detalles = {
                k: v for k, v in form.items()
                if k not in ['titulo', 'descripcion', 'cantidad_requerida', 'categoria', 'fecha_limite']
            }
            if fecha_limite:
                detalles['fecha_limite'] = fecha_limite

            exito = NecesidadesManager.crear_necesidad(
                fundacion.id,
                titulo,
                descripcion,
                cantidad,
                categoria,
                detalles
            )

            if exito:
                return True, "Necesidad publicada exitosamente."

            return False, "Error al publicar la necesidad."
        except Exception as e:
            print(f"Error publicando necesidad: {e}")
            return False, "Error inesperado al publicar la necesidad."
