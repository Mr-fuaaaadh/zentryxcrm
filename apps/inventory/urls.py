from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.AssetListView.as_view(), name='asset_list'),
    path('assets/create/', views.AssetCreateView.as_view(), name='asset_add'),
    path('assets/<uuid:pk>/', views.AssetDetailView.as_view(), name='asset_detail'),
    path('assets/<uuid:pk>/edit/', views.AssetUpdateView.as_view(), name='asset_edit'),
    path('assets/<uuid:pk>/delete/', views.AssetDeleteView.as_view(), name='asset_delete'),
    
    # Assignments
    path('assets/<uuid:id>/assign/', views.AssetAssignView.as_view(), name='asset_assign'),
    path('assignments/<uuid:pk>/return/', views.AssetReturnView.as_view(), name='asset_return'),
    
    # For compatibility with legacy buttons in template
    path('assets/<uuid:pk>/stock-update/', views.AssetStockAdjustmentView.as_view(), name='stock_update'),
    path('assets/bulk-delete/', views.AssetBulkDeleteView.as_view(), name='asset_bulk_delete'),
    path('assets/export-csv/', views.AssetExportCSVView.as_view(), name='export_inventory_csv'),

    
    path('logs/', views.InventoryLogListView.as_view(), name='log_list'),
]
