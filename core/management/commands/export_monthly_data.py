"""
Django management command to export monthly data (transactions or sales) as Excel files in a zip archive.

Usage:
    # Export transactions from January to March 2024
    python manage.py export_monthly_data --type transactions --start-month 2024-01 --end-month 2024-03

    # Export sales for the entire year 2024
    python manage.py export_monthly_data --type sales --start-month 2024-01 --end-month 2024-12 --output ./exports

    # Export single month
    python manage.py export_monthly_data --type transactions --start-month 2024-06 --end-month 2024-06
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core.models import MineralBatch, MineralSale
from office3.utils.exporter import TransactionExcelExporter, SaleTransactionExcelExporter
from datetime import datetime
from calendar import monthrange
import zipfile
import os
import tempfile
from openpyxl import Workbook
from io import BytesIO


class Command(BaseCommand):
    help = 'Export monthly data (transactions or sales) as Excel files in a zip archive'

    def add_months(self, date, months):
        """Add specified number of months to a date"""
        month = date.month - 1 + months
        year = date.year + month // 12
        month = month % 12 + 1
        day = min(date.day, monthrange(year, month)[1])
        return date.replace(year=year, month=month, day=day)

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            required=True,
            choices=['transactions', 'sales'],
            help='Type of data to export: transactions or sales'
        )
        parser.add_argument(
            '--start-month',
            type=str,
            required=True,
            help='Start month in YYYY-MM format (e.g., 2024-01)'
        )
        parser.add_argument(
            '--end-month',
            type=str,
            required=True,
            help='End month in YYYY-MM format (e.g., 2024-12)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='.',
            help='Output directory for the zip file (defaults to current directory)'
        )

    def handle(self, *args, **options):
        export_type = options['type']
        start_month_str = options['start_month']
        end_month_str = options['end_month']
        output_dir = options['output']

        # Validate and parse dates
        try:
            start_date = datetime.strptime(start_month_str, '%Y-%m')
            end_date = datetime.strptime(end_month_str, '%Y-%m')
        except ValueError:
            raise CommandError('Invalid date format. Use YYYY-MM (e.g., 2024-01)')

        if start_date > end_date:
            raise CommandError('Start month must be before or equal to end month')

        # Ensure output directory exists
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                self.stdout.write(self.style.SUCCESS(f'Created output directory: {output_dir}'))
            except Exception as e:
                raise CommandError(f'Failed to create output directory: {e}')

        # Generate zip filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'{export_type}_monthly_export_{start_month_str}_to_{end_month_str}_{timestamp}.zip'
        zip_path = os.path.join(output_dir, zip_filename)

        self.stdout.write(self.style.SUCCESS(f'\n=== Monthly {export_type.title()} Export ==='))
        self.stdout.write(f'Period: {start_month_str} to {end_month_str}')
        self.stdout.write(f'Output: {zip_path}\n')

        # Create zip file
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                current_date = start_date
                month_count = 0
                total_records = 0

                while current_date <= end_date:
                    month_str = current_date.strftime('%Y-%m')
                    year = current_date.year
                    month = current_date.month

                    self.stdout.write(f'Processing {month_str}...', ending='')

                    # Get data for this month
                    if export_type == 'transactions':
                        queryset = MineralBatch.objects.filter(
                            timestamp__year=year,
                            timestamp__month=month
                        ).order_by('timestamp')
                        exporter = TransactionExcelExporter()
                    else:  # sales
                        queryset = MineralSale.objects.filter(
                            sale_date__year=year,
                            sale_date__month=month
                        ).order_by('sale_date')
                        exporter = SaleTransactionExcelExporter()

                    record_count = queryset.count()

                    if record_count == 0:
                        self.stdout.write(self.style.WARNING(f' No data found'))
                    else:
                        # Generate Excel file in memory
                        excel_data = self._generate_excel(queryset, exporter, export_type)
                        
                        # Add to zip with descriptive filename
                        excel_filename = f'{export_type}_{month_str}.xlsx'
                        zipf.writestr(excel_filename, excel_data)
                        
                        month_count += 1
                        total_records += record_count
                        self.stdout.write(self.style.SUCCESS(f' ✓ {record_count} records exported'))

                    # Move to next month
                    current_date = self.add_months(current_date, 1)

                # Add summary file
                summary = self._generate_summary(
                    export_type, start_month_str, end_month_str, month_count, total_records
                )
                zipf.writestr('README.txt', summary)

            self.stdout.write(self.style.SUCCESS(f'\n✓ Export completed successfully!'))
            self.stdout.write(f'  Months processed: {month_count}')
            self.stdout.write(f'  Total records: {total_records}')
            self.stdout.write(f'  Zip file: {zip_path}')

        except Exception as e:
            raise CommandError(f'Failed to create zip file: {e}')

    def _generate_excel(self, queryset, exporter, export_type):
        """Generate Excel file in memory and return as bytes"""
        if not queryset.exists():
            # Create empty workbook with message
            wb = Workbook()
            ws = wb.active
            ws.title = "No Data"
            ws['A1'] = "No data found for this period"
            
            buffer = BytesIO()
            wb.save(buffer)
            return buffer.getvalue()

        # Use existing exporter to create workbook
        wb = exporter._create_workbook(queryset)
        
        # Save to BytesIO buffer
        buffer = BytesIO()
        wb.save(buffer)
        return buffer.getvalue()

    def _generate_summary(self, export_type, start_month, end_month, month_count, total_records):
        """Generate summary text file content"""
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        
        summary = f"""
Monthly {export_type.title()} Export Summary
{'=' * 50}

Export Date: {timestamp}
Period: {start_month} to {end_month}
Months with Data: {month_count}
Total Records: {total_records}

Files Included:
{'=' * 50}
"""
        
        # Parse dates for iteration
        start_date = datetime.strptime(start_month, '%Y-%m')
        end_date = datetime.strptime(end_month, '%Y-%m')
        current_date = start_date
        
        while current_date <= end_date:
            month_str = current_date.strftime('%Y-%m')
            summary += f"- {export_type}_{month_str}.xlsx\n"
            current_date = self.add_months(current_date, 1)

        summary += f"""
{'=' * 50}

Instructions:
1. Extract all files from this zip archive
2. Open individual Excel files to view monthly data
3. Each file contains detailed transaction/sale information
4. Files are organized by month for easy analysis

Generated by: Yarima Mining Management System
"""
        
        return summary
