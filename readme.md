# Triple Crown for Heart - Donation Pages


## Setup

Create a file named **secrets.py** and fill in your API credentials:
```
wufoo_api_key = ''
paypal_api_username = ''
paypal_api_password	= ''
paypal_api_signature = ''
mailgun_api_key = ''
```


Install dependencies
```
pip3 install requests
```

To run script
```
python3 run.py
```

To run locally (http://localhost:8000/)
```
python3 -m http.server
```


## Ideas
- Very cool contrib page: http://www.arduino.cc/en/Main/Donate


## Media
- https://www.flickr.com/photos/94324846@N05/sets/72157634977479181/
- http://triplecrownforheart.ca/gallery/


## How it works
- Rider registration is hosted on Wufoo
- Rider donations are done via PayPal
- Data is pulled from Wufoo and PayPal to generate JSON files
- Donation site uses JSON file to populate rider pages
- Script is run at set intervals to update JSON file
- Updates are pushed to this GitHub repo


## Wufoo
- Fetch donors from Wufoo API
    - http://help.wufoo.com/articles/en_US/SurveyMonkeyArticleType/Wufoo-REST-API-V3


## PayPal Standard payments

- https://developer.paypal.com/docs/classic/paypal-payments-standard/integration-guide/formbasics/
- https://developer.paypal.com/docs/classic/paypal-payments-standard/integration-guide/Appx_websitestandard_htmlvariables/#id08A6HF00TZS

*Notes*: Using PayPal instead of Stripe because they let us pass & retrieve a custom variable containing donation details.


## PayPal Fetching Data
1. Get credentials to use NVP API
    - https://developer.paypal.com/webapps/developer/docs/classic/api/NVPAPIOverview/
2. Use TransactionSearch API Operation (NVP) to find recent transactions
    - https://developer.paypal.com/webapps/developer/docs/classic/api/merchant/TransactionSearch_API_Operation_NVP/
2. Use GetTransactionDetails API Operation (NVP) to get custom field
    - https://developer.paypal.com/webapps/developer/docs/classic/api/merchant/GetTransactionDetails_API_Operation_NVP/


*Notes*: REST API requires OAuth 2 client authentication. Not ideal for server-less implementation.


