# Mi Tienda · Sistema de facturación con Django

Proyecto de la **Actividad de aprendizaje práctico N.º 2 – Desarrollar aplicaciones básicas en Django**.

## Qué incluye
- **Modelos y relaciones**: `Marca` 1:N `Producto`, `Producto` N:M `Categoria`, `User` 1:1 `Perfil`, y `Cliente`.
- **CRUD con Vistas Basadas en Funciones (VBF)**: Marcas y Categorías.
- **CRUD con Vistas Basadas en Clases (VBC)**: Productos y Clientes (con buscador y paginación).
- **Autenticación**: login / logout, menú que cambia según la sesión.
- **Templates**: `base.html` con herencia, mensajes de éxito/error y Bootstrap 5.
- **Estilo propio**: `static/css/estilos.css` (tema Índigo & Coral).
- **Panel admin** configurado para todos los modelos.

## Cómo ejecutarlo
```bash
python -m venv venv
venv\Scripts\activate        # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
cd mi_tienda
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Abrir http://127.0.0.1:8000/ e iniciar sesión.
