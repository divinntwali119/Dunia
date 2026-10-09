from django.urls import path

from . import views

app_name = 'home'

urlpatterns = [
    path('', views.index, name='index'),
    path('service-worker.js', views.service_worker, name='service_worker'),
]
