# =====================================================================
# facturacion/tests.py · pruebas automáticas del sistema
# Se ejecutan con:  python manage.py test
# Django crea una base de datos temporal, así que NO toca tus datos reales.
# =====================================================================
import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Categoria, Cliente, Compra, Marca, Perfil, Producto, Proveedor, Venta

MEDIA_TEMPORAL = tempfile.mkdtemp()          # carpeta temporal para las imágenes de prueba

def png_valido():
    """Genera una imagen PNG real de 4x4 píxeles (así Pillow la acepta como imagen válida)."""
    from io import BytesIO
    from PIL import Image
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "#4f46e5").save(buffer, "PNG")
    return buffer.getvalue()


def formset(prefijo, filas, iniciales=0):
    """Arma los datos POST de un formset (campos de control + una entrada por fila)."""
    datos = {f"{prefijo}-TOTAL_FORMS": len(filas), f"{prefijo}-INITIAL_FORMS": iniciales,
             f"{prefijo}-MIN_NUM_FORMS": 1, f"{prefijo}-MAX_NUM_FORMS": 1000}
    for i, fila in enumerate(filas):
        for campo, valor in fila.items():
            datos[f"{prefijo}-{i}-{campo}"] = valor
    return datos


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class SistemaTests(TestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)

    def setUp(self):
        self.usuario = User.objects.create_user("tester", password="Clave12345")
        self.client.login(username="tester", password="Clave12345")
        self.marca = Marca.objects.create(nombre="Samsung")
        self.categoria = Categoria.objects.create(nombre="Celulares")
        self.producto = Producto.objects.create(nombre="Galaxy", marca=self.marca, precio=Decimal("100.00"), stock=0)
        self.cliente = Cliente.objects.create(cedula="0912345678", nombres="Ana", apellidos="Loor")
        self.proveedor = Proveedor.objects.create(nombre="Luis", apellido="Andrade", ruc="0991234567001")

    # ---------- acceso ----------
    def test_sin_sesion_redirige_al_login(self):
        self.client.logout()
        r = self.client.get(reverse("facturacion:producto_lista"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login/", r.url)

    def test_todas_las_listas_y_formularios_cargan(self):
        nombres = ["producto_lista", "producto_crear", "venta_lista", "venta_crear", "marca_lista", "marca_crear",
                   "categoria_lista", "categoria_crear", "cliente_lista", "cliente_crear", "proveedor_lista",
                   "proveedor_crear", "compra_lista", "compra_crear", "mi_perfil"]
        for nombre in nombres:
            self.assertEqual(self.client.get(reverse(f"facturacion:{nombre}")).status_code, 200, nombre)
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_registro_crea_cuenta_e_inicia_sesion(self):
        self.client.logout()
        r = self.client.post(reverse("registro"), {"username": "nuevo", "password1": "Clave-Segura-77", "password2": "Clave-Segura-77"})
        self.assertRedirects(r, reverse("home"))
        self.assertTrue(User.objects.filter(username="nuevo").exists())

    # ---------- marca / categoría ----------
    def test_marca_crud_y_proteccion(self):
        r = self.client.post(reverse("facturacion:marca_crear"), {"nombre": "Apple", "pais_origen": "EE.UU.", "activo": "on"})
        self.assertRedirects(r, reverse("facturacion:marca_lista"))
        self.assertEqual(Marca.objects.get(nombre="Apple").user, self.usuario)        # UsuarioRegistroMixin
        # Samsung tiene un producto → no se puede eliminar (ProtectedError atrapado)
        self.client.post(reverse("facturacion:marca_eliminar", args=[self.marca.pk]))
        self.assertTrue(Marca.objects.filter(pk=self.marca.pk).exists())
        # Apple no tiene productos → sí se elimina
        self.client.post(reverse("facturacion:marca_eliminar", args=[Marca.objects.get(nombre="Apple").pk]))
        self.assertFalse(Marca.objects.filter(nombre="Apple").exists())

    def test_categoria_se_elimina_sin_borrar_productos(self):
        self.producto.categorias.add(self.categoria)
        self.client.post(reverse("facturacion:categoria_eliminar", args=[self.categoria.pk]))
        self.assertFalse(Categoria.objects.filter(pk=self.categoria.pk).exists())
        self.assertTrue(Producto.objects.filter(pk=self.producto.pk).exists())      # el producto sigue

    # ---------- cliente ----------
    def test_cliente_valida_cedula(self):
        datos = {"nombres": "Pedro", "apellidos": "Gil", "cedula": "123"}
        r = self.client.post(reverse("facturacion:cliente_crear"), datos)
        self.assertEqual(r.status_code, 200)                                          # vuelve al formulario con error
        self.assertFalse(Cliente.objects.filter(apellidos="Gil").exists())
        datos["cedula"] = "12345abcde"
        self.client.post(reverse("facturacion:cliente_crear"), datos)
        self.assertFalse(Cliente.objects.filter(apellidos="Gil").exists())
        datos["cedula"] = "0987654321"
        self.client.post(reverse("facturacion:cliente_crear"), datos)
        self.assertTrue(Cliente.objects.filter(apellidos="Gil").exists())

    def test_cliente_buscador_y_detalle(self):
        r = self.client.get(reverse("facturacion:cliente_lista"), {"q": "0912"})      # busca por cédula
        self.assertContains(r, "Loor")
        r = self.client.get(reverse("facturacion:cliente_lista"), {"q": "zzzz"})
        self.assertNotContains(r, "Loor")
        self.assertEqual(self.client.get(reverse("facturacion:cliente_detalle", args=[self.cliente.pk])).status_code, 200)

    def test_cliente_con_ventas_no_se_elimina(self):
        self._crear_venta_directa(1)
        self.client.post(reverse("facturacion:cliente_eliminar", args=[self.cliente.pk]))
        self.assertTrue(Cliente.objects.filter(pk=self.cliente.pk).exists())

    # ---------- proveedor ----------
    def test_proveedor_valida_ruc_y_sube_logo(self):
        base = {"nombre": "Eva", "apellido": "Paz", "email": "", "contacto": ""}
        for ruc_malo in ("123", "0991234567002", "09912345670ab"):                    # corto / no termina en 001 / letras
            self.client.post(reverse("facturacion:proveedor_crear"), {**base, "ruc": ruc_malo})
            self.assertFalse(Proveedor.objects.filter(apellido="Paz").exists(), ruc_malo)
        r = self.client.post(reverse("facturacion:proveedor_crear"),
                             {**base, "ruc": "1790123456001", "logo": SimpleUploadedFile("logo.png", png_valido(), "image/png")})
        self.assertRedirects(r, reverse("facturacion:proveedor_lista"))
        self.assertTrue(Proveedor.objects.get(apellido="Paz").logo.name.startswith("proveedores/"))

    # ---------- compras: el stock SUBE ----------
    def _datos_compra(self, filas, iniciales=0):
        return {"proveedor": self.proveedor.pk, "fecha_hora": "2026-01-15T10:30", "tipo_pago": "contado",
                **formset("detalles", filas, iniciales)}

    def test_compra_sube_stock_se_edita_y_se_elimina(self):
        r = self.client.post(reverse("facturacion:compra_crear"),
                             self._datos_compra([{"producto": self.producto.pk, "cantidad": 10, "precio": "50.00"}]))
        compra = Compra.objects.get()
        self.assertRedirects(r, reverse("facturacion:compra_detalle", args=[compra.pk]))
        self.producto.refresh_from_db(); self.assertEqual(self.producto.stock, 10)    # 0 + 10
        self.assertEqual((compra.subtotal, compra.iva, compra.total), (Decimal("500.00"), Decimal("75.00"), Decimal("575.00")))

        detalle = compra.detalles.get()                                               # editar: 10 → 4
        self.client.post(reverse("facturacion:compra_editar", args=[compra.pk]), self._datos_compra(
            [{"id": detalle.pk, "compra": compra.pk, "producto": self.producto.pk, "cantidad": 4, "precio": "50.00"}], 1))
        self.producto.refresh_from_db(); self.assertEqual(self.producto.stock, 4)
        compra.refresh_from_db(); self.assertEqual(compra.total, Decimal("230.00"))   # 200 + 15 % de IVA

        self.client.post(reverse("facturacion:compra_eliminar", args=[compra.pk]))
        self.producto.refresh_from_db(); self.assertEqual(self.producto.stock, 0)     # se revierte
        self.assertEqual(Compra.objects.count(), 0)

    def test_compra_ya_vendida_no_se_elimina_ni_se_edita(self):
        self.client.post(reverse("facturacion:compra_crear"),
                         self._datos_compra([{"producto": self.producto.pk, "cantidad": 10, "precio": "50.00"}]))
        compra = Compra.objects.get()
        self._crear_venta_directa(8)                                                  # quedan 2 en bodega
        self.client.post(reverse("facturacion:compra_eliminar", args=[compra.pk]))
        self.assertTrue(Compra.objects.filter(pk=compra.pk).exists())                 # bloqueado
        detalle = compra.detalles.get()
        r = self.client.post(reverse("facturacion:compra_editar", args=[compra.pk]), self._datos_compra(
            [{"id": detalle.pk, "compra": compra.pk, "producto": self.producto.pk, "cantidad": 3, "precio": "50.00"}], 1))
        self.assertEqual(r.status_code, 200)                                          # error de validación (reto)
        self.producto.refresh_from_db(); self.assertEqual(self.producto.stock, 2)     # nada cambió

    # ---------- ventas: el stock BAJA ----------
    def _crear_venta_directa(self, cantidad):
        """Crea una venta usando la misma lógica del modelo (sin pasar por la vista)."""
        from .models import DetalleVenta
        self.producto.refresh_from_db()                                               # stock real de la base de datos
        if self.producto.stock < cantidad:
            Producto.objects.filter(pk=self.producto.pk).update(stock=cantidad)
        venta = Venta.objects.create(cliente=self.cliente)
        DetalleVenta.objects.create(venta=venta, producto=self.producto, cantidad=cantidad, precio=self.producto.precio)
        venta.descontar_stock(); venta.calcular_totales()
        self.producto.refresh_from_db()
        return venta

    def test_venta_baja_stock_valida_y_devuelve(self):
        Producto.objects.filter(pk=self.producto.pk).update(stock=5)
        datos = {"cliente": self.cliente.pk, "fecha_hora": "2026-01-15T10:30", "tipo_pago": "tarjeta"}
        # pide 9 y hay 5 → error de stock
        r = self.client.post(reverse("facturacion:venta_crear"),
                             {**datos, **formset("detalles", [{"producto": self.producto.pk, "cantidad": 9}])})
        self.assertEqual(r.status_code, 200); self.assertEqual(Venta.objects.count(), 0)
        # pide 3 → ok, el precio lo pone la vista
        self.client.post(reverse("facturacion:venta_crear"),
                         {**datos, **formset("detalles", [{"producto": self.producto.pk, "cantidad": 3}])})
        venta = Venta.objects.get()
        self.assertEqual(venta.detalles.get().precio, Decimal("100.00"))
        self.assertEqual(venta.total, Decimal("345.00"))                              # 300 + 15 %
        self.producto.refresh_from_db(); self.assertEqual(self.producto.stock, 2)
        self.client.post(reverse("facturacion:venta_eliminar", args=[venta.pk]))
        self.producto.refresh_from_db(); self.assertEqual(self.producto.stock, 5)     # stock devuelto

    # ---------- inicio y perfil ----------
    def test_inicio_muestra_stock_bajo(self):
        Producto.objects.filter(pk=self.producto.pk).update(stock=2)
        self.assertContains(self.client.get(reverse("home")), "Galaxy")

    def test_mi_perfil_se_crea_y_se_edita(self):
        self.assertEqual(self.client.get(reverse("facturacion:mi_perfil")).status_code, 200)
        self.client.post(reverse("facturacion:mi_perfil"), {"cedula": "0912345678", "telefono": "099", "cargo": "Vendedor"})
        self.assertEqual(Perfil.objects.get(usuario=self.usuario).cargo, "Vendedor")
