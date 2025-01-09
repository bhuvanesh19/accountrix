from django.shortcuts import render
from rest_framework import mixins, views, viewsets, generics, response

from transactions.serializers import *
from transactions import controllers

from transactions.models import (
    Customer,
    AccountType,
    Account,
    TransactionType,
)


class CustomerViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CreateCustomerSerializer
    queryset = Customer.objects.all()


class AccountViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CreateAccountSerializer
    queryset = Account.objects.all()


class CreateAccountTypeViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = CreateAccountTypeSerializer


class CreateTransactionTypeViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = CreateTransactionTypeSerializer


class MaxLimitViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = MaxLimitSerializer
    queryset = MaxLimit.objects.all()


class LedgerViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = LedgerSerializer
    queryset = Ledger.objects.all()


class TransferView(mixins.ListModelMixin, generics.GenericAPIView):

    serializer_class = MoneyDepositIntentSerializer
    queryset = TransferIntent.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        transfer_intent = serializer.create(serializer.validated_data)
        transfer_intent.process()
        return response.Response(
            data={
                "success": True,
                "transaction_reference": transfer_intent.transaction_reference,
            }
        )

    def get(self, request, *args, **kwargs):
        return self.list(request)


class DepositChargesView(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DepositchargesSerializer
    queryset = controllers.Charges.objects.all()
