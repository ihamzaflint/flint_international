from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class InsurancePolicy(models.Model):
    _name = 'insurance.policy'
    _description = 'Insurance Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc'

    name = fields.Char(string='Policy Name', required=True, tracking=True)
    policy_number = fields.Char(string='Policy Number', required=True, tracking=True)
    insurance_company_id = fields.Many2one('res.partner', 
                                         string='Insurance Company', 
                                         domain=[('vendor_type', '=', 'insurance')],
                                         required=True, tracking=True)
    date_start = fields.Date(string='Start Date', required=True, tracking=True)
    date_end = fields.Date(string='End Date', required=True, tracking=True)
    insurance_class_ids = fields.Many2many('insurance.class', string='Insurance Classes',
                                           help='Classes included in this policy')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Related fields
    employee_insurance_line_ids = fields.One2many('employee.insurance.line', 'policy_id', 
                                                 string='Employee Insurance Lines')
    total_employees = fields.Integer(string='Total Employees', compute='_compute_totals')
    total_annual_cost = fields.Float(string='Total Annual Cost', compute='_compute_totals')
    
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                 default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company)
    
    notes = fields.Text(string='Notes')
    active = fields.Boolean(string='Active', default=True)
    
    @api.depends('employee_insurance_line_ids')
    def _compute_totals(self):
        for policy in self:
            active_lines = policy.employee_insurance_line_ids.filtered(lambda l: l.state == 'active')
            policy.total_employees = len(active_lines)
            policy.total_annual_cost = sum(line.annual_cost for line in active_lines)
    
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for policy in self:
            if policy.date_start >= policy.date_end:
                raise ValidationError(_('End date must be after start date.'))
    
    def action_activate(self):
        """Activate the insurance policy"""
        self.ensure_one()
        self.write({'state': 'active'})
        
    def action_expire(self):
        """Mark policy as expired"""
        self.ensure_one()
        self.write({'state': 'expired'})
        # Auto-end all active insurance lines
        active_lines = self.employee_insurance_line_ids.filtered(lambda l: l.state == 'active')
        for line in active_lines:
            line.action_end_coverage()
    
    def action_cancel(self):
        """Cancel the policy"""
        self.ensure_one()
        self.write({'state': 'cancelled'})
        # Auto-end all active insurance lines
        active_lines = self.employee_insurance_line_ids.filtered(lambda l: l.state == 'active')
        for line in active_lines:
            line.action_end_coverage()
    
    def get_class_cost(self, insurance_class_code, passenger_type='employee'):
        """Get the cost for a specific insurance class and passenger type"""
        self.ensure_one()
        
        # Find the insurance class by code
        insurance_class = self.env['insurance.class'].search([
            ('code', '=', insurance_class_code),
            ('is_active', '=', True)
        ], limit=1)
        
        if not insurance_class:
            return 0.0
        
        # Return the appropriate cost based on passenger type
        if passenger_type == 'employee':
            return insurance_class.employee_cost
        elif passenger_type == 'spouse':
            return insurance_class.spouse_cost
        elif passenger_type in ['father', 'mother', 'child']:
            return insurance_class.child_cost
        else:
            return 0.0


