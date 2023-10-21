from time import sleep

import requests
from asgiref.sync import sync_to_async
from django.contrib import messages
from django.shortcuts import render, redirect

from bestPayApp import helper, models, forms
from bestPayApp.forms import SendMessageForm
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect


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
    print("got to verification")
    payment = models.Payment.objects.get(reference=ref)
    sleep(5)
    print("About to verify")
    verified = payment.verify_payment()
    current_user = request.user

    if verified:
        statuss = models.Site.objects.all()
        status = statuss[0]
        print(status)
        needed = status.ishare_status
        print("Verified")
        bundle = helper.ishare_map[float(payment.amount)]
        print(bundle)

        if channel == "ishare":
            if models.IShareBundleTransaction.objects.filter(reference=ref, message="200 Status Code") or models.IShareBundleTransaction.objects.filter(reference=ref, message="Status code was 200 but query showed the transaction was unsuccessful") or models.IShareBundleTransaction.objects.filter(reference=ref, message="Status code was 200 but query did not return anything useful"):
                return redirect('thank_you')
            else:
                if needed == "Inactive":
                    new_ishare_bundle_transaction = models.IShareBundleTransaction.objects.create(
                        user=current_user,
                        email=current_user.email,
                        bundle_number=payment.payment_number,
                        offer=f"{bundle}MB",
                        reference=payment.reference,
                        batch_id="None",
                        message="Inactive Ishare",
                        transaction_status="Pending"
                    )
                    new_ishare_bundle_transaction.save()
                    messages.success(request, "Payment Verification Successful. Your transaction will be completed in no time")
                    return redirect('thank_you')
                ishare_response = helper.send_ishare_bundle(request.user, payment.payment_number, bundle)
                if ishare_response.status_code == 200:
                    data = ishare_response.json()
                    batch_id = data["batchId"]
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
                    sleep(10)
                    verified = helper.ishare_verification(batch_id)
                    if verified is not False:
                        code = verified["flexiIshareTranxStatus"]["flexiIshareTranxStatusResult"]["apiResponse"][
                            "responseCode"]
                        if code == '200':
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
                                messages.success(request, "Payment Verification Successful")
                                return redirect("thank_you")
                            except:
                                messages.success(request, "Payment Verification Successful")
                                return redirect("thank_you")
                        else:
                            recent_ishare_transaction = models.IShareBundleTransaction.objects.get(reference=payment.reference)
                            recent_ishare_transaction.message = "Status code was 200 but query showed the transaction was unsuccessful"
                            recent_ishare_transaction.save()
                            messages.success(request, "Payment Verification Successful")
                            return redirect('thank_you')
                    else:
                        recent_ishare_transaction = models.IShareBundleTransaction.objects.get(
                            reference=payment.reference)
                        recent_ishare_transaction.message = "Status code was 200 but query did not return anything useful"
                        recent_ishare_transaction.save()
                        messages.info(request, "Transaction Completed")
                        messages.success(request, "Payment Verification Successful")
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
                        messages.success(request, "Payment Verification Successful")
                        return redirect('failed')
                    except:
                        return redirect('failed')
        else:
            messages.success(request, "Verified Successfully")
            return redirect('home')
    else:
        messages.info(request, "Payment did not go through for this reference")
        try:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        except:
            return redirect('ishare_bundle')


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
