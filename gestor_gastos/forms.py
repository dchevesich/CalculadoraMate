from django import forms
from .models import Gasto
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Categoria, Gasto
import re # Para expresiones regulares

class GastoRapidoForm(forms.ModelForm):
    # Cambiamos el tipo de campo del formulario de NumberInput a TextInput.
    # Esto permite al usuario ingresar el punto como separador de miles y la coma como decimal.
    monto = forms.CharField(
        label='Monto del Gasto',
        widget=forms.TextInput(attrs={
            'class': 'form-input-monto',
            'placeholder': 'Ej: 20.000 o 15.500,50' # Indicamos el formato esperado
        })
    )

    class Meta:
        model = Gasto
        fields = ['monto', 'descripcion']

        # Personalizar widgets para otros campos si es necesario
        widgets = {
            # 'monto' ya se define arriba, así que no es necesario aquí.
            'descripcion': forms.Textarea(attrs={'class': 'form-input-descripcion', 'placeholder': 'Nota rápida (opcional)...', 'rows': 3}),
        }

        labels = {
            'monto': 'Monto del Gasto',
            'descripcion': 'Descripción',
        }

    # Método de limpieza personalizado para el campo 'monto'
    # Este método se ejecuta cuando se llama a form.is_valid()
    def clean_monto(self):
        monto_str = self.cleaned_data['monto'] # Obtiene el valor ingresado como string

        # Paso 1: Eliminar puntos que actúan como separadores de miles
        # '20.000' -> '20000'
        # '1.500.000' -> '1500000'
        monto_limpio = monto_str.replace('.', '')

        # Paso 2: Reemplazar la coma decimal por un punto decimal
        # '15500,50' -> '15500.50'
        # Usamos una expresión regular para asegurarnos de que solo la ÚLTIMA coma (la decimal) sea reemplazada,
        # en caso de que alguien haya usado comas por error en los miles (ej: 1,500,000.00)
        monto_limpio = re.sub(r',(\d+)$', r'.\1', monto_limpio)
        # Esto maneja casos como '1000,50' a '1000.50'
        # y no afecta '10000'

        try:
            # Paso 3: Convertir el string limpio a un tipo Decimal
            # Es importante usar Decimal para precisión con dinero
            monto_decimal = float(monto_limpio) # Convertir a float primero para manejar posibles notaciones científicas o evitar errores con Decimal si el string no es perfectamente floatable
            monto_decimal = round(monto_decimal, 2) # Redondear a 2 decimales, ya que tu modelo Gasto.monto es DecimalField(decimal_places=2)

            # Validaciones adicionales (opcional, pero buena práctica)
            if monto_decimal < 0:
                raise ValidationError(_("El monto no puede ser negativo."))
            if monto_decimal == 0:
                raise ValidationError(_("El monto no puede ser cero."))

            return monto_decimal # Devuelve el valor Decimal ya limpio y validado

        except ValueError:
            # Si la conversión falla (ej. el usuario escribió "abc" o "123,asd")
            raise ValidationError(_("El monto ingresado no es un número válido. Use puntos para miles y coma para decimales (ej: 20.000 o 15.500,50)."))
        except TypeError: # En caso de que monto_limpio sea None o algo inesperado
            raise ValidationError(_("El monto ingresado no es un número válido."))
        
        

