# GENERATED FILE: do not edit directly.
from __future__ import annotations

from django.db import models

class OrderModel(models.Model):
    orderId = models.CharField(max_length=255, null=false, blank=false, primary_key=True)
    customer = models.JSONField(null=false, blank=false)
    totalAmount = models.FloatField(null=false, blank=false)
    discountCode = models.CharField(max_length=255, null=true, blank=true)
    tags = models.JSONField(null=true, blank=true)
    shippingAddress = models.JSONField(null=true, blank=true)
    currentState = models.CharField(max_length=64, default='created')

    class Meta:
        app_label = 'generated'
        db_table = 'orders'

class UserModel(models.Model):
    userId = models.CharField(max_length=255, null=false, blank=false, primary_key=True)
    email = models.CharField(max_length=255, null=false, blank=false)

    class Meta:
        app_label = 'generated'
        db_table = 'users'
