# Mi Tienda · Sistema de facturación con Django

Proyecto de la **Actividad de aprendizaje práctico N.º 2 – Desarrollar aplicaciones básicas en Django**
(Guía 3: Modelos y Vistas Basadas en Clases). Todo el CRUD usa **vistas basadas en clases**; solo el
inicio de sesión, el cierre de sesión y el registro de cuenta son funciones.

## Qué incluye
- **ModeloBase abstracto** (usuario que registra + fechas) del que heredan todos los modelos.
- **10 modelos**: Categoría, Marca, Producto, Cliente, Proveedor, Perfil, Venta, DetalleVenta, Compra, DetalleCompra.
- **Relaciones**: 1:N (Marca→Producto, Cliente→Venta, Proveedor→Compra), N:M (Producto↔Categoría), 1:1 (Usuario↔Perfil)
  y maestro-detalle (Venta/DetalleVenta y Compra/DetalleCompra).
- **Imágenes** con `ImageField`: foto de producto y logo de proveedor (carpeta `media/`).
- **CRUD completo** de Productos, Ventas, Marcas, Categorías, Clientes, Proveedores y Compras.
- **Ventas**: el stock baja, IVA 15 %, factura imprimible. **Compras**: el stock sube y se revierte al editar o eliminar.
- **Validaciones**: cédula (10 dígitos), RUC (13 dígitos y termina en 001), stock suficiente, precios mayores que 0.
- **Protección de borrado** (`ProtectedError`): una marca con productos, un cliente con ventas o un proveedor con compras no se eliminan.
- **Mi perfil** (reto): `UpdateView` sin `pk` en la URL.
- **Panel de inicio** con productos activos, ventas de hoy y productos con stock bajo.
- **Diseño propio** (tema Índigo & Coral) en `static/css/estilos.css`.
- **14 pruebas automáticas**: `python manage.py test`.

## Cómo ejecutarlo
```bash
python -m venv venv
venv\Scripts\activate        # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
cd mi_tienda
python manage.py runserver
```
Abrir http://127.0.0.1:8000/ e iniciar sesión.

**Usuario de prueba:** `admin` · **Contraseña:** `Admin12345`

La base `db.sqlite3` ya trae datos de prueba: 3 marcas, 4 categorías, 5 clientes, 2 proveedores con logo,
5 productos con foto, 3 ventas y 2 compras.

## Estructura
```
mi_tienda/
├── manage.py
├── db.sqlite3
├── media/                  (fotos de productos y logos de proveedores)
├── mi_tienda/              (settings, urls, views: inicio + login/logout/registro)
├── facturacion/            (models, mixins, forms, views, urls, admin, tests)
│   └── templates/facturacion/
├── templates/              (base.html, home.html, registration/)
└── static/css/estilos.css
```
