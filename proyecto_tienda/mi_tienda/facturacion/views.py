from django.contrib import messages                          # mensajes verdes / rojos
from django.contrib.auth.mixins import LoginRequiredMixin   # exige sesión (el @login_required de las clases)
from django.contrib.messages.views import SuccessMessageMixin   # mensaje de éxito automático
from django.db import transaction                            # transaction.atomic(): todo o nada
from django.db.models import ProtectedError, Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView

from .forms import (MarcaForm, CategoriaForm, ClienteForm, ProveedorForm, ProductoForm,
                    VentaForm, DetalleVentaFormSet, CompraForm, DetalleCompraFormSet, PerfilForm)
from .mixins import UsuarioRegistroMixin
from .models import (Marca, Categoria, Cliente, Proveedor, Producto, Perfil,
                     Venta, Compra, TipoPago, IVA_TARIFA)

# =====================================================================
# PRODUCTOS · Vistas Basadas en Clases (VBC)
# =====================================================================

class ProductoListView(LoginRequiredMixin, ListView):     # LISTAR
    model = Producto                                       # ¿qué tabla?
    template_name = "facturacion/producto_lista.html"      # ¿qué HTML?
    context_object_name = "productos"                      # nombre de la lista en el HTML
    paginate_by = 5                                        # 5 por página → envía page_obj
    extra_context = {"titulo": "Productos"}                # datos fijos extra para el HTML

    def get_queryset(self):                                # ¿QUÉ registros se muestran?
        productos = super().get_queryset()                 # lo normal: Producto.objects.all()
        productos = productos.select_related("marca").prefetch_related("categorias")   # menos consultas
        q = self.request.GET.get("q", "")                  # buscador: ?q=galaxy
        if q:
            productos = productos.filter(nombre__icontains=q)
        return productos

    def get_context_data(self, **kwargs):                  # ¿qué datos EXTRA recibe el HTML?
        contexto = super().get_context_data(**kwargs)      # lo que ListView ya armó
        contexto["q"] = self.request.GET.get("q", "")      # + lo buscado
        return contexto


class ProductoCreateView(LoginRequiredMixin, UsuarioRegistroMixin, SuccessMessageMixin, CreateView):   # CREAR
    model = Producto
    form_class = ProductoForm                              # nuestro formulario
    template_name = "facturacion/producto_form.html"
    success_url = reverse_lazy("facturacion:producto_lista")   # a dónde ir al guardar
    success_message = "Producto «%(nombre)s» creado."      # %(nombre)s = el campo nombre del formulario
    extra_context = {"titulo": "Nuevo producto", "boton": "Guardar"}


class ProductoUpdateView(LoginRequiredMixin, UsuarioRegistroMixin, SuccessMessageMixin, UpdateView):   # EDITAR
    model = Producto
    form_class = ProductoForm
    template_name = "facturacion/producto_form.html"       # el mismo template de crear
    success_url = reverse_lazy("facturacion:producto_lista")
    success_message = "Producto «%(nombre)s» actualizado."
    extra_context = {"titulo": "Editar producto", "boton": "Actualizar"}

    def form_invalid(self, form):                          # cuando hay errores (POST inválido)
        messages.error(self.request, "Revisa los campos marcados en rojo.")
        return super().form_invalid(form)                  # vuelve a mostrar el formulario


class ProductoDetailView(LoginRequiredMixin, DetailView):  # VER UNO
    model = Producto
    template_name = "facturacion/producto_detalle.html"
    context_object_name = "producto"


class ProductoDeleteView(LoginRequiredMixin, DeleteView):  # ELIMINAR
    model = Producto
    template_name = "facturacion/producto_eliminar.html"
    context_object_name = "producto"
    success_url = reverse_lazy("facturacion:producto_lista")

    def form_valid(self, form):                            # se ejecuta al confirmar (POST)
        nombre = self.object.nombre                        # self.object = el producto a eliminar
        try:
            respuesta = super().form_valid(form)           # DELETE + redirect
        except ProtectedError:                             # ya está en una venta o compra (PROTECT)
            messages.error(self.request, f"No se puede eliminar «{nombre}»: ya tiene ventas o compras. Desactívalo.")
            return redirect("facturacion:producto_lista")
        messages.success(self.request, f"Producto «{nombre}» eliminado.")
        return respuesta


