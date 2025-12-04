/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useState } from "@odoo/owl";

console.log('[DEBUG] Loading helpdesk_portal.js module');

export class HelpdeskPortalForm extends Component {
    setup() {
        console.log('[DEBUG] HelpdeskPortalForm setup called');
        this.state = useState({
            serviceTypes: [],
            selectedTypes: [],
            searchText: "",
            dropdownVisible: false,
            isValid: true,
            filteredTypes: [],
            ticketTypeId: null
        });

        this.elements = {};

        onMounted(() => {
            console.log('[DEBUG] Component mounted');
            this.initializeForm();
            document.addEventListener('click', this.handleClickOutside.bind(this));
        });

        onWillUnmount(() => {
            console.log('[DEBUG] Component will unmount');
            this.cleanup();
            document.removeEventListener('click', this.handleClickOutside.bind(this));
        });
    }

    initializeForm() {
        console.log('[DEBUG] Initializing form...');
        const form = document.querySelector('form[action="/helpdesk/ticket/submit"]');
        console.log('[DEBUG] Form found:', form);
        if (!form) {
            console.error('[DEBUG] Form not found');
            return;
        }

        this.setupTicketTypeListener();
        this.setupFormElements(form);
    }

    setupTicketTypeListener() {
        // Store the select element as a class property
        this.ticketTypeSelect = document.querySelector('select[name="ticket_type_id"]');
        console.log('[DEBUG] Setting up ticket type listener. Found select:', this.ticketTypeSelect);

        if (this.ticketTypeSelect) {
            // Bind the event handler to this instance
            this.boundTicketTypeChange = this.onTicketTypeChange.bind(this);
            this.ticketTypeSelect.addEventListener('change', this.boundTicketTypeChange);
            
            // If there's an initial value, trigger the change
            if (this.ticketTypeSelect.value) {
                console.log('[DEBUG] Initial ticket type value:', this.ticketTypeSelect.value);
                this.loadServiceTypes(this.ticketTypeSelect.value);
            }
        } else {
            console.error('[DEBUG] Ticket type select not found in the DOM');
        }
    }

