import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from bestPayApp.paystack import Paystack


# Create your models here.
class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=100, null=False, blank=False)
    last_name = models.CharField(max_length=100, null=False, blank=False)
    username = models.CharField(max_length=100, null=False, blank=False, unique=True)
    email = models.EmailField(max_length=250, null=False, blank=False)
    wallet = models.FloatField(null=True, blank=True, default=0.0)
    phone = models.PositiveIntegerField(null=True, blank=True)
    password1 = models.CharField(max_length=100, null=False, blank=False)
    password2 = models.CharField(max_length=100, null=False, blank=False)


class Site(models.Model):
    status = models.BooleanField(null=True, blank=True)
    choices = (
        ("Active", "Active"),
        ("Inactive", "Inactive")
    )
    ishare_status = models.CharField(choices=choices, max_length=200, default="Active", null=False, blank=False)

    def __str__(self):
        return str(self.status)


class Payment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    reference = models.CharField(max_length=256, null=False, blank=False)
    payment_number = models.CharField(max_length=256, null=True, blank=True)
    amount = models.FloatField(null=True, blank=True)
    payment_description = models.CharField(max_length=500, null=True, blank=True)
    transaction_status = models.CharField(max_length=256, null=True, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=500, null=True, blank=True)
    payment_visited = models.BooleanField(blank=False, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.reference}"

    def save(self, *args, **kwargs):
        while not self.reference:
            ref = secrets.token_urlsafe(5)
            object_with_similar_ref = Payment.objects.filter(reference=ref)
            if not object_with_similar_ref:
                self.reference = ref

        super().save(*args, **kwargs)

    def amount_value(self):
        return float(self.amount) * 100

    def verify_payment(self):
        paystack = Paystack()
        status, result = paystack.verify_payment(self.reference, self.amount)
        if status:
            if result['status'] == 'success':
                print("data success")
                if result['amount'] / 100 == self.amount:
                    self.transaction_status = "Verified"
                    self.payment_visited = True
                self.save()
            else:
                print(result['status'])
                return False
        if self.transaction_status == "Verified":
            return True
        return False


class MTNBundlePrice(models.Model):
    price = models.FloatField(null=False, blank=False)
    bundle_volume = models.FloatField(null=False, blank=False)

    def __str__(self):
        if self.bundle_volume >= 1000:
            return f"GHS{self.price} - {self.bundle_volume/1000}GB"
        return f"GHS{self.price} - {self.bundle_volume}MB"


class AppPayment(models.Model):
    username = models.CharField(max_length=256, null=False, blank=False)
    reference = models.CharField(max_length=256, null=False, blank=False)
    payment_number = models.CharField(max_length=256, null=True, blank=True)
    amount = models.FloatField(null=True, blank=True)
    payment_description = models.CharField(max_length=500, null=True, blank=True)
    transaction_status = models.CharField(max_length=256, null=True, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=500, null=True, blank=True)
    payment_visited = models.BooleanField(blank=False, null=False)

    def __str__(self):
        return f"{self.username} - {self.payment_number} - {self.reference}"


class Intruder(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    reference = models.CharField(max_length=256, null=False, blank=False)
    transaction_date = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}"


class AirtimeTransaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    email = models.EmailField(max_length=250, null=False, blank=True)
    airtime_number = models.PositiveBigIntegerField(null=False, blank=False)
    airtime_amount = models.FloatField(null=False, blank=True)
    provider = models.CharField(max_length=20, null=False, blank=True)
    reference = models.CharField(max_length=20, null=False, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    transaction_status = models.CharField(max_length=100, null=False)

    def __str__(self):
        return f"{self.user.username} - {self.airtime_number} - {self.reference}"


class MTNBundleTransaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    email = models.EmailField(max_length=250, null=False, blank=True)
    bundle_number = models.PositiveBigIntegerField(null=False, blank=False)
    offer = models.CharField(max_length=250, null=False, blank=False)
    reference = models.CharField(max_length=20, null=False, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    transaction_status = models.CharField(max_length=100, null=False)
    choices = (
        ("Flexi", "Flexi"),
        ("Normal", "Normal")
    )
    type = models.CharField(max_length=200, null=True, blank=True, choices=choices, default="Normal")

    def __str__(self):
        return f"{self.user.username} - {self.bundle_number} - {self.reference}"


class OtherMTNBundleTransaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    email = models.EmailField(max_length=250, null=False, blank=True)
    bundle_number = models.PositiveBigIntegerField(null=False, blank=False)
    offer = models.CharField(max_length=250, null=False, blank=False)
    reference = models.CharField(max_length=20, null=False, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    transaction_status = models.CharField(max_length=100, null=False)
    description = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.bundle_number} - {self.reference}"


class VodafoneBundleTransaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    email = models.EmailField(max_length=250, null=False, blank=True)
    bundle_number = models.PositiveBigIntegerField(null=False, blank=False)
    offer = models.CharField(max_length=250, null=False, blank=False)
    reference = models.CharField(max_length=20, null=False, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    transaction_status = models.CharField(max_length=100, null=False)

    def __str__(self):
        return f"{self.user.username} - {self.bundle_number} - {self.reference}"


class AirtelTigoBundleTransaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    email = models.EmailField(max_length=250, null=False, blank=True)
    bundle_number = models.PositiveBigIntegerField(null=False, blank=False)
    offer = models.CharField(max_length=250, null=False, blank=False)
    reference = models.CharField(max_length=20, null=False, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    transaction_status = models.CharField(max_length=100, null=False)
    description = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.bundle_number} - {self.reference}"


class IShareBundleTransaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    email = models.EmailField(max_length=250, null=False, blank=True)
    bundle_number = models.BigIntegerField(null=False, blank=False)
    offer = models.CharField(max_length=250, null=False, blank=False)
    batch_id = models.CharField(max_length=250, null=False, blank=False)
    message = models.CharField(max_length=250, null=True, blank=True)
    reference = models.CharField(max_length=20, null=True, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    transaction_status = models.CharField(max_length=100, null=False)
    description = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.bundle_number} - {self.reference}"


class AppIShareBundleTransaction(models.Model):
    username = models.CharField(max_length=250, null=False, blank=False)
    email = models.EmailField(max_length=250, null=False, blank=True)
    bundle_number = models.BigIntegerField(null=False, blank=False)
    offer = models.CharField(max_length=250, null=False, blank=False)
    batch_id = models.CharField(max_length=250, null=False, blank=False)
    message = models.CharField(max_length=250, null=True, blank=True)
    reference = models.CharField(max_length=20, null=False, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    transaction_status = models.CharField(max_length=100, null=False)
    description = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.username} - {self.bundle_number} - {self.reference}"


class SikaKokooBundleTransaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    email = models.EmailField(max_length=250, null=False, blank=True)
    bundle_number = models.PositiveBigIntegerField(null=False, blank=False)
    offer = models.CharField(max_length=250, null=False, blank=False)
    reference = models.CharField(max_length=20, null=False, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    transaction_status = models.CharField(max_length=100, null=False)

    def __str__(self):
        return f"{self.user.username} - {self.bundle_number} - {self.reference}"


class TvTransaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    email = models.EmailField(max_length=250, null=False, blank=True)
    account_number = models.PositiveIntegerField(null=False, blank=False)
    amount = models.PositiveIntegerField(null=False, blank=False)
    provider = models.CharField(max_length=250, null=False, blank=False)
    reference = models.CharField(max_length=20, null=False, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    transaction_status = models.CharField(max_length=100, null=False)

    def __str__(self):
        return f"{self.user.username} - {self.account_number} - {self.reference}"


# ========================== SHOP ============================


class Product(models.Model):
    name = models.CharField(max_length=250, null=False, blank=True)
    product_image = models.CharField(max_length=300, null=False, blank=False)
    description = models.TextField(max_length=600, null=False, blank=False)
    quantity = models.PositiveIntegerField(null=False, blank=False)
    original_price = models.FloatField(null=False, blank=False)
    selling_price = models.FloatField(null=False, blank=False)
    status = models.BooleanField(default=False, help_text="0=default, 1=Hidden")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_qty = models.PositiveIntegerField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    order_name = models.CharField(max_length=300, null=False, blank=False)
    email = models.EmailField(null=False, blank=False)
    phone = models.PositiveIntegerField(null=False, blank=False)
    address = models.CharField(max_length=400, null=False, blank=False)
    total_price = models.FloatField(null=False, blank=False)
    payment_reference = models.CharField(max_length=100, null=False, blank=False)
    order_statuses = (
        ('Pending', 'Pending'),
        ('Out for Shipping', 'Out for Shipping'),
        ('Completed', 'Completed')
    )
    status = models.CharField(max_length=100, choices=order_statuses, default="Pending")
    tracking_number = models.CharField(max_length=150, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tracking_number} - {self.user} - {self.order_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.FloatField(null=False)
    tracking_number = models.CharField(max_length=150, null=True)
    quantity = models.PositiveIntegerField(null=False)

    def __str__(self):
        return f"{self.order.tracking_number} - {self.order.user} - {self.order.order_name}"


class TopUpRequests(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    previous_balance = models.PositiveIntegerField(null=True, blank=True)
    current_balance = models.PositiveIntegerField(null=True, blank=True)


class NotificationMessage(models.Model):
    message = models.CharField(max_length=400, null=True, blank=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    active = models.BooleanField(default=False)









