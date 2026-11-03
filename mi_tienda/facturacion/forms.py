from django import forms
from .models import Marca, Categoria, Producto, Cliente   # ← ¡Aquí agregamos Cliente!

class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ["nombre", "pais_origen", "activo"]
        labels = {
            "nombre": "Nombre de la marca",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Samsung"}),
            "pais_origen": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Corea del Sur"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        if len(nombre) < 2:
            raise forms.ValidationError("El nombre debe tener al menos 2 letras.")
        return nombre.title()


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ProductoForm(forms.ModelForm):                     
    class Meta:
        model = Producto                                 
        fields = ["nombre", "descripcion", "marca", "categorias", "precio", "stock", "activo"]  
        widgets = {                                      
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Laptop Pro 14"}),  
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),   
            "marca": forms.Select(attrs={"class": "form-select"}),       # 1:N → lista desplegable
            "categorias": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}), # N:M → casillas múltiples
            "precio": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),  
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),     
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),         
        }

    def clean_precio(self):                              # Validación propia: el precio no puede ser 0 o negativo
        precio = self.cleaned_data["precio"]             
        if precio <= 0:                                  
            raise forms.ValidationError("El precio debe ser mayor que 0.")   
        return precio

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["cedula", "nombres", "apellidos", "email", "telefono", "direccion"]
        widgets = {
            "cedula": forms.TextInput(attrs={"class": "form-control"}),
            "nombres": forms.TextInput(attrs={"class": "form-control"}),
            "apellidos": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
        }