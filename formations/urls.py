from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views

app_name = 'formations'

urlpatterns = [
    path('', views.formations, name='list'),
    path('creer-un-compte/', views.student_signup, name='signup'),
    path('connexion/', views.StudentLoginView.as_view(), name='login'),
    path('deconnexion/', auth_views.LogoutView.as_view(next_page='formations:login'), name='logout'),
    path('mon-espace/', views.student_dashboard, name='student_dashboard'),
    path('mot-de-passe-oublie/', auth_views.PasswordResetView.as_view(
        template_name='formations/password_reset_form.html',
        email_template_name='formations/password_reset_email.txt',
        subject_template_name='formations/password_reset_subject.txt',
        success_url=reverse_lazy('formations:password_reset_done'),
    ), name='password_reset'),
    path('mot-de-passe-oublie/envoye/', auth_views.PasswordResetDoneView.as_view(
        template_name='formations/password_reset_done.html',
    ), name='password_reset_done'),
    path('reinitialiser/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='formations/password_reset_confirm.html',
        success_url=reverse_lazy('formations:password_reset_complete'),
    ), name='password_reset_confirm'),
    path('reinitialiser/termine/', auth_views.PasswordResetCompleteView.as_view(
        template_name='formations/password_reset_complete.html',
    ), name='password_reset_complete'),
    path('inscription/<int:formation_id>/', views.enroll, name='enroll'),
    path('paiement/<int:enrollment_id>/', views.submit_payment, name='payment'),
    path('lecon/<int:lesson_id>/', views.lesson_detail, name='lesson'),
    path('lecon/<int:lesson_id>/terminer/', views.complete_lesson, name='complete_lesson'),
    path('ressource/<int:resource_id>/', views.download_resource, name='resource_download'),
    path('fichiers-prives/<path:file_path>/', views.download_private_file, name='private_media'),
    path('attestation/<uuid:certificate_number>/', views.verify_certificate, name='certificate'),
    path('<int:pk>/', views.formation_detail, name='detail'),
]