# =====================================================================
# VENTAS (maestro-detalle) · Vistas Basadas en Clases
# =====================================================================

class VentaListView(LoginRequiredMixin, ListView):
    model = Venta
    template_name = "facturacion/venta_lista.html"
    context_object_name = "ventas"
    paginate_by = 10
    extra_context = {"titulo": "Ventas", "tipos_pago": TipoPago.choices}   # opciones para el filtro

    def get_queryset(self):
        ventas = super().get_queryset().select_related("cliente")   # trae el cliente en el mismo JOIN
        q = self.request.GET.get("q", "")
        tipo = self.request.GET.get("tipo_pago", "")
        if q:   # Q(...) | Q(...) = condición con OR: por apellido O por cédula
            ventas = ventas.filter(Q(cliente__apellidos__icontains=q) | Q(cliente__cedula__icontains=q))
        if tipo:
            ventas = ventas.filter(tipo_pago=tipo)
        return ventas

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["q"] = self.request.GET.get("q", "")
        contexto["tipo_pago"] = self.request.GET.get("tipo_pago", "")
        return contexto


class VentaDetallesMixin:
    """Lo que COMPARTEN crear y editar una venta: cabecera (form) + filas (formset)."""
    model = Venta
    form_class = VentaForm
    template_name = "facturacion/venta_form.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)      # trae "form" (la cabecera)
        if "detalles" not in contexto:                     # en GET el formset todavía no existe...
            contexto["detalles"] = DetalleVentaFormSet(instance=self.object)   # ...lo creamos (vacío o lleno)
        return contexto

    def post(self, request, *args, **kwargs):              # REEMPLAZA el post() normal de la vista
        form = self.get_form()                             # 1. cabecera con request.POST
        detalles = DetalleVentaFormSet(request.POST, instance=self.object)   # 2. filas con request.POST
        if form.is_valid() and detalles.is_valid():        # 3. ¿las DOS partes están bien?
            return self.form_valid(form, detalles)
        return self.form_invalid(form, detalles)

    def form_valid(self, form, detalles):
        with transaction.atomic():                         # TODO o NADA: si algo falla, se deshace todo
            if self.object:                                # al EDITAR: devolver lo que la venta tenía
                self.object.devolver_stock()
            form.instance.user = self.request.user
            self.object = form.save()                      # INSERT o UPDATE de la cabecera
            self.guardar_detalles(detalles)                # INSERT / UPDATE / DELETE de las filas
            self.object.descontar_stock()                  # saca de bodega lo vendido
            self.object.calcular_totales()                 # subtotal, IVA y total
        messages.success(self.request, f"{self.object} guardada. Total: ${self.object.total}")
        return HttpResponseRedirect(self.get_success_url())

    def guardar_detalles(self, detalles):
        detalles.instance = self.object                    # las filas pertenecen a ESTA venta
        filas = detalles.save(commit=False)                # objetos nuevos o cambiados, SIN guardar todavía
        for fila in detalles.deleted_objects:              # filas con la casilla "Quitar"
            fila.delete()
        cambio_producto = {obj.pk for obj, campos in detalles.changed_objects if "producto" in campos}
        for fila in filas:
            if fila.pk is None or fila.pk in cambio_producto:   # fila nueva o con otro producto...
                fila.precio = fila.producto.precio              # ...toma el precio ACTUAL del producto
            fila.user = self.request.user
            fila.save()

    def form_invalid(self, form, detalles):
        messages.error(self.request, "Revisa los datos de la venta.")
        # volvemos a dibujar la página con la cabecera Y las filas, con sus errores
        return self.render_to_response(self.get_context_data(form=form, detalles=detalles))

    def get_success_url(self):
        return reverse("facturacion:venta_detalle", kwargs={"pk": self.object.pk})   # a la factura


