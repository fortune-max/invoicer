from rest_framework import serializers
from .models import CashCall, Investment, Investor, Bill

class CashCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashCall
        fields = "__all__"

class InvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investment
        fields = "__all__"

class InvestorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investor
        fields = "__all__"

class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = "__all__"
