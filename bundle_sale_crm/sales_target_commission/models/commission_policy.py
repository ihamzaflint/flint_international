from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CommissionPolicy(models.Model):
    _name = 'commission.policy'
    _description = 'Commission Policy'

    name = fields.Char(string="Description", readonly=True,
                       copy=False)
    active = fields.Boolean(default=False)
    state = fields.Selection(string="Commission Policy Status",
                             selection=[('draft', 'Draft'),
                                        ('active', 'Active'),
                                        ('in_active', 'In-Active'),
                                        ], default='draft')
    commission_policy = fields.Selection(selection=[('amount_based', 'Target amount based'),
                                                    ('payroll_based', 'Payroll Based')],
                                         required=True, default='amount_based', readonly=True,
                                         )
    fixed_payroll = fields.Float(string="Fixed payroll (%)", readonly=True,
                                 )
    variable_payroll = fields.Float(string="Variable Payroll (%)", store=True, readonly=True,
                                    compute='_compute_variable_payroll')

    target_type = fields.Selection(selection=[('percentage', 'Percentage'), ('amount', 'Amount'), ],
                                   default='percentage', required=True, readonly=True,
                                   )

    details_ids = fields.One2many(comodel_name="policy.details", inverse_name="policy_id", string="Policy Details",
                                  readonly=True, copy=True)

    @api.onchange('details_ids')
    def _onchange_details_ids(self):
        for rec in self:
            for index, line in enumerate(rec.details_ids):
                if index > 0:
                    line.target_from = rec.details_ids[index - 1].target_to
                    if line.target_to > 0 and line.target_from > 0:
                        if line.target_to <= line.target_from:
                            raise ValidationError(_("Target to must be greater than Target from"))
                    if line.target_from > 0:
                        if line.target_from != rec.details_ids[index - 1].target_to:
                            raise ValidationError(
                                _("Target from must be equal to {}").format(rec.details_ids[index - 1].target_to))
                    if line.commission > 0:
                        if line.commission <= rec.details_ids[index - 1].commission:
                            raise ValidationError(
                                _("The commission of the previous line shall be less than the commission of the next line"))

    @api.constrains('name')
    def _constrain_name(self):
        for rec in self:
            name_count = self.search_count([('name', '=', rec.name)])
            if name_count > 1:
                raise ValidationError(_("Description is unique"))

    @api.constrains('active')
    def _constrain_active(self):
        for rec in self:
            target_id = self.env['sales.team.target'].search([('policy_id', '=', rec.id), ('state', '=', 'running')])
            if not rec.active and target_id:
                raise ValidationError(
                    _("Sorry, the commission policy cannot be archived due to it is set to a running target {}").format(
                        target_id.name))

    @api.constrains('fixed_payroll', 'commission_policy')
    def _constrain_fixed_payroll(self):
        for rec in self:
            if rec.commission_policy == 'payroll_based':
                if not (0 < rec.fixed_payroll <= 100):
                    raise ValidationError(
                        _("Fixed payroll (%) must be greater zero and less than or equal to 100"))

    @api.depends('fixed_payroll')
    def _compute_variable_payroll(self):
        for rec in self:
            rec.variable_payroll = 100 - rec.fixed_payroll

    @api.model
    def create(self, values):
        if not values.get('details_ids'):
            raise ValidationError(_("At least one details line shall be recorded"))
        return super(CommissionPolicy, self).create(values)

    @api.constrains('details_ids')
    def _constrain_details_ids(self):
        for rec in self:
            if len(rec.details_ids) <= 0:
                raise ValidationError(_("At least one details line shall be recorded"))

    def set_active(self):
        for rec in self:
            rec.state = 'active'
            rec.active = True

    def set_in_active(self):
        for rec in self:
            rec.state = 'in_active'
            rec.active = False

    def set_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.active = False

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You can't delete this record"))
        return super(CommissionPolicy, self).unlink()

    def copy(self, default=None):
        self.ensure_one()
        res = super(CommissionPolicy, self.with_context(from_copy=True)).copy(default)
        return res


class PolicyDetails(models.Model):
    _name = 'policy.details'
    _description = 'Policy Details'

    policy_id = fields.Many2one(comodel_name="commission.policy", string="Commission Policy")
    target_from = fields.Float()
    target_to = fields.Float()
    commission = fields.Float(string="Commission %")

    def get_last_line(self, policy_id, line):
        last_line = self.search([('policy_id', '=', policy_id.id),
                                 ('id', '<', line.id)], order='id desc', limit=1)
        return last_line

    def get_after_line(self, policy_id, line):
        after_line = self.search([('policy_id', '=', policy_id.id),
                                  ('id', '>', line.id)], order='id asc', limit=1)
        return after_line

    # @api.onchange('commission')
    # def _onchange_commission(self):
    #     for rec in self:
    #         if rec.commission != 0:
    #             rec._constrain_commission()

    @api.constrains('commission')
    def _constrain_commission(self):
        for rec in self:
            get_after_line = self.get_after_line(rec.policy_id, rec)
            if get_after_line:
                if rec.commission >= get_after_line.commission:
                    raise ValidationError(
                        _("The commission of the previous line shall be less than the commission of the next line"))
            if rec.policy_id and rec.policy_id.target_type == 'percentage':
                if not (0 <= rec.commission <= 100):
                    raise ValidationError(_("Commission must be greater or equal to zero and less or equal to 100"))
            last_line = self.get_last_line(rec.policy_id, rec)
            if last_line:
                if rec.commission <= last_line.commission:
                    raise ValidationError(
                        _("The commission of the next line shall be greater than the previous line(more than {})").format(
                            last_line.commission))

    # @api.onchange('target_from', 'target_to')
    # def _onchange_target_from_to(self):
    #     for rec in self:
    #         if rec.target_from != 0 or rec.target_to != 0:
    #             rec._constrain_target_from_to()
    #
    @api.constrains('target_from', 'target_to')
    def _constrain_target_from_to(self):
        if not self._context.get('from_copy'):
            for index, rec in enumerate(self):
                last_line = self.get_last_line(rec.policy_id, rec)
                if rec.policy_id and rec.policy_id.target_type == 'percentage':
                    if not (0 <= rec.target_from <= 100):
                        raise ValidationError(
                            _("Target from must be greater or equal to zero and less or equal to 100"))
                    if not (0 <= rec.target_to <= 100):
                        raise ValidationError(
                            _("Target to must be greater than or equal to zero and less than or equal to 100"))
                if len(self) > 1:
                    if index > 0:
                        get_after_line = self.get_after_line(rec.policy_id, rec)
                        if get_after_line:
                            if rec.target_to != get_after_line.target_from:
                                raise ValidationError(
                                    _("Target To must be equal to target from at next line at line {}").format(
                                        index + 1))
                        if rec.target_from != last_line.target_to:
                            raise ValidationError(
                                _("Target from must be equal to {} at line {}").format(last_line.target_to, index + 1))
                        if rec.target_to <= rec.target_from:
                            raise ValidationError(
                                _("Target to must be greater than Target from at line {}").format(index + 1))
                else:
                    get_after_line = self.get_after_line(rec.policy_id, rec)
                    if get_after_line:
                        if rec.target_to != get_after_line.target_from:
                            raise ValidationError(
                                _("Target To must be equal to target from at next line at line"))
                    if last_line:
                        if rec.target_from != last_line.target_to:
                            raise ValidationError(_("Target from must be equal to {}").format(last_line.target_to))
                        if rec.target_to <= rec.target_from:
                            raise ValidationError(_("Target to must be greater than Target from"))
