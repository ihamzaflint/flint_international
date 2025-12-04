from typing import Set, Dict, List, Union
from odoo import models, fields
from odoo.exceptions import AccessError


class IrAttachmentCheck(models.Model):
    _inherit = 'ir.attachment'

    public = fields.Boolean('Is public document', default=True)

    def check(self, mode: str, values: dict = None) -> None:
        """
        Check access rights for attachments

        Args:
            mode: Access mode to check ('read', 'write', 'create', 'unlink')
            values: Optional values dictionary for new attachments
        """
        res_ids: Dict[str, Set[int]] = {}

        if self.ids:
            # Convert single ID to list if necessary
            ids = [self.ids] if isinstance(self.ids, int) else self.ids

            self.env.cr.execute('''
                SELECT DISTINCT res_model, res_id, create_uid 
                FROM ir_attachment 
                WHERE id = ANY (%s)
            ''', (ids,))

            for rmod, rid, create_uid in self.env.cr.fetchall():
                if not (rmod and rid):
                    continue
                res_ids.setdefault(rmod, set()).add(rid)

        # Check values for new attachments
        if values and values.get('res_model') and values.get('res_id'):
            res_ids.setdefault(values['res_model'], set()).add(values['res_id'])

        # Check access rights for each model
        for model, mids in res_ids.items():
            model_obj = self.env.get(model)

            # Skip if model doesn't exist anymore
            if not model_obj:
                continue

            # Filter existing records
            existing_records = model_obj.browse(list(mids)).exists()
            existing_ids = existing_records.ids

            # Check model access rights
            self.env['ir.model.access'].check(model, mode)

            # Check record rules
            if existing_ids:
                model_obj.check_access_rights(mode)
                model_obj.check_access_rule(mode)