import json
from odoo import http
from odoo.http import request
from .jwt_auth import jwt_required, validate_token

class ShipmentApiController(http.Controller):

    @http.route('/api/shipments', type='http', auth='public', methods=['POST'], csrf=False)
    @jwt_required
    def create_shipment(self, **kwargs):
        try:
            payload = json.loads(request.httprequest.data.decode('utf-8'))
        except Exception:
            payload = kwargs

        sender_id = payload.get('sender_id')
        delivery_address = payload.get('delivery_address')
        weight = payload.get('weight', 1.0)
        notes = payload.get('notes', '')
        product_id = payload.get('product_id')
        price_unit = payload.get('price_unit')
        quantity = payload.get('quantity', 1)

        if not product_id or not price_unit:
            return request.make_json_response({'error': 'Fields product_id and price_unit are required'}, status=400)

        try:
            quantity = float(quantity)
            price_unit = float(price_unit)
            weight = float(weight)
        except (ValueError, TypeError):
            return request.make_json_response({'error': 'Fields quantity, price_unit and weight must be numbers'}, status=400)

        if quantity <= 0:
            return request.make_json_response({'error': 'Quantity must be greater than zero'}, status=400)

        if price_unit < 0:
            return request.make_json_response({'error': 'Price unit cannot be negative'}, status=400)

        partner_model = request.env['res.partner'].sudo()

        token = request.httprequest.headers.get('Authorization').split(' ', 1)[1]
        token_data = validate_token(token)
        customer_partner_id = token_data.get('partner_id')

        customer = partner_model.browse(int(customer_partner_id))
        if not customer.exists():
            return request.make_json_response({'error': 'Customer partner from token not found'}, status=404)

        if not delivery_address:
            delivery_address = customer.street
            if not delivery_address:
                return request.make_json_response({'error': 'Field delivery_address is required or must be set in your user profile'}, status=400)

        product = request.env['product.product'].sudo().browse(int(product_id))
        if not product.exists():
            return request.make_json_response({'error': 'Product not found'}, status=404)

        if sender_id:
            sender = partner_model.browse(int(sender_id))
            if not sender.exists():
                return request.make_json_response({'error': 'Sender partner not found'}, status=404)
        else:
            company = request.env['res.company'].sudo().search([], order='id asc', limit=1)
            sender = company.partner_id if company and company.partner_id else partner_model.search([], limit=1)
            sender_id = sender.id

        try:
            shipment = request.env['sendtrack.shipment'].sudo().create({
                'sender_id': int(sender_id),
                'receiver_id': int(customer.id),
                'delivery_address': delivery_address,
                'weight': weight,
                'notes': notes,
                'status': 'draft'
            })

            order = request.env['sale.order'].sudo().create({
                'partner_id': customer.id,
                'order_line': [(0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': quantity,
                    'price_unit': price_unit,
                })],
            })
            if payload.get('confirm_sale', True):
                order.action_confirm()
            shipment.write({'sale_order_id': order.id})

            result = shipment.to_dict()
            result['sale_order_name'] = order.name
            result['sale_state'] = order.state
            result['amount_total'] = order.amount_total
            result['product_id'] = product.id
            result['product_name'] = product.name
            result['quantity'] = quantity
            result['price_unit'] = price_unit

            return request.make_json_response(result, status=201)
        except Exception as e:
            return request.make_json_response({'error': str(e)}, status=500)

    @http.route('/api/shipments/me', type='http', auth='public', methods=['GET'], csrf=False)
    @jwt_required
    def get_my_shipments(self, **kwargs):
        token = request.httprequest.headers.get('Authorization').split(' ', 1)[1]
        token_data = validate_token(token)
        partner_id = token_data.get('partner_id')
        try:
            shipments = request.env['sendtrack.shipment'].sudo().search([('receiver_id', '=', int(partner_id))])
            result = [s.to_dict() for s in shipments]
            return request.make_json_response(result, status=200)
        except Exception as e:
            return request.make_json_response({'error': str(e)}, status=500)

    @http.route('/api/shipments/person/<int:partner_id>', type='http', auth='public', methods=['GET'], csrf=False)
    @jwt_required
    def get_shipments_by_person(self, partner_id, **kwargs):
        partner = request.env['res.partner'].sudo().browse(int(partner_id))
        if not partner.exists():
            return request.make_json_response({'error': 'Partner not found'}, status=404)

        role = kwargs.get('role', 'all')
        if role == 'sender':
            domain = [('sender_id', '=', partner_id)]
        elif role == 'receiver':
            domain = [('receiver_id', '=', partner_id)]
        else:
            domain = ['|', ('sender_id', '=', partner_id), ('receiver_id', '=', partner_id)]

        try:
            shipments = request.env['sendtrack.shipment'].sudo().search(domain)
            result = [s.to_dict() for s in shipments]
            return request.make_json_response(result, status=200)
        except Exception as e:
            return request.make_json_response({'error': str(e)}, status=500)

    @http.route('/api/shipments/track/<string:tracking_code>', type='http', auth='public', methods=['GET'], csrf=False)
    @jwt_required
    def track_shipment(self, tracking_code, **kwargs):
        shipment = request.env['sendtrack.shipment'].sudo().search([('tracking_code', '=', tracking_code)], limit=1)
        if not shipment:
            return request.make_json_response({'error': 'Shipment not found with given tracking code'}, status=404)

        return request.make_json_response(shipment.to_dict(), status=200)

    @http.route('/api/shipments/<int:shipment_id>/sale', type='http', auth='public', methods=['GET'], csrf=False)
    @jwt_required
    def get_shipment_sale(self, shipment_id, **kwargs):
        token = request.httprequest.headers.get('Authorization').split(' ', 1)[1]
        token_data = validate_token(token)
        user_partner_id = int(token_data.get('partner_id'))
        user_id = int(token_data.get('user_id'))

        shipment = request.env['sendtrack.shipment'].sudo().browse(shipment_id)
        if not shipment.exists():
            return request.make_json_response({'error': 'Shipment not found'}, status=404)

        if not shipment.sale_order_id:
            return request.make_json_response({'error': 'No quotation or sale order associated with this shipment'}, status=404)

        user = request.env['res.users'].sudo().browse(user_id)
        is_admin = user.has_group('base.group_system')

        if not is_admin and shipment.sender_id.id != user_partner_id and shipment.receiver_id.id != user_partner_id:
            return request.make_json_response({'error': 'Forbidden: You are not authorized to view this quotation'}, status=403)

        order = shipment.sale_order_id
        line = order.order_line[0] if order.order_line else None

        result = {
            'sale_order_id': order.id,
            'sale_order_name': order.name,
            'state': order.state,
            'partner_id': order.partner_id.id,
            'partner_name': order.partner_id.name,
            'amount_untaxed': order.amount_untaxed,
            'amount_tax': order.amount_tax,
            'amount_total': order.amount_total,
            'shipment_id': shipment.id,
            'shipment_name': shipment.name,
            'shipment_tracking_code': shipment.tracking_code,
            'product_id': line.product_id.id if line else None,
            'product_name': line.product_id.name if line else '',
            'quantity': line.product_uom_qty if line else 0.0,
            'price_unit': line.price_unit if line else 0.0,
            'date_order': str(order.date_order) if order.date_order else ''
        }
        return request.make_json_response(result, status=200)

    @http.route('/api/shipments/<int:shipment_id>/sale/confirm', type='http', auth='public', methods=['POST'], csrf=False)
    @jwt_required
    def confirm_shipment_sale(self, shipment_id, **kwargs):
        token = request.httprequest.headers.get('Authorization').split(' ', 1)[1]
        token_data = validate_token(token)
        user_partner_id = int(token_data.get('partner_id'))
        user_id = int(token_data.get('user_id'))

        shipment = request.env['sendtrack.shipment'].sudo().browse(shipment_id)
        if not shipment.exists():
            return request.make_json_response({'error': 'Shipment not found'}, status=404)

        if not shipment.sale_order_id:
            return request.make_json_response({'error': 'No quotation or sale order associated with this shipment'}, status=404)

        order = shipment.sale_order_id
        user = request.env['res.users'].sudo().browse(user_id)
        is_admin = user.has_group('base.group_system')

        if not is_admin and shipment.sender_id.id != user_partner_id and shipment.receiver_id.id != user_partner_id and order.partner_id.id != user_partner_id:
            return request.make_json_response({'error': 'Forbidden: You are not authorized to confirm this quotation'}, status=403)

        if order.state in ['sale', 'done']:
            return request.make_json_response({
                'message': 'Quotation is already confirmed',
                'sale_order_id': order.id,
                'sale_order_name': order.name,
                'state': order.state,
                'amount_total': order.amount_total
            }, status=200)

        if order.state == 'cancel':
            return request.make_json_response({'error': 'Cancelled quotation cannot be confirmed'}, status=400)

        try:
            order.action_confirm()
            return request.make_json_response({
                'message': 'Quotation confirmed successfully',
                'sale_order_id': order.id,
                'sale_order_name': order.name,
                'state': order.state,
                'partner_id': order.partner_id.id,
                'partner_name': order.partner_id.name,
                'amount_total': order.amount_total
            }, status=200)
        except Exception as e:
            return request.make_json_response({'error': str(e)}, status=500)

    @http.route('/api/shipments/<int:shipment_id>/invoice', type='http', auth='public', methods=['POST'], csrf=False)
    @jwt_required
    def create_shipment_invoice(self, shipment_id, **kwargs):
        token = request.httprequest.headers.get('Authorization').split(' ', 1)[1]
        token_data = validate_token(token)
        user_partner_id = int(token_data.get('partner_id'))
        user_id = int(token_data.get('user_id'))

        shipment = request.env['sendtrack.shipment'].sudo().browse(shipment_id)
        if not shipment.exists():
            return request.make_json_response({'error': 'Shipment not found'}, status=404)

        if not shipment.sale_order_id:
            return request.make_json_response({'error': 'No quotation or sale order associated with this shipment'}, status=404)

        order = shipment.sale_order_id
        user = request.env['res.users'].sudo().browse(user_id)
        is_admin = user.has_group('base.group_system')

        if not is_admin and shipment.sender_id.id != user_partner_id and shipment.receiver_id.id != user_partner_id and order.partner_id.id != user_partner_id:
            return request.make_json_response({'error': 'Forbidden: You are not authorized to invoice this shipment'}, status=403)

        if order.state == 'draft':
            return request.make_json_response({'error': 'Quotation must be confirmed before creating an invoice. Please confirm it first.'}, status=400)

        if order.state == 'cancel':
            return request.make_json_response({'error': 'Cannot create invoice for a cancelled order'}, status=400)

        existing_invoices = order.invoice_ids.filtered(lambda inv: inv.state != 'cancel')
        if existing_invoices:
            inv = existing_invoices[0]
            return request.make_json_response({
                'error': 'An invoice already exists for this shipment',
                'invoice_id': inv.id,
                'invoice_name': inv.name if (inv.name and inv.name != '/') else 'Draft',
                'state': inv.state,
                'amount_total': inv.amount_total
            }, status=409)

        try:
            invoices = order.sudo()._create_invoices()
            if not invoices:
                return request.make_json_response({'error': 'No invoice lines could be generated for this order'}, status=400)

            inv = invoices[0]
            return request.make_json_response({
                'message': 'Draft invoice created successfully',
                'invoice_id': inv.id,
                'invoice_name': inv.name if (inv.name and inv.name != '/') else 'Draft',
                'state': inv.state,
                'payment_state': inv.payment_state or 'not_paid',
                'invoice_date': str(inv.invoice_date) if inv.invoice_date else '',
                'partner_id': inv.partner_id.id,
                'partner_name': inv.partner_id.name,
                'amount_untaxed': inv.amount_untaxed,
                'amount_tax': inv.amount_tax,
                'amount_total': inv.amount_total,
                'currency': inv.currency_id.name if inv.currency_id else '',
                'shipment_id': shipment.id,
                'sale_order_id': order.id
            }, status=201)
        except Exception as e:
            return request.make_json_response({'error': str(e)}, status=500)

    @http.route('/api/shipments/<int:shipment_id>/invoice/post', type='http', auth='public', methods=['POST'], csrf=False)
    @jwt_required
    def post_shipment_invoice(self, shipment_id, **kwargs):
        token = request.httprequest.headers.get('Authorization').split(' ', 1)[1]
        token_data = validate_token(token)
        user_partner_id = int(token_data.get('partner_id'))
        user_id = int(token_data.get('user_id'))

        shipment = request.env['sendtrack.shipment'].sudo().browse(shipment_id)
        if not shipment.exists():
            return request.make_json_response({'error': 'Shipment not found'}, status=404)

        if not shipment.sale_order_id:
            return request.make_json_response({'error': 'No quotation or sale order associated with this shipment'}, status=404)

        order = shipment.sale_order_id
        user = request.env['res.users'].sudo().browse(user_id)
        is_admin = user.has_group('base.group_system')

        if not is_admin and shipment.sender_id.id != user_partner_id and shipment.receiver_id.id != user_partner_id and order.partner_id.id != user_partner_id:
            return request.make_json_response({'error': 'Forbidden: You are not authorized to post this invoice'}, status=403)

        draft_invoices = order.invoice_ids.filtered(lambda inv: inv.state == 'draft')
        if not draft_invoices:
            posted_invoices = order.invoice_ids.filtered(lambda inv: inv.state == 'posted')
            if posted_invoices:
                inv = posted_invoices[0]
                return request.make_json_response({
                    'message': 'Invoice is already posted',
                    'invoice_id': inv.id,
                    'invoice_name': inv.name,
                    'state': inv.state,
                    'amount_total': inv.amount_total
                }, status=200)
            return request.make_json_response({'error': 'No draft invoice found for this shipment. Please generate the invoice first.'}, status=404)

        inv = draft_invoices[0]
        try:
            inv.action_post()
            return request.make_json_response({
                'message': 'Invoice posted successfully',
                'invoice_id': inv.id,
                'invoice_name': inv.name,
                'state': inv.state,
                'payment_state': inv.payment_state or 'not_paid',
                'invoice_date': str(inv.invoice_date) if inv.invoice_date else '',
                'partner_id': inv.partner_id.id,
                'partner_name': inv.partner_id.name,
                'amount_untaxed': inv.amount_untaxed,
                'amount_tax': inv.amount_tax,
                'amount_total': inv.amount_total,
                'currency': inv.currency_id.name if inv.currency_id else '',
                'shipment_id': shipment.id,
                'sale_order_id': order.id
            }, status=200)
        except Exception as e:
            return request.make_json_response({'error': str(e)}, status=500)

    @http.route('/api/shipments/<int:shipment_id>/invoice', type='http', auth='public', methods=['GET'], csrf=False)
    @jwt_required
    def get_shipment_invoice(self, shipment_id, **kwargs):
        token = request.httprequest.headers.get('Authorization').split(' ', 1)[1]
        token_data = validate_token(token)
        user_partner_id = int(token_data.get('partner_id'))
        user_id = int(token_data.get('user_id'))

        shipment = request.env['sendtrack.shipment'].sudo().browse(shipment_id)
        if not shipment.exists():
            return request.make_json_response({'error': 'Shipment not found'}, status=404)

        if not shipment.sale_order_id:
            return request.make_json_response({'error': 'No quotation or sale order associated with this shipment'}, status=404)

        order = shipment.sale_order_id
        user = request.env['res.users'].sudo().browse(user_id)
        is_admin = user.has_group('base.group_system')

        if not is_admin and shipment.sender_id.id != user_partner_id and shipment.receiver_id.id != user_partner_id and order.partner_id.id != user_partner_id:
            return request.make_json_response({'error': 'Forbidden: You are not authorized to view this invoice'}, status=403)

        invoices = order.invoice_ids.filtered(lambda inv: inv.state != 'cancel')
        if not invoices:
            return request.make_json_response({'error': 'No invoice found for this shipment'}, status=404)

        inv = invoices[0]
        return request.make_json_response({
            'invoice_id': inv.id,
            'invoice_name': inv.name if (inv.name and inv.name != '/') else 'Draft',
            'state': inv.state,
            'payment_state': inv.payment_state or 'not_paid',
            'invoice_date': str(inv.invoice_date) if inv.invoice_date else '',
            'partner_id': inv.partner_id.id,
            'partner_name': inv.partner_id.name,
            'amount_untaxed': inv.amount_untaxed,
            'amount_tax': inv.amount_tax,
            'amount_total': inv.amount_total,
            'currency': inv.currency_id.name if inv.currency_id else '',
            'shipment_id': shipment.id,
            'sale_order_id': order.id
        }, status=200)
