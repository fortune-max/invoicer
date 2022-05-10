from datetime import date
from decimal import Decimal
from .models import CashCall, Investment, Investor

def get_cashcall(investor: Investor, validated: bool):
    """
    Returns the first cashcall for supplied investor that is/is not validated.
    Creates and saves a cashcall if none exists. Helps in grouping bills to appropriate cashcalls.
    """
    not_sent = CashCall.objects.filter(investor=investor).filter(sent=False).all() # Filter cashcalls by investor not yet sent out
    not_sent = [cashcall for cashcall in not_sent if cashcall.validated==validated or cashcall.bill_count==0] # match validity
    if not_sent:
        return sorted(not_sent, key=lambda x: x.bill_count, reverse=True)[0] # Prioritize non-empty cashcalls to append bill to
    new_cashcall = CashCall(investor=investor, sent=False) # No existing matching cashcall, so create one
    new_cashcall.save()
    return new_cashcall

dcm = lambda x: Decimal(str(x))
def calc_amount(investment: Investment, instalment_no: int):
    """
    Get the amount due for an investment given the instalment no. (year)
    """
    year_rates = {
                date(2050, 4, 1): {1:dcm(0), 2:dcm(1), 3:dcm(2), "default":dcm(5)},
                date(2019, 4, 1): {1:dcm(0), 2:dcm(0), 3:dcm(0.2), 4:dcm(0.5), "default":dcm(1)},
                date(1900, 1, 1): {1:dcm(0), 2:dcm(0), 3:dcm(0), "default": dcm(0)},
            } # dates are lower limits, and are the dates rates were changed. Sorted newest to oldest.
    for date_obj, yearly_discount in year_rates.items():
        if investment.date_created >= date_obj:
            discount = yearly_discount.get(instalment_no, yearly_discount.get("default"))
            break
    if instalment_no == 1:
        end_of_year = date(investment.date_created.year, 12, 31)
        num_of_days = dcm((end_of_year - investment.date_created).days)
        days_in_year = dcm((end_of_year - date(investment.date_created.year, 1, 1)).days)
        amount = (num_of_days / days_in_year) * (investment.fee_percent - discount) / 100 * investment.total_amount
    amount = (investment.fee_percent - discount) / 100 * investment.total_amount
    return min(amount, investment.amount_left)
