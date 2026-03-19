from django.urls import path
from .views import *


app_name = 'sales'

urlpatterns = [
    path('proposals/', ProposalListView.as_view(), name='proposal_list'),
    path('proposals/add/', ProposalCreateView.as_view(), name='proposal_add'),
    path('proposals/<int:pk>/edit/', ProposalUpdateView.as_view(), name='proposal_edit'),
    path('proposals/<int:pk>/delete/', ProposalDeleteView.as_view(), name='proposal_delete'),

    path('estimates/', EstimateListView.as_view(), name='estimate_list'),
    path('estimates/add/', EstimateCreateView.as_view(), name='estimate_add'),
    path('estimates/<int:pk>/edit/', EstimateUpdateView.as_view(), name='estimate_edit'),
    path('estimates/<int:pk>/delete/', EstimateDeleteView.as_view(), name='estimate_delete'),

    # Staff Monthly Targets
    path('staff-targets/', StaffMonthlyTargetListView.as_view(), name='staff_target_list'),
    path('staff-targets/add/', StaffMonthlyTargetCreateView.as_view(), name='staff_target_add'),
    path('staff-targets/<int:pk>/edit/', StaffMonthlyTargetUpdateView.as_view(), name='staff_target_edit'),
    path('staff-targets/<int:pk>/delete/', StaffMonthlyTargetDeleteView.as_view(), name='staff_target_delete'),
    
    path('performance-monitoring/', StaffPerformanceDashboardView.as_view(), name='performance_monitoring'),
]
