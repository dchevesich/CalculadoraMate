from django.contrib import admin
from .models import Categoria, Gasto  # Importamos tus modelos

# Register your models here.


class CategoriaAdmin(admin.ModelAdmin):
    # Campos que se mostrarán en la lista de categorías
    list_display = ('nombre',)
    search_fields = ('nombre',)  # Habilita una barra de búsqueda por nombre


class GastoAdmin(admin.ModelAdmin):
    list_display = ('descripcion_corta', 'monto', 'fecha', 'categoria',
                    'usuario_display')  # Campos en la lista de gastos
    list_filter = ('fecha', 'categoria')  # Filtros laterales
    search_fields = ('descripcion', 'categoria__nombre')  # Búsqueda
    date_hierarchy = 'fecha'  # Navegación por fechas en la parte superior

    # Pequeña función para mostrar el nombre de usuario si existiera (lo dejamos preparado)
    def usuario_display(self, obj):
        # if obj.usuario:
        #     return obj.usuario.username
        return "N/A"  # Cambiar cuando implementes usuarios
    usuario_display.short_description = 'Usuario'

    # Función para mostrar una descripción corta
    def descripcion_corta(self, obj):
        if obj.descripcion:
            return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
        return f"Gasto en {obj.categoria.nombre}"
    descripcion_corta.short_description = 'Descripción'


admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Gasto, GastoAdmin)
