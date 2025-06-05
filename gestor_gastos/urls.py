from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_principal_gastos, name='principal_gastos'),
]
