# core/migrations/0016_alter_transactionstatuslog_transaction.py

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0016_populate_mineralbatch'),
    ]

    operations = [
        # Change FK from MineralTransaction to MineralBatch
        migrations.AlterField(
            model_name='transactionstatuslog',
            name='transaction',
            field=models.ForeignKey(
                to='core.mineralbatch',
                on_delete=models.CASCADE,
                related_name='status_logs'
            ),
        ),
    ]