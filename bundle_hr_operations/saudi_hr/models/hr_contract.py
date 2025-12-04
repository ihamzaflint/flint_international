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


class HrContract(models.Model):
    _inherit = 'hr.contract'

    gosi_number = fields.Char(string="GOSI Number")
    sponsor_id = fields.Many2one('hr.sponsor', string="Sponsor")
    sponsor_number = fields.Char(related="sponsor_id.code", string="Sponsor Number")
    gosi_registration_date = fields.Date('GOSI Registration Date', groups="hr.group_hr_user", tracking=True)
    phone_allowance = fields.Monetary(string='Phone Allowance')
    tools_allowance = fields.Monetary(string='Tools Allowance')
    tickets_allowance = fields.Monetary(string='Tickets Allowance')

    eos_payment_allowance = fields.Monetary(string='EOS Payment', help='To pay monthly EOS amount')
    eos_provision_accural_allowance = fields.Monetary(string='EOS Provision Accural', help='To adjust the increment accural values manually.')
    annual_leave_vacation_amount_allowance = fields.Monetary(string='Annual Leave Vacation')

    tech_allowance = fields.Monetary(string='Technical Allowance')
    kids_allowance = fields.Monetary(string='Kids Allowance')
    granted_monthly_bonus = fields.Monetary(string='Granted Monthly Bonus')
    special_allowance = fields.Monetary(string='Special Allowance')
    niche_skill_allowance = fields.Monetary(string='Niche Skill Allowance')
    shift_allowance = fields.Monetary(string='Shift Allowance')
    car_allowance = fields.Monetary(string='Car Allowance')
    gas_allowance = fields.Monetary(string='Gas Allowance')
    oc_rec_allowance = fields.Monetary(string='OC/Rec Allowance')
    project_allowance = fields.Monetary(string='Project Allowance')
    food_allowance = fields.Monetary(string='Food Allowance')
    edu_allowance = fields.Monetary(string='Education Allowance')
    gosi_comp_onbehalf = fields.Monetary(string='GOSI OnBehalf', help='GOSI company contribution onbehalf')

    @api.depends('employee_id', 'employee_id.job_id')
    def _compute_employee_contract(self):
        for contract in self.filtered('employee_id'):
            contract.job_id = contract.employee_id.job_id
            contract.department_id = contract.employee_id.department_id
            contract.resource_calendar_id = contract.employee_id.resource_calendar_id
            contract.company_id = contract.employee_id.company_id


