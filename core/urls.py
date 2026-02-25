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
    path('creer-compte-entite/', views.creer_compte_entite, name='creer_compte_entite'),
    path('dashboard/', views.sg_dashboard, name='sg_dashboard'),
    path('minister/', views.minister_dashboard, name='minister_dashboard'),
    path('minister/signer/<uuid:uid>/', views.minister_sign_action, name='minister_sign_action'),
]
