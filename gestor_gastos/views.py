import datetime
from django.shortcuts import render, redirect, get_object_or_404
from .models import Categoria, Gasto
from .forms import GastoRapidoForm
from django.db.models import Sum
from django.contrib import messages
import json

# --- Función auxiliar para formatear a CLP (Peso Chileno) ---
def _format_clp(amount):
    """
    Formatea un número (Decimal, float, int) a string con separador de miles '.'
    y sin decimales si el número es entero.
    Ej: 1234567.00 -> '1.234.567'
        12345.67   -> '12.345,67'
        50000.00   -> '50.000'
    """
    if amount is None:
        return "0"
    
    # Convertir a Decimal si aún no lo es, para manejar la precisión.
    # Si viene de DecimalField, ya será Decimal. Si es int o float, lo convertimos.
    from decimal import Decimal
    try:
        amount_decimal = Decimal(str(amount))
    except Exception: # Captura cualquier error de conversión a Decimal
        return str(amount) # Si no se puede convertir a Decimal, devolver tal cual

    # Verificar si el número es un entero (no tiene parte decimal)
    # Ejemplo: Decimal('50000.00') - Decimal('50000') = Decimal('0.00')
    if amount_decimal == amount_decimal.to_integral_value():
        # Es un entero, formatear sin decimales.
        # to_integral_value() lo convierte a entero si no tiene decimales.
        # Convertimos a string y luego aplicamos la lógica de separador de miles.
        formatted_integer_part = f"{int(amount_decimal):,}".replace(",", ".")
        return formatted_integer_part
    else:
        # Tiene decimales, formatear con dos decimales y coma como separador decimal.
        # Python f-string usa punto decimal por defecto, así que hay que reemplazar.
        # Formato: 1,234.56 -> luego convertir a 1.234,56
        formatted_with_decimals = f"{amount_decimal:,.2f}" # Ej: '50,123.45'

        # Reemplazar la coma de miles a punto, y el punto decimal a coma.
        # Un truco para intercambiar:
        # 1. Reemplazar punto decimal por un caracter temporal (ej: '@')
        # 2. Reemplazar coma de miles por punto
        # 3. Reemplazar caracter temporal por coma
        temp_char = '@' # Caracter que no debería aparecer en el número
        result = formatted_with_decimals.replace('.', temp_char).replace(',', '.').replace(temp_char, ',')
        return result

# Vista para la página principal con los botones de gasto rápido
def pagina_principal_gastos(request):
    categorias = Categoria.objects.all().order_by('nombre')
    
    contexto = {
        'mensaje_bienvenida': '¡Bienvenido a tu Calculadora de Gastos!',
        'categorias': categorias
    }
    return render(request, 'gestor_gastos/principal.html', contexto)

# Vista para registrar un gasto específico por categoría
def registrar_gasto(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)

    if request.method == 'POST':
        form = GastoRapidoForm(request.POST)
        if form.is_valid():
            nuevo_gasto = form.save(commit=False)
            nuevo_gasto.categoria = categoria
            nuevo_gasto.save()
            messages.success(request, f'Gasto de ${nuevo_gasto.monto} en "{categoria.nombre}" registrado con éxito.')
            return redirect('principal_gastos')
        else:
            messages.error(request, 'Error al registrar el gasto. Por favor, revisa los datos.')
    else:
        form = GastoRapidoForm()

    contexto = {
        'form': form,
        'categoria': categoria
    }
    return render(request, 'gestor_gastos/gasto_form.html', contexto)

