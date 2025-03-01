# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum
from datetime import datetime

class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    STAFF = "staff"
    INTERN = "intern"

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.STAFF
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class User(UserInDB):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None

# app/schemas/inventory.py
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime

class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"

# Category schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CategoryInDB(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Category(CategoryInDB):
    pass

# Product schemas
class ProductBase(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None
    model_number: Optional[str] = None
    specifications: Optional[str] = None
    cost_price: float = Field(..., gt=0)
    selling_price: float = Field(..., gt=0)
    barcode: Optional[str] = None
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    model_number: Optional[str] = None
    specifications: Optional[str] = None
    cost_price: Optional[float] = Field(None, gt=0)
    selling_price: Optional[float] = Field(None, gt=0)
    barcode: Optional[str] = None
    image_url: Optional[str] = None

class ProductInDB(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Product(ProductInDB):
    pass

class ProductWithStock(Product):
    current_stock: int
    status: StockStatus

# Inventory schemas
class InventoryItemBase(BaseModel):
    product_id: int
    quantity: int = 0
    location: Optional[str] = None
    status: StockStatus = StockStatus.IN_STOCK

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(BaseModel):
    quantity: Optional[int] = None
    location: Optional[str] = None
    status: Optional[StockStatus] = None

class InventoryItemInDB(InventoryItemBase):
    id: int
    last_updated: datetime

    class Config:
        orm_mode = True

class InventoryItem(InventoryItemInDB):
    pass

class InventoryItemWithProduct(InventoryItem):
    product: Product

# app/schemas/sales.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from enum import Enum
from datetime import datetime

class PaymentMethod(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    MOBILE_PAYMENT = "mobile_payment"

# Sale Item schemas
class SaleItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    total_price: float = Field(..., gt=0)

class SaleItemCreate(SaleItemBase):
    pass

class SaleItemInDB(SaleItemBase):
    id: int
    sale_id: int

    class Config:
        orm_mode = True

class SaleItem(SaleItemInDB):
    pass

# Sale schemas
class SaleBase(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    total_amount: float = Field(..., gt=0)
    payment_method: PaymentMethod = PaymentMethod.CASH

class SaleCreate(SaleBase):
    items: List[SaleItemCreate]

class SaleInDB(SaleBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class Sale(SaleInDB):
    items: List[SaleItem]