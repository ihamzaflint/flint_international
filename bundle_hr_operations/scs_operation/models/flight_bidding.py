from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import datetime
import pytz
import uuid


class FlightBidding(models.Model):
    _name = 'flight.bidding'
    _description = 'Flight Bidding'

    name = fields.Char(string='Name', readonly=True, compute='_compute_name')
    number_of_tickets = fields.Integer(string='Number of Tickets')
    airline = fields.Char(string='Airline', required=True)
    number_of_baggage = fields.Integer(string='Number of Baggage', required=True)
    is_direct = fields.Boolean(string='Is Direct', default=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.company.currency_id)
    is_refundable = fields.Boolean(string='Is Refundable', default=True)
    price = fields.Float(string='Price', required=True)
    logistic_order_id = fields.Many2one('logistic.order', string='Logistic Order')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('reject', 'Rejected')
    ], string='Status', default='draft')
    flight_number = fields.Char(string='Flight Number')
    departure_time = fields.Datetime(string='Departure Time', required=True, tz='Asia/Riyadh')
    arrival_time = fields.Datetime(string='Arrival Time', required=True)
    confirmation_link = fields.Char(string='Confirmation Link', readonly=True)
    access_token = fields.Char(string='Access Token', readonly=True, copy=False)
    baggage_weight = fields.Float(string='Baggage', copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['access_token'] = str(uuid.uuid4())
        return super().create(vals_list)

    def _generate_confirmation_link(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/my/flight-bidding/confirm/{self.id}?access_token={self.access_token}"

    def action_confirm(self):
        for record in self:
            if record.price <= 0:
                raise ValidationError(_('You Can Not Confirm Bidding With Price Less Than Or Equal To Zero'))
            record.state = 'confirm'
            record.logistic_order_id.state = 'approval'
            # Generate confirmation link
            record.confirmation_link = record._generate_confirmation_link()
            # Send confirmation email
            template = self.env.ref('scs_operation.email_template_flight_bidding_confirmation')
            if template:
                template.send_mail(record.id, force_send=True)
        self.env['flight.bidding'].search([('logistic_order_id', '=', self.logistic_order_id.id)]).action_reject()
        return True

    def action_reject(self):
        for record in self:
            if record.price <= 0:
                raise ValidationError(_('You Can Not Confirm Bidding With Price Less Than Or Equal To Zero'))
            if record.state == 'draft':
                record.state = 'reject'
        return True

    @api.depends('logistic_order_id', 'logistic_order_id.employee_id', 'airline', 'flight_number')
    def _compute_name(self):
        for record in self:
            if record.logistic_order_id and record.airline and record.flight_number:
                record.name = (record.airline + ' # ' + record.flight_number +
                               ' / ' + record.logistic_order_id.employee_id.name or '')
            else:
                record.name = 'New'

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('You Can Not Delete Bidding while it is not in draft state,'
                                        ' try to cancel and reset the request to draft'))
        return super(FlightBidding, self).unlink()

    @api.constrains('departure_time', 'arrival_time', 'logistic_order_id')
    def _check_flight_times(self):
        for record in self:
            if not record.departure_time:
                raise ValidationError(_('Departure time must be set'))
            if not record.arrival_time:
                raise ValidationError(_('Arrival time must be set'))

            # Convert UTC times to user's timezone (Asia/Riyadh)
            user_tz = pytz.timezone(record.logistic_order_id.departure_airport_id.timezone)
            local_departure = pytz.utc.localize(record.departure_time).astimezone(user_tz)
            local_arrival = pytz.utc.localize(record.arrival_time).astimezone(user_tz)
            
            # Ensure arrival time is after departure time (comparing in local time)
            if local_arrival <= local_departure:
                raise ValidationError(_('Arrival time must be later than departure time'))
            
            # If logistic order has a departure date, validate against it
            if record.logistic_order_id and record.logistic_order_id.departure_date:
                logistic_departure_date = fields.Datetime.to_datetime(record.logistic_order_id.departure_date)
                local_logistic_departure = pytz.utc.localize(logistic_departure_date).astimezone(user_tz)
                
                if local_departure.date() < local_logistic_departure.date():
                    raise ValidationError(_('Flight departure time cannot be before the logistic order departure date'))
                
                # Check return date if it exists
                if record.logistic_order_id.return_date:
                    return_date = fields.Datetime.to_datetime(record.logistic_order_id.return_date)
                    local_return_date = pytz.utc.localize(return_date).astimezone(user_tz)
                    if local_arrival.date() > local_return_date.date():
                        raise ValidationError(_('Flight arrival time cannot be after the logistic order return date'))