class VentaCreateView(LoginRequiredMixin, VentaDetallesMixin, CreateView):   # CREAR
    extra_context = {"titulo": "Nueva venta", "boton": "Guardar venta"}

    def post(self, request, *args, **kwargs):
        self.object = None                                 # CreateView: aún no hay venta
        return super().post(request, *args, **kwargs)      # sigue al post() del mixin


class VentaUpdateView(LoginRequiredMixin, VentaDetallesMixin, UpdateView):   # EDITAR
    extra_context = {"titulo": "Editar venta", "boton": "Actualizar venta"}

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()                    # UpdateView: la venta del <int:pk>
        return super().post(request, *args, **kwargs)


class VentaDetailView(LoginRequiredMixin, DetailView):     # VER (la factura)
    model = Venta
    template_name = "facturacion/venta_detalle.html"
    context_object_name = "venta"

    def get_queryset(self):
        return super().get_queryset().select_related("cliente", "user").prefetch_related("detalles__producto")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["iva_porcentaje"] = IVA_TARIFA * 100      # 15
        return contexto


class VentaDeleteView(LoginRequiredMixin, DeleteView):     # ELIMINAR
    model = Venta
    template_name = "facturacion/venta_eliminar.html"
    context_object_name = "venta"
    success_url = reverse_lazy("facturacion:venta_lista")

    def form_valid(self, form):
        with transaction.atomic():
            self.object.devolver_stock()                   # 1. los productos regresan a la bodega
            respuesta = super().form_valid(form)           # 2. DELETE de la venta (CASCADE borra sus detalles)
        messages.success(self.request, "Venta eliminada y stock devuelto.")
        return respuesta


# =====================================================================
# MARCAS · Vistas Basadas en Clases  (TAREA 1)
# =====================================================================

class MarcaListView(LoginRequiredMixin, ListView):         # LISTAR
    model = Marca                                          # ¿qué tabla?
    template_name = "facturacion/marca_lista.html"         # ¿qué HTML?
    context_object_name = "marcas"                         # nombre de la lista en el HTML
    paginate_by = 5                                        # 5 por página → envía page_obj
    extra_context = {"titulo": "Marcas"}                   # dato fijo extra para el HTML

    def get_queryset(self):                                # ¿QUÉ registros se muestran?
        marcas = super().get_queryset()                    # lo normal: Marca.objects.all()
        q = self.request.GET.get("q", "")                  # buscador: ?q=samsung
        if q:
            marcas = marcas.filter(nombre__icontains=q)    # icontains: contiene el texto, sin importar mayúsculas
        return marcas

    def get_context_data(self, **kwargs):                  # ¿qué datos EXTRA recibe el HTML?
        contexto = super().get_context_data(**kwargs)
        contexto["q"] = self.request.GET.get("q", "")      # devolvemos lo buscado para dejarlo en la caja
        return contexto


class MarcaCreateView(LoginRequiredMixin, UsuarioRegistroMixin, SuccessMessageMixin, CreateView):   # CREAR
    model = Marca
    form_class = MarcaForm                                 # nuestro formulario
    template_name = "facturacion/marca_form.html"
    success_url = reverse_lazy("facturacion:marca_lista")  # a dónde ir al guardar
    success_message = "Marca «%(nombre)s» creada."         # %(nombre)s = el campo nombre del formulario
    extra_context = {"titulo": "Nueva marca", "boton": "Guardar"}


class MarcaUpdateView(LoginRequiredMixin, UsuarioRegistroMixin, SuccessMessageMixin, UpdateView):   # EDITAR
    model = Marca
    form_class = MarcaForm
    template_name = "facturacion/marca_form.html"          # el mismo template de crear
    success_url = reverse_lazy("facturacion:marca_lista")
    success_message = "Marca «%(nombre)s» actualizada."
    extra_context = {"titulo": "Editar marca", "boton": "Actualizar"}

    def form_invalid(self, form):                          # POST con errores
        messages.error(self.request, "Revisa los campos marcados en rojo.")
        return super().form_invalid(form)                  # vuelve a mostrar el formulario


