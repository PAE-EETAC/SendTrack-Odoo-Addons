from odoo import http
from odoo.http import request

class DocsApiController(http.Controller):

    @http.route('/api/openapi.json', type='http', auth='public', methods=['GET'], csrf=False)
    def openapi_json(self):
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "SendTrack Odoo REST API",
                "version": "1.0.0",
                "description": "API REST para gestion de autenticacion, contactos, envios y tickets en Odoo"
            },
            "servers": [
                {"url": "/", "description": "Server"}
            ],
            "paths": {
                "/api/auth/register": {
                    "post": {
                        "summary": "Registrar nuevo usuario y contacto",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["name", "email", "password"],
                                        "properties": {
                                            "name": {"type": "string", "example": "Carlos Gomez"},
                                            "email": {"type": "string", "example": "carlos@test.com"},
                                            "password": {"type": "string", "example": "mypassword123"},
                                            "phone": {"type": "string", "example": "600112233"},
                                            "street": {"type": "string", "example": "Calle Mayor 10"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "Usuario y contacto creados"},
                            "400": {"description": "Parametros requeridos faltantes"},
                            "409": {"description": "Email ya existente"}
                        }
                    }
                },
                "/api/auth/login": {
                    "post": {
                        "summary": "Iniciar sesion",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["email", "password"],
                                        "properties": {
                                            "email": {"type": "string", "example": "carlos@test.com"},
                                            "password": {"type": "string", "example": "mypassword123"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {"description": "Login exitoso, devuelve token JWT"},
                            "401": {"description": "Credenciales invalidas"}
                        }
                    }
                },
                "/api/auth/logout": {
                    "post": {
                        "summary": "Cerrar sesion",
                        "responses": {
                            "200": {"description": "Sesion cerrada"}
                        }
                    }
                },
                "/api/shipments": {
                    "post": {
                        "summary": "Crear envio para el usuario autenticado",
                        "security": [{"BearerAuth": []}],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["product_id", "price_unit"],
                                        "properties": {
                                            "product_id": {"type": "integer", "example": 1},
                                            "price_unit": {"type": "number", "example": 25.50},
                                            "quantity": {"type": "number", "example": 1.0},
                                            "delivery_address": {"type": "string", "example": "Avenida Diagonal 200, Barcelona"},
                                            "sender_id": {"type": "integer", "example": 68},
                                            "weight": {"type": "number", "example": 2.5},
                                            "notes": {"type": "string", "example": "Timbre 2B"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "Envio creado exitosamente"},
                            "400": {"description": "Datos obligatorios faltantes"}
                        }
                    }
                },
                "/api/shipments/me": {
                    "get": {
                        "summary": "Listar mis envios (usuario autenticado)",
                        "security": [{"BearerAuth": []}],
                        "responses": {
                            "200": {"description": "Listado de envios del usuario"}
                        }
                    }
                },
                "/api/shipments/person/{partner_id}": {
                    "get": {
                        "summary": "Listar envios de una persona",
                        "security": [{"BearerAuth": []}],
                        "parameters": [
                            {
                                "name": "partner_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"}
                            },
                            {
                                "name": "role",
                                "in": "query",
                                "required": False,
                                "schema": {
                                    "type": "string",
                                    "enum": ["all", "sender", "receiver"],
                                    "default": "all"
                                }
                            }
                        ],
                        "responses": {
                            "200": {"description": "Listado de envios"},
                            "404": {"description": "Contacto no encontrado"}
                        }
                    }
                },
                "/api/shipments/track/{tracking_code}": {
                    "get": {
                        "summary": "Rastrear envio por tracking code",
                        "security": [{"BearerAuth": []}],
                        "parameters": [
                            {
                                "name": "tracking_code",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "Detalles del envio"},
                            "404": {"description": "Envio no encontrado"}
                        }
                    }
                },
                "/api/shipments/{shipment_id}/sale": {
                    "get": {
                        "summary": "Consultar presupuesto o venta asociada a un envio",
                        "security": [{"BearerAuth": []}],
                        "parameters": [
                            {
                                "name": "shipment_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "Detalles del presupuesto o venta"},
                            "403": {"description": "No autorizado para ver este presupuesto"},
                            "404": {"description": "Envio o presupuesto no encontrado"}
                        }
                    }
                },
                "/api/shipments/{shipment_id}/sale/confirm": {
                    "post": {
                        "summary": "Confirmar presupuesto asociado a un envio",
                        "security": [{"BearerAuth": []}],
                        "parameters": [
                            {
                                "name": "shipment_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "Presupuesto confirmado exitosamente"},
                            "400": {"description": "Estado invalido para confirmacion"},
                            "403": {"description": "No autorizado para confirmar este presupuesto"},
                            "404": {"description": "Envio o presupuesto no encontrado"}
                        }
                    }
                },
                "/api/shipments/{shipment_id}/invoice": {
                    "get": {
                        "summary": "Consultar factura asociada a un envio",
                        "security": [{"BearerAuth": []}],
                        "parameters": [
                            {
                                "name": "shipment_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "Detalles de la factura"},
                            "403": {"description": "No autorizado"},
                            "404": {"description": "Envio o factura no encontrada"}
                        }
                    },
                    "post": {
                        "summary": "Generar factura borrador desde la venta del envio (Paso 3)",
                        "security": [{"BearerAuth": []}],
                        "parameters": [
                            {
                                "name": "shipment_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {
                            "201": {"description": "Factura borrador creada exitosamente"},
                            "400": {"description": "El pedido debe estar confirmado primero"},
                            "409": {"description": "Ya existe una factura para este envio"}
                        }
                    }
                },
                "/api/shipments/{shipment_id}/invoice/post": {
                    "post": {
                        "summary": "Validar y publicar factura de un envio (Paso 4)",
                        "security": [{"BearerAuth": []}],
                        "parameters": [
                            {
                                "name": "shipment_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "Factura validada y publicada con numero oficial"},
                            "404": {"description": "Factura borrador no encontrada"}
                        }
                    }
                },
                "/api/invoices/{invoice_id}/post": {
                    "post": {
                        "summary": "Validar y publicar una factura por su ID (Paso 4)",
                        "security": [{"BearerAuth": []}],
                        "parameters": [
                            {
                                "name": "invoice_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "Factura validada y publicada"},
                            "403": {"description": "No autorizado"},
                            "404": {"description": "Factura no encontrada"}
                        }
                    }
                },
                "/api/invoices/me": {
                    "get": {
                        "summary": "Listar facturas del usuario autenticado",
                        "security": [{"BearerAuth": []}],
                        "responses": {
                            "200": {"description": "Listado de facturas"},
                            "401": {"description": "No autenticado"}
                        }
                    }
                },
                "/api/invoices/person/{partner_id}": {
                    "get": {
                        "summary": "Listar facturas de un contacto",
                        "security": [{"BearerAuth": []}],
                        "parameters": [
                            {
                                "name": "partner_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "Listado de facturas"},
                            "403": {"description": "No autorizado"},
                            "404": {"description": "Contacto no encontrado"}
                        }
                    }
                },
                "/api/tickets": {
                    "post": {
                        "summary": "Crear ticket de soporte",
                        "security": [{"BearerAuth": []}],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["title", "description", "partner_id"],
                                        "properties": {
                                            "title": {"type": "string", "example": "Paquete retrasado"},
                                            "description": {"type": "string", "example": "No ha llegado en la fecha prevista"},
                                            "partner_id": {"type": "integer", "example": 3},
                                            "tracking_code": {"type": "string", "example": "8A7B6C5D4E3F"},
                                            "priority": {
                                                "type": "string",
                                                "enum": ["low", "medium", "high"],
                                                "default": "medium"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "Ticket creado"},
                            "400": {"description": "Campos obligatorios faltantes"}
                        }
                    }
                },
                "/api/tickets/person/{partner_id}": {
                    "get": {
                        "summary": "Listar tickets de una persona",
                        "security": [{"BearerAuth": []}],
                        "parameters": [
                            {
                                "name": "partner_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "Listado de tickets"},
                            "404": {"description": "Contacto no encontrado"}
                        }
                    }
                }
            },
            "components": {
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            }
        }
        return request.make_json_response(spec, status=200)

    @http.route('/api/docs', type='http', auth='public', methods=['GET'], csrf=False)
    def swagger_ui(self):
        html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>SendTrack API - Swagger UI</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css" />
    <style>
        body { margin: 0; padding: 0; background: #fafafa; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {
            SwaggerUIBundle({
                url: "/api/openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ]
            });
        };
    </script>
</body>
</html>"""
        return request.make_response(html_content, headers=[('Content-Type', 'text/html; charset=utf-8')])
