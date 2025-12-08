// static/js/office3.js

document.addEventListener('DOMContentLoaded', function () {
    let minerals = [];
    let grades = [];

    // DOM Elements
    const mineralsList = document.getElementById('mineralsList');
    const gradesList = document.getElementById('gradesList');
    const mineralSearch = document.getElementById('mineralSearch');
    const gradeSearch = document.getElementById('gradeSearch');
    const mineralFilter = document.getElementById('mineralFilter');
    const mineralCount = document.getElementById('mineralCount');
    const gradeCount = document.getElementById('gradeCount');

    // Load data
    loadMinerals();
    loadGrades();

    async function loadMinerals() {
        showLoading('mineralLoading');
        try {
            const data = await fetch('/office3/api/minerals/').then(r => r.json());
            minerals = data;
            updateMineralCount();
            populateMineralSelects();
            renderMinerals();
        } catch (e) {
            showToast('Failed to load minerals', 'danger');
        } finally {
            hideLoading('mineralLoading');
        }
    }

    async function loadGrades() {
        showLoading('gradeLoading');
        try {
            const data = await fetch('/office3/api/grades/').then(r => r.json());
            grades = data;
            updateGradeCount();
            populateMineralFilter();
            renderGrades();
        } catch (e) {
            showToast('Failed to load grades', 'danger');
        } finally {
            hideLoading('gradeLoading');
        }
    }

    function showLoading(id) {
        document.getElementById(id).classList.remove('d-none');
        document.getElementById(id.replace('Loading', 'List')).classList.add('d-none');
        document.getElementById(id.replace('Loading', 'Empty')).classList.add('d-none');
    }

    function hideLoading(id) {
        document.getElementById(id).classList.add('d-none');
        document.getElementById(id.replace('Loading', 'List')).classList.remove('d-none');
    }

    function renderMinerals() {
        const query = (mineralSearch.value || '').toLowerCase();
        const filtered = minerals.filter(m => m.name.toLowerCase().includes(query));

        if (filtered.length === 0) {
            document.getElementById('mineralsList').innerHTML = '';
            document.getElementById('mineralsEmpty').classList.remove('d-none');
        } else {
            document.getElementById('mineralsEmpty').classList.add('d-none');
            mineralsList.innerHTML = filtered.map(m => `
                <div class="col-md-6 col-lg-4">
                    <div class="mineral-card">
                        <h5 class="text-white">${escapeHtml(m.name)}</h5>
                        ${m.description ? `<p class="text-muted small">${escapeHtml(m.description)}</p>` : ''}
                        <div class="action-buttons">
                            <button class="btn btn-sm btn-outline-warning" onclick="editMineral(${m.id})">
                                <i class="fas fa-edit me-1"></i>Edit
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteMineral(${m.id})">
                                <i class="fas fa-trash me-1"></i>Delete
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    }

    function renderGrades() {
        const query = (gradeSearch.value || '').toLowerCase();
        const filter = mineralFilter.value;

        let filtered = grades;
        if (filter) filtered = filtered.filter(g => g.mineral_id == filter);
        if (query) filtered = filtered.filter(g => g.grade_name.toLowerCase().includes(query));

        if (filtered.length === 0) {
            document.getElementById('gradesList').innerHTML = '';
            document.getElementById('gradesEmpty').classList.remove('d-none');
        } else {
            document.getElementById('gradesEmpty').classList.add('d-none');
            gradesList.innerHTML = filtered.map(g => `
                <div class="col-md-6 col-lg-4">
                    <div class="grade-card">
                        <h5 class="text-white">${escapeHtml(g.grade_name)}</h5>
                        <p class="text-muted small">${escapeHtml(g.mineral_name)}</p>
                        <div class="price-info">
                            ${g.price_per_pound ? `<span class="price-badge">£${g.price_per_pound}/lb</span>` : ''}
                            ${g.price_per_kg ? `<span class="price-badge">£${g.price_per_kg}/kg</span>` : ''}
                        </div>
                        <div class="action-buttons">
                            <button class="btn btn-sm btn-outline-warning" onclick="editGrade(${g.id})">
                                <i class="fas fa-edit me-1"></i>Edit
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteGrade(${g.id})">
                                <i class="fas fa-trash me-1"></i>Delete
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    }

    function populateMineralFilter() {
        mineralFilter.innerHTML = '<option value="">All Minerals</option>';
        minerals.forEach(m => {
            const option = document.createElement('option');
            option.value = m.id;
            option.textContent = m.name;
            mineralFilter.appendChild(option);
        });
    }

    function populateMineralSelects() {
        ['gradeMineralSelect', 'editGradeMineralSelect'].forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            el.innerHTML = '<option value="">Select Mineral</option>';
            minerals.forEach(m => {
                const option = document.createElement('option');
                option.value = m.id;
                option.textContent = m.name;
                el.appendChild(option);
            });
        });
    }

    function updateMineralCount() {
        mineralCount.textContent = `${minerals.length} Minerals`;
    }

    function updateGradeCount() {
        gradeCount.textContent = `${grades.length} Grades`;
    }

    // Search & Filter
    mineralSearch?.addEventListener('input', renderMinerals);
    gradeSearch?.addEventListener('input', renderGrades);
    mineralFilter?.addEventListener('change', renderGrades);

    // Refresh buttons
    document.getElementById('refreshMinerals')?.addEventListener('click', loadMinerals);
    document.getElementById('refreshGrades')?.addEventListener('click', loadGrades);
});

