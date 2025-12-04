/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { FloatField } from "@web/views/fields/float/float_field";
import { patch } from "@web/core/utils/patch";

patch(FloatField.prototype, {
    setup() {
        super.setup();
    },
    
    isValid() {
        let isValid = true;
        if (this.props.type === 'integer' || this.props.type === 'float' || this.props.type === 'monetary') {
            if (this.props.value < 0 && this.props.record.fields[this.props.name].block_negative) {
                isValid = false;
            }
            if (this.props.value === 0 && this.props.record.fields[this.props.name].prevent_zero) {
                isValid = false;
            }
        }
        else if (this.props.type === 'char' && this.props.value !== '' && this.props.record.fields[this.props.name].email) {
            const mailformat = /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/;
            if (!(mailformat.test(String(this.props.value).toLowerCase()))) {
                isValid = false;
            }
        }
        return isValid;
    },
});