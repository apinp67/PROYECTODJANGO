from django.contrib import messages                                  # mensajes
from django.contrib.auth import login, logout                      # abrir y cerrar sesión
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Sum                                   # SUM() de SQL
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView                      # NUEVO: VBC que muestra un template

from facturacion.models import Producto, Venta                     # NUEVO: para los números del inicio


# =====================================================================
# INICIO · tu primera Vista Basada en Clases
# =====================================================================
class InicioView(TemplateView):                    # TemplateView: "muestra un template con datos"
    template_name = "home.html"                    # ATRIBUTO: ¿qué HTML?

    def get_context_data(self, **kwargs):          # MÉTODO: ¿qué datos recibe el HTML?
        contexto = super().get_context_data(**kwargs)   # 1. lo que TemplateView ya prepara
        hoy = timezone.localdate()                      # 2. la fecha de hoy en Ecuador
        ventas_hoy = Venta.objects.filter(fecha_hora__date=hoy)
        contexto["total_productos"] = Producto.objects.filter(activo=True).count()
        contexto["ventas_hoy"] = ventas_hoy.count()
        contexto["vendido_hoy"] = ventas_hoy.aggregate(suma=Sum("total"))["suma"] or 0   # SUM(total)
        contexto["stock_bajo"] = Producto.objects.filter(activo=True, stock__lt=5)        # menos de 5 unidades
        return contexto                                 # 3. entregamos todo


# =====================================================================
# AUTENTICACIÓN · se queda en funciones (VBF), como en la guía anterior
# =====================================================================

def ingresar(request):                                     # LOGIN
    if request.user.is_authenticated:                      # ya inició sesión → al inicio
        return redirect("home")
    siguiente = request.POST.get("next") or request.GET.get("next") or ""   # la página que quería ver
    if request.method == "POST":                           # presionó "Ingresar"
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():                                # usuario y clave correctos
            login(request, form.get_user())                # abre la sesión
            if siguiente and url_has_allowed_host_and_scheme(siguiente, allowed_hosts={request.get_host()}):
                return redirect(siguiente)
            return redirect("home")
    else:                                                  # GET: formulario vacío
        form = AuthenticationForm(request)
    return render(request, "registration/login.html", {"form": form, "next": siguiente})


@require_POST                                              # cerrar sesión SOLO con POST
def salir(request):                                        # LOGOUT
    logout(request)
    messages.info(request, "Cerraste sesión.")
    return redirect("login")


def registro(request):                                     # CREAR CUENTA
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()                          # crea el usuario con la clave cifrada
            login(request, usuario)
            messages.success(request, f"¡Bienvenido, {usuario.username}!")
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "registration/registro.html", {"form": form})
