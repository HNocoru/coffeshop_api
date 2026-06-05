# SPEC.md — RestaurantApp 🍽️

> Documento de especificación para OpenCode / agentes de codificación IA.
> Contiene contexto arquitectónico completo, decisiones técnicas y tareas atomizadas.

---

## 0. Contexto del Proyecto

Aplicación móvil transaccional para gestión de pedidos de restaurante.
Compuesta por dos proyectos independientes que se comunican vía REST:

| Componente | Stack | Directorio |
|---|---|---|
| **Backend** | Python · FastAPI · SQLAlchemy · SQLite · uv | `restaurant-api/` |
| **Frontend** | Flutter · Provider · http · Material 3 | `restaurant-app/` |

---

## 1. Arquitectura General

### Principio fundamental
El backend y el frontend están **desacoplados por contrato HTTP**.
El frontend nunca conoce la implementación interna del backend — solo conoce los endpoints.

### Analogía de referencia (para entender las decisiones)
Toda la estructura sigue el modelo de **Arquitectura Hexagonal**:

```
  [ Flutter UI ]
       │  HTTP (puerto de entrada)
  [ FastAPI Router ]      ← Adaptador de entrada
       │
  [ Service ]             ← Lógica de dominio (pura, sin frameworks)
       │
  [ SQLAlchemy Model ]    ← Adaptador de salida (puerto hacia DB)
       │
  [ SQLite ]
```

**Regla clave:** El `service.py` de cada módulo NUNCA importa FastAPI ni SQLAlchemy directamente desde una capa de presentación — solo opera sobre entidades del dominio.

---

## 2. Backend — `restaurant-api/`

### 2.1 Stack y herramientas

```
Python 3.12+
uv               → gestor de entornos y dependencias (reemplaza pip+venv)
FastAPI          → framework web
SQLAlchemy       → ORM
SQLite           → base de datos (archivo local restaurant.db)
python-jose      → JWT tokens
passlib[bcrypt]  → hashing de contraseñas
```

### 2.2 Setup con uv

```bash
uv init restaurant-api
cd restaurant-api
uv add "fastapi[standard]" sqlalchemy "python-jose[cryptography]" "passlib[bcrypt]" python-multipart
uv add --dev pytest httpx
```

### 2.3 Estructura de directorios

```
restaurant-api/
├── pyproject.toml
├── .env
├── restaurant.db                    ← generado automático al correr
└── app/
    ├── main.py                      ← FastAPI app, registra routers, crea tablas
    ├── database.py                  ← engine SQLite + SessionLocal + Base
    ├── dependencies.py              ← get_db(), get_current_user()
    ├── core/
    │   ├── config.py                ← Settings con pydantic-settings
    │   └── security.py              ← hash_password, create_access_token, decode_token
    └── modules/
        ├── auth/
        │   ├── models.py            ← User (SQLAlchemy)
        │   ├── schemas.py           ← UserCreate, UserLogin, TokenResponse
        │   ├── service.py           ← register_user(), login_user()
        │   └── router.py            ← POST /api/auth/register, /api/auth/login
        ├── categories/
        │   ├── models.py            ← Category
        │   ├── schemas.py           ← CategoryCreate, CategoryRead
        │   ├── service.py           ← get_all, get_by_id, create, update, delete
        │   └── router.py            ← GET/POST/PUT/DELETE /api/categories
        ├── products/
        │   ├── models.py            ← Product (FK → Category)
        │   ├── schemas.py           ← ProductCreate, ProductRead
        │   ├── service.py
        │   └── router.py            ← GET/POST/PUT/DELETE /api/products
        └── orders/
            ├── models.py            ← Order + OrderItem + OrderStatus(Enum)
            ├── schemas.py           ← OrderCreate, OrderRead, OrderUpdateStatus
            ├── service.py           ← create() transaccional, update_status()
            └── router.py            ← GET/POST/PUT/DELETE /api/orders
```

### 2.4 Modelo de datos

```sql
-- users
id INTEGER PK, name TEXT, email TEXT UNIQUE, password_hash TEXT,
role TEXT DEFAULT 'waiter',  -- 'admin' | 'waiter'
created_at DATETIME

-- categories
id INTEGER PK, name TEXT, description TEXT, created_at DATETIME

-- products
id INTEGER PK, name TEXT, description TEXT, price REAL,
image_url TEXT, available INTEGER DEFAULT 1,
category_id INTEGER FK(categories.id), created_at DATETIME

-- orders
id INTEGER PK, table_number INTEGER, status TEXT DEFAULT 'pending',
-- status ENUM: pending | preparing | ready | delivered
notes TEXT, total REAL DEFAULT 0,
user_id INTEGER FK(users.id),
created_at DATETIME, updated_at DATETIME

-- order_items
id INTEGER PK, order_id INTEGER FK(orders.id),
product_id INTEGER FK(products.id),
quantity INTEGER, unit_price REAL, subtotal REAL
```

### 2.5 Endpoints REST completos

```
# AUTH (sin token requerido)
POST   /api/auth/register     body: { name, email, password }
POST   /api/auth/login        body: { email, password } → { access_token, token_type }

# CATEGORIES (requiere Bearer token)
GET    /api/categories
GET    /api/categories/{id}
POST   /api/categories        body: { name, description }
PUT    /api/categories/{id}   body: { name?, description? }
DELETE /api/categories/{id}

# PRODUCTS (requiere Bearer token)
GET    /api/products
GET    /api/products/{id}
POST   /api/products          body: { name, description, price, image_url, category_id }
PUT    /api/products/{id}     body: campos opcionales
DELETE /api/products/{id}

# ORDERS (requiere Bearer token)  ← CRUD principal del informe
GET    /api/orders
GET    /api/orders/{id}
POST   /api/orders            body: { table_number, notes?, items: [{product_id, quantity}] }
PUT    /api/orders/{id}       body: { status }  ← transición de estado
DELETE /api/orders/{id}
```

### 2.6 Reglas de negocio del dominio Orders

```
TRANSICIÓN DE ESTADOS (State Machine):
  pending → preparing → ready → delivered

REGLAS:
  - Al crear una Order, se calculan automáticamente unit_price y subtotal por item
  - El total de la Order = suma de todos los subtotales
  - No se puede hacer DELETE de una orden en estado 'delivered'
  - El status solo puede avanzar (no retroceder)
```

### 2.7 Archivos de implementación clave

#### `app/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLITE_URL = "sqlite:///./restaurant.db"
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass
```

#### `app/core/config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas

    class Config:
        env_file = ".env"

settings = Settings()
```

#### `app/dependencies.py`
```python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.core.security import decode_token
from app.modules.auth.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)
        user_id: int = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user
```

#### `app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.modules.auth.router      import router as auth_router
from app.modules.categories.router import router as categories_router
from app.modules.products.router   import router as products_router
from app.modules.orders.router     import router as orders_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RestaurantApp API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(orders_router)
```

### 2.8 Correr el backend

```bash
# Desarrollo
uv run fastapi dev app/main.py

# Producción
uv run fastapi run app/main.py --host 0.0.0.0 --port 8000

