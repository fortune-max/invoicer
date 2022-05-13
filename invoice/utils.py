import calendar
from decimal import Decimal
from datetime import date, timedelta
from .models import CashCall, Investment, Investor, Bill

dcm = lambda x: Decimal(str(x))
days_in_year = lambda year: 365 + calendar.isleap(year)

def get_cashcall(investor: Investor, validated: bool):
    """
    Returns the first cashcall for supplied investor that is/is not validated.
    Creates and saves a cashcall if none exists. Helps in grouping bills to appropriate cashcalls.
    """
    not_sent = CashCall.objects.filter(investor=investor, sent=False).all() # Take cashcalls for investor and not yet sent
    not_sent = [cashcall for cashcall in not_sent if cashcall.validated==validated or cashcall.bill_count==0] # match validity
    if not_sent:
        return sorted(not_sent, key=lambda x: x.bill_count, reverse=True)[0] # Prioritize non-empty cashcalls to append bill to
    new_cashcall = CashCall(investor=investor, sent=False) # No existing matching cashcall, so create one
    new_cashcall.save()
    return new_cashcall


def calc_amount_due_investment(investment: Investment, instalment_no: int):
    """
    Get the amount due for an investment given the instalment no. (year)
    """
    year_rates = {
                date(2050, 4, 1): {1:dcm(0), 2:dcm(1), 3:dcm(2), "default":dcm(5)},
                date(2019, 4, 1): {1:dcm(0), 2:dcm(0), 3:dcm(0.2), 4:dcm(0.5), "default":dcm(1)},
                date(1950, 1, 1): {1:dcm(0), 2:dcm(0), 3:dcm(0), "default":dcm(0)},
                date(1900, 1, 1): {1:dcm(0.5), 2:dcm(1), 3:dcm(5), "default":dcm(10)},
            } # dates are lower limits, and are the dates rates were changed. Sorted newest to oldest.
    for date_obj, yearly_discount in year_rates.items():
        if investment.date_created >= date_obj:
            discount = yearly_discount.get(instalment_no, yearly_discount.get("default"))
            break
    if instalment_no == 1:
        end_of_year = date(investment.date_created.year, 12, 31)
        num_of_days = dcm((end_of_year - investment.date_created).days + 1)
        days_in_year = dcm((end_of_year - date(investment.date_created.year, 1, 1)).days + 1)
        amount = (num_of_days / days_in_year) * (investment.fee_percent - discount) / 100 * investment.total_amount
        to_pay = min(amount, investment.amount_not_billed)
        to_waive = (num_of_days / days_in_year) * discount / 100 * investment.total_amount
        to_waive = min(to_waive, investment.amount_not_billed - to_pay)
        return to_pay, to_waive
    amount = (investment.fee_percent - discount) / 100 * investment.total_amount
    to_pay = min(amount, investment.amount_not_billed)
    to_waive = discount / 100 * investment.total_amount
    to_waive = min(to_waive, investment.amount_not_billed - to_pay)
    return to_pay, to_waive


def yearly_spend(investor: Investor, start_date:date, years_back: int):
    """
    Get amount spent by an investor from {start_year-years_back} to {start_year}
    """
    period_start = start_date.replace(year=start_date.year-years_back)
    relevant_bills = Bill.objects.filter(investor=investor, fulfilled=True, date__gt=period_start, date__lte=start_date)
    amount_spent = sum([bill.amount for bill in relevant_bills])
    return amount_spent


def calc_amount_due_membership(investor: Investor, pro_rata_days=None):
    """
    Get membership amount due. Accounts for waiving if over yearly spend.
    Also accounts for membership deactivation by pro-rata billing.
    """
    year_rates = {
        date(2050, 4, 1): {"membership": dcm(50_000), "membership_waive": dcm(100_000)},
        date(2030, 6, 1): {"membership": dcm(25_000), "membership_waive": dcm(50_000)},
        date(1900, 1, 1): {"membership": dcm(3_000), "membership_waive": dcm(50_000)},
    } # dates are lower limits, and are the dates yearly membership bills were changed. Sorted newest to oldest.
    for date_obj, yearly_fee in year_rates.items():
        if date.today() >= date_obj:
            membership_fee = yearly_fee["membership"]
            membership_waive = yearly_fee["membership_waive"]
            break
    # Spent over fee threshold within year
    if yearly_spend(investor=investor,start_date=date.today(), years_back=1) >= membership_waive:
        return Decimal('0')
    # Handle membership billing prorata on deactivation of account
    if pro_rata_days != None:
        start_date = date.today() - timedelta(days=pro_rata_days)
        return dcm(pro_rata_days)/days_in_year(start_date.year) * membership_fee
    # Handle regular membership
    return membership_fee
