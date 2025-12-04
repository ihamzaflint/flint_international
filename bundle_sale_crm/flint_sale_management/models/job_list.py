from odoo import api, fields, models


class JobList(models.Model):
    _name = 'job.list'
    _description = 'this model is designed to define the list of positions that can be recruited at the service line ' \
                   'level '

    name = fields.Char(string='Job Position', required=True)
    description = fields.Text(string='Description')
    job_code = fields.Char(string='Job Code')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'The job position must be unique!'),
        ('job_code_unique', 'unique(job_code)', 'The job code must be unique!'),
    ]
