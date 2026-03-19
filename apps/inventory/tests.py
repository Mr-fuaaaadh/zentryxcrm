from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Asset, Supplier, Purchase, InventoryBalance, StockLedger, SerialNumber
from .services import InventoryService
import uuid

class InventoryModelTests(TestCase):
    def setUp(self):
        self.asset = Asset.objects.create(
            name="Test Device",
            asset_code="TD-001",
            brand="TestBrand",
            model_number="M1",
            asset_type="DEVICE",
            default_purchase_price=100.00,
            default_selling_price=150.00,
            is_serialized=True
        )

    def test_asset_creation_auto_creates_balance(self):
        """Signals should create an InventoryBalance for each new asset."""
        balance = InventoryBalance.objects.get(item=self.asset)
        self.assertEqual(balance.quantity, 0)

    def test_soft_delete(self):
        """Verify that assets are not actually deleted from DB."""
        asset_id = self.asset.id
        self.asset.delete()
        
        # Should not be in default objects
        self.assertFalse(Asset.objects.filter(id=asset_id).exists())
        # Should be in all_objects
        self.assertTrue(Asset.all_objects.filter(id=asset_id).exists())


class InventoryServiceTests(TestCase):
    def setUp(self):
        self.asset = Asset.objects.create(
            name="Laptop",
            asset_code="LP-99",
            brand="BrandX",
            model_number="B1",
            asset_type="DEVICE",
            default_purchase_price=500.00,
            default_selling_price=800.00,
            is_serialized=True
        )
        self.ref_id = uuid.uuid4()

    def test_stock_in_single(self):
        """Test recording stock in with serial numbers."""
        InventoryService.record_stock_in(
            item=self.asset,
            quantity=1,
            reference_type='PURCHASE',
            reference_id=self.ref_id,
            unit_price=500.00,
            serial_numbers=['SN-LP-001']
        )
        
        balance = InventoryBalance.objects.get(item=self.asset)
        self.assertEqual(balance.quantity, 1)
        
        ledger = StockLedger.objects.get(item=self.asset, movement_type='IN')
        self.assertEqual(ledger.quantity, 1)
        
        sn = SerialNumber.objects.get(serial_number='SN-LP-001')
        self.assertEqual(sn.status, 'IN_STOCK')

    def test_stock_out_insufficient_stock(self):
        """Test that stock out fails if balance is low."""
        with self.assertRaises(ValueError):
            InventoryService.record_stock_out(
                item=self.asset,
                quantity=10,
                reference_type='SALE',
                reference_id=uuid.uuid4(),
                unit_selling_price=800.0,
                issued_to="John Doe"
            )

    def test_complete_workflow(self):
        """Stock In -> Stock Out -> Balance Check."""
        # 1. Stock In
        InventoryService.record_stock_in(
            item=self.asset,
            quantity=2,
            reference_type='PURCHASE',
            reference_id=self.ref_id,
            serial_numbers=['SN-01', 'SN-02']
        )
        
        # 2. Stock Out
        InventoryService.record_stock_out(
            item=self.asset,
            quantity=1,
            reference_type='SALE',
            reference_id=uuid.uuid4(),
            unit_selling_price=800.0,
            issued_to="Buyer A",
            serial_numbers=['SN-01']
        )
        
        # 3. Check Balance
        balance = InventoryBalance.objects.get(item=self.asset)
        self.assertEqual(balance.quantity, 1)
        
        # 4. Check SN status
        sn1 = SerialNumber.objects.get(serial_number='SN-01')
        self.assertEqual(sn1.status, 'ISSUED')
        
        sn2 = SerialNumber.objects.get(serial_number='SN-02')
        self.assertEqual(sn2.status, 'IN_STOCK')
