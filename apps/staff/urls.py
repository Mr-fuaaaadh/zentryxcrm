from django.urls import path
from .views import StaffListView, StaffAdd, StaffUpdateView, StaffDeleteView

app_name = 'staff'

urlpatterns = [
    path('list/', StaffListView.as_view(), name='list'),
    path("add/", StaffAdd.as_view(), name="add"),
    path("<int:pk>/update/", StaffUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", StaffDeleteView.as_view(), name="delete"),
]