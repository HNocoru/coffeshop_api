from app.database import SessionLocal, Base, engine

from app.modules.auth.models import User
from app.modules.categories.models import Category
from app.modules.products.models import Product

from app.core.security import hash_password


def seed():

    db = SessionLocal()

    # crear tablas
    Base.metadata.create_all(bind=engine)

    # =========================
    # USERS
    # =========================

    users = [
        User(
            name="Admin",
            email="admin@test.com",
            role="admin",
            password_hash=hash_password("123456"),
        ),
        User(
            name="Caja",
            email="cashier@test.com",
            role="cashier",
            password_hash=hash_password("123456"),
        ),
        User(
            name="Mesero",
            email="waiter@test.com",
            role="waiter",
            password_hash=hash_password("123456"),
        ),
    ]

    for user in users:
        db.add(user)

    db.commit()

    # =========================
    # CATEGORIES
    # =========================

    drinks = Category(
        name="Bebidas",
    )

    coffee = Category(
        name="Café",
    )

    desserts = Category(
        name="Postres",
    )

    food = Category(
        name="Comida",
    )

    db.add_all([
        drinks,
        coffee,
        desserts,
        food,
    ])

    db.commit()

    db.refresh(drinks)
    db.refresh(coffee)
    db.refresh(desserts)
    db.refresh(food)

    # =========================
    # PRODUCTS
    # =========================

    products = [

        Product(
            name="Espresso",
            description="Café espresso",
            price=45,
            available=True,
            category_id=coffee.id,
        ),

        Product(
            name="Capuccino",
            description="Capuccino clásico",
            price=65,
            available=True,
            category_id=coffee.id,
        ),

        Product(
            name="Latte",
            description="Latte vainilla",
            price=70,
            available=True,
            category_id=coffee.id,
        ),

        Product(
            name="Cheesecake",
            description="Cheesecake de frutos rojos",
            price=90,
            available=True,
            category_id=desserts.id,
        ),

        Product(
            name="Brownie",
            description="Brownie chocolate",
            price=55,
            available=True,
            category_id=desserts.id,
        ),

        Product(
            name="Hamburguesa",
            description="Hamburguesa clásica",
            price=120,
            available=True,
            category_id=food.id,
        ),

        Product(
            name="Papas fritas",
            description="Orden grande",
            price=60,
            available=True,
            category_id=food.id,
        ),

        Product(
            name="Refresco",
            description="Lata 355ml",
            price=35,
            available=True,
            category_id=drinks.id,
        ),
    ]

    db.add_all(products)

    db.commit()

    db.close()

    print("Seed completado")


if __name__ == "__main__":
    seed()