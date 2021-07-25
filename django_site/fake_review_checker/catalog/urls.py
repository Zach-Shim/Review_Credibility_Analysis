from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('search_link/', views.search_link, name='search_link'),
    path('static_result/<str:product_ASIN>/', views.static_result, name = 'static_result'),
    path('link_result/<str:product_ASIN>/', views.link_result, name = 'link_result'),
] 
 