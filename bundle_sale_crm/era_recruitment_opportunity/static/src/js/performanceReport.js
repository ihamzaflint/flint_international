/** @odoo-module */
const { Component } = owl;
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";
import { BlockUI } from "@web/core/ui/block_ui";
const actionRegistry = registry.category("actions");
import { uiService } from "@web/core/ui/ui_service";
//  Extending components for adding purchase report class
class PerformanceReport extends Component {
   async setup() {
       super.setup(...arguments);
       this.uiService = useService('ui');
       this.initial_render = true;
       this.orm = useService('orm');
       this.action = useService('action');
       this.start_date = useRef('date_from');
       this.end_date = useRef('date_to');
//       this.order_by = useRef('order_by');
       this.state = useState({
           order_line: [],
           data: null,
//           order_by : 'report_by_order',
           wizard_id : [],
           start_date: "",
           end_date: ""
       });
       this.load_data();
       }
       async load_data(wizard_id = null) {
       /**
        * Loads the data for the purchase report.
        */
       let move_lines = ''
       try {
           if(wizard_id == null){
               this.state.wizard_id = await this.orm.create("applicant.line",[{}]);
               }
           this.state.data = await this.orm.call("applicant.line", "recruitment_performance_report", [this.state.wizard_id]);
           $.each(this.state.data, function (index, value) {
               move_lines = value
           })
           this.state.order_line = move_lines
       }
       catch (el) {
           window.location.href
       }
   }
   async onDateChange(ev) {
        if (ev.target.name === "date_from") {
            this.state.start_date = ev.target.value
        } else if (ev.target.name === "date_to") {
            this.state.end_date = ev.target.value
        }
    }
   async applyFilter(ev) {
       let filter_data = {}
//       this.state.order_by = this.order_by.el.value
       filter_data.date_from = this.start_date.el.value
       filter_data.date_to = this.end_date.el.value
//       filter_data.report_type = this.order_by.el.value
       let data = await this.orm.write("applicant.line",this.state.wizard_id, filter_data);
       this.load_data(this.state.wizard_id)
   }
   viewCandidate(ev){
   return this.action.doAction({
           type: "ir.actions.act_window",
           res_model: 'applicant.line',
           res_id: parseInt(ev.target.id),
           views: [[false, "form"]],
           target: "current",
       });
   }
     async print_xlsx() {
       /**
        * Generates and downloads an XLSX report for the purchase orders.
        */
       var data = this.state.data
       var action = {
               'data': {
                  'model': 'applicant.line',
                  'options': JSON.stringify(data['orders']),
                  'output_format': 'xlsx',
                  'report_data': JSON.stringify(data['report_lines']),
                  'report_name': 'Performance Report',
                  'dfr_data': JSON.stringify(data),
               },
            };
       this.uiService.block();
       download({
           url: '/performance_dynamic_xlsx_reports',
           data: action.data,
           complete: this.uiService.unblock(),
           error: (error) => this.call('crash_manager', 'rpc_error', error),
         });
         }
     async printPdf(ev) {
       /**
        * Generates and displays a PDF report for the purchase orders.
        *
        * @param {Event} ev - The event object triggered by the action.
        * @returns {Promise} - A promise that resolves to the result of the action.
        */

       ev.preventDefault();
       var self = this;
       var action_title = self.props.action.display_name;
       return this.env.services.action.doAction({
           'type': 'ir.actions.report',
           'report_type': 'qweb-pdf',
           'report_name': 'era_recruitment_opportunity.performance_report_pdf',
           'report_file': 'era_recruitment_opportunity.performance_report_pdf',
           'data': {
               'report_data': this.state.data['report_lines']
           },
           'context': {
                  'date_from' : this.state.data['orders']['date_from'],
                  'date_to' : this.state.data['orders']['date_to'],
               },
         'display_name': 'Purchase Order',
       });
   }
   }
PerformanceReport.template = 'PerformanceReport';
actionRegistry.add("recruitment_performance_report", PerformanceReport);