import secrets

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework.exceptions import ValidationError

from .models import CodigoOTP


def _generar_codigo():
    return ''.join(secrets.choice('0123456789') for _ in range(6))


def generar_y_enviar_otp(usuario, tipo):
    """Invalida OTPs previos sin usar del mismo tipo, crea uno nuevo y lo envia por correo."""
    CodigoOTP.objects.filter(usuario=usuario, tipo=tipo, usado=False).update(usado=True)

    codigo_otp = CodigoOTP.objects.create(
        usuario=usuario,
        codigo=_generar_codigo(),
        tipo=tipo,
        expira_en=timezone.now() + timezone.timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
    )
    _enviar_correo_otp(usuario, codigo_otp)
    return codigo_otp


def _enviar_correo_otp(usuario, codigo_otp):
    es_registro = codigo_otp.tipo == CodigoOTP.TIPO_REGISTRO
    asunto = 'Tu codigo de verificacion RunForce' if es_registro else 'Restablece tu password de RunForce'

    contexto = {
        'asunto': asunto,
        'nombre_completo': usuario.nombre_completo,
        'codigo': codigo_otp.codigo,
        'minutos': settings.OTP_EXPIRY_MINUTES,
        'es_registro': es_registro,
    }

    texto_plano = (
        f'Hola {usuario.nombre_completo},\n\n'
        f'Tu codigo de verificacion es: {codigo_otp.codigo}\n'
        f'Expira en {settings.OTP_EXPIRY_MINUTES} minutos.\n\n'
        'Si no solicitaste esto, ignora este correo.'
    )
    html = render_to_string('emails/otp_email.html', contexto)

    email = EmailMultiAlternatives(asunto, texto_plano, settings.DEFAULT_FROM_EMAIL, [usuario.correo])
    email.attach_alternative(html, 'text/html')
    email.send(fail_silently=False)


def validar_otp(usuario, codigo, tipo):
    """Valida un OTP para el usuario y tipo dados. Lanza ValidationError si no es valido."""
    codigo_otp = (
        CodigoOTP.objects.filter(usuario=usuario, tipo=tipo, usado=False)
        .order_by('-creado_en')
        .first()
    )

    if codigo_otp is None:
        raise ValidationError('No hay un codigo pendiente para este usuario.')

    if codigo_otp.intentos >= settings.OTP_MAX_ATTEMPTS:
        codigo_otp.usado = True
        codigo_otp.save(update_fields=['usado'])
        raise ValidationError('Se excedio el numero de intentos. Solicita un nuevo codigo.')

    if timezone.now() > codigo_otp.expira_en:
        raise ValidationError('El codigo ha expirado. Solicita uno nuevo.')

    if codigo_otp.codigo != codigo:
        codigo_otp.intentos += 1
        codigo_otp.save(update_fields=['intentos'])
        raise ValidationError('Codigo invalido.')

    codigo_otp.usado = True
    codigo_otp.save(update_fields=['usado'])
    return codigo_otp


def validar_google_id_token(id_token_str):
    """Valida el idToken de Google contra los servidores de Google y retorna sus claims."""
    try:
        idinfo = google_id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            audience=settings.GOOGLE_CLIENT_ID or None,
        )
    except ValueError as exc:
        raise ValidationError(f'idToken de Google invalido: {exc}') from exc

    if idinfo.get('iss') not in ('accounts.google.com', 'https://accounts.google.com'):
        raise ValidationError('idToken de Google con emisor invalido.')

    return idinfo
