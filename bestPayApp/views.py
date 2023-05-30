import requests
from django.shortcuts import render, redirect

from bestPayApp import helper, models
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


def verify_transaction(request, reference):
    if request.method == "GET":
        response = helper.verify_paystack_transaction(reference)
        data = response.json()
        try:
            status = data["data"]["status"]
            amount = data["data"]["amount"]
            api_reference = data["data"]["reference"]
            date = data["data"]["paid_at"]
            real_amount = float(amount) / 100

            new_payment = models.Payment.objects.create(
                user=request.user,
                transaction_status=status,
                amount=real_amount,
                reference=api_reference,
                transaction_date=date
            )
            new_payment.save()
        except:
            status = data["status"]
            new_payment = models.Payment.objects.create(
                user=request.user,
                transaction_status=status,
                reference=reference
            )
            new_payment.save()
        return JsonResponse({'status': status})


