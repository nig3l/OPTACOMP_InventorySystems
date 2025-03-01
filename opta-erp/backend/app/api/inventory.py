# app/api/inventory.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.db import get_db
from ..core.security import get_current_active_user
from ..models.user import User
from ..models.inventory import Category, Product, InventoryItem, StockStatus
from ..schemas.inventory import (
    Category as CategorySchema,
    CategoryCreate,
    CategoryUpdate,
    Product as ProductSchema,
    ProductCreate,
    ProductUpdate,
    InventoryItem as InventoryItemSchema,
    InventoryItemCreate,
    InventoryItemUpdate,
    ProductWithStock
)

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"]
)

# Category endpoints
@router.post("/categories", response_model=CategorySchema)
async def create_category(category: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/categories", response_model=List[CategorySchema])
async def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories

@router.get("/categories/{category_id}", response_model=CategorySchema)
async def read_category(category_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

@router.put("/categories/{category_id}", response_model=CategorySchema)
async def update_category(category_id: int, category: CategoryUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = category.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/categories/{category_id}")
async def delete_category(category_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db.delete(db_category)
    db.commit()
    return {"message": "Category deleted successfully"}

# Product endpoints
@router.post("/products", response_model=ProductSchema)
async def create_product(product: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Check if category exists
    category = db.query(Category).filter(Category.id == product.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Initialize inventory with zero quantity
    inventory_item = InventoryItem(product_id=db_product.id, quantity=0, status=StockStatus.OUT_OF_STOCK)
    db.add(inventory_item)
    db.commit()
    
    return db_product

@router.get("/products", response_model=List[ProductWithStock])
async def read_products(
    skip: int = 0, 
    limit: int = 100, 
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Product, InventoryItem).join(InventoryItem, Product.id == InventoryItem.product_id, isouter=True)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search_term)) | 
            (Product.model_number.ilike(search_term)) |
            (Product.description.ilike(search_term))
        )
    
    results = query.offset(skip).limit(limit).all()
    
    products_with_stock = []
    for product, inventory in results:
        product_dict = {**ProductSchema.from_orm(product).dict()}
        
        # Add inventory information
        if inventory:
            product_dict["current_stock"] = inventory.quantity
            product_dict["status"] = inventory.status
        else:
            product_dict["current_stock"] = 0
            product_dict["status"] = StockStatus.OUT_OF_STOCK
        
        products_with_stock.append(ProductWithStock(**product_dict))
    
    return products_with_stock

@router.get("/products/{product_id}", response_model=ProductWithStock)
async def read_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get inventory information
    inventory = db.query(InventoryItem).filter(InventoryItem.product_id == product_id).first()
    
    product_dict = {**ProductSchema.from_orm(db_product).dict()}
    
    # Add inventory information
    if inventory:
        product_dict["current_stock"] = inventory.quantity
        product_dict["status"] = inventory.status
    else:
        product_dict["current_stock"] = 0
        product_dict["status"] = StockStatus.OUT_OF_STOCK
    
    return ProductWithStock(**product_dict)

@router.put("/products/{product_id}", response_model=ProductSchema)
async def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product.dict(exclude_unset=True)
    
    # Check if category exists if it's being updated
    if "category_id" in update_data:
        category = db.query(Category).filter(Category.id == update_data["category_id"]).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Delete associated inventory item first
    db.query(InventoryItem).filter(InventoryItem.product_id == product_id).delete()
    
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}

# Inventory endpoints
@router.put("/inventory/{product_id}", response_model=InventoryItemSchema)
async def update_inventory(
    product_id: int, 
    inventory_data: InventoryItemUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if inventory item exists, create if not
    inventory_item = db.query(InventoryItem).filter(InventoryItem.product_id == product_id).first()
    if not inventory_item:
        inventory_item = InventoryItem(product_id=product_id)