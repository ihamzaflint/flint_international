/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.ApplicantBidding = publicWidget.Widget.extend({
    selector: '.container',
    events: {
        'click button.btn-success:not(.disabled)': '_onConfirmBidding',
        'click button.btn-danger:not(.disabled)': '_onRejectBidding',
    },

    /**
     * Initialize the widget and ensure it only binds events once.
     */
    start: function () {
        // Ensure the widget is only initialized once for the given selector
        if (this.$el.data('widget-initialized')) {
            return Promise.resolve();
        }
        this.$el.data('widget-initialized', true);
        return this._super.apply(this, arguments);
    },

    /**
     * Handle Confirm button click.
     */
    async _onConfirmBidding(ev) {
        ev.preventDefault(); // Prevent default action
        ev.stopPropagation(); // Stop event bubbling

        const $button = $(ev.currentTarget);
        $button.addClass('disabled'); // Disable button to prevent multiple clicks

        const biddingId = $button.data('bidding-id');
        const accessToken = $button.data('access-token');

        if (!confirm('Are you sure you want to confirm this Applicant bidding?')) {
            $button.removeClass('disabled'); // Re-enable button if user cancels
            return;
        }

        try {
            const result = await jsonrpc(`/my/applicant-bidding/confirm/${biddingId}`, {
                access_token: accessToken,
            });
            console.log("Confirm response:", result);
            if (result.status === 'success') {
                $button.closest('.card-body').html('<span class="badge bg-success">Confirmed</span>');
            } else {
                alert(result.error || "Something went wrong");
                $button.removeClass('disabled'); // Re-enable button on error
            }
        } catch (err) {
            console.error(err);
            alert("Server error");
            $button.removeClass('disabled'); // Re-enable button on error
        }
    },

    /**
     * Handle Reject button click.
     */
    async _onRejectBidding(ev) {
        ev.preventDefault(); // Prevent default action
        ev.stopPropagation(); // Stop event bubbling

        const $button = $(ev.currentTarget);
        $button.addClass('disabled'); // Disable button to prevent multiple clicks

        const biddingId = $button.data('bidding-id');
        const accessToken = $button.data('access-token');

        if (!confirm('Are you sure you want to reject this Applicant bidding?')) {
            $button.removeClass('disabled'); // Re-enable button if user cancels
            return;
        }

        try {
            const result = await jsonrpc(`/my/applicant-bidding/reject/${biddingId}`, {
                access_token: accessToken,
            });
            console.log("Reject response:", result);
            if (result.status === 'success') {
                $button.closest('.card-body').html('<span class="badge bg-danger">Rejected</span>');
            } else {
                alert(result.error || "Something went wrong");
                $button.removeClass('disabled'); // Re-enable button on error
            }
        } catch (err) {
            console.error(err);
            alert("Server error");
            $button.removeClass('disabled'); // Re-enable button on error
        }
    },
});

