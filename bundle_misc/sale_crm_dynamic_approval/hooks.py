 # coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from os.path import join, dirname, realpath
from odoo import api, tools, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    module = 'sale_crm_dynamic_approval'
    # run _get_approval_validation_model_names method
    try:
        env['dynamic.approval']._get_approval_validation_model_names()
    except Exception as e:
        _logger.error(f"Error running _get_approval_validation_model_names method: {e}")