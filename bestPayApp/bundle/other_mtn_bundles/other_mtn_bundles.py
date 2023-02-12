import json

import requests
from decouple import config
from django.contrib import messages
from django.shortcuts import render, redirect
from bestPayApp.forms import OtherMTNBundleForm
from bestPayApp import helper, models


def other_mtn_bundles(request):
    form = OtherMTNBundleForm()
    if request.method == "POST":
        if request.user.is_authenticated:
            form = OtherMTNBundleForm(request.POST)
            if form.is_valid():
                phone_number = form.cleaned_data["phone_number"]
                offer_chosen = str(form.cleaned_data["offers"])

                other_mtn_codes = helper.other_mtn_codes
                value = f"\"{other_mtn_codes[offer_chosen]}\""
                amount = helper.generate_amount_for_other_mtn_codes(offer_chosen)
                amount_to_be_charged = helper.trim_amount(float(amount))
                client_ref = helper.ref_generator(2)
                provider = "Other MTN Bundle"
                return_url = f"https://www.bestpaygh.com/send_other_mtn_bundle/{client_ref}/{phone_number}/{amount}/{value}"

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
    return render(request, 'layouts/services/other_mtn_bundles.html', context=context)


def send_other_mtn_bundle(request, client_ref, phone_number, amount, value):
    current_user = request.user
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        "api-key": "8f56b7ea-e1d0-4ce7-ace0-162f7dc55a39"
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
                    f'https://www.bestpaygh.com/send_other_mtn_bundle/{client_ref}/'
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
                if value == "kokrokoo_bundle_1":
                    url = 'https://cs.hubtel.com/commissionservices/2016884/b230733cd56b4a0fad820e39f66bc27c'
                else:
                    url = "https://cs.hubtel.com/commissionservices/2016884/b230733cd56b4a0fad820e39f66bc27c"
                reference = f"\"{client_ref}\""

                payload = "{\r\n    \"Destination\": " + str(phone_number) + ",\r\n    \"Amount\": " + str(amount) + ",\r\n    \"CallbackUrl\": \"https://webhook.site/33d27e7d-6dd5-4899-b702-6c9022bea8c7\",\r\n    \"ClientReference\": " + str(reference) + ",\r\n    \"Extradata\" : {\r\n        \"bundle\" : " + value + "\r\n    }\r\n}\r\n"
                headers = {
                    'Authorization': 'Basic VnY3MHhuTTplNTAzYzcyMGYzYzA0N2Q2ODNjYTM3MWQ5YWEwMDZkZg==',
                    'Content-Type': 'text/plain'
                }

                response = requests.request("POST", url, headers=headers, data=payload)

                if response.status_code == 200:
                    desc = helper.airtime_description(client_ref)
                    new_mtn_bundle_transaction = models.OtherMTNBundleTransaction.objects.create(
                        user=current_user,
                        email=current_user.email,
                        bundle_number=phone_number,
                        offer=f"{amount}-{value}",
                        reference=client_ref,
                        transaction_status="Success",
                        description=desc
                    )
                    new_mtn_bundle_transaction.save()
                    return redirect('thank_you')
                else:
                    print(response.json())
                    print("Not 200 error")
                    new_mtn_bundle_transaction = models.OtherMTNBundleTransaction.objects.create(
                        user=current_user,
                        email=current_user.email,
                        bundle_number=phone_number,
                        offer=f"{amount}-{value}",
                        reference=client_ref,
                        transaction_status="Failed"
                    )
                    new_mtn_bundle_transaction.save()
                    return redirect("failed")
        else:
            new_mtn_bundle_transaction = models.OtherMTNBundleTransaction.objects.create(
                user=current_user,
                email=current_user.email,
                bundle_number=phone_number,
                offer=f"{amount}-{value}",
                reference=client_ref,
                transaction_status="Failed"
            )
            new_mtn_bundle_transaction.save()
            print("last error")
            return redirect('failed')
