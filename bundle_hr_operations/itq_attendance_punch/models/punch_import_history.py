from odoo import api, fields, models


class PunchHistory(models.Model):
    _name = 'punch.import.history'
    _description = 'Attendance Punch Import History'
    _log_access = False
    _order = "zk_action_date Desc"

    user_id = fields.Many2one('res.users', string='Imported by', required=False)
    text = fields.Text(required=True, string='Import Data')
    zk_action_date = fields.Datetime(string='Action Date time', required=True, default=fields.Datetime.now)
    zk_action_type = fields.Selection(string="Data Importing", selection=[('manual', 'Manual'), ('auto', 'Automatic')])
    date_from = fields.Datetime(string="From Date", required=False, )
    date_to = fields.Datetime(string="To Date", required=False, )
    count = fields.Integer(string="Record Count", required=False)
    machine_id = fields.Many2one(comodel_name="itq.attendance.punch.config", string="Machine ID", required=False, )
