"""Canonical intent-stage delegation doctrine and approval rubric.

Interview capture and every intent reviewer import these exact words. This is
kept with the cross-module contract so elicitation and review cannot define
opposing meanings of a complete intent.
"""

DELEGATION_DOCTRINE = """The founder owns product intent: the problem, audience, core value, scope,
and product-level quality intent. The engineering process owns discovery of current external facts
and implementation methods. A founder answer such as 'you decide' or 'up to you' records a delegated
gap; it must become a research brief owned by the spec/architecture stage, not a repeated founder
question and not not_applicable. Declared open questions remain visible gaps. Neither a recorded
delegation nor a declared open question is missing intent."""

INTENT_GATE_RUBRIC = """APPROVE when the problem, audience, core value, and scope are clear and every
remaining gap is recorded either as (a) a research brief / FOUNDER-DELEGATED item owned by a downstream
stage, or (b) a declared open question. REJECT only for an unclear problem, unclear audience or core
value, contradictory scope, or material ambiguity that is neither delegated nor declared.
Do NOT require the intent artifact to choose APIs, historical data sources, data-quality standards,
cloud providers/deployment methods, model-verification methods, or other engineering solutions.
Do NOT reject merely because done criteria or quantitative targets are delegated or declared open;
the downstream stage must propose the method or target per requirement and the founder reviews it at
the gate. Never silently resolve gaps from model memory."""


def intent_gate_instructions() -> str:
    return DELEGATION_DOCTRINE + "\n\n" + INTENT_GATE_RUBRIC
