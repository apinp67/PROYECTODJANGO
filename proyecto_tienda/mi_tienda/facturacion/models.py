# =====================================================================
# facturacion/models.py
# Recuerda: cada CLASE es una TABLA, cada ATRIBUTO es una COLUMNA, cada OBJETO es una FILA.
# Nombre de cada tabla en la base de datos: <app>_<modelo>  →  facturacion_producto
# =====================================================================
from decimal import Decimal                      # Decimal: números exactos (para dinero nunca usamos float)

from django.contrib.auth.models import User      # La tabla de usuarios que YA trae Django (auth_user)
from django.core.validators import MinValueValidator   # Regla: "el valor debe ser al menos N"
from django.db import models                     # models.Model y todos los tipos de campo
from django.db.models import F                   # F("campo"): usa el valor que está EN la base de datos
from django.utils import timezone                # timezone.now(): fecha y hora actual con zona horaria

IVA_TARIFA = Decimal("0.15")                     # IVA de Ecuador: 15 %. Si cambia, solo cambias esta línea
DOS_DECIMALES = Decimal("0.01")                  # Para redondear el dinero a 2 decimales


# ---------------------------------------------------------------------
# MODELO BASE (abstracto)
# Guarda 3 datos que TODAS las tablas necesitan: quién registró y cuándo.
# abstract = True → NO crea tabla. Sus campos se COPIAN en cada modelo que hereda de él.
# ---------------------------------------------------------------------
class ModeloBase(models.Model):
    user = models.ForeignKey(                    # 1:N con User: un usuario registra muchos registros
        User,
        on_delete=models.SET_NULL,               # Si borran al usuario, el registro se queda con user vacío
        null=True,                               # SET_NULL necesita que la columna acepte NULL
        blank=True,
        editable=False,                          # No aparece en formularios: lo llena la VISTA, no la persona
        related_name="%(class)s_registrados",    # %(class)s = nombre del modelo → user.producto_registrados
        verbose_name="Registrado por",
    )
    fecha_creacion = models.DateTimeField("Fecha de creación", auto_now_add=True)   # Se llena sola al CREAR
    fecha_modificacion = models.DateTimeField("Última modificación", auto_now=True) # Se actualiza sola en CADA save()

    class Meta:
        abstract = True                          # ← LA CLAVE: modelo "molde", sin tabla propia


# ---------------------------------------------------------------------
# OPCIONES DE PAGO (choices)
# TextChoices crea una lista fija de opciones: valor que se guarda + texto que se muestra.
# ---------------------------------------------------------------------
class TipoPago(models.TextChoices):
    CONTADO = "contado", "Contado"               # se guarda "contado", se muestra "Contado"
    CREDITO = "credito", "Crédito"
    TRANSFERENCIA = "transferencia", "Transferencia"
    TARJETA = "tarjeta", "Tarjeta"