# Docs interactivas
http://127.0.0.1:8000/docs
```

---

## 3. Frontend — `restaurant-app/`

### 3.1 Stack y dependencias Flutter

```yaml
# pubspec.yaml — dependencias clave
dependencies:
  flutter:
    sdk: flutter
  provider: ^6.1.2          # gestión de estado (OBLIGATORIO)
  http: ^1.2.1              # cliente HTTP (OBLIGATORIO)
  shared_preferences: ^2.2.3 # persistir JWT token localmente

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^4.0.0
```

### 3.2 Estructura de directorios (Screaming Architecture + Vertical Slicing)

```
lib/
├── main.dart                          ← registra MultiProvider, define rutas
│
├── core/
│   ├── theme/
│   │   └── app_theme.dart             ← Material Theme 3.0 (colores, tipografía)
│   ├── network/
│   │   └── api_client.dart            ← wrapper http: get/post/put/delete + inject token
│   ├── di/
│   │   └── injector.dart              ← inyección manual de dependencias
│   └── routes/
│       └── app_routes.dart            ← constantes de rutas + Navigator 1.0
│
└── features/
    │
    ├── auth/                           ← Feature: Login / Register
    │   ├── data/
    │   │   ├── models/
    │   │   │   └── user_model.dart     ← fromJson / toJson
    │   │   └── repositories/
    │   │       └── auth_repository_impl.dart
    │   ├── domain/
    │   │   ├── entities/
    │   │   │   └── user.dart           ← clase pura, sin dependencias
    │   │   └── repositories/
    │   │       └── auth_repository.dart  ← interfaz abstracta (puerto)
    │   └── presentation/
    │       ├── viewmodels/
    │       │   └── auth_viewmodel.dart   ← extends ChangeNotifier
    │       └── pages/
    │           ├── login_page.dart
    │           └── register_page.dart
    │
    ├── products/                        ← Feature: Menú / Catálogo
    │   ├── data/
    │   │   ├── models/
    │   │   │   └── product_model.dart
    │   │   └── repositories/
    │   │       └── product_repository_impl.dart
    │   ├── domain/
    │   │   ├── entities/
    │   │   │   └── product.dart
    │   │   └── repositories/
    │   │       └── product_repository.dart
    │   └── presentation/
    │       ├── viewmodels/
    │       │   └── product_viewmodel.dart
    │       └── pages/
    │           └── menu_page.dart       ← GridView de productos por categoría
    │
    └── orders/                          ← Feature: CRUD principal
        ├── data/
        │   ├── models/
        │   │   ├── order_model.dart
        │   │   └── order_item_model.dart
        │   └── repositories/
        │       └── order_repository_impl.dart
        ├── domain/
        │   ├── entities/
        │   │   ├── order.dart
        │   │   └── order_item.dart
        │   └── repositories/
        │       └── order_repository.dart
        └── presentation/
            ├── viewmodels/
            │   └── order_viewmodel.dart
            └── pages/
                ├── order_list_page.dart    ← ListTile de pedidos activos
                ├── create_order_page.dart  ← seleccionar productos + crear pedido
                └── order_detail_page.dart  ← ver detalle + cambiar estado
```

### 3.3 Rutas de navegación (Navigator 1.0)

```dart
// core/routes/app_routes.dart
class AppRoutes {
  static const String login         = '/login';
  static const String register      = '/register';
  static const String menu          = '/menu';
  static const String orderList     = '/orders';
  static const String createOrder   = '/orders/new';
  static const String orderDetail   = '/orders/detail';
}

// Uso (Navigator 1.0 — sin go_router):
Navigator.pushNamed(context, AppRoutes.orderList);
Navigator.pushNamed(context, AppRoutes.orderDetail, arguments: orderId);
```

### 3.4 Patrón MVVM con Provider

```
CreateOrderPage (View)
    │  Consumer<OrderViewModel> / context.watch<OrderViewModel>()
    │  context.read<OrderViewModel>().createOrder(...)
    │
OrderViewModel (ViewModel) extends ChangeNotifier
    │  ViewState _state = ViewState.idle | loading | success | error
    │  List<Order> _orders = []
    │  notifyListeners()
    │  llama a: _repository.create(payload)
    │
OrderRepository (interfaz — Domain)      ← Puerto abstracto
    │
OrderRepositoryImpl (Data)               ← Adaptador concreto
    │  ApiClient.post('/api/orders', body)
    │
