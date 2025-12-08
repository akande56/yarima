## 🏢 Yarima Mining System — Powered by Hamzury Innovation Hub

A robust, role-based mineral transaction and record-keeping system developed under **Hamzury Innovation Hub**. Built to streamline workflows across intake, approval, and oversight offices with integrated **security (MFA)** and **POS-style receipt handling**.

---

### 🔧 Tech Stack

* **Framework:** Django 
* **Database:** Sqlite
* **Auth:** Django Allauth + Custom Roles + **Multi-Factor Authentication**
* **PDF/Receipts:** WeasyPrint
* **Environment:** Docker (local + production)
* **UI/UX:** Bootstrap, JavaScript, jQuery, Font Awesome


---

## 🧠 Roles & Responsibilities

| Role       | Access Point           | Responsibilities                            |
| ---------- | ---------------------- | ------------------------------------------- |
| Office 1   | `/office1/dashboard/`  | Record transactions, auto-generate receipts |
| Office 2   | `/office2/dashboard/`  | Approve & mark transactions as paid         |
| Office 3   | `/office3/dashboard/`  | View KPIs, assign roles, export reports     |
| Superuser  | `/admin/`              | Full system access                          |
| Unassigned | `/account/unassigned/` | Blocked from system until role assigned     |

---

## 🔐 Security

✅ Django Allauth with secure login
✅ Integrated **Multi-Factor Authentication (MFA)** support
✅ Role-based access control
✅ CSRF-protected AJAX forms
✅ Input validation and confirmation prompts

---

## 🧾 POS Receipt Flow

1. Office1 submits a transaction.
2. A **PDF opens in a new tab** (receipt).
3. User presses **Ctrl+P** to print via POS printer.
4. Designed for thermal paper layout.

---

## 🏦 Payment Methods (Nigeria Supported)

```python
PAYMENT_METHOD_CHOICES = [
    ('bank', 'Bank Transfer'),
    ('opay', 'OPay'),
    ('moniepoint', 'Moniepoint'),
    ('palmpay', 'PalmPay'),
    ('cash', 'Cash'),
    ('other', 'Other Fintech'),
    # and more...
]
```

Used in both model field and dropdown UI.

---


## 📌 Highlights

✅ Cookiecutter Django structure
✅ MFA-ready login system
✅ AJAX-enhanced role assignment
✅ Realtime-ready via WebSocket (optional)
✅ PDF generation and filterable reports
✅ Role-based router in `core.views.dashboard_router`
✅ Transaction lifecycle logged via `TransactionStatusLog`

---

## 📬 Contact & Support

Built by **Hamzury Innovation Hub**

* 🌍 Website: [hamzuryhub.com.ng](https://hamzuryhub.com.ng)
* 📧 Email: `coo@hamzuryhub.com.ng`
* 💼 Clients: Reach out for white-labeled setups or training