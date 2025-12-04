from odoo import fields, models, api


class ServiceType(models.Model):
    _name = "service.type"
    _description = "Service Type"

    def _get_default_credit_account(self):
        return self.env['account.account'].search([('name', 'ilike', 'Outstanding Payments'),
                                                   ('company_id', '=', self.env.company.id)], limit=1)

    name = fields.Char(required=True)
    code = fields.Char()
    description = fields.Text("Description")
    active = fields.Boolean(default=True)
    is_saddad_required = fields.Boolean("Is Saddad Required", default=False)
    service_type = fields.Selection([('individual', 'Individual'),
                                     ('enterprise', 'Enterprise'),
                                     ('no_payment', 'Without Payment')], default='individual')
    is_project_required = fields.Boolean("Is Project Required", default=False)
    sister_company_ids = fields.Many2many('sister.company', string="Sister Companies")
    default_credit_account_id = fields.Many2one('account.account',
                                                string="Default Credit Account",
                                                default=_get_default_credit_account, )
    default_debit_account_id = fields.Many2one('account.account',
                                               string="Default Debit Account",

                                               )
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    initial_cost = fields.Monetary("Initial Cost", currency_field='currency_id')
    including_payment = fields.Boolean("Including Payment", default=False)
    is_muqeem_service = fields.Boolean("Is Muqeem Service", required=True)

    saddad_type = fields.Selection(
        [
            ('saddad', 'Saddad'),
            ('moi', 'MOI')
        ],
        string="Selection Field",
        compute='_compute_saddad_type',
        store=True
    )
    partner_id = fields.Many2one('res.partner', string="Default Partner")
    tax_ids = fields.Many2many('account.tax', string="Taxes")
    product_id = fields.Many2one('product.product', string="Product")
    account_id = fields.Many2one('account.account', string="Invoice / Bill Account")


    @api.depends('is_saddad_required')
    def _compute_saddad_type(self):
        for record in self:
            record.saddad_type = 'saddad' if record.is_saddad_required else 'moi'

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Service Type name already exists!"),
    ]

    @api.onchange('including_payment')
    def _onchange_including_payment(self):
        if self.including_payment:
            self.default_credit_account_id = self.env['account.account'].search(
                [('name', 'ilike', 'Outstanding Payments'),
                 ('company_id', '=', self.env.company.id)], limit=1)
        else:
            self.default_credit_account_id = False
            self.default_debit_account_id = False
            self.initial_cost = 0.0
