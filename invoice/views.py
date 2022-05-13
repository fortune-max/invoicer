from django.db.models import F
from rest_framework import viewsets
from datetime import date, timedelta
from django.http import HttpResponse
from ast import literal_eval as safe_eval
from django.shortcuts import get_object_or_404
from .models import CashCall, Investment, Investor, Bill
from invoice.utils import calc_amount_due_investment, calc_amount_due_membership, get_cashcall
from invoice.serializer import BillSerializer, CashCallSerializer, InvestmentSerializer, InvestorSerializer


class InvestorViewSet(viewsets.ModelViewSet):
    queryset = Investor.objects.all()
    serializer_class = InvestorSerializer

class CashCallViewSet(viewsets.ModelViewSet):
    serializer_class = CashCallSerializer

    def get_queryset(self):
        queryset = CashCall.objects.all()
        sent = self.request.GET.get("sent")
        fulfilled = self.request.GET.get("fulfilled")
        validated = self.request.GET.get("validated")
        investor_id = self.request.GET.get("investor_id")
        if investor_id:
            investor = get_object_or_404(Investor, pk=investor_id)
            queryset = queryset.filter(investor=investor)
        if fulfilled:
            queryset = [cashcall for cashcall in queryset if cashcall.fulfilled==safe_eval(fulfilled)]
        if validated:
            queryset = [cashcall for cashcall in queryset if cashcall.validated==safe_eval(validated)]
        if sent:
            queryset = queryset.filter(sent=sent)
        return queryset

class InvestmentViewSet(viewsets.ModelViewSet):
    serializer_class = InvestmentSerializer

    def get_queryset(self):
        queryset = Investment.objects.all()
        fulfilled = self.request.GET.get("fulfilled")
        investor_id = self.request.GET.get("investor_id")
        if investor_id:
            investor = get_object_or_404(Investor, pk=investor_id)
            queryset = queryset.filter(investor=investor)
        if fulfilled:
            queryset = [investment for investment in queryset if investment.fulfilled==safe_eval(fulfilled)]
        return Investment.objects.all()

class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer

    def get_queryset(self):
        queryset = Bill.objects.all()
        sent = self.request.GET.get("sent")
        fulfilled = self.request.GET.get("fulfilled")
        validated = self.request.GET.get("validated")
        investor_id = self.request.GET.get("investor_id")
        if investor_id:
            investor = get_object_or_404(Investor, pk=investor_id)
            queryset = queryset.filter(investor=investor)
        if fulfilled:
            queryset = queryset.filter(fulfilled_one=fulfilled)
        if validated:
            queryset = queryset.filter(validated=validated)
        if sent:
            queryset = [bill for bill in queryset if bill.cashcall.sent==safe_eval(sent)]
        return queryset


def generate(self):
    investor_id = self.POST.get("investor_id")
    dry_run = safe_eval(self.POST.get("dry_run", "False"))
    all_investors = safe_eval(self.POST.get("all", "False"))

    today = date.today()
    # Use this to set how far back older bills should be considered.
    # Ideally should be a bit (minimum a day) over the maximum period of any recurring bill.
    # To account for system downtime, so as not to miss time window, best to add a few months extra, we use 12 here.
    years_back = safe_eval(self.POST.get("years_back", "2"))
    bill_date_lower_limit = today.replace(year=today.year-years_back)

    if not (investor_id or all_investors):
        return HttpResponse("POST investor ID's whose cashcall & bills are to be generated to this endpoint. eg curl -d 'investor_id=2' -X POST http://localhost:8000/invoice/generate")

    response = []

    # Generate bills for membership
    bills = Bill.objects.filter(date__gt=bill_date_lower_limit, bill_type="MEMBERSHIP", frequency="Y1").order_by("date") # oldest to newest
    if investor_id:
        investor = get_object_or_404(Investor, pk=investor_id)
        bills = bills.filter(investor=investor)
    last_membership_bill = {bill.investor.id: bill for bill in bills}
    for investor_id, bill in last_membership_bill.items():
        next_bill_date = bill.date.replace(year=bill.date.year+1)
        if next_bill_date <= today:
            investor = Investor.objects.get(pk=investor_id)
            active = investor.active_member
            amount = calc_amount_due_membership(investor=investor)
            if not dry_run:
                membership_cashcall = get_cashcall(investor=investor, validated=not active)
                membership_bill = Bill(
                    frequency = "Y1",
                    bill_type = "MEMBERSHIP",
                    amount = amount if active else 0,
                    validated = False if active else True,
                    ignore = False if active else True,
                    fulfilled = False if active else True,
                    investor = investor,
                    cashcall = membership_cashcall,
                    date = next_bill_date,
                )
                membership_bill.save()
            response.append(f"{'[DRY RUN!!] ' if dry_run else ''}Billed {investor.name} {membership_bill.amount} EUR for yearly membership")

    # Generate bills for investment
    bills = Bill.objects.filter(date__gt=bill_date_lower_limit, bill_type="INVESTMENT", frequency="Y1").order_by("date") # oldest to newest
    if investor_id:
        investor = get_object_or_404(Investor, pk=investor_id)
        bills = bills.filter(investor=investor)
    bills = [bill for bill in bills if bill.investment.amount_not_billed > 0 and bill.investment.last_instalment < bill.investment.total_instalments]
    last_investment_bill = {(bill.investor.id, bill.investment.id): bill for bill in bills}
    for ((investor_id, investment_id), bill) in last_investment_bill.items():
        next_bill_date = bill.date.replace(year=bill.date.year+1)
        if next_bill_date <= today:
            investor = Investor.objects.get(pk=investor_id)
            active = investor.active_member
            amount, waived = calc_amount_due_investment(investment=bill.investment, instalment_no=bill.instalment_no + 1)
            if not dry_run:
                investment_cashcall = get_cashcall(investor=investor, validated=not active)
                investment_bill = Bill(
                    frequency = "Y1",
                    bill_type = "INVESTMENT",
                    amount = amount if active else 0,
                    validated = False if active else True,
                    ignore = False if active else True,
                    fulfilled = False if active else True,
                    investor = investor,
                    cashcall = investment_cashcall,
                    date = next_bill_date,
                    investment = bill.investment,
                    instalment_no = bill.instalment_no + active,
                )
                investment_bill.save()
                bill.investment.amount_waived = F("amount_waived") + waived
                bill.investment.save()
            response.append(f"{'[DRY RUN!!] ' if dry_run else ''}Billed {investor.name} {amount} EUR for yearly investment")
    if response:
        return HttpResponse('\n'.join(response))
    else:
        return HttpResponse("No bills due, no additional cashcalls generated")

