from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import (Categoria, Marca, Producto, Cliente, Proveedor, Perfil,
                     Venta, DetalleVenta, Compra, DetalleCompra)


# =====================================================================
# PRODUCTO
# =====================================================================
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        # user, fecha_creacion y fecha_modificacion NO van: los llena el sistema
        fields = ["nombre", "descripcion", "marca", "categorias", "precio", "stock", "imagen", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Galaxy A55"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "marca": forms.Select(attrs={"class": "form-select"}),                         # 1:N → una opción
            "categorias": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),  # N:M → varias
            "precio": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            # ClearableFileInput = <input type="file"> + casilla "Limpiar" para quitar la foto actual
            "imagen": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["marca"].queryset = Marca.objects.filter(activo=True)   # solo marcas activas
        self.fields["marca"].empty_label = "— Elige una marca —"

    def clean_precio(self):
        precio = self.cleaned_data["precio"]
        if precio <= 0:
            raise forms.ValidationError("El precio debe ser mayor que 0.")
        return precio


# =====================================================================
# VENTA: cabecera (maestro)
# =====================================================================
class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ["cliente", "fecha_hora", "tipo_pago"]   # subtotal, iva y total los calcula el sistema
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-select"}),
            # type="datetime-local" → el navegador muestra un calendario con hora
            "fecha_hora": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"},
                                              format="%Y-%m-%dT%H:%M"),
            "tipo_pago": forms.Select(attrs={"class": "form-select"}),   # las opciones salen de TipoPago
        }


# =====================================================================
# VENTA: filas del detalle
# =====================================================================
class ProductoConPrecioField(forms.ModelChoiceField):
    """Lista desplegable de productos que muestra también el precio y el stock."""
    def label_from_instance(self, obj):           # Django llama a este método para escribir cada <option>
        return f"{obj.nombre} · ${obj.precio} · stock: {obj.stock}"


