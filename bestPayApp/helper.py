import json
import secrets
from datetime import datetime
from time import sleep

import requests
from decouple import config
from django.contrib import messages
from django.shortcuts import redirect
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from bestPayApp import models

mtn_codes = {
    0.5: 'data_bundle_1',
    1: 'data_bundle_2',
    3: 'data_bundle_3',
    10: 'data_bundle_4',
    20: 'flexi_data_bundle',
    40: 'flexi_data_bundle',
    60: 'flexi_data_bundle',
    80: 'flexi_data_bundle',
    100: 'flexi_data_bundle',
    120: 'flexi_data_bundle',
    150: 'flexi_data_bundle',
    200: 'flexi_data_bundle',
    250: 'flexi_data_bundle',
    299: 'flexi_data_bundle'
}

ishare_map = {
    3.5: 500,
    4.5: 1000,
    7.5: 2000,
    10.5: 3000,
    12.5: 4000,
    15.5: 5000,
    18.5: 6000,
    22.5: 7000,
    25.5: 8000,
    30.5: 10000,
    45.5: 15000,
    61: 20000,
    76: 25000,
    91: 30000,
    121: 40000,
    146: 50000,
    286: 100000,
    561: 200000
}


wallet_ishare_map = {
    3: 50,
    4: 1000,
    7: 2000,
    10: 3000,
    12: 4000,
    15: 5000,
    18: 6000,
    22: 7000,
    25: 8000,
    30: 10000,
    45: 15000,
    61: 20000,
    76: 25000,
    91: 30000,
    121: 40000,
    146: 50000,
    286: 100000,
    561: 200000
}

other_mtn_codes = {
    '1.09': 'kokrokoo_bundle_1',
    '1': 'video_bundle_1',
    '5': 'video_bundle_2',
    '10': 'video_bundle_3',
    '1s': 'social_media_bundle_1',
    '5s': 'social_media_bundle_2',
    '10s': 'social_media_bundle_3'
}


def send_ishare_bundle(current_user, phone_number, bundle):
    print("in send bundle")
    url = "https://backend.boldassure.net:445/live/api/context/business/transaction/new-transaction"

    payload = json.dumps({
        "accountNo": f"233{str(current_user.phone)}",
        "accountFirstName": current_user.first_name,
        "accountLastName": current_user.last_name,
        "accountMsisdn": phone_number,
        "accountEmail": current_user.email,
        "accountVoiceBalance": 0,
        "accountDataBalance": float(bundle),
        "accountCashBalance": 0,
        "active": True
    })

    headers = {
        'Authorization': config("BEARER_TOKEN"),
        'Content-Type': 'application/json'
    }
    print("here")
    session = requests.Session()
    retry = Retry(connect=15, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)

    response = session.post(url, headers=headers, data=payload)
    print(response)
    print("after response")

    parsed = response.json()

    print(parsed)

    # response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.json())
    return response

    # if response.status_code == 200:
    #     data = response.json()
    #     print(data)
    #     batch_id = data["batchId"]
    #     print(type(batch_id))
    #     print(batch_id)
    #
    #     new_ishare_bundle_transaction = models.IShareBundleTransaction.objects.create(
    #         user=current_user,
    #         email=current_user.email,
    #         bundle_number=phone_number,
    #         offer=f"{phone_number}-{bundle}",
    #         batch_id=batch_id,
    #         reference=client_ref,
    #         transaction_status="Success",
    #     )
    #     new_ishare_bundle_transaction.save()
    #     receiver_message = f"Your bundle purchase has been completed successfully. {bundle}MB has been credited to you by {current_user.phone}.\nReference: {batch_id}\n"
    #     sms_message = f"Hello @{current_user.username}. Your bundle purchase has been completed successfully. {bundle}MB has been credited to {phone_number}.\nReference: {batch_id}\nThank you for using BestPay.\n\nThe BestPayTeam."
    #     sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{current_user.phone}&from=BESTPAY GH&sms={sms_message}"
    #     response = requests.request("GET", url=sms_url)
    #     print(response.status_code)
    #     print(response.text)
    #     r_sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to={phone_number}&from=Bundle&sms={receiver_message}"
    #     response = requests.request("GET", url=r_sms_url)
    #     print(response.text)
    #     return redirect('thank_you')
    # else:
    #     new_ishare_bundle_transaction = models.IShareBundleTransaction.objects.create(
    #         user=current_user,
    #         email=current_user.email,
    #         bundle_number=phone_number,
    #         offer=f"{phone_number}-{bundle}MB",
    #         batch_id='failed',
    #         reference=client_ref,
    #         message="Airtime status code was not 200",
    #         transaction_status="Failed"
    #     )
    #     new_ishare_bundle_transaction.save()
    #     print(response.json())
    #     print("Not 200 error")
    #     sms_message = f"Hello @{current_user.username}. Your bundle purchase was not successful. You tried crediting {phone_number} with {bundle}MB.\nReference:{top_batch_id}\nContact Support for assistance.\n\nThe BestPayTeam."
    #     sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{current_user.phone}&from=BESTPAY GH&sms={sms_message}"
    #     response = requests.request("GET", url=sms_url)
    #     print(response.status_code)
    #     print(response.text)
    #     return redirect("failed")


