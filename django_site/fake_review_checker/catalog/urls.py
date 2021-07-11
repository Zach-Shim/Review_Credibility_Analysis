from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('search_link/', views.search_link, name='search_link'),
    path('result/<str:product_ASIN>/', views.result, name = 'result'),
] 
 