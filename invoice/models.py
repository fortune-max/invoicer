from decimal import Decimal
from django.db import models
from datetime import date
from django.core.validators import MinValueValidator, MaxValueValidator

PRICE_VALIDATOR=[MinValueValidator(Decimal('0.00'))]
PERCENTAGE_VALIDATOR = [MinValueValidator(0), MaxValueValidator(100)]

class Investor(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    join_date = models.DateField(default=date.today)
    active_member = models.BooleanField()

    def __str__(self):
        return self.name


class Investment(models.Model):
    name = models.CharField(max_length=50)
    date_created = models.DateField(default=date.today)
    fee_percent = models.DecimalField(max_digits=10, decimal_places=2, validators=PERCENTAGE_VALIDATOR)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, validators=PRICE_VALIDATOR)
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2, default=0, validators=PRICE_VALIDATOR)
    amount_waived = models.DecimalField(max_digits=20, decimal_places=2, default=0, validators=PRICE_VALIDATOR)
    total_instalments = models.IntegerField()
    last_instalment = models.IntegerField(default=0)
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)

    @property
    def amount_left(self):
        return max(self.total_amount - (self.amount_waived + self.amount_paid), 0)

    @property
    def fulfilled(self):
        return self.amount_paid + self.amount_waived >= self.total_amount

    def __str__(self):
        return f"{self.name} €{self.amount_paid + self.amount_waived} of €{self.total_amount} paid"


class CashCall(models.Model):
    sent_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    sent = models.BooleanField(default=False)
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)

    @property
    def total_amount(self):
        return sum([bill.amount for bill in Bill.objects.filter(cashcall=self.pk)])
        
    @property
    def amount_paid(self):
        return sum([bill.amount for bill in Bill.objects.filter(cashcall=self.pk) if bill.fulfilled])

    @property
    def validated(self):
        return all([bill.validated for bill in Bill.objects.filter(cashcall=self.pk)] or [False])

    @property
    def fulfilled(self):
        return self.amount_paid >= self.total_amount

    @property
    def overdue(self):
        if self.fulfilled or not self.sent:
            return False
        return date.today() > self.due_date

    @property
    def bill_count(self):
        return Bill.objects.filter(cashcall=self.pk).count()

    @property
    def bills(self):
        return Bill.objects.filter(cashcall=self.pk)

    def __str__(self):
        return f"{self.investor.name} €{self.amount_paid} of €{self.total_amount} paid"


class Bill(models.Model):
    frequency = models.CharField(max_length=10) # Y5 (quinquennial), O1 (oneoff), M2 (bimonthly), D1 (daily)
    bill_type = models.CharField(max_length=50) # INVESTMENT, MEMBERSHIP
    amount = models.DecimalField(max_digits=20, decimal_places=2, validators=PRICE_VALIDATOR)
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    validated = models.BooleanField(default=False)
    ignore = models.BooleanField(default=False)
    fulfilled = models.BooleanField(default=False)
    cashcall = models.ForeignKey(CashCall, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    # specific to yearly investments
    instalment_no = models.IntegerField(blank=True, null=True)
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"{self.investor.name} {self.bill_type} {self.amount}"
