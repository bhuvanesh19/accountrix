from __future__ import annotations
from typing import Dict, List
from collections import OrderedDict

from django.db import models
from django.utils.module_loading import import_string


from entryhold.exceptions import (
    InvalidSupplementaryClassException,
    MultipleRouterException,
    NoMatchingPostingRuleException,
    InvalidPostingRuleRouter,
)
from entryhold.utils import case_convert


class BaseSupplementaryClass(models.Model):

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    @classmethod
    def get_latest(supplementary_cls, parent_cls):
        return supplementary_cls.objects


class SupplymentaryClassAdderMixin:

    _supplemetary_classes: List[BaseSupplementaryClass] = []

    @classmethod
    def add_suplementary_model(cls, model: models.Model) -> models.Model:
        if not (issubclass(model, BaseSupplementaryClass)):
            raise InvalidSupplementaryClassException

        cls._supplemetary_classes.append(model)
        access_name = getattr(model.Meta, "access_name", case_convert(model.__name__))
        setattr(
            cls,
            access_name,
            classmethod(
                property(
                    (model.get_latest),
                )
            ),
        )
        setattr(
            cls,
            model.__name__,
            model,
        )
        return model

    class Meta:
        abstract = True


class BasePostingRule(SupplymentaryClassAdderMixin):

    def post(self, event: BaseEvent):
        raise NotImplementedError

    class Meta:
        abstract = True


class BasePostingRuleRoutingStrategy:
    def get_posting_rule(self, event):
        raise NotImplementedError


class BaseEventPostingRuleRouter(SupplymentaryClassAdderMixin):
    posting_rules_routing_stratageis: Dict[str, BasePostingRuleRoutingStrategy] = (
        OrderedDict()
    )

    @classmethod
    def add_strategy(cls, stratagey: BaseEventPostingRuleRouter):
        if stratagey.__class__.__name__ not in cls.posting_rules_routing_stratageis:
            cls.posting_rules_routing_stratageis[stratagey.__class__.__name__] = (
                stratagey
            )

        return stratagey

    @classmethod
    def get_posting_rule(cls, event: BaseEvent) -> BasePostingRule:
        for stratagey in cls.posting_rules_routing_stratageis.values():
            if posting_rule := stratagey().get_posting_rule(event):
                return posting_rule


class BaseEvent(models.Model, SupplymentaryClassAdderMixin):

    _router: BaseEventPostingRuleRouter
    _env_router_registered: bool = False

    def process(self):
        posting_rule = self._router.get_posting_rule(self)

        if not posting_rule:
            raise NoMatchingPostingRuleException

        return posting_rule().post(self)

    @classmethod
    def register_posting_rule_router(cls, router: BaseEventPostingRuleRouter):

        if not issubclass(router, BaseEventPostingRuleRouter):
            raise InvalidPostingRuleRouter

        if hasattr(cls, "_router") and cls._router is not None:
            raise MultipleRouterException

        setattr(cls, "_router", router)
        print(f"Router {router} registered")
        return router

    @classmethod
    def register_posting_rule_router_env(cls, router: str):
        if cls._env_router_registered:
            raise MultipleRouterException

        router_cls = import_string(router)

        if not issubclass(router_cls, BaseEventPostingRuleRouter):
            raise InvalidPostingRuleRouter

        cls._router = router_cls
        cls._env_router_registered = True

        return router_cls

    class Meta:
        abstract = True


class BaseEntry(models.Model, SupplymentaryClassAdderMixin):

    class Meta:
        abstract = True