def paystack_ref_generator():
    now_time = datetime.now().strftime('%H%M%S')
    secret = secrets.token_hex(2)

    return f"{now_time}{secret}".upper()


def verify_paystack_transaction(reference):
    print("verifying")
    url = f"https://api.paystack.co/transaction/verify/{reference}"

    headers = {
        "Authorization": config("PAYSTACK_SECRET_KEY")
    }

    response = requests.request("GET", url, headers=headers)

    print(response.json())

    return response


def generate_amount_for_other_mtn_codes(code):
    if code == '1.09':
        return 1.09
    elif code == '1':
        return 1
    elif code == '5':
        return 5
    elif code == '10':
        return 10
    elif code == '1s':
        return 1
    elif code == '5s':
        return 5
    elif code == '10s':
        return 10


voda_codes = {
    0.5: 'DATANVSTRDLY',
    1: 'DATANVDR1DLY',
    2: 'DATANVCHTDLY',
    5: 'DATANVDR5WLY',
    10: 'DATANVDBDL1',
    20: 'DATANVDBDL2',
    50: 'DATANVDBDL3',
    100: 'DATANVDBDL4',
    200: 'DATANVDBDL5',
    300: 'DATANVDBDL6',
    400: 'DATANVDBDL7'
}

at_codes = {
    1: 'DATA1',
    2: 'DATA2',
    5: 'DATA5',
    10: 'DATA10',
    20: 'DATA20',
    50: 'DATA50',
    100: 'DATA100',
    300: 'DATA300',
    350: 'DATA350',
    400: 'DATA400'
}

sk_codes = {
    3: 'SK3',
    5: 'SK5',
    6: 'SK6',
    10: 'SK10',
    11: 'SK11',
    15: 'SK15',
    20: 'SK20',
    50: 'SK50',
}


def ref_generator(number):
    now_time = datetime.now().strftime('%H%M%S')
    secret = secrets.token_hex(number)

    return f"BP{now_time}{secret}".upper()


def trim_amount(amount):
    if amount == 0.50:
        percentage = 0.01
        return amount - percentage
    elif amount == 1.09:
        percentage = 0.1
        return amount - percentage
    elif amount == 1.00:
        percentage = 0.01
        return amount - percentage
    elif 2 <= amount <= 10:
        percentage = 0.10
        return amount - percentage
    elif 11 <= amount <= 50:
        percentage = 0.50
        return amount - percentage
    else:
        return amount


def execute_payment(amount_to_be_charged, client_ref, provider, return_url):
    url = "https://payproxyapi.hubtel.com/items/initiate"

    payload = json.dumps({
        "totalAmount": amount_to_be_charged,
        "description": f"{provider}",
        "callbackUrl": 'https://webhook.site/d53f5c53-eaba-4139-ad27-fb05b0a7be7f',
        "returnUrl": f'{return_url}',
        "cancellationUrl": 'https://www.bestpaygh.com/services',
        "merchantAccountNumber": "2017101",
        "clientReference": client_ref
    })
    headers = {
        'Authorization': config("HUBTEL_API_KEY"),
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response


def airtime_description(client_ref):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        "api-key": config("API_KEY")
    }

    token_id = "9125cb31-9481-47ad-972f-d1d7765a5957"
    r = requests.get('https://webhook.site/token/9125cb31-9481-47ad-972f-d1d7765a5957/requests', headers=headers)

    for request in r.json()['data']:
        print(request)
        content = json.loads(request["content"])
        ref = content["Data"]["ClientReference"]
        if ref == client_ref:
            description = content["Data"]["Description"]
            print(description)
            return description


