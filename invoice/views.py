from datetime import date, timedelta
from django.http import HttpResponse
from rest_framework import viewsets
from ast import literal_eval as safe_eval
from django.shortcuts import get_object_or_404
from .models import CashCall, Investment, Investor, Bill
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
    return HttpResponse("Hello world")

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

def validate(self):
    return HttpResponse("Holla")