# =====================================================================
# CATÁLOGO
# =====================================================================
class Categoria(ModeloBase):                     # Hereda de ModeloBase (y este de models.Model)
    nombre = models.CharField(max_length=60, unique=True)
    descripcion = models.TextField("Descripción", blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Marca(ModeloBase):
    nombre = models.CharField(max_length=60, unique=True)
    pais_origen = models.CharField("País de origen", max_length=60, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(ModeloBase):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField("Descripción", blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)    # Precio de VENTA actual
    stock = models.PositiveIntegerField(default=0)                   # Unidades en bodega (nunca negativo)
    imagen = models.ImageField(                  # NUEVO: guarda una FOTO
        upload_to="productos/",                  #   el archivo va a MEDIA_ROOT/productos/
        blank=True,                              #   la foto es opcional
    )                                            #   En la tabla solo se guarda el TEXTO de la ruta: "productos/a55.jpg"

    # 1:N con Marca → columna marca_id
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name="productos")
    # N:M con Categoria → tabla intermedia facturacion_producto_categorias (la crea Django)
    categorias = models.ManyToManyField(Categoria, related_name="productos", blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


# =====================================================================
# PERSONAS
# =====================================================================
class Cliente(ModeloBase):
    cedula = models.CharField("Cédula", max_length=10, unique=True)
    nombres = models.CharField(max_length=80)
    apellidos = models.CharField(max_length=80)
    email = models.EmailField("Correo", blank=True)
    telefono = models.CharField("Teléfono", max_length=15, blank=True)
    direccion = models.CharField("Dirección", max_length=200, blank=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return f"{self.apellidos} {self.nombres}"


class Proveedor(ModeloBase):                     # NUEVO
    nombre = models.CharField(max_length=80)
    apellido = models.CharField(max_length=80)
    ruc = models.CharField("RUC", max_length=13, unique=True)        # RUC de Ecuador: 13 dígitos
    email = models.EmailField("Correo", blank=True)
    contacto = models.CharField("Teléfono de contacto", max_length=15, blank=True)
    logo = models.ImageField(upload_to="proveedores/", blank=True)   # Archivo en MEDIA_ROOT/proveedores/

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["nombre", "apellido"]

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Perfil(ModeloBase):
    # 1:1 con User: los datos extra del usuario. OJO: no confundir con "user" del ModeloBase:
    #   usuario → DE QUIÉN es el perfil       user → QUIÉN lo registró
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    cedula = models.CharField("Cédula", max_length=10, blank=True)
    telefono = models.CharField("Teléfono", max_length=15, blank=True)
    cargo = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


# =====================================================================
# VENTAS: maestro (Venta) y detalle (DetalleVenta)
# Una venta tiene MUCHAS filas de detalle; cada fila es UN producto con su cantidad y su precio.
# =====================================================================
class Venta(ModeloBase):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="ventas")   # 1:N
    fecha_hora = models.DateTimeField("Fecha y hora", default=timezone.now)   # default: la hora actual, editable
    # Los totales NO los escribe la persona: los calcula el sistema (editable=False → fuera de los formularios)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    iva = models.DecimalField("IVA", max_digits=12, decimal_places=2, default=0, editable=False)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    tipo_pago = models.CharField(
        "Tipo de pago",
        max_length=15,
        choices=TipoPago.choices,                # Solo acepta contado, credito, transferencia o tarjeta
        default=TipoPago.CONTADO,
    )

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ["-fecha_hora"]               # La más reciente primero

    def __str__(self):
        return f"Venta #{self.pk}"

    # ---------- MÉTODOS: la lógica del negocio vive en el modelo ----------
    def calcular_totales(self):
        """Suma los detalles y guarda subtotal, IVA y total."""
        subtotal = sum((d.subtotal for d in self.detalles.all()), Decimal("0"))   # Σ cantidad × precio
        self.subtotal = subtotal.quantize(DOS_DECIMALES)                          # redondea a 2 decimales
        self.iva = (self.subtotal * IVA_TARIFA).quantize(DOS_DECIMALES)
        self.total = self.subtotal + self.iva
        self.save(update_fields=["subtotal", "iva", "total", "fecha_modificacion"])  # UPDATE solo de estas columnas

    def descontar_stock(self):
        """Saca de la bodega las unidades vendidas."""
        for detalle in self.detalles.all():
            # UPDATE producto SET stock = stock - cantidad  (lo resta la base de datos, sin leer antes)
            Producto.objects.filter(pk=detalle.producto_id).update(stock=F("stock") - detalle.cantidad)

    def devolver_stock(self):
        """Lo contrario: regresa a la bodega las unidades (al editar o eliminar la venta)."""
        for detalle in self.detalles.all():
            Producto.objects.filter(pk=detalle.producto_id).update(stock=F("stock") + detalle.cantidad)


class DetalleVenta(ModeloBase):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")   # se borra con su venta
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="detalles_venta")
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])  # mínimo 1
    precio = models.DecimalField(max_digits=10, decimal_places=2)   # precio del producto EL DÍA de la venta

    class Meta:
        verbose_name = "Detalle de venta"
        verbose_name_plural = "Detalles de venta"

    def __str__(self):
        return f"{self.cantidad} × {self.producto}"

    @property                                    # @property: se usa como atributo, sin paréntesis: detalle.subtotal
    def subtotal(self):
        return self.cantidad * self.precio       # NO se guarda en la tabla: se calcula cada vez


# =====================================================================
# COMPRAS: el espejo de las ventas, pero el stock SUBE
# =====================================================================
class Compra(ModeloBase):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name="compras")
    fecha_hora = models.DateTimeField("Fecha y hora", default=timezone.now)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    iva = models.DecimalField("IVA", max_digits=12, decimal_places=2, default=0, editable=False)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    tipo_pago = models.CharField("Tipo de pago", max_length=15, choices=TipoPago.choices, default=TipoPago.CONTADO)

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"Compra #{self.pk}"

    def calcular_totales(self):
        subtotal = sum((d.subtotal for d in self.detalles.all()), Decimal("0"))
        self.subtotal = subtotal.quantize(DOS_DECIMALES)
        self.iva = (self.subtotal * IVA_TARIFA).quantize(DOS_DECIMALES)
        self.total = self.subtotal + self.iva
        self.save(update_fields=["subtotal", "iva", "total", "fecha_modificacion"])

    def ingresar_stock(self):
        """Mete a la bodega las unidades compradas (el stock SUBE)."""
        for detalle in self.detalles.all():
            Producto.objects.filter(pk=detalle.producto_id).update(stock=F("stock") + detalle.cantidad)

    def revertir_stock(self):
        """Saca de la bodega lo que había entrado (al editar o eliminar la compra)."""
        for detalle in self.detalles.all():
            Producto.objects.filter(pk=detalle.producto_id).update(stock=F("stock") - detalle.cantidad)


class DetalleCompra(ModeloBase):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="detalles_compra")
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    precio = models.DecimalField("Costo unitario", max_digits=10, decimal_places=2)   # lo que cobró el proveedor

    class Meta:
        verbose_name = "Detalle de compra"
        verbose_name_plural = "Detalles de compra"

    def __str__(self):
        return f"{self.cantidad} × {self.producto}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio
