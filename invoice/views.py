from rest_framework import viewsets
from .models import CashCall, Investment, Investor, Bill
from invoice.serializer import BillSerializer, CashCallSerializer, InvestmentSerializer, InvestorSerializer


class CashCallViewSet(viewsets.ModelViewSet):
    serializer_class = CashCallSerializer

    def get_queryset(self):
        return CashCall.objects.all()

class InvestorViewSet(viewsets.ModelViewSet):
    serializer_class = InvestorSerializer

    def get_queryset(self):
        return Investor.objects.all()

class InvestmentViewSet(viewsets.ModelViewSet):
    serializer_class = InvestmentSerializer

    def get_queryset(self):
        return Investment.objects.all()

class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer

    def get_queryset(self):
        return Bill.objects.all()
