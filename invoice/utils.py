from .models import CashCall, Investor

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
