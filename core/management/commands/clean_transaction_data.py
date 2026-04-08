from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction
from django.utils.dateparse import parse_date

from core.models import MineralBatch
from core.models import MineralSale


class Command(BaseCommand):
    help = (
        "Clean mineral transactions (batches) and/or sales data. "
        "By default targets both."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            choices=["transactions", "sales", "all"],
            default="all",
            help="Data group to clean. Defaults to all.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without deleting.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Required to perform destructive deletion.",
        )
        parser.add_argument(
            "--start-date",
            type=str,
            help="Optional start date filter in YYYY-MM-DD (inclusive).",
        )
        parser.add_argument(
            "--end-date",
            type=str,
            help="Optional end date filter in YYYY-MM-DD (inclusive).",
        )

    def handle(self, *args, **options):
        clean_type = options["type"]
        dry_run = options["dry_run"]
        confirmed = options["yes"]
        start_date_raw = options.get("start_date")
        end_date_raw = options.get("end_date")

        start_date = parse_date(start_date_raw) if start_date_raw else None
        end_date = parse_date(end_date_raw) if end_date_raw else None

        if start_date_raw and not start_date:
            raise CommandError("Invalid --start-date. Use YYYY-MM-DD.")
        if end_date_raw and not end_date:
            raise CommandError("Invalid --end-date. Use YYYY-MM-DD.")
        if start_date and end_date and start_date > end_date:
            raise CommandError("--start-date cannot be after --end-date.")

        delete_transactions = clean_type in {"transactions", "all"}
        delete_sales = clean_type in {"sales", "all"}

        tx_queryset = MineralBatch.objects.all()
        sales_queryset = MineralSale.objects.all()

        if start_date:
            tx_queryset = tx_queryset.filter(timestamp__date__gte=start_date)
            sales_queryset = sales_queryset.filter(sale_date__date__gte=start_date)
        if end_date:
            tx_queryset = tx_queryset.filter(timestamp__date__lte=end_date)
            sales_queryset = sales_queryset.filter(sale_date__date__lte=end_date)

        tx_count = tx_queryset.count() if delete_transactions else 0
        sales_count = sales_queryset.count() if delete_sales else 0

        self.stdout.write(self.style.WARNING("Cleanup summary:"))
        self.stdout.write(f"- Mineral batches: {tx_count}")
        self.stdout.write(f"- Mineral sales: {sales_count}")
        if start_date or end_date:
            self.stdout.write(
                f"- Date range: {start_date or '...'} to {end_date or '...'} "
                "(inclusive, based on transaction/sale date)"
            )

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry-run complete. No data deleted."))
            return

        if not confirmed:
            raise CommandError(
                "Refusing to delete data without --yes. "
                "Re-run with --yes or use --dry-run first."
            )

        with transaction.atomic():
            deleted_tx = 0
            deleted_sales = 0

            if delete_transactions:
                deleted_tx, _ = tx_queryset.delete()
            if delete_sales:
                deleted_sales, _ = sales_queryset.delete()

        self.stdout.write(self.style.SUCCESS("Cleanup completed successfully."))
        self.stdout.write(f"- Deleted rows (cascade count) from transactions: {deleted_tx}")
        self.stdout.write(f"- Deleted rows (cascade count) from sales: {deleted_sales}")