    async loadServiceTypes(ticketTypeId) {
        console.log('[DEBUG] Loading service types for ticket type:', ticketTypeId);
        
        if (!ticketTypeId) {
            console.log('[DEBUG] No ticket type ID provided, clearing service types');
            this.state.serviceTypes = [];
            this.state.filteredTypes = [];
            return;
        }

        try {
            const response = await fetch(`/helpdesk/get_service_types/${ticketTypeId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const serviceTypes = await response.json();
            console.log('[DEBUG] Retrieved service types:', serviceTypes);
            
            this.state.serviceTypes = serviceTypes;
            this.filterServiceTypes();
            
        } catch (error) {
            console.error('[DEBUG] Error loading service types:', error);
            this.state.serviceTypes = [];
            this.state.filteredTypes = [];
        }
    }

    onTicketTypeChange(event) {
        console.log('[DEBUG] Ticket type change event triggered:', event);
        const ticketTypeId = event.target.value;
        console.log('[DEBUG] Selected ticket type ID:', ticketTypeId);
        this.loadServiceTypes(ticketTypeId);
    }

    setupFormElements(form) {
        console.log('[DEBUG] Setting up form elements...');
        
        // Tags Input Setup
        const tagsInput = form.querySelector('.o_tags_input');
        console.log('[DEBUG] Tags input container:', tagsInput);
        if (!tagsInput) {
            console.error('[DEBUG] Tags input container not found');
            return;
        }

        const tagsSearch = tagsInput.querySelector('.o_tags_search');
        console.log('[DEBUG] Tags search input:', tagsSearch);
        if (!tagsSearch) {
            console.error('[DEBUG] Tags search input not found');
            return;
        }

        const tagsDropdown = form.querySelector('.o_tags_dropdown');
        console.log('[DEBUG] Tags dropdown:', tagsDropdown);
        if (!tagsDropdown) {
            console.error('[DEBUG] Tags dropdown not found');
            return;
        }

        const tagsSection = tagsInput.querySelector('.o_tags_section');
        console.log('[DEBUG] Tags section:', tagsSection);
        if (!tagsSection) {
            console.error('[DEBUG] Tags section not found');
            return;
        }

        const hiddenSelect = form.querySelector('select[name="service_type_ids"]');
        console.log('[DEBUG] Hidden select:', hiddenSelect);
        if (!hiddenSelect) {
            console.error('[DEBUG] Hidden select not found');
            return;
        }

        console.log('[DEBUG] All elements found successfully');

        // Store references
        this.elements = {
            input: tagsSearch,
            dropdown: tagsDropdown,
            section: tagsSection,
            select: hiddenSelect,
            container: tagsInput,
            form: form
        };

        // Setup event listeners
        this.setupEventListeners();

        this.initializeServiceTypes();
    }

    setupEventListeners() {
        console.log('[DEBUG] Setting up event listeners');
        
        this.elements.input.addEventListener('input', this.updateSearch.bind(this));
        this.elements.input.addEventListener('focus', this.showDropdown.bind(this));
        this.elements.container.addEventListener('click', this.showDropdown.bind(this));
        this.elements.form.addEventListener('submit', this.onSubmit.bind(this));
    }

    cleanup() {
        // Remove event listeners
        if (this.elements.input) {
            this.elements.input.removeEventListener('input', this.updateSearch.bind(this));
            this.elements.input.removeEventListener('focus', this.showDropdown.bind(this));
        }
        if (this.elements.container) {
            this.elements.container.removeEventListener('click', this.showDropdown.bind(this));
        }
        if (this.elements.form) {
            this.elements.form.removeEventListener('submit', this.onSubmit.bind(this));
        }
        if (this.ticketTypeSelect) {
            this.ticketTypeSelect.removeEventListener('change', this.boundTicketTypeChange);
        }
    }

    async initializeServiceTypes() {
        try {
            const response = await fetch('/helpdesk/service_types', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) throw new Error('Failed to fetch service types');
            
            const data = await response.json();
            this.state.serviceTypes = data;
            this.filterServiceTypes();
        } catch (error) {
            console.error('Error loading service types:', error);
        }
    }

    filterServiceTypes() {
        const searchTerm = this.state.searchText.toLowerCase().trim();
        this.state.filteredTypes = this.state.serviceTypes.filter(type => 
            !this.state.selectedTypes.includes(type) &&
            type.name.toLowerCase().includes(searchTerm)
        );
        console.log('[DEBUG] Filtered service types:', this.state.filteredTypes);
    }

    updateSearch(ev) {
        this.state.searchText = ev.target.value;
        this.filterServiceTypes();
        this.state.dropdownVisible = true;
    }

    addType(type) {
        if (!this.state.selectedTypes.includes(type)) {
            this.state.selectedTypes.push(type);
            this.state.searchText = "";
            this.filterServiceTypes();
            this.updateHiddenInput();
            console.log('[DEBUG] Added service type:', type);
        }
    }

    removeType(type) {
        this.state.selectedTypes = this.state.selectedTypes.filter(t => t.id !== type.id);
        this.filterServiceTypes();
        this.updateHiddenInput();
        console.log('[DEBUG] Removed service type:', type);
    }

    updateHiddenInput() {
        const hiddenSelect = document.querySelector('select[name="service_type_ids"]');
        if (hiddenSelect) {
            // Clear existing options
            while (hiddenSelect.firstChild) {
                hiddenSelect.removeChild(hiddenSelect.firstChild);
            }

            // Add selected options
            this.state.selectedTypes.forEach(type => {
                const option = document.createElement('option');
                option.value = type.id;
                option.selected = true;
                option.textContent = type.name;
                hiddenSelect.appendChild(option);
            });
            
            console.log('[DEBUG] Updated hidden input with selected types:', this.state.selectedTypes);
        }
    }

    handleClickOutside(event) {
        const dropdown = document.querySelector('.o_tags_dropdown');
        const input = document.querySelector('.o_tags_search');
        
        if (dropdown && input && 
            !dropdown.contains(event.target) && 
            !input.contains(event.target)) {
            this.state.dropdownVisible = false;
        }
    }

    showDropdown() {
        this.state.dropdownVisible = true;
        this.filterServiceTypes();
    }

    onSubmit(e) {
        console.log('[DEBUG] Form submit');
        if (!this.validateForm()) {
            e.preventDefault();
        }
    }

    validateForm() {
        this.state.isValid = this.state.selectedTypes.length > 0;
        return this.state.isValid;
    }
}

console.log('[DEBUG] HelpdeskPortalForm class defined');
HelpdeskPortalForm.template = 'flint_helpdesk_portal.HelpdeskPortalForm';
