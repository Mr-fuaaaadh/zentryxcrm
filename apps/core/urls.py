from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('dashboard/', views.CoreDashboardView.as_view(), name='dashboard'),
    
    # Department URLs
    path('departments/', views.DepartmentListView.as_view(), name='department-list'),
    path('departments/add/', views.DepartmentCreateView.as_view(), name='department-add'),
    path('departments/<int:pk>/update/', views.DepartmentUpdateView.as_view(), name='department-update'),
    path('departments/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department-delete'),
    
    # Designation URLs
    path('designations/', views.DesignationListView.as_view(), name='designation-list'),
    path('designations/add/', views.DesignationCreateView.as_view(), name='designation-add'),
    path('designations/<int:pk>/update/', views.DesignationUpdateView.as_view(), name='designation-update'),
    path('designations/<int:pk>/delete/', views.DesignationDeleteView.as_view(), name='designation-delete'),

]
