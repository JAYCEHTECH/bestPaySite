from time import sleep
from bestPayApp import models
from django.shortcuts import render, redirect
from decouple import config
import json
import requests


def send_ishare_bundle(username, first_name, last_name, account_msisdn, user_number, email, client_ref, phone_number, bundle):
    sleep(5)
    global ref_needed
    global status_needed
    global content_needed
    payment = models.Payment.objects.filter(reference=client_ref)
    if payment:
        return redirect('intruder')
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        "api-key": config("API_KEY"),
    }
    webhook_response = requests.request("GET",
                                        "https://webhook.site/token/d53f5c53-eaba-4139-ad27-fb05b0a7be7f/"
                                        "requests?sorting=newest",
                                        headers=headers)
    json_webhook_response = webhook_response.json()['data']
    txns_list = []
    ref_list = []
    for txn in json_webhook_response:
        txns_list.append(txn)
    for item in txns_list:
        content = json.loads(item["content"])
        content_needed = content
        ref = content["Data"]["ClientReference"]
        status = content["Status"]
        print(ref)
        print(status)
        if ref == client_ref:
            print("========================================================")
            print("========================================================")
            print("=======================Ref=================================")
            print(ref)
            print("=====================Client Ref================================")
            print(client_ref)
            ref_needed = ref
            status_needed = status
            break

    if ref_needed == client_ref and status_needed == "Success":
        momo_number = content_needed["Data"]["CustomerPhoneNumber"]
        amount = content_needed["Data"]["Amount"]
        payment_description = content_needed["Data"]["Description"]
        print(f"{status_needed}--{ref_needed}--{momo_number}--{amount}--{payment_description}")
        payment = models.AppPayment.objects.filter(username=username, reference=client_ref, payment_visited=True)
        if payment:
            return redirect("intruder")
        else:
            new_payment = models.AppPayment.objects.create(
                username=username,
                reference=client_ref,
                payment_number=momo_number,
                amount=amount,
                payment_description=payment_description,
                transaction_status=status_needed,
                payment_visited=True,
                message="Payment verified successfully",
            )
            new_payment.save()
            url = "https://lab.xardtek.com/npe/api/context/business/transaction/new-transaction"

            payload = json.dumps({
                "accountNo": f"233{user_number}",
                "accountFirstName": first_name,
                "accountLastName": last_name,
                "accountMsisdn": account_msisdn,
                "accountEmail": email,
                "accountVoiceBalance": 0,
                "accountDataBalance": float(bundle),
                "accountCashBalance": 0,
                "active": True
            })

            headers = {
                'Authorization': config("BEARER_TOKEN"),
                'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            json_data = response.json()
            top_batch_id = json_data["batchId"]

            if response.status_code == 200:
                data = response.json()
                print(data)
                batch_id = data["batchId"]
                print(type(batch_id))
                print(batch_id)

                new_ishare_bundle_transaction = models.AppIShareBundleTransaction.objects.create(
                    username=username,
                    email=email,
                    bundle_number=phone_number,
                    offer=f"{phone_number}-{bundle}",
                    batch_id=batch_id,
                    reference=client_ref,
                    transaction_status="Success",
                )
                new_ishare_bundle_transaction.save()
                receiver_message = f"Your bundle purchase has been completed successfully. {bundle}MB has been credited to you by {user_number}.\nReference: {batch_id}\n"
                sms_message = f"Hello @{username}. Your bundle purchase has been completed successfully. {bundle}MB has been credited to {phone_number}.\nReference: {batch_id}\nThank you for using BestPay.\n\nThe BestPayTeam."
                sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{user_number}&from=BestPay&sms={sms_message}"
                response = requests.request("GET", url=sms_url)
                print(response.status_code)
                print(response.text)
                r_sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to={phone_number}&from=Bundle&sms={receiver_message}"
                response = requests.request("GET", url=r_sms_url)
                print(response.text)
                return redirect('thank_you')
            else:
                new_ishare_bundle_transaction = models.AppIShareBundleTransaction.objects.create(
                    username=username,
                    email=email,
                    bundle_number=phone_number,
                    offer=f"{phone_number}-{bundle}MB",
                    batch_id='failed',
                    reference=client_ref,
                    message="Airtime status code was not 200",
                    transaction_status="Failed"
                )
                new_ishare_bundle_transaction.save()
                print(response.json())
                print("Not 200 error")
                sms_message = f"Hello @{username}. Your bundle purchase was not successful. You tried crediting {phone_number} with {bundle}MB.\nReference:{top_batch_id}\nContact Support for assistance.\n\nThe BestPayTeam."
                sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{user_number}&from=BestPay&sms={sms_message}"
                response = requests.request("GET", url=sms_url)
                print(response.status_code)
                print(response.text)
                return redirect("failed")
    else:
        new_ishare_bundle_transaction = models.AppIShareBundleTransaction.objects.create(
            username=username,
            email=email,
            bundle_number=phone_number,
            offer=f"{phone_number}-{bundle}MB",
            batch_id="failed",
            reference=client_ref,
            message="Couldn't validate mobile money transaction",
            transaction_status="Failed"
        )
        new_ishare_bundle_transaction.save()
        sms_message = f"Hello @{username}. Your bundle purchase was not successful. You tried crediting {phone_number} with {bundle}MB.\nReference:{client_ref}\nContact Support for assistance.\n\nThe BestPayTeam."
        sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{user_number}&from=BestPay&sms={sms_message}"
        response = requests.request("GET", url=sms_url)
        print(response.text)
        print("last error")
        return redirect('failed')



