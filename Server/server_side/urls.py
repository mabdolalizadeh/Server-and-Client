from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='server'),
    path('logout/', views.logout_view, name='logout'),
]