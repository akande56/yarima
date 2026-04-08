# Implementation Plan: Office2 Transaction Creation/Deletion and Flexible Transaction Dates

## Document Version
- Date: 2026-04-08
- Owner: Engineering
- Status: Planned

## Confirmed Requirements
1. Office2 users must be able to create mineral batch transactions (same capability as Office1).
2. Office2 users must be able to delete mineral batch transactions they created.
3. Delete scope must match Office1 rule: only `pending` or `rejected` batches are deletable.
4. Mineral batch transaction date must be user-selectable (not only auto-current time).
5. Mineral sale transaction date (Office3 flow) must be user-selectable and persist exactly.
6. Office2 sidebar/navigation labeling issue must be corrected.

## Current State Summary
- Office1 has create and delete endpoints for batches.
- Office2 currently has list/approve/pay endpoints, but no create/delete endpoints.
- `MineralBatch.timestamp` already supports manual assignment (`default=timezone.now`), so no schema change is required for batch date flexibility.
- `MineralSale.sale_date` is currently `auto_now_add=True`, which overrides user input and prevents true flexible date behavior.
- Office2 sidebar text is inconsistent between templates:
  - Dashboard page uses `Mineral Transactions` label.
  - Transaction list page uses `Transaction List` label.

## Implementation Strategy

### Phase 1: Backend Permissions and Shared Intake Logic
- Extract Office1 batch creation validation/create logic into a reusable service/helper to avoid duplicated business rules.
- Allow both Office1 and Office2 roles to call shared creation flow.
- Keep role checks strict for each app route while sharing core create logic.

Target files:
- `office1/views.py`
- `office2/views.py`
- New shared helper module (for example: `core/services/batch_intake.py`)

### Phase 2: Office2 Create and Delete Endpoints
- Add Office2 endpoints:
  - Create batch
  - Delete batch
- Enforce delete ownership and state restrictions:
  - `batch.recorded_by == request.user`
  - `batch.status in ['pending', 'rejected']`

Target files:
- `office2/urls.py`
- `office2/views.py`

### Phase 3: UI Updates for Office2
- Add "New Batch" creation UI in Office2 (same functional fields as Office1):
  - supplier name
  - supplier phone
  - mineral rows (mineral, grade, weight, unit, negotiated price)
  - transaction datetime input (`datetime-local`)
- Add delete action button for eligible Office2-owned rows.
- Wire JS calls to new create/delete endpoints.

Target files:
- `office2/templates/office2/transaction_list.html`
- `yarima_mining/static/js/office2.js`

### Phase 4: Flexible Date for Mineral Batch Transactions
- Accept `transaction_date` from Office1 and Office2 create requests.
- Parse/validate to aware datetime.
- On invalid format, return validation error.
- On empty value, fallback to `timezone.now()`.
- Persist to `MineralBatch.timestamp`.

Target files:
- `office1/templates/office1/transactions.html`
- `office1/views.py`
- Office2 create template and view files

### Phase 5: Flexible Date for Sale Transactions (Office3)
- Change model field:
  - from `sale_date = models.DateTimeField(auto_now_add=True, ...)`
  - to `sale_date = models.DateTimeField(default=timezone.now, ...)`
- Generate and apply migration.
- Keep existing Office3 submit parser logic; ensure passed date is stored unchanged.

Target files:
- `core/models.py`
- `core/migrations/<new_migration>.py`
- Validate with `office3/views.py` create submit flow

### Phase 6: Office2 Sidebar/Navigation Fix
- Standardize menu label and active states across Office2 templates.
- Recommended standard labels:
  - `Dashboard`
  - `Mineral Transactions`
- Ensure active class is correct for each page and does not mislead users.

Target files:
- `office2/templates/office2/dashboard.html`
- `office2/templates/office2/transaction_list.html`

## Data and Migration Plan
- Required migration: `MineralSale.sale_date` alteration only.
- No data backfill required; existing sale timestamps remain intact.
- Batch timestamp remains backward-compatible.

## Security and Authorization Rules
- Office2 create: allowed only for `User.Roles.OFFICE_2`.
- Office2 delete: allowed only for `User.Roles.OFFICE_2` and owned batches.
- Office1 behavior remains unchanged.
- Status transition constraints remain enforced server-side.

## Test Plan

### Unit/Integration
1. Office2 create batch success with valid data and explicit `transaction_date`.
2. Office2 create batch fallback when `transaction_date` missing.
3. Office2 create batch rejects invalid `transaction_date` format.
4. Office2 delete succeeds for own batch in `pending`.
5. Office2 delete succeeds for own batch in `rejected`.
6. Office2 delete fails for own batch in `approved/paid/completed`.
7. Office2 delete fails for batch created by another user.
8. Office3 sale create stores submitted `sale_date` after migration.

### Manual QA
1. Verify Office2 sidebar labels are consistent on dashboard and transaction pages.
2. Verify Office2 can create from UI and entry appears with selected timestamp.
3. Verify Office2 delete action appears only when eligible.
4. Verify Office1 creation still works with selected date.
5. Verify Office3 sale date input persists exact chosen date/time.

## Rollout Checklist
1. Implement backend changes.
2. Implement Office2 UI and JS wiring.
3. Add and run migration.
4. Run tests.
5. Run manual QA scenarios.
6. Deploy.
7. Monitor logs for create/delete/date parse errors for first 24 hours.

## Acceptance Criteria
- Office2 can create batches with same validation behavior as Office1.
- Office2 can delete only own `pending/rejected` batches.
- Office1 and Office2 can set custom batch transaction date/time.
- Office3 sale transaction date/time is editable and stored exactly as submitted.
- Office2 sidebar labels and active-state behavior are consistent across pages.
