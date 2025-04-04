from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings




urlpatterns = [
    path('', views.home, name='home'),
    path('generate/', views.generate, name='generate'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('help/', views.help_page, name='help'),
    path('summary/', views.summary, name='summary'),
    path("results/", views.results_page, name="results"),
    path('download-exercises/', views.exercise_pdf, name='download_exercises'),
    path('add-exercises/', views.add_exercises, name='add_exercises'),
    path('update_exercise/', views.update_exercise, name='update_exercise'),
    path('delete_exercise/', views.delete_exercise, name='delete_exercise'),



]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


