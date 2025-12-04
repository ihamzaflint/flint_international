/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { DatePickerHijri } from "@hijri_date_util/datepicker_hijri/datepicker_hijri";
import { areDateEquals } from "@web/core/l10n/dates";
import { _lt } from "@web/core/l10n/translation";


class DateFieldHijri extends Component {
    static props = {
        ...standardFieldProps,
        pickerOptions: { type: Object, optional: true },
        placeholder: { type: String, optional: true },
    };
    static defaultProps = {
        pickerOptions: {},
    };
    setup() {
        this.lastSetValue = null;
        this.revId = 0;
    }
    get isDateTime() {
        return this.props.record.fields[this.props.name].type === "datetime";
    }
    get date() {
        return this.props.value && this.props.value.startOf("day");
    }

    get formattedValue() {
        // return this.isDateTime
        //     ? formatDateTime(this.props.value, { format: localization.dateFormat })
        //     : formatDate(this.props.value);
        return this.props.value;
    }

    onDateTimeChanged(date) {
        if (!areDateEquals(this.date || "", date)) {
            this.revId++;
            this.props.update(date);
        }
    }
    onDatePickerInput(ev) {
        this.props.setDirty(ev.target.value !== this.lastSetValue);
    }
    onUpdateInput(date) {
        this.props.setDirty(false);
        this.lastSetValue = date;
    }
}

DateFieldHijri.template = "hijri_date_util.DateFieldHijri";
DateFieldHijri.components = {
    DatePickerHijri,
};
DateFieldHijri.props = {
    ...standardFieldProps,
    pickerOptions: { type: Object, optional: true },
    placeholder: { type: String, optional: true },
};
DateFieldHijri.defaultProps = {
    pickerOptions: {},
};

DateFieldHijri.displayName = _lt("Date");
DateFieldHijri.supportedTypes = ["date"];

DateFieldHijri.extractProps = ({ attrs }) => {
    return {
        pickerOptions: attrs.options.DatePickerHijri,
        placeholder: attrs.placeholder,
    };
};

registry.category("fields").add("hijri", DateFieldHijri);
