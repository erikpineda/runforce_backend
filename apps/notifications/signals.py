from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.runs.models import Carrera
from apps.runs.services import rango_semana, resumen_periodo
from apps.social.services import ids_amigos

from .services import notificar_logro, notificar_ranking_superado

Usuario = get_user_model()

HITOS_KM_ACUMULADOS = [Decimal('5'), Decimal('10'), Decimal('21.1'), Decimal('42.2'), Decimal('100')]


@receiver(post_save, sender=Carrera)
def verificar_logro_por_acumulado(sender, instance, created, **kwargs):
    if not created:
        return

    total_previo = (
        Carrera.objects.filter(usuario=instance.usuario)
        .exclude(id=instance.id)
        .aggregate(total=Sum('distancia_km'))['total']
        or Decimal('0')
    )
    total_actual = total_previo + Decimal(str(instance.distancia_km))

    for hito in HITOS_KM_ACUMULADOS:
        if total_previo < hito <= total_actual:
            notificar_logro(instance.usuario, f'¡Felicidades! Alcanzaste {hito} km acumulados en RunForce.')


@receiver(post_save, sender=Carrera)
def verificar_ranking_semanal_superado(sender, instance, created, **kwargs):
    if not created:
        return

    inicio, fin = rango_semana(instance.iniciada_en)
    if not (inicio <= instance.iniciada_en < fin):
        return

    resumen_usuario = resumen_periodo(Carrera.objects, instance.usuario, inicio, fin)
    total_actual = resumen_usuario['km_totales']
    total_previo = total_actual - Decimal(str(instance.distancia_km))

    for amigo_id in ids_amigos(instance.usuario):
        amigo = Usuario.objects.get(id=amigo_id)
        total_amigo = resumen_periodo(Carrera.objects, amigo, inicio, fin)['km_totales']
        if total_previo <= total_amigo < total_actual:
            notificar_ranking_superado(
                amigo, f'{instance.usuario.nombre_completo} te supero en el ranking semanal.'
            )
