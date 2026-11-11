from django.urls import path
from . import views

app_name = "facturacion"     # apellido de las URLs: 'facturacion:producto_lista'

urlpatterns = [
    # ---------- PRODUCTOS ----------
    path("productos/", views.ProductoListView.as_view(), name="producto_lista"),
    path("productos/crear/", views.ProductoCreateView.as_view(), name="producto_crear"),
    path("productos/<int:pk>/", views.ProductoDetailView.as_view(), name="producto_detalle"),
    path("productos/editar/<int:pk>/", views.ProductoUpdateView.as_view(), name="producto_editar"),
    path("productos/eliminar/<int:pk>/", views.ProductoDeleteView.as_view(), name="producto_eliminar"),

    # ---------- VENTAS ----------
    path("ventas/", views.VentaListView.as_view(), name="venta_lista"),
    path("ventas/crear/", views.VentaCreateView.as_view(), name="venta_crear"),
    path("ventas/<int:pk>/", views.VentaDetailView.as_view(), name="venta_detalle"),
    path("ventas/editar/<int:pk>/", views.VentaUpdateView.as_view(), name="venta_editar"),
    path("ventas/eliminar/<int:pk>/", views.VentaDeleteView.as_view(), name="venta_eliminar"),

    # ---------- MARCAS (Tarea 1) ----------
    path("marcas/", views.MarcaListView.as_view(), name="marca_lista"),
    path("marcas/crear/", views.MarcaCreateView.as_view(), name="marca_crear"),
    path("marcas/editar/<int:pk>/", views.MarcaUpdateView.as_view(), name="marca_editar"),
    path("marcas/eliminar/<int:pk>/", views.MarcaDeleteView.as_view(), name="marca_eliminar"),

    # ---------- CATEGORÍAS (Tarea 2) ----------
    path("categorias/", views.CategoriaListView.as_view(), name="categoria_lista"),
    path("categorias/crear/", views.CategoriaCreateView.as_view(), name="categoria_crear"),
    path("categorias/editar/<int:pk>/", views.CategoriaUpdateView.as_view(), name="categoria_editar"),
    path("categorias/eliminar/<int:pk>/", views.CategoriaDeleteView.as_view(), name="categoria_eliminar"),

    # ---------- CLIENTES (Tarea 3) ----------
    path("clientes/", views.ClienteListView.as_view(), name="cliente_lista"),
    path("clientes/crear/", views.ClienteCreateView.as_view(), name="cliente_crear"),
    path("clientes/<int:pk>/", views.ClienteDetailView.as_view(), name="cliente_detalle"),
    path("clientes/editar/<int:pk>/", views.ClienteUpdateView.as_view(), name="cliente_editar"),
    path("clientes/eliminar/<int:pk>/", views.ClienteDeleteView.as_view(), name="cliente_eliminar"),

    # ---------- PROVEEDORES (Tarea 4) ----------
    path("proveedores/", views.ProveedorListView.as_view(), name="proveedor_lista"),
    path("proveedores/crear/", views.ProveedorCreateView.as_view(), name="proveedor_crear"),
    path("proveedores/editar/<int:pk>/", views.ProveedorUpdateView.as_view(), name="proveedor_editar"),
    path("proveedores/eliminar/<int:pk>/", views.ProveedorDeleteView.as_view(), name="proveedor_eliminar"),

    # ---------- COMPRAS (Tarea 5) ----------
    path("compras/", views.CompraListView.as_view(), name="compra_lista"),
    path("compras/crear/", views.CompraCreateView.as_view(), name="compra_crear"),
    path("compras/<int:pk>/", views.CompraDetailView.as_view(), name="compra_detalle"),
    path("compras/editar/<int:pk>/", views.CompraUpdateView.as_view(), name="compra_editar"),
    path("compras/eliminar/<int:pk>/", views.CompraDeleteView.as_view(), name="compra_eliminar"),

    # ---------- MI PERFIL (reto) ----------
    path("mi-perfil/", views.MiPerfilView.as_view(), name="mi_perfil"),
]
