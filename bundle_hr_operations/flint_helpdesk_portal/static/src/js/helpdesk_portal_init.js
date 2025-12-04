/** @odoo-module **/

import { mount } from "@odoo/owl";
import { HelpdeskPortalForm } from "./helpdesk_portal";
import { registry } from "@web/core/registry";

console.log('[DEBUG] Loading helpdesk_portal_init.js');

// Function to create and mount component
function createServiceTypeSelector(env, target) {
    console.log('[DEBUG] Creating service type selector');
    
    // Find the target location
    const form = document.querySelector('form[action="/helpdesk/ticket/submit"]');
    if (!form) {
        console.warn('[DEBUG] Form not found');
        return;
    }

    // Find the insertion point (after ticket type selection)
    const ticketTypeSelect = form.querySelector('select[name="ticket_type_id"]');
    if (!ticketTypeSelect) {
        console.warn('[DEBUG] Ticket type select not found');
        return;
    }

    // Create container if it doesn't exist
    let container = form.querySelector('.service-types-container');
    if (!container) {
        console.log('[DEBUG] Creating container element');
        container = document.createElement('div');
        container.className = 'service-types-container form-group mb-3';
        
        // Insert after the ticket type's parent div
        const targetElement = ticketTypeSelect.closest('.form-group');
        if (targetElement && targetElement.parentNode) {
            targetElement.parentNode.insertBefore(container, targetElement.nextSibling);
            console.log('[DEBUG] Container inserted into DOM');
        }
    }

    console.log('[DEBUG] Attempting to mount component');
    mount(HelpdeskPortalForm, container, {
        props: {
            name: 'service_type_ids'
        }
    }).then(() => {
        console.log('[DEBUG] Component mounted successfully');
    }).catch(error => {
        console.error('[DEBUG] Error mounting component:', error);
    });
}

// Register the frontend component
registry.category("public_components").add("helpdesk_portal_form", {
    selector: 'form[action="/helpdesk/ticket/submit"]',
    async start(env, target) {
        console.log('[DEBUG] Public component starting');
        createServiceTypeSelector(env, target);
    },
});
