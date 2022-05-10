from django.db import models
from datetime import date

class Investor(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    join_date = models.DateField()
    active_member = models.BooleanField()

    def __str__(self):
        return self.name


class Investment(models.Model):
    name = models.CharField(max_length=50)
    date_created = models.DateField()
    fee_percent = models.DecimalField(max_digits=20, decimal_places=2)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2)
    amount_waived = models.DecimalField(max_digits=20, decimal_places=2)
    total_instalments = models.IntegerField()
    last_instalment = models.IntegerField()
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)

    @property
    def fulfilled(self):
        return self.amount_paid + self.amount_waived >= self.total_amount

    def __str__(self):
        return f"{self.name} €{self.amount_paid + self.amount_waived} of €{self.total_amount} paid"


class CashCall(models.Model):
    sent_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    sent = models.BooleanField()
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)

    @property
    def total_amount(self):
        return sum([bill.amount for bill in Bill.objects.filter(cashcall=self.pk)])
        
    @property
    def amount_paid(self):
        return sum([bill.amount for bill in Bill.objects.filter(cashcall=self.pk) if bill.fulfilled])

    @property
    def validated(self):
        return all([bill.validated for bill in Bill.objects.filter(cashcall=self.pk)])

    @property
    def fulfilled(self):
        return self.amount_paid >= self.total_amount

    @property
    def overdue(self):
        if self.fulfilled:
            return False
        return date.today() > self.due_date

    @property
    def bill_count(self):
        return len(Bill.objects.filter(cashcall=self.pk))

    @property
    def bills(self):
        return Bill.objects.filter(cashcall=self.pk)

    def __str__(self):
        return f"{self.investor.name} €{self.amount_paid} of €{self.total_amount} paid"


class Bill(models.Model):
    frequency = models.CharField(max_length=10) # Y5 (quinquennial), O1 (oneoff), M2 (bimonthly), D1 (daily)
    bill_type = models.CharField(max_length=50) # INVESTMENT, MEMBERSHIP
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    validated = models.BooleanField()
    invalid = models.BooleanField()
    fulfilled_one = models.BooleanField()
    fulfilled_all = models.BooleanField()
    cashcall = models.ForeignKey(CashCall, on_delete=models.CASCADE)
    date = models.DateField()
    # specific to yearly investments
    instalment_no = models.IntegerField(blank=True, null=True)
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, blank=True, null=True)
    
    @property
    def fulfilled(self):
        return self.fulfilled_one and self.fulfilled_all
    
    def __str__(self):
        return f"{self.investor.name} {self.bill_type} {self.amount}"
