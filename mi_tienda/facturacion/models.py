from django.contrib.auth.models import User      # User: el modelo de usuarios que YA trae Django (username, password, email...)
from django.db import models                     # models trae todos los tipos de campo


class Categoria(models.Model):                   # Hereda de models.Model → Django la convierte en tabla
    nombre = models.CharField(max_length=60, unique=True)   # Texto corto (máx. 60 letras) que NO se puede repetir
    descripcion = models.TextField(blank=True)   # Texto largo. blank=True: se puede dejar vacío en el formulario
    activo = models.BooleanField(default=True)   # Verdadero/Falso. Si no se indica, vale True

    class Meta:                                  # Opciones extra de la tabla
        verbose_name = "Categoría"               # Nombre bonito en singular (se ve en el admin)
        verbose_name_plural = "Categorías"       # Nombre bonito en plural
        ordering = ["nombre"]                    # Orden por defecto: alfabético por nombre

    def __str__(self):                           # Qué texto mostrar cuando se imprime el objeto
        return self.nombre                       # Ej: en una lista aparece "Laptops" y no "Categoria object (1)"


class Marca(models.Model):
    nombre = models.CharField(max_length=60, unique=True)              # Nombre único de la marca
    pais_origen = models.CharField("País de origen", max_length=60, blank=True)  # El primer texto es la etiqueta del formulario
    activo = models.BooleanField(default=True)                          # Activa por defecto

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=100)                           # Nombre del producto
    descripcion = models.TextField("Descripción", blank=True)           # Opcional
    precio = models.DecimalField(max_digits=10, decimal_places=2)       # Dinero: 10 dígitos en total, 2 decimales
    stock = models.PositiveIntegerField(default=0)                      # Número entero que no puede ser negativo

    # ---------- RELACIÓN UNO A MUCHOS (1:N) con Marca ----------
    # Cada producto tiene UNA marca; una marca tiene MUCHOS productos.
    # La ForeignKey va en el lado de los "muchos" (Producto). En la tabla crea la columna marca_id.
    marca = models.ForeignKey(
        Marca,                         # ¿Con qué modelo se relaciona? Con Marca
        on_delete=models.PROTECT,      # ¿Y si borran la marca? PROTECT: no deja borrarla mientras tenga productos
        related_name="productos",      # Nombre para ir al revés, de la marca a sus productos: marca.productos.all()
    )

    # ---------- RELACIÓN MUCHOS A MUCHOS (N:M) con Categoría ----------
    # Un producto puede estar en VARIAS categorías y una categoría tiene VARIOS productos.
    # No crea una columna aquí: Django crea una TABLA INTERMEDIA (facturacion_producto_categorias)
    # que guarda los pares producto_id – categoria_id. El nombre va en plural porque son varias.
    categorias = models.ManyToManyField(
        Categoria,                     # ¿Con qué modelo? Con Categoria
        related_name="productos",      # Al revés, de la categoría a sus productos: categoria.productos.all()
        blank=True,                    # El formulario permite guardar un producto sin ninguna categoría
    )                                  # (no lleva on_delete: si borras una categoría, solo se borran sus pares en la tabla intermedia)

    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)            # Guarda sola la fecha y hora al crear

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.marca})"                          # Ej: "Galaxy A55 (Samsung)"


class Cliente(models.Model):
    cedula = models.CharField("Cédula", max_length=10, unique=True)     # 10 caracteres, no se repite
    nombres = models.CharField(max_length=80)
    apellidos = models.CharField(max_length=80)
    email = models.EmailField("Correo", blank=True)                     # Revisa que tenga formato de correo
    telefono = models.CharField("Teléfono", max_length=15, blank=True)
    direccion = models.CharField("Dirección", max_length=200, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)            # Fecha de registro automática

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["apellidos", "nombres"]                             # Ordena por apellido y luego por nombre

    def __str__(self):
        return f"{self.apellidos} {self.nombres}"


class Perfil(models.Model):
    # User de Django solo guarda usuario, contraseña, nombre y correo.
    # Perfil guarda los datos EXTRA que necesita Mi Tienda para cada usuario.

    # ---------- RELACIÓN UNO A UNO (1:1) con User ----------
    # Un usuario tiene UN solo perfil y un perfil es de UN solo usuario.
    # Es como una ForeignKey que no se puede repetir: en la tabla crea la columna usuario_id (única).
    usuario = models.OneToOneField(
        User,                          # ¿Con qué modelo? Con el User de Django
        on_delete=models.CASCADE,      # Si se borra el usuario, se borra también su perfil (en cascada)
        related_name="perfil",         # Al revés, del usuario a su perfil: request.user.perfil
    )
    cedula = models.CharField("Cédula", max_length=10, blank=True)
    telefono = models.CharField("Teléfono", max_length=15, blank=True)
    direccion = models.CharField("Dirección", max_length=200, blank=True)
    cargo = models.CharField(max_length=50, blank=True)                 # Ej: Vendedor, Cajero, Administrador

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

    def __str__(self):
        return f"Perfil de {self.usuario.username}"                     # Ej: "Perfil de ana"