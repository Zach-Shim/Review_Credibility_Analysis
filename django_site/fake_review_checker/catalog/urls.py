from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('test', views.test, name = 'test'),
    path('<str:product_ASIN>/result', views.result, name = 'result'),
] 
'''
path('<int:userID>/analyze', views.analyze, name = 'analyze'),
path('<int:userID>/result', views.result, name = 'result'),
path('', views.index, name = 'index'),
'''
