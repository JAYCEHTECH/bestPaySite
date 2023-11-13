import datetime
from time import sleep

import requests
from asgiref.sync import sync_to_async
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
    announcement = models.NotificationMessage.objects.filter(active=True).first()

    if announcement:
        title = announcement.title
        message = announcement.message
        context = {'form': form, 'title': title, 'message': message}
    else:
        context = {'form': form}

    # if announcements:
    #     for ann in announcements:
    #         message = ann.message
    #         status = ann.active
    #         print(message)
    #
    #         if status:
    #             print("hello world this is active")
    #             messages.info(request, f"{message}")

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


@login_required(login_url='login')
def wallet_topup(request):
    if request.method == "POST":
        amount = request.POST.get("topup-amount")
        print(amount)

        pk = "pk_live_99e10d6f2512390f0960dbf9ac3a8163af13e275"
        # pk = "pk_test_39d8b43d02deb0cc6eeb5389db47ee263928045a"

        payment = models.Payment.objects.create(amount=amount, user=request.user, payment_description="Wallet Topup")
        payment.save()

        reference = payment.reference

        if payment:
            context = {
                'payment': payment,
                'reference_f': reference,
                'field_values': request.POST,
                'paystack_pub_key': pk,
                'amount_value': payment.amount_value(),
                'email': request.user.email,
                'channel': 'topup'
            }
            print("moved to make payment")
            return render(request, 'layouts/services/make_payment.html', context)
        else:
            return redirect('wallet-topup')
    current_user = models.CustomUser.objects.get(id=request.user.id)
    context = {'wallet_balance': current_user.wallet}
    return render(request, "layouts/services/wallet-topup.html", context=context)


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
    print(channel)
    print("got to verification")
    payment = models.Payment.objects.get(reference=ref)
    sleep(5)
    print("About to verify")
    verified = payment.verify_payment()
    current_user = request.user

    if verified:
        if channel == "ishare":
            statuss = models.Site.objects.all()
            status = statuss[0]
            print(status)
            needed = status.ishare_status
            print("Verified")
            bundle = helper.ishare_map[float(payment.amount)]
            print(bundle)

        if channel == "ishare":
            if models.IShareBundleTransaction.objects.filter(reference=ref, message="200 Status Code") or models.IShareBundleTransaction.objects.filter(reference=ref, message="Status code was 200 but query showed the transaction was unsuccessful") or models.IShareBundleTransaction.objects.filter(reference=ref, message="Status code was 200 but query did not return anything useful"):
                txn = models.IShareBundleTransaction.objects.get(reference=ref)
                status = helper.ishare_verification(txn.batch_id)
                if status is not False:
                    print(status)
                    message = status["flexiIshareTranxStatus"]["flexiIshareTranxStatusResult"]["apiResponse"]["responseMsg"]
                    if message == "No record for transactionID":
                        ishare_response = helper.send_ishare_bundle(request.user, payment.payment_number, bundle)
                        if ishare_response.status_code == 200:
                            data = ishare_response.json()
                            batch_id = data["batchId"]
                            txn.batch_id = batch_id
                            txn.message = "200 Status Code"
                            txn.transaction_status = "Successful"
                            txn.save()
                            return redirect('thank_you')
                        else:
                            messages.error(request, "Try again")
                            return redirect('flexi_payment_table')
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
        elif channel == "flexi_mtn":
            print("verified")
            print("This is flexi mtn")
            offer = models.MTNBundlePrice.objects.get(price=payment.amount)
            bundle = offer.bundle_volume
            new_mtn_transaction = models.MTNBundleTransaction.objects.create(
                user=request.user,
                bundle_number=payment.payment_number,
                offer=f"{bundle}MB",
                reference=payment.reference,
                transaction_status="Pending",
                type="Flexi"
            )
            new_mtn_transaction.save()
            sms_message = f"An order has been placed. {bundle}MB for {payment.payment_number}.\nReference: {payment.reference}"
            sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0592117523&from=BESTPAY GH&sms={sms_message}"
            response = requests.request("GET", url=sms_url)
            print(response.text)
            messages.success(request, "Your transaction will be completed shortly.")
            return redirect('thank_you')
        elif channel == "topup":
            print("topup is here")
            amount = payment.amount
            print(amount)
            current_user = models.CustomUser.objects.get(id=request.user.id)
            current_user.wallet += amount
            new_topup_txn = models.TopUpRequests.objects.create(
                user=request.user,
                amount=amount,
                date=datetime.datetime.now(),
                previous_balance=current_user.wallet,
                current_balance=current_user.wallet + amount,
            )
            new_topup_txn.save()
            current_user.save()
            sms_message = f"Hello,\nYour BestPay wallet has been credited with GHS{amount}.\nDo more with BestPay.\nThank you!"
            sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{current_user.phone}&from=BESTPAY GH&sms={sms_message}"
            response = requests.request("GET", url=sms_url)
            print(response.text)
            return redirect('thank_you')
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
