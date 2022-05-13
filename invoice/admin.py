from . import models
from django.db.models import F
from django.contrib import admin
from datetime import date, timedelta
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from .utils import get_cashcall, calc_amount_due_membership, calc_amount_due_investment

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
            ignore = True,
            fulfilled = True,
            cashcall = membership_cashcall,
        )
        membership_cashcall.save()
        membership_bill.save()

# Create a bill for Investment first instalment once Investment created
@receiver(post_save, sender=models.Investment)
def bill_investment(sender, instance, created, **kwargs):
    if created:
        to_pay, to_waive = calc_amount_due_investment(instance, 1)
        investment_cashcall = get_cashcall(instance.investor, False)
        investment_bill = models.Bill(
            frequency = "Y1",
            bill_type = "INVESTMENT",
            amount = to_pay,
            investor = instance.investor,
            cashcall = investment_cashcall,
            instalment_no = 1,
            investment = instance,
        )
        investment_bill.save()
        instance.amount_waived = F("amount_waived") + to_waive
        instance.save()

# Bill membership fee on active toggle. 0 EUR if reactivated, {days/yr_days * membership_fee} EUR if deactivated
@receiver(pre_save, sender=models.Investor)
def bill_membership_active_toggle(sender, instance, *args, **kwargs):
    if instance.id: # Ensure the Investor already exists
        investor_old = models.Investor.objects.get(pk=instance.id)
        if investor_old.active_member==True and instance.active_member==False:
            # deactivation of account
            last_membership_bill = models.Bill.objects.filter(bill_type="MEMBERSHIP", investor=instance).order_by("-date").first()
            pro_rata_days = (date.today() - last_membership_bill.date).days
            membership_cashcall = get_cashcall(instance, False)
            membership_bill = models.Bill(
                frequency = "Y1",
                bill_type = "MEMBERSHIP",
                amount = calc_amount_due_membership(investor=instance, pro_rata_days=pro_rata_days),
                investor = instance,
                cashcall = membership_cashcall,
            )
            membership_bill.save()
        elif investor_old.active_member==False and instance.active_member==True:
            # reactivation of account
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
                ignore = True,
                fulfilled = True,
                cashcall = membership_cashcall,
            )
            membership_cashcall.save()
            membership_bill.save()

# Ensure that amount is set to 0 EUR when bill is set to ignored/not valid
@receiver(pre_save, sender=models.Bill)
def bill_membership_active_toggle(sender, instance, *args, **kwargs):
    if instance.id: # Ensure the Bill already exists
        bill_old = models.Bill.objects.get(pk=instance.id)
        if bill_old.ignore==False and instance.ignore==True:
            instance.amount = 0
