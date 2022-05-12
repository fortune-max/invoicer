# Invoicer
Invoicer is a utility built with Django Rest Framework that serves the following functions.

- Store Investments both ongoing and completed.
- Hold Investor information.
- Generate bills when due and send to Investors based on subscriptions.
- Keep track of Investor bills and their states.

To begin simply clone the repo.

`git clone https://github.com/fortune-max/invoicer`

CD into the directory and run [pipenv](https://pypi.org/project/pipenv/) install to install dependencies.

`cd invoicer && pipenv install`

Activate the virtual environment.

`pipenv shell`

Load some data into the database

`python manage.py loaddata fixtures/mydata.json`

Then start the server.

`python manage.py runserver`

## Endpoints - 1 (Models)
Here are some important endpoints. We are working with the server running on localhost, port 8000.

**Investors**

To get all the investors

`curl http://localhost:8000/invoice/investor/`

And to get a particular investor, we supply the investor ID

`curl http://localhost:8000/invoice/investor/3/`


**Cashcalls**

A cashcall is made of one or more bills grouped together intended to be sent to an investor to notify them of a breakdown of amounts due.

To get all cashcalls

`curl http://localhost:8000/invoice/cashcall/`

And to view a single cashcall,

`curl http://localhost:8000/invoice/cashcall/3/`

**Query Params**

One or more query params may be added to our call, to limit our results from cashcall endpoint.
- `?investor_id=3`
This limits our request to all cashcalls pertaining to the Investor with ID of 3.

- `?validated=1`
This limits our cashcalls to only those which have been validated (checked off on by a human).

- `?sent=1`
  This limits our cashcalls to only those which have been sent to their respective Investor.

- `?fulfilled=1`
  This limits our cashcalls to only those which the Investor has fully settled.

Also note that `investor_id`, `validated`, `sent`, and `fulfilled` can as well be passed as query params to `/bill/`, and `/investment/` endpoints. They can also accept falsy values.

**Bills**

A Bill is a record containing a single item of purchase or subscription due an Investor. A collection of bills by the same Investor make a cashcall.

To view all bills

`curl http://localhost:8000/invoice/bill/`

And to view a single bill,

`curl http://localhost:8000/invoice/bill/4/`

To view all bills by Investor with ID 5

`curl http://localhost:8000/invoice/bill/?investor_id=5`

The same query params as cashcall apply to bills (`investor_id`, `fulfilled`, `sent`, `validated`) and can be used singly or chained to further filter results.


**Investments**

An Investment represents a commitment by an Investor to pay a percentage of an agreed upon amount as an instalment each period (usually a year).

To view all investments

`curl http://localhost:8000/invoice/investment/`

And to view a single investment,

`curl http://localhost:8000/invoice/investment/1/`

Similar to `Bill` and `Cashcall`, `Investment` also takes the same query parameters (`investor_id`, `fulfilled`, `sent`, `validated`).

## Endpoints - 2 (Billing)

Following are not view endpoints and are used for operating on the models above by initiating an action on them.

**Generate**

This generates cashcalls containing bills not yet generated which are presently due. The generated cashcalls/bills are held in the database to be later viewed and validated by a human, and sent out.

To generate investment or membership bills for an investor with ID 3 (if his last payment is over a year old):

`curl -X POST -d "investor_id=3" http://localhost:8000/invoice/generate/`

To generate all pending bills/cashcalls for all investors:

`curl -X POST -d "all=1" http://localhost:8000/invoice/generate/`

**Validate**

Following generation, it is necessary to validate cashcalls to verify they can be sent out to investors.

To validate a cashcall with ID 2:

`curl -X POST -d "cashcall_id=2" http://localhost:8000/invoice/validate/`

To validate all not validated cashcalls that have been generated so far:

`curl -X POST -d "all=1" http://localhost:8000/invoice/validate/`

**Send**

To send out validated cashcalls to investor's emails, we use the send endpoint.

To send a cashcall with ID 2:

`curl -X POST -d "cashcall_id=2" http://localhost:8000/invoice/send/`

To send out all cashcalls currently validated:

`curl -X POST -d "all=1" http://localhost:8000/invoice/send/`

The `all=1` param allows for putting any/all of these in a job that runs periodically to handle billing of investors.

`/generate/`, `/validate/` and `/send/` also accept a parameter `dry_run=1` to print changes expected without modifying the database.

##Working Principle

At the most fundamental level, the way bills are generated is by considering, for a recurring subscription, it's most recently dated bill. If this bill is older than a year, a new bill for the same subscription is issued.

## Assumptions

1) Bills are either paid in full or not at all.
2) For memberships, first bill is issued after one-year of membership. For investments, first bill is issued as soon as an investor makes a pledge. This way funding is available for the start-up immediately.
3) When a member chooses to become inactive, their membership is calculated pro-rata from the date of their last membership bill.
4) If a member joins 21st Jul 2022, they are billed their membership fee on 21st Jul 2023. If another member joins 10th Nov 2024, they are billed on 10th Nov 2025. (Membership billing dates can vary across members).
5) Investment commitments are billed at the last day of every year.
6) A cashcall's due date is set to 62 days (2 months) after it was successfully sent out.
7) Bill computation/generation is done at least once in six months. (Max server downtime is six months).
8) All currencies in EUR.
9) If a member has a cumulative spend of ≥ 50k EUR within the last 12 months, they are not billed for membership for that year.
