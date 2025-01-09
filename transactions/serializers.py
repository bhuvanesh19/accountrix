from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from transactions.models import (
    Customer,
    AccountType,
    Account,
    MaxLimit,
    TransactionType,
    Ledger,
    TransferIntent,
)
from transactions.controllers import Charges as DepositCharges
from transactions.utils import generate_12_digit_number, generate_cif, verify_checksum


class CreateCustomerSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        validated_data["cif"] = generate_cif(8)
        print(validated_data)
        return super().create(validated_data)

    class Meta:
        model = Customer
        exclude = ["id", "cif"]


class CreateAccountSerializer(serializers.ModelSerializer):
    cif = serializers.CharField(
        max_length=8,
        write_only=True,
    )

    def validate_cif(self, value):
        if not verify_checksum(value):
            raise serializers.ValidationError("Invalid CIF")
        customer = Customer.objects.filter(cif=value)
        if not customer:
            raise serializers.ValidationError("Customer not found")

        return customer.get()

    def validate(self, data):
        data["customer"] = data.pop("cif")
        return super().validate(data)

    def create(self, validated_data):
        validated_data["account_number"] = generate_12_digit_number(
            validated_data["branch_code"], validated_data["customer"].cif
        )
        print("Validated Data", validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        raise

    class Meta:
        model = Account
        fields = [
            "cif",
            "account_type",
            "currency",
            "branch_code",
        ]
        write_only_fields = ["cif"]


class CreateAccountTypeSerializer(serializers.ModelSerializer):

    def update(self, instance, validated_data):
        raise

    class Meta:
        model = AccountType
        fields = "__all__"


class CreateTransactionTypeSerializer(serializers.ModelSerializer):

    def update(self, instance, validated_data):
        raise

    class Meta:
        model = TransactionType
        fields = "__all__"


class MaxLimitSerializer(serializers.ModelSerializer):

    class Meta:
        model = MaxLimit
        fields = [
            "limit",
        ]


class LedgerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ledger
        exclude = ["created_at", "updated_at"]


class MoneyDepositIntentSerializer(serializers.ModelSerializer):

    to_account = serializers.CharField(max_length=12, write_only=True)
    transaction_type = serializers.SlugRelatedField(
        queryset=TransactionType.objects.all(), slug_field="code", write_only=True
    )

    def validate_to_account(self, to_account):
        account = Account.objects.filter(account_number=to_account).first()
        if not account:
            raise serializers.ValidationError("From account not found")
        return account

    def create(self, validated_data):
        content_type_from = ContentType.objects.get_for_model(Ledger)
        object_id_from = Ledger.objects.get(code="006").id
        content_type_to = ContentType.objects.get_for_model(Account)
        object_id_to = validated_data["to_account"].id
        transfer_intent = TransferIntent(
            content_type_from=content_type_from,
            object_id_from=object_id_from,
            content_type_to=content_type_to,
            object_id_to=object_id_to,
            **validated_data,
        )
        transfer_intent.save()
        return transfer_intent

    class Meta:
        model = TransferIntent
        exclude = [
            "content_type_from",
            "object_id_from",
            "content_type_to",
            "object_id_to",
            "status",
            "initiated_at",
            "completed_at",
        ]


class DepositchargesSerializer(serializers.ModelSerializer):

    class Meta:
        model = DepositCharges
        fields = "__all__"
