from odoo import http
from odoo.http import request
from .jwt_auth import jwt_required, validate_token

class InvoiceApiController(http.Controller):

    def _invoice_to_dict(self, inv):
        return {
            'id': inv.id,
            'name': inv.name if (inv.name and inv.name != '/') else 'Draft',
            'move_type': inv.move_type,
            'state': inv.state,
            'payment_state': inv.payment_state or '',
            'invoice_date': str(inv.invoice_date) if inv.invoice_date else '',
            'invoice_date_due': str(inv.invoice_date_due) if inv.invoice_date_due else '',
            'partner_id': inv.partner_id.id,
            'partner_name': inv.partner_id.name,
            'amount_untaxed': inv.amount_untaxed,
            'amount_tax': inv.amount_tax,
            'amount_total': inv.amount_total,
            'currency': inv.currency_id.name if inv.currency_id else ''
        }

    @http.route('/api/invoices/me', type='http', auth='public', methods=['GET'], csrf=False)
    @jwt_required
    def get_my_invoices(self, **kwargs):
        token = request.httprequest.headers.get('Authorization').split(' ', 1)[1]
        token_data = validate_token(token)
        partner_id = token_data.get('partner_id')

        try:
            invoices = request.env['account.move'].sudo().search([
                ('partner_id', '=', int(partner_id)),
                ('move_type', 'in', ['out_invoice', 'out_refund'])
            ], order='invoice_date desc, id desc')
            result = [self._invoice_to_dict(inv) for inv in invoices]
            return request.make_json_response(result, status=200)
        except Exception as e:
            return request.make_json_response({'error': str(e)}, status=500)

    @http.route('/api/invoices/person/<int:partner_id>', type='http', auth='public', methods=['GET'], csrf=False)
    @jwt_required
    def get_invoices_by_person(self, partner_id, **kwargs):
        token = request.httprequest.headers.get('Authorization').split(' ', 1)[1]
        token_data = validate_token(token)
        token_partner_id = int(token_data.get('partner_id'))
        user_id = int(token_data.get('user_id'))

        user = request.env['res.users'].sudo().browse(user_id)
        is_admin = user.has_group('base.group_system')

        if not is_admin and token_partner_id != partner_id:
            return request.make_json_response({'error': 'Forbidden: You can only view your own invoices'}, status=403)

        partner = request.env['res.partner'].sudo().browse(int(partner_id))
        if not partner.exists():
            return request.make_json_response({'error': 'Partner not found'}, status=404)

        try:
            invoices = request.env['account.move'].sudo().search([
                ('partner_id', '=', partner_id),
                ('move_type', 'in', ['out_invoice', 'out_refund'])
            ], order='invoice_date desc, id desc')
            result = [self._invoice_to_dict(inv) for inv in invoices]
            return request.make_json_response(result, status=200)
        except Exception as e:
            return request.make_json_response({'error': str(e)}, status=500)

    @http.route('/api/invoices/<int:invoice_id>/post', type='http', auth='public', methods=['POST'], csrf=False)
    @jwt_required
    def post_invoice(self, invoice_id, **kwargs):
        token = request.httprequest.headers.get('Authorization').split(' ', 1)[1]
        token_data = validate_token(token)
        user_partner_id = int(token_data.get('partner_id'))
        user_id = int(token_data.get('user_id'))

        inv = request.env['account.move'].sudo().browse(invoice_id)
        if not inv.exists() or inv.move_type not in ['out_invoice', 'out_refund']:
            return request.make_json_response({'error': 'Invoice not found'}, status=404)

        user = request.env['res.users'].sudo().browse(user_id)
        is_admin = user.has_group('base.group_system')

        if not is_admin and inv.partner_id.id != user_partner_id:
            return request.make_json_response({'error': 'Forbidden: You are not authorized to post this invoice'}, status=403)

        if inv.state == 'posted':
            return request.make_json_response({
                'message': 'Invoice is already posted',
                'invoice_id': inv.id,
                'invoice_name': inv.name,
                'state': inv.state,
                'amount_total': inv.amount_total
            }, status=200)

        if inv.state == 'cancel':
            return request.make_json_response({'error': 'Cancelled invoice cannot be posted'}, status=400)

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
                'currency': inv.currency_id.name if inv.currency_id else ''
            }, status=200)
        except Exception as e:
            return request.make_json_response({'error': str(e)}, status=500)
