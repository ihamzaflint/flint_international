/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useInputField } from "@web/views/fields/input_field_hook";
import { Component, onMounted, useRef } from "@odoo/owl";

/* [sanjay-techvoot] Lightweight component to edit PEM keys in a monospace textarea.
   Provides a small, reusable OWL field for storing multi-line key text. */
export class PemKeyField extends Component {
    /* [sanjay-techvoot] Initialize textarea ref and input binding.
       Applies simple styling (monospace, min height, full width) on mount. */
    setup() {
        this.textareaRef = useRef("textarea");
        useInputField({ getValue: () => this.props.value || "" });
        
        onMounted(() => {
            if (this.textareaRef.el) {
                this.textareaRef.el.style.fontFamily = "monospace";
                this.textareaRef.el.style.minHeight = "150px";
                this.textareaRef.el.style.width = "100%";
            }
        });
    }

    /* [sanjay-techvoot] Return the current value (or empty string) for display.
       Keeps accessor tiny and predictable for templates and bindings. */
    get formattedValue() {
        return this.props.value || "";
    }
}

PemKeyField.template = "saib_bank_integration.PemKeyField";
PemKeyField.props = {
    ...standardFieldProps,
    placeholder: { type: String, optional: true },
};

registry.category("fields").add("pem_key", PemKeyField);
