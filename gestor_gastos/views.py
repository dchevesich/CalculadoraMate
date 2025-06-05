from django.shortcuts import render
from django.http import HttpResponse


def pagina_principal_gastos(request):
    contexto = {'mensaje_bienvenida': '¡Bienvenido a tu Calculadora de Gastos!'}
    return render(request, 'gestor_gastos/principal.html', contexto)
