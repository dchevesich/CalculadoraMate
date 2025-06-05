from django.db import models
# Para manejar fechas y horas, especialmente para el default
from django.utils import timezone

# Create your models here.


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    # Podríamos añadir un campo para un ícono más adelante si quieres,
    # por ejemplo: icono_css = models.CharField(max_length=50, blank=True, null=True) # ej: 'fas fa-coffee'

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        # Ordena las categorías alfabéticamente por defecto
        ordering = ['nombre']


class Gasto(models.Model):
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    # Por defecto la fecha actual al crear
    fecha = models.DateField(default=timezone.now)
    # Opcional, puede estar vacío
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name='gastos')
    # usuario = models.ForeignKey(User, on_delete=models.CASCADE) # Descomentar si implementas login

    def __str__(self):
        return f"{self.descripcion[:30] if self.descripcion else self.categoria.nombre} - S/.{self.monto} - {self.fecha.strftime('%d-%m-%Y')}"

    class Meta:
        # Los más recientes primero (por fecha, y luego por id si hay varios en misma fecha)
        ordering = ['-fecha', '-id']
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
