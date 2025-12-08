from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import gettext as _
from core.models import MineralTransaction  # Replace 'your_app' with your actual app name


class Command(BaseCommand):
    help = 'Fix weight_unit based on grade pricing when agreed_payout is set'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually making changes',
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Fix all transactions, not just those with agreed_payout',
        )
        parser.add_argument(
            '--transaction-ids',
            nargs='+',
            type=int,
            help='Specific transaction IDs to fix (space-separated)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fix_all = options['fix_all']
        transaction_ids = options.get('transaction_ids')

        # Build queryset based on options
        if transaction_ids:
            queryset = MineralTransaction.objects.filter(id__in=transaction_ids)
            self.stdout.write(f"Processing specific transaction IDs: {transaction_ids}")
        elif fix_all:
            queryset = MineralTransaction.objects.all()
            self.stdout.write("Processing ALL transactions")
        else:
            queryset = MineralTransaction.objects.filter(agreed_payout__isnull=False)
            self.stdout.write("Processing transactions with agreed_payout set")

        if not queryset.exists():
            self.stdout.write(
                self.style.WARNING("No transactions found matching the criteria.")
            )
            return

        total_transactions = queryset.count()
        self.stdout.write(f"Found {total_transactions} transaction(s) to process")

        # Statistics tracking
        stats = {
            'no_change_needed': 0,
            'fixed_to_kg': 0,
            'fixed_to_lb': 0,
            'no_pricing_available': 0,
            'errors': 0,
        }

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        with transaction.atomic():
            for mineral_transaction in queryset.select_related('grade'):
                try:
                    result = self.fix_transaction_weight_unit(mineral_transaction, dry_run)
                    stats[result] += 1
                    
                    if result != 'no_change_needed':
                        self.stdout.write(
                            f"Transaction #{mineral_transaction.id}: {result.replace('_', ' ').title()}"
                        )
                
                except Exception as e:
                    stats['errors'] += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"Error processing transaction #{mineral_transaction.id}: {str(e)}"
                        )
                    )

        # Print summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("SUMMARY:"))
        self.stdout.write(f"Total processed: {total_transactions}")
        self.stdout.write(f"No change needed: {stats['no_change_needed']}")
        self.stdout.write(f"Fixed to kg: {stats['fixed_to_kg']}")
        self.stdout.write(f"Fixed to lb: {stats['fixed_to_lb']}")
        self.stdout.write(f"No pricing available: {stats['no_pricing_available']}")
        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f"Errors: {stats['errors']}"))

        if dry_run and (stats['fixed_to_kg'] + stats['fixed_to_lb']) > 0:
            self.stdout.write(
                self.style.WARNING(
                    "Run without --dry-run to apply these changes."
                )
            )

    def fix_transaction_weight_unit(self, transaction, dry_run=False):
        """
        Fix the weight_unit for a single transaction based on grade pricing.
        Returns a string indicating what action was taken.
        """
        grade = transaction.grade
        current_unit = transaction.weight_unit

        # Check what pricing is available for this grade
        has_kg_price = grade.price_per_kg is not None
        has_lb_price = grade.price_per_pound is not None

        # Determine the correct weight unit
        if has_kg_price and has_lb_price:
            # Both prices available - keep current unit if valid, otherwise prefer kg
            if current_unit in ['kg', 'lb']:
                return 'no_change_needed'
            else:
                correct_unit = 'kg'
        elif has_kg_price:
            correct_unit = 'kg'
        elif has_lb_price:
            correct_unit = 'lb'
        else:
            # No pricing available - can't determine correct unit
            return 'no_pricing_available'

        # Check if change is needed
        if current_unit == correct_unit:
            return 'no_change_needed'

        # Apply the fix
        if not dry_run:
            transaction.weight_unit = correct_unit
            transaction.save(update_fields=['weight_unit'])

        return f'fixed_to_{correct_unit}'

    def get_transaction_info(self, transaction):
        """Helper method to get transaction info for logging."""
        return (
            f"ID: {transaction.id}, "
            f"Mineral: {transaction.mineral_type.name}, "
            f"Grade: {transaction.grade.grade_name}, "
            f"Weight: {transaction.weight} {transaction.weight_unit}, "
            f"Agreed Payout: {transaction.agreed_payout}"
        )