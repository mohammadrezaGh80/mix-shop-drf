# Generated by Django 5.0.4 on 2024-05-07 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0022_alter_orderitem_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='zarinpal_authority',
            field=models.CharField(blank=True, max_length=255, verbose_name='Zarinpal authority'),
        ),
    ]
