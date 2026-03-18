import { API } from './modules/api.js';
import { state } from './modules/state.js';
import { ui } from './modules/ui.js';

// Initialization
async function initApp() {
    setupEventListeners();
    await refreshData();
}

async function refreshData() {
    try {
        ui.showLoading();
        const [eq, lends] = await Promise.all([
            API.getEquipment(),
            API.getActiveLendings()
        ]);
        
        state.setEquipment(eq);
        state.setLendings(lends);
        ui.renderGrid(handleLendClick, handleDetailsClick);
    } catch (err) {
        console.error("Initialization failed", err);
        ui.showError("Failed to load data. API might be offline.");
    }
}

// Handlers passed to UI
function handleLendClick(id, available) {
    const item = state.equipment.find(e => (e.id || e.equipment_id) === id);
    if (!item || available <= 0) return;

    document.getElementById('lend-equipment-id').value = id;
    document.getElementById('lend-eq-name').innerText = item.name;
    document.getElementById('lend-available-qty').innerText = `${available} available`;
    
    const qtyInput = document.getElementById('lend-quantity');
    qtyInput.max = available;
    qtyInput.value = 1;
    
    ui.openModal('lend');
}

async function handleDetailsClick(id) {
    const item = state.equipment.find(e => (e.id || e.equipment_id) === id);
    if (!item) return;

    const details = ui.elements.modals.details;
    details.querySelector('#details-title').innerText = item.name;
    details.querySelector('#details-location').innerText = item.location || 'N/A';
    details.querySelector('#details-quantity').innerText = item.quantity;
    
    const photoEl = details.querySelector('#details-photo');
    if (item.photo_url) {
        photoEl.src = item.photo_url;
        photoEl.style.display = 'block';
    } else {
        photoEl.style.display = 'none';
    }

    // Loans
    const loansList = details.querySelector('#current-loans-list');
    const itemLoans = state.lendings.filter(l => l.equipment_id === id);
    loansList.innerHTML = itemLoans.length ? '' : '<li>None currently lent out.</li>';
    
    itemLoans.forEach(loan => {
        const li = document.createElement('li');
        li.innerHTML = `
            <div>
                <strong>${loan.borrower}</strong> (${loan.quantity}x) <br>
                <small>Since ${new Date(loan.lent_date).toLocaleDateString()}</small>
            </div>
            <button class="return-btn" data-loan-id="${loan.lending_id}">Return</button>
        `;
        li.querySelector('.return-btn').addEventListener('click', () => handleReturn(id, loan.lending_id));
        loansList.appendChild(li);
    });

    // History
    const timeline = details.querySelector('#history-timeline');
    timeline.innerHTML = 'Loading...';
    ui.openModal('details');

    try {
        const history = await API.getHistory(id);
        timeline.innerHTML = history.length ? '' : 'No history yet.';
        history.forEach(h => {
            timeline.innerHTML += `
                <div class="timeline-item">
                    <small>${new Date(h.timestamp).toLocaleString()}</small>
                    <p>${h.action}: ${h.details || ''}</p>
                </div>
            `;
        });
    } catch (e) {
        timeline.innerHTML = 'Error loading history.';
    }
}

async function handleReturn(eqId, lendId) {
    if (!confirm("Confirm return?")) return;
    try {
        await API.returnItem(eqId, lendId);
        ui.closeModal('details');
        await refreshData();
    } catch (e) {
        alert(e.message);
    }
}

function setupEventListeners() {
    // Search & Filter
    ui.elements.search.addEventListener('input', (e) => {
        state.setSearchTerm(e.target.value);
        ui.renderGrid(handleLendClick, handleDetailsClick);
    });

    ui.elements.filters.forEach(btn => {
        btn.addEventListener('click', (e) => {
            ui.elements.filters.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.setFilter(btn.dataset.filter);
            ui.renderGrid(handleLendClick, handleDetailsClick);
        });
    });

    // Add Equipment
    document.getElementById('btn-add-equipment').addEventListener('click', () => {
        document.getElementById('equipment-form').reset();
        document.getElementById('equipment-id').value = '';
        ui.openModal('equipment');
    });

    document.getElementById('equipment-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('equipment-id').value;
        const data = {
            name: document.getElementById('eq-name').value,
            quantity: document.getElementById('eq-quantity').value,
            location: document.getElementById('eq-location').value
        };

        try {
            const saved = id ? await API.updateEquipment(id, data) : await API.createEquipment(data);
            const file = document.getElementById('equipment-photo').files[0];
            if (file) {
                const { upload_url } = await API.getPhotoUploadUrl(id || saved.equipment_id, file.type);
                await API.uploadPhotoToS3(upload_url, file);
            }
            ui.closeModal('equipment');
            await refreshData();
        } catch (err) {
            alert(err.message);
        }
    });

    // Lend Form
    document.getElementById('lend-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('lend-equipment-id').value;
        const borrower = document.getElementById('lend-borrower').value;
        const qty = document.getElementById('lend-quantity').value;
        try {
            await API.lendItem(id, borrower, qty);
            ui.closeModal('lend');
            await refreshData();
        } catch (err) {
            alert(err.message);
        }
    });

    // Generic Close
    document.querySelectorAll('.close-btn, #cancel-equipment, #cancel-lend').forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal');
            if (modal) modal.classList.add('hidden');
        });
    });
}

document.addEventListener('DOMContentLoaded', initApp);
