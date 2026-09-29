from django.urls import path

from . import views

app_name = 'formations'

urlpatterns = [
    path('', views.formations, name='list'),
]
