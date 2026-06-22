from models.models import db, Usuario, Fundacion, Necesidad, DonacionFisica, DonacionMonetaria
from models.necesidades_manager import NecesidadesManager
from services.auth_service import AuthService
from services.donacion_service import DonacionService


class FundacionService:
    @staticmethod
    def puede_acceder(usuario_id):
        return AuthService.fundacion_activa(usuario_id)



    @staticmethod
    def obtener_dashboard(usuario_id, q=None, donante=None, categoria=None, est=None):
        """
        Carga el dashboard de la fundación. Ahora acepta los 4 filtros
        del formulario de 'Trazabilidad y Filtros' (q, donante, categoria,
        est) y los aplica sobre la lista de donaciones mostrada, usando
        el mismo motor de filtrado ya probado en el panel del donante
        (DonacionService.obtener_donaciones_filtradas_fundacion).
        """
        try:
            if not AuthService.fundacion_activa(usuario_id):
                return False, "Tu fundacion aun no esta aprobada para ingresar.", None

            # 1. Limpiamos caché para obligar a leer los datos reales de Postgres
            db.session.expire_all()

            usuario = Usuario.query.get(usuario_id)
            fundacion = Fundacion.query.filter_by(usuario_id=usuario_id).first()

            if not usuario or not fundacion:
                return False, "No fue posible encontrar la fundacion.", None

            # 2. Donaciones (físicas + monetarias) YA FILTRADAS según los
            # parámetros de búsqueda recibidos desde la URL.
            lista_donaciones = DonacionService.obtener_donaciones_filtradas_fundacion(
                fundacion_id=fundacion.id,
                q=q,
                donante=donante,
                categoria=categoria,
                est=est
            )

            # 3. Solicitudes de ayuda: se mantienen SIN filtrar, porque
            # corresponden a la sección "Requerimientos de la Fundación"
            # (necesidades publicadas), no al historial de trazabilidad.
            solicitudes_ayuda = (
                Necesidad.query.filter(Necesidad.fundacion_id == fundacion.id)
                .order_by(Necesidad.created_at.desc())
                .all()
            )

            # 4. Estadísticas reales calculadas sobre TODAS las donaciones
            # de la fundación (no las filtradas), para que las tarjetas
            # del panel lateral no cambien según la búsqueda aplicada.
            todas_las_donaciones = DonacionService.obtener_donaciones_por_fundacion(fundacion.id)
            pendientes = sum(1 for d in todas_las_donaciones if d['estado'] == 'pendiente')
            recibidas = sum(1 for d in todas_las_donaciones if d['estado'] == 'recibida')
            rechazadas = sum(1 for d in todas_las_donaciones if d['estado'] == 'rechazada')
            alimentos = sum(1 for d in todas_las_donaciones if d['tipo'] == 'fisica' and d['nombre_categoria'] == 'alimentos')
            ropa = sum(1 for d in todas_las_donaciones if d['tipo'] == 'fisica' and d['nombre_categoria'] == 'ropa')
            otros = sum(1 for d in todas_las_donaciones if d['tipo'] == 'fisica' and d['nombre_categoria'] not in ['alimentos', 'ropa'])
            monetarias_count = sum(1 for d in todas_las_donaciones if d['tipo'] == 'monetario')

            stats_dashboard = {
                "total_combinado": len(todas_las_donaciones),
                "pendientes": pendientes,
                "recibidas": recibidas,
                "rechazadas": rechazadas,
                "alimentos": alimentos,
                "ropa": ropa,
                "otros": otros,
                "monetarias": monetarias_count
            }

            return True, "Dashboard cargado.", {
                "usuario": usuario,
                "fundacion": fundacion,
                "donaciones": lista_donaciones,
                "stats": stats_dashboard,
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

            # 1. CAPTURAMOS EL MONTO CORRECTO DESDE HTML (monto_meta) O FISICO (cantidad_requerida)
            cantidad = form.get('cantidad_requerida') or form.get('monto_meta')

            # 2. CAPTURAMOS LA CATEGORÍA O LE ASIGNAMOS 'monetaria' SI VIENE DEL FORMULARIO MONETARIO
            categoria = form.get('categoria')
            if not categoria and form.get('monto_meta'):
                categoria = 'Causa Social (Monetaria)' # Se asigna automáticamente

            if not titulo or not descripcion or not cantidad or not categoria:
                return False, "Completa los campos obligatorios de la necesidad."

            detalles = {
                k: v for k, v in form.items()
                if k not in ['titulo', 'descripcion', 'cantidad_requerida', 'monto_meta', 'categoria', 'fecha_limite']
            }
            if form.get('fecha_limite'):
                detalles['fecha_limite'] = form.get('fecha_limite')

            exito = NecesidadesManager.crear_necesidad(
                fundacion.id,
                titulo,
                descripcion,
                int(float(cantidad)),
                categoria,
                detalles
            )

            if exito:
                return True, "Necesidad publicada exitosamente."

            return False, "Error al publicar la necesidad."
        except Exception as e:
            print(f"Error publicando necesidad: {e}")
            return False, "Error inesperado al publicar la necesidad."