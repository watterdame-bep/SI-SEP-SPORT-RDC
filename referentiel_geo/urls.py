from django.urls import path
from . import views

app_name = 'referentiel_geo'

urlpatterns = [
    # Page principale avec onglets
    path('', views.parametres_geographiques, name='parametres_geographiques'),
    
    # API pour récupérer les données par niveau (AJAX)
    path('api/provinces/', views.api_provinces, name='api_provinces'),
    path('api/territoires/<uuid:province_id>/', views.api_territoires, name='api_territoires'),
    path('api/secteurs/<uuid:territoire_id>/', views.api_secteurs, name='api_secteurs'),
    path('api/groupements/<uuid:secteur_id>/', views.api_groupements, name='api_groupements'),
    
    # API avec query parameters pour les cascades
    path('api/territoires/', views.api_territoires_by_province, name='api_territoires_by_province'),
    path('api/secteurs/', views.api_secteurs_by_territoire, name='api_secteurs_by_territoire'),
    path('api/groupements/', views.api_groupements_by_secteur, name='api_groupements_by_secteur'),
    
    # API pour récupérer les détails d'un élément
    path('territoire/<uuid:pk>/detail/', views.territoire_detail, name='territoire_detail'),
    path('secteur/<uuid:pk>/detail/', views.secteur_detail, name='secteur_detail'),
    path('groupement/<uuid:pk>/detail/', views.groupement_detail, name='groupement_detail'),
    
    # Actions CRUD
    path('province/create/', views.province_create, name='province_create'),
    path('province/<uuid:pk>/update/', views.province_update, name='province_update'),
    path('province/<uuid:pk>/delete/', views.province_delete, name='province_delete'),
    
    path('territoire/create/', views.territoire_create, name='territoire_create'),
    path('territoire/<uuid:pk>/update/', views.territoire_update, name='territoire_update'),
    path('territoire/<uuid:pk>/delete/', views.territoire_delete, name='territoire_delete'),
    
    path('secteur/create/', views.secteur_create, name='secteur_create'),
    path('secteur/<uuid:pk>/update/', views.secteur_update, name='secteur_update'),
    path('secteur/<uuid:pk>/delete/', views.secteur_delete, name='secteur_delete'),
    
    path('groupement/create/', views.groupement_create, name='groupement_create'),
    path('groupement/<uuid:pk>/update/', views.groupement_update, name='groupement_update'),
    path('groupement/<uuid:pk>/delete/', views.groupement_delete, name='groupement_delete'),
]
