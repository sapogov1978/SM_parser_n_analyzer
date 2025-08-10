// Network management module
class NetworkManager {
    constructor() {
        this.modal = document.getElementById('editModal');
        this.init();
    }

    init() {
        // Set up modal event listeners
        this.setupModalEventListeners();
    }

    setupModalEventListeners() {
        // Close modal when clicking outside of it
        window.addEventListener('click', (event) => {
            if (event.target === this.modal) {
                this.closeEditModal();
            }
        });

        // Close modal when pressing Escape
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.modal.style.display === 'block') {
                this.closeEditModal();
            }
        });

        // Prevent closing when clicking on modal content
        const modalContent = this.modal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.addEventListener('click', (event) => {
                event.stopPropagation();
            });
        }
    }

    /**
     * Opens network edit modal
     * @param {number} networkId - Network ID
     */
    async openEditModal(networkId) {
        try {
            // Show loading indicator
            this.showLoading(true);

            const response = await fetch(`/networks/edit/${networkId}`);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
            }

            const data = await response.json();

            // Populate form with data
            this.populateForm(data);

            // Show modal
            this.modal.style.display = 'block';

            // Focus on first input field
            const firstInput = this.modal.querySelector('input[type="text"]');
            if (firstInput) {
                firstInput.focus();
                firstInput.select();
            }

        } catch (error) {
            console.error('Error loading network data:', error);
            this.showError(`Error loading network data: ${error.message}`);
            return false; // Return false to indicate failure
        } finally {
            this.showLoading(false);
        }

        return true; // Return true to indicate success
    }

    /**
     * Populates form with network data
     * @param {Object} data - Network data
     */
    populateForm(data) {
        const fields = {
            'edit_network_id': data.id,
            'edit_network_name': data.name,
            'edit_domain': data.domain
        };

        Object.entries(fields).forEach(([fieldId, value]) => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.value = value || '';
            }
        });
    }

    /**
     * Closes edit modal
     */
    closeEditModal() {
        this.modal.style.display = 'none';
        this.clearForm();
        this.closeAllDropdowns();
    }

    /**
     * Closes all open dropdown menus
     */
    closeAllDropdowns() {
        const allDetails = document.querySelectorAll('details[open]');
        allDetails.forEach(details => {
            details.removeAttribute('open');
        });
    }

    /**
     * Clears form data
     */
    clearForm() {
        const form = this.modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }

    /**
     * Shows/hides loading indicator
     * @param {boolean} show - Show or hide indicator
     */
    showLoading(show) {
        const submitButton = this.modal.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = show;
            submitButton.textContent = show ? 'Loading...' : 'Update Network';
        }
    }

    /**
     * Shows error message
     * @param {string} message - Error message text
     */
    showError(message) {
        // Can be replaced with a nicer notification system
        alert(message);
    }
}

// Initialize network manager after DOM is loaded
let networkManager;

document.addEventListener('DOMContentLoaded', () => {
    networkManager = new NetworkManager();
});

// Global functions for use in HTML
async function openEditModal(networkId) {
    if (networkManager) {
        try {
            await networkManager.openEditModal(networkId);
        } catch (error) {
            console.error('Failed to open edit modal:', error);
        }
    }
}

function closeEditModal() {
    if (networkManager) {
        networkManager.closeEditModal();
    }
}

// Export for possible use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NetworkManager };
}