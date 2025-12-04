from dateutil.relativedelta import relativedelta
from odoo import _, models, fields, api
from odoo.exceptions import UserError
import base64


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def get_iqama_expiry_emp(self):
        employee_ids = self.search(
            [
                ("visa_expire", ">=", fields.Date.today()),
                ("visa_expire", "<=", fields.Date.today() + relativedelta(months=+3)),
            ],
            order="visa_expire",
        )
        if not employee_ids:
            raise UserError(_("No Employee Found"))

        return self.env.ref(
            "scs_hr_payroll.action_report_empl_iqama_exp"
        ).report_action(employee_ids)

    @api.model
    def _cron_iqama_contract_notify(self):
        employee_ids = self.search(
            [
                ("visa_expire", ">=", fields.Date.today()),
                ("visa_expire", "<=", fields.Date.today() + relativedelta(days=60)),
            ],
            order="visa_expire",
        )

        contract_ids = self.env["hr.contract"].search(
            [
                ("date_end", ">=", fields.Date.today()),
                ("date_end", "<=", fields.Date.today() + relativedelta(days=75)),
            ],
            order="date_end",
        )

        iqama_template = self.env.ref("scs_hr_payroll.email_template_employee_expiry")
        contract_template = self.env.ref(
            "scs_hr_payroll.email_template_employee_contract"
        )
        iqama_report = self.env.ref("scs_hr_payroll.action_report_empl_iqama_exp")
        contract_report = self.env.ref(
            "scs_hr_payroll.report_action_report_contract_expiry"
        )
        analytic_account_id_id = self.contract_id.analytic_account_id

        new_attachments = []
        emp_ids = employee_ids.filtered(
            lambda l: l.contract_id.analytic_account_id.id == analytic_account_id_id.id
        )
        if emp_ids:
                qr_pdf = iqama_report._render_qweb_pdf(emp_ids.ids)[0]
                qr_pdf = base64.b64encode(qr_pdf)
                new_attachments.append(("Iqama Expiry Details - %s.pdf" % analytic_account_id_id.name, qr_pdf))
                email_to = ",".join(
                    e.login
                    for e in analytic_account_id_id.sds_ids.filtered(lambda l: l.login)
                )
                if email_to:
                    iqama_template.send_mail(
                        emp_ids[0].id,
                        force_send=True,
                        email_values={
                            "attachments": new_attachments,
                            "email_to": email_to,
                            'subject': "Employee Iqama Expiry Details: %s" % self.name,
                        },
                    )

        analytic_account_id_id = self.contract_id.analytic_account_id
        new_attachments = []
        if analytic_account_id_id:
            qr_pdf = contract_report._render_qweb_pdf(analytic_account_id_id.id)
            qr_pdf = base64.b64encode(qr_pdf[0])  
            new_attachments.append(("Contract Expiry Details - %s.pdf" % self.name, qr_pdf))
            email_to = ",".join(
                e.login
                for e in analytic_account_id_id.sds_ids.filtered(lambda l: l.login)
            )
            if email_to:
                contract_template.send_mail(
                    self.id,
                    force_send=True,
                    email_values={
                        "attachments": new_attachments,
                        "email_to": email_to,
                        'subject': "Employee Contract Expiry Details: %s" % analytic_account_id_id.name,
                    },
                )


class AnalyticAccounts(models.Model):
    _inherit = "account.analytic.account"

    sds_ids = fields.Many2many(
        "res.users",
        string="SDE",
    )
