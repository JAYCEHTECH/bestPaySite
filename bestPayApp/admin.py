from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models
from .models import CustomUser
# Register your models here.


class CustomUserAdmin(UserAdmin):
    list_display = ['first_name', 'last_name', 'username', 'email', 'wallet', 'phone']

    fieldsets = (
        *UserAdmin.fieldsets,
        (
            'Other Personal info',
            {
                'fields': (
                    'phone', 'wallet'
                )
            }
        )
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'wallet')
        }),)


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'payment_number', 'amount', 'reference', 'transaction_status', 'transaction_date']
    search_fields = ['reference']


class IntruderAdmin(admin.ModelAdmin):
    list_display = ['user', 'reference', 'message', 'transaction_date']


class AirtimeTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'airtime_amount', 'airtime_number', 'reference', 'provider', 'transaction_date']
    search_fields = ['reference']


class MTNBundleTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'bundle_number', 'offer', 'reference', 'transaction_date', "transaction_status"]
    search_fields = ['reference']


class VodafoneBundleTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'bundle_number', 'offer', 'reference', 'transaction_date', "transaction_status"]
    search_fields = ['reference']


class OtherMTNBundleTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'bundle_number', 'offer', 'reference', 'transaction_date', "transaction_status"]
    search_fields = ['reference']


class AirtelTigoBundleTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'bundle_number', 'offer', 'reference', 'transaction_date', "transaction_status"]
    search_fields = ['reference']


class SikaKokooBundleTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'bundle_number', 'offer', 'reference', 'transaction_date', "transaction_status"]
    search_fields = ['reference']


class IShareBundleTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'bundle_number', 'offer', 'reference', 'batch_id', 'transaction_status', 'transaction_date', 'message']
    search_fields = ['reference', 'batch_id', 'bundle_number']


class TopupRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'date', 'previous_balance', 'current_balance']


class TvTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'account_number', 'amount', 'reference', 'transaction_date', "transaction_status"]
    search_fields = ['reference']


class NotificationMessageAdmin(admin.ModelAdmin):
    list_display = ['message', 'active']

class AppPaymentAdmin(admin.ModelAdmin):
    ...


class AppIShareBundleTransactionAdmin(admin.ModelAdmin):
    ...


class ProductAdmin(admin.ModelAdmin):
    ...


class CartAdmin(admin.ModelAdmin):
    ...


class OrderAdmin(admin.ModelAdmin):
    ...


class OrderItemAdmin(admin.ModelAdmin):
    ...


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(models.AirtimeTransaction, AirtimeTransactionAdmin)
admin.site.register(models.MTNBundleTransaction, MTNBundleTransactionAdmin)
admin.site.register(models.VodafoneBundleTransaction, VodafoneBundleTransactionAdmin)
admin.site.register(models.OtherMTNBundleTransaction, OtherMTNBundleTransactionAdmin)
admin.site.register(models.AirtelTigoBundleTransaction, AirtelTigoBundleTransactionAdmin)
admin.site.register(models.SikaKokooBundleTransaction, SikaKokooBundleTransactionAdmin)
admin.site.register(models.IShareBundleTransaction, IShareBundleTransactionAdmin)
admin.site.register(models.TvTransaction, TvTransactionAdmin)
admin.site.register(models.Payment, PaymentAdmin)
admin.site.register(models.Intruder, IntruderAdmin)
admin.site.register(models.AppPayment)
admin.site.register(models.AppIShareBundleTransaction)
admin.site.register(models.Site)
admin.site.register(models.MTNBundlePrice)
admin.site.register(models.TopUpRequests, TopupRequestAdmin)
admin.site.register(models.NotificationMessage, NotificationMessageAdmin)

admin.site.register(models.Product, ProductAdmin)
admin.site.register(models.Cart, CartAdmin)
admin.site.register(models.Order, OrderAdmin)
admin.site.register(models.OrderItem, OrderItemAdmin)



