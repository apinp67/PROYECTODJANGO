from django.http import HttpResponse, JsonResponse   # Importamos dos tipos de respuesta
from django.shortcuts import render                  # render: responde usando un template .html


# ---------------------------------------------------------------
# 1) HttpResponse: devuelve un texto o HTML escrito aquí mismo.
#    Sirve para pruebas rápidas. No se usa para páginas grandes.
# ---------------------------------------------------------------
def saludo(request):                                   # Toda vista recibe request
    return HttpResponse("<h1>¡Hola desde Django!</h1><p>Esto es un HttpResponse.</p>")  # Respuesta: ese HTML


# ---------------------------------------------------------------
# 2) JsonResponse: devuelve DATOS en formato JSON (no una página).
#    Lo usan las apps móviles y JavaScript para pedir información.
#    Recibe un diccionario de Python y lo convierte en JSON.
# ---------------------------------------------------------------
def info_peticion(request):
    datos = {                                          # Armamos un diccionario con datos de la petición
        "metodo": request.method,                      # 'GET' o 'POST'
        "ruta": request.path,                          # la dirección visitada, por ejemplo '/info/'
        "parametros_get": request.GET.dict(),          # lo que viene después del ? en la URL
        "navegador": request.headers.get("User-Agent", ""),  # qué navegador usa la persona
    }
    return JsonResponse(datos)                         # Lo devolvemos como JSON
    # Para devolver una LISTA en vez de un diccionario: JsonResponse([1, 2, 3], safe=False)


# ---------------------------------------------------------------
# 3) render: junta un TEMPLATE (.html) con un CONTEXTO (diccionario de datos)
#    y devuelve la página terminada. Es lo que usarás casi siempre.
#    Forma: render(request, "nombre_del_template.html", contexto)
# ---------------------------------------------------------------
def home(request):
    nombre = ""                                        # Empieza vacío

    # ¿Cómo llegó la petición? Esta pregunta es la clave de todo el curso:
    if request.method == "POST":                       # Si llegó por POST (el usuario envió el formulario)...
        nombre = request.POST.get("nombre", "").strip()   # ...leemos el campo name="nombre" (strip quita espacios)
    # Si llegó por GET (solo abrió la página), no hacemos nada especial.

    contexto = {                                       # Datos que vamos a enviar al template
        "titulo": "Mi Tienda",                         # En el HTML se usa como {{ titulo }}
        "nombre": nombre,                              # En el HTML se usa como {{ nombre }}
        "productos": ["Laptop", "Mouse", "Teclado"],   # Una lista para practicar el {% for %}
    }
    return render(request, "home.html", contexto)      # Junta home.html + contexto y responde