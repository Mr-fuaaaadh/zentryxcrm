from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PurchaseItem, StockOut
from .services import InventoryService

@receiver(post_save, sender=PurchaseItem)
def handle_purchase_item_save(sender, instance, created, **kwargs):
    if created:
        InventoryService.record_stock_in(
            asset=instance.item,
            quantity=instance.quantity,
            reference_type='PURCHASE',
            reference_id=instance.purchase.id,
            unit_price=instance.unit_price
        )

@receiver(post_save, sender=StockOut)
def handle_stock_out_save(sender, instance, created, **kwargs):
    if created:
        InventoryService.record_stock_out(
            asset=instance.item,
            quantity=instance.quantity,
            reference_type='SALE/ISSUE',
            reference_id=instance.id,
            unit_selling_price=instance.unit_selling_price,
            issued_to=instance.issued_to
        )

from .models import Asset, InventoryBalance
@receiver(post_save, sender=Asset)
def handle_asset_save(sender, instance, created, **kwargs):
    if created:
        InventoryBalance.objects.get_or_create(item=instance)
