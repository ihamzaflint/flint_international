
from odoo import models, fields, api, _
import requests




class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    iqama_number = fields.Char(string="Iqama Number")
    last_visa_number = fields.Char(string="Last Visanumber" )
    borderNumber = fields.Char(string="BorderNumber")
    passportNumber = fields.Char(string="PassportNumber")
    expiry_pass_date = fields.Date(string="PassportExpiry")
    expiry_date_iqama = fields.Date(string="IqamaExpiry")
    address_id = fields.Many2one('res.partner', string="Address", compute='_compute_address_id')

    def _get_is_admin(self):
        """
        Compute method to check if the user is an admin.
        """
        for rec in self:
            rec.is_admin = False
            is_debug_mode = self.user_has_groups('base.group_no_one')

            if self.env.user.id == self.env.ref('base.user_admin').id :
                rec.is_admin = True

    is_admin = fields.Boolean(compute=_get_is_admin, string="Is Admin",
                              help='Check if the user is an admin.')


    @api.onchange('expiry_date_iqama')
    def _compute_is_iqama_expired(self):
        if self.expiry_date_iqama:
            self.visa_expire = self.expiry_date_iqama

    @api.onchange('iqama_number')
    def _compute_is_iqama_exist(self):
        if self.iqama_number:
            self.visa_no = self.iqama_number

    @api.onchange('expiry_pass_date')
    def _compute_is_passport_expired(self):
        if self.expiry_pass_date:
            self.passport_expiry_date = self.expiry_pass_date
            self.passport_exp_date = self.expiry_pass_date
            self.passport_expiry_date = self.expiry_pass_date
