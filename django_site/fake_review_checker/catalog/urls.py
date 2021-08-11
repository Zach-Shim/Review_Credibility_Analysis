from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search_link/', views.search_link, name='search_link'),
    path('about/', views.about, name='about'),
    path('result/<str:product_ASIN>/', views.result, name = 'result'),
    path('link_result/<str:product_ASIN>/', views.link_result, name = 'link_result'),
] 
 