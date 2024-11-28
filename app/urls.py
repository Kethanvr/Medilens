from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Home page
    path('product/', views.product_page, name='product_page'),  # Product page for upload
    path('upload/', views.upload_image, name='upload'),  # Image upload endpoint
    path('result/', views.result_page, name='result'),  # Result page
    path('generate-audio/<str:field>/', views.generate_audio, name='generate_audio'),  # Audio generation endpoint
]
