from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import MineralType, MineralGrade  # Replace 'myapp' with your actual app name


class Command(BaseCommand):
    help = 'Add grades to existing Columbite and Monozite minerals'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating the grades',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        try:
            if not dry_run:
                transaction_context = transaction.atomic()
            else:
                # Use a dummy context manager for dry run
                from contextlib import nullcontext
                transaction_context = nullcontext()
                
            with transaction_context:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING('DRY RUN MODE - No changes will be made to the database')
                    )
                # Get existing minerals
                try:
                    columbite = MineralType.objects.get(name="Columbite")
                except MineralType.DoesNotExist:
                    raise CommandError('Mineral "Columbite" does not exist. Please create it first.')

                try:
                    monozite = MineralType.objects.get(name="Monozite")
                except MineralType.DoesNotExist:
                    raise CommandError('Mineral "Monozite" does not exist. Please create it first.')

                # Add grades for Columbite (18.5 to 21.0 with 0.1 increments)
                columbite_created_count = 0
                columbite_existing_count = 0
                
                # Generate range from 18.5 to 21.0 with 0.1 increments
                start = 18.5
                end = 21.0
                step = 0.1
                current = start
                
                while current <= end:
                    grade_name = f"{current:.1f}"
                    
                    if dry_run:
                        # Check if grade exists without creating
                        exists = MineralGrade.objects.filter(
                            mineral=columbite,
                            grade_name=grade_name
                        ).exists()
                        
                        if exists:
                            columbite_existing_count += 1
                            self.stdout.write(f"  Would skip existing: {grade_name}")
                        else:
                            columbite_created_count += 1
                            self.stdout.write(f"  Would create: {grade_name} (price_per_pound=0.00)")
                    else:
                        grade, created = MineralGrade.objects.get_or_create(
                            mineral=columbite,
                            grade_name=grade_name,
                            defaults={
                                'price_per_pound': 0.00,
                                'price_per_kg': None
                            }
                        )
                        
                        if created:
                            columbite_created_count += 1
                        else:
                            columbite_existing_count += 1
                    
                    current = round(current + step, 1)  # Round to avoid floating point precision issues
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Columbite: Created {columbite_created_count} new grades, '
                        f'{columbite_existing_count} already existed'
                    )
                )

                # Add grades for Monozite (95 down to 60 with 5 unit decrements)
                monozite_created_count = 0
                monozite_existing_count = 0
                
                # Generate range from 95 down to 60 with decrements of 5
                for grade_value in range(95, 59, -5):  # 59 because range is exclusive of end
                    grade_name = str(grade_value)
                    
                    if dry_run:
                        # Check if grade exists without creating
                        exists = MineralGrade.objects.filter(
                            mineral=monozite,
                            grade_name=grade_name
                        ).exists()
                        
                        if exists:
                            monozite_existing_count += 1
                            self.stdout.write(f"  Would skip existing: {grade_name}")
                        else:
                            monozite_created_count += 1
                            self.stdout.write(f"  Would create: {grade_name} (price_per_kg=0.00)")
                    else:
                        grade, created = MineralGrade.objects.get_or_create(
                            mineral=monozite,
                            grade_name=grade_name,
                            defaults={
                                'price_per_pound': None,
                                'price_per_kg': 0.00
                            }
                        )
                        
                        if created:
                            monozite_created_count += 1
                        else:
                            monozite_existing_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Monozite: Created {monozite_created_count} new grades, '
                        f'{monozite_existing_count} already existed'
                    )
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'{"[DRY RUN] " if dry_run else ""}Successfully completed adding mineral grades!'
                    )
                )

        except Exception as e:
            raise CommandError(f'An error occurred: {str(e)}')