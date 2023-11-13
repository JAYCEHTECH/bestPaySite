import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bestPayApp import models, helper


@login_required(login_url='login')
def dashboard(request):
    airtime_transactions = models.AirtimeTransaction.objects.filter(user=request.user).order_by('transaction_date').reverse()
    context = {'airtime_txns': airtime_transactions}
    return render(request, 'dashboard/layouts/index.html', context=context)


@login_required(login_url='login')
def txn_table(request, keyword):
    data = helper.data_needed_from_model(keyword, request.user)
    model_data = data["model_data"]
    heading = data["heading"]
    return render(request, 'dashboard/layouts/tables.html', context={'data': model_data, 'heading': heading})


@login_required(login_url='login')
def payment_table(request):
    payments = models.Payment.objects.filter(user=request.user, payment_description="Ishare Payment").order_by('transaction_date').reverse()
    context = {'payments': payments}
    return render(request, "dashboard/layouts/payment-table.html", context=context)


@login_required(login_url='login')
def mtn_admin(request):
    if request.user.is_superuser:
        all_flexi_transactions = models.MTNBundleTransaction.objects.filter(type="Flexi").order_by('transaction_date').reverse()
        context = {
            'txns': all_flexi_transactions
        }
        return render(request, "dashboard/layouts/mtn-admin.html", context=context)
    else:
        messages.error(request, "Access Denied")
        return redirect("user-dashboard")


@login_required(login_url='login')
def mark_as_sent(request, reference):
    if request.user.is_superuser:
        transaction = models.MTNBundleTransaction.objects.get(reference=reference, type="Flexi")
        transaction.transaction_status = "Successful"

        sms_message = f"Hello,\nYour MTN order with reference {transaction.reference} has been completed successfully, Your account has been credited with {transaction.offer}.\nThank you."
        first_sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{transaction.user.phone}&from=BESTPAY GH&sms={sms_message}"
        sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to=0{transaction.bundle_number}&from=BESTPAY GH&sms=Hello\nYour account has been credited with {transaction.offer}.\nReference:{transaction.reference}."
        first_response = requests.request("GET", url=sms_url)
        response = requests.request("GET", url=first_sms_url)
        print(response.text)
        print(first_response.text)

        transaction.save()
        messages.success(request, "Marked as sent")
        return redirect('mtn_admin')
    else:
        messages.error(request, "Access Denied")
        return redirect('user-dashboard')

