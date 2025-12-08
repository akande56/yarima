document.addEventListener('DOMContentLoaded', function () {
    const filterForm = document.getElementById('filterForm');
    const tableBody = document.getElementById('tableBody');
    const kpiContainer = document.getElementById('kpiContainer');
    const paginationInfo = document.getElementById('paginationInfo');
    const paginationControls = document.getElementById('paginationControls');
    const modal = new bootstrap.Modal(document.getElementById('transactionModal'));
    const modalContent = document.getElementById('modalContent');
    const approveBtn = document.getElementById('approveBtn');
    const editBtn = document.getElementById('editBtn');
    const editBtnLink = document.getElementById('editBtn');

    let currentUrl = new URL(window.location.href);

    // Initial load
    loadTransactions(currentUrl.search);

    // Handle filter submission
    filterForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const formData = new FormData(filterForm);
        const params = new URLSearchParams();
        for (let [key, value] of formData.entries()) {
            if (value) params.append(key, value);
        }
        const queryString = params.toString();
        history.pushState(null, '', '?' + queryString);
        loadTransactions('?' + queryString);
    });

    // Clear filters
    document.getElementById('clearFilters').addEventListener('click', function () {
        filterForm.reset();
        history.pushState(null, '', window.location.pathname);
        loadTransactions('');
    });

    // Pagination click handler
    document.addEventListener('click', function (e) {
        if (e.target.matches('.pagination a')) {
            e.preventDefault();
            const url = e.target.getAttribute('href');
            loadTransactions(new URL(url).search);
        }
    });

    // View transaction modal
    document.addEventListener('click', function (e) {
        if (e.target.matches('.view-btn') || e.target.closest('.view-btn')) {
            const btn = e.target.closest('.view-btn');
            const transactionId = btn.getAttribute('data-id');
            openTransactionModal(transactionId);
        }
    });

    // Approve transaction
    approveBtn.addEventListener('click', function () {
        const transactionId = approveBtn.getAttribute('data-id');
        fetch(`/office3/sales/${transactionId}/approve/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                modal.hide();
                alert('Transaction approved successfully.');
                loadTransactions(window.location.search);
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(err => console.error('Error:', err));
    });

    // Load transactions via AJAX
    function loadTransactions(queryString) {
        fetch(`/office3/sales/data/${queryString}`)
            .then(response => response.json())
            .then(data => {
                tableBody.innerHTML = data.rows_html;
                document.getElementById('kpiTotalCount').textContent = data.kpis.total_count;
                document.getElementById('kpiTotalKg').textContent = data.kpis.total_kg + ' kg';
                document.getElementById('kpiTotalLb').textContent = data.kpis.total_lb + ' lb';
                document.getElementById('kpiTotalValue').textContent = '₦' + parseFloat(data.kpis.total_value).toLocaleString(undefined, {minimumFractionDigits: 2});

                paginationInfo.textContent = data.pagination_info;
                paginationControls.innerHTML = data.pagination_html;

                // Rebind view buttons after reload
                document.querySelectorAll('.view-btn').forEach(btn => {
                    btn.addEventListener('click', function (e) {
                        const id = this.getAttribute('data-id');
                        openTransactionModal(id);
                    });
                });
            })
            .catch(err => console.error('Fetch error:', err));
    }

    // Open modal with transaction details
    function openTransactionModal(id) {
        fetch(`/office3/sales/${id}/detail/`)
            .then(response => response.json())
            .then(data => {
                modalContent.innerHTML = `
                    <p><strong>Reference:</strong> ${data.reference_number}</p>
                    <p><strong>Mineral Type:</strong> ${data.mineral_type}</p>
                    <p><strong>Grade:</strong> ${data.grade}</p>
                    <p><strong>Buyer:</strong> ${data.buyer_name}</p>
                    <p><strong>Quantity:</strong> ${data.quantity} ${data.quantity_unit}</p>
                    <p><strong>Total Price:</strong> ₦${parseFloat(data.total_price).toLocaleString()}</p>
                    <p><strong>Sale Date:</strong> ${new Date(data.sale_date).toLocaleString()}</p>
                    <p><strong>Status:</strong> 
                        <span class="badge ${getStatusBadgeClass(data.status)}">${data.status_display}</span>
                    </p>
                    <p><strong>Recorded By:</strong> ${data.recorded_by}</p>
                `;

                approveBtn.style.display = data.status === 'pending' ? 'inline-block' : 'none';
                editBtnLink.style.display = data.status !== 'completed' ? 'inline-block' : 'none';
                editBtnLink.href = `/office3/sales/${data.id}/edit/`;

                approveBtn.setAttribute('data-id', data.id);

                modal.show();
            })
            .catch(err => {
                modalContent.innerHTML = '<div class="alert alert-danger">Failed to load transaction.</div>';
                modal.show();
            });
    }

    // Helper: Get badge class for status
    function getStatusBadgeClass(status) {
        switch (status) {
            case 'pending': return 'badge-warning';
            case 'approved': return 'badge-info';
            case 'completed': return 'badge-success';
            case 'rejected': return 'badge-secondary';
            default: return 'badge-secondary';
        }
    }

    // CSRF Token helper
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});