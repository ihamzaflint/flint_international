# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import time
from lxml import etree


class PostmanCourierType(models.Model):
    """Courier Type."""

    _name = "postman.courier.type"
    _description = "Courier Type"

    name = fields.Char('Name', required=True)


class PostmanCourier(models.Model):
    _name = 'postman.courier.inwards'
    _description = "Inwards Courier"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Serial No',
        copy=False,
        default='New'
    )

    summary = fields.Char('Summary',
                          readonly=True)
    active = fields.Boolean('Active', default=1)
    user_id = fields.Many2one('res.users', 'Collect By',
                              default=lambda self: self._uid,
                              readonly=True)
    owner_id = fields.Many2one('res.users', 'Assignee Name',
                               readonly=True,
                               tracking=True, )
    department_id = fields.Many2one('hr.department', 'Department',
                                    readonly=True)
    package_amount = fields.Float(string="Package Amount", readonly=True)
    description = fields.Text('Description',
                              readonly=True)
    email_from = fields.Char('Email',
                             readonly=True)
    date_open = fields.Datetime('Opened', readonly=True,
                                )
    categ_id = fields.Many2one('postman.courier.type', 'Type of Indent',
                               readonly=True)
    date = fields.Datetime('Date',
                           default=lambda *a:
                           time.strftime('%Y-%m-%d %H:%M:%S'),
                           readonly=True,
                           )
    state = fields.Selection([('pending', 'Pending'),
                              ('receive', 'Receive'),
                              ('cancel', 'Cancel')],
                             string='State', default='pending',
                             readonly=True,
                             )
    place_from = fields.Char('Place From',
                             readonly=True)
    full_name_address = fields.Char('Address',
                                    readonly=True)
    docket_no = fields.Char('Docket No.',
                            readonly=True)
    remark = fields.Text('Remark',
                         readonly=True)
    sender_name = fields.Char("Sender's Name Detail")
    letter_no = fields.Char("Letter No")
    letter_date = fields.Datetime("Letter Date")
    post_name = fields.Char("Name/Post")
    project_id = fields.Many2one("project.project", string="Project")
    from_name = fields.Text('From')
    to_name = fields.Text('To')

    @api.model
    def create(self, vals):
        """Create Method."""
        if vals.get('name') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'postman.courier') or 'New'
        result = super(PostmanCourier, self).create(vals)
        return result

    def courier_cancel(self):
        """Courier state set cancel."""
        for courier in self:
            courier.state = 'cancel'
        return True

    def courier_receive(self):
        """Courier state set receive."""
        for courier in self:
            courier.state = 'receive'
        return True

    def courier_pending(self):
        """Courier state set receive."""
        for courier in self:
            courier.state = 'pending'
        return True

    def unlink(self):
        if not self.user_has_groups('base.group_system'):
            for rec in self:
                if rec.state == 'receive':
                    raise ValidationError(_('''You can not delete Courier that is already received!'''))
        return super(PostmanCourier, self).unlink()

    @api.model
    def get_views(self, views, options=None):
        result = super(PostmanCourier, self).get_view(self, views, options)
        if self.user_has_groups('base.group_system'):
            if "form" in result['views']:
                doc = etree.XML(result['arch'])
                for field in result['fields']:
                    if field not in ['owner_id']:
                        for node in doc.xpath("//field[@name='%s']" % field):
                            node.set('modifiers', '{"readonly": false, "required": true}')
                result['arch'] = etree.tostring(doc)
        return result


class PostmanCourierOutward(models.Model):
    _name = 'postman.courier.outwards'
    _description = "Outwards Courier"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Serial No',
        copy=False,
        default='New'
    )

    summary = fields.Char('Summary',
                          readonly=True)
    active = fields.Boolean('Active', default=1)
    user_id = fields.Many2one('res.users', 'Collect By',
                              default=lambda self: self._uid,
                              readonly=True)
    owner_id = fields.Many2one('res.users', 'Senders Name Detail',
                               readonly=True, )
    department_id = fields.Many2one('hr.department', 'Department',
                                    readonly=True,
                                    )
    package_amount = fields.Float(string="Package Amount", readonly=True,
                                  )
    description = fields.Text('Description',
                              readonly=True)
    email_from = fields.Char('Email',
                             readonly=True)
    date_open = fields.Datetime('Opened', readonly=True,
                                )
    categ_id = fields.Many2one('postman.courier.type', 'Type of Indent',
                               readonly=True)
    date = fields.Datetime('Date',
                           default=lambda *a:
                           time.strftime('%Y-%m-%d %H:%M:%S'),
                           readonly=True,
                           )
    state = fields.Selection([('pending', 'Pending'),
                              ('receive', 'Receive'),
                              ('cancel', 'Cancel')],
                             string='State', default='pending',
                             readonly=True,
                             )
    place_from = fields.Char('Place',
                             readonly=True)
    full_name_address = fields.Char('Address',
                                    readonly=True)
    docket_no = fields.Char('Docket Number',
                            readonly=True)
    remark = fields.Text('Remark',
                         readonly=True)
    sender_name = fields.Char("Sender's Name Detail")
    letter_no = fields.Char("Letter No")
    letter_date = fields.Datetime("Letter Date")
    post_name = fields.Char("Name/Post")
    project_id = fields.Many2one("project.project", string="Project")
    from_name = fields.Text('From')
    to_name = fields.Text('To')

    @api.model
    def create(self, vals):
        """Create Method."""
        if vals.get('name') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('postman.courier.outword') or 'New'
        result = super(PostmanCourierOutward, self).create(vals)
        return result

    def courier_cancel(self):
        """Courier state set cancel."""
        for courier in self:
            courier.state = 'cancel'
        return True

    def courier_receive(self):
        """Courier state set receive."""
        for courier in self:
            courier.state = 'receive'
        return True

    def courier_pending(self):
        """Courier state set receive."""
        for courier in self:
            courier.state = 'pending'
        return True

    def unlink(self):
        for rec in self:
            if rec.state == 'receive':
                raise ValidationError(_('''You can not delete Courier that is already received!'''))
        return super(PostmanCourierOutward, self).unlink()

