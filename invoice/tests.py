from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from rest_framework import status
from .models import Bill, CashCall, Investment, Investor
from .serializer import BillSerializer, CashCallSerializer, InvestmentSerializer, InvestorSerializer
from .utils import get_cashcall, yearly_spend, calc_amount_due_investment, calc_amount_due_membership


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
        response = self.client.post(url, self.investor_json, format="json")
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

    def test_get_cashcall(self):
        """
        Ensure appropriate cashcall for bill is returned when requested.
        """
        Investor.objects.create(name="Harry Guile", email="hguile@gmail.com", active_member=True)
        # No cashcall available return one
        self.assertEqual(CashCall.objects.count(), 1)
        get_cashcall(Investor.objects.first(), 1)
        self.assertEqual(CashCall.objects.count(), 2) # Cashcall created when none available
        get_cashcall(Investor.objects.first(), 0)
        self.assertEqual(CashCall.objects.count(), 2) # Empty cashcall available, don't create more
        Investor.objects.create(name="Harry Guile's clone", email="hguile@clone.com", active_member=True)
        self.assertEqual(CashCall.objects.count(), 3) # Membership placeholder cashcall
        get_cashcall(Investor.objects.last(), 0)
        self.assertEqual(CashCall.objects.count(), 4) # Cashcall created when none available for different investor
        get_cashcall(Investor.objects.last(), 1)
        self.assertEqual(CashCall.objects.count(), 4) # Cashcall repurposed as still empty
        Investor.objects.create(name="Harry Guile's clone 2", email="hguile@clone2.com", active_member=True)
        self.assertEqual(CashCall.objects.count(), 5) # Membership placeholder cashcall
        last_cashcall = CashCall.objects.last()
        last_cashcall.sent = False
        last_cashcall.save()
        for bill in last_cashcall.bills:
            bill.validated = False
            bill.ignore = False
            bill.fulfilled = False
            bill.save()
        get_cashcall(Investor.objects.last(), 0)
        self.assertEqual(CashCall.objects.count(), 5) # Membership bill cashcall fits
        last_cashcall = CashCall.objects.last()
        for bill in last_cashcall.bills:
            bill.validated = True
            bill.save()
        get_cashcall(Investor.objects.last(), 1)
        self.assertEqual(CashCall.objects.count(), 5) # Membership bill cashcall fits

    def test_yearly_spend(self):
        """
        Ensure that yearly spend is accurately calculated.
        Even across leap years.
        """
        investor = Investor.objects.create(name="Harry Guile", email="hguile@gmail.com", active_member=True)
        Bill.objects.create(frequency="M1", bill_type="A", amount=10_000, investor=investor, fulfilled=True, cashcall=get_cashcall(investor, 0), date = date.today())
        one_year_back = date.today().replace(year=date.today().year - 1)
        Bill.objects.create(frequency="M1", bill_type="A", amount=10_000, investor=investor, fulfilled=True, cashcall=get_cashcall(investor, 0), date = one_year_back)
        two_years_back = date.today().replace(year=date.today().year - 2)
        Bill.objects.create(frequency="M1", bill_type="A", amount=10_000, investor=investor, fulfilled=True, cashcall=get_cashcall(investor, 0), date = two_years_back)
        three_years_back = date.today().replace(year=date.today().year - 3)
        Bill.objects.create(frequency="M1", bill_type="A", amount=10_000, investor=investor, fulfilled=True, cashcall=get_cashcall(investor, 0), date = three_years_back)
        four_years_back = date.today().replace(year=date.today().year - 4)
        Bill.objects.create(frequency="M1", bill_type="A", amount=10_000, investor=investor, fulfilled=True, cashcall=get_cashcall(investor, 0), date = four_years_back)
        five_years_back = date.today().replace(year=date.today().year - 5)
        Bill.objects.create(frequency="M1", bill_type="A", amount=10_000, investor=investor, fulfilled=True, cashcall=get_cashcall(investor, 0), date = five_years_back)
        self.assertEqual(yearly_spend(investor, date.today(), 1), 10_000)
        self.assertEqual(yearly_spend(investor, date.today(), 2), 20_000)
        self.assertEqual(yearly_spend(investor, date.today(), 3), 30_000)
        self.assertEqual(yearly_spend(investor, date.today(), 4), 40_000)
        self.assertEqual(yearly_spend(investor, date.today(), 5), 50_000)

    def test_50K_threshold_spend(self):
        """
        Test that once 50K or over is spent in past year cumulatively, no membership is billed.
        Both when membership billing is triggered on deactivation or in regular course of full year.
        """
        # gte threshold, billed 0
        investor = Investor.objects.create(name="Harry Guile", email="hguile@gmail.com", active_member=True)
        one_year_back_inc = date.today().replace(year=date.today().year - 1) + timedelta(days=1)
        Bill.objects.create(frequency="M1", bill_type="A", amount=50_000, investor=investor, fulfilled=True, cashcall=get_cashcall(investor, 0), date = one_year_back_inc)
        self.assertEqual(yearly_spend(investor, date.today(), 1), 50_000)
        response = self.client.patch("/invoice/investor/1/", {"active_member": False}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Bill.objects.last().amount, 0)
        # under threshold, billed in full
        one_year_back = date.today().replace(year=date.today().year - 1)
        investor_2 = Investor.objects.create(name="Harry Guile 2", email="hguile2@gmail.com", active_member=True)
        response = self.client.patch("/invoice/bill/4/", {"date": one_year_back}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        Bill.objects.create(frequency="M1", bill_type="A", amount=50_000, investor=investor_2, fulfilled=True, cashcall=get_cashcall(investor_2, 0), date=one_year_back)
        self.assertEqual(yearly_spend(investor_2, date.today(), 1), 0)
        response = self.client.patch("/invoice/investor/2/", {"active_member": False}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Bill.objects.filter(investor=investor_2).last().amount, 3000)

    def test_generate_bill_membership(self):
        """
        Ensure membership bill generation is accurate.
        Ensure member is billed same day every year, even across leap years.
        """
        four_years_back = date.today().replace(year=date.today().year - 4)
        investor = Investor.objects.create(name="Harry Guile", email="hguile@gmail.com", active_member=True, join_date=four_years_back)
        response = self.client.patch("/invoice/bill/1/", {"date": four_years_back}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Bill.objects.count(), 1)
        response = self.client.post("/invoice/generate", {"all": 1, "years_back": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Bill.objects.count(), 2)
        self.assertEqual(Bill.objects.last().amount, 3000)
        response = self.client.post("/invoice/generate", {"all": 1, "years_back": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Bill.objects.count(), 3)
        self.assertEqual(Bill.objects.last().amount, 3000)
        response = self.client.post("/invoice/generate", {"all": 1, "years_back": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Bill.objects.count(), 4)
        self.assertEqual(Bill.objects.last().amount, 3000)
        response = self.client.post("/invoice/generate", {"all": 1, "years_back": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Bill.objects.count(), 5)
        self.assertEqual(Bill.objects.last().amount, 3000)
        response = self.client.post("/invoice/generate", {"all": 1, "years_back": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Bill.objects.count(), 5)
        self.assertEqual(Bill.objects.last().amount, 3000)
