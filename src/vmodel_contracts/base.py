"""Base model every contract derives from.

Each payload carries `contract_version` so a consumer can reject (or migrate)
a payload produced against a different contract release. Producers fill it
automatically; consumers validate it.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .version import CONTRACT_VERSION


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    contract_version: str = Field(
        default=CONTRACT_VERSION,
        description="Version of vmodel-contracts this payload was produced against.",
    )
