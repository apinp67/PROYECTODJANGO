# =====================================================================
# facturacion/mixins.py
# Un MIXIN es una clase pequeña con UNA habilidad, pensada para sumarse a otras clases.
# =====================================================================


class UsuarioRegistroMixin:
    """Llena el campo user del ModeloBase con el usuario conectado."""

    def form_valid(self, form):                      # se ejecuta cuando el formulario es válido (POST)
        form.instance.user = self.request.user       # form.instance = el objeto que se va a guardar
        return super().form_valid(form)              # sigue la cadena: guarda y redirige