class MarcaDeleteView(LoginRequiredMixin, DeleteView):     # ELIMINAR
    model = Marca
    template_name = "facturacion/marca_eliminar.html"
    context_object_name = "marca"
    success_url = reverse_lazy("facturacion:marca_lista")

    def form_valid(self, form):                            # se ejecuta al confirmar (POST)
        nombre = self.object.nombre                        # self.object = la marca a eliminar
        try:
            respuesta = super().form_valid(form)           # DELETE + redirect
        except ProtectedError:                             # Producto.marca usa PROTECT: tiene productos
            messages.error(self.request, f"No se puede eliminar «{nombre}»: tiene productos. Desactívala en su lugar.")
            return redirect("facturacion:marca_lista")
        messages.success(self.request, f"Marca «{nombre}» eliminada.")
        return respuesta


# =====================================================================
# CATEGORÍAS · Vistas Basadas en Clases  (TAREA 2)
# =====================================================================

class CategoriaListView(LoginRequiredMixin, ListView):     # LISTAR
    model = Categoria
    template_name = "facturacion/categoria_lista.html"
    context_object_name = "categorias"
    paginate_by = 5
    extra_context = {"titulo": "Categorías"}

    def get_queryset(self):
        categorias = super().get_queryset()
        q = self.request.GET.get("q", "")
        if q:
            categorias = categorias.filter(nombre__icontains=q)
        return categorias

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["q"] = self.request.GET.get("q", "")
        return contexto


class CategoriaCreateView(LoginRequiredMixin, UsuarioRegistroMixin, SuccessMessageMixin, CreateView):   # CREAR
    model = Categoria
    form_class = CategoriaForm
    template_name = "facturacion/categoria_form.html"
    success_url = reverse_lazy("facturacion:categoria_lista")
    success_message = "Categoría «%(nombre)s» creada."
    extra_context = {"titulo": "Nueva categoría", "boton": "Guardar"}


class CategoriaUpdateView(LoginRequiredMixin, UsuarioRegistroMixin, SuccessMessageMixin, UpdateView):   # EDITAR
    model = Categoria
    form_class = CategoriaForm
    template_name = "facturacion/categoria_form.html"
    success_url = reverse_lazy("facturacion:categoria_lista")
    success_message = "Categoría «%(nombre)s» actualizada."
    extra_context = {"titulo": "Editar categoría", "boton": "Actualizar"}

    def form_invalid(self, form):
        messages.error(self.request, "Revisa los campos marcados en rojo.")
        return super().form_invalid(form)


class CategoriaDeleteView(LoginRequiredMixin, DeleteView):  # ELIMINAR
    model = Categoria
    template_name = "facturacion/categoria_eliminar.html"
    context_object_name = "categoria"
    success_url = reverse_lazy("facturacion:categoria_lista")

    def form_valid(self, form):
        nombre = self.object.nombre
        # Aquí NO hace falta try/except: la relación con Producto es N:M, así que solo se borran
        # los pares de la tabla intermedia; los productos siguen existiendo.
        respuesta = super().form_valid(form)
        messages.success(self.request, f"Categoría «{nombre}» eliminada.")
        return respuesta


# =====================================================================
# CLIENTES · Vistas Basadas en Clases  (TAREA 3)
# =====================================================================

class ClienteListView(LoginRequiredMixin, ListView):       # LISTAR
    model = Cliente
    template_name = "facturacion/cliente_lista.html"
    context_object_name = "clientes"
    paginate_by = 5                                        # 5 por página, como pide la tarea
    extra_context = {"titulo": "Clientes"}

    def get_queryset(self):
        clientes = super().get_queryset()
        q = self.request.GET.get("q", "")
        if q:   # Q(...) | Q(...) = condición con OR: por apellido O por cédula
            clientes = clientes.filter(Q(apellidos__icontains=q) | Q(cedula__icontains=q))
        return clientes

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["q"] = self.request.GET.get("q", "")
        return contexto


