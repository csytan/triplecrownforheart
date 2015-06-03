import hashlib
import json
import re
import requests
import urllib

import secrets


def wufoo_get_entries():
    """
    Returns the list of entries for the Triple Crown for Heart registration form.
    
    http://help.wufoo.com/articles/en_US/SurveyMonkeyArticleType/The-Entries-GET-API
    """
    # Build request arguments
    subdomain = 'triplecrownforheart'
    form_id = 'z1a4h2p0qbi57j'
    url = ('https://{}.wufoo.com/api/v3/forms/{}/entries.json'
        .format(subdomain, form_id))
        
    # Get response
    response = requests.get(url, auth=(secrets.wufoo_api_key, 'footastic'))
    
    # Filter out cruft
    data = json.loads(response.text)
    return data['Entries']


def get_riders():
    """Returns a list of riders with their names and hashed emails as IDs"""
    riders = []
    for entry in wufoo_get_entries():
        rider_name = (entry['Field5'].capitalize() + ' ' + 
            entry['Field6'].capitalize())
        rider_email = entry['Field7'].strip().encode('utf8')
        rider_id = hashlib.sha256(rider_email).hexdigest()[:10]
        riders.append({
            'id': rider_id,
            'name': rider_name
        })
    return riders


def paypal_nvp(**kwargs):
    """
    https://developer.paypal.com/docs/classic/api/NVPAPIOverview/
    """
    # Prep request variables
    kwargs['USER'] = secrets.paypal_api_username
    kwargs['PWD'] = secrets.paypal_api_password
    kwargs['SIGNATURE'] = secrets.paypal_api_signature
    kwargs['VERSION'] = 122
    # Send request
    response = requests.post('https://api-3t.paypal.com/nvp', kwargs)
    return urllib.parse.parse_qsl(response.text)


def paypal_transactionsearch():
    """
    https://developer.paypal.com/webapps/developer/docs/classic/api/merchant/TransactionSearch_API_Operation_NVP/
    """
    results = paypal_nvp(
        METHOD='TransactionSearch', STARTDATE='2015-01-01T00:00:00Z')
    
    # Group data by transaction
    transactions = {}
    for key, value in results:
        # Example: "L_NETAMT12"
        if not key.startswith('L'):
            continue
                
        # Extract attribute (L_NETAMT) and number (12)
        attr, num = re.findall('(\D+)(\d+)$', key)[0]
        txn = transactions.setdefault(num, {})
        txn[attr] = value
    return transactions.values()
    




import pprint
pp = pprint.PrettyPrinter(indent=4)

#pp.pprint(get_riders())
pp.pprint(paypal_transactionsearch())

