from django.urls import path
from .views import (
    LeadListView, LeadDetailView, LeadCreateView, 
    LeadUpdateView, LeadDeleteView,
    AddActivityView
)

app_name = 'leads'

urlpatterns = [
    
    path('list/', LeadListView.as_view(), name='list'),
    path('add/', LeadCreateView.as_view(), name='add'),
    path('<int:pk>/', LeadDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', LeadUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', LeadDeleteView.as_view(), name='delete'),
    path('<int:pk>/activity/add/', AddActivityView.as_view(), name='add_activity'),

]
