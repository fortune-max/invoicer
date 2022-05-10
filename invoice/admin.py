from datetime import date, timedelta
from django.contrib import admin
from django.db.models.signals import post_save
from django.dispatch import receiver
from . import models
from .utils import get_cashcall, calc_amount

# Model registration
admin.site.register(models.Investor)
admin.site.register(models.Investment)
admin.site.register(models.CashCall)
admin.site.register(models.Bill)

# Create a dummy membership bill on Investor creation
@receiver(post_save, sender=models.Investor)
def bill_membership(sender, instance, created, **kwargs):
    if created:
        membership_cashcall = models.CashCall(
            sent = True,
            investor = instance,
            sent_date = date.today(),
            due_date = date.today() + timedelta(days=62),
        )
        membership_bill = models.Bill(
            frequency = "Y1", 
            bill_type = "MEMBERSHIP",
            amount = 0,
            investor = instance,
            validated = True,
            fulfilled_one = True,
            fulfilled_all = True,
            cashcall = membership_cashcall,
        )
        membership_cashcall.save()
        membership_bill.save()

@receiver(post_save, sender=models.Investment)
def bill_investment(sender, instance, created, **kwargs):
    if created:
        investment_cashcall = get_cashcall(instance.investor, False)
        investment_bill = models.Bill(
            frequency = "Y1",
            bill_type = "INVESTMENT",
            amount = calc_amount(instance, 1),
            investor = instance.investor,
            cashcall = investment_cashcall,
        )
        investment_bill.save()