# Vista para listar y resumir los gastos con filtro por mes y año
def lista_gastos(request):
    hoy = datetime.date.today()

    # 1. Obtener mes y año de los parámetros GET o usar el actual por defecto
    mes_seleccionado = hoy.month
    anio_seleccionado = hoy.year

    if request.GET.get('mes') and request.GET.get('anio'):
        try:
            mes_from_get = int(request.GET.get('mes'))
            anio_from_get = int(request.GET.get('anio'))
            
            if 1 <= mes_from_get <= 12 and 2000 <= anio_from_get <= hoy.year + 10:
                mes_seleccionado = mes_from_get
                anio_seleccionado = anio_from_get
            else:
                messages.warning(request, "Mes o año inválido. Mostrando datos del mes actual.")
        except ValueError:
            messages.error(request, "Formato de mes o año inválido. Mostrando datos del mes actual.")

    # 2. Filtrar los gastos para el mes y año seleccionado
    gastos_filtrados_mes_anio = Gasto.objects.filter(
        fecha__year=anio_seleccionado,
        fecha__month=mes_seleccionado
    )

    # 3. Calcular el total gastado y formatearlo
    total_gastado_mes = gastos_filtrados_mes_anio.aggregate(total=Sum('monto'))['total']
    total_gastado_mes_formateado = _format_clp(total_gastado_mes) # ¡Formateado aquí!

    # 4. Calcular el desglose por categoría y formatear sus montos
    gastos_por_categoria_queryset = gastos_filtrados_mes_anio.values('categoria__nombre').annotate(total=Sum('monto')).order_by('-total')
    
    gastos_por_categoria_formateado = []
    for item in gastos_por_categoria_queryset:
        gastos_por_categoria_formateado.append({
            'categoria__nombre': item['categoria__nombre'],
            'total': _format_clp(item['total']) # ¡Formateado aquí!
        })

    # 5. Obtener TODOS los gastos para la tabla de "Detalle de Todos los Gastos" y formatear sus montos
    gastos_todos_registros = Gasto.objects.all().order_by('-fecha', '-id')
    gastos_para_tabla_formateados = []
    for gasto_obj in gastos_todos_registros:
        gastos_para_tabla_formateados.append({
            'id': gasto_obj.id,
            'fecha': gasto_obj.fecha,
            'categoria': gasto_obj.categoria,
            'descripcion': gasto_obj.descripcion,
            'monto': _format_clp(gasto_obj.monto) # ¡Formateado aquí!
        })


    # 6. Preparar datos para el gráfico de torta (JSON) - MONTOS DEBEN SER NÚMEROS AQUÍ
    labels_grafico = []
    data_grafico = []
    for item in gastos_por_categoria_queryset: # Usar el queryset original aquí
        labels_grafico.append(item['categoria__nombre'])
        data_grafico.append(float(item['total'])) # ¡AQUÍ DEBE SEGUIR SIENDO NÚMERO/FLOAT para Chart.js!


    # 7. Listas para los selectores de Mes y Año en el filtro
    nombres_meses = [
        ("1", "Enero"), ("2", "Febrero"), ("3", "Marzo"), ("4", "Abril"),
        ("5", "Mayo"), ("6", "Junio"), ("7", "Julio"), ("8", "Agosto"),
        ("9", "Septiembre"), ("10", "Octubre"), ("11", "Noviembre"), ("12", "Diciembre")
    ]
    rango_anios = range(hoy.year - 5, hoy.year + 1)

    contexto = {
        'gastos': gastos_para_tabla_formateados, # Pasar la lista con montos YA FORMATEADOS (strings)
        'total_mes': total_gastado_mes_formateado, # Pasar el total YA FORMATEADO (string)
        'gastos_por_categoria': gastos_por_categoria_formateado, # Pasar el desglose YA FORMATEADO (strings)
        'labels_grafico': json.dumps(labels_grafico),
        'data_grafico': json.dumps(data_grafico), # Esto sigue siendo números (floats)
        'mes_seleccionado': str(mes_seleccionado),
        'anio_seleccionado': str(anio_seleccionado),
        'nombres_meses': nombres_meses,
        'rango_anios': rango_anios,
    }
    
    return render(request, 'gestor_gastos/lista_gastos.html', contexto)

def eliminar_gasto(request, gasto_id):
    gasto = get_object_or_404(Gasto, pk=gasto_id) # Obtiene el gasto o lanza 404

    if request.method == 'POST':
        gasto.delete() # Elimina el gasto de la base de datos
        messages.success(request, 'Gasto eliminado con éxito.')
        return redirect('lista_gastos') # Redirige a la lista de gastos actualizada
    
    # Si la solicitud es GET, muestra una página de confirmación
    contexto = {
        'gasto': gasto # Pasamos el objeto gasto para mostrar sus detalles en la confirmación
    }
    # Asegúrate de que este render apunte al template correcto: 'confirmar_eliminar.html'
    return render(request, 'gestor_gastos/confirmar_eliminar.html', contexto)


def modificar_gasto(request, gasto_id):
    gasto = get_object_or_404(Gasto, pk=gasto_id) # Obtiene el gasto o lanza 404

    if request.method == 'POST':
        # Instancia el formulario con los datos recibidos y el objeto de gasto EXISTENTE
        form = GastoRapidoForm(request.POST, instance=gasto)
        if form.is_valid():
            form.save() # Si es válido, guarda los cambios en ese mismo objeto de gasto
            messages.success(request, 'Gasto modificado con éxito.')
            return redirect('lista_gastos') # Redirige a la lista de gastos actualizada
        else:
            messages.error(request, 'Error al modificar el gasto. Por favor, revisa los datos.')
    else:
        # Si la solicitud es GET, instancia el formulario con los datos actuales del gasto
        form = GastoRapidoForm(instance=gasto)

    contexto = {
        'form': form,
        'gasto': gasto, # Pasamos el objeto gasto por si se necesita en la plantilla
        'categoria_nombre': gasto.categoria.nombre # Para mostrar la categoría en el título de la página
    }
    # Asegúrate de que este render apunte al template correcto: 'modificar_gasto.html'
    return render(request, 'gestor_gastos/modificar_gasto.html', contexto)