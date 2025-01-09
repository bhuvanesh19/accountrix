from django.db import models, transaction

from entryhold.models import (
    BasePostingRule,
    BaseEventPostingRuleRouter,
    BasePostingRuleRoutingStrategy,
    BaseSupplementaryClass,
)
from transactions.models import (
    TransferIntent,
    Ledger,
    Account,
    LedgerEntry,
    AccountEntry,
    DrCrType,
    CurrencyField,
)


@TransferIntent.register_posting_rule_router
class TransferIntentRouter(BaseEventPostingRuleRouter):
    pass


@TransferIntentRouter.add_strategy
class TransferTypeRoutingStratagey(BasePostingRuleRoutingStrategy):

    def get_posting_rule(self, event: TransferIntent):
        if event.transaction_type.code == "100":
            return MoneyDepositPostingRule

        elif event.transaction_type.code == "101":
            return AccountToAccountPostingRule


class MoneyDepositPostingRule(BasePostingRule):

    def post(self, event: TransferIntent):
        with transaction.atomic():
            charge_amount = (
                MoneyDepositPostingRule.Charges.objects.filter(currency=event.currency)
                .latest("timestamp")
                .charge
                / 100
            ) * event.amount
            cash = event.amount - charge_amount
            # All debits
            cash_ledger_entry = LedgerEntry(
                ledger=event.from_account,
                dr_cr_type=DrCrType.DEBIT,
                amount=event.amount,
                currency=event.currency,
                description=f"Money deposit into account {event.to_account.account_number}",
                transaction_reference=event.transaction_reference,
            )

            # All Credits
            charge_ledger_entry = LedgerEntry(
                ledger=Ledger.objects.get(code="007"),
                dr_cr_type=DrCrType.CREDIT,
                amount=charge_amount,
                currency=event.currency,
                description=f"Money deposit into account {event.to_account.account_number}",
                transaction_reference=event,
            )
            account_entry = AccountEntry(
                account=event.to_account,
                dr_cr_type=DrCrType.CREDIT,
                amount=cash,
                currency=event.currency,
                description=f"Money deposited into account {event.to_account.account_number}",
                transaction_reference=event,
            )

            to_account: Account = event.to_account
            to_account.balance += cash
            to_account.save()

            charge_ledger_entry.save()
            cash_ledger_entry.save()
            account_entry.save()
        return account_entry


@MoneyDepositPostingRule.add_suplementary_model
class Charges(BaseSupplementaryClass):
    charge = models.DecimalField(max_digits=4, decimal_places=2)
    currency = CurrencyField


class AccountToAccountPostingRule(BasePostingRule):

    def post(self, event):
        return super().post(event)
