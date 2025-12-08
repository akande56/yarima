# management/commands/fix_negotiated_prices.py
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import MineralTransaction
from decimal import Decimal


class Command(BaseCommand):
    help = 'Convert existing negotiated total amounts to per-unit prices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch (default: 100)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']

        # Get all transactions with negotiated prices (agreed_payout is not null)
        transactions_with_negotiated = MineralTransaction.objects.filter(
            agreed_payout__isnull=False,
            weight__gt=0  # Ensure weight is greater than 0 to avoid division by zero
        ).select_related('mineral_type', 'grade', 'supplier')

        total_count = transactions_with_negotiated.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No transactions with negotiated prices found.')
            )
            return

        self.stdout.write(f'Found {total_count} transactions with negotiated prices to fix.')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        processed = 0
        updated = 0
        errors = 0

        # Process in batches to avoid memory issues
        for offset in range(0, total_count, batch_size):
            batch = transactions_with_negotiated[offset:offset + batch_size]
            
            with transaction.atomic():
                for txn in batch:
                    processed += 1
                    
                    try:
                        # Calculate per-unit price: current_total / weight
                        current_total = float(txn.agreed_payout)
                        weight = float(txn.weight)
                        
                        if weight <= 0:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'Transaction #{txn.id}: Invalid weight ({weight}), skipping'
                                )
                            )
                            errors += 1
                            continue
                        
                        per_unit_price = current_total / weight
                        per_unit_price_decimal = Decimal(str(round(per_unit_price, 2)))
                        
                        # Show what we're doing
                        self.stdout.write(
                            f'Transaction #{txn.id}: {txn.mineral_type.name} ({txn.grade.grade_name})\n'
                            f'  Supplier: {txn.supplier.name}\n'
                            f'  Weight: {weight} {txn.weight_unit}\n'
                            f'  Current negotiated total: ₦{current_total:,.2f}\n'
                            f'  New per-unit price: ₦{per_unit_price:.2f} per {txn.weight_unit}\n'
                            f'  Verification (new calc): {weight} × ₦{per_unit_price:.2f} = ₦{weight * per_unit_price:,.2f}'
                        )
                        
                        # Update if not dry run
                        if not dry_run:
                            txn.agreed_payout = per_unit_price_decimal
                            txn.save(update_fields=['agreed_payout'])
                            updated += 1
                            
                        self.stdout.write('  ✅ Updated\n')
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Transaction #{txn.id}: Error - {str(e)}'
                            )
                        )
                        errors += 1
                        continue

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'SUMMARY:')
        self.stdout.write(f'  Total processed: {processed}')
        if not dry_run:
            self.stdout.write(f'  Successfully updated: {updated}')
        else:
            self.stdout.write(f'  Would be updated: {processed - errors}')
        self.stdout.write(f'  Errors: {errors}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\nThis was a DRY RUN. Run without --dry-run to make actual changes.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Successfully converted {updated} negotiated prices from totals to per-unit prices!'
                )
            )

        # Additional verification step
        if not dry_run and updated > 0:
            self.stdout.write('\n' + '-'*30)
            self.stdout.write('VERIFICATION: Checking a few updated records...')
            
            # Check first 3 updated records
            sample_transactions = MineralTransaction.objects.filter(
                agreed_payout__isnull=False
            )[:3]
            
            for txn in sample_transactions:
                calculated_total = float(txn.weight) * float(txn.agreed_payout)
                self.stdout.write(
                    f'Transaction #{txn.id}: {txn.weight} × ₦{txn.agreed_payout} = ₦{calculated_total:.2f}'
                )