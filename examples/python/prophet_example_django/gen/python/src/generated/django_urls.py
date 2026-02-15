# GENERATED FILE: do not edit directly.
from __future__ import annotations

from django.urls import path

from . import django_views as views

urlpatterns = [
    path('actions/approveOrder', views.action_approveOrder),
    path('actions/createOrder', views.action_createOrder),
    path('actions/shipOrder', views.action_shipOrder),
    path('orders', views.list_order),
    path('orders/<str:id>', views.get_order),
    path('orders/query', views.query_order),
    path('users', views.list_user),
    path('users/<str:id>', views.get_user),
    path('users/query', views.query_user),
]
