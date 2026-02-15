# GENERATED FILE: do not edit directly.
from __future__ import annotations

from django.db import models

class OrderModel(models.Model):
    orderId = models.CharField(max_length=255, null=False, blank=False, primary_key=True)
    customer = models.JSONField(null=False, blank=False)
    totalAmount = models.FloatField(null=False, blank=False)
    discountCode = models.CharField(max_length=255, null=True, blank=True)
    tags = models.JSONField(null=True, blank=True)
    shippingAddress = models.JSONField(null=True, blank=True)
    currentState = models.CharField(max_length=64, default='created')

    class Meta:
        app_label = 'generated'
        db_table = 'orders'

class UserModel(models.Model):
    userId = models.CharField(max_length=255, null=False, blank=False, primary_key=True)
    email = models.CharField(max_length=255, null=False, blank=False)

    class Meta:
        app_label = 'generated'
        db_table = 'users'
