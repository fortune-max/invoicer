from rest_framework import serializers
from .models import CashCall, Investment, Investor, Bill

class BillSerializer(serializers.ModelSerializer):
    fulfilled = serializers.ReadOnlyField()

    class Meta:
        model = Bill
        fields = "__all__"
        depth = 1

class CashCallSerializer(serializers.ModelSerializer):
    total_amount = serializers.ReadOnlyField()
    amount_paid = serializers.ReadOnlyField()
    validated = serializers.ReadOnlyField()
    fulfilled = serializers.ReadOnlyField()
    overdue = serializers.ReadOnlyField()
    bill_count = serializers.ReadOnlyField()
    bills = serializers.SerializerMethodField()

    class Meta:
        model = CashCall
        fields = "__all__"

    def get_bills(self, cashcall):
        return BillSerializer(cashcall.bills.all(), many=True).data

class InvestmentSerializer(serializers.ModelSerializer):
    fulfilled = serializers.ReadOnlyField()
    amount_paid = serializers.ReadOnlyField()
    amount_left = serializers.ReadOnlyField()
    last_instalment = serializers.ReadOnlyField()

    class Meta:
        model = Investment
        fields = "__all__"

class InvestorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investor
        fields = "__all__"
