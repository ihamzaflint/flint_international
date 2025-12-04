from odoo import models, fields, api
from odoo.exceptions import ValidationError
# from odoo.addons.hijri_date_util import itq_date_util as ddd
# from odoo.addons.hijri_date_util import itq_date_util as ddd
# from odoo.addons.hijri_date_util import itq_date_util as ddd
from . import itq_date_util as ddd
from datetime import datetime
from datetime import date



class TestScreen(models.Model):
    _name='test.date.screen'

    name=fields.Char('test')
    date_to_operate=fields.Date('Date')
    year=fields.Integer('Year')
    month=fields.Integer('Month')
    day=fields.Integer('Day')
    operation=fields.Selection([('add','Add'),('sub','Subtract')],'Operation')
    operation_result=fields.Date('Result')


    date_diff_one=fields.Date('Date Difference 1')
    date_diff_two=fields.Date('Date Difference 2')
    year_diff=fields.Integer('Year')
    month_diff=fields.Integer('Month')
    day_diff=fields.Integer('Day')


    cron_date=fields.Date(string='CRON DATE')

    @api.onchange('date_diff_one','date_diff_two')
    def get_date_diff(self):
        for rec in self:
            if not rec.date_diff_one or not rec.date_diff_two:
                return
            d1=datetime.strptime(rec.date_diff_one, "%Y-%m-%d").date()
            d2=datetime.strptime(rec.date_diff_two, "%Y-%m-%d").date()

            if d2>=d1:
                rec.year_diff,rec.month_diff,rec.day_diff=ddd.hijri_date_diff(d1,d2)
            else:
                rec.year_diff, rec.month_diff, rec.day_diff = ddd.hijri_date_diff(d2, d1)
    def check_numbers(self,lst, num):
        lst2 = []
        for l in lst:
            if num == 0:
                lst2.append(l)
            elif num > l:
                num = num - l
                lst2.append(0)
            else:
                lst2.append(l - num)
                num = 0
        return lst2,num

    @api.one
    def cron_test_year(self):
        current_day = datetime.strptime(self.cron_date, "%Y-%m-%d").date()

        leave_configurations = self.env['itq.leave.configuration'].search(
            [('balance_age', '>', 0), ('balance_frame', '=', 'year')])
        print('configuration are', leave_configurations)
        for config in leave_configurations:
            print('config is', config.name)
            duration = config.duration
            required_date = ddd.sub_duration(current_day, 0, duration, 0)
            allocation_dates = self.env['itq.last.allocation.date'].search(
                [('leave_type', '=', config.holiday_type_id.id), (
                    'last_allocation_date', '=', required_date)])
            print('alloc', allocation_dates)
            # leave_infos=allocation_dates.mapped('emp_info_id')
            for alloc in allocation_dates:
                leave_info = alloc.emp_info_id
                total_leave_days = sum(self.env['hr.holidays'].search([('employee_id', '=', leave_info.emp_id.id),
                                                                       ('holiday_status_id', '=', alloc.leave_type.id),
                                                                       ('date_from_full', '>=', required_date),
                                                                       ('date_to_full', '<', current_day)]).mapped(
                    'number_of_days'))
                duration_limit = config.leave_limit
                print('total days',total_leave_days)
                balance_age = self.env['itq.balance.age.info'].search([('leave_type', '=', alloc.leave_type.id),
                                                                       ('emp_info_id', '=', leave_info.id)], limit=1)
                alloc.last_allocation_date = current_day
                if not balance_age:
                    continue
                print('balance age is', balance_age)
                ages = []
                for x in range(1, config.balance_age + 1):
                    print(x)
                    ages.append(balance_age.get_var(x))
                ages.reverse()
                ages.append(duration_limit)
                print('ages', ages)
                ages, total_leave_days = self.check_numbers(ages, total_leave_days)
                ages = ages[1:]
                ages.reverse()
                print('ages', ages)
                for x in range(1, config.balance_age+1):
                    print(x)
                    balance_age.set_var(x, ages[x - 1])



    @api.one
    def cron_test(self):
        current_day = datetime.strptime(self.cron_date, "%Y-%m-%d").date()

        leave_configurations = self.env['itq.leave.configuration'].search([('balance_age', '>', 0),('balance_frame','in',['assigning','year'])])
        for config in leave_configurations:
            duration = config.duration
            required_date=ddd.sub_duration(current_day,0,duration,0)
            frame_end=ddd.sub_duration(current_day,0,0,1)
            allocation_dates=self.env['itq.last.allocation.date'].search([('leave_type','=',config.holiday_type_id.id),(
                                                          'last_allocation_date','=',required_date)])
            # leave_infos=allocation_dates.mapped('emp_info_id')
            for alloc in allocation_dates:
                leave_info = alloc.emp_info_id
                total_leaves=self.env['hr.holidays'].search([('employee_id','=',leave_info.emp_id.id),
                                                               ('holiday_status_id','=',alloc.leave_type.id),
                                                             '|', '&', ('date_from_full', '>=', required_date),
                                                             ('date_from_full', '<=', current_day), '&',
                                                             ('date_to_full', '<=', current_day),
                                                             ('date_to_full', '>=', required_date)],
                                                            order='date_from_full')
                total_leave_days=0
                for leave in total_leaves:
                    date_from=datetime.strptime(leave.date_from_full, "%Y-%m-%d").date()
                    date_to=datetime.strptime(leave.date_to_full, "%Y-%m-%d").date()
                    if date_from<required_date:
                        total_leave_days+=self.env[
                    'hr.holidays']._compute_requested_leave_duration(leave_info.emp_id, config.holiday_type_id,
                                                                     str(required_date),
                                                                     str(leave.date_to_full))
                    else:
                        if date_to>=current_day:
                            total_leave_days += self.env[
                                'hr.holidays']._compute_requested_leave_duration(leave_info.emp_id,
                                                                                 config.holiday_type_id,
                                                                                 str(leave.date_from_full),
                                                                                 str(frame_end))
                        else:
                            total_leave_days+=leave.number_of_days
                duration_limit=0
                if config.balance_frame=='year' and config.accumulation:
                    assign_date = datetime.strptime(leave_info.emp_id.assigning_date, "%Y-%m-%d").date()

                    if assign_date>=required_date and assign_date<=frame_end:
                        duration_limit = int(ddd.get_work_ratio(required_date, frame_end,
                                                                    assign_date,
                                                                    frame_end) * config.leave_limit)
                    else:
                        duration_limit = config.leave_limit
                else:
                    duration_limit = config.leave_limit

                balance_age=self.env['itq.balance.age.info'].search([('leave_type','=',alloc.leave_type.id),
                                                                     ('emp_info_id','=',leave_info.id)],limit=1)
                alloc.last_allocation_date=current_day
                if not balance_age:
                    continue
                ages=[]
                for x in range(1,config.balance_age+1):
                    ages.append(balance_age.get_var(x))
                ages.reverse()
                ages.append(duration_limit)
                ages,total_leave_days=self.check_numbers(ages,total_leave_days)
                ages=ages[1:]
                ages.reverse()
                for x in range(1,config.balance_age+1):
                    print(x)
                    balance_age.set_var(x,ages[x-1])

                # while total_leave_days>0:

    def operate_test(self):
        for rec in self:
            if not rec.date_to_operate or not rec.operation:
                raise ValidationError('Please enter all data')
            print('type is',type(rec.date_to_operate))

            da=datetime.strptime(rec.date_to_operate, "%Y-%m-%d").date()
            if rec.operation=='add':
                rec.operation_result=ddd.add_duration(da,rec.year,rec.month,rec.day)
                print(rec.operation_result,'add')
            if rec.operation=='sub':
                rec.operation_result=ddd.sub_duration(da,rec.year,rec.month,rec.day)
                print(rec.operation_result,'sub')





