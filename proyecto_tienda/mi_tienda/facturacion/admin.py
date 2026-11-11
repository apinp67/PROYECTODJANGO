from django.contrib import admin
from .models import (Categoria, Marca, Producto, Cliente, Proveedor, Perfil,
                     Venta, DetalleVenta, Compra, DetalleCompra)


class BaseAdmin(admin.ModelAdmin):
    """Admin común: muestra los campos del ModeloBase y llena user solo."""
    readonly_fields = ("user", "fecha_creacion", "fecha_modificacion")   # se ven, pero no se editan

    def save_model(self, request, obj, form, change):
        obj.user = request.user                  # quién guardó desde el admin
        super().save_model(request, obj, form, change)


admin.site.register([Categoria, Marca, Cliente, Proveedor, Perfil], BaseAdmin)   # varios modelos a la vez


@admin.register(Producto)
class ProductoAdmin(BaseAdmin):
    list_display = ("nombre", "marca", "precio", "stock", "activo")
    search_fields = ("nombre",)
    list_filter = ("marca", "categorias", "activo")
    filter_horizontal = ("categorias",)


class DetalleVentaInline(admin.TabularInline):   # Inline: los detalles se editan DENTRO de la venta
    model = DetalleVenta
    extra = 1                                    # 1 fila vacía para agregar


@admin.register(Venta)
class VentaAdmin(BaseAdmin):
    list_display = ("id", "cliente", "fecha_hora", "tipo_pago", "total")
    list_filter = ("tipo_pago",)
    readonly_fields = BaseAdmin.readonly_fields + ("subtotal", "iva", "total")
    inlines = [DetalleVentaInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)   # primero guarda los detalles
        form.instance.calcular_totales()                      # luego recalcula los totales
        # OJO: el admin NO mueve el stock. Las ventas reales se hacen desde tu sistema.


class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 1


@admin.register(Compra)
class CompraAdmin(BaseAdmin):
    list_display = ("id", "proveedor", "fecha_hora", "tipo_pago", "total")
    readonly_fields = BaseAdmin.readonly_fields + ("subtotal", "iva", "total")
    inlines = [DetalleCompraInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.calcular_totales()
