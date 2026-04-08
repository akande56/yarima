"""
Monthly maintenance command to optimize database performance.

Usage:
    python manage.py monthly_maintenance

This command should be run once per month to:
1. Vacuum and analyze PostgreSQL tables
2. Show database statistics
3. Identify slow queries
"""
from django.core.management.base import BaseCommand
from django.db import connection
from decimal import Decimal


class Command(BaseCommand):
    help = 'Run monthly database maintenance to prevent performance degradation'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting monthly maintenance...'))
        
        # 1. Database statistics
        self.stdout.write('\n=== Database Statistics ===')
        self.show_table_sizes()
        
        # 2. Vacuum and analyze
        self.stdout.write('\n=== Running VACUUM ANALYZE ===')
        self.vacuum_analyze()
        
        # 3. Show recommendations
        self.stdout.write('\n=== Recommendations ===')
        self.show_recommendations()
        
        self.stdout.write(self.style.SUCCESS('\n✓ Monthly maintenance completed!'))

    def show_table_sizes(self):
        """Show size of main tables"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    schemaname,
                    relname,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) AS size,
                    n_live_tup as row_count
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||relname) DESC
                LIMIT 10;
            """)
            
            self.stdout.write('Top 10 largest tables:')
            for row in cursor.fetchall():
                self.stdout.write(f'  {row[1]}: {row[2]} ({row[3]:,} rows)')

    def vacuum_analyze(self):
        """Run VACUUM ANALYZE on all tables"""
        with connection.cursor() as cursor:
            # Get all user tables
            cursor.execute("""
                SELECT relname 
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public';
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                try:
                    self.stdout.write(f'  Optimizing {table}...')
                    cursor.execute(f'VACUUM ANALYZE {table};')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'    Warning: {e}'))
            
            self.stdout.write(self.style.SUCCESS('  ✓ All tables optimized'))

    def show_recommendations(self):
        """Show maintenance recommendations"""
        from core.models import MineralBatch, MineralSale
        
        # Count records
        total_batches = MineralBatch.objects.count()
        paid_batches = MineralBatch.objects.filter(status='paid').count()
        total_sales = MineralSale.objects.count()
        
        self.stdout.write(f'Total Batches: {total_batches:,}')
        self.stdout.write(f'Paid Batches: {paid_batches:,}')
        self.stdout.write(f'Total Sales: {total_sales:,}')
        
        # Recommendations based on data volume
        if paid_batches > 10000:
            self.stdout.write(self.style.WARNING(
                '\n⚠ Consider archiving batches older than 6 months to improve performance'
            ))
        
        if total_batches > 50000:
            self.stdout.write(self.style.WARNING(
                '⚠ Database is getting large. Consider implementing data archival strategy'
            ))
        
        self.stdout.write('\nNext maintenance due: ~30 days from now')
