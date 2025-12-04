# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
from odoo.addons.hijri_date_util.models import itq_date_util as Hijri


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def get_hijri_date(self, check_date):
        self.ensure_one()
        if check_date:
            if not isinstance(check_date, date):
                check_date = fields.Date.from_string(check_date)
            hijri_obj = Hijri.create_hij_from_greg(check_date)
            hijri_date = str(hijri_obj.year) + '/' + str(hijri_obj.month) + '/' + str(hijri_obj.day)
            return hijri_date
        else:
            return False
