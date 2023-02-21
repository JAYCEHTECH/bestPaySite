import json
import random
from datetime import datetime
import secrets

import requests
from decouple import config
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

from bestPayApp import forms
from bestPayApp.models import CustomUser
from django.contrib.auth.models import User
from bestPayApp import models, helper


def ref_generator(number):
    now_time = datetime.now().strftime('%H%M%S')
    secret = secrets.token_hex(number)

    return f"BP{now_time}{secret}".upper()


def airtime(request):
    form = forms.AirtimeForm()
    if request.method == "POST":
        if request.user.is_authenticated:
            form = forms.AirtimeForm(request.POST)
            if form.is_valid():
                phone_number = str(form.cleaned_data["phone_number"])
                amount = str(form.cleaned_data["amount"])
                provider = form.cleaned_data["provider"]
                reference = ref_generator(2)

                amount_to_be_charged = amount

                float_amount = float(amount)
                if float_amount == 0.5:
                    amount_to_be_charged = 0.49
                elif float_amount == 1.00:
                    percentage = 0.01
                    amount_to_be_charged = float_amount - percentage
                elif 2 <= float_amount <= 10:
                    percentage = 0.10
                    amount_to_be_charged = float_amount - percentage
                elif 11 <= float_amount <= 50:
                    percentage = 0.50
                    amount_to_be_charged = float_amount - percentage

                url = "https://payproxyapi.hubtel.com/items/initiate"

                payload = json.dumps({
                    "totalAmount": amount_to_be_charged,
                    "description": "Test",
                    "callbackUrl": 'https://webhook.site/d53f5c53-eaba-4139-ad27-fb05b0a7be7f',
                    "returnUrl": f'https://www.bestpaygh.com/send_airtime/{reference}/{phone_number}/{amount}/{provider}',
                    "cancellationUrl": 'https://www.bestpaygh.com/services',
                    "merchantAccountNumber": "2017101",
                    "clientReference": reference
                })

                headers = {
                    'Authorization': config("HUBTEL_API_KEY"),
                    'Content-Type': 'application/json'
                }

                response = requests.request("POST", url, headers=headers, data=payload)

                data = response.json()
                if data["status"] == "Success":
                    checkout_url = data["data"]["checkoutUrl"]
                    return redirect(checkout_url)
                else:
                    return redirect("failed")
        else:
            messages.success(request, "Login to continue")
            return redirect('login')
    context = {'form': form}
    return render(request, 'layouts/services/airtime.html', context=context)


def send_airtime(request, phone_number, amount, provider, reference):
    payment = models.Payment.objects.filter(reference=reference, payment_visited=True)
    if payment:
        new_intruder = models.Intruder.objects.create(
            user=request.user,
            reference=reference,
            message="Payment already exists and the reference has expired. User tried using it again."
        )
        new_intruder.save()
        return redirect('intruder')
    current_user = request.user
    airtime_provider = helper.airtime_provider_string(provider)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        "api-key": '8f56b7ea-e1d0-4ce7-ace0-162f7dc55a39'
    }

    url = helper.url_provider(provider=provider)

    webhook_response = requests.request("GET",
                                        "https://webhook.site/token/d53f5c53-eaba-4139-ad27-fb05b0a7be7f/requests?sorting=newest",
                                        headers=headers)

    for request in webhook_response.json()['data']:
        try:
            try:
                content = json.loads(request["content"])
            except ValueError:
                return redirect(
                    f'https://www.bestpaygh.com/send_airtime/{reference}/{phone_number}/{amount}/{provider}')
            status = content["Status"]
            ref = content["Data"]["ClientReference"]
        except KeyError:
            print("Key Error")
            return redirect("failed")

        if ref == reference and status == "Success":
            momo_number = content["Data"]["CustomerPhoneNumber"]
            amount = content["Data"]["Amount"]
            payment_description = content["Data"]["Description"]
            print(f"{status}--{ref}--{momo_number}--{amount}--{payment_description}")
            payment = models.Payment.objects.filter(user=current_user, reference=reference, payment_visited=True)
            if payment:
                new_intruder = models.Intruder.objects.create(
                    user=current_user,
                    reference=reference,
                    message="Payment already exists and the reference has expired. User tried using it again."
                )
                new_intruder.save()
                return redirect('intruder')
            else:
                new_payment = models.Payment.objects.create(
                    user=current_user,
                    reference=reference,
                    payment_number=momo_number,
                    amount=amount,
                    payment_description=payment_description,
                    transaction_status=status,
                    payment_visited=True,
                    message="Payment verified successfully",
                )
                new_payment.save()
                reference = f"\"{reference}\""
                payload = "{\r\n    \"Destination\": " + str(phone_number) + ",\r\n    \"Amount\": " + str(amount) + ",\r\n    \"CallbackUrl\": \"https://webhook.site/9125cb31-9481-47ad-972f-d1d7765a5957\",\r\n    \"ClientReference\": " + str(reference) + "\r\n}"

                airtime_headers = {
                    'Authorization': config("HUBTEL_API_KEY"),
                    'Content-Type': 'text/plain'
                }

                response = requests.request("POST", url, headers=airtime_headers, data=payload)
                airtime_data = response.json()
                print(airtime_data)
                print(response.status_code)

                if response.status_code == 200:
                    new_airtime_transaction = models.AirtimeTransaction.objects.create(
                        user=current_user,
                        email=current_user.email,
                        airtime_number=phone_number,
                        airtime_amount=amount,
                        provider=airtime_provider,
                        reference=reference,
                        transaction_status="Success"
                    )
                    new_airtime_transaction.save()
                    return redirect('thank_you')
                else:
                    print("not 200 error")
                    new_airtime_transaction = models.AirtimeTransaction.objects.create(
                        user=current_user,
                        email=current_user.email,
                        airtime_number=phone_number,
                        airtime_amount=amount,
                        provider=airtime_provider,
                        reference=reference,
                        transaction_status="Failed"
                    )
                    new_airtime_transaction.save()
                    print("Last error")
                    return redirect("failed")
        else:
            new_airtime_transaction = models.AirtimeTransaction.objects.create(
                user=current_user,
                email=current_user.email,
                airtime_number=phone_number,
                airtime_amount=amount,
                provider=airtime_provider,
                reference=reference,
                transaction_status="Failed"
            )
            new_airtime_transaction.save()
            print("last error")
            return redirect("failed")






