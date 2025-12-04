from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.exceptions import AccessError, MissingError
import uuid
import werkzeug

class FlightBiddingPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'flight_bidding_count' in counters:
            values['flight_bidding_count'] = request.env['flight.bidding'].search_count([])
        return values

    def _flight_bidding_get_page_view_values(self, logistic_order, access_token, **kwargs):
        values = {
            'page_name': 'flight_bidding',
            'logistic_order': logistic_order,
            'biddings': logistic_order.flight_bidding_ids.filtered(lambda b: b.state == 'draft'),
        }
        return self._get_page_view_values(logistic_order, access_token, values, 'my_flight_biddings_history', False, **kwargs)

    def _flight_selection_get_page_view_values(self, logistics_order, access_token, **kwargs):
        values = {
            'page_name': 'flight_selection',
            'logistics_order': logistics_order,
        }
        return self._get_page_view_values(logistics_order, access_token, values, 'my_flight_selections_history', False, **kwargs)

    @http.route(['/my/flight-bidding/<int:logistic_order_id>'], type='http', auth="public", website=True)
    def portal_flight_bidding(self, logistic_order_id, access_token=None, **kw):
        try:
            # Verify access using the logistic order's access token
            logistic_order_sudo = self._document_check_access('logistic.order', logistic_order_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = self._flight_bidding_get_page_view_values(logistic_order_sudo, access_token, **kw)
        return request.render("scs_operation.portal_flight_bidding", values)

    @http.route(['/flight-bidding/accept/<int:bidding_id>'], type='http', auth="public", website=True)
    def accept_flight_bidding(self, bidding_id, access_token=None, **kw):
        try:
            bidding_sudo = request.env['flight.bidding'].sudo().browse(bidding_id)
            # Verify access using the logistic order's access token
            if bidding_sudo.exists():
                logistic_order = bidding_sudo.logistic_order_id
                self._document_check_access('logistic.order', logistic_order.id, access_token)
                if bidding_sudo.state == 'draft':
                    bidding_sudo.action_confirm()
                return werkzeug.utils.redirect('/my/flight-bidding/%s?access_token=%s' % 
                    (logistic_order.id, access_token))
        except (AccessError, MissingError):
            pass
        return request.redirect('/my')

    @http.route(['/my/flight-bidding/confirm/<int:bidding_id>'], type='http', auth="public", website=True)
    def confirm_flight_bidding_http(self, bidding_id, access_token=None, **kw):
        try:
            bidding_sudo = request.env['flight.bidding'].sudo().browse(bidding_id)
            if bidding_sudo.exists():
                logistic_order = bidding_sudo.logistic_order_id
                self._document_check_access('logistic.order', logistic_order.id, access_token)
                if bidding_sudo.state == 'draft':
                    bidding_sudo.action_confirm()
                return werkzeug.utils.redirect('/my/flight-bidding/%s' % logistic_order.id)
        except (AccessError, MissingError):
            pass
        return request.redirect('/my')

    @http.route(['/my/flight/confirm/<int:bidding_id>'], type='json', auth="public", website=True)
    def confirm_flight_bidding(self, bidding_id, **kw):
        try:
            bidding_sudo = request.env['flight.bidding'].sudo().browse(bidding_id)
            if bidding_sudo.exists() and bidding_sudo.state == 'draft':
                bidding_sudo.action_confirm()
                return {'success': True}
            return {'success': False, 'error': 'Invalid bidding state'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route(['/my/flight-selection/<int:logistics_order_id>'], type='http', auth="public", website=True)
    def portal_flight_selection(self, logistics_order_id, access_token=None, **kw):
        try:
            logistics_order_sudo = self._document_check_access('logistic.order', logistics_order_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = self._flight_selection_get_page_view_values(logistics_order_sudo, access_token, **kw)
        return request.render("scs_operation.portal_flight_selection", values)

    @http.route(['/my/flight-selection/submit/<int:logistics_order_id>'], type='http', auth="public", website=True, methods=['POST'])
    def submit_flight_selection(self, logistics_order_id, access_token=None, **kw):
        try:
            logistics_order_sudo = self._document_check_access('logistic.order', logistics_order_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        selected_bidding_id = int(kw.get('selected_bidding', 0))
        if selected_bidding_id:
            bidding = request.env['flight.bidding'].sudo().browse(selected_bidding_id)
            if bidding.exists() and bidding.logistic_order_id.id == logistics_order_id:
                bidding.write({'state': 'approval'})
                logistics_order_sudo.action_to_approval()
                
        return request.redirect('/my/flight-selection/%s?access_token=%s' % (logistics_order_id, access_token))
