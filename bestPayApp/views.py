from time import sleep

import requests
from asgiref.sync import sync_to_async
from django.contrib import messages
from django.shortcuts import render, redirect

from bestPayApp import helper, models, forms
from bestPayApp.forms import SendMessageForm
from django.http import HttpResponse, JsonResponse


# Create your views here.
def home(request):
    form = SendMessageForm()
    if request.user.is_authenticated:
        form = SendMessageForm(
            initial={
                'name': request.user.username,
                'email': request.user.email
            }
        )
    if request.method == "POST":
        form = SendMessageForm(request.POST)
        if form.is_valid():
            name = str(form.cleaned_data["name"])
            email = str(form.cleaned_data["email"])
            message = str(form.cleaned_data["message"])

            url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0242442147&from=BP-Site&sms={name}\n{email}\n{message}"

            response = requests.request("GET", url)
            print(response.text)
            print(message)
    context = {'form': form}
    return render(request, 'layouts/index.html', context=context)
    # return HttpResponse("Site under maintenance. Try again later.")


def services(request):
    return render(request, 'layouts/services.html')


def about(request):
    return render(request, 'layouts/about.html')


def blog(request):
    return render(request, 'layouts/blog-single.html')


def thank_you(request):
    return render(request, "layouts/thank_you.html")


def failed(request):
    return render(request, "layouts/failed.html")


def intruder(request):
    return render(request, "layouts/thief.html")


def maintenance(request):
    return render(request, "layouts/maintenance.html")


def privacy_policy(request):
    return render(request, "layouts/privacy.html")


def api_documentation(request):
    return render(request, "layouts/api-documentation.html")


# def verify_transaction(request, reference):
#     if request.method == "GET":
#         print("got here")
#         response = helper.verify_paystack_transaction(reference)
#         data = response.json()
#         try:
#             print("got into the try")
#             status = data["data"]["status"]
#             amount = data["data"]["amount"]
#             api_reference = data["data"]["reference"]
#             date = data["data"]["paid_at"]
#             real_amount = float(amount) / 100
#
#             new_payment = models.Payment.objects.create(
#                 user=request.user,
#                 transaction_status=status,
#                 amount=real_amount,
#                 reference=api_reference,
#                 transaction_date=date
#             )
#             new_payment.save()
#         except:
#             print("got into the except")
#             status = data["status"]
#             new_payment = models.Payment.objects.create(
#                 user=request.user,
#                 transaction_status=status,
#                 reference=reference
#             )
#             new_payment.save()
#         return JsonResponse({'status': status})

@sync_to_async
def verify_payment(request, ref, channel):
    payment = models.Payment.objects.get(reference=ref)
    verified = payment.verify_payment()
    current_user = request.user

    if verified:
        print("Verified")
        bundle = helper.ishare_map[float(payment.amount)]
        print(bundle)
        ishare_response = helper.send_ishare_bundle(request.user, payment.payment_number, bundle)

        if channel == "ishare":
            return helper.ishare_after_verification(request, current_user, payment, bundle)

    # return render(request, "layouts/thank_you.html")


def process_transaction(request, ref):
    ...


def credit_user(request):
    form = forms.CreditUserForm()
    if request.method == "POST":
        form = forms.CreditUserForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            amount = form.cleaned_data["amount"]
            print(user)
            print(amount)
            user_needed = models.CustomUser.objects.get(username=user)
            if user_needed.wallet is None:
                user_needed.wallet = float(amount)
            else:
                user_needed.wallet += float(amount)
            user_needed.save()
            print(user_needed.username)
            messages.success(request, "Crediting Successful")
            return redirect('credit_user')
    context = {'form': form}
    return render(request, "layouts/services/credit.html", context=context)
