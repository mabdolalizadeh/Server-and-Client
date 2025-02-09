from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='server'),
    path('logout/', views.logout_view, name='logout'),
]