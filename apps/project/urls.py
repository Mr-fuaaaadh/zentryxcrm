from django.urls import path
from .views import ProjectListView, ProjectCreateView, ProjectUpdateView, ProjectDeleteView

app_name = 'projects'

urlpatterns = [
    path('list/', ProjectListView.as_view(), name='list'),
    path('create/', ProjectCreateView.as_view(), name='create'),
    path('update/<int:pk>/', ProjectUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', ProjectDeleteView.as_view(), name='delete'),
]
