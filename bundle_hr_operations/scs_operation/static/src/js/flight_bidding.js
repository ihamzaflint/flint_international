/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { Dialog } from "@web/core/dialog/dialog";

class ConfirmBidDialog extends Dialog {
    setup() {
        super.setup();
        this.title = "Confirm Bid Selection";
    }
}
ConfirmBidDialog.template = 'scs_operation.ConfirmBidDialog';
ConfirmBidDialog.components = { Dialog };

class FlightBidding extends Component {
    setup() {
        this.state = useState({
            showDialog: false,
            selectedBidUrl: '',
        });
    }

    async onBidClick(ev) {
        ev.preventDefault();
        const url = ev.currentTarget.getAttribute('href');
        this.state.selectedBidUrl = url;
        
        const confirmed = await this.env.services.dialog.add(ConfirmBidDialog, {
            body: "Are you sure you want to accept this flight offer? This action cannot be undone and will reject all other offers.",
            confirmLabel: "Accept Offer",
            cancelLabel: "Cancel",
        });
        
        if (confirmed) {
            window.location.href = this.state.selectedBidUrl;
        }
    }
}

FlightBidding.template = 'scs_operation.FlightBidding';
FlightBidding.props = {};

registry.category("public_components").add("flight_bidding", FlightBidding);
