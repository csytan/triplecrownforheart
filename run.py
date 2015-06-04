import hashlib
import json
import pprint
import re
import requests
import urllib

import secrets


def hash_id(secret):
    """
    Hashes IDs like emails and paypal transaction ids to keep them (somewhat) private
    """
    salt = '1a2a3a4a5a6a7a8a9a'
    return hashlib.sha256(secret + salt).hexdigest()[:10]


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
        riders.append({
            'id': hash_id(rider_email),
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
        METHOD='TransactionSearch', STARTDATE='2014-01-01T00:00:00Z')
    
    # Group attributes by transaction
    transactions = {}
    for key, value in results:
        # Example: "L_NETAMT12"
        if not key.startswith('L'):
            continue
                
        # Extract attribute (L_NETAMT) and number (12)
        attr, num = re.findall('(\D+)(\d+)$', key)[0]
        txn = transactions.setdefault(num, {})
        txn[attr] = value
    return list(transactions.values())
    

def paypal_transactiondetails(txn_id):
    """
    https://developer.paypal.com/webapps/developer/docs/classic/api/merchant/GetTransactionDetails_API_Operation_NVP/
    """
    results = paypal_nvp(
        METHOD='GetTransactionDetails', TRANSACTIONID=txn_id)
    return dict(results)


def get_donations():
    transactions = paypal_transactionsearch()
    donation_ids = [
        txn['L_TRANSACTIONID'] for txn in transactions 
        if txn['L_TYPE'] == 'Donation']
    return donation_ids


if __name__ == '__main__':
    pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(get_riders())
    #pp.pprint(paypal_transactionsearch())
    #pp.pprint(paypal_transactiondetails())
    pp.pprint(get_donations())
