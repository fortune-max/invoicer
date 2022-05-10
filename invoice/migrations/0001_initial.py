# Generated by Django 4.0.4 on 2022-05-09 14:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Investor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
                ('join_date', models.DateField()),
                ('active_member', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Investment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('date_created', models.DateField()),
                ('fee_percent', models.DecimalField(decimal_places=2, max_digits=20)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=20)),
                ('amount_paid', models.DecimalField(decimal_places=2, max_digits=20)),
                ('amount_waived', models.DecimalField(decimal_places=2, max_digits=20)),
                ('total_instalments', models.IntegerField()),
                ('last_instalment', models.IntegerField()),
                ('investor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoice.investor')),
            ],
        ),
        migrations.CreateModel(
            name='CashCall',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=20)),
                ('amount_paid', models.DecimalField(decimal_places=2, max_digits=20)),
                ('sent_date', models.DateField()),
                ('due_date', models.DateField()),
                ('validated', models.BooleanField()),
                ('sent', models.BooleanField()),
                ('investor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoice.investor')),
            ],
        ),
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('frequency', models.CharField(max_length=10)),
                ('bill_type', models.CharField(max_length=50)),
                ('amount', models.IntegerField()),
                ('validated', models.BooleanField()),
                ('invalid', models.BooleanField()),
                ('non_investment_fulfilled', models.BooleanField()),
                ('date', models.DateField()),
                ('instalment_no', models.IntegerField(blank=True, null=True)),
                ('cashcall', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoice.cashcall')),
                ('investment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='invoice.investment')),
                ('investor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoice.investor')),
            ],
        ),
    ]
