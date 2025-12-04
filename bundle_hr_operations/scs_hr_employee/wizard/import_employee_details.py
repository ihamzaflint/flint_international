# Copyright (C) 2021 Open Source Integrators
# (https://www.opensourceintegrators.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from datetime import datetime
import logging
import xlrd

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HrEmployeeImport(models.TransientModel):
    _name = "hr.employee.import"
    _description = "Employee Import"

    files = fields.Binary(string="Import Excel File")
    datas_fname = fields.Char("Import File Name")

    def get_date(self, date_value):
        date = False
        if isinstance(date_value, float) or isinstance(date_value, int):
            seconds = (date_value - 25569) * 86400.0
            date = datetime.utcfromtimestamp(seconds).date()
        elif isinstance(date_value, str) and date_value:
            date = datetime.strptime(date_value, "%d/%m/%Y").date()
        return date

    def import_file(self):
        try:
            workbook = xlrd.open_workbook(file_contents=base64.decodebytes(self.files))
        except TypeError:
            raise ValidationError(_("Please select .xls/xlsx file..."))
        sheet = workbook.sheet_by_index(0)
        header_dict = {}
        self = self.sudo()
        emp_obj = self.env["hr.employee"]
        client_type_obj = self.env["client.type"]
        client_obj = self.env["client.client"]
        project_obj = self.env["client.project"]
        profession_obj = self.env["employee.profession"]
        bank_obj = self.env["res.bank"]
        degree_obj = self.env["employee.degree"]
        job_obj = self.env["hr.job"]
        contract_history_obj = self.env["hr.contract.history"]
        contract_obj = self.env["hr.contract"]
        contract_type_obj = self.env["hr.contract.type"]
        country_obj = self.env["res.country"]
        analytic_obj = self.env["account.analytic.account"]
        type_obj = self.env["hr.payroll.structure.type"]
        sponsor_obj = self.env["hr.sponsor"]
        for row_no in range(sheet.nrows):
            if row_no <= 0:
                header_list = [x for x in sheet.row_values(row_no)]
                for header in header_list:
                    header_dict.update({header: header_list.index(header)})
                continue
            else:
                line = sheet.row_values(row_no)
                emp_id = emp_obj.search(
                    [
                        (
                            "registration_number",
                            "=",
                            str(line[header_dict.get("Flint EMP.ID", False)]).split(".")[0],
                        )
                    ],
                    limit=1,
                )

                _logger.info("\nEmployee Data: %s" % (line,))

                if not emp_id:
                    partner_id = self.env["res.partner"].create(
                        {"name": line[header_dict["Name"]]}
                    )
                    emp_id = emp_id.create(
                        {
                            "name": line[header_dict["Name"]],
                            "registration_number": str(
                                line[header_dict.get("Flint EMP.ID", False)]
                            ).split(".")[0],
                            "address_id": partner_id.id,
                        }
                    )

                if emp_id:
                    gender = ""
                    Marital = ""
                    education_level = ""
                    clinet_type = client_type_obj.search(
                        [("name", "=", line[header_dict.get("Client Type", 0)])],
                    )
                    if not clinet_type and line[header_dict.get("Client Type", 0)]:
                        clinet_type = clinet_type.create(
                            {"name": line[header_dict.get("Client Type", 0)]}
                        )

                    clinet_id = client_obj.search(
                        [("name", "=", line[header_dict.get("Client", 0)])]
                    )
                    if not clinet_id and line[header_dict.get("Client", 0)]:
                        clinet_id = clinet_id.create(
                            {"name": line[header_dict.get("Client", 0)]}
                        )

                    project_ids = project_obj.search(
                        [("name", "=", line[header_dict.get("Client Project ", 0)])]
                    )
                    if not project_ids and line[header_dict.get("Client Project ", 0)]:
                        project_ids = project_ids.create(
                            {"name": line[header_dict.get("Client Project ", 0)]}
                        )

                    country_id = country_obj.search(
                        [
                            (
                                "name",
                                "=",
                                line[
                                    header_dict.get(
                                        "Nationality (Country) In English", 0
                                    )
                                ],
                            )
                        ]
                    )

                    birth_country_id = country_obj.search([
                            ("name", '=', line[header_dict.get(
                                "Country of Birth", 0
                                )])
                        ])

                    profession_id = profession_obj.search(
                        [("name", "=", line[header_dict["Profession in Iqama"]])]
                    )
                    if not profession_id and line[header_dict["Profession in Iqama"]]:
                        profession_id = profession_id.create(
                            {"name": line[header_dict["Profession in Iqama"]]}
                        )
                    rel_user_id = self.env['res.users'].search(
                        [("name", "=", line[header_dict["Related User/Name"]])]
                    )
                    if not rel_user_id and line[header_dict["Related User/Name"]]:
                        rel_user_id = rel_user_id.create(
                            {"name": line[header_dict["Related User/Name"]]}
                        )

                    if line[header_dict["Gender"]] == "Male":
                        gender = "male"
                    elif line[header_dict["Gender"]] == "Female":
                        gender = "female"

                    if line[header_dict["Marital Status"]] == "Single":
                        Marital = "single"
                    elif line[header_dict["Marital Status"]] == "Married":
                        Marital = "married"
                    elif line[header_dict["Marital Status"]] == "Legal Cohabitant":
                        Marital = "cohabitant"
                    elif line[header_dict["Marital Status"]] == "Widower":
                        Marital = "widower"
                    elif line[header_dict["Marital Status"]] == "Divorced":
                        Marital = "divorced"

                    if line[header_dict["Education Level"]] == "Graduate":
                        education_level = "graduate"
                    elif line[header_dict["Education Level"]] == "Bachelor":
                        education_level = "bachelor"
                    elif line[header_dict["Education Level"]] == "Master":
                        education_level = "master"
                    elif line[header_dict["Education Level"]] == "Doctor":
                        education_level = "doctor"
                    elif line[header_dict["Education Level"]] == "Other":
                        education_level = "other"

                    degree_id = degree_obj.search(
                        [("name", "=", line[header_dict["Degree"]])]
                    )
                    if not degree_id and line[header_dict["Degree"]]:
                        degree_id = degree_obj.create(
                            {"name": line[header_dict["Degree"]]}
                        )

                    job_id = job_obj.search(
                        [
                            (
                                "name",
                                "=",
                                line[header_dict["Job Position in project"]],
                            )
                        ]
                    )
                    if not job_id and line[header_dict["Job Position in project"]]:
                        job_id = job_obj.create(
                            {"name": line[header_dict["Job Position in project"]]}
                        )

                    vals = {
                        "client_employee_id": str(
                            line[header_dict.get("Client Employee ID", 0)]
                        ).split(".")[0],
                        "client_type_id": clinet_type and clinet_type[0].id or False,
                        "client_id": clinet_id and clinet_id[0].id or False,
                        "project_id": project_ids and project_ids[0].id or False,
                        "name": line[header_dict.get("Name", 0)],
                        "muqeem_name": line[header_dict["Name As per Muqeem"]] or False,
                        "visa_no": str(line[header_dict["Iqama Number"]]).split(".")[0]
                        or False,
                        "muqeem_profession": line[
                            header_dict["Profession as per Muqeem in arabic"]
                        ]
                        or False,
                        "profession_id": profession_id and profession_id[0].id or False,
                        "user_id": rel_user_id and rel_user_id[0].id or False,
                        "birthday": self.get_date(line[header_dict["Date of Birth"]]),
                        "gender": gender or False,
                        "personal_email": line[header_dict["Personal Email"]] or False,
                        "work_phone": str(line[header_dict["Mobile"]]).split(".")[0]
                        or False,
                        "emp_degree_id": degree_id and degree_id[0].id or False,
                        "job_id": job_id and job_id[0].id or False,
                        "emergency_contact": str(
                            line[header_dict["Emergency Contact"]]
                        ).split(".")[0]
                        or False,
                        "children": line[header_dict["Number of Children"]] or 0,
                        "marital": Marital or False,
                        "date_of_entry": self.get_date(
                            line[header_dict["Date of Entry"]]
                        ),
                        "passport_id": str(line[header_dict["Passport No"]]).split(".")[
                            0
                        ]
                        or False,
                        "passport_expiry_date": self.get_date(
                            line[header_dict["Passport Expiry Date"]]
                        )
                        or False,
                        "visa_expire": self.get_date(
                            line[header_dict["Iqama Expiry Date"]]
                        )
                        or False,
                        "study_field": line[header_dict["Field of Study"]] or '',
                        "certificate": education_level or False,
                    }
                    if country_id:
                        vals.update(
                            {
                                "country_id": country_id and country_id[0].id or False,
                            }
                        )
                    if birth_country_id:
                        vals.update({
                            'country_of_birth': birth_country_id and birth_country_id[0].id or False,
                            })

                    contract_vals = {
                        "wage": line[header_dict["Basic Salary"]],
                        "l10n_sa_housing_allowance": float(
                            line[header_dict["Housing Allowance"]] or 0
                        ),
                        "l10n_sa_transportation_allowance": float(
                            line[header_dict["Transport Allowance"]] or 0
                        ),
                        "phone_allowance": float(
                            line[header_dict["Mobile Allowance"]] or 0
                        ),
                        "oc_rec_allowance": float(
                            line[header_dict["On Call Recurring"]] or 0
                        ),
                        "l10n_sa_other_allowances": float(
                            line[header_dict["Other Allowances"]] or 0
                        ),
                        "tech_allowance": float(
                            line[header_dict["Technical Allowance"]] or 0
                        ),
                        "tools_allowance": float(
                            line[header_dict["Laptop & Tools Allowance"]] or 0
                        ),
                        "car_allowance": float(line[header_dict["Car Allowance"]] or 0),
                        "tickets_allowance": float(
                            line[header_dict["Ticket Allowance"]] or 0
                        ),
                        "granted_monthly_bonus": float(
                            line[header_dict["Guaranteed Monthly Bonus"]] or 0
                        ),
                        "edu_allowance": float(
                            line[header_dict["Educational Allowance"]] or 0
                        ),
                        "niche_skill_allowance": float(
                            line[header_dict["Niche Skill Allowance"]] or 0
                        ),
                        "project_allowance": float(
                            line[header_dict["Project Allowance"]] or 0
                        ),
                        "special_allowance": float(
                            line[header_dict["Special Allowance"]] or 0
                        ),
                        "eos_payment_allowance": float(
                            line[header_dict["EOS Payment"]] or 0
                        ),
                        "eos_provision_accural_allowance": float(
                            line[header_dict["EOS Provision Accural"]] or 0
                        ),
                        "annual_leave_vacation_amount_allowance": float(
                            line[header_dict["Annual Leave Vacation Amount"]] or 0
                        ),
                        "gosi_comp_onbehalf": float(
                            line[header_dict["GOSI OnBehalf"]] or 0
                        ),
                        "kids_allowance": float(
                            line[header_dict["Kids Allowance"]] or 0
                        ),
                        "shift_allowance": float(
                            line[header_dict["Shift Allowance"]] or 0
                        ),
                        "gas_allowance": float(
                            line[header_dict["Gas Allowance"]] or 0
                        ),
                        "food_allowance": float(
                            line[header_dict["Food Allowance"]] or 0
                        ),

                        "date_start": self.get_date(
                            line[header_dict["Contract Start Date"]]
                        )
                        or False,
                        "date_end": self.get_date(
                            line[header_dict["Contract End Date"]]
                        )
                        or False,
                    }
                    analytic_id = analytic_obj.search(
                        [("name", "=", line[header_dict.get("Analytic Accounts", 0)])],
                        limit=1,
                    )

                    emp_id.write(vals)

                    if analytic_id:
                        contract_vals.update({"analytic_account_id": analytic_id.id})
                    if line[header_dict["Status"]]:
                        status = line[header_dict["Status"]]
                        if status == "Running":
                            contract_vals.update({"state": "open"})
                        elif status == "New":
                            contract_vals.update({"state": "draft"})
                        elif status == "Expired":
                            contract_vals.update({"state": "close"})
                        elif status == "Cancelled":
                            contract_vals.update({"state": "cancel"})
                    if line[header_dict["Salary Structure Type"]]:
                        type_id = type_obj.search(
                            [("name", "=", line[header_dict["Salary Structure Type"]])],
                            limit=1,
                        )
                        if type_id:
                            contract_vals.update({"structure_type_id": type_id.id})
                    emp_id.write(vals)

                    if (
                        line[header_dict["Sponsor Number"]]
                        or line[header_dict["Sponsor Name"]]
                    ):
                        sponsor_id = sponsor_obj.search(
                            [
                                "|",
                                ("code", "=", line[header_dict["Sponsor Number"]]),
                                ("name", "=", line[header_dict["Sponsor Name"]]),
                            ],
                            limit=1,
                        )
                        if not sponsor_id:
                            sponsor_id = sponsor_obj.create(
                                {
                                    "code": line[header_dict["Sponsor Number"]],
                                    "name": line[header_dict["Sponsor Name"]],
                                }
                            )
                        contract_vals.update({"sponsor_id": sponsor_id.id})

                    if emp_id.contract_id:
                        emp_id.contract_id.write(contract_vals)
                    else:
                        contract_id = contract_obj.search(
                            [("employee_id", "=", emp_id.id), ("state", "=", "draft")],
                            limit=1,
                        )
                        if status == "Running":
                            contract_vals.update({"state": "open"})
                        elif status == "New":
                            contract_vals.update({"state": "draft"})
                        elif status == "Expired":
                            contract_vals.update({"state": "close"})
                        elif status == "Cancelled":
                            contract_vals.update({"state": "cancel"})
                    if line[header_dict["Salary Structure Type"]]:
                        type_id = type_obj.search(
                            [("name", "=", line[header_dict["Salary Structure Type"]])],
                            limit=1,
                        )
                        if type_id:
                            contract_vals.update({"structure_type_id": type_id.id})

                    if emp_id.contract_id:
                        emp_id.contract_id.write(contract_vals)
                    else:
                        contract_id = contract_obj.search(
                            [("employee_id", "=", emp_id.id), ("state", "=", "draft")],
                            limit=1,
                        )
                        if contract_id:
                            contract_id.write(contract_vals)
                        else:
                            contract_vals.update(
                                {
                                    "name": emp_id.display_name,
                                    "employee_id": emp_id.id,
                                }
                            )
                            contract_obj.create(contract_vals)

                    bank_id = bank_obj.search(
                        [("name", "=", line[header_dict["Bank Name"]])], limit=1
                    )

                    if not bank_id and line[header_dict["Bank Name"]]:
                        bank_id = bank_id.create(
                            {"name": line[header_dict["Bank Name"]]}
                        )
                    bank_account_id = emp_id.bank_account_id.search(
                        [
                            (
                                "acc_number",
                                "=",
                                line[header_dict["Bank Account Number/IBAN Number"]],
                            )
                        ],
                        limit=1,
                    )
                    if emp_id.bank_account_id:
                        emp_id.bank_account_id.write(
                            {
                                "acc_number": line[
                                    header_dict["Bank Account Number/IBAN Number"]
                                ],
                                "bank_id": bank_id.id,
                            }
                        )
                    else:
                        if bank_account_id:
                            emp_id.bank_account_id = bank_account_id.id
                        else:
                            partner_id = self.env["res.partner"]
                            if not emp_id.address_id:
                                partner_id = self.env["res.partner"].search(
                                    [("name", "=", emp_id.name)], limit=1
                                )
                                if not partner_id:
                                    partner_id = self.env["res.partner"].create(
                                        {"name": line[header_dict["Name"]]}
                                    )
                            bank_id = emp_id.bank_account_id.create(
                                {
                                    "acc_number": line[
                                        header_dict["Bank Account Number/IBAN Number"]
                                    ],
                                    "bank_id": bank_id.id,
                                    "partner_id": emp_id.address_id.id
                                    or partner_id.id,
                                }
                            )

                            emp_id.write(
                                {
                                    "bank_account_id": bank_id.id,
                                    "address_id": emp_id.address_id.id
                                    or partner_id.id,
                                }
                            )
