from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.ExpenseListView.as_view(), name='expense_list'),
    path('create/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('<int:pk>/', views.ExpenseDetailView.as_view(), name='expense_detail'),
    path('<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='expense_edit'),
    path('<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense_delete'),
    
    # Workflow & Actions
    path('<int:pk>/workflow/<str:action>/', views.ExpenseWorkflowView.as_view(), name='expense_workflow'),
    path('<int:pk>/payment/add/', views.ExpensePaymentCreateView.as_view(), name='payment_add'),
    path('<int:pk>/attachment/add/', views.ExpenseAttachmentCreateView.as_view(), name='attachment_add'),
    path('bulk-actions/', views.ExpenseBulkActionView.as_view(), name='bulk_actions'),
    path('export-csv/', views.ExpenseExportCSVView.as_view(), name='export_csv'),
]