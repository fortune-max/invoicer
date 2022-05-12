from rest_framework import viewsets
from datetime import date, timedelta
from django.http import HttpResponse
from ast import literal_eval as safe_eval
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

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
    response = []
    today = date.today()
    two_years_ago = today.replace(year=today.year-2)

    # Generate bills for membership, TODO check if user is active
    bills = Bill.objects.filter(date__gt=two_years_ago, bill_type="MEMBERSHIP", frequency="Y1").order_by("date") # oldest to newest
    last_membership_bill = {bill.investor.id: bill for bill in bills}
    for investor_id, bill in last_membership_bill.items():
        next_bill_date = bill.date.replace(year=bill.date.year+1)
        if next_bill_date <= today:
            investor = Investor.objects.get(pk=investor_id)
            active = investor.active_member
            amount = calc_amount_due_membership(investor=investor)
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
            response.append(f"Billed {investor.name} {membership_bill.amount} EUR for yearly membership")

    # Generate bills for investment, TODO check if user is active
    bills = Bill.objects.filter(date__gt=two_years_ago, bill_type="INVESTMENT", frequency="Y1").order_by("date") # oldest to newest
    bills = [bill for bill in bills if not bill.investment.fulfilled and bill.investment.last_instalment < bill.investment.total_instalments]
    last_investment_bill = {bill.investor.id: bill for bill in bills}
    for investor_id, bill in last_investment_bill.items():
        next_bill_date = bill.date.replace(year=bill.date.year+1)
        if next_bill_date <= today:
            investor = Investor.objects.get(pk=investor_id)
            active = investor.active_member
            amount = calc_amount_due_investment(investment=bill.investment, instalment_no=bill.instalment_no + 1)
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
            response.append(f"Billed {investor.name} {amount} EUR for yearly investment")
    return HttpResponse('\n'.join(response))

@csrf_exempt # Allow cURL to hit this
def send(self):
    cashcall_id = self.POST.get("cashcall_id")
    if cashcall_id:
        cashcall = get_object_or_404(CashCall, pk=cashcall_id)
        if not cashcall.validated:
            return HttpResponse("Unable to send this cashcall, validate it first")
        cashcall.sent = True
        cashcall.sent_date = date.today()
        cashcall.due_date = date.today() + timedelta(days=62)
        cashcall.save()
        return HttpResponse(f"Successfully sent cashcall {cashcall_id} to {cashcall.investor.name} ({cashcall.investor.email})")
    # send all validated cashcalls available
    cashcalls = [cashcall for cashcall in CashCall.objects.filter(sent=False) if cashcall.validated]
    if not cashcalls:
        return HttpResponse("No validated cashcalls in queue to send")
    response = []
    for cashcall in cashcalls:
        cashcall.sent = True
        cashcall.sent_date = date.today()
        cashcall.due_date = date.today() + timedelta(days=62)
        cashcall.save()
        response.append(f"Successfully sent cashcall {cashcall.id} to {cashcall.investor.name} ({cashcall.investor.email})")
    return HttpResponse('\n'.join(response))

@csrf_exempt # Allow cURL to hit this
def validate(self):
    cashcall_id = self.POST.get("cashcall_id")
    if cashcall_id:
        cashcall = get_object_or_404(CashCall, pk=cashcall_id)
        if cashcall.validated:
            return HttpResponse("Cashcall already validated")
        if cashcall.bill_count == 0:
            return HttpResponse("Cashcall contains no bills")
        for bill in cashcall.bills:
            bill.validated = True
            bill.save()
        return HttpResponse("Cashcall successfully validated")
    return HttpResponse("POST cashcall ID's to be validated to this endpoint. eg curl -d 'cashcall_id=2' -X POST http://../validate")
