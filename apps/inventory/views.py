from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q, Sum, F
from django.utils import timezone

from .models import Asset, Supplier, Purchase, StockOut, InventoryLog, InventoryBalance, AssetAssignment
from .forms import AssetForm, SupplierForm, PurchaseForm, AssetAssignmentForm
from .services import InventoryService

# =========================
# DASHBOARD / LIST
# =========================
class AssetListView(LoginRequiredMixin, ListView):
    model = Asset
    template_name = 'inventory/list.html'
    context_object_name = 'assets'
    paginate_by = 25  # Increased for production use

    def get_queryset(self):
        queryset = Asset.objects.select_related('balance').prefetch_related('assignments')
        
        # 1. Advanced Searching
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(asset_code__icontains=search) |
                Q(brand__icontains=search) |
                Q(model_number__icontains=search) |
                Q(description__icontains=search)
            )
            
        # 2. Detailed Filtering
        asset_type = self.request.GET.get('asset_type')
        if asset_type:
            queryset = queryset.filter(asset_type=asset_type)

        brand = self.request.GET.get('brand')
        if brand:
            queryset = queryset.filter(brand=brand)

        is_serialized = self.request.GET.get('is_serialized')
        if is_serialized in ['0', '1']:
            queryset = queryset.filter(is_serialized=(is_serialized == '1'))
            
        stock_status = self.request.GET.get('stock_status')
        if stock_status == 'low':
            queryset = queryset.filter(balance__quantity__lt=F('min_stock_level'))
        elif stock_status == 'out':
            queryset = queryset.filter(balance__quantity=0)
        elif stock_status == 'in':
            queryset = queryset.filter(balance__quantity__gt=0)

        # Price Filtering
        min_price = self.request.GET.get('min_price')
        if min_price:
            queryset = queryset.filter(default_selling_price__gte=min_price)
        max_price = self.request.GET.get('max_price')
        if max_price:
            queryset = queryset.filter(default_selling_price__lte=max_price)
            
        # 3. Dynamic Sorting
        sort = self.request.GET.get('sort', '-created_at')
        sort_map = {
            'name': 'name',
            '-name': '-name',
            'code': 'asset_code',
            '-code': '-asset_code',
            'stock': 'balance__quantity',
            '-stock': '-balance__quantity',
            'price': 'default_selling_price',
            '-price': '-default_selling_price',
            'created': 'created_at',
            '-created': '-created_at',
        }
        
        order_by = sort_map.get(sort, '-created_at')
        return queryset.order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_assets = Asset.objects.all()
        
        # Statistics
        context['total_count'] = all_assets.count()
        context['serialized_count'] = all_assets.filter(is_serialized=True).count()
        context['low_stock_count'] = InventoryBalance.objects.filter(
            quantity__lt=F('item__min_stock_level')
        ).count()
        
        # Performance optimization: aggregate inventory value
        total_value = all_assets.aggregate(
            total=Sum(F('balance__quantity') * F('default_selling_price'))
        )['total'] or 0
        context['total_inventory_value'] = total_value
        
        # Dynamic filter options
        context['brands'] = Asset.objects.values_list('brand', flat=True).distinct().exclude(brand="")
        context['asset_types'] = Asset.ASSET_TYPE
        
        # Current filter states
        context['current_search'] = self.request.GET.get('search', '')
        context['current_serialized'] = self.request.GET.get('is_serialized', '')
        context['current_stock_status'] = self.request.GET.get('stock_status', '')
        context['current_asset_type'] = self.request.GET.get('asset_type', '')
        context['current_brand'] = self.request.GET.get('brand', '')
        context['current_min_price'] = self.request.GET.get('min_price', '')
        context['current_max_price'] = self.request.GET.get('max_price', '')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        
        return context


