from django.urls import path

from . import views

app_name = 'news'

urlpatterns = [
    path('', views.news, name='list'),
    path('notifications/', views.notifications_settings, name='notifications_settings'),
    path('push/subscribe/', views.push_subscribe, name='push_subscribe'),
    path('push/unsubscribe/', views.push_unsubscribe, name='push_unsubscribe'),
    path('newsletter/inscription/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('newsletter/confirmer/<uuid:token>/', views.newsletter_confirm, name='newsletter_confirm'),
    path('newsletter/desinscription/<uuid:token>/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),
]
