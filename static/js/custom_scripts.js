/* Global Custom Scripts for Table Actions */
/* Handles Modals, Sidebar Profiles, and Form Logic */

// --- 1. Modal / Sidebar Toggle ---
function toggleModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    // Check if it's a Sidebar (has .sidebar-panel)
    const panel = modal.querySelector('.sidebar-panel');

    if (panel) {
        // Sidebar Logic
        if (!modal.classList.contains('active')) {
            modal.style.display = 'flex';
            // Small timeout to allow display:flex to apply before transition
            setTimeout(() => {
                modal.classList.add('active');
            }, 10);
        } else {
            modal.classList.remove('active');
            // Wait for transition to finish before hiding
            setTimeout(() => {
                modal.style.display = 'none';
            }, 300);
        }
    } else {
        // Simple Modal Logic
        modal.classList.toggle('active');
    }
}


// --- 2. Customer Profile Logic (customers.html) ---
function openProfile(id) {
    toggleModal('profileSidebar');

    // Reset UI
    const nameEl = document.getElementById('profileName');
    const listEl = document.getElementById('measurementsList');
    if (nameEl) nameEl.innerText = "Loading...";
    if (listEl) listEl.innerHTML = '<p>Loading...</p>';

    // Fetch Data
    fetch('/api/customer/' + id)
        .then(response => response.json())
        .then(data => {
            if (document.getElementById('profileName')) {
                document.getElementById('profileName').innerText = data.name;
                document.getElementById('profileMobile').innerText = data.mobile + " (" + data.gender + ")";
                document.getElementById('profilePending').innerText = '₹' + data.total_pending;
                document.getElementById('profileOrdersCount').innerText = data.orders_count;
                document.getElementById('profileNewMeasBtn').href = "/customer/" + data.id + "/measurement";
            }

            // Render Measurements
            const list = document.getElementById('measurementsList');
            if (list) {
                list.innerHTML = '';
                if (data.measurements.length === 0) {
                    list.innerHTML = '<p>No measurements saved yet.</p>';
                } else {
                    data.measurements.forEach(m => {
                        const item = document.createElement('div');
                        item.className = 'card';
                        item.style.padding = '1rem';
                        item.style.border = '1px solid var(--border-color)';

                        // Parse JSON data for display format
                        let measText = '';
                        if (typeof m.data === 'object' && m.data !== null) {
                            measText += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">';
                            for (let [key, val] of Object.entries(m.data)) {
                                measText += `
                                    <div style="background: var(--bg-color); padding: 0.75rem; border-radius: 6px; border: 1px solid var(--border-color); text-align: center; display: flex; flex-direction: column; justify-content: center; height: 100%;">
                                        <div style="font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px;">${key}</div>
                                        <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary);">${val}</div>
                                    </div>
                                `;
                            }
                            measText += '</div>';
                        } else {
                            measText = `<div style="padding: 0.75rem; background: var(--bg-color); border-radius: 6px;">${JSON.stringify(m.data)}</div>`;
                        }

                        item.innerHTML = `
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem;">
                                <h5 style="font-weight: 600; font-size: 1.1rem; color: var(--primary-color); margin: 0;">
                                    <i class="fa-solid fa-scissors" style="margin-right: 0.5rem;"></i> ${m.category}
                                </h5>
                                <span style="font-size: 0.85rem; color: var(--text-secondary); background: var(--bg-color); padding: 4px 10px; border-radius: 12px; border: 1px solid var(--border-color);">${m.date}</span>
                            </div>
                            
                            <div style="margin-bottom: 1.2rem;">${measText}</div>
                            
                            ${m.remarks ? `
                                <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 1rem; background: #fff3cd; color: #856404; padding: 0.75rem; border-radius: 6px; border: 1px solid #ffeeba;">
                                    <i class="fa-solid fa-note-sticky" style="margin-right: 5px;"></i> ${m.remarks}
                                </div>` : ''}
                            
                            <div>
                                <button type="button" class="btn btn-primary" 
                                    onclick="window.location.href='/customer/${data.id}/measurement?reuse_id=${m.id}'" 
                                    style="width: 100%; justify-content: center; padding: 0.75rem; font-size: 1rem; font-weight: 500;">
                                    <i class="fa-solid fa-rotate-right" style="margin-right: 8px;"></i> Reuse for New Order
                                </button>
                            </div>
                        `;
                        list.appendChild(item);
                    });
                }
            }
        })
        .catch(err => {
            console.error(err);
            if (listEl) listEl.innerHTML = '<p style="color: red;">Error loading profile.</p>';
        });
}