def url_provider(provider):
    if provider == "1":
        return "https://cs.hubtel.com/commissionservices/2016884/fdd76c884e614b1c8f669a3207b09a98"
    elif provider == "2":
        return "https://cs.hubtel.com/commissionservices/2016884/dae2142eb5a14c298eace60240c09e4b"
    elif provider == "3":
        return "https://cs.hubtel.com/commissionservices/2016884/f4be83ad74c742e185224fdae1304800"
    elif provider == "4":
        return "https://cs.hubtel.com/commissionservices/2016884/47d88e88f50f47468a34a14ac73e8ab5"


def airtime_provider_string(provider):
    if provider == "1":
        return "MTN"
    elif provider == "2":
        return "AirtelTigo"
    elif provider == "3":
        return "Vodafone"
    elif provider == "4":
        return "Glo"


def tv_provider_url(provider):
    if provider == "DSTV":
        return "https://cs.hubtel.com/commissionservices/2016884/297a96656b5846ad8b00d5d41b256ea7"
    if provider == "GOTV":
        return "https://cs.hubtel.com/commissionservices/2016884/e6ceac7f3880435cb30b048e9617eb41"
    if provider == "STARTIMES":
        return "https://cs.hubtel.com/commissionservices/2016884/6598652d34ea4112949c93c079c501ce"


def data_needed_from_model(keyword, user):
    if keyword == "mtn_bundles":
        model_data = models.MTNBundleTransaction.objects.filter(user=user).order_by('transaction_date').reverse()
        return {'model_data': model_data, 'heading': "MTN Bundles"}
    elif keyword == "mtn_other_bundles":
        model_data = models.OtherMTNBundleTransaction.objects.filter(user=user).order_by('transaction_date').reverse()
        return {'model_data': model_data, 'heading': "MTN Other Bundles"}
    elif keyword == "airteltigo_bundles":
        model_data = models.AirtelTigoBundleTransaction.objects.filter(user=user).order_by('transaction_date').reverse()
        return {'model_data': model_data, 'heading': "AirtelTigo Bundles"}
    elif keyword == "airteltigo_sika_kokoo":
        model_data = models.SikaKokooBundleTransaction.objects.filter(user=user).order_by('transaction_date').reverse()
        return {'model_data': model_data, 'heading': "AirtelTigo Sika Kokoo Bundles"}
    elif keyword == "vodafone_bundles":
        model_data = models.VodafoneBundleTransaction.objects.filter(user=user).order_by('transaction_date').reverse()
        return {'model_data': model_data, 'heading': "Vodafone Bundles"}
    elif keyword == "tv_subscriptions":
        model_data = models.TvTransaction.objects.filter(user=user).order_by('transaction_date').reverse()
        return {'model_data': model_data, 'heading': "TV Subscriptions"}
    elif keyword == "ishare_bundles":
        model_data = models.IShareBundleTransaction.objects.filter(user=user).order_by('transaction_date').reverse()
        return {'model_data': model_data, 'heading': 'Flexi Bundles'}


def check_network(phone_number):
    if phone_number:
        if str(phone_number)[4] == "4" or str(phone_number)[4] == "5" or str(phone_number)[4] == "9":
            return f"https://cs.hubtel.com/commissionservices/2016884/3e0841e70afc42fb97d13d19abd36384?destination={phone_number}"
        elif str(phone_number)[4] == "7" or str(phone_number)[4] == "6":
            return f"https://cs.hubtel.com/commissionservices/2016884/0d542e644a4440a3ae122adcfbade818?destination={phone_number}"
        elif str(phone_number)[4] == "0":
            return f"https://cs.hubtel.com/commissionservices/2016884/8767ecd553a7415e96c22eb9adae2879?destination={phone_number}"


def display_name(phone_number):
    url = check_network(phone_number)

    payload = json.dumps({
        "destination": phone_number
    })

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': config("HUBTEL_API_KEY")
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    data = response.json()
    customer_name = data["Data"][0]["Value"]
    return customer_name


def balance_check_url(provider, account_number):
    if provider == "DSTV":
        return f"https://cs.hubtel.com/commissionservices/2016884/297a96656b5846ad8b00d5d41b256ea7?destination={account_number}"
    if provider == "GOTV":
        return f"https://cs.hubtel.com/commissionservices/2016884/e6ceac7f3880435cb30b048e9617eb41?destination={account_number}"
    if provider == "STARTIMES":
        return f"https://cs.hubtel.com/commissionservices/2016884/6598652d34ea4112949c93c079c501ce?destination={account_number}"