// Utility
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Toast
function showToast(message, type = 'success') {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>`;
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    const toastElement = document.createElement('div');
    toastElement.innerHTML = toastHtml;
    toastContainer.appendChild(toastElement.firstElementChild);
    const toast = new bootstrap.Toast(toastContainer.lastElementChild, { delay: 5000 });
    toast.show();
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// === MODAL HANDLERS ===

// Add Mineral
document.getElementById('addMineralForm')?.addEventListener('submit', async function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    const data = {
        name: formData.get('name'),
        description: formData.get('description')
    };

    try {
        const response = await fetch('/office3/api/minerals/create/', {
            method: 'POST',
            body: formData
        });
        if (response.ok) {
            showToast('Mineral added!', 'success');
            document.getElementById('addMineralModal').querySelector('.btn-close').click();
            location.reload();
        } else {
            const error = await response.json();
            showToast(error.error || 'Save failed', 'danger');
        }
    } catch (e) {
        showToast('Network error', 'danger');
    }
});

// Edit Mineral
function editMineral(id) {
    const mineral = window.minerals.find(m => m.id === id);
    if (!mineral) return;

    document.getElementById('editMineralId').value = mineral.id;
    document.getElementById('editMineralName').value = mineral.name;
    document.getElementById('editMineralDescription').value = mineral.description || '';

    const modal = new bootstrap.Modal(document.getElementById('editMineralModal'));
    modal.show();
}

document.getElementById('editMineralForm')?.addEventListener('submit', async function (e) {
    e.preventDefault();
    const id = document.getElementById('editMineralId').value;
    const formData = new FormData(this);

    try {
        const response = await fetch(`/office3/api/minerals/${id}/update/`, {
            method: 'POST',
            body: formData
        });
        if (response.ok) {
            showToast('Mineral updated!', 'success');
            document.getElementById('editMineralModal').querySelector('.btn-close').click();
            location.reload();
        } else {
            const error = await response.json();
            showToast(error.error || 'Update failed', 'danger');
        }
    } catch (e) {
        showToast('Network error', 'danger');
    }
});

// Delete Mineral
function deleteMineral(id) {
    const mineral = window.minerals.find(m => m.id === id);
    if (!mineral) return;

    document.getElementById('deleteMessage').textContent = `Delete "${mineral.name}"? This will also delete all associated grades.`;
    window.deleteTargetId = id;
    window.deleteTargetType = 'mineral';

    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

// Add Grade
document.getElementById('addGradeForm')?.addEventListener('submit', async function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    const data = {
        mineral: formData.get('mineral'),
        grade_name: formData.get('grade_name'),
        price_per_pound: formData.get('price_per_pound') || null,
        price_per_kg: formData.get('price_per_kg') || null,
    };

    try {
        const response = await fetch('/office3/api/grades/create/', {
            method: 'POST',
            body: JSON.stringify(data),
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            showToast('Grade added!', 'success');
            document.getElementById('addGradeModal').querySelector('.btn-close').click();
            location.reload();
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to add grade', 'danger');
        }
    } catch (e) {
        showToast('Network error', 'danger');
    }
});

// Edit Grade
function editGrade(id) {
    const grade = window.grades.find(g => g.id === id);
    if (!grade) return;

    document.getElementById('editGradeId').value = grade.id;
    document.getElementById('editGradeMineralSelect').value = grade.mineral_id;
    document.getElementById('editGradeName').value = grade.grade_name;
    document.getElementById('editPricePound').value = grade.price_per_pound || '';
    document.getElementById('editPriceKg').value = grade.price_per_kg || '';

    const modal = new bootstrap.Modal(document.getElementById('editGradeModal'));
    modal.show();
}

document.getElementById('editGradeForm')?.addEventListener('submit', async function (e) {
    e.preventDefault();
    const id = document.getElementById('editGradeId').value;
    const formData = new FormData(this);
    const data = {
        mineral: formData.get('mineral'),
        grade_name: formData.get('grade_name'),
        price_per_pound: formData.get('price_per_pound') || null,
        price_per_kg: formData.get('price_per_kg') || null,
    };

    try {
        const response = await fetch(`/office3/api/grades/${id}/update/`, {
            method: 'POST',
            body: JSON.stringify(data),
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            showToast('Grade updated!', 'success');
            document.getElementById('editGradeModal').querySelector('.btn-close').click();
            location.reload();
        } else {
            const error = await response.json();
            showToast(error.error || 'Update failed', 'danger');
        }
    } catch (e) {
        showToast('Network error', 'danger');
    }
});

// Delete Grade
function deleteGrade(id) {
    const grade = window.grades.find(g => g.id === id);
    if (!grade) return;

    document.getElementById('deleteMessage').textContent = `Delete grade "${grade.grade_name}"?`;
    window.deleteTargetId = id;
    window.deleteTargetType = 'grade';

    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

// Confirm Delete
document.getElementById('confirmDelete')?.addEventListener('click', async function () {
    const id = window.deleteTargetId;
    const type = window.deleteTargetType;
    const url = `/office3/api/${type}s/${id}/delete/`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: new FormData(document.getElementById('deleteModal').closest('form') || document.createElement('form'))
        });
        if (response.ok) {
            showToast(`${type === 'mineral' ? 'Mineral' : 'Grade'} deleted.`, 'success');
            document.getElementById('deleteModal').querySelector('.btn-close').click();
            location.reload();
        } else {
            const error = await response.json();
            showToast(error.error || 'Delete failed', 'danger');
        }
    } catch (e) {
        showToast('Network error', 'danger');
    }
});