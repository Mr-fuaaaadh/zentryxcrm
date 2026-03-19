import uuid
from django.db import models
from django.db.models import Sum, QuerySet
from django.utils import timezone


# =========================
# BASE UTILITIES
# =========================

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteMixin(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save()

    class Meta:
        abstract = True


class BaseModel(SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by and updated_by could be added if user model is defined

    class Meta:
        abstract = True


# =========================
# ASSET MASTER
# =========================
class Asset(BaseModel):
    ASSET_TYPE = (
        ('DEVICE', 'Device'),
        ('COMPONENT', 'Component'),
        ('ACCESSORY', 'Accessory'),
    )

    name = models.CharField(max_length=255, db_index=True)
    asset_code = models.CharField(max_length=100, unique=True, db_index=True, help_text="SKU / Unique Code")
    description = models.TextField(null=True, blank=True)
    
    brand = models.CharField(max_length=100, db_index=True, null=True, blank=True, default="")
    model_number = models.CharField(max_length=100, null=True, blank=True, default="")

    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE, default='DEVICE')

    default_purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    default_selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    is_serialized = models.BooleanField(default=True)
    unit = models.CharField(max_length=50, default="pcs")
    min_stock_level = models.PositiveIntegerField(default=5)

    class Meta:
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.asset_code})"

    @property
    def total_stock(self):
        return getattr(self.balance, 'quantity', 0)

    @property
    def available_stock(self):
        assigned_count = self.assignments.filter(status='assigned').count()
        return self.total_stock - assigned_count


# =========================
# SERIAL NUMBER TRACKING
# =========================
class SerialNumber(BaseModel):
    STATUS = (
        ('IN_STOCK', 'In Stock'),
        ('ISSUED', 'Issued'),
        ('DAMAGED', 'Damaged'),
        ('RETURNED', 'Returned'),
    )

    item = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='serial_numbers')

    serial_number = models.CharField(max_length=255, unique=True, db_index=True)

    # Price per device (important for enterprise)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=50, choices=STATUS, default='IN_STOCK')

    class Meta:
        verbose_name = "Serial Number"
        verbose_name_plural = "Serial Numbers"

    def __str__(self):
        return self.serial_number


# =========================
# INVENTORY BALANCE (FAST ACCESS)
# =========================
class InventoryBalance(BaseModel):
    item = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name='balance')
    quantity = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Inventory Balance"
        verbose_name_plural = "Inventory Balances"

    def __str__(self):
        return f"{self.item.name}: {self.quantity}"


# =========================
# STOCK LEDGER (CORE SYSTEM)
# =========================
class StockLedger(BaseModel):
    MOVEMENT_TYPE = (
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUSTMENT', 'Adjustment'),
    )

    item = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='ledger_entries')

    quantity = models.IntegerField()

    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE)

    reference_type = models.CharField(max_length=50)  
    # PURCHASE / ISSUE / RETURN / MANUAL

    reference_id = models.UUIDField(null=True, blank=True)

    # Financial tracking
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Stock Ledger"
        verbose_name_plural = "Stock Ledgers"
        ordering = ['-created_at']


# =========================
# SUPPLIER
# =========================
class Supplier(BaseModel):
    name = models.CharField(max_length=255, db_index=True)
    contact_person = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True, unique=True)
    address = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"

    def __str__(self):
        return self.name


# =========================
# PURCHASE (HEADER)
# =========================
class Purchase(BaseModel):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchases')

    invoice_number = models.CharField(max_length=100, unique=True, db_index=True)
    purchase_date = models.DateField(default=timezone.now)

    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"
        ordering = ['-purchase_date']

    def update_total(self):
        total = self.items.aggregate(
            total=Sum('total_price')
        )['total'] or 0

        self.total_amount = total
        self.save(update_fields=['total_amount'])


# =========================
# PURCHASE ITEMS (REAL COST)
# =========================
class PurchaseItem(BaseModel):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='purchase_items')

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = "Purchase Item"
        verbose_name_plural = "Purchase Items"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

        # Update purchase total
        self.purchase.update_total()


# =========================
# STOCK OUT (SALES / ISSUE)
# =========================
class StockOut(BaseModel):
    item = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='stock_outs')

    quantity = models.PositiveIntegerField()

    # Selling
    unit_selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_selling_price = models.DecimalField(max_digits=14, decimal_places=2)

    # Cost tracking
    unit_cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost_price = models.DecimalField(max_digits=14, decimal_places=2)

    # Profit
    profit = models.DecimalField(max_digits=14, decimal_places=2)

    issued_to = models.CharField(max_length=255, db_index=True)
    purpose = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Stock Out"
        verbose_name_plural = "Stock Outs"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.total_selling_price = self.quantity * self.unit_selling_price
        self.total_cost_price = self.quantity * self.unit_cost_price
        self.profit = self.total_selling_price - self.total_cost_price

        super().save(*args, **kwargs)


# =========================
# INVENTORY LOG (AUDIT)
# =========================
class InventoryLog(BaseModel):
    action = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    
    # Optional metadata (JSON could be used for extra flexibility)
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Inventory Log"
        verbose_name_plural = "Inventory Logs"
        ordering = ['-created_at']


# =========================
# ASSET ASSIGNMENT (ISSUANCE)
# =========================
class AssetAssignment(BaseModel):
    STATUS = (
        ('assigned', 'Assigned'),
        ('returned', 'Returned'),
    )
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='assignments')
    staff_name = models.CharField(max_length=255)
    
    quantity = models.PositiveIntegerField(default=1)
    serial_number = models.ForeignKey(SerialNumber, on_delete=models.SET_NULL, null=True, blank=True)
    
    issued_date = models.DateField(default=timezone.now)
    returned_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS, default='assigned')
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Asset Assignment"
        verbose_name_plural = "Asset Assignments"

    def __str__(self):
        return f"{self.asset.name} assigned to {self.staff_name}"