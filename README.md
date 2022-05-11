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

`python manage.py loaddata fixtures/mydata`

Then start the server.

`python manage.py runserver`

## Endpoints
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
This limits our cashcalls to only those which have not yet been validated (checked off on by a human).

- `?sent=1`
  This limits our cashcalls to only those which have been sent to their respective Investor.

- `?fulfilled=1`
  This limits our cashcalls to only those which the Investor has fully settled.

Also note that `investor_id`, `validated`, `sent`, and `fulfilled` can as well be passed as query params to `/bill/`, and `/investment/` endpoints.

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
