from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings




urlpatterns = [
    path('', views.home, name='home'),
    path('generate/', views.generate, name='generate'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('FAQs', views.help_page, name='FAQs'),
    path('summary/', views.summary, name='summary'),
    path("results/", views.results_page, name="results"),
    path('download-exercises/', views.exercise_pdf, name='download_exercises'),
    path('add-exercises/', views.add_exercises, name='add_exercises'),
    path('update_exercise/', views.update_exercise, name='update_exercise'),
    path('delete_exercise/', views.delete_exercise, name='delete_exercise'),
    path('add_custom_exercise/', views.add_custom_exercise, name='add_custom_exercise'),
    path('generate_exercise_given_word/', views.generate_exercise_given_word, name='generate_exercise_given_word'),
    path('update_title/', views.update_title, name='update_title'),
    path('store-api-key/', views.store_api_key, name='store_api_key'),
    path('lesson/', views.lesson, name='lesson'),







]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


