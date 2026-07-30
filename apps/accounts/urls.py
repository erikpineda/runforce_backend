from django.urls import path

from . import views

urlpatterns = [
    path('auth/registro', views.RegistroView.as_view(), name='auth-registro'),
    path('auth/verificar-otp', views.VerificarOTPView.as_view(), name='auth-verificar-otp'),
    path('auth/login', views.LoginView.as_view(), name='auth-login'),
    path('auth/google', views.GoogleAuthView.as_view(), name='auth-google'),
    path('auth/token/refresh', views.TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('auth/olvide-password', views.OlvidePasswordView.as_view(), name='auth-olvide-password'),
    path('auth/reset-password', views.ResetPasswordView.as_view(), name='auth-reset-password'),
    path('usuarios/me', views.UsuarioMeView.as_view(), name='usuario-me'),
    path('usuarios/me/foto', views.FotoPerfilView.as_view(), name='usuario-me-foto'),
    path('usuarios/me/password', views.CambiarPasswordView.as_view(), name='usuario-me-password'),
]
