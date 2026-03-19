from django.contrib import admin
from .models import Proposal, Estimate,  Invoice, PriceLevel, ProductPrice

class ProductPriceInline(admin.TabularInline):
    model = ProductPrice
    extra = 1



@admin.register(PriceLevel)
class PriceLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'customer', 'price_level', 'total_amount', 'status', 'issue_date')
    list_filter = ('status', 'price_level', 'issue_date')
    search_fields = ('document_number', 'customer__name')

@admin.register(Estimate)
class EstimateAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'customer', 'price_level', 'total_amount', 'status', 'issue_date')
    list_filter = ('status', 'price_level', 'issue_date')
    search_fields = ('document_number', 'customer__name')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'customer', 'price_level', 'total_amount', 'status', 'issue_date')
    list_filter = ('status', 'price_level', 'issue_date')
    search_fields = ('document_number', 'customer__name')

admin.site.register(ProductPrice)
