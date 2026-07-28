"""
URL configuration for the RunForce project.
"""
from django.contrib import admin
from django.urls import include, path

from apps.common.views import DocsSchemaView, DocsSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/schema/', DocsSchemaView.as_view(), name='schema'),
    path('api/docs/', DocsSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    path('api/v1/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.runs.urls')),
    path('api/v1/', include('apps.social.urls')),
    path('api/v1/', include('apps.notifications.urls')),
]
