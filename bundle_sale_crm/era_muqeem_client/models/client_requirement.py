# -*- coding: utf-8 -*-


from odoo import models, fields, _,api

class Clientrequests(models.Model):
    _name = "client.requests"
    _description = "Client requests"
    _order = 'date desc'


    name = fields.Char(
        string="Request",
        copy=False,
    )
    user=fields.Char(
        string="User")

    employee=fields.Char(
        string="Employee")


    des=fields.Char(
        string="Result")

    date=fields.Datetime(string="Date")




