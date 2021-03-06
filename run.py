import hashlib
import json
import pprint
import re
import requests
import subprocess
import time
import urllib

import secrets


def hash_id(secret):
    """
    Hashes IDs like emails and paypal transaction ids to keep them (somewhat) private
    """
    text = ('1a2a3a4a5a6a7a8a9a' + secret).encode('utf8')
    return hashlib.sha256(text).hexdigest()[:10]


def wufoo_get_entries(pagestart=0):
    """
    Returns the list of entries for the Triple Crown for Heart registration form.
    
    http://help.wufoo.com/articles/en_US/SurveyMonkeyArticleType/The-Entries-GET-API
    """
    # Build request arguments
    subdomain = 'triplecrownforheart'
    form_id = 'z1a4h2p0qbi57j'
    url = ('https://{}.wufoo.com/api/v3/forms/{}/entries.json?pageStart={}&pageSize=100'
        .format(subdomain, form_id, pagestart))
        
    # Get response
    response = requests.get(url, auth=(secrets.wufoo_api_key, 'footastic'))
    
    # Filter out cruft
    data = json.loads(response.text)
    entries = data['Entries']
    if len(entries) == 100:
        entries += wufoo_get_entries(pagestart + 100)
    return entries


def get_riders():
    """Returns a list of riders with their names and hashed emails as IDs"""
    riders = []
    for entry in wufoo_get_entries():
        first_name = entry['Field5'].capitalize().strip()
        last_name = entry['Field6'].capitalize().strip()
        rider_email = entry['Field7'].strip()
        riders.append({
            'id': hash_id(rider_email),
            'first_name': first_name,
            'last_name': last_name,
            'name': first_name + ' ' + last_name,
            'email': rider_email
        })
    return riders


def update_riders():
    # Load email template
    with open('email_welcome.txt', 'r') as f:
        email_template = f.read()
    
    # Load riders file
    with open('riders.json', 'r+') as f: 
        riders = json.loads(f.read())
        rider_ids = set(r['id'] for r in riders)
        
        # Add new riders
        for rider in get_riders():
            if rider['id'] not in rider_ids:
                # Add new rider
                riders.append(rider)
                rider_ids.add(rider['id'])
                
                # Send welcome email to rider
                send_email_to_rider(
                    rider=rider,
                    subject='Triple Crown for Heart: Donation Page',
                    template=email_template)
                
                # Remove rider email from JSON
                del rider['email']
        
        # Sort by last name, then first name
        riders.sort(key=lambda r: r['last_name'])
        riders.sort(key=lambda r: r['first_name'])
        
        # Write updated file
        f.seek(0)
        f.write(json.dumps(riders, indent=4, sort_keys=True))
        f.truncate()


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
        METHOD='TransactionSearch', STARTDATE='2015-05-01T00:00:00Z')
    
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


def get_donation_ids():
    transactions = paypal_transactionsearch()
    donation_ids = [
        txn['L_TRANSACTIONID'] for txn in transactions 
        if txn['L_TYPE'] == 'Donation']
    return donation_ids
    
    
def update_donations():
    # Load email templates
    with open('email_donor.txt', 'r') as f:
        email_donor = f.read()
        
    with open('email_donation_notify.txt', 'r') as f:
        email_donation_notify = f.read()
        
    # Update donations file
    with open('donations.json', 'r+') as f: 
        donations = json.loads(f.read())
        donation_ids = set(d['id'] for d in donations)
        
        # Load rider ids (to get emails)
        riders = {r['id']: r for r in get_riders()}
        
        # Check for new donations
        for txn_id in get_donation_ids():
            # Don't update existing donations (PayPal API is slow)
            donation_id = hash_id(txn_id)
            if donation_id in donation_ids:
                continue
            
            # Fetch donation data
            donation = paypal_transactiondetails(txn_id)
            rider_id = donation.get('L_NUMBER0', None)
            
            # Load custom field
            custom = donation.get('CUSTOM', '{}')
            try:
                custom = json.loads(custom)
            except:
                custom = {}
            donor = custom.get('name') or 'Anonymous'
            message = custom.get('message', '')
            
            # Update donations
            donations.append({
                'id': donation_id,
                'to': rider_id,
                'from': donor,
                'amount': float(donation['AMT']),
                'message': message
            })
            
            # Send email to donor
            send_email(
                to=donation['EMAIL'],
                subject='Triple Crown for Heart: Donation',
                text=email_donor)
                
            # Send email to rider
            rider = riders.get(rider_id)
            if rider:
                send_email_to_rider(
                    rider=rider,
                    subject='Donation made by: ' + donor,
                    template=email_donation_notify)
        
        # Write updated file
        f.seek(0)
        f.write(json.dumps(donations, indent=4, sort_keys=True))
        f.truncate()


def send_email(to, subject, text):
    print('Sending email to: ' + to)
    return requests.post(
        "https://api.mailgun.net/v3/mg.triplecrownforheart.ca/messages",
        auth=("api", secrets.mailgun_api_key),
        data={
            "from": "Triple Crown for Heart Donations <donate@mg.triplecrownforheart.ca>",
            "to": [to],
            "subject": subject,
            "text": text
        })


def send_email_to_rider(rider, subject, template):
    donation_link = 'http://donate.triplecrownforheart.ca/#' + rider['id']
    text = (template
        .replace('[DONATION_LINK]', donation_link))
    return send_email(
        to=rider['email'],
        subject=subject,
        text=text)


if __name__ == '__main__':
    pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(get_riders())
    #pp.pprint(paypal_transactionsearch())
    #pp.pprint(paypal_transactiondetails())
    #pp.pprint(get_donation_ids())
    #pp.pprint(paypal_transactiondetails(secrets.paypal_example_txn))
    
    #response = send_email('csytan@gmail.com', 'hi chris', 'testing')
    
    #exit()
    print('Updating riders')
    update_riders()
    print('Updating donations')
    update_donations()