# =========================
# ASSET CRUD
# =========================
class AssetCreateView(LoginRequiredMixin, CreateView):
    model = Asset
    form_class = AssetForm
    template_name = 'inventory/add.html'
    success_url = reverse_lazy('inventory:asset_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = False
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Asset '{form.cleaned_data['name']}' created successfully.")
        return super().form_valid(form)


class AssetUpdateView(LoginRequiredMixin, UpdateView):
    model = Asset
    form_class = AssetForm
    template_name = 'inventory/add.html'
    success_url = reverse_lazy('inventory:asset_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Asset '{form.cleaned_data['name']}' updated successfully.")
        return super().form_valid(form)


class AssetDetailView(LoginRequiredMixin, DetailView):
    model = Asset
    template_name = 'inventory/detail.html'
    context_object_name = 'asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignments'] = self.object.assignments.all().order_by('-issued_date')
        context['ledger'] = self.object.ledger_entries.all().order_by('-created_at')[:10] # Show last 10
        return context


class AssetDeleteView(LoginRequiredMixin, DeleteView):
    model = Asset
    success_url = reverse_lazy('inventory:asset_list')
    
    def post(self, request, *args, **kwargs):
        asset = self.get_object()
        asset.delete() # Uses soft delete from mixin
        messages.warning(request, f"Asset '{asset.name}' has been deleted (soft-delete).")
        return redirect(self.success_url)


# =========================
# ASSIGNMENT VIEWS
# =========================
class AssetAssignView(LoginRequiredMixin, CreateView):
    model = AssetAssignment
    form_class = AssetAssignmentForm
    template_name = 'inventory/assign_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.asset = get_object_or_404(Asset, pk=self.kwargs.get('id'))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['asset'] = self.asset
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asset'] = self.asset
        return context

    def form_valid(self, form):
        assignment = form.save(commit=False)
        assignment.asset = self.asset
        assignment.save()
        messages.success(self.request, f"Asset assigned to {assignment.staff_name}.")
        return redirect('inventory:asset_detail', pk=self.asset.pk)

class AssetReturnView(LoginRequiredMixin, View):
    def post(self, request, pk):
        assignment = get_object_or_404(AssetAssignment, pk=pk)
        assignment.status = 'returned'
        assignment.returned_date = timezone.now().date()
        assignment.save()
        messages.info(request, f"Asset returned from {assignment.staff_name}.")
        return redirect('inventory:asset_detail', pk=assignment.asset.pk)

class AssetStockAdjustmentView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/stock_adjustment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asset'] = get_object_or_404(Asset, pk=self.kwargs.get('pk'))
        return context

    def post(self, request, *args, **kwargs):
        asset = get_object_or_404(Asset, pk=self.kwargs.get('pk'))
        adjustment_type = request.POST.get('adjustment_type') # 'ADD' or 'REMOVE'
        quantity = int(request.POST.get('quantity', 0))
        reason = request.POST.get('reason', 'Manual Adjustment')

        try:
            with transaction.atomic():
                if adjustment_type == 'ADD':
                    InventoryService.record_stock_in(
                        asset=asset,
                        quantity=quantity,
                        reference_type='MANUAL_ADJUSTMENT',
                        reference_id=asset.id,
                        unit_price=asset.default_purchase_price
                    )
                    messages.success(request, f"Added {quantity} to stock.")
                elif adjustment_type == 'REMOVE':
                    InventoryService.record_stock_out(
                        asset=asset,
                        quantity=quantity,
                        reference_type='MANUAL_ADJUSTMENT',
                        reference_id=asset.id,
                        unit_selling_price=asset.default_selling_price,
                        issued_to="Manual Adjustment"
                    )
                    messages.success(request, f"Removed {quantity} from stock.")
                else:
                    messages.error(request, "Invalid adjustment type.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

        return redirect('inventory:asset_detail', pk=asset.pk)


# =========================
# AUDIT LOGS
# =========================
class InventoryLogListView(LoginRequiredMixin, ListView):
    model = InventoryLog
    template_name = 'inventory/log_list.html'
    context_object_name = 'logs'
    paginate_by = 50


# =========================
# PRODUCTION UTILITIES
# =========================
import csv
from django.http import HttpResponse

class AssetExportCSVView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Apply the same filtering as the list view
        queryset = AssetListView().get_queryset() # This is a bit hacky, better to move filtering to a mixin
        # For simplicity and robustness, let's just use the current filters from request
        list_view = AssetListView()
        list_view.request = request
        queryset = list_view.get_queryset()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="inventory_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Asset Code', 'Name', 'Brand', 'Model', 'Type', 'Total Stock', 'Selling Price', 'Total Value'])

        for asset in queryset:
            total_stock = asset.total_stock
            writer.writerow([
                asset.asset_code,
                asset.name,
                asset.brand or "N/A",
                asset.model_number or "N/A",
                asset.get_asset_type_display(),
                total_stock,
                asset.default_selling_price,
                total_stock * asset.default_selling_price
            ])

        return response


class AssetBulkDeleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        asset_ids = request.POST.getlist('asset_ids')
        if asset_ids:
            # Using soft delete (if implemented in model) or standard delete
            assets = Asset.objects.filter(pk__in=asset_ids)
            count = assets.count()
            # Loop through to trigger object-level soft delete if applicable
            for asset in assets:
                asset.delete()
            
            messages.warning(request, f"Successfully deleted {count} assets.")
        else:
            messages.error(request, "No assets selected for deletion.")
            
        return redirect('inventory:asset_list')
