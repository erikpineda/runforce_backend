# Generated manually (equivalent to running makemigrations for this field change)

import decimal

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_usuario_meta_racha_semanal'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usuario',
            name='meta_racha_semanal',
        ),
        migrations.AddField(
            model_name='usuario',
            name='meta_semanal_km',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Kilometros que el usuario se propone correr por semana, para mantener su racha.', max_digits=6, null=True, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.1'))]),
        ),
    ]
