from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId
from typing import List, Optional

from database import create_document, get_documents, collection
from schemas import Product, Sale

app = FastAPI(title="Reseller Dashboard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductOut(BaseModel):
    id: str
    name: str
    sku: Optional[str]
    variant: Optional[str]
    category: str
    purchase_price: float
    purchase_date: str
    status: str
    image_url: Optional[str]


@app.get("/test")
async def test():
    # quick db check
    try:
        collection("product").count_documents({})
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/products", response_model=ProductOut)
async def create_product(product: Product):
    doc = create_document("product", product.model_dump())
    return to_product_out(doc)


@app.get("/products", response_model=List[ProductOut])
async def list_products(status: Optional[str] = None, category: Optional[str] = None):
    filt = {}
    if status:
        filt["status"] = status
    if category:
        filt["category"] = category
    docs = get_documents("product", filt, limit=200)
    return [to_product_out(d) for d in docs]


class SaleIn(BaseModel):
    product_id: str
    sale_price: float
    platform: Optional[str] = None
    platform_fee: float = 0
    shipping_cost: float = 0


class SaleOut(BaseModel):
    id: str
    product_id: str
    sale_price: float
    platform: Optional[str]
    platform_fee: float
    shipping_cost: float
    net_profit: float
    sold_at: str


@app.post("/sales", response_model=SaleOut)
async def create_sale(payload: SaleIn):
    # fetch product to compute profit
    prod = collection("product").find_one({"_id": ObjectId(payload.product_id)})
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    net = payload.sale_price - float(prod.get("purchase_price", 0)) - payload.platform_fee - payload.shipping_cost
    sale_doc = create_document(
        "sale",
        {
            "product_id": payload.product_id,
            "sale_price": payload.sale_price,
            "platform": payload.platform,
            "platform_fee": payload.platform_fee,
            "shipping_cost": payload.shipping_cost,
            "net_profit": net,
        },
    )
    # mark product sold
    collection("product").update_one({"_id": prod["_id"]}, {"$set": {"status": "Sold"}})
    return to_sale_out(sale_doc)


@app.get("/analytics/kpis")
async def kpis():
    # aggregate KPIs
    products = list(collection("product").find({}))
    sales = list(collection("sale").find({}))

    total_investment = sum(float(p.get("purchase_price", 0)) for p in products)
    total_value = sum(float(p.get("purchase_price", 0)) for p in products if p.get("status") != "Sold")
    realized_profit = sum(float(s.get("net_profit", 0)) for s in sales)
    sold_count = len({s.get("product_id") for s in sales})
    roi = (realized_profit / total_investment * 100) if total_investment > 0 else 0

    return {
        "total_investment": round(total_investment, 2),
        "total_value": round(total_value, 2),
        "realized_profit": round(realized_profit, 2),
        "roi": round(roi, 2),
        "sold_count": sold_count,
    }


@app.get("/analytics/monthly")
async def monthly():
    # simple monthly profit bar data
    pipeline = [
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}},
                "profit": {"$sum": "$net_profit"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    result = list(collection("sale").aggregate(pipeline))
    return [{"month": r["_id"], "profit": round(float(r.get("profit", 0)), 2)} for r in result]


def to_product_out(doc) -> ProductOut:
    return ProductOut(
        id=str(doc.get("_id")),
        name=doc.get("name"),
        sku=doc.get("sku"),
        variant=doc.get("variant"),
        category=doc.get("category"),
        purchase_price=float(doc.get("purchase_price", 0)),
        purchase_date=str(doc.get("purchase_date")),
        status=doc.get("status"),
        image_url=doc.get("image_url"),
    )


def to_sale_out(doc) -> SaleOut:
    return SaleOut(
        id=str(doc.get("_id")),
        product_id=str(doc.get("product_id")),
        sale_price=float(doc.get("sale_price", 0)),
        platform=doc.get("platform"),
        platform_fee=float(doc.get("platform_fee", 0)),
        shipping_cost=float(doc.get("shipping_cost", 0)),
        net_profit=float(doc.get("net_profit", 0)),
        sold_at=str(doc.get("created_at")),
    )
