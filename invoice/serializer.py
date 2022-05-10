from rest_framework import serializers
from .models import CashCall, Investment, Investor, Bill

class CashCallSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CashCall
        fields = "__all__"

class InvestmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Investment
        fields = "__all__"

class InvestorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Investor
        fields = "__all__"

class BillSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Bill
        fields = "__all__"
