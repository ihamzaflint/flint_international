# -*- coding: utf-8 -*-
# from odoo import http


# class EraRecruitmentOpportunity(http.Controller):
#     @http.route('/era_recruitment_opportunity/era_recruitment_opportunity', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/era_recruitment_opportunity/era_recruitment_opportunity/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('era_recruitment_opportunity.listing', {
#             'root': '/era_recruitment_opportunity/era_recruitment_opportunity',
#             'objects': http.request.env['era_recruitment_opportunity.era_recruitment_opportunity'].search([]),
#         })

#     @http.route('/era_recruitment_opportunity/era_recruitment_opportunity/objects/<model("era_recruitment_opportunity.era_recruitment_opportunity"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('era_recruitment_opportunity.object', {
#             'object': obj
#         })

# code by shailesh

import logging
from odoo import fields, http, _
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.exceptions import AccessError, MissingError
import uuid
import werkzeug
from odoo.exceptions import AccessError, MissingError

_logger = logging.getLogger(__name__)


class FlightBiddingPortal(portal.CustomerPortal):

    def _bidding_applicant_get_page_view_values(self, recruitment_order, access_token, **kwargs):
        values = {
            'page_name': 'bidding_applicant',
            'recruitment_order': recruitment_order,
            'biddings': recruitment_order.applicant_line,
        }
        return self._get_page_view_values(recruitment_order, access_token, values, 'my_applicant_bidding_history',
                                          False, **kwargs)

    def _rejecting_applicant_get_page_view_values(self, bidding_id, access_token, **kwargs):
        values = {
            'page_name': 'bidding_applicant_rejecting',
            'bidding_name': bidding_id.name,
            'bidding_id': bidding_id.id,
            # 'biddings': recruitment_order.applicant_line,
        }
        return self._get_page_view_values(bidding_id, access_token, values, 'my_rejecting_applicant_bidding_history',
                                          False, **kwargs)

    def _applicant_selection_get_page_view_values(self, recruitment_order, access_token, **kwargs):
        values = {
            'page_name': 'applicant_selection',
            'recruitment_order': recruitment_order,
        }
        return self._get_page_view_values(recruitment_order, access_token, values, 'my_applicant_selections_history',
                                          False, **kwargs)

    @http.route(['/my/recruitment-order/<int:recruitment_order_id>'], type='http', auth="public", website=True)
    def portal_bidding_applicant(self, recruitment_order_id, access_token=None, **kw):
        try:
            # Verify access using the recruitment order's access token
            recruitment_order_sudo = self._document_check_access('recruitment.order', recruitment_order_id,
                                                                 access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._bidding_applicant_get_page_view_values(recruitment_order_sudo, access_token, **kw)
        return request.render("era_recruitment_opportunity.portal_bidding_applicant", values)

    @http.route(['/my/applicant-selection/<int:recruitment_order_id>'], type='http', auth="public", website=True)
    def portal_applicant_selection(self, recruitment_order_id, access_token=None, **kw):
        try:
            recruitment_order_sudo = self._document_check_access('recruitment.order', recruitment_order_id,
                                                                 access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._applicant_selection_get_page_view_values(recruitment_order_sudo, access_token, **kw)
        return request.render("era_recruitment_opportunity.portal_applicant_selection", values)

    @http.route(['/my/applicant-selection/submit/<int:recruitment_order_id>'], type='http', auth="public", website=True,
                methods=['POST'])
    def submit_applicant_selection(self, recruitment_order_id, access_token=None, **kw):
        try:
            recruitment_order_sudo = self._document_check_access('recruitment.order', recruitment_order_id,
                                                                 access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        selected_applicant_id = int(kw.get('selected_applicant', 0))
        if selected_applicant_id:
            applicant = request.env['applicant.line'].sudo().browse(selected_applicant_id)
            if applicant.exists() and applicant.recruitment_order_id.id == recruitment_order_id:
                applicant.write({'state': 'confirm'})
                recruitment_order_sudo.action_done()

        return request.redirect('/my/applicant-selection/%s?access_token=%s' % (recruitment_order_id, access_token))

    # @http.route(['/my/applicant-bidding/confirm/<int:bidding_id>'], type='json', auth="public", website=True)
    # def confirm_flight_bidding_http(self, bidding_id, access_token=None, **kw):
    #     try:
    #         print("SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",bidding_id)
    #         bidding_sudo = request.env['applicant.line'].sudo().browse(bidding_id)
    #         if bidding_sudo.exists():
    #             recruitment_order = bidding_sudo.recruitment_order_id
    #             if not self._document_check_access('applicant.line', bidding_sudo.id, access_token):
    #                 return request.redirect('/my')
    #             if bidding_sudo.state == 'draft':
    #                 bidding_sudo.sudo().action_confirm()
    #             return werkzeug.utils.redirect('/my/recruitment-order/%s?access_token=%s' % (recruitment_order.id, recruitment_order.access_token))
    #     except (AccessError, MissingError):
    #         pass
    #     return request.redirect('/my')

    @http.route(['/my/applicant-bidding/reject/<int:bidding_id>'], type='json', auth="public", website=True)
    def reject_applicant_bidding_http(self, bidding_id, access_token=None, **kw):
        try:
            print("skkkkkkkkkkkkkkkkkkk")
            bidding_sudo = request.env['applicant.line'].sudo().browse(bidding_id)
            if bidding_sudo.exists():
                self._document_check_access('applicant.line', bidding_sudo.id, access_token)
                if bidding_sudo.state == 'draft':
                    bidding_sudo.sudo().action_reject()
                return {"status": "success"}
                # values = self._rejecting_applicant_get_page_view_values(bidding_sudo, access_token, **kw)
                # return request.render('era_recruitment_opportunity.template_applicant_reject_wizard', values)
        except (AccessError, MissingError):
            pass
        return request.redirect('/my')

    @http.route(['/my/applicant-bidding/reject/submit/<int:bidding_id>'], type='http', auth="public", methods=['POST'],
                website=True)
    def submit_reject_applicant_bidding(self, bidding_id, rejection_reason, access_token=None, **kw):
        try:
            _logger.info(f"Processing rejection for bidding ID: {bidding_id} with access token: {access_token}")

            bidding_sudo = request.env['applicant.line'].sudo().browse(int(bidding_id))

            if not bidding_sudo.exists():
                _logger.warning(f"Bidding ID {bidding_id} does not exist.")
                return request.redirect('/my')

            recruitment_order = bidding_sudo.recruitment_order_id

            # Validate access token
            if not self._document_check_access('applicant.line', bidding_sudo.id, access_token):
                _logger.warning(f"Access token validation failed for bidding ID {bidding_id}.")
                return request.redirect('/my')

            # Update state and save rejection reason
            _logger.info(f"Updating bidding {bidding_id} state to 'reject' with reason: {rejection_reason}")
            bidding_sudo.write(
                {'state': 'reject', 'rejection_reason': rejection_reason, 'rejection_date': fields.Date.today()})
            request.env.cr.commit()  # Ensure the change is committed immediately

            # Ensure recruitment_order exists before redirecting
            if recruitment_order:
                _logger.info(f"Redirecting to recruitment order {recruitment_order.id}")
                return werkzeug.utils.redirect(
                    '/my/recruitment-order/%s?access_token=%s' % (recruitment_order.id, recruitment_order.access_token))
            else:
                _logger.warning(f"No recruitment order found for bidding ID {bidding_id}. Redirecting to /my")
                return request.redirect('/my')

        except (AccessError, MissingError) as e:
            _logger.error(f"AccessError or MissingError: {str(e)}")
            return request.redirect('/my')

        except Exception as e:
            _logger.error(f"Unexpected error in rejection: {str(e)}")
            return request.redirect('/my')

    @http.route(['/applicant/offer/response'], type='http', auth='public', website=True)
    def applicant_offer_response(self, applicant_id=None, response=None, **kwargs):
        if not applicant_id or response not in ['accept', 'reject']:
            return request.redirect('/')

        applicant = request.env['hr.applicant'].sudo().browse(int(applicant_id))
        if not applicant:
            return request.redirect('/')

        # Update applicant state based on response
        # Using sudo for now
        contract_stage = request.env['hr.recruitment.stage'].sudo().search([('name', '=', 'Contract Signed')])
        if response == 'accept':
            applicant.sudo().write({'stage_id': contract_stage.id})
        # elif response == 'reject':
        #     applicant.sudo().write({'state': 'offer_rejected'})

        # Redirect to a confirmation page
        return request.render('era_recruitment_opportunity.template_applicant_response', {
            'applicant_name': applicant.name,
            'response': response,
        })


class ApplicantBiddingController(http.Controller):

    @http.route(['/my/applicant-bidding/confirm/<int:bidding_id>'], type='json', auth="public", website=True)
    def confirm_flight_bidding_http(self, bidding_id, access_token=None, **kw):
        print("SWSSSSSSSSSSSSSSSSSSSSSS")
        try:
            bidding_sudo = request.env['applicant.line'].sudo().browse(bidding_id)
            if bidding_sudo.exists():
                recruitment_order = bidding_sudo.recruitment_order_id
                print("recruitment_order>>>>>>>>>>>>>>>>....", recruitment_order)
                # if not self.sudo()._document_check_access('applicant.line', bidding_sudo.id, access_token):
                #     return {"status": "error", "error": "Access denied"}
                print("bidding_sudo>>>>>>>>>>>.", bidding_sudo, bidding_sudo.state)
                if bidding_sudo.state == 'draft':
                    bidding_sudo.sudo().action_confirm()
                return {"status": "success", "recruitment_order_id": recruitment_order.id}
        except (AccessError, MissingError):
            return {"status": "error", "error": "Record not found"}
