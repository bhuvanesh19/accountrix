from enum import Enum
import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


from entryhold.models import BaseEvent, BaseSupplementaryClass, BaseEntry

# Create your models here.


class Customer(models.Model):
    # CIF is typically a unique identifier for the customer in the banking system
    cif = models.CharField(
        max_length=20, unique=True, help_text="Customer Information File (CIF) number"
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=10, choices=[("M", "Male"), ("F", "Female"), ("O", "Other")]
    )

    # Contact information
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)

    # Address information
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)

    # Additional fields that could be relevant
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True, help_text="Indicates if the customer account is active"
    )
    home_branch = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (CIF: {self.cif})"

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"


# Enum for account status
class AccountStatus(Enum):
    ACTIVE = "Active"
    BLOCKED = "Blocked"
    CLOSED = "Closed"
    PENDING = "Pending"


CurrencyField = models.CharField(
    max_length=3, help_text="Currency code (e.g., USD, EUR)"
)


# Model for AccountType
class AccountType(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Type of account (e.g., Savings, Checking)",
    )
    description = models.TextField(
        blank=True, null=True, help_text="Description of the account type"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Account Type"
        verbose_name_plural = "Account Types"


class Account(models.Model):

    # Foreign Key to AccountType model
    account_type = models.ForeignKey(
        AccountType, on_delete=models.SET_NULL, null=True, related_name="bank_accounts"
    )

    # Foreign Key to Customer model
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="bank_accounts"
    )

    account_number = models.CharField(
        max_length=12, unique=True, help_text="Unique account number"
    )

    currency = CurrencyField

    # Enum field for account status
    status = models.CharField(
        max_length=10,
        choices=[(status.name, status.value) for status in AccountStatus],
        default=AccountStatus.ACTIVE.name,
        help_text="Current status of the account",
    )

    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Current balance of the account",
    )

    # Metadata Fields
    branch_code = models.CharField(
        max_length=5, help_text="Code of the branch where the account is held"
    )

    opening_date = models.DateField(
        help_text="The date when the account was opened", auto_now=True
    )

    last_activity_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The last time there was activity on the account",
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="Last account update timestamp"
    )

    def __str__(self):
        return f"Account {self.account_number} ({self.account_type}) - {self.get_status_display()} - Balance: {self.balance} {self.currency}"

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"


class TransactionType(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Name of the transaction type (e.g., Transfer, Deposit)",
    )
    description = models.TextField(
        blank=True, null=True, help_text="Description of the transaction type"
    )
    code = models.CharField(
        max_length=3, unique=True, help_text="Code of the transaction type"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Transaction Type"
        verbose_name_plural = "Transaction Types"


class TransactionStatus(models.TextChoices):
    PENDING = "Pending", "Pending"
    COMPLETED = "Completed", "Completed"
    FAILED = "Failed", "Failed"
    REVERSED = "Reversed", "Reversed"


class TransferIntent(BaseEvent):
    # Related accounts
    content_type_from = models.ForeignKey(
        ContentType, on_delete=models.RESTRICT, related_name="from_account_model"
    )
    object_id_from = models.PositiveIntegerField()
    from_account = GenericForeignKey("content_type_from", "object_id_from")

    # Second generic foreign key
    content_type_to = models.ForeignKey(
        ContentType, on_delete=models.RESTRICT, related_name="to_account_model"
    )
    object_id_to = models.PositiveIntegerField()
    to_account = GenericForeignKey("content_type_to", "object_id_to")

    # Transaction details
    amount = models.DecimalField(
        max_digits=15, decimal_places=2, help_text="Amount involved in the transaction"
    )
    currency = CurrencyField
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description or note for the transaction",
    )

    # Foreign Key to TransactionType
    transaction_type = models.ForeignKey(
        TransactionType,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Type of the transaction (e.g., Transfer, Deposit)",
    )

    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        help_text="Current status of the transaction",
    )
    transaction_reference = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Unique reference identifier for the transaction",
    )

    # Timestamps
    initiated_at = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp when the transaction was initiated"
    )
    completed_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp when the transaction was completed"
    )

    def __str__(self):
        return f"Transaction {self.transaction_reference} - {self.amount} {self.currency} ({self.status})"


@TransferIntent.add_suplementary_model
class MaxLimit(BaseSupplementaryClass):
    limit = models.PositiveIntegerField()


class Ledger(models.Model):
    """
    Represents a ledger containing journal entries for accounting purposes.
    """

    name = models.CharField(
        max_length=255, help_text="Name of the ledger (e.g., General Ledger)"
    )
    description = models.TextField(
        blank=True, null=True, help_text="Description of the ledger"
    )
    code = models.CharField(max_length=3, unique=True, help_text="Code of the ledger")
    parent_ledger = models.ForeignKey(
        "self",
        on_delete=models.RESTRICT,
        related_name="sub_ledgers",
        null=True,
        blank=True,
        help_text="Reference to a parent ledger, if this is a sub-ledger",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="When the ledger was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="When the ledger was last updated"
    )

    def __str__(self):
        return f"{self.name} (Parent: {self.parent_ledger.name if self.parent_ledger else 'None'})"


class DrCrType(models.TextChoices):
    DEBIT = "DEBIT", "Debit"
    CREDIT = "CREDIT", "Credit"


class LedgerEntry(BaseEntry):
    """
    Represents a single journal entry in a ledger.
    """

    ledger = models.ForeignKey(
        Ledger,
        on_delete=models.RESTRICT,
        related_name="journal_entries",
        help_text="The ledger this journal entry belongs to",
    )
    dr_cr_type = models.CharField(
        max_length=6, choices=DrCrType.choices, verbose_name="Entry Type"
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        verbose_name="Amount",
    )
    currency = CurrencyField
    description = models.TextField(blank=True, verbose_name=("Description"))
    transaction_reference = models.CharField(
        max_length=100, blank=True, verbose_name=("Transaction Reference")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("Created At"))

    def __str__(self):
        return (
            f"{'Debit' if self.is_debit else 'Credit'} {self.amount} on {self.account}"
        )


class AccountEntry(BaseEntry):
    """
    Represents an entry in an account's journal for tracking transactions.
    """

    account = models.ForeignKey(
        Account,
        on_delete=models.RESTRICT,
        related_name="account_entries",
        help_text="The account this journal entry belongs to",
    )
    dr_cr_type = models.CharField(
        max_length=6, choices=DrCrType.choices, verbose_name="Entry Type"
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        verbose_name="Amount",
    )
    currency = CurrencyField
    description = models.TextField(blank=True, verbose_name=("Description"))
    transaction_reference = models.ForeignKey(
        TransferIntent,
        on_delete=models.RESTRICT,
        verbose_name=("Transaction Reference"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("Created At"))

    def __str__(self):
        return f"Account {self.account} Entry: {self.journal_entry}"
