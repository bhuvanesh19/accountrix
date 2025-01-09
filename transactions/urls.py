from transactions.views import (
    CustomerViewSet,
    AccountViewSet,
    CreateAccountTypeViewSet,
    CreateTransactionTypeViewSet,
    MaxLimitViewSet,
    LedgerViewSet,
    TransferView,
    DepositChargesView
)

from django.contrib import admin
from django.urls import path
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r"customer", CustomerViewSet, "customer")
router.register(r"account", AccountViewSet, "account")
router.register(r"account-type", CreateAccountTypeViewSet, "account-type")
router.register(r"transaction-type", CreateTransactionTypeViewSet, "transaction-type")
router.register(r"management/max-limit", MaxLimitViewSet, "max-limit")
router.register(r"management/ledger", LedgerViewSet, "ledger")
router.register(r"management/deposit-charges", DepositChargesView, "deposit-charges")
urlpatterns = [path(r"transfer/deposit/", TransferView.as_view())] + router.urls
