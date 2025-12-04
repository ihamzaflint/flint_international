from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def run_update_currency(self):
        """
        Placeholder method to prevent errors when currency_rate_live module is not installed.
        This method is called from a cron job defined in the currency_rate_live module.
        
        When the currency_rate_live module is installed, this method will be overridden
        with the actual implementation.
        """
        _logger.info("Currency rate update requested but currency_rate_live module is not installed.")
        _logger.info("To enable automatic currency updates, install the currency_rate_live module.")
        return True
