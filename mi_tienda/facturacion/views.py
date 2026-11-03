from django.contrib import messages                        # Para mostrar mensajes de éxito o error
from django.db.models import ProtectedError                # Error que sale al borrar una marca con productos
from django.shortcuts import render, redirect, get_object_or_404   # render: mostrar página; redirect: ir a otra; get_object_or_404: buscar o mostrar 404

# --- NUEVOS IMPORTS PARA CLASES ---
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .forms import MarcaForm, CategoriaForm, ProductoForm, ClienteForm  # ← ¡Agregamos ClienteForm!
from .models import Marca, Categoria, Producto, Cliente                 # ← ¡Agregamos Cliente!


# =====================================================================
# MARCAS · Vistas Basadas en Funciones (VBF)
# =====================================================================

def marca_lista(request):                                  # READ: muestra todas las marcas
    q = request.GET.get("q", "")                           # 1. Leemos el buscador: /facturacion/marcas/?q=sam (si no hay, queda "")
    marcas = Marca.objects.all()                           # 2. Pedimos todas las marcas a la base de datos

    if q:                                                  # 3. Si el usuario escribió algo en el buscador...
        marcas = marcas.filter(nombre__icontains=q)        #    ...dejamos solo las que contienen ese texto

    contexto = {                                           # 4. Datos que enviamos al template
        "titulo": "Marcas",                                #    → {{ titulo }}
        "marcas": marcas,                                  #    → {% for marca in marcas %}
        "q": q,                                            #    → para que el buscador no se borre
    }
    return render(request, "facturacion/marca_lista.html", contexto)   # 5. Mostramos la página

def marca_crear(request):                                  # CREATE: crear una marca nueva
    if request.method == "POST":                           # ¿El usuario presionó "Guardar"? (llegó por POST)
        form = MarcaForm(request.POST)                     # 1. Llenamos el formulario con lo que escribió
        if form.is_valid():                                # 2. ¿Los datos están bien? (obligatorios, únicos, clean_nombre)
            marca = form.save()                            # 3. Guardamos en la base de datos (save devuelve la marca)
            messages.success(request, f"Marca «{marca.nombre}» creada correctamente.")   # 4. Mensaje verde
            return redirect("facturacion:marca_lista")     # 5. Vamos a la lista. Así, si recarga, no se guarda dos veces
        # Si NO es válido, no entra al if: baja hasta el render y muestra el formulario CON errores

    else:                                                  # Si llegó por GET (solo abrió la página)...
        form = MarcaForm()                                 # ...creamos un formulario vacío

    contexto = {                                           # Datos para el template
        "titulo": "Nueva marca",                           # Título de la página
        "form": form,                                      # El formulario (vacío o con errores)
        "boton": "Guardar",                                # Texto del botón
    }
    return render(request, "facturacion/marca_form.html", contexto)

def marca_editar(request, pk):                             # UPDATE. pk llega desde la URL: /marcas/editar/3/ → pk=3
    marca = get_object_or_404(Marca, pk=pk)                # 1. Buscamos la marca. Si no existe → página 404

    if request.method == "POST":                           # 2. ¿Presionó "Actualizar"?
        form = MarcaForm(request.POST, instance=marca)     #    Datos nuevos + la marca que vamos a cambiar
        if form.is_valid():                                #    ¿Están bien?
            form.save()                                    #    Actualiza (UPDATE), no crea una nueva
            messages.success(request, f"Marca «{marca.nombre}» actualizada.")
            return redirect("facturacion:marca_lista")     #    Volvemos a la lista
    else:                                                  # 3. Llegó por GET...
        form = MarcaForm(instance=marca)                   #    ...formulario lleno con los datos actuales

    contexto = {
        "titulo": f"Editar marca: {marca.nombre}",
        "form": form,
        "boton": "Actualizar",
    }
    return render(request, "facturacion/marca_form.html", contexto)   # ¡El mismo template de crear!


def marca_eliminar(request, pk):                           # DELETE
    marca = get_object_or_404(Marca, pk=pk)                # Buscamos la marca o mostramos 404

    if request.method == "POST":                           # ¿Presionó "Sí, eliminar"?
        try:                                               # Intentamos borrar...
            nombre = marca.nombre                          # Guardamos el nombre para el mensaje
            marca.delete()                                 # DELETE en la base de datos
            messages.success(request, f"Marca «{nombre}» eliminada.")
        except ProtectedError:                             # ...si tiene productos, PROTECT no deja borrarla
            messages.error(request, f"No se puede eliminar «{marca.nombre}» porque tiene productos. Desactívala en su lugar.")
        return redirect("facturacion:marca_lista")         # En los dos casos volvemos a la lista

    # Si llegó por GET: mostramos la pregunta "¿Seguro?"
    contexto = {"titulo": "Eliminar marca", "marca": marca}
    return render(request, "facturacion/marca_eliminar.html", contexto)

