from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

app_name = "facturacion"

urlpatterns = [
    # --- Rutas de Marcas (VBF) ---
    path("marcas/", views.marca_lista, name="marca_lista"),
    path("marcas/crear/", views.marca_crear, name="marca_crear"),
    path("marcas/editar/<int:pk>/", views.marca_editar, name="marca_editar"),
    path("marcas/eliminar/<int:pk>/", views.marca_eliminar, name="marca_eliminar"),
    
    # --- Rutas de Categorías (VBF) ---
    path("categorias/", views.categoria_lista, name="categoria_lista"),
    path("categorias/crear/", views.categoria_crear, name="categoria_crear"),
    path("categorias/editar/<int:pk>/", views.categoria_editar, name="categoria_editar"),
    path("categorias/eliminar/<int:pk>/", views.categoria_eliminar, name="categoria_eliminar"),

    # --- Rutas de Productos (VBC) ---
    path("productos/", views.ProductoListView.as_view(), name="producto_lista"),
    path("productos/crear/", views.ProductoCreateView.as_view(), name="producto_crear"),
    path("productos/editar/<int:pk>/", views.ProductoUpdateView.as_view(), name="producto_editar"),
    path("productos/eliminar/<int:pk>/", views.ProductoDeleteView.as_view(), name="producto_eliminar"),
    # ... tus rutas anteriores ...

    # --- Rutas de Clientes (VBC) ---
    path("clientes/", views.ClienteListView.as_view(), name="cliente_lista"),
    path("clientes/crear/", views.ClienteCreateView.as_view(), name="cliente_crear"),
    path("clientes/editar/<int:pk>/", views.ClienteUpdateView.as_view(), name="cliente_editar"),
    path("clientes/eliminar/<int:pk>/", views.ClienteDeleteView.as_view(), name="cliente_eliminar"),
    # --- Rutas de Autenticación ---
    path("login/", LoginView.as_view(template_name="facturacion/login.html"), name="login"),
    path("logout/", LogoutView.as_view(next_page="home"), name="logout"),
]
