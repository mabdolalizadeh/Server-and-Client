from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('logout/', views.logout_view, name='logout'),
    path('command/', views.SendCommand.as_view(), name='command'),
    path('download/', views.FileDownloadView.as_view(), name='download'),
    path('upload/', views.FileUploadView.as_view(), name='upload'),
]