from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import timezone

from apps.notifications.services import notificar_inactividad

Usuario = get_user_model()

DIAS_INACTIVIDAD = 3


class Command(BaseCommand):
    help = (
        'Notifica a los usuarios activos que no han registrado una carrera en '
        f'{DIAS_INACTIVIDAD} o mas dias. Pensado para ejecutarse via cron/systemd timer diario.'
    )

    def handle(self, *args, **options):
        limite = timezone.now() - timezone.timedelta(days=DIAS_INACTIVIDAD)
        usuarios_activos = Usuario.objects.filter(estado=Usuario.ESTADO_ACTIVO, creado_en__lt=limite)

        total = 0
        for usuario in usuarios_activos:
            ultima_carrera = usuario.carreras.aggregate(ultima=Max('iniciada_en'))['ultima']
            if ultima_carrera is None or ultima_carrera < limite:
                notificar_inactividad(usuario)
                total += 1

        self.stdout.write(self.style.SUCCESS(f'Notificaciones de inactividad enviadas: {total}'))
