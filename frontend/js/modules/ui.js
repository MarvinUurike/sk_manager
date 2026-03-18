import { state } from './state.js';

export const ui = {
    elements: {
        grid: document.getElementById('equipment-grid'),
        filters: document.querySelectorAll('.filter-btn'),
        search: document.getElementById('search-input'),
        modals: {
            equipment: document.getElementById('equipment-modal'),
            lend: document.getElementById('lend-modal'),
            details: document.getElementById('details-modal')
        }
    },

    renderGrid(onLend, onDetails) {
        this.elements.grid.innerHTML = '';
        const filteredData = state.getFilteredData();

        if (filteredData.length === 0) {
            this.elements.grid.innerHTML = '<div class="empty-state">No equipment found.</div>';
            return;
        }

        filteredData.forEach(item => {
            const total = parseInt(item.quantity);
            const item_id = item.id || item.equipment_id;
            const lent = state.getLentQuantity(item_id);
            const available = total - lent;
            
            let badgeClass, badgeText;
            if (available === total) {
                badgeClass = 'badge-available';
                badgeText = 'Fully Available';
            } else if (available === 0) {
                badgeClass = 'badge-out';
                badgeText = 'All Lent Out';
            } else {
                badgeClass = 'badge-lent';
                badgeText = `${available} Available`;
            }

            const photoHtml = item.photo_url 
                ? `<img src="${item.photo_url}" class="card-img" alt="${item.name}">`
                : `<div class="card-img-placeholder"><i class="ph ph-image"></i></div>`;

            const card = document.createElement('div');
            card.className = 'eq-card';
            card.innerHTML = `
                <div class="card-img-container">
                    ${photoHtml}
                    <span class="card-badge ${badgeClass}">${badgeText}</span>
                </div>
                <div class="card-body">
                    <h3 class="card-title">${item.name}</h3>
                    <div class="card-detail">
                        <i class="ph ph-map-pin"></i> ${item.location || 'No location set'}
                    </div>
                    <div class="card-detail">
                        <i class="ph ph-stack"></i> Total: ${total} | Lent: ${lent}
                    </div>
                    <div class="card-actions">
                        <button class="btn btn-primary btn-sm btn-action lend-btn" data-id="${item_id}" data-available="${available}">
                            Lend
                        </button>
                        <button class="btn btn-secondary btn-sm btn-action details-btn" data-id="${item_id}">
                            Details
                        </button>
                    </div>
                </div>
            `;
            
            // Add event listeners directly to avoid global scope pollution
            card.querySelector('.lend-btn').addEventListener('click', () => onLend(item_id, available));
            card.querySelector('.details-btn').addEventListener('click', () => onDetails(item_id));
            
            this.elements.grid.appendChild(card);
        });
    },

    showLoading() {
        this.elements.grid.innerHTML = '<div class="loading-spinner"><i class="ph ph-circle-notch ph-spin"></i> Loading...</div>';
    },

    showError(msg) {
        this.elements.grid.innerHTML = `<div class="error-msg">${msg}</div>`;
    },

    openModal(name) {
        this.elements.modals[name].classList.remove('hidden');
    },

    closeModal(name) {
        this.elements.modals[name].classList.add('hidden');
    }
};