// --- 3. Order Management Logic (orders.html) ---
function openManageModal(id, status, total, advance, mode, start, delivery, creator, customerName, itemsText) {
    if (!document.getElementById('manage_order_id')) return;

    document.getElementById('manage_order_id').value = id;
    document.getElementById('manage_status').value = status;
    document.getElementById('manage_total').value = total == 'None' ? 0 : total;
    document.getElementById('manage_advance').value = advance == 'None' ? 0 : advance;
    document.getElementById('manage_mode').value = mode == 'None' ? '' : mode;

    // Info Display (New)
    if (document.getElementById('manage_info_customer')) {
        document.getElementById('manage_info_customer').innerText = customerName || 'Unknown';
        document.getElementById('manage_info_items').innerText = itemsText || 'No items';
    }

    // Dates & Creator (Hidden or Readonly now per user request, but keeping values populated)
    const startDateEl = document.getElementById('manage_start_date');
    if (startDateEl) startDateEl.value = start == 'None' ? '' : start;

    document.getElementById('manage_delivery_date').value = delivery == 'None' ? '' : delivery;

    // Set Min Delivery Date to Today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('manage_delivery_date').min = today;

    updateBalanceDisplay();
    toggleModal('manageModal');
}

function addFullPayment() {
    const total = parseFloat(document.getElementById('manage_total').value) || 0;
    if (total > 0) {
        document.getElementById('manage_advance').value = total;
        updateBalanceDisplay();
    }
}

function updateBalanceDisplay() {
    const totalInput = document.getElementById('manage_total');
    const advanceInput = document.getElementById('manage_advance');
    const balSpan = document.getElementById('calc_balance');

    if (!totalInput || !advanceInput || !balSpan) return;

    const total = parseFloat(totalInput.value) || 0;
    const advance = parseFloat(advanceInput.value) || 0;
    const bal = total - advance;

    balSpan.innerText = '₹' + bal;

    if (bal <= 0 && total > 0) {
        balSpan.style.color = 'var(--success-color)';
        balSpan.innerText += ' (Paid)';
    } else if (total == 0 && advance > 0) {
        balSpan.style.color = 'var(--success-color)';
        balSpan.innerText += ' (Credit)';
    } else {
        balSpan.style.color = 'var(--danger-color)';
    }
}


// --- 4. Bill Payment Logic (bills.html) ---
function openPaymentModal(id, total, advance, status, mode, start, delivery, creator) {
    if (!document.getElementById('pay_order_id')) return;

    document.getElementById('pay_order_id').value = id;
    document.getElementById('pay_total').value = total;
    document.getElementById('pay_advance').value = advance;
    document.getElementById('pay_status').value = status;
    document.getElementById('pay_mode').value = mode == 'None' ? '' : mode;

    // New Fields
    document.getElementById('pay_start_date').value = start == 'None' ? '' : start;
    document.getElementById('pay_delivery_date').value = delivery == 'None' ? '' : delivery;
    document.getElementById('pay_created_by').value = creator == 'None' ? 'Unknown' : creator;

    // Set Min Delivery Date
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('pay_delivery_date').min = today;

    toggleModal('paymentModal');
}

function filterBills(status) {
    const rows = document.querySelectorAll('.bill-row');
    rows.forEach(row => {
        const rowStatus = row.getAttribute('data-status');
        if (status === 'all' || rowStatus === status) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}


// --- 5. Event Delegation for Inputs (Persist through AJAX) ---
document.addEventListener('input', (e) => {
    // Orders Balance Calculation
    if (e.target.id === 'manage_total' || e.target.id === 'manage_advance') {
        updateBalanceDisplay();
    }

    // Bills Auto Status Update
    if (e.target.id === 'pay_advance') {
        const total = parseFloat(document.getElementById('pay_total').value) || 0;
        const paid = parseFloat(e.target.value) || 0;
        const statusSelect = document.getElementById('pay_status');

        if (statusSelect) {
            if (paid >= total && total > 0) {
                statusSelect.value = 'Paid';
            } else if (paid > 0) {
                statusSelect.value = 'Half-Payment';
            } else {
                statusSelect.value = 'Pending';
            }
        }
    }
});
