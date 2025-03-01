from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from ..core.db import get_db
from ..core.security import get_current_active_user
from ..models.user import User
from ..models.inventory import Product, InventoryItem
from ..models.sales import Sale, SaleItem, PaymentMethod
from ..schemas.sales import (
    SaleCreate,
    Sale as SaleSchema,
    SaleItem as SaleItemSchema
)

router = APIRouter(
    prefix="/sales",
    tags=["sales"]
)

@router.post("/", response_model=SaleSchema)
async def create_sale(
    sale: SaleCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    # Create new sale
    db_sale = Sale(
        user_id=current_user.id,
        customer_name=sale.customer_name,
        customer_email=sale.customer_email,
        customer_phone=sale.customer_phone,
        total_amount=sale.total_amount,
        payment_method=sale.payment_method
    )
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    
    # Add sale items and update inventory
    for item in sale.items:
        # Check if product exists
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            db.delete(db_sale)
            db.commit()
            raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found")
        
        # Check if sufficient inventory
        inventory = db.query(InventoryItem).filter(InventoryItem.product_id == item.product_id).first()
        if not inventory or inventory.quantity < item.quantity:
            db.delete(db_sale)
            db.commit()
            raise HTTPException(status_code=400, detail=f"Insufficient inventory for product {product.name}")
        
        # Create sale item
        db_sale_item = SaleItem(
            sale_id=db_sale.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price
        )
        db.add(db_sale_item)
        
        # Update inventory
        inventory.quantity -= item.quantity
        if inventory.quantity <= 0:
            inventory.status = StockStatus.OUT_OF_STOCK
        elif inventory.quantity < 5:  # Threshold for low stock
            inventory.status = StockStatus.LOW_STOCK
    
    db.commit()
    
    # Refresh sale to include items
    db_sale = db.query(Sale).filter(Sale.id == db_sale.id).first()
    return db_sale

@router.get("/", response_model=List[SaleSchema])
async def get_sales(
    skip: int = 0, 
    limit: int = 100, 
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Sale)
    
    # Filter by date range if provided
    if start_date:
        query = query.filter(Sale.created_at >= start_date)
    if end_date:
        # Add one day to include the end date
        next_day = end_date + timedelta(days=1)
        query = query.filter(Sale.created_at < next_day)
    
    sales = query.order_by(Sale.created_at.desc()).offset(skip).limit(limit).all()
    return sales

@router.get("/{sale_id}", response_model=SaleSchema)
async def get_sale(
    sale_id: int,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale