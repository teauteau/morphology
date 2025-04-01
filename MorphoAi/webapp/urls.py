from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('generate/', views.generate, name='generate'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('help/', views.help_page, name='help'),
    path('summary/', views.summary, name='summary'),
    path("results/", views.results_page, name="results")
]