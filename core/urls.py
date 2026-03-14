from django.urls import path
from django.contrib.auth.views import LogoutView, PasswordResetView, PasswordResetDoneView

from . import views
from .views import CustomLoginView

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),
    path('password-reset/', PasswordResetView.as_view(
        template_name='core/password_reset_form.html',
        email_template_name='core/password_reset_email.html',
        success_url='/password-reset/done/',
    ), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(
        template_name='core/password_reset_done.html',
    ), name='password_reset_done'),
    path('superadmin/setup/', views.setup_sisep, name='setup_sisep'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('gestion-administrative/', views.gestion_administrative, name='gestion_administrative'),
    path('gerer-comptes/', views.gerer_comptes, name='gerer_comptes'),
    path('profil-compte/<int:user_id>/', views.profil_compte, name='profil_compte'),
    path('creer-compte-agent/', views.creer_compte_agent, name='creer_compte_agent'),
    path('api/agents-disponibles/', views.api_agents_disponibles, name='api_agents_disponibles'),
    path('api/compte/<int:user_id>/toggle/', views.api_toggle_compte, name='api_toggle_compte'),
    path('api/compte/<int:user_id>/delete/', views.api_delete_compte, name='api_delete_compte'),
    path('api/compte/<int:user_id>/lier-agent/', views.api_lier_agent, name='api_lier_agent'),
]
