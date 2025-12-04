# -*- coding: utf-8 -*-
###################################################################################
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    visa_no = fields.Char('Id Number', groups="hr.group_hr_user", tracking=True)
    visa_expire = fields.Date('Iqama Expiry Date', groups="hr.group_hr_user", tracking=True)
    work_permit_expiration_date_hijri = fields.Char('Work Permit Expiration Date (Hijri)', groups="hr.group_hr_user",
                                                    tracking=True)

    # employee_no = fields.Char(string="Employee ID")
    # name = fields.Char(string="Employee Name", tracking=True,translate=True)
    # name = fields.Char(string="Employee Name", related='resource_id.name', store=True, readonly=False, tracking=True)
    blood_group = fields.Char('Blood Group')
    iqama_occupation = fields.Char('Iqama Occupation')
    actual_work_trade = fields.Char('Actual Work Trade')
    actual_work_trade_arabic = fields.Char('Actual Work Trade Arabic')
    personal_email = fields.Char('Personal Email')

    date_of_entry = fields.Char('Date of Entry', groups="hr.group_hr_user",tracking=True, help='Date of entry in kingdom.')
    passport_expiry_date = fields.Date('Passport Expiry Date', groups="hr.group_hr_user", tracking=True)
    work_permit_issue_date = fields.Date('Work Permit IssueDate', groups="hr.group_hr_user", tracking=True)
    is_outside_kingdom = fields.Boolean('Outside Kingdom',groups="hr.group_hr_user")
    pf_no = fields.Char('PF No', groups="hr.group_hr_user", tracking=True)

    
    @api.depends('visa_no')
    def _fill_idendification_no(self):
        for rec in self:
            rec.identification_id = rec.visa_no
            