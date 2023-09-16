from http.client import HTTPResponse
import json
from time import sleep
from datetime import datetime

import requests
from asgiref.sync import sync_to_async
from decouple import config
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from requests.adapters import HTTPAdapter
from urllib3 import Retry

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

                payload = "{\r\n    \"Destination\": " + str(phone_number) + ",\r\n    \"Amount\": " + str(
                    amount) + ",\r\n    \"CallbackUrl\": \"https://webhook.site/33d27e7d-6dd5-4899-b702-6c9022bea8c7\",\r\n    \"ClientReference\": " + str(
                    reference) + ",\r\n    \"Extradata\" : {\r\n        \"bundle\" : " + value + "\r\n    }\r\n}\r\n"
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


@login_required(login_url='login')
def save_details(request):
    if request.method == "POST":
        phone_number = request.POST.get("phone")
        amount = float(request.POST.get("amount"))
        reference = request.POST.get("ref")
        ishare_map = helper.ishare_map
        bundle = ishare_map[amount]

        current_user = request.user

        new_transaction = models.IShareBundleTransaction.objects.create(
            user=request.user,
            email=current_user.email,
            bundle_number=phone_number,
            offer=f"{bundle}MB",
            reference=reference,
            batch_id="Null",
            transaction_status="Unfinished"
        )

        new_transaction.save()

        return JsonResponse({'status': 'True'})


@login_required(login_url='login')
def initiate_payment(request):
    status = models.Site.objects.filter(status=True).first()
    if status:
        form = IShareBundleForm()
        if request.method == "POST":
            form = IShareBundleForm(request.POST)
            if form.is_valid():
                amount = form.cleaned_data["offers"]
                phone_number = form.cleaned_data["phone_number"]

                print(amount)
                print(phone_number)

                pk = "pk_live_99e10d6f2512390f0960dbf9ac3a8163af13e275"

                payment = models.Payment.objects.create(amount=amount, user=request.user, payment_number=phone_number, payment_description="Ishare Payment")
                payment.save()

                reference = payment.reference

                if payment:
                    context = {
                        'payment': payment,
                        'reference_f': reference,
                        'field_values': request.POST,
                        'paystack_pub_key': pk,
                        'amount_value': payment.amount_value(),
                        'phone_number': phone_number,
                        'email': request.user.email,
                        'channel': 'ishare'
                    }
                    print("moved to make payment")
                    return render(request, 'layouts/services/make_payment.html', context)
                else:
                    return redirect('ishare_bundle')
            else:
                print("nope")
        context = {'form': form}
        return render(request, 'layouts/services/ishare.html', context=context)


# def pay_with_wallet(request):
#     if request.method == "POST":
#         user = models.CustomUser.objects.get(id=request.user.id)
#         phone_number = request.POST.get("phone")
#         amount = request.POST.get("amount")
#         reference = request.POST.get("reference")
#         if user.wallet is None:
#             return JsonResponse({'status': f'Your wallet balance is low. Top up to use wallet'})
#         elif user.wallet <= 0 or user.wallet < float(amount):
#             print(user.wallet)
#             return JsonResponse({'status': f'Your wallet balance is low. Top up to use wallet'})
#         print(phone_number)
#         print(amount)
#         print(reference)
#         bundle = helper.ishare_map[float(amount)]
#         print(bundle)
#         send_bundle_response = helper.send_ishare_bundle(request.user, phone_number, bundle)
#         data = send_bundle_response.json()
#         print(data)
#
#         sms_headers = {
#             'Authorization': 'Bearer 1050|VDqcCUHwCBEbjcMk32cbdOhCFlavpDhy6vfgM4jU',
#             'Content-Type': 'application/json'
#         }
#
#         sms_url = 'https://webapp.usmsgh.com/api/sms/send'
#         if send_bundle_response.status_code == 200:
#             data = send_bundle_response.json()
#             batch_id = data["batchId"]
#             new_ishare_bundle_transaction = models.IShareBundleTransaction.objects.create(
#                 user=request.user,
#                 email=request.user.email,
#                 bundle_number=phone_number,
#                 offer=f"{bundle}MB",
#                 reference=reference,
#                 batch_id=batch_id,
#                 message="200 Status Code",
#                 transaction_status="Successful"
#             )
#             new_ishare_bundle_transaction.save()
#             receiver_message = f"Your bundle purchase has been completed successfully. {bundle}MB has been credited to you by {request.user.phone}.\nReference: {batch_id}\n"
#             sms_message = f"Hello @{request.user.username}. Your bundle purchase has been completed successfully. {bundle}MB has been credited to {phone_number}.\nReference: {batch_id}\nThank you for using BestPay.\n\nThe BestPayTeam."
#             sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{request.user.phone}&from=BESTPAY GH&sms={sms_message}"
#             response = requests.request("GET", url=sms_url)
#             print(response.status_code)
#             print(response.text)
#             r_sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to={phone_number}&from=Bundle&sms={receiver_message}"
#             response = requests.request("GET", url=r_sms_url)
#             print(response.text)
#             return JsonResponse({'status': 'Transaction Completed Successfully', 'icon': 'success'})
#         else:
#             new_ishare_bundle_transaction = models.IShareBundleTransaction.objects.create(
#                 user=request.user,
#                 email=request.user.email,
#                 bundle_number=phone_number,
#                 offer=f"{bundle}MB",
#                 reference=reference,
#                 batch_id='Failed',
#                 message="Status code was not 200",
#                 transaction_status="Failed"
#             )
#             new_ishare_bundle_transaction.save()
#             print("Not 200 error")
#             sms_message = f"Hello @{request.user.username}. Your bundle purchase was not successful. You tried crediting {phone_number} with {bundle}MB.\nReference:{reference}\nContact Support for assistance.\n\nThe BestPayTeam."
#             sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{phone_number}&from=BESTPAY GH&sms={sms_message}"
#             response = requests.request("GET", url=sms_url)
#             print(response.status_code)
#             print(response.text)
#             return JsonResponse({'status': 'Something went wrong'})
#     return redirect('airtel-tigo')



