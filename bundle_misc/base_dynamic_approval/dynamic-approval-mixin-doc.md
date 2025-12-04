# DynamicApprovalMixin Documentation

## Overview

The `DynamicApprovalMixin` is an abstract model that provides advanced approval functionality for Odoo models. It allows for dynamic, multi-level approval processes with customizable workflows.

## Model Information

- **Name**: `dynamic.approval.mixin`
- **Description**: Advanced Approval Mixin

## Key Features

1. Multi-level approval process
2. Customizable approval workflows
3. Integration with Odoo's activity system
4. Email notifications for approvals and rejections
5. Support for attachments in approval requests
6. Configurable server actions at different approval stages

## Fields

| Field Name | Type | Description |
|------------|------|-------------|
| dynamic_approve_request_ids | One2many | Related approval requests |
| dynamic_approve_pending_group | Boolean | Computed field to check if current user is in a pending approval group |
| approve_requester_id | Many2one | User who initiated the approval request |
| dynamic_approval_id | Many2one | Related dynamic approval configuration |
| is_dynamic_approval_requester | Boolean | Computed field to check if current user is the approval requester |
| state_from_name | Char | Original state before approval process started |

## Methods

### Compute Methods

- `compute_is_dynamic_approval_requester()`: Determines if the current user is the approval requester
- `_compute_dynamic_approve_pending_group()`: Checks if the current user is in a pending approval group

### Notification Methods

- `_notify_next_approval_request(matched_approval, user)`: Notifies the next user in the approval chain
- `_create_approve_activity(user)`: Creates an activity for the approver
- `_create_done_approve_activity(user)`: Creates an activity when approval is complete
- `_create_reject_activity(user)`: Creates an activity when approval is rejected
- `_create_recall_activity(user)`: Creates an activity when approval is recalled

### Approval Process Methods

- `_action_final_approve()`: Executes final approval actions
- `_run_final_approve_function()`: Custom function to be overridden for final approval actions
- `_get_pending_approvals(user)`: Retrieves pending approvals for a user
- `_action_reset_original_state(reason, attachments, reset_type)`: Resets the record to its original state

### Main Action Methods

- `action_dynamic_approval_request()`: Initiates the approval process
- `action_under_approval(note)`: Processes an approval action

## Usage

To use the `DynamicApprovalMixin`, inherit it in your Odoo model:

```python
from odoo import models

class YourModel(models.Model):
    _name = 'your.model'
    _inherit = ['dynamic.approval.mixin']

    # Your model fields and methods
```

Customize the following attributes in your model:

- `_state_under_approval`: State to set when approval is requested
- `_state_to`: State to set when fully approved
- `_state_from`: List of states from which approval can be requested
- `_state_field`: Field name for the state
- `_company_field`: Field name for the company
- `_not_matched_action_xml_id`: Action to trigger if no matching approval is found
- `_reset_user`: Field to determine who can request approval again

## Workflow

1. User requests approval using `action_dynamic_approval_request()`
2. System checks for matching approval configuration
3. If found, creates approval requests and notifies first approver
4. Approvers use `action_under_approval()` to approve
5. System moves to next approval level or finalizes approval
6. Rejection or recall can be initiated using `_action_reset_original_state()`

## Notes

- Ensure proper configuration of Dynamic Approval settings in Odoo
- Customize email templates and server actions for notifications and automated processes
- Override methods as needed to add custom logic for your specific use case

