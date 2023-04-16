from decouple import config, UndefinedValueError
import requests
from requests_oauthlib import OAuth1
import json
import base64
import pytz
from datetime import datetime

base_url= config("WORDPRESS_BASE_URL")
app_user = config("WORDPRESS_USER")
app_pass = config("WORDPRESS_APP_PASSWORD")
form_id = config("WORDPRESS_FORM_ID")

oauth = OAuth1(
    client_key=app_user,
    client_secret=app_pass,
)

headers = {'Content-type': 'application/json'}

def getFormFields(formid):
    url = base_url + f"wp-json/gf/v2/forms/{formid}"

    response = requests.get(url, auth=oauth, headers=headers)

    form_data = json.loads(response.text)

    fields = form_data['fields']

    return fields

def getFormFieldChoices(fields, fieldid):
    field_data = None

    for field in fields:
        if field['id'] == fieldid:
            field_data = field
            break

    if field_data is None:
        return None

    # Get the choices for the field.
    choices = field_data['choices']

    return choices

    # Find the choice with matching text and return its value.
def getChoiceValueForText(choices, choice_text):
    for choice in choices:
        if normalizeChoice(choice['text']) == normalizeChoice(choice_text):
            return choice['value']

    # If no matching choice is found, return None.
    return None
    
# Normalize the string we search for (AO specific naming convention here)
def normalizeAO(dirty_data):
    dirty_data = dirty_data.replace("ao-", '')
    dirty_data = dirty_data.replace("bd-", '')
    dirty_data = dirty_data.replace("-", ' ')
    return dirty_data

def normalizeChoice(dirty_data):
    dirty_data = dirty_data.replace("the", '')
    dirty_data = dirty_data.replace("-", '')
    dirty_data = dirty_data.replace(" ", '')
    return dirty_data.strip().lower()

# Post the data to wordpress.  
#  date: str in 'MM/DD/YYYY' format
#  pax/qic: comma separated list of names
#  fngs: array of names
def postToWordpress(title, date, qic, ao, pax, fngs, backblast, preblast=False):
    ao = normalizeAO(ao)

    formFields = getFormFields(form_id)

    aochoices = getFormFieldChoices(formFields, 6)
    paxchoices = getFormFieldChoices(formFields, 13)

    # Get AO Id from gravity form
    ao_id = getChoiceValueForText(aochoices, ao)

    qicnames = [s.strip() for s in qic.split(',')]

    paxnames = [s.strip() for s in pax.split(',')]

    # Get pax ids from gravity forms
    paxids = []

    for paxname in paxnames:
        paxid = getChoiceValueForText(paxchoices, paxname)

        if paxid is not None:
            paxids.append(paxid)
        else:
            paxids.append(paxname)

    for qicname in qicnames:
        paxid = getChoiceValueForText(paxchoices, qicname)

        if paxid is not None:
            paxids.append(paxid)
        else:
            paxids.append(qicname)

    post = {
        'input_8': title,
        'input_16': backblast,
        'input_6': ao_id, 
        'input_10': date,
        'input_13': paxids,
        'input_11': qic,
        'input_12': len(paxids),
        'input_14': len(fngs),
        'input_15': ", ".join(fngs),
    }

    # # Serialize the object to a JSON-formatted string.
    # json_string = json.dumps(post, indent=4)

    # # Print the JSON-formatted string to the console.
    # print(json_string)

    # print(str(ao_id))
    # print(str(tags))
    #response = requests.get(url + "&status=draft", headers=headers)
    url = base_url + f"wp-json/gf/v2/forms/{form_id}/submissions"
    response = requests.post(url, auth=oauth, headers=headers, json=post)
    
    # print(response.content)
    
    response_json = json.loads(response.content.decode('utf-8'))

    return response_json
    
