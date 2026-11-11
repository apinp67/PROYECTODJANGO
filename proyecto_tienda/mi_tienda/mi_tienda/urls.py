from django.conf import settings                   # para leer DEBUG, MEDIA_URL y MEDIA_ROOT
from django.conf.urls.static import static         # sirve los archivos subidos mientras programas
from django.contrib import admin
from django.urls import path, include

from . import views                                # InicioView (clase) + ingresar, salir, registro (funciones)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.InicioView.as_view(), name="home"),          # VBC: .as_view() convierte la clase en vista
    # ---------- AUTENTICACIÓN: funciones (VBF) ----------
    path("login/", views.ingresar, name="login"),
    path("logout/", views.salir, name="logout"),
    path("registro/", views.registro, name="registro"),
    # ---------- LA APP ----------
    path("facturacion/", include("facturacion.urls")),
]

if settings.DEBUG:                                 # solo en desarrollo: /media/... muestra las fotos
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
