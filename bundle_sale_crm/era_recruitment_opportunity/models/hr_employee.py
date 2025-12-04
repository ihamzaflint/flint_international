# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    code = fields.Char(default=lambda self: _('New'), readonly=True, copy=False)

    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('hr.employee.code') or 'New'
        return super(HrEmployee, self).create(vals)


class HrPaylsip(models.Model):
    _inherit = 'hr.payslip'

    crm_costing_processed = fields.Boolean(string="CRM Costing Processed", default=False, copy=False)

    def _get_net_from_payslip(self, payslip):
        """Return Net Salary value for a payslip (single record expected)."""

        # try payslip-level fields first
        for fld in ('net_wage', 'amount_total', 'net_total', 'net_amount', 'net', 'net_pay', 'total'):
            if fld in payslip._fields:
                val = getattr(payslip, fld, False)
                if val:
                    return float(val or 0.0)

        # fallback: use NET line by code
        if payslip.line_ids:
            net_lines = payslip.line_ids.filtered(lambda l: (getattr(l, 'code', '') or '').upper() == 'NET')
            if net_lines:
                # *** IMPORTANT: use amount_org if present ***
                if 'amount_org' in net_lines._fields:
                    return float(sum([getattr(l, 'amount_org', 0.0) or 0.0 for l in net_lines]))
                # fallback to total/amount if amount_org not available
                return float(sum([
                    getattr(l, 'total', 0.0) or getattr(l, 'amount', 0.0) or 0.0
                    for l in net_lines
                ]))

        return 0.0

    def _find_applicant_lines_for_employee(self, employee):
        """Find crm.applicant.line records associated with an employee."""
        CRMApplicant = self.env['crm.applicant.line']
        # 1) file_name == employee.code
        if getattr(employee, 'code', False):
            lines = CRMApplicant.search([('file_name', '=', employee.code)])
            if lines:
                return lines
        # 2) work_email or email
        email = getattr(employee, 'work_email', False) or getattr(employee, 'email', False)
        if email:
            lines = CRMApplicant.search([('email', '=', email)])
            if lines:
                return lines
        # 3) name match
        if getattr(employee, 'name', False):
            lines = CRMApplicant.search([('name', '=', employee.name)])
            if lines:
                return lines
        return CRMApplicant.browse([])

    def _create_or_update_costing_line(self, lead, applicant_line, employee, net_amount):
        """
        Create or update crm.costing.summary.line for given parameters.
        - lead: crm.lead record
        - applicant_line: crm.applicant.line record
        - employee: hr.employee record
        - net_amount: float
        """
        CrmCostLine = self.env['crm.costing.summary.line']
        existing = CrmCostLine.search([
            ('lead_id', '=', lead.id),
            ('employee_id', '=', employee.id),
            ('applicant_line_id', '=', applicant_line.id),
        ], limit=1)
        if existing:
            existing.write({
                'net_salary': (existing.net_salary or 0.0) + float(net_amount or 0.0),
                'payslip_count': (existing.payslip_count or 0) + 1,
            })
            _logger.info("Updated costing line %s (lead %s) +%s", existing.id, lead.id, net_amount)
        else:
            CrmCostLine.create({
                'lead_id': lead.id,
                'applicant_line_id': applicant_line.id,
                'employee_id': employee.id,
                'net_salary': float(net_amount or 0.0),
                'payslip_count': 1,
            })
            _logger.info("Created costing line for lead %s emp %s amount %s", lead.id, employee.id, net_amount)

    def compute_sheet(self):
        """
        Override compute_sheet: call super, then create/update costing_summary lines
        for any payslips computed in this call.
        """
        res = super(HrPaylsip, self).compute_sheet()

        # Process each payslip in the recordset
        for payslip in self:
            try:
                # Skip if already processed (optional)
                if payslip.crm_costing_processed:
                    continue

                # Ensure payslip has employee
                if not payslip.employee_id:
                    payslip.crm_costing_processed = True
                    continue

                # Extract net amount (best-effort)
                net_amount = self._get_net_from_payslip(payslip)

                # Find crm applicant lines for this employee
                appl_lines = self._find_applicant_lines_for_employee(payslip.employee_id)
                if not appl_lines:
                    # nothing to attach to — mark as processed so we don't keep trying
                    payslip.crm_costing_processed = True
                    _logger.debug("No CRM applicant line found for employee %s (payslip %s)", payslip.employee_id.id,
                                  payslip.id)
                    continue

                # For every applicant_line found, create/update cost summary line under its lead
                for appl in appl_lines:
                    lead = appl.crm_lead_id
                    if not lead:
                        _logger.debug("Applicant line %s has no lead; skipping", appl.id)
                        continue
                    self._create_or_update_costing_line(lead, appl, payslip.employee_id, net_amount)

                # mark processed
                payslip.crm_costing_processed = True

            except Exception as e:
                # log and continue with next payslip
                _logger.exception("Error processing payslip %s for crm costing: %s", payslip.id, e)
        return res

    def action_payslip_cancel(self):
        """Reset processed flag on cancel (do not auto-delete cost lines)."""
        res = super(HrPaylsip, self).action_payslip_cancel()
        # We reset flag so that a re-compute can pick it up, if needed
        for p in self:
            if p.crm_costing_processed:
                p.crm_costing_processed = False
        return res
