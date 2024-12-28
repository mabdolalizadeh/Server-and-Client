from django.urls import path
from server_side import views

urlpatterns = [
    path('', views.index, name='index'),
]