class ClienteDetailView(LoginRequiredMixin, DetailView):   # VER UNO: datos + sus ventas
    model = Cliente
    template_name = "facturacion/cliente_detalle.html"
    context_object_name = "cliente"                        # en el HTML: cliente.ventas.all (related_name="ventas")


class ClienteCreateView(LoginRequiredMixin, UsuarioRegistroMixin, SuccessMessageMixin, CreateView):   # CREAR
    model = Cliente
    form_class = ClienteForm
    template_name = "facturacion/cliente_form.html"
    success_url = reverse_lazy("facturacion:cliente_lista")
    success_message = "Cliente «%(apellidos)s %(nombres)s» creado."
    extra_context = {"titulo": "Nuevo cliente", "boton": "Guardar"}


class ClienteUpdateView(LoginRequiredMixin, UsuarioRegistroMixin, SuccessMessageMixin, UpdateView):   # EDITAR
    model = Cliente
    form_class = ClienteForm
    template_name = "facturacion/cliente_form.html"
    success_url = reverse_lazy("facturacion:cliente_lista")
    success_message = "Cliente «%(apellidos)s %(nombres)s» actualizado."
    extra_context = {"titulo": "Editar cliente", "boton": "Actualizar"}

    def form_invalid(self, form):
        messages.error(self.request, "Revisa los campos marcados en rojo.")
        return super().form_invalid(form)


class ClienteDeleteView(LoginRequiredMixin, DeleteView):   # ELIMINAR
    model = Cliente
    template_name = "facturacion/cliente_eliminar.html"
    context_object_name = "cliente"
    success_url = reverse_lazy("facturacion:cliente_lista")

    def form_valid(self, form):
        nombre = str(self.object)                          # usa Cliente.__str__: "Apellidos Nombres"
        try:
            respuesta = super().form_valid(form)
        except ProtectedError:                             # Venta.cliente usa PROTECT: ya compró
            messages.error(self.request, f"No se puede eliminar a «{nombre}»: tiene ventas registradas.")
            return redirect("facturacion:cliente_lista")
        messages.success(self.request, f"Cliente «{nombre}» eliminado.")
        return respuesta


# =====================================================================
# PROVEEDORES · Vistas Basadas en Clases  (TAREA 4)
# =====================================================================

class ProveedorListView(LoginRequiredMixin, ListView):     # LISTAR (con miniatura del logo)
    model = Proveedor
    template_name = "facturacion/proveedor_lista.html"
    context_object_name = "proveedores"
    paginate_by = 5
    extra_context = {"titulo": "Proveedores"}

    def get_queryset(self):
        proveedores = super().get_queryset()
        q = self.request.GET.get("q", "")
        if q:   # busca por nombre, apellido o RUC
            proveedores = proveedores.filter(
                Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(ruc__icontains=q)
            )
        return proveedores

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["q"] = self.request.GET.get("q", "")
        return contexto


class ProveedorCreateView(LoginRequiredMixin, UsuarioRegistroMixin, SuccessMessageMixin, CreateView):   # CREAR
    model = Proveedor
    form_class = ProveedorForm
    template_name = "facturacion/proveedor_form.html"
    success_url = reverse_lazy("facturacion:proveedor_lista")
    success_message = "Proveedor «%(nombre)s %(apellido)s» creado."
    extra_context = {"titulo": "Nuevo proveedor", "boton": "Guardar"}


