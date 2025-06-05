from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_principal_gastos, name='principal_gastos'),
    path('nuevo/<int:categoria_id>/', views.registrar_gasto, name='registrar_gasto'),
    path('lista/', views.lista_gastos, name='lista_gastos'),

]
