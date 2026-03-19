from .views import StudentListView, StudentAdd, StudentUpdateView, StudentDeleteView
from django.urls import path
app_name = 'students'

urlpatterns = [
    path('list/', StudentListView.as_view(), name='list'),
    path('add/', StudentAdd.as_view(), name='add'),
    path('update/<uuid:pk>/', StudentUpdateView.as_view(), name='update'),
    path('delete/<uuid:pk>/', StudentDeleteView.as_view(), name='delete'),
]