class ProveedorUpdateView(LoginRequiredMixin, UsuarioRegistroMixin, SuccessMessageMixin, UpdateView):   # EDITAR
    model = Proveedor
    form_class = ProveedorForm
    template_name = "facturacion/proveedor_form.html"
    success_url = reverse_lazy("facturacion:proveedor_lista")
    success_message = "Proveedor «%(nombre)s %(apellido)s» actualizado."
    extra_context = {"titulo": "Editar proveedor", "boton": "Actualizar"}

    def form_invalid(self, form):
        messages.error(self.request, "Revisa los campos marcados en rojo.")
        return super().form_invalid(form)


class ProveedorDeleteView(LoginRequiredMixin, DeleteView):  # ELIMINAR
    model = Proveedor
    template_name = "facturacion/proveedor_eliminar.html"
    context_object_name = "proveedor"
    success_url = reverse_lazy("facturacion:proveedor_lista")

    def form_valid(self, form):
        nombre = str(self.object)
        try:
            respuesta = super().form_valid(form)
        except ProtectedError:                             # Compra.proveedor usa PROTECT: tiene compras
            messages.error(self.request, f"No se puede eliminar a «{nombre}»: tiene compras registradas.")
            return redirect("facturacion:proveedor_lista")
        messages.success(self.request, f"Proveedor «{nombre}» eliminado.")
        return respuesta


# =====================================================================
# COMPRAS (maestro-detalle) · Vistas Basadas en Clases  (TAREA 5)
# Es el espejo de las Ventas: aquí el stock SUBE en lugar de bajar.
# =====================================================================

class CompraListView(LoginRequiredMixin, ListView):        # LISTAR con filtros
    model = Compra
    template_name = "facturacion/compra_lista.html"
    context_object_name = "compras"
    paginate_by = 10
    extra_context = {"titulo": "Compras", "tipos_pago": TipoPago.choices}   # opciones para el filtro de pago

    def get_queryset(self):
        compras = super().get_queryset().select_related("proveedor")   # trae el proveedor en el mismo JOIN
        proveedor = self.request.GET.get("proveedor", "")              # ?proveedor=3 (el id)
        tipo = self.request.GET.get("tipo_pago", "")                   # ?tipo_pago=credito
        if proveedor:
            compras = compras.filter(proveedor_id=proveedor)
        if tipo:
            compras = compras.filter(tipo_pago=tipo)
        return compras

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["proveedores"] = Proveedor.objects.all()              # opciones del filtro de proveedor
        contexto["proveedor_sel"] = self.request.GET.get("proveedor", "")   # para dejar marcada la opción elegida
        contexto["tipo_pago"] = self.request.GET.get("tipo_pago", "")
        return contexto


class CompraDetallesMixin:
    """Lo que COMPARTEN crear y editar una compra: cabecera (form) + filas (formset)."""
    model = Compra
    form_class = CompraForm
    template_name = "facturacion/compra_form.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)      # trae "form" (la cabecera)
        if "detalles" not in contexto:                     # en GET el formset todavía no existe...
            contexto["detalles"] = DetalleCompraFormSet(instance=self.object)   # ...lo creamos (vacío o lleno)
        return contexto

    def post(self, request, *args, **kwargs):              # REEMPLAZA el post() normal de la vista
        form = self.get_form()                             # 1. cabecera con request.POST
        detalles = DetalleCompraFormSet(request.POST, instance=self.object)   # 2. filas con request.POST
        if form.is_valid() and detalles.is_valid():        # 3. ¿las DOS partes están bien?
            return self.form_valid(form, detalles)
        return self.form_invalid(form, detalles)

    def form_valid(self, form, detalles):
        with transaction.atomic():                         # TODO o NADA: si algo falla, se deshace todo
            if self.object:                                # al EDITAR: sacar de bodega lo que esta compra había metido
                self.object.revertir_stock()
            form.instance.user = self.request.user         # quién registra
            self.object = form.save()                      # INSERT o UPDATE de la cabecera
            self.guardar_detalles(detalles)                # INSERT / UPDATE / DELETE de las filas
            self.object.ingresar_stock()                   # mete a bodega lo comprado (el stock SUBE)
            self.object.calcular_totales()                 # subtotal, IVA y total
        messages.success(self.request, f"{self.object} guardada. Total: ${self.object.total}")
        return HttpResponseRedirect(self.get_success_url())

    def guardar_detalles(self, detalles):
        detalles.instance = self.object                    # las filas pertenecen a ESTA compra
        filas = detalles.save(commit=False)                # objetos nuevos o cambiados, SIN guardar todavía
        for fila in detalles.deleted_objects:              # filas con la casilla "Quitar"
            fila.delete()
        for fila in filas:
            fila.user = self.request.user                  # el precio (costo) ya viene del formulario
            fila.save()

    def form_invalid(self, form, detalles):
        messages.error(self.request, "Revisa los datos de la compra.")
        # volvemos a dibujar la página con la cabecera Y las filas, con sus errores
        return self.render_to_response(self.get_context_data(form=form, detalles=detalles))

    def get_success_url(self):
        return reverse("facturacion:compra_detalle", kwargs={"pk": self.object.pk})   # al detalle de la compra


