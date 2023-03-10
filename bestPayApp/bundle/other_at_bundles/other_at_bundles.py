from http.client import HTTPResponse
import json
from time import sleep

import requests
from decouple import config
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from bestPayApp.forms import SikaKokooBundleForm, IShareBundleForm
from bestPayApp import helper, models


def sika_kokoo(request):
    form = SikaKokooBundleForm()
    if request.method == "POST":
        if request.user.is_authenticated:
            form = SikaKokooBundleForm(request.POST)
            if form.is_valid():
                phone_number = form.cleaned_data["phone_number"]
                offer_chosen = str(form.cleaned_data["offers"])

                sk_codes = helper.sk_codes
                value = f"\"{sk_codes[offer_chosen]}\""
                amount = float(offer_chosen)
                amount_to_be_charged = helper.trim_amount(float(offer_chosen))
                client_ref = helper.ref_generator(2)
                provider = "AirtelTigo Sika Kokoo Bundle"
                return_url = f"https://www.bestpaygh.com/send_sk_bundle/{client_ref}/{phone_number}/{amount}/{value}"

                response = helper.execute_payment(amount_to_be_charged, client_ref,
                                                  provider, return_url)
                print(response.json())
                data = response.json()

                if data["status"] == "Success":
                    checkout = data['data']['checkoutUrl']
                    return redirect(checkout)
                else:
                    return redirect('failed')
        else:
            messages.warning(request, "Login to continue")
            return redirect('login')
    context = {'form': form}
    return render(request, 'layouts/services/at-sika-kokoo.html', context=context)


def send_sk_bundle(request, client_ref, phone_number, amount, value):
    payment = models.Payment.objects.filter(reference=client_ref)
    if payment:
        new_intruder = models.Intruder.objects.create(
            user=request.user,
            reference=client_ref,
            message="Payment already exists and the reference has expired. User tried using it again."
        )
        new_intruder.save()
        return redirect('intruder')
    current_user = request.user
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        "api-key": config("API_KEY"),
    }
    webhook_response = requests.request("GET",
                                        "https://webhook.site/token/d53f5c53-eaba-4139-ad27-fb05b0a7be7f/"
                                        "requests?sorting=newest",
                                        headers=headers)

    for request in webhook_response.json()['data']:
        try:
            try:
                content = json.loads(request["content"])
            except ValueError:
                return redirect(
                    f'https://www.bestpaygh.com/send_sk_bundle/{client_ref}/'
                    f'{phone_number}/{amount}/{value}')
            status = content["Status"]
            ref = content["Data"]["ClientReference"]
        except KeyError:
            return redirect("failed")
        if ref == client_ref and status == "Success":
            momo_number = content["Data"]["CustomerPhoneNumber"]
            amount = content["Data"]["Amount"]
            payment_description = content["Data"]["Description"]
            print(f"{status}--{ref}--{momo_number}--{amount}--{payment_description}")
            payment = models.Payment.objects.filter(user=current_user, reference=client_ref, payment_visited=True)
            if payment:
                new_intruder = models.Intruder.objects.create(
                    user=current_user,
                    reference=client_ref,
                    message="Payment already exists and the reference has expired. User tried using it again."
                )
                new_intruder.save()
                return redirect('intruder')
            else:
                new_payment = models.Payment.objects.create(
                    user=current_user,
                    reference=client_ref,
                    payment_number=momo_number,
                    amount=amount,
                    payment_description=payment_description,
                    transaction_status=status,
                    payment_visited=True,
                    message="Payment verified successfully",
                )
                new_payment.save()
                url = "https://cs.hubtel.com/commissionservices/2016884/06abd92da459428496967612463575ca"

                reference = f"\"{client_ref}\""

                payload = "{\r\n    \"Destination\": " + str(phone_number) + ",\r\n    \"Amount\": " + str(amount) + ",\r\n    \"CallbackUrl\": \"https://webhook.site/33d27e7d-6dd5-4899-b702-6c9022bea8c7\",\r\n    \"ClientReference\": " + str(reference) + ",\r\n    \"Extradata\" : {\r\n        \"bundle\" : " + value + "\r\n    }\r\n}\r\n"
                headers = {
                    'Authorization': config("HUBTEL_API_KEY"),
                    'Content-Type': 'text/plain'
                }

                response = requests.request("POST", url, headers=headers, data=payload)

                if response.status_code == 200:
                    desc = helper.airtime_description(client_ref)
                    new_sk_bundle_transaction = models.SikaKokooBundleTransaction.objects.create(
                        user=current_user,
                        email=current_user.email,
                        bundle_number=phone_number,
                        offer=f"{amount}-{value}",
                        reference=client_ref,
                        transaction_status="Success",
                        description=desc
                    )
                    new_sk_bundle_transaction.save()
                    return redirect('thank_you')
                else:
                    print(response.json())
                    print("Not 200 error")
                    new_sk_bundle_transaction = models.SikaKokooBundleTransaction.objects.create(
                        user=current_user,
                        email=current_user.email,
                        bundle_number=phone_number,
                        offer=f"{amount}-{value}",
                        reference=client_ref,
                        transaction_status="Failed"
                    )
                    new_sk_bundle_transaction.save()
                    return redirect("failed")
        else:
            new_sk_bundle_transaction = models.SikaKokooBundleTransaction.objects.create(
                user=current_user,
                email=current_user.email,
                bundle_number=phone_number,
                offer=f"{amount}-{value}",
                reference=client_ref,
                transaction_status="Failed"
            )
            new_sk_bundle_transaction.save()
            print("last error")
            return redirect('failed')