# =====================================================================
# CATEGORÍAS · Vistas Basadas en Funciones (VBF)
# =====================================================================

def categoria_lista(request):
    q = request.GET.get("q", "")
    categorias = Categoria.objects.all()
    if q:
        categorias = categorias.filter(nombre__icontains=q)
    contexto = {
        "titulo": "Categorías",
        "categorias": categorias,
        "q": q,
    }
    return render(request, "facturacion/categoria_lista.html", contexto)

def categoria_crear(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f"Categoría «{categoria.nombre}» creada.")
            return redirect("facturacion:categoria_lista")
    else:
        form = CategoriaForm()
    
    contexto = {"titulo": "Nueva categoría", "form": form, "boton": "Guardar"}
    return render(request, "facturacion/categoria_form.html", contexto)

def categoria_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, f"Categoría «{categoria.nombre}» actualizada.")
            return redirect("facturacion:categoria_lista")
    else:
        form = CategoriaForm(instance=categoria)
        
    contexto = {"titulo": f"Editar categoría: {categoria.nombre}", "form": form, "boton": "Actualizar"}
    return render(request, "facturacion/categoria_form.html", contexto)

def categoria_eliminar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        nombre = categoria.nombre
        categoria.delete()
        messages.success(request, f"Categoría «{nombre}» eliminada.")
        return redirect("facturacion:categoria_lista")
        
    contexto = {"titulo": "Eliminar categoría", "categoria": categoria}
    return render(request, "facturacion/categoria_eliminar.html", contexto)


# =====================================================================
# PRODUCTOS · Vistas Basadas en Clases (VBC)
# =====================================================================

class ProductoListView(ListView):                          # READ (Listar)
    model = Producto
    template_name = "facturacion/producto_lista.html"      # A qué HTML va
    context_object_name = "productos"                      # Cómo se llama la lista en el HTML
    paginate_by = 5                                        # ¡Magia! Django pagina de 5 en 5 automático

    def get_queryset(self):                                # Buscador
        queryset = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(nombre__icontains=q)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Productos"
        context["q"] = self.request.GET.get("q", "")
        return context


class ProductoCreateView(CreateView):                      # CREATE (Crear)
    model = Producto
    form_class = ProductoForm
    template_name = "facturacion/producto_form.html"       # Reciclamos un solo HTML para form
    success_url = reverse_lazy("facturacion:producto_lista") # A dónde va al terminar

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nuevo producto"
        context["boton"] = "Guardar"
        return context

    def form_valid(self, form):                            # Mensaje verde al guardar
        messages.success(self.request, f"Producto «{form.instance.nombre}» creado.")
        return super().form_valid(form)


class ProductoUpdateView(UpdateView):                      # UPDATE (Editar)
    model = Producto
    form_class = ProductoForm
    template_name = "facturacion/producto_form.html"
    success_url = reverse_lazy("facturacion:producto_lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = f"Editar producto: {self.object.nombre}"
        context["boton"] = "Actualizar"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Producto «{form.instance.nombre}» actualizado.")
        return super().form_valid(form)


class ProductoDeleteView(DeleteView):                      # DELETE (Eliminar)
    model = Producto
    template_name = "facturacion/producto_eliminar.html"
    success_url = reverse_lazy("facturacion:producto_lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Eliminar producto"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Producto «{self.object.nombre}» eliminado.")
        return super().form_valid(form)

# =====================================================================
# CLIENTES · Vistas Basadas en Clases (VBC)
# =====================================================================

class ClienteListView(ListView):
    model = Cliente
    template_name = "facturacion/cliente_lista.html"
    context_object_name = "clientes"
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(nombres__icontains=q) # Buscará por nombres
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Clientes"
        context["q"] = self.request.GET.get("q", "")
        return context


class ClienteCreateView(CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "facturacion/cliente_form.html"
    success_url = reverse_lazy("facturacion:cliente_lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nuevo cliente"
        context["boton"] = "Guardar"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Cliente «{form.instance.nombres} {form.instance.apellidos}» creado.")
        return super().form_valid(form)


class ClienteUpdateView(UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "facturacion/cliente_form.html"
    success_url = reverse_lazy("facturacion:cliente_lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = f"Editar cliente: {self.object.nombres} {self.object.apellidos}"
        context["boton"] = "Actualizar"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Cliente «{form.instance.nombres} {form.instance.apellidos}» actualizado.")
        return super().form_valid(form)


class ClienteDeleteView(DeleteView):
    model = Cliente
    template_name = "facturacion/cliente_eliminar.html"
    success_url = reverse_lazy("facturacion:cliente_lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Eliminar cliente"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Cliente «{self.object.nombres} {self.object.apellidos}» eliminado.")
        return super().form_valid(form)