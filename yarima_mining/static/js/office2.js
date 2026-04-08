
class TransactionManager {
  constructor() {
    this.currentPage = 1;
    this.pageSize = 10;
    this.currentBatchId = null;
    this.csrfToken = this.getCookie('csrftoken');
    this.transactionCache = {};
    this.init();
  }

  init() {
    this.bindEvents();
    this.loadTransactions();
  }

  bindEvents() {
    document.getElementById('applyFilters')?.addEventListener('click', () => {
      this.currentPage = 1;
      this.loadTransactions();
    });

    document.getElementById('clearFilters')?.addEventListener('click', () => {
      this.clearFilters();
    });

    document.getElementById('refreshData')?.addEventListener('click', () => {
      this.loadTransactions();
    });

    document.getElementById('addPaymentRow')?.addEventListener('click', () => {
      this.addPaymentRow();
    });

    document.getElementById('paymentsTableBody')?.addEventListener('click', (e) => {
      const removeBtn = e.target.closest('.remove-payment');
      if (removeBtn) this.removePaymentRow(removeBtn);
    });

    document.getElementById('confirmApproval')?.addEventListener('click', () => {
      this.approveBatch();
    });

    document.getElementById('confirmPayment')?.addEventListener('click', () => {
      this.submitPayment();
    });

    const tableBody = document.getElementById('transactionTableBody');
    if (tableBody) {
      tableBody.addEventListener('click', (e) => {
        const previewBtn = e.target.closest('.preview-btn');
        if (previewBtn) {
          this.previewBatch(previewBtn.dataset.batchId);
          return;
        }

        const approveBtn = e.target.closest('.approve-btn');
        if (approveBtn) {
          this.showApprovalModal(approveBtn.dataset.batchId);
          return;
        }

        const markPaidBtn = e.target.closest('.mark-paid-btn');
        if (markPaidBtn) {
          this.markAsPaid(markPaidBtn.dataset.batchId);
          return;
        }

        const deleteBtn = e.target.closest('.delete-btn');
        if (deleteBtn) {
          this.deleteBatch(deleteBtn.dataset.batchId);
        }
      });
    }

    document.getElementById('pagination')?.addEventListener('click', (e) => {
      const pageLink = e.target.closest('[data-page]');
      if (pageLink) {
        e.preventDefault();
        this.currentPage = parseInt(pageLink.dataset.page);
        this.loadTransactions();
      }
    });
  }

  getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  showLoading() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
      spinner.classList.remove('d-none');
      spinner.style.display = 'block';
    }
    const table = document.getElementById('transactionTable');
    if (table) table.style.opacity = '0.6';
  }

  hideLoading() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
      spinner.classList.add('d-none');
      spinner.style.display = 'none';
    }
    const table = document.getElementById('transactionTable');
    if (table) table.style.opacity = '1';
  }

  showError(message) {
    console.error('Error:', message);
    window.showToast?.(message, 'error');
  }

  showSuccess(message) {
    window.showToast?.(message, 'success');
  }

  clearFilters() {
    document.getElementById('searchId').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('dateFrom').value = '';
    document.getElementById('dateTo').value = '';
    this.currentPage = 1;
    this.loadTransactions();
  }

  getFilters() {
    return {
      search_id: document.getElementById('searchId').value.trim(),
      status: document.getElementById('statusFilter').value,
      date_from: document.getElementById('dateFrom').value,
      date_to: document.getElementById('dateTo').value,
      page: this.currentPage,
      page_size: this.pageSize
    };
  }

  async loadTransactions() {
    this.showLoading();
    try {
      const filters = this.getFilters();
      const queryString = new URLSearchParams(filters).toString();
      const url = '/office2/transactions/?' + queryString;

      const response = await fetch(url, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        }
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      if (data.success) {
        this.renderTransactions(data.data);
        this.renderPagination(data.pagination);
        this.updateTotalCount(data.pagination.total);
      } else {
        throw new Error(data.error || 'Failed to load transactions');
      }
    } catch (error) {
      console.error('Load error:', error);
      this.showError('Failed to load batches.');
      this.showEmptyState();
    } finally {
      this.hideLoading();
    }
  }

  renderTransactions(batches) {
    const tbody = document.getElementById('transactionTableBody');
    const emptyState = document.getElementById('emptyState');

    if (!batches || batches.length === 0) {
      this.showEmptyState();
      return;
    }

    emptyState.classList.add('d-none');
    emptyState.style.display = 'none';

    tbody.innerHTML = batches.map(b => this.createBatchRow(b)).join('');
  }

  createBatchRow(b) {
    const statusBadge = this.getStatusBadge(b.status);
    const actionButtons = this.getActionButtons(b);
    return `
      <tr>
        <td><strong>#${b.batch_no}</strong></td>
        <td>${b.items[0]?.mineral_type || 'Multiple'}</td>
        <td>${b.supplier_name}</td>
        <td>
          ${b.total_weight_kg > 0 ? `<strong>${b.total_weight_kg}kg</strong>` : ''}
          ${b.total_weight_lb > 0 ? (b.total_weight_kg > 0 ? ' / ' : '') + `<strong>${b.total_weight_lb}lb</strong>` : ''}
        </td>
        <td><strong class="text-success">₦${this.formatCurrency(b.total_value)}</strong></td>
        <td>${this.formatDate(b.date_received)}</td>
        <td>${statusBadge}</td>
        <td>${actionButtons}</td>
      </tr>
    `;
  }

  getStatusBadge(status) {
    const badges = {
      pending: '<span class="badge bg-warning text-dark">Pending</span>',
      approved: '<span class="badge bg-success">Approved</span>',
      paid: '<span class="badge bg-primary">Paid</span>',
      rejected: '<span class="badge bg-danger">Rejected</span>'
    };
    return badges[status] || '<span class="badge bg-secondary">Unknown</span>';
  }

  getActionButtons(batch) {
    let buttons = `
      <button class="btn btn-outline-primary btn-sm me-1 preview-btn" 
              data-batch-id="${batch.id}" title="View Details">
        <i class="fas fa-eye"></i>
      </button>
    `;
    if (batch.status === 'pending') {
      buttons += `
        <button class="btn btn-primary btn-sm me-1 approve-btn" 
                data-batch-id="${batch.id}" title="Approve">
          <i class="fas fa-check"></i>
        </button>
      `;
    }
    if (batch.status === 'approved') {
      buttons += `
        <button class="btn btn-success btn-sm mark-paid-btn" 
                data-batch-id="${batch.id}" title="Mark as Paid">
          <i class="fas fa-dollar-sign"></i>
        </button>
      `;
    }
    if (batch.can_delete) {
      buttons += `
        <button class="btn btn-outline-danger btn-sm delete-btn"
                data-batch-id="${batch.id}" title="Delete">
          <i class="fas fa-trash"></i>
        </button>
      `;
    }
    return `<div class="btn-group btn-group-sm">${buttons}</div>`;
  }

  async previewBatch(id) {
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    const modalContent = document.getElementById('modalContent');
    const modalFooter = document.getElementById('modalFooter');

    modalContent.innerHTML = `
      <div class="text-center py-4">
        <div class="spinner-border text-primary" role="status"></div>
        <p class="text-white mt-2">Loading batch details...</p>
      </div>
    `;
    modal.show();

    try {
      const response = await fetch(`/office2/transactions/api/${id}/`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      const data = await response.json();

      if (data.success) {
        this.renderBatchDetails(data.data, modalContent, modalFooter);
        this.currentBatchId = id;
        this.transactionCache[id] = data.data;
      } else {
        throw new Error();
      }
    } catch (error) {
      modalContent.innerHTML = `
        <div class="alert alert-danger text-center">
          <i class="fas fa-exclamation-circle me-2"></i>
          Failed to load batch details.
        </div>
      `;
      this.showError('Could not load batch.');
    }
  }

  renderBatchDetails(b, modalContent, modalFooter) {
    modalContent.innerHTML = `
      <div class="row">
        <div class="col-md-6">
          <h6 class="text-primary border-bottom pb-2 mb-3">
            <i class="fas fa-gem me-2"></i>Batch Info
          </h6>
          <table class="table table-dark table-sm">
            <tr><td>ID:</td><td><strong>#${b.batch_no}</strong></td></tr>
            <tr><td>Items:</td><td><strong>${b.items_count}</strong></td></tr>
            <tr><td>Total Value:</td><td><strong class="text-success">₦${this.formatCurrency(b.total_value)}</strong></td></tr>
            <tr><td>Weight (kg):</td><td>${b.total_weight_kg || '0'} kg</td></tr>
            <tr><td>Weight (lb):</td><td>${b.total_weight_lb || '0'} lb</td></tr>
          </table>
        </div>
        <div class="col-md-6">
          <h6 class="text-primary border-bottom pb-2 mb-3">
            <i class="fas fa-user me-2"></i>Supplier & Status
          </h6>
          <table class="table table-dark table-sm">
            <tr><td>Supplier:</td><td>${b.supplier_name}</td></tr>
            <tr><td>Phone:</td><td>${b.supplier_phone || 'Not Provided'}</td></tr>
            <tr><td>Received:</td><td>${this.formatDate(b.date_received)}</td></tr>
            <tr><td>Status:</td><td>${this.getStatusBadge(b.status)}</td></tr>
            <tr><td>Recorded By:</td><td>${b.recorded_by}</td></tr>
            ${b.approved_by ? `<tr><td>Approved By:</td><td>${b.approved_by}</td></tr>` : ''}
            ${b.paid_by ? `<tr><td>Paid By:</td><td>${b.paid_by}</td></tr>` : ''}
            ${b.paid_at ? `<tr><td>Paid At:</td><td>${this.formatDate(b.paid_at)}</td></tr>` : ''}
          </table>
        </div>
      </div>
      ${b.items?.length ? `
  <div class="mt-4">
    <h6 class="text-primary border-bottom pb-2 mb-3">
      <i class="fas fa-list me-2"></i>Items
    </h6>
    <div class="table-responsive">
      <table class="table table-dark table-sm">
        <thead><tr><th>Mineral</th><th>Grade</th><th>Weight</th><th>Value</th></tr></thead>
        <tbody>
          ${b.items.map(i => `
            <tr>
              <td>${i.mineral_type}</td>
              <td>${i.grade}</td>
              <td>${i.weight} ${i.weight_unit}</td>
              <td>₦${this.formatCurrency(i.total_value)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  </div>
` : ''}

${b.payment_components?.length ? `
  <div class="mt-4">
    <h6 class="text-primary border-bottom pb-2 mb-3">
      <i class="fas fa-money-bill-wave me-2"></i>Payment Details
    </h6>
    <div class="table-responsive">
      <table class="table table-dark table-sm">
        <thead>
          <tr>
            <th>Method</th>
            <th>Amount</th>
            <th>Account</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          ${b.payment_components.map(p => `
            <tr>
              <td>${p.method_display}</td>
              <td>₦${this.formatCurrency(p.amount)}</td>
              <td>${p.payout_account_number || '–'}</td>
              <td>${this.formatDate(p.recorded_at)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  </div>
` : ''}
    `;

    const closeBtn = `
      <button type="button" class="btn btn-outline-primary" data-bs-dismiss="modal">
        <i class="fas fa-times me-2"></i>Close
      </button>
    `;
    modalFooter.innerHTML = closeBtn;

    if (b.status === 'pending') {
      modalFooter.innerHTML += `
        <button type="button" class="btn btn-primary open-approval-btn">
          <i class="fas fa-check me-2"></i>Approve Batch
        </button>
      `;
      modalFooter.querySelector('.open-approval-btn').addEventListener('click', () => {
        this.showApprovalModal(b.id);
      });
    }
  }

  showApprovalModal(id) {
    this.currentBatchId = id;
    const previewModal = bootstrap.Modal.getInstance(document.getElementById('previewModal'));
    if (previewModal) previewModal.hide();

    const modal = new bootstrap.Modal(document.getElementById('approvalModal'));
    const tbody = document.getElementById('paymentsTableBody');
    tbody.innerHTML = '';
    this.addPaymentRow(); // One empty row
    document.getElementById('approvalReference').value = '';
    modal.show();
  }

  addPaymentRow() {
    const tbody = document.getElementById('paymentsTableBody');
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>
        <select class="form-select form-select-sm payment-method">
          <option style="background-color: #000; color: #fff" value="">Select Method</option>
          <option style="background-color: #000; color: #fff" value="cash">Cash</option>
          <option style="background-color: #000; color: #fff" value="opay">OPay</option>
          <option style="background-color: #000; color: #fff" value="moniepoint">Moniepoint</option>
          <option style="background-color: #000; color: #fff" value="palmpay">PalmPay</option>
          <option style="background-color: #000; color: #fff" value="kuda">Kuda</option>
          <option style="background-color: #000; color: #fff" value="flutterwave">Flutterwave</option>
          <option style="background-color: #000; color: #fff" value="paystack">Paystack</option>
          <option style="background-color: #000; color: #fff" value="other_fintech">Other Fintech</option>
          <option style="background-color: #000; color: #fff" value="access_bank">Access Bank</option>
          <option style="background-color: #000; color: #fff" value="gtbank">GTBank</option>
          <option style="background-color: #000; color: #fff" value="zenith_bank">Zenith Bank</option>
          <option style="background-color: #000; color: #fff" value="first_bank">First Bank</option>
          <option style="background-color: #000; color: #fff" value="uba">UBA</option>
          <option style="background-color: #000; color: #fff" value="fcmb">FCMB</option>
          <option style="background-color: #000; color: #fff" value="fidelity_bank">Fidelity Bank</option>
          <option style="background-color: #000; color: #fff" value="union_bank">Union Bank</option>
          <option style="background-color: #000; color: #fff" value="sterling_bank">Sterling Bank</option>
          <option style="background-color: #000; color: #fff" value="wema_bank">Wema Bank</option>
          <option style="background-color: #000; color: #fff" value="keystone_bank">Keystone Bank</option>
          <option style="background-color: #000; color: #fff" value="polaris_bank">Polaris Bank</option>
          <option style="background-color: #000; color: #fff" value="other_bank">Other Bank</option>
        </select>
      </td>
      <td>
        <input type="number" step="0.01" min="0" class="form-control form-control-sm payment-amount" placeholder="0.00">
      </td>
      <td>
        <input type="text" class="form-control form-control-sm payment-account" placeholder="Wallet or Account No.">
      </td>
      <td>
        <button type="button" class="btn btn-sm btn-outline-danger remove-payment">
          <i class="fas fa-trash"></i>
        </button>
      </td>
    `;
    tbody.appendChild(row);
  }

  removePaymentRow(btn) {
    const tbody = document.getElementById('paymentsTableBody');
    if (tbody.children.length > 1) {
      btn.closest('tr').remove();
    } else {
      this.showError('At least one payment entry is required.');
    }
  }

  async approveBatch() {
  if (!this.currentBatchId) return;

  const btn = document.getElementById('confirmApproval');
  const original = btn.innerHTML;
  const errorDiv = document.getElementById('approvalError');
  const errorMsg = document.getElementById('approvalErrorMessage');

  // Clear previous error
  errorDiv.classList.add('d-none');

  btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Approving...';
  btn.disabled = true;

  try {
    const payments = [];
    const rows = document.querySelectorAll('#paymentsTableBody tr');

    let totalPaid = 0;
    let hasAnyPayment = false;

    for (const row of rows) {
      const method = row.querySelector('.payment-method').value;
      const amountStr = row.querySelector('.payment-amount').value;
      const account = row.querySelector('.payment-account').value?.trim();

      if (method || amountStr || account) {
        hasAnyPayment = true;

        if (!method) {
          this.showErrorInModal("Payment method is required for filled rows.");
          return;
        }
        const amount = parseFloat(amountStr) || 0;
        if (amount <= 0) {
          this.showErrorInModal("Amount must be greater than zero for filled rows.");
          return;
        }

        totalPaid += amount;

        payments.push({
          method,
          amount,
          payout_account_number: account || null,
          payout_account_name: null,
        });
      }
    }

    // ✅ Only validate total if any payment was entered
    if (hasAnyPayment) {
      const batch = this.transactionCache[this.currentBatchId] ||
                   (await (await fetch(`/office2/transactions/api/${this.currentBatchId}/`)).json()).data;

      const expectedTotal = batch.total_value;
      const tolerance = 0.01;

      if (Math.abs(totalPaid - expectedTotal) > tolerance) {
        this.showErrorInModal(
          `Total payment (₦${totalPaid.toFixed(2)}) must equal batch value (₦${expectedTotal.toFixed(2)}).`
        );
        return;
      }
    }

    const reference = document.getElementById('approvalReference')?.value || null;

    const response = await fetch(`/office2/transactions/approve/${this.currentBatchId}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': this.csrfToken,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ payments, reference })
    });

    const result = await response.json();
    if (result.success) {
      this.showSuccess(result.message);
      const modal = bootstrap.Modal.getInstance(document.getElementById('approvalModal'));
      modal.hide();
      this.loadTransactions();
      this.currentBatchId = null;
    } else {
      this.showErrorInModal(result.error || 'Approval failed. Please try again.');
    }
  } catch (error) {
    this.showErrorInModal('Network error. Please check connection and try again.');
    console.error(error);
  } finally {
    btn.innerHTML = original;
    btn.disabled = false;
  }
}

// ✅ Helper: Show error in modal
showErrorInModal(message) {
  const errorDiv = document.getElementById('approvalError');
  const errorMsg = document.getElementById('approvalErrorMessage');
  errorMsg.textContent = message;
  errorDiv.classList.remove('d-none');
}

  async markAsPaid(id) {
    this.currentBatchId = id;
    const modal = new bootstrap.Modal(document.getElementById('paymentModal'));
    const summary = document.getElementById('paymentSummary');
    summary.innerHTML = '<div class="text-center"><div class="spinner-border spinner-border-sm"></div> Loading...</div>';

    try {
      const response = await fetch(`/office2/transactions/api/${id}/`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      const data = await response.json();
      if (!data.success) throw new Error();

      summary.innerHTML = `
        <p class="text-white mb-2"><strong>Total:</strong> ₦${this.formatCurrency(data.data.total_value)}</p>
        <p class="text-muted small">Confirm to mark as paid.</p>
      `;
      modal.show();
    } catch (error) {
      summary.innerHTML = '<div class="text-danger">Failed to load.</div>';
      this.showError('Could not retrieve details.');
    }
  }

  async submitPayment() {
    if (!this.currentBatchId) return;

    const btn = document.getElementById('confirmPayment');
    const original = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    btn.disabled = true;

    try {
      const response = await fetch(`/office2/transactions/pay/${this.currentBatchId}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': this.csrfToken,
          'Content-Type': 'application/json'
        }
      });

      const result = await response.json();
      if (result.success) {
        this.showSuccess('Batch marked as paid!');
        const modal = bootstrap.Modal.getInstance(document.getElementById('paymentModal'));
        modal.hide();
        this.loadTransactions();
        this.currentBatchId = null;
      } else {
        this.showError(result.error || 'Failed to mark as paid.');
      }
    } catch (error) {
      this.showError('Network error occurred.');
    } finally {
      btn.innerHTML = original;
      btn.disabled = false;
    }
  }

  async deleteBatch(id) {
    if (!confirm('Are you sure you want to delete this batch? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/office2/transactions/delete/${id}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': this.csrfToken,
          'Content-Type': 'application/json'
        }
      });

      const result = await response.json();
      if (result.success) {
        this.showSuccess(result.message || 'Batch deleted successfully.');
        this.loadTransactions();
      } else {
        this.showError(result.error || 'Failed to delete batch.');
      }
    } catch (error) {
      this.showError('Network error. Please try again.');
    }
  }

  showEmptyState() {
    const tbody = document.getElementById('transactionTableBody');
    tbody.innerHTML = '';
    const emptyState = document.getElementById('emptyState');
    emptyState.classList.remove('d-none');
    emptyState.style.display = 'block';
  }

  renderPagination(pagination) {
    const el = document.getElementById('pagination');
    if (!pagination || pagination.total_pages <= 1) {
      el.innerHTML = '';
      return;
    }

    let html = '';
    if (pagination.has_previous) {
      html += `<li class="page-item"><a class="page-link" href="#" data-page="${pagination.current_page - 1}">&laquo;</a></li>`;
    } else {
      html += `<li class="page-item disabled"><span class="page-link">&laquo;</span></li>`;
    }

    const start = Math.max(1, pagination.current_page - 2);
    const end = Math.min(pagination.total_pages, pagination.current_page + 2);

    for (let i = start; i <= end; i++) {
      html += `<li class="page-item ${i === pagination.current_page ? 'active' : ''}">
                 <a class="page-link" href="#" data-page="${i}">${i}</a>
               </li>`;
    }

    if (pagination.has_next) {
      html += `<li class="page-item"><a class="page-link" href="#" data-page="${pagination.current_page + 1}">&raquo;</a></li>`;
    } else {
      html += `<li class="page-item disabled"><span class="page-link">&raquo;</span></li>`;
    }

    el.innerHTML = html;
  }

  updateTotalCount(total) {
    document.getElementById('totalCount').textContent = `${total} batch${total !== 1 ? 'es' : ''}`;
  }

  formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString() + ' ' +
           new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  formatCurrency(num) {
    return num.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
  }
}

// Initialize after DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  if (typeof bootstrap !== 'undefined') {
    window.TransactionManager = new TransactionManager();
  } else {
    console.error('Bootstrap is required but not loaded.');
  }
});