@login_required(login_url='login')
def delete_unfinished(request):
    if request.method == "POST":
        reference = request.POST.get("reference")
        print(reference)
        delete_transaction = models.IShareBundleTransaction.objects.filter(reference=reference)
        if delete_transaction.exists():
            delete_transaction.delete()
            return redirect('ishare_bundle')
        else:
            return redirect('ishare_bundle')


@login_required(login_url='login')
def ishare_bundle(request):
    status = models.Site.objects.filter(status=True).first()
    if status:
        current_user = request.user
        form = IShareBundleForm()
        reference = helper.ref_generator(2)
        user_email = request.user.email
        if request.method == "POST":
            phone_number = request.POST.get("phone")
            amount = float(request.POST.get("amount"))
            reference = request.POST.get("reference")
            transaction = models.IShareBundleTransaction.objects.get(reference=reference)
            new_payment = models.Payment.objects.create(
                user=request.user,
                transaction_status="Completed",
                amount=amount,
                reference=reference,
                transaction_date=datetime.now()
            )
            new_payment.save()

            ishare_map = helper.ishare_map
            bundle = ishare_map[amount]

            transaction.transaction_status = "Unfinished"

            # new_transaction = models.IShareBundleTransaction.objects.create(
            #     user=request.user,
            #     email=current_user.email,
            #     bundle_number=phone_number,
            #     offer=f"{bundle}MB",
            #     reference=reference,
            #     batch_id="Null",
            #     transaction_status="Unfinished"
            # )
            transaction.save()

            send_bundle_response = helper.send_ishare_bundle(request.user, phone_number, bundle)

            if send_bundle_response.status_code == 200:
                data = send_bundle_response.json()
                batch_id = data["batchId"]
                transaction_to_be_updated = models.IShareBundleTransaction.objects.get(reference=reference)
                print(transaction_to_be_updated.transaction_status)
                transaction_to_be_updated.batch_id = batch_id
                transaction_to_be_updated.transaction_status = "Completed"
                transaction_to_be_updated.save()
                receiver_message = f"Your bundle purchase has been completed successfully. {bundle}MB has been credited to you by {current_user.phone}.\nReference: {batch_id}\n"
                sms_message = f"Hello @{current_user.username}. Your bundle purchase has been completed successfully. {bundle}MB has been credited to {phone_number}.\nReference: {batch_id}\nThank you for using BestPay.\n\nThe BestPayTeam."
                sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{current_user.phone}&from=BESTPAY GH&sms={sms_message}"
                response = requests.request("GET", url=sms_url)
                print(response.status_code)
                print(response.text)
                r_sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to={phone_number}&from=Bundle&sms={receiver_message}"
                response = requests.request("GET", url=r_sms_url)
                print(response.text)
                # return redirect("thank_you")
                return JsonResponse({'status': "Transaction completed Successfully", "icon": "success"})
            else:
                transaction_to_be_updated = models.IShareBundleTransaction.objects.get(reference=reference)
                print(transaction_to_be_updated.transaction_status)
                transaction_to_be_updated.transaction_status = "Failed"
                transaction_to_be_updated.message = "Status Code was not 200"
                transaction_to_be_updated.save()
                # new_ishare_bundle_transaction = models.IShareBundleTransaction.objects.create(
                #     user=current_user,
                #     email=current_user.email,
                #     bundle_number=phone_number,
                #     offer=f"{bundle}MB",
                #     reference=reference,
                #     batch_id='failed',
                #     message="Status code was not 200",
                #     transaction_status="Failed"
                # )
                # new_ishare_bundle_transaction.save()
                print("Not 200 error")
                sms_message = f"Hello @{current_user.username}. Your bundle purchase was not successful. You tried crediting {phone_number} with {bundle}MB.\nReference:{reference}\nContact Support for assistance.\n\nThe BestPayTeam."
                sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{current_user.phone}&from=BESTPAY GH&sms={sms_message}"
                response = requests.request("GET", url=sms_url)
                print(response.status_code)
                print(response.text)
                return JsonResponse({'status': "Transaction Failed", "icon": "error"})
        context = {'form': form, "ref": reference, "email": user_email}
        return render(request, 'layouts/services/ishare.html', context=context)
    else:
        return render(request, "layouts/maintenance.html")


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
            url = "https://backend.boldassure.net:445/live/api/context/business/transaction/new-transaction"

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
                sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{current_user.phone}&from=BESTPAY GH&sms={sms_message}"
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
                sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{current_user.phone}&from=BESTPAY GH&sms={sms_message}"
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
        sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{current_user.phone}&from=BESTPAY GH&sms={sms_message}"
        response = requests.request("GET", url=sms_url)
        print(response.text)
        print("last error")
        return redirect('failed')
