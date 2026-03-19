from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('list/', views.AttendanceListView.as_view(), name='list'),
    path('add/', views.AttendanceCreateView.as_view(), name='add'),
    path('edit/<int:pk>/', views.AttendanceUpdateView.as_view(), name='edit'),
    path('export/', views.export_attendance_csv, name='export_csv'),
]