from django.db import transaction
from django.db.models import F
from .models import (
    Asset, InventoryBalance, StockLedger, 
    SerialNumber, InventoryLog
)
from typing import Optional, List
import uuid

class InventoryService:
    @staticmethod
    @transaction.atomic
    def record_stock_in(
        asset: Asset, 
        quantity: int, 
        reference_type: str, 
        reference_id: uuid.UUID, 
        unit_price: Optional[float] = None,
        serial_numbers: Optional[List[str]] = None
    ):
        """
        Records incoming stock, updates balance, and logs the movement.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        # 1. Update Inventory Balance
        balance, created = InventoryBalance.objects.select_for_update().get_or_create(item=asset)
        balance.quantity = F('quantity') + quantity
        balance.save()

        # 2. Create Stock Ledger Entry
        total_price = (float(unit_price) * quantity) if unit_price else None
        StockLedger.objects.create(
            item=asset,
            quantity=quantity,
            movement_type='IN',
            reference_type=reference_type,
            reference_id=reference_id,
            unit_price=unit_price,
            total_price=total_price
        )

        # 3. Handle Serial Numbers if applicable
        if asset.is_serialized and serial_numbers:
            if len(serial_numbers) != quantity:
                raise ValueError(f"Expected {quantity} serial numbers, got {len(serial_numbers)}.")
            
            for sn in serial_numbers:
                SerialNumber.objects.create(
                    item=asset,
                    serial_number=sn,
                    purchase_price=unit_price,
                    status='IN_STOCK'
                )

        # 4. Log the action
        InventoryLog.objects.create(
            action="STOCK_IN",
            description=f"Received {quantity} {asset.unit} of {asset.name} via {reference_type}."
        )

    @staticmethod
    @transaction.atomic
    def record_stock_out(
        asset: Asset, 
        quantity: int, 
        reference_type: str, 
        reference_id: uuid.UUID,
        unit_selling_price: float,
        issued_to: str,
        serial_numbers: Optional[List[str]] = None
    ):
        """
        Records outgoing stock, validates availability, updates balance, and logs movement.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        # 1. Check and Update Balance
        balance = InventoryBalance.objects.select_for_update().filter(item=asset).first()
        if not balance or balance.quantity < quantity:
            raise ValueError(f"Insufficient stock for {asset.name}. Available: {balance.quantity if balance else 0}")

        balance.quantity = F('quantity') - quantity
        balance.save()

        # 2. Handle Serial Numbers
        if asset.is_serialized:
            if not serial_numbers or len(serial_numbers) != quantity:
                raise ValueError(f"Serial numbers required for serialized asset {asset.name}.")
            
            sns = SerialNumber.objects.filter(item=asset, serial_number__in=serial_numbers, status='IN_STOCK')
            if sns.count() != quantity:
                raise ValueError("One or more serial numbers are invalid or not in stock.")
            
            sns.update(status='ISSUED')

        # 3. Create Stock Ledger Entry
        StockLedger.objects.create(
            item=asset,
            quantity=quantity,
            movement_type='OUT',
            reference_type=reference_type,
            reference_id=reference_id,
            unit_price=unit_selling_price,
            total_price=float(unit_selling_price) * quantity
        )

        # 4. Log action
        InventoryLog.objects.create(
            action="STOCK_OUT",
            description=f"Issued {quantity} {asset.unit} of {asset.name} to {issued_to}."
        )

    @staticmethod
    @transaction.atomic
    def adjust_stock(asset: Asset, new_quantity: int, reason: str):
        """
        Manually adjusts the stock level.
        """
        balance, created = InventoryBalance.objects.select_for_update().get_or_create(item=asset)
        old_qty = balance.quantity
        diff = new_quantity - old_qty

        if diff == 0:
            return

        balance.quantity = new_quantity
        balance.save()

        StockLedger.objects.create(
            item=asset,
            quantity=abs(diff),
            movement_type='ADJUSTMENT',
            reference_type='MANUAL_ADJUSTMENT',
            description=reason
        )

        InventoryLog.objects.create(
            action="ADJUSTMENT",
            description=f"Adjusted {asset.name} from {old_qty} to {new_quantity}. Reason: {reason}"
        )
