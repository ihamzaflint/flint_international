from odoo import api, fields, models
from datetime import timedelta

class RenewalContractWizard(models.TransientModel):
    _inherit = 'renewal.contract.wizard'
    

    def create_new_contract(self):
        date_start = self.start_date
        date_end = self.end_date
        if not self.contract_id.date_end:
            self.contract_id.date_end = self.start_date + timedelta(days=-1)
        else:
            date_start = self.contract_id.date_end + timedelta(days=+1)
        valuable_benefit_ids = self.contract_id.valuable_benefit_ids
        non_valuable_benefit_ids = self.contract_id.non_valuable_benefit_ids
        valuable_benefit = []
        non_valuable_benefit = []
        for line in valuable_benefit_ids:
            valuable_benefit.append(
                (0, 0, {'benefit_id': line.benefit_id.id, 'benefit_value': line.benefit_value}))
        for line in non_valuable_benefit_ids:
            non_valuable_benefit.append(
                (0, 0, {'benefit_id': line.benefit_id.id, 'benefit_value': line.benefit_value}))
        new_contract_id = self.contract_id.copy(
            {'date_start': date_start, 'date_end': date_end, 'trial_start_date': False, 'trial_end_date': False,
             'trial_period_no': 0, 'non_valuable_benefit_ids': non_valuable_benefit,
             'valuable_benefit_ids': valuable_benefit})
        self.contract_id.next_contract_id = new_contract_id.id

        