class CompraCreateView(LoginRequiredMixin, CompraDetallesMixin, CreateView):   # CREAR
    extra_context = {"titulo": "Nueva compra", "boton": "Guardar compra"}

    def post(self, request, *args, **kwargs):
        self.object = None                                 # CreateView: aún no hay compra
        return super().post(request, *args, **kwargs)      # sigue al post() del mixin


class CompraUpdateView(LoginRequiredMixin, CompraDetallesMixin, UpdateView):   # EDITAR
    extra_context = {"titulo": "Editar compra", "boton": "Actualizar compra"}

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()                    # UpdateView: la compra del <int:pk>
        return super().post(request, *args, **kwargs)


class CompraDetailView(LoginRequiredMixin, DetailView):    # VER (el detalle de la compra)
    model = Compra
    template_name = "facturacion/compra_detalle.html"
    context_object_name = "compra"

    def get_queryset(self):
        return super().get_queryset().select_related("proveedor", "user").prefetch_related("detalles__producto")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["iva_porcentaje"] = IVA_TARIFA * 100      # 15
        return contexto


class CompraDeleteView(LoginRequiredMixin, DeleteView):    # ELIMINAR
    model = Compra
    template_name = "facturacion/compra_eliminar.html"
    context_object_name = "compra"
    success_url = reverse_lazy("facturacion:compra_lista")

    def form_valid(self, form):
        # Antes de revertir, comprobamos que el stock no quede negativo (si ya se vendió parte, no se puede)
        for detalle in self.object.detalles.select_related("producto"):
            if detalle.producto.stock < detalle.cantidad:
                messages.error(
                    self.request,
                    f"No se puede eliminar: de «{detalle.producto.nombre}» ya se vendieron unidades de esta compra.",
                )
                return redirect("facturacion:compra_detalle", pk=self.object.pk)
        with transaction.atomic():
            self.object.revertir_stock()                   # 1. el stock baja lo que había subido
            respuesta = super().form_valid(form)           # 2. DELETE de la compra (CASCADE borra sus detalles)
        messages.success(self.request, "Compra eliminada y stock revertido.")
        return respuesta


# =====================================================================
# MI PERFIL · UpdateView sin pk en la URL  (RETO)
# =====================================================================

class MiPerfilView(LoginRequiredMixin, UsuarioRegistroMixin, SuccessMessageMixin, UpdateView):
    model = Perfil
    form_class = PerfilForm
    template_name = "facturacion/mi_perfil.html"
    success_url = reverse_lazy("facturacion:mi_perfil")    # se queda en la misma página al guardar
    success_message = "Tu perfil se actualizó."
    extra_context = {"titulo": "Mi perfil", "boton": "Guardar perfil"}

    def get_object(self, queryset=None):                   # en vez de buscar por pk en la URL...
        perfil, creado = Perfil.objects.get_or_create(usuario=self.request.user)   # ...el del usuario conectado
        return perfil                                      # (si aún no tenía perfil, se crea vacío)
