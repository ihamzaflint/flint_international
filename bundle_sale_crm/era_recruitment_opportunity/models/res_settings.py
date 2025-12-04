from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    flint_fee = fields.Float(string="Flint Fee", store=True, default=0,
                             config_parameter='era_recruitment_opportunity.flint_fee')
    annual_ticket_serv = fields.Float(string="Annual Ticket + SERV", store=True, default=0,
                                      config_parameter='era_recruitment_opportunity.annual_ticket_serv')

    misc = fields.Float(string="Miscellaneous", store=True, default=0,
                        config_parameter='era_recruitment_opportunity.misc')

    spouse_annual_ticket = fields.Float(string="Spouse Annual Ticket", store=True, default=0,
                                        config_parameter='era_recruitment_opportunity.spouse_annual_ticket')
    kid_annual_ticket = fields.Float(string="Kid Annual Ticket", store=True, default=0,
                                     config_parameter='era_recruitment_opportunity.kid_annual_ticket')

    iqama_fee = fields.Float(string="Annual Iqama Fee", store=True, default=0,
                             config_parameter='era_recruitment_opportunity.iqama_fee')
    iqama_transfer_fee = fields.Float(string="Annual Iqama Transfer", store=True, default=0,
                                      config_parameter='era_recruitment_opportunity.iqama_transfer_fee')
    iqama_transfer_fee = fields.Float(string="Annual Iqama Transfer", store=True, default=0,
                                      config_parameter='era_recruitment_opportunity.iqama_transfer_fee')
    saudi_eng_council = fields.Float(string="Saudi Engineering Council Fee", store=True, default=0,
                                     config_parameter='era_recruitment_opportunity.saudi_eng_council')
    hire_right_process = fields.Float(string="Hire Right Process", store=True, default=0,
                                      config_parameter='era_recruitment_opportunity.hire_right_process')
    visa_cost = fields.Float(string="Employee Visa Cost", store=True, default=0,
                             config_parameter='era_recruitment_opportunity.visa_cost')
    visa_endorsement = fields.Float(string="Employee Visa Endorsement", store=True, default=0,
                                    config_parameter='era_recruitment_opportunity.visa_endorsement')
    family_visa_cost = fields.Float(string="Family Visa Cost", store=True, default=0,
                                    config_parameter='era_recruitment_opportunity.family_visa_cost')
    family_visa_endorsement = fields.Float(string="Family Visa Endorsement", store=True, default=0,
                                           config_parameter='era_recruitment_opportunity.family_visa_endorsement')
    health_insurance_a = fields.Float(string="Annual Health Insurance Class A", store=True, default=0,
                                      config_parameter='era_recruitment_opportunity.health_insurance_a')
    health_insurance_a_plus = fields.Float(string="Annual Health Insurance Class A+", store=True, default=0,
                                           config_parameter='era_recruitment_opportunity.health_insurance_a_plus')
    health_insurance_b = fields.Float(string="Annual Health Insurance Class B", store=True, default=0,
                                      config_parameter='era_recruitment_opportunity.health_insurance_b')
    health_insurance_b_plus = fields.Float(string="Annual Health Insurance Class B+", store=True, default=0,
                                           config_parameter='era_recruitment_opportunity.health_insurance_b_plus')
    health_insurance_c = fields.Float(string="Annual Health Insurance Class C", store=True, default=0,
                                      config_parameter='era_recruitment_opportunity.health_insurance_c')
    health_insurance_c_plus = fields.Float(string="Annual Health Insurance Class C+", store=True, default=0,
                                           config_parameter='era_recruitment_opportunity.health_insurance_c_plus')

    spouse_health_insurance_a = fields.Float(string="Spouse Annual Health Insurance Class A", store=True, default=0,
                                             config_parameter='era_recruitment_opportunity.spouse_health_insurance_a')
    spouse_health_insurance_a_plus = fields.Float(string="Spouse Annual Health Insurance Class A+", store=True,
                                                  default=0,
                                                  config_parameter='era_recruitment_opportunity.spouse_health_insurance_a_plus')
    spouse_health_insurance_b = fields.Float(string="Spouse Annual Health Insurance Class B", store=True, default=0,
                                             config_parameter='era_recruitment_opportunity.spouse_health_insurance_b')
    spouse_health_insurance_b_plus = fields.Float(string="Spouse Annual Health Insurance Class B+", store=True,
                                                  default=0,
                                                  config_parameter='era_recruitment_opportunity.spouse_health_insurance_b_plus')
    spouse_health_insurance_c = fields.Float(string="Spouse Annual Health Insurance Class C", store=True, default=0,
                                             config_parameter='era_recruitment_opportunity.spouse_health_insurance_c')
    spouse_health_insurance_c_plus = fields.Float(string="Spouse Annual Health Insurance Class C+", store=True,
                                                  default=0,
                                                  config_parameter='era_recruitment_opportunity.spouse_health_insurance_c_plus')

    kids_health_insurance_a = fields.Float(string="Kids Annual Health Insurance Class A", store=True, default=0,
                                           config_parameter='era_recruitment_opportunity.kids_health_insurance_a')
    kids_health_insurance_a_plus = fields.Float(string="Kids Annual Health Insurance Class A+", store=True, default=0,
                                                config_parameter='era_recruitment_opportunity.kids_health_insurance_a_plus')
    kids_health_insurance_b = fields.Float(string="Kids Annual Health Insurance Class B", store=True, default=0,
                                           config_parameter='era_recruitment_opportunity.kids_health_insurance_b')
    kids_health_insurance_b_plus = fields.Float(string="Kids Annual Health Insurance Class B+", store=True, default=0,
                                                config_parameter='era_recruitment_opportunity.kids_health_insurance_b_plus')
    kids_health_insurance_c = fields.Float(string="Kids  Annual Health Insurance Class C", store=True, default=0,
                                           config_parameter='era_recruitment_opportunity.kids_health_insurance_c')
    kids_health_insurance_c_plus = fields.Float(string="Kids Annual Health Insurance Class C+", store=True, default=0,
                                                config_parameter='era_recruitment_opportunity.kids_health_insurance_c_plus')