def get_balance(account_number, provider):
    url = balance_check_url(provider, account_number)

    payload = json.dumps({
        "destination": account_number
    })
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': config("HUBTEL_API_KEY")
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.json()


def ishare_verification(batch_id):

    url = f"https://backend.boldassure.net:445/live/api/context/business/airteltigo-gh/ishare/tranx-status/{batch_id}"

    payload = {}
    headers = {
        'Authorization': config("BEARER_TOKEN")
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        json_data = response.json()
        print(json_data)
        return json_data
    else:
        return False


def ishare_after_verification(request, current_user, payment, bundle):
    ishare_response = send_ishare_bundle(request.user, payment.payment_number, bundle)
    if ishare_response.status_code == 200:
        data = ishare_response.json()
        batch_id = data["batchId"]
        sleep(10)
        verified = ishare_verification(batch_id)
        if verified is not False:
            code = verified["flexiIshareTranxStatus"]["flexiIshareTranxStatusResult"]["apiResponse"]["responseCode"]
            if code == '200':
                new_ishare_bundle_transaction = models.IShareBundleTransaction.objects.create(
                    user=current_user,
                    email=current_user.email,
                    bundle_number=payment.payment_number,
                    offer=f"{bundle}MB",
                    reference=payment.reference,
                    batch_id=batch_id,
                    message="200 Status Code",
                    transaction_status="Successful"
                )
                new_ishare_bundle_transaction.save()
                receiver_message = f"Your bundle purchase has been completed successfully. {bundle}MB has been credited to you by {current_user.phone}.\nReference: {batch_id}\n"
                sms_message = f"Hello @{request.user.username}. Your bundle purchase has been completed successfully. {bundle}MB has been credited to {payment.payment_number}.\nReference: {batch_id}\nThank you for using BestPay.\n\nThe BestPayTeam."
                sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{current_user.phone}&from=BESTPAY GH&sms={sms_message}"
                try:
                    response = requests.request("GET", url=sms_url)
                    print(response.status_code)
                    print(response.text)
                    r_sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to={payment.payment_number}&from=Bundle&sms={receiver_message}"
                    response = requests.request("GET", url=r_sms_url)
                    print(response.text)
                    return redirect("thank_you")
                except:
                    return redirect("thank_you")
            else:
                new_ishare_bundle_transaction = models.IShareBundleTransaction.objects.create(
                    user=current_user,
                    email=current_user.email,
                    bundle_number=payment.payment_number,
                    offer=f"{bundle}MB",
                    reference=payment.reference,
                    batch_id=batch_id,
                    message="Status code was 200 but query showed the transaction was unsuccessful",
                    transaction_status="Successful"
                )
                new_ishare_bundle_transaction.save()
                return redirect('thank_you')
        else:
            new_ishare_bundle_transaction = models.IShareBundleTransaction.objects.create(
                user=current_user,
                email=current_user.email,
                bundle_number=payment.payment_number,
                offer=f"{bundle}MB",
                reference=payment.reference,
                batch_id='Successful',
                message="Status code was 200 but query did not return anything useful",
                transaction_status="Success"
            )
            new_ishare_bundle_transaction.save()
            messages.info(request, "Transaction Completed")
            return redirect('thank_you')

    else:
        new_ishare_bundle_transaction = models.IShareBundleTransaction.objects.create(
            user=current_user,
            email=current_user.email,
            bundle_number=payment.payment_number,
            offer=f"{bundle}MB",
            reference=payment.reference,
            batch_id='Failed',
            message="Status code was not 200",
            transaction_status="Failed"
        )
        new_ishare_bundle_transaction.save()
        print("Not 200 error")
        try:
            sms_message = f"Hello @{current_user.username}. Your bundle purchase was not successful. You tried crediting {payment.payment_number} with {bundle}MB.\nReference:{payment.reference}\nContact Support for assistance.\n\nThe BestPayTeam."
            sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{current_user.phone}&from=BESTPAY GH&sms={sms_message}"
            response = requests.request("GET", url=sms_url)
            print(response.status_code)
            print(response.text)
            return redirect('failed')
        except:
            return redirect('failed')
