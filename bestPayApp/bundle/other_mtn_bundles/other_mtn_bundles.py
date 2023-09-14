import json
from datetime import datetime

import requests
from decouple import config
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from bestPayApp.forms import OtherMTNBundleForm
from bestPayApp import helper, models, forms


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
        "api-key": config('API_KEY')
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


@login_required(login_url='login')
def flexi_mtn(request):
    user = models.CustomUser.objects.get(id=request.user.id)
    # status = user.status
    form = forms.MTNFlexiBundleForm()
    reference = helper.ref_generator(2)
    user_email = request.user.email
    if request.method == "POST":
        payment_reference = request.POST.get("reference")
        amount_paid = request.POST.get("amount")
        print(payment_reference)
        print(amount_paid)
        new_payment = models.Payment.objects.create(
            user=request.user,
            reference=payment_reference,
            amount=amount_paid,
            transaction_date=datetime.now(),
            transaction_status="Completed"
        )
        new_payment.save()
        phone_number = request.POST.get("phone")
        offer = request.POST.get("amount")

        bundle = models.MTNBundlePrice.objects.get(price=float(offer)).bundle_volume

        print(phone_number)
        new_mtn_transaction = models.MTNBundleTransaction.objects.create(
            user=request.user,
            bundle_number=phone_number,
            offer=f"{bundle}MB",
            reference=payment_reference,
            transaction_status="Pending"
        )
        new_mtn_transaction.save()
        sms_headers = {
            'Authorization': 'Bearer 1050|VDqcCUHwCBEbjcMk32cbdOhCFlavpDhy6vfgM4jU',
            'Content-Type': 'application/json'
        }

        sms_url = 'https://webapp.usmsgh.com/api/sms/send'
        sms_message = f"An order has been placed. {bundle}MB for {phone_number}.\nReference:{payment_reference}"

        sms_body = {
            'recipient': "233242442147",
            'sender_id': 'BESTPAY GH',
            'message': sms_message
        }
        response = requests.request('POST', url=sms_url, params=sms_body, headers=sms_headers)
        print(response.text)
        return JsonResponse({'status': "Your transaction will be completed shortly", 'icon': 'success'})
    user = models.CustomUser.objects.get(id=request.user.id)
    context = {'form': form, "ref": reference, "email": user_email,
               'wallet': 0 if user.wallet is None or user.wallet is 0.0 else user.wallet}
    return render(request, "layouts/services/mtn-flexi.html", context=context)


def mtn_pay_with_wallet(request):
    if request.method == "POST":
        user = models.CustomUser.objects.get(id=request.user.id)
        phone_number = request.POST.get("phone")
        amount = request.POST.get("amount")
        reference = request.POST.get("reference")
        print(phone_number)
        print(amount)
        print(reference)
        sms_headers = {
            'Authorization': 'Bearer 1136|LwSl79qyzTZ9kbcf9SpGGl1ThsY0Ujf7tcMxvPze',
            'Content-Type': 'application/json'
        }

        sms_url = 'https://webapp.usmsgh.com/api/sms/send'

        if user.wallet is None:
            return JsonResponse({'status': f'Your wallet balance is low. Top up to use wallet.'})
        elif user.wallet <= 0 or user.wallet < float(amount):
            return JsonResponse({'status': f'Your wallet balance is low. Top up to use wallet.'})
        bundle = models.MTNBundlePrice.objects.get(price=float(amount)).bundle_volume
        print(bundle)
        sms_message = f"An order has been placed. {bundle}MB for {phone_number}.\nReference:{reference}"
        new_mtn_transaction = models.MTNBundleTransaction.objects.create(
            user=request.user,
            bundle_number=phone_number,
            offer=f"{bundle}MB",
            reference=reference,
        )
        new_mtn_transaction.save()
        user.wallet -= float(amount)
        user.save()
        sms_body = {
            'recipient': f"233242442147",
            'sender_id': 'BESTPAY GH',
            'message': sms_message
        }
        response = requests.request('POST', url=sms_url, params=sms_body, headers=sms_headers)
        print(response.text)
        return JsonResponse({'status': "Your transaction will be completed shortly", 'icon': 'success'})
    return redirect('mtn')