REST API (FastAPI backend)
```

### 3.5 ViewState — enum compartido para todos los ViewModels

```dart
// core/utils/view_state.dart
enum ViewState { idle, loading, success, error }
```

Todos los ViewModels exponen `ViewState get state` para que la UI decida qué widget mostrar.

### 3.6 ApiClient — wrapper sobre `http`

```dart
// core/network/api_client.dart
// Responsabilidades:
// - Adjuntar header Authorization: Bearer <token> en cada request
// - Lanzar excepciones tipadas según status HTTP (401, 404, 500)
// - Centralizar la base URL (BASE_URL = 'http://10.0.2.2:8000' en Android emulator)
```

> `10.0.2.2` en Android Emulator apunta a `localhost` del host — equivale a `127.0.0.1` para el backend.

### 3.7 Inyección de dependencias manual

```dart
// core/di/injector.dart
// Se instancian las dependencias UNA VEZ y se pasan como argumentos:
//
// ApiClient apiClient = ApiClient();
// AuthRepositoryImpl authRepo = AuthRepositoryImpl(apiClient);
// AuthViewModel authViewModel = AuthViewModel(authRepo);
//
// Luego en main.dart se usan con MultiProvider:
// ChangeNotifierProvider(create: (_) => authViewModel)
```

### 3.8 Material Theme 3.0

```dart
// core/theme/app_theme.dart
// Paleta sugerida para RestaurantApp:
//   seedColor: Color(0xFFE65100)  ← naranja restaurante
//   useMaterial3: true
//
// ThemeData.from(
//   colorScheme: ColorScheme.fromSeed(seedColor: Color(0xFFE65100)),
//   useMaterial3: true,
// )
```

### 3.9 Widgets clave por pantalla

| Pantalla | Widgets obligatorios del proyecto |
|---|---|
| `login_page` | `Card`, `TextField`, `ElevatedButton` |
| `register_page` | `Card`, `TextField`, `ElevatedButton` |
| `menu_page` | `GridView.builder`, `Card`, `Stack` (badge disponible) |
| `order_list_page` | `CustomScrollView`, `SliverList`, `ListTile`, `Chip` (estado) |
| `create_order_page` | `ListTile` (productos), `FloatingActionButton` |
| `order_detail_page` | `Card`, `ListTile`, `SegmentedButton` (cambiar estado) |

---

## 4. Flujo completo de una operación (POST /api/orders)

```
1. Usuario selecciona productos en CreateOrderPage
2. Tap "Crear Pedido" → context.read<OrderViewModel>().createOrder(items, table)
3. OrderViewModel:
   - _state = ViewState.loading → notifyListeners()
   - await _repository.create(payload)
4. OrderRepositoryImpl:
   - apiClient.post('/api/orders', body: { table_number, items: [...] })
   - http.post con header Authorization: Bearer <token>
5. FastAPI router recibe el request
6. get_current_user() valida JWT → extrae user_id
7. order service.create():
   - Para cada item: busca Product, calcula subtotal
   - Crea Order + todos los OrderItems en una transacción DB
   - Retorna OrderRead
8. Response 201 → OrderModel.fromJson(json)
9. OrderViewModel:
   - _state = ViewState.success → notifyListeners()
10. CreateOrderPage re-renderiza → navega a OrderListPage
```

---

## 5. Tareas atomizadas para OpenCode

> Ejecutar en orden. Cada tarea es independiente y verificable.

### BACKEND

```
TASK-B01: Crear estructura base con uv
  - uv init restaurant-api
  - agregar todas las dependencias listadas en 2.2
  - crear archivo .env con SECRET_KEY

TASK-B02: Implementar app/database.py y app/core/config.py

TASK-B03: Implementar app/core/security.py
  - hash_password(), verify_password()
  - create_access_token(), decode_token()

TASK-B04: Implementar módulo auth/
  - models.py: tabla users
  - schemas.py: UserCreate, UserLogin, TokenResponse
  - service.py: register_user(), login_user()
  - router.py: POST /api/auth/register y /api/auth/login

TASK-B05: Implementar app/dependencies.py
  - get_db()
  - get_current_user()

TASK-B06: Implementar módulo categories/ (CRUD completo)

TASK-B07: Implementar módulo products/ (CRUD completo, FK categories)

TASK-B08: Implementar módulo orders/
  - models.py: Order + OrderItem + OrderStatus enum
  - schemas.py: con composición OrderCreate → items[]
  - service.py: create() transaccional, update_status() con validación de flujo
  - router.py: los 4 verbos HTTP

TASK-B09: Implementar app/main.py
  - registrar todos los routers
  - Base.metadata.create_all()
  - CORS middleware

TASK-B10: Verificar con uv run fastapi dev app/main.py
  - probar todos los endpoints en http://127.0.0.1:8000/docs
```

### FRONTEND

```
TASK-F01: Crear proyecto Flutter
  - flutter create restaurant_app
  - agregar dependencias en pubspec.yaml (provider, http, shared_preferences)

