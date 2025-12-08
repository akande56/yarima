document.addEventListener('DOMContentLoaded', function () {
    const mineralTypeSelect = document.getElementById('mineralType');
    const gradeSelect = document.getElementById('grade');
    const quantityInput = document.getElementById('quantity');
    const unitSelect = document.getElementById('unit');
    const pricePerUnitInput = document.getElementById('pricePerUnit');
    const totalPriceInput = document.getElementById('totalPrice');

    if (!mineralTypeSelect || !gradeSelect) {
        console.error("Form elements not found");
        return;
    }

    if (typeof mineralGrades === 'undefined') {
        console.error("mineralGrades is not defined. Check template context.");
        return;
    }

    // Update grades when mineral type changes
    mineralTypeSelect.addEventListener('change', function () {
        const mineralId = this.value;
        gradeSelect.innerHTML = '<option value="">Select Grade</option>';
        gradeSelect.disabled = true;

        if (mineralId && mineralGrades[mineralId]) {
            mineralGrades[mineralId].forEach(grade => {
                const option = document.createElement('option');
                option.value = grade.id;
                option.textContent = `${grade.name} (₦${parseFloat(grade.price_per_kg || 0).toLocaleString()}/kg, ₦${parseFloat(grade.price_per_lb || 0).toLocaleString()}/lb)`;
                option.dataset.pricePerKg = grade.price_per_kg;
                option.dataset.pricePerLb = grade.price_per_lb;
                gradeSelect.appendChild(option);
            });
            gradeSelect.disabled = false;
        }
    });

    // Auto-fill price per unit when grade is selected
    gradeSelect.addEventListener('change', function () {
        const selectedOption = this.options[this.selectedIndex];
        const pricePerKg = parseFloat(selectedOption.dataset.pricePerKg) || 0;
        const pricePerLb = parseFloat(selectedOption.dataset.pricePerLb) || 0;
        const unit = unitSelect.value;

        const price = unit === 'kg' ? pricePerKg : pricePerLb;
        pricePerUnitInput.value = price;
        calculateTotal();
    });

    // Update price per unit on unit change
    unitSelect.addEventListener('change', function () {
        const selectedGradeId = gradeSelect.value;
        if (!selectedGradeId) return;

        const selectedOption = gradeSelect.options[gradeSelect.selectedIndex];
        const pricePerKg = parseFloat(selectedOption.dataset.pricePerKg) || 0;
        const pricePerLb = parseFloat(selectedOption.dataset.pricePerLb) || 0;
        const unit = this.value;

        const price = unit === 'kg' ? pricePerKg : pricePerLb;
        pricePerUnitInput.value = price;
        calculateTotal();
    });

    // Recalculate total price on quantity or price change
    function calculateTotal() {
        const quantity = parseFloat(quantityInput.value) || 0;
        const pricePerUnit = parseFloat(pricePerUnitInput.value) || 0;
        totalPriceInput.value = (quantity * pricePerUnit).toFixed(2);
    }

    quantityInput.addEventListener('input', calculateTotal);
    pricePerUnitInput.addEventListener('input', calculateTotal);

    // Trigger change if mineral was pre-selected
    if (mineralTypeSelect.value) {
        mineralTypeSelect.dispatchEvent(new Event('change'));
    }

    // Form submission
    const form = document.getElementById('createSaleForm');
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const data = {
            mineral_type_id: mineralTypeSelect.value,
            grade_id: gradeSelect.value,
            buyer_name: document.getElementById('buyerName').value.trim(),
            quantity: document.getElementById('quantity').value,
            quantity_unit: document.getElementById('unit').value,
            price_per_unit: document.getElementById('pricePerUnit').value,
            total_price: document.getElementById('totalPrice').value,
            sale_date: document.getElementById('saleDate').value,
            notes: document.getElementById('notes').value
        };

        if (!data.mineral_type_id) {
            alert('Please select a mineral type.');
            return;
        }
        if (!data.grade_id) {
            alert('Please select a grade.');
            return;
        }
        if (isNaN(data.quantity) || data.quantity <= 0) {
            alert('Please enter a valid quantity.');
            return;
        }
        if (isNaN(data.price_per_unit) || data.price_per_unit <= 0) {
            alert('Please enter a valid price per unit.');
            return;
        }

        fetch('/office3/sales/create/submit/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(result => {
            if (result.success) {
                alert('Sale transaction created successfully!');
                window.location.href = result.redirect_url;
            } else {
                alert('Error: ' + result.error);
            }
        })
        .catch(err => {
            console.error('Fetch error:', err);
            alert('Failed to submit. Check console for details.');
        });
    });

    // CSRF Token Helper
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