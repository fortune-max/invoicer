from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from rest_framework import status
from .models import Bill, CashCall, Investment, Investor
from .utils import get_cashcall, calc_amount_due_investment, calc_amount_due_membership
from .serializer import BillSerializer, CashCallSerializer, InvestmentSerializer, InvestorSerializer


class Test(TestCase):
    investor_json = {
            "name": "Harry Guile",
            "email": "hguile@gmail.com",
            "active_member": True,
        }

    def test_create_investor(self):
        """
        Ensure that endpoint to create investor works.
        """
        url = "/invoice/investor/"
        response = self.client.post(url, self.investor_json, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Investor.objects.count(), 1)
        self.assertEqual(Investor.objects.get().name, self.investor_json["name"])
        self.assertEqual(Investor.objects.get().email, self.investor_json["email"])
        self.assertEqual(Investor.objects.get().active_member, self.investor_json["active_member"])
        self.assertEqual(Investor.objects.get().join_date, date.today())

    def test_membership_bill_pre_save(self):
        """
        Ensure that when a new investor is created, a corresponding 0 EUR membership bill is created as well.
        """
        self.assertEqual(Bill.objects.count(), 0)
        Investor.objects.create(name="Harry Guile", email="hguile@gmail.com", active_member=True)
        self.assertEqual(Bill.objects.count(), 1)

    def test_membership_bill_deactivation(self):
        """
        Ensure member is billed pro-rata when they deactivate their accounts.
        """
        minus_25_days = date.today() - timedelta(days=25)
        Investor.objects.create(name="Harry Guile", email="hguile@gmail.com", active_member=True, join_date=minus_25_days)
        self.assertEqual(Bill.objects.count(), 1)
        first_bill = Bill.objects.get()
        first_bill.date = minus_25_days
        first_bill.save()
        response = self.client.patch("/invoice/investor/1/", {"active_member": False}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Bill.objects.count(), 2)
        self.assertEqual(int(Bill.objects.last().amount), 205)

    def test_membership_bill_reactivation(self):
        """
        Ensure user is billed 0 EUR on reactivation of account.
        """
        minus_25_days = date.today() - timedelta(days=25)
        Investor.objects.create(name="Harry Guile", email="hguile@gmail.com", active_member=False, join_date=minus_25_days)
        response = self.client.patch("/invoice/investor/1/", {"active_member": True}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Bill.objects.count(), 2)
        self.assertEqual(int(Bill.objects.last().amount), 0)

    def test_bill_created_investment(self):
        """
        Ensure as an Investment is created, a crsp bill is issued, and Investment properties updated.
        """
        Investor.objects.create(name="Harry Guile", email="hguile@gmail.com", active_member=True)
        self.assertEqual(Bill.objects.count(), 1)
        minus_75_days_inc = date.today().replace(month=12, day=31) - timedelta(days=24)
        Investment.objects.create(name="Borland", fee_percent=Decimal('25'), total_amount=12_000, total_instalments=4, date_created=minus_75_days_inc, investor=Investor.objects.first())
        self.assertEqual(Bill.objects.count(), 2)
        self.assertEqual(int(Bill.objects.last().amount), 205)

    def test_ignored_bill_set_to_zero(self):
        """
        Ensure bills marked as invalid are set to 0 EUR amount.
        """
        Investor.objects.create(name="Harry Guile", email="hguile@gmail.com", active_member=True)
        self.client.patch("/invoice/bill/1/", {"amount": 300, "ignore": False}, content_type="application/json")
        self.assertEqual(Bill.objects.first().amount, 300)
        self.client.patch("/invoice/bill/1/", {"ignore": True}, content_type="application/json")
        self.assertEqual(Bill.objects.first().amount, 0)