TASK-F02: Implementar core/theme/app_theme.dart
  - Material Theme 3.0 con seed naranja

TASK-F03: Implementar core/network/api_client.dart
  - Métodos: get, post, put, delete
  - Inyectar token desde SharedPreferences
  - BASE_URL configurable

TASK-F04: Implementar feature auth/ completa
  - User entity, UserModel, AuthRepository interface
  - AuthRepositoryImpl con ApiClient
  - AuthViewModel: login(), register(), logout()
  - LoginPage y RegisterPage con validación de formularios

TASK-F05: Implementar core/di/injector.dart y main.dart
  - MultiProvider con todos los ViewModels
  - Rutas registradas con onGenerateRoute

TASK-F06: Implementar feature products/ 
  - Product entity, ProductModel
  - ProductViewModel: loadProducts(), filterByCategory()
  - MenuPage con GridView.builder + Card

TASK-F07: Implementar feature orders/ — parte 1 (Read)
  - Order + OrderItem entities y models
  - OrderViewModel: loadOrders()
  - OrderListPage con CustomScrollView + SliverList + ListTile

TASK-F08: Implementar feature orders/ — parte 2 (Create)
  - OrderViewModel: createOrder()
  - CreateOrderPage: selección de items, resumen, submit

TASK-F09: Implementar feature orders/ — parte 3 (Update + Delete)
  - OrderViewModel: updateStatus(), deleteOrder()
  - OrderDetailPage: Card de detalle + SegmentedButton para cambiar estado
```

---

## 6. Convenciones de código

### Python (Backend)
- Snake_case para variables y funciones
- PascalCase para clases
- Docstrings en servicios con lógica compleja
- Cada `service.py` recibe `db: Session` como primer argumento
- Los routers solo llaman a servicios — no lógica directa

### Dart/Flutter (Frontend)
- camelCase para variables y métodos
- PascalCase para clases y widgets
- Cada `ViewModel` expone: `ViewState get state`, el dato principal, y los métodos de acción
- Las `Page` no acceden al `Repository` directamente — solo al `ViewModel`
- Los `Model` implementan `fromJson` y `toJson`

---

## 7. Variables de entorno

### Backend `.env`
```
SECRET_KEY=tu_clave_secreta_muy_larga_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Flutter — `core/network/api_client.dart`
```dart
// Cambiar según entorno:
// Android Emulator → http://10.0.2.2:8000
// iOS Simulator   → http://127.0.0.1:8000
// Dispositivo físico → http://<IP-local-PC>:8000
// Producción → https://tu-api.onrender.com
static const String baseUrl = 'http://10.0.2.2:8000';
```

---

## 8. Despliegue en Render

```yaml
# render.yaml
services:
  - type: web
    name: restaurant-api
    runtime: python
    buildCommand: "pip install uv && uv sync"
    startCommand: "uv run fastapi run app/main.py --host 0.0.0.0 --port $PORT"
    envVars:
      - key: SECRET_KEY
        generateValue: true
```

Después del deploy, actualizar `baseUrl` en `api_client.dart` con la URL de Render.

---

## 9. Checklist de entrega

- [ ] Backend corre localmente sin errores (`uv run fastapi dev`)
- [ ] Todos los endpoints responden correctamente en `/docs`
- [ ] Flutter conecta al backend (login funcional)
- [ ] CRUD completo de Orders desde la app
- [ ] Cambio de estado de pedido funcional
- [ ] Material Theme 3.0 aplicado consistentemente
- [ ] GridView en MenuPage, ListTile en OrderListPage
- [ ] Provider notifica cambios correctamente en todos los ViewModels
- [ ] Inyección de dependencias manual (sin service locator automático)
- [ ] Navegación con Navigator 1.0 (sin go_router)
- [ ] API desplegada en Render con URL actualizada en Flutter

---

*Generado para: Curso Desarrollo de Aplicaciones Móviles con Flutter*
*Proyecto: RestaurantApp — Sistema de Pedidos*

opencode -s ses_1961fc92effeXx6RwBXIenkefw1