class DetalleVentaForm(forms.ModelForm):
    producto = ProductoConPrecioField(
        queryset=Producto.objects.filter(activo=True),
        empty_label="— Elige un producto —",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = DetalleVenta
        fields = ["producto", "cantidad"]           # el precio NO: lo pone la vista con el precio actual
        widgets = {"cantidad": forms.NumberInput(attrs={"class": "form-control", "min": "1"})}


class BaseDetalleVentaFormSet(BaseInlineFormSet):
    """Validación de TODAS las filas juntas: ¿hay stock para lo que se pide?"""

    def clean(self):
        super().clean()                           # primero las validaciones normales de cada fila
        if any(self.errors):                      # si alguna fila ya tiene errores, no seguimos
            return

        pedido = {}                               # {producto: cantidad total pedida}
        for fila in self.forms:
            datos = fila.cleaned_data
            if not datos or datos.get("DELETE"):  # fila vacía o marcada para quitar → se ignora
                continue
            producto = datos["producto"]
            pedido[producto] = pedido.get(producto, 0) + datos["cantidad"]   # suma si el producto se repite

        anterior = {}                             # al EDITAR: lo que esta venta ya tenía reservado
        if self.instance.pk:
            for detalle in self.instance.detalles.all():
                anterior[detalle.producto_id] = anterior.get(detalle.producto_id, 0) + detalle.cantidad

        for producto, cantidad in pedido.items():
            disponible = producto.stock + anterior.get(producto.pk, 0)
            if cantidad > disponible:
                raise ValidationError(
                    f"Stock insuficiente de «{producto.nombre}»: pides {cantidad} y hay {disponible}."
                )


# inlineformset_factory crea una CLASE de formset: muchos DetalleVentaForm unidos a UNA Venta
DetalleVentaFormSet = inlineformset_factory(
    Venta,                                        # el maestro
    DetalleVenta,                                 # el detalle (tiene la ForeignKey venta)
    form=DetalleVentaForm,                        # el formulario de cada fila
    formset=BaseDetalleVentaFormSet,              # nuestra validación de stock
    extra=0,                                      # filas vacías extra (las agrega el botón con JavaScript)
    min_num=1,                                    # mínimo 1 fila...
    validate_min=True,                            # ...y se valida que exista
    can_delete=True,                              # cada fila tiene la casilla "Quitar"
)


# =====================================================================
# MARCA  (TAREA 1)
# =====================================================================
class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ["nombre", "pais_origen", "activo"]      # user y fechas los llena el sistema
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Samsung"}),
            "pais_origen": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Corea del Sur"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# =====================================================================
# CATEGORÍA  (TAREA 2)
# =====================================================================
class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Celulares"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),   # caja grande de texto
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# =====================================================================
# CLIENTE  (TAREA 3) · con validación de la cédula
# =====================================================================
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["cedula", "nombres", "apellidos", "email", "telefono", "direccion"]
        widgets = {
            "cedula": forms.TextInput(attrs={"class": "form-control", "maxlength": "10", "placeholder": "10 dígitos"}),
            "nombres": forms.TextInput(attrs={"class": "form-control"}),
            "apellidos": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_cedula(self):                           # Django llama clean_<campo>() al validar cada campo
        cedula = self.cleaned_data["cedula"].strip()
        if len(cedula) != 10 or not cedula.isdigit():  # exactamente 10 caracteres y todos números
            raise forms.ValidationError("La cédula debe tener exactamente 10 dígitos numéricos.")
        return cedula                                  # siempre se devuelve el valor ya limpio


# =====================================================================
# PROVEEDOR  (TAREA 4) · con logo y validación del RUC
# =====================================================================
class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombre", "apellido", "ruc", "email", "contacto", "logo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido": forms.TextInput(attrs={"class": "form-control"}),
            "ruc": forms.TextInput(attrs={"class": "form-control", "maxlength": "13", "placeholder": "13 dígitos, termina en 001"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "contacto": forms.TextInput(attrs={"class": "form-control"}),
            # ClearableFileInput: caja para subir archivo + casilla "Limpiar" para quitar el logo actual
            "logo": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }

    def clean_ruc(self):
        ruc = self.cleaned_data["ruc"].strip()
        if len(ruc) != 13 or not ruc.isdigit():        # 13 caracteres y solo números
            raise forms.ValidationError("El RUC debe tener exactamente 13 dígitos numéricos.")
        if not ruc.endswith("001"):                    # el RUC de una persona/empresa termina en 001
            raise forms.ValidationError("El RUC debe terminar en 001.")
        return ruc


# =====================================================================
# COMPRA: cabecera (maestro)  (TAREA 5)
# =====================================================================
class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ["proveedor", "fecha_hora", "tipo_pago"]    # subtotal, iva y total los calcula el sistema
        widgets = {
            "proveedor": forms.Select(attrs={"class": "form-select"}),
            "fecha_hora": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"},
                                              format="%Y-%m-%dT%H:%M"),
            "tipo_pago": forms.Select(attrs={"class": "form-select"}),
        }


# =====================================================================
# COMPRA: filas del detalle
# =====================================================================
class ProductoConStockField(forms.ModelChoiceField):
    """Lista desplegable de productos que muestra el nombre y el stock actual."""
    def label_from_instance(self, obj):
        return f"{obj.nombre} · stock: {obj.stock}"


class DetalleCompraForm(forms.ModelForm):
    producto = ProductoConStockField(
        queryset=Producto.objects.filter(activo=True),
        empty_label="— Elige un producto —",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = DetalleCompra
        # A diferencia de la venta, aquí el precio (costo) SÍ lo escribe la persona: va en fields
        fields = ["producto", "cantidad", "precio"]
        widgets = {
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "precio": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01"}),
        }

    def clean_precio(self):
        precio = self.cleaned_data["precio"]
        if precio <= 0:                                # un costo de 0 o negativo no tiene sentido
            raise forms.ValidationError("El costo unitario debe ser mayor que 0.")
        return precio


class BaseDetalleCompraFormSet(BaseInlineFormSet):
    """RETO: al EDITAR una compra se revierte su stock; no puede quedar negativo."""

    def clean(self):
        super().clean()                                # primero las validaciones normales de cada fila
        if any(self.errors):                           # si ya hay errores en alguna fila, no seguimos
            return
        if not self.instance.pk:                       # compra NUEVA: no hay nada que revertir
            return

        anterior = {}                                  # {producto: unidades que esta compra había ingresado}
        for detalle in self.instance.detalles.select_related("producto"):
            anterior[detalle.producto] = anterior.get(detalle.producto, 0) + detalle.cantidad

        for producto, cantidad in anterior.items():
            if producto.stock < cantidad:              # stock actual - lo que se revierte < 0
                raise ValidationError(
                    f"No se puede editar: de «{producto.nombre}» ya se vendieron unidades de esta compra "
                    f"(stock {producto.stock}, la compra ingresó {cantidad})."
                )


# inlineformset_factory: muchos DetalleCompraForm unidos a UNA Compra
DetalleCompraFormSet = inlineformset_factory(
    Compra,                                            # el maestro
    DetalleCompra,                                     # el detalle (tiene la ForeignKey compra)
    form=DetalleCompraForm,                            # el formulario de cada fila
    formset=BaseDetalleCompraFormSet,                  # nuestra validación del reto
    extra=0,                                           # las filas nuevas las agrega el botón con JavaScript
    min_num=1,                                         # mínimo 1 fila...
    validate_min=True,                                 # ...y se valida que exista
    can_delete=True,                                   # casilla "Quitar" en cada fila
)


# =====================================================================
# MI PERFIL  (RETO)
# =====================================================================
class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["cedula", "telefono", "cargo"]       # "usuario" NO va: siempre es quien tiene la sesión
        widgets = {
            "cedula": forms.TextInput(attrs={"class": "form-control", "maxlength": "10"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "cargo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Vendedor"}),
        }

    def clean_cedula(self):
        cedula = self.cleaned_data["cedula"].strip()
        if cedula and (len(cedula) != 10 or not cedula.isdigit()):   # es opcional, pero si la escribe, debe ser válida
            raise forms.ValidationError("La cédula debe tener exactamente 10 dígitos numéricos.")
        return cedula
