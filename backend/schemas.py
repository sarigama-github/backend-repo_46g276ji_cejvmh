from typing import Optional, Literal
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

# Collection: product
class Product(BaseModel):
    name: str = Field(..., description="Product name")
    sku: Optional[str] = Field(None, description="Stock keeping unit / code")
    variant: Optional[str] = Field(None, description="Size or variant, e.g., 10US, Large")
    category: Literal["Sneaker", "TCG", "Streetwear"] = "Sneaker"
    purchase_price: float = Field(..., ge=0)
    purchase_date: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["In Stock", "Listed", "Sold"] = "In Stock"
    image_url: Optional[HttpUrl] = None

# Collection: sale
class Sale(BaseModel):
    product_id: str = Field(..., description="Reference to product _id as string")
    sale_price: float = Field(..., ge=0)
    platform: Optional[str] = Field(None, description="Where it sold: StockX, eBay, etc.")
    platform_fee: float = Field(0, ge=0, description="Absolute fee amount in the same currency")
    shipping_cost: float = Field(0, ge=0)
    net_profit: Optional[float] = Field(None, description="Computed: sale_price - purchase_price - fees - shipping")
    sold_at: datetime = Field(default_factory=datetime.utcnow)