def send(self):
    all_cashcalls = safe_eval(self.POST.get("all", "False"))
    cashcall_id = self.POST.get("cashcall_id")
    dry_run = safe_eval(self.POST.get("dry_run", "False"))
    if all_cashcalls:
        # send all validated cashcalls available
        cashcalls = [cashcall for cashcall in CashCall.objects.filter(sent=False) if cashcall.validated]
        if not cashcalls:
            return HttpResponse("No validated cashcalls in queue to send")
        response = []
        for cashcall in cashcalls:
            if not dry_run:
                cashcall.sent = True
                cashcall.sent_date = date.today()
                cashcall.due_date = date.today() + timedelta(days=62)
                cashcall.save()
            response.append(f"{'[DRY RUN!!] ' if dry_run else ''}Successfully sent cashcall {cashcall.id} to {cashcall.investor.name} ({cashcall.investor.email})")
        return HttpResponse('\n'.join(response))
    elif cashcall_id:
        # send a specific cash_call
        cashcall = get_object_or_404(CashCall, pk=cashcall_id)
        if not cashcall.validated:
            return HttpResponse("Unable to send this cashcall, validate it first")
        if not dry_run:
            cashcall.sent = True
            cashcall.sent_date = date.today()
            cashcall.due_date = date.today() + timedelta(days=62)
            cashcall.save()
        return HttpResponse(f"{'[DRY RUN!!] ' if dry_run else ''}Successfully sent cashcall {cashcall_id} to {cashcall.investor.name} ({cashcall.investor.email})")
    return HttpResponse("POST cashcall ID's to be sent to this endpoint. eg curl -d 'cashcall_id=2' -X POST http://localhost:8000/invoice/send")

def validate(self):
    all_cashcalls = safe_eval(self.POST.get("all", "False"))
    cashcall_id = self.POST.get("cashcall_id")
    dry_run = safe_eval(self.POST.get("dry_run", "False"))
    if all_cashcalls:
        cashcalls = [cashcall for cashcall in CashCall.objects.all() if not cashcall.validated and cashcall.bill_count]
        if not cashcalls:
            return HttpResponse("No non-empty unvalidated cashcalls in queue to validate")
        response = []
        for cashcall in cashcalls:
            for bill in cashcall.bills:
                if not dry_run:
                    bill.validated = True
                    bill.save()
                response.append(f"{'[DRY RUN!!] ' if dry_run else ''}Cashcall {cashcall.id} successfully validated")
        return HttpResponse('\n'.join(response))
    elif cashcall_id:
        cashcall = get_object_or_404(CashCall, pk=cashcall_id)
        if cashcall.validated:
            return HttpResponse("Cashcall already validated")
        if cashcall.bill_count == 0:
            return HttpResponse("Cashcall contains no bills")
        for bill in cashcall.bills:
            if not dry_run:
                bill.validated = True
                bill.save()
        return HttpResponse(f"{'[DRY RUN!!] ' if dry_run else ''}Cashcall successfully validated")
    return HttpResponse("POST cashcall ID's to be validated to this endpoint. eg curl -d 'cashcall_id=2' -X POST http://localhost:8000/invoice/validate")