class EmployeeInsuranceLine(models.Model):
    _name = 'employee.insurance.line'
    _description = 'Employee Insurance Coverage Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_added desc'
    
    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    policy_id = fields.Many2one('insurance.policy', string='Insurance Policy', 
                               required=True, ondelete='cascade', tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    
    # Coverage details
    passenger_type = fields.Selection([
        ('employee', 'Employee'),
        ('spouse', 'Spouse'),
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('child', 'Child')
    ], string='Passenger Type', required=True, default='employee', tracking=True)
    
    family_member_id = fields.Many2one('hr.employee.family', string='Family Member', tracking=True)
    
    insurance_class = fields.Many2one('insurance.class', string='Insurance Class', required=True, tracking=True)
    
    # Dates
    date_added = fields.Date(string='Coverage Start Date', required=True, 
                           default=fields.Date.context_today, tracking=True)
    date_removed = fields.Date(string='Coverage End Date', tracking=True)
    
    # Calculated fields
    annual_cost = fields.Float(string='Annual Cost', compute='_compute_costs', store=True)
    prorated_cost = fields.Float(string='Prorated Cost', compute='_compute_costs', store=True)
    refund_amount = fields.Float(string='Refund Amount', compute='_compute_costs', store=True)
    days_covered = fields.Integer(string='Days Covered', compute='_compute_costs', store=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Action tracking
    action_type = fields.Selection([
        ('addition', 'Addition'),
        ('deletion', 'Deletion'),
        ('update', 'Update'),
        ('downgrade', 'Downgrade'),
        ('upgrade', 'Upgrade'),
    ], string='Action Type', default='addition', tracking=True)
    
    # Financial tracking
    bill_id = fields.Many2one('account.move', string='Bill', readonly=True, copy=False)
    refund_id = fields.Many2one('account.move', string='Refund', readonly=True, copy=False)
    
    currency_id = fields.Many2one('res.currency', related='policy_id.currency_id', readonly=True)
    company_id = fields.Many2one('res.company', related='policy_id.company_id', readonly=True)
    
    notes = fields.Text(string='Notes')
    
    @api.depends('employee_id', 'passenger_type', 'family_member_id', 'insurance_class')
    def _compute_name(self):
        for line in self:
            if line.passenger_type == 'employee':
                name = f"{line.employee_id.name} - {line.insurance_class.name}"
            elif line.family_member_id:
                name = f"{line.family_member_id.name} ({line.passenger_type}) - {line.insurance_class.name}"
            else:
                name = f"{line.employee_id.name} ({line.passenger_type}) - {line.insurance_class.name}"
            line.name = name
    
    @api.depends('policy_id', 'insurance_class', 'passenger_type', 'date_added', 'date_removed')
    def _compute_costs(self):
        for line in self:
            if not line.policy_id or not line.insurance_class:
                line.annual_cost = 0.0
                line.prorated_cost = 0.0
                line.refund_amount = 0.0
                line.days_covered = 0
                continue
                
            # Get annual cost for this class and passenger type
            line.annual_cost = line.policy_id.get_class_cost(line.insurance_class.code, line.passenger_type)
            
            # Calculate prorated cost (addition)
            if line.date_added:
                end_date = line.date_removed or line.policy_id.date_end
                if end_date >= line.date_added:
                    days_covered = (end_date - line.date_added).days + 1
                    line.days_covered = days_covered
                    line.prorated_cost = (days_covered / 365.0) * line.annual_cost
                else:
                    line.days_covered = 0
                    line.prorated_cost = 0.0
            else:
                line.days_covered = 0
                line.prorated_cost = 0.0
            
            # Calculate refund amount (deletion)
            if line.date_removed and line.state == 'ended':
                remaining_days = (line.policy_id.date_end - line.date_removed).days
                if remaining_days > 0:
                    line.refund_amount = (remaining_days / 365.0) * line.annual_cost
                else:
                    line.refund_amount = 0.0
            else:
                line.refund_amount = 0.0
    
    @api.constrains('date_added', 'date_removed', 'policy_id')
    def _check_dates(self):
        for line in self:
            if line.date_added and line.policy_id:
                if line.date_added < line.policy_id.date_start:
                    raise ValidationError(_('Coverage start date cannot be before policy start date.'))
                if line.date_added > line.policy_id.date_end:
                    raise ValidationError(_('Coverage start date cannot be after policy end date.'))
                    
            if line.date_removed:
                if line.date_removed < line.date_added:
                    raise ValidationError(_('Coverage end date cannot be before start date.'))
                if line.date_removed > line.policy_id.date_end:
                    raise ValidationError(_('Coverage end date cannot be after policy end date.'))
    
    # @api.constrains('employee_id', 'passenger_type', 'family_member_id', 'policy_id', 'insurance_class')
    # def _check_unique_coverage(self):
    #     for line in self:
    #         if line.state in ['draft', 'active']:
    #             domain = [
    #                 ('employee_id', '=', line.employee_id.id),
    #                 ('passenger_type', '=', line.passenger_type),
    #                 ('policy_id', '=', line.policy_id.id),
    #                 ('state', 'in', ['draft', 'active']),
    #                 ('id', '!=', line.id),
    #                 ('action_type', '=', line.action_type)
    #             ]
    #
    #             if line.passenger_type != 'employee' and line.family_member_id:
    #                 domain.append(('family_member_id', '=', line.family_member_id.id))
    #
    #             existing = self.search(domain)
    #             if existing:
    #                 raise ValidationError(_('This employee/family member already has active coverage in this policy.'))
    def action_activate(self):
        """Activate the insurance coverage and create bill"""
        for line in self:
            if line.state != 'draft':
                raise UserError(_('Only draft insurance lines can be activated.'))
                
            line.write({'state': 'active'})
            
            # Create bill for the prorated cost
            if line.prorated_cost > 0:
                line._create_insurance_bill()
                
            # Log the activation
            line.message_post(
                body=_('Insurance coverage activated. Prorated cost: %s SAR for %s days.') % 
                     (line.prorated_cost, line.days_covered),
                subject=_('Coverage Activated')
            )
    
    def action_end_coverage(self):
        """End the insurance coverage and create refund if applicable"""
        for line in self:
            if line.state != 'active':
                raise UserError(_('Only active insurance lines can be ended.'))
                
            line.write({
                'state': 'ended',
                'date_removed': line.date_removed or fields.Date.context_today(line)
            })
            
            # Create refund if there's a refund amount
            if line.refund_amount > 0:
                line._create_insurance_refund()
                
            # Log the end of coverage
            line.message_post(
                body=_('Insurance coverage ended. Refund amount: %s SAR.') % line.refund_amount,
                subject=_('Coverage Ended')
            )
    
    def action_cancel(self):
        """Cancel the insurance coverage"""
        self.write({'state': 'cancelled'})
    
    def _create_insurance_bill(self):
        """Create vendor bill for insurance cost"""
        self.ensure_one()
        
        if not self.policy_id.insurance_company_id:
            raise UserError(_('Insurance company is required to create bill.'))
            
        # Get the insurance service product
        product = self._get_insurance_product()
        if not product:
            raise UserError(_('Insurance service product not found. Please contact administrator.'))
            
        # Prepare bill values
        bill_vals = {
            'move_type': 'in_invoice',
            'partner_id': self.policy_id.insurance_company_id.id,
            'invoice_date': fields.Date.context_today(self),
            'ref': f"Insurance Coverage - {self.name}",
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'name': f"Insurance Coverage - {self.name} ({self.days_covered} days)",
                'quantity': 1,
                'price_unit': self.prorated_cost,
                'account_id': product.property_account_expense_id.id or 
                             product.categ_id.property_account_expense_categ_id.id,
            })]
        }
        
        bill = self.env['account.move'].create(bill_vals)
        bill.action_post()
        
        self.bill_id = bill.id
        
        _logger.info(f'Insurance bill {bill.name} created for {self.name} - Amount: {self.prorated_cost} SAR')
        
        return bill
    
    def _create_insurance_refund(self):
        """Create credit note for insurance refund"""
        self.ensure_one()
        
        if not self.policy_id.insurance_company_id:
            raise UserError(_('Insurance company is required to create refund.'))
            
        # Get the insurance service product
        product = self._get_insurance_product()
        if not product:
            raise UserError(_('Insurance service product not found. Please contact administrator.'))
            
        # Prepare credit note values
        refund_vals = {
            'move_type': 'in_refund',
            'partner_id': self.policy_id.insurance_company_id.id,
            'invoice_date': fields.Date.context_today(self),
            'ref': f"Insurance Refund - {self.name}",
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'name': f"Insurance Refund - {self.name}",
                'quantity': 1,
                'price_unit': self.refund_amount,
                'account_id': product.property_account_expense_id.id or 
                             product.categ_id.property_account_expense_categ_id.id,
            })]
        }
        
        refund = self.env['account.move'].create(refund_vals)
        refund.action_post()
        
        self.refund_id = refund.id
        
        _logger.info(f'Insurance refund {refund.name} created for {self.name} - Amount: {self.refund_amount} SAR')
        
        return refund
    
    def _get_insurance_product(self):
        """Get the insurance service product"""
        try:
            return self.env.ref('scs_operation.product_insurance_service')
        except ValueError:
            # Fallback: search for any insurance service product
            product = self.env['product.product'].search([
                ('name', 'ilike', 'insurance'),
                ('type', '=', 'service')
            ], limit=1)
            if not product:
                # Create a basic insurance service product if none exists
                product = self.env['product.product'].create({
                    'name': 'Insurance Service',
                    'type': 'service',
                    'can_be_expensed': True,
                })
            return product
    
    def action_view_bill(self):
        """View the related bill"""
        self.ensure_one()
        if not self.bill_id:
            return
            
        return {
            'type': 'ir.actions.act_window',
            'name': _('Insurance Bill'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.bill_id.id,
            'target': 'current'
        }
    
    def action_view_refund(self):
        """View the related refund"""
        self.ensure_one()
        if not self.refund_id:
            return
            
        return {
            'type': 'ir.actions.act_window',
            'name': _('Insurance Refund'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.refund_id.id,
            'target': 'current'
        }


# Extension to existing LogisticOrder model
class LogisticOrderInsuranceExtension(models.Model):
    _inherit = 'logistic.order'
    
    insurance_policy_id = fields.Many2one('insurance.policy', string='Insurance Policy',
                                        domain=[('state', '=', 'active')])

    def _create_insurance_lines_from_order(self):
        """Create insurance lines based on logistic order lines"""
        self.ensure_one()
        
        if self.order_type != 'insurance' or not self.insurance_policy_id:
            return
            
        insurance_lines = []
        
        # Create employee insurance line when type is 'employee' or 'both'
        if self.insurance_type in ['employee', 'both'] and self.insurance_class:
            employee_line_vals = {
                'policy_id': self.insurance_policy_id.id,
                'employee_id': self.employee_id.id,
                'passenger_type': 'employee',
                'family_member_id': False,
                'insurance_class': self.insurance_class.id,
                'date_added': fields.Date.context_today(self),
                'action_type': self.insurance_required_action or 'addition',
                'notes': f'Created from logistic order: {self.name} (Employee)'
            }
            
            employee_insurance_line = self.env['employee.insurance.line'].create(employee_line_vals)
            insurance_lines.append(employee_insurance_line)
        
        # Create family member insurance lines when type is 'family' or 'both'
        if self.insurance_type in ['family', 'both']:
            for order_line in self.logistic_order_line_ids:
                if order_line.insurance_class and order_line.insurance_cost > 0:
                    # Since insurance_class is now a Many2one field, use it directly
                    insurance_class = order_line.insurance_class
                    
                    if insurance_class:
                        line_vals = {
                            'policy_id': self.insurance_policy_id.id,
                            'employee_id': self.employee_id.id,
                            'passenger_type': order_line.passenger_type,
                            'family_member_id': order_line.family_member_id.id if order_line.family_member_id else False,
                            'insurance_class': insurance_class.id,
                            'date_added': fields.Date.context_today(self),
                            'action_type': self.insurance_required_action or 'addition',
                            'notes': f'Created from logistic order: {self.name} (Family)'
                        }
                        
                        insurance_line = self.env['employee.insurance.line'].create(line_vals)
                        insurance_lines.append(insurance_line)
                
        return insurance_lines
    
    def action_approve_operation_manager(self):
        """Override to create insurance lines when insurance order is approved"""
        result = super().action_approve_operation_manager()
        
        if self.order_type == 'insurance' and self.insurance_policy_id:
            # Create insurance lines and activate them
            insurance_lines = self._create_insurance_lines_from_order()
            for line in insurance_lines:
                line.action_activate()
                
        return result


# Wizard for bulk insurance operations
class InsuranceBulkOperationWizard(models.TransientModel):
    _name = 'insurance.bulk.operation.wizard'
    _description = 'Bulk Insurance Operations Wizard'
    
    operation_type = fields.Selection([
        ('add_employees', 'Add Multiple Employees'),
        ('change_class', 'Change Insurance Class'),
        ('end_coverage', 'End Coverage for Multiple Employees')
    ], string='Operation Type', required=True)
    
    policy_id = fields.Many2one('insurance.policy', string='Insurance Policy', required=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    insurance_class = fields.Many2one('insurance.class', string='Insurance Class')
    
    new_insurance_class = fields.Many2one('insurance.class', string='New Insurance Class')
    
    date_effective = fields.Date(string='Effective Date', default=fields.Date.context_today)
    
    def action_execute(self):
        """Execute the bulk operation"""
        if self.operation_type == 'add_employees':
            self._add_employees()
        elif self.operation_type == 'change_class':
            self._change_insurance_class()
        elif self.operation_type == 'end_coverage':
            self._end_coverage()
            
        return {'type': 'ir.actions.act_window_close'}
    
    def _add_employees(self):
        """Add multiple employees to insurance policy"""
        for employee in self.employee_ids:
            line_vals = {
                'policy_id': self.policy_id.id,
                'employee_id': employee.id,
                'passenger_type': 'employee',
                'insurance_class': self.insurance_class.id,
                'date_added': self.date_effective,
                'action_type': 'addition'
            }
            
            insurance_line = self.env['employee.insurance.line'].create(line_vals)
            insurance_line.action_activate()
    
    def _change_insurance_class(self):
        """Change insurance class for multiple employees"""
        for employee in self.employee_ids:
            # End current coverage
            current_lines = self.env['employee.insurance.line'].search([
                ('employee_id', '=', employee.id),
                ('policy_id', '=', self.policy_id.id),
                ('passenger_type', '=', 'employee'),
                ('state', '=', 'active')
            ])
            
            for line in current_lines:
                line.date_removed = self.date_effective
                line.action_end_coverage()
            
            # Create new coverage with new class
            line_vals = {
                'policy_id': self.policy_id.id,
                'employee_id': employee.id,
                'passenger_type': 'employee',
                'insurance_class': self.new_insurance_class.id,
                'date_added': self.date_effective,
                'action_type': 'upgrade' if self.new_insurance_class.sequence > self.insurance_class.sequence else 'downgrade'
            }
            
            insurance_line = self.env['employee.insurance.line'].create(line_vals)
            insurance_line.action_activate()
    
    def _end_coverage(self):
        """End coverage for multiple employees"""
        for employee in self.employee_ids:
            active_lines = self.env['employee.insurance.line'].search([
                ('employee_id', '=', employee.id),
                ('policy_id', '=', self.policy_id.id),
                ('state', '=', 'active')
            ])
            
            for line in active_lines:
                line.date_removed = self.date_effective
                line.action_end_coverage()