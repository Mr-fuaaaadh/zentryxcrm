from django.urls import path
from .views import CustomerListView, CustomerCreateView, CustomerUpdateView, CustomerDeleteView

app_name = 'customers'

urlpatterns = [
    path('list/', CustomerListView.as_view(), name='list'),
    path('add/', CustomerCreateView.as_view(), name='add'),
    path('update/<uuid:pk>/', CustomerUpdateView.as_view(), name='update'),
    path('delete/<uuid:pk>/', CustomerDeleteView.as_view(), name='delete'),
]
