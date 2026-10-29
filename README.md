# SendTrack - Odoo Addons

Módulos personalizados de Odoo 19 para la plataforma SendTrack:

- **`sendtrack_api`**: API REST para autenticación (JWT), envíos con creación automática de orden de venta en Sales y tickets de soporte.
- **`logistics_companies`**: Catálogo en Odoo que muestra en una vista propia las empresas que tengan la etiqueta `Operador Logístico`.

---

## Swagger UI

Documentación interactiva disponible en:
- Interfaz: `http://localhost:8069/api/docs`
- Especificación OpenAPI: `http://localhost:8069/api/openapi.json`

---

## Arranque en local

1. Levantar contenedores:
```bash
docker compose up -d --build
```

2. Acceder a Odoo en `http://localhost:8069`:
- Usuario: `admin`
- Contraseña: `admin`

---

## Estructura

```text
├── sendtrack_api/          # Módulo API REST
├── logistics_companies/    # Módulo catálogo Compañías
├── docker-compose.yml      # Entorno Docker local (Odoo 19 + Postgres 15)
├── Dockerfile              # Build con PyJWT
└── requirements.txt        # Dependencias Python
```

---

## Endpoints

Todos los endpoints que devuelven datos retornan JSON plano (sin objetos anidados).

### Auth

#### Registro
`POST /api/auth/register`

Body:
```json
{
  "name": "Pepe",
  "email": "pepe@test.com",
  "password": "1234password",
  "phone": "600123456",
  "street": "Calle Mayor 12"
}
```

Respuesta (201):
```json
{
  "user_id": 7,
  "partner_id": 9,
  "name": "Pepe",
  "email": "pepe@test.com",
  "phone": "600123456",
  "street": "Calle Mayor 12"
}
```

#### Login
`POST /api/auth/login`

Body:
```json
{
  "email": "pepe@test.com",
  "password": "1234password"
}
```

Respuesta (200):
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": 7,
  "partner_id": 9,
  "name": "Pepe",
  "email": "pepe@test.com",
  "phone": "600123456",
  "street": "Calle Mayor 12"
}
```

#### Logout
`POST /api/auth/logout`

Respuesta (200):
```json
{
  "status": "logged_out"
}
```

---

### Envíos

#### Crear envío
`POST /api/shipments`

Headers:
```http
Authorization: Bearer <token>
```

Body:
```json
{
  "sender_id": 1,
  "receiver_id": 9,
  "delivery_address": "Av Diagonal 100, Barcelona",
  "weight": 1.5,
  "product_id": 1,
  "price_unit": 25.50,
  "quantity": 1.0,
  "notes": "Dejar en portería"
}
```

Respuesta (201):
```json
{
  "id": 1,
  "name": "SHP-A1B2C3D4",
  "tracking_code": "E5F6G7H8I9J0",
  "sender_id": 1,
  "sender_name": "My Company",
  "receiver_id": 9,
  "receiver_name": "Pepe",
  "receiver_email": "pepe@test.com",
  "receiver_phone": "600123456",
  "delivery_address": "Av Diagonal 100, Barcelona",
  "weight": 1.5,
  "status": "draft",
  "notes": "Dejar en portería",
  "sale_order_id": 2,
  "sale_order_name": "S00002",
  "sale_state": "sale",
  "amount_total": 30.85,
  "product_id": 1,
  "product_name": "Servicio de Envío",
  "quantity": 1.0,
  "price_unit": 25.50,
  "created_at": "2026-10-23 07:50:00"
}
```

#### Mis envíos
`GET /api/shipments/me`

Headers:
```http
Authorization: Bearer <token>
```

#### Envíos por persona
`GET /api/shipments/person/<partner_id>`

Headers:
```http
Authorization: Bearer <token>
```

Query param opcional: `?role=sender` o `?role=receiver`

#### Tracking de envío
`GET /api/shipments/track/<tracking_code>`

Respuesta (200):
```json
{
  "id": 1,
  "name": "SHP-A1B2C3D4",
  "tracking_code": "E5F6G7H8I9J0",
  "sender_id": 1,
  "sender_name": "My Company",
  "receiver_id": 9,
  "receiver_name": "Pepe",
  "receiver_email": "pepe@test.com",
  "receiver_phone": "600123456",
  "delivery_address": "Av Diagonal 100, Barcelona",
  "weight": 1.5,
  "status": "draft",
  "notes": "Dejar en portería",
  "created_at": "2026-10-23 07:50:00"
}
```

#### Consultar presupuesto o venta de un envío
`GET /api/shipments/<shipment_id>/sale`

Headers:
```http
Authorization: Bearer <token>
```

Respuesta (200):
```json
{
  "sale_order_id": 2,
  "sale_order_name": "S00002",
  "state": "draft",
  "partner_id": 9,
  "partner_name": "Pepe",
  "amount_untaxed": 25.50,
  "amount_tax": 5.35,
  "amount_total": 30.85,
  "shipment_id": 1,
  "shipment_name": "SHP-A1B2C3D4",
  "shipment_tracking_code": "E5F6G7H8I9J0",
  "product_id": 1,
  "product_name": "Servicio de Envío",
  "quantity": 1.0,
  "price_unit": 25.50,
  "date_order": "2026-10-29 18:00:00"
}
```

#### Confirmar presupuesto de un envío
`POST /api/shipments/<shipment_id>/sale/confirm`

Headers:
```http
Authorization: Bearer <token>
```

Respuesta (200):
```json
{
  "message": "Quotation confirmed successfully",
  "sale_order_id": 2,
  "sale_order_name": "S00002",
  "state": "sale",
  "partner_id": 9,
  "partner_name": "Pepe",
  "amount_total": 30.85
}
```

---

### Facturas

#### Listar mis facturas
`GET /api/invoices/me`

Headers:
```http
Authorization: Bearer <token>
```

Respuesta (200):
```json
[
  {
    "id": 5,
    "name": "INV/2026/00001",
    "move_type": "out_invoice",
    "state": "posted",
    "payment_state": "not_paid",
    "invoice_date": "2026-10-29",
    "invoice_date_due": "2026-11-29",
    "partner_id": 9,
    "partner_name": "Pepe",
    "amount_untaxed": 25.50,
    "amount_tax": 5.35,
    "amount_total": 30.85,
    "currency": "EUR"
  }
]
```

#### Listar facturas de una persona
`GET /api/invoices/person/<partner_id>`

Headers:
```http
Authorization: Bearer <token>
```
*(Requiere ser el propio usuario o administrador).*

---

### Tickets

#### Crear ticket
`POST /api/tickets`

Headers:
```http
Authorization: Bearer <token>
```

Body:
```json
{
  "title": "Paquete dañado",
  "description": "La caja ha llegado rota",
  "partner_id": 9,
  "tracking_code": "E5F6G7H8I9J0",
  "priority": "high"
}
```

Respuesta (201):
```json
{
  "id": 1,
  "name": "TCK-9A8B7C6D",
  "title": "Paquete dañado",
  "description": "La caja ha llegado rota",
  "partner_id": 9,
  "partner_name": "Pepe",
  "partner_email": "pepe@test.com",
  "shipment_id": 1,
  "shipment_tracking_code": "E5F6G7H8I9J0",
  "priority": "high",
  "status": "open",
  "created_at": "2026-10-12 18:05:00"
}
```

#### Listar tickets de una persona
`GET /api/tickets/person/<partner_id>`

Headers:
```http
Authorization: Bearer <token>
```
