from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.modules.auth.models import User
from app.modules.categories.models import Category
from app.modules.products.models import Product
from app.modules.orders.models import Order, OrderItem

# Routers
from app.modules.auth.router import router as auth_router
from app.modules.categories.router import router as categories_router
from app.modules.products.router import router as products_router
from app.modules.orders.router import router as orders_router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RestaurantApp API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(orders_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
    }