def ishare_bundle(request):
    form = IShareBundleForm()
    if request.method == "POST":
        if request.user.is_authenticated:
            form = IShareBundleForm(request.POST)
            if form.is_valid():
                phone_number = form.cleaned_data["phone_number"]
                offer_chosen = form.cleaned_data["offers"]
                amount = float(offer_chosen)

                ishare_map = helper.ishare_map
                bundle = ishare_map[amount]

                amount_to_be_charged = helper.trim_amount(float(offer_chosen))
                client_ref = helper.ref_generator(2)
                provider = "IShare Bundle"
                return_url = f"https://www.bestpaygh.com/send_ishare_bundle/{client_ref}/{phone_number}/{bundle}"

                response = helper.execute_payment(amount, client_ref,
                                                  provider, return_url)
                try:
                    print(response.json())
                    data = response.json()
                    print(data)
                    if data["status"] == "Success":
                        checkout = data['data']['checkoutUrl']
                        return redirect(checkout)
                    else:
                        return redirect('failed')
                except ValueError:
                    return redirect("error")    
        else:
            messages.warning(request, "Login to continue")
            return redirect('login')
    context = {'form': form}
    return render(request, 'layouts/services/ishare.html', context=context)


def send_ishare_bundle(request, client_ref, phone_number, bundle):
    sleep(5)
    global ref_needed
    global status_needed
    global content_needed
    payment = models.Payment.objects.filter(reference=client_ref)
    if payment:
        new_intruder = models.Intruder.objects.create(
            user=request.user,
            reference=client_ref,
            message="Payment already exists and the reference has expired. User tried using it again."
        )
        new_intruder.save()
        return redirect('intruder')
    current_user = request.user
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
            content_needed = content
            break

    if ref_needed == client_ref and status_needed == "Success":
        momo_number = content_needed["Data"]["CustomerPhoneNumber"]
        amount = content_needed["Data"]["Amount"]
        payment_description = content_needed["Data"]["Description"]
        print(f"{status_needed}--{ref_needed}--{momo_number}--{amount}--{payment_description}")
        payment = models.Payment.objects.filter(user=current_user, reference=client_ref, payment_visited=True)
        if payment:
            new_intruder = models.Intruder.objects.create(
                user=current_user,
                reference=client_ref,
                message="Payment already exists and the reference has expired. User tried using it again."
            )
            new_intruder.save()
            return redirect("intruder")
        else:
            new_payment = models.Payment.objects.create(
                user=current_user,
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
                "accountNo": f"233{str(current_user.phone)}",
                "accountFirstName": current_user.first_name,
                "accountLastName": current_user.last_name,
                "accountMsisdn": str(phone_number),
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

            response = requests.request("POST", url, headers=headers, data=payload)
            json_data = response.json()
            top_batch_id = json_data["batchId"]

            if response.status_code == 200:
                data = response.json()
                print(data)
                batch_id = data["batchId"]
                print(type(batch_id))
                print(batch_id)

                new_ishare_bundle_transaction = models.IShareBundleTransaction.objects.create(
                    user=current_user,
                    email=current_user.email,
                    bundle_number=phone_number,
                    offer=f"{phone_number}-{bundle}",
                    batch_id=batch_id,
                    reference=client_ref,
                    transaction_status="Success",
                )
                new_ishare_bundle_transaction.save()
                receiver_message = f"Your bundle purchase has been completed successfully. {bundle}MB has been credited to you by {current_user.phone}.\nReference: {batch_id}\n"
                sms_message = f"Hello @{current_user.username}. Your bundle purchase has been completed successfully. {bundle}MB has been credited to {phone_number}.\nReference: {batch_id}\nThank you for using BestPay.\n\nThe BestPayTeam."
                sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{current_user.phone}&from=BestPay&sms={sms_message}"
                response = requests.request("GET", url=sms_url)
                print(response.status_code)
                print(response.text)
                r_sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to={phone_number}&from=Bundle&sms={receiver_message}"
                response = requests.request("GET", url=r_sms_url)
                print(response.text)
                return redirect('thank_you')
            else:
                new_ishare_bundle_transaction = models.IShareBundleTransaction.objects.create(
                    user=current_user,
                    email=current_user.email,
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
                sms_message = f"Hello @{current_user.username}. Your bundle purchase was not successful. You tried crediting {phone_number} with {bundle}MB.\nReference:{top_batch_id}\nContact Support for assistance.\n\nThe BestPayTeam."
                sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{current_user.phone}&from=BestPay&sms={sms_message}"
                response = requests.request("GET", url=sms_url)
                print(response.status_code)
                print(response.text)
                return redirect("failed")
    else:
        new_ishare_bundle_transaction = models.IShareBundleTransaction.objects.create(
            user=current_user,
            email=current_user.email,
            bundle_number=phone_number,
            offer=f"{phone_number}-{bundle}MB",
            batch_id="failed",
            reference=client_ref,
            message="Couldn't validate mobile money transaction",
            transaction_status="Failed"
        )
        new_ishare_bundle_transaction.save()
        sms_message = f"Hello @{current_user.username}. Your bundle purchase was not successful. You tried crediting {phone_number} with {bundle}MB.\nReference:{client_ref}\nContact Support for assistance.\n\nThe BestPayTeam."
        sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{current_user.phone}&from=BestPay&sms={sms_message}"
        response = requests.request("GET", url=sms_url)
        print(response.text)
        print("last error")
        return redirect('failed')
