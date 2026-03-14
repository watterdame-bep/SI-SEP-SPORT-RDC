from django.urls import path
from . import views

app_name = 'parametres'

urlpatterns = [
    path('fonctions/', views.parametres_fonctions, name='parametres_fonctions'),
]
