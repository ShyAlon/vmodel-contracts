# Method pack - systems-engineering interview and requirements knowledge

Distilled and RESTATED in our own words from the IEEE SWEBOK Guide v4.0a,
Software Requirements knowledge area (no verbatim excerpts; IEEE copyright
2014-2025, educational use with citation - https://computer.org/swebok).
Secondary framing: NASA Systems Engineering Handbook (public domain).

This pack is static context for prompts. It shapes QUESTIONS and QUALITY BAR;
it never answers for the founder and never becomes a need by itself.

## 1. Requirement kinds and the NFR taxonomy

A requirement is a condition or capability a user needs to solve a problem, or
one a system must meet to satisfy a contract or standard - and its documented
representation.

- Functional: observable behaviors - policies to enforce and processes to
  carry out ("an account balance never goes negative", "deposit/withdraw/
  transfer semantics").
- Nonfunctional: split into (a) technology constraints - mandated platform,
  stack, environment; and (b) quality-of-service constraints - the -ilities.

Quality-of-service taxonomy, with the probe question for each:
- Performance: latency, throughput, freshness. Ask: "how stale can the data be
  before it stops being useful?"
- Reliability/availability: failure modes, recovery. Ask: "what happens when
  this dependency is down at the worst moment?"
- Security: authentication, authorization, data protection. Ask: "who must
  NOT be able to see or do this?"
- Privacy: PII collection, retention, flows. Ask: "where does personal data
  go, and where must it never go?"
- Usability/accessibility: who is excluded if we ignore this?
- Scalability/capacity: volumes, growth. Ask: "what breaks first at 10x?"
- Maintainability/portability: who changes this later, and how often?
- Compliance: standards and regulations that apply by domain or geography.

Nonfunctional requirements interact: improving one can degrade another
(security vs latency). When one changes, ask what else it drags.

Quantified quality targets have a perfection point (beyond which nobody cares)
and a fail point (below which the system is useless). Elicit the FAIL point
("what number makes this not worth using?"), not the wish number - the fail
point is the requirement; the wish number is aspiration.

## 2. Elicitation discipline

- Incompleteness is the default failure mode. There is no complete elicitation;
  the job is to minimize what is missed. Treat a short interview as suspicious.
- Elicitation is active, not passive. Stakeholders leave important things
  unstated (tacit knowledge), struggle to describe their work, and sometimes
  cannot cooperate. Probe the obvious - the obvious is what gets omitted.
- Stakeholders come in CLASSES, not just the founder: end users (split by
  frequency, skill, privilege), operators, support, integrators, subject-matter
  experts, regulators, and people negatively affected if the project succeeds.
  Ask: "who else touches this, and who is hurt if it works?"
- Requirements come from non-person sources too: prior systems, interfacing
  systems, organizational policy, standards, the computing environment. Ask:
  "what do the existing tools force on you?"
- Press-once rule: when the founder waves away a consistency, conflict, or
  accuracy question, press exactly once with a concrete counterexample from
  their own scenario. If it is still waved away, capture the claim as an
  ASSUMPTION (asserted, validated later, never built as a need) and move on.
- Needs vs assumptions: a need is something the founder will verify the system
  does; an assertion about the world ("these sources never disagree") is an
  assumption - it goes in the assumption register, not the needs list.

## 3. Well-formed requirements (the quality bar for spec-generator)

Each requirement should be:
- unambiguous - interpretable in exactly one way;
- testable - quantified so compliance can be demonstrated, not argued;
- atomic - one decision per requirement, one "shall";
- binding - the founder would pay to keep it and object to losing it;
- a real stakeholder need - traced to a captured need, never invented;
- in stakeholder vocabulary - founder language in needs, system language only
  in requirements;
- acceptable to stakeholders - conflicts negotiated, not silently picked.

Write "the system SHALL ..." with a machine-checkable criterion for every
requirement. Banned vague words: "fast", "user-friendly", "appropriate",
"adequate", "robust", "minimal", "as needed" - each must be replaced by a
number, a named behavior, or an explicit open question.

## 4. Conflict and scope discipline

- More stakeholders means more conflicting requirements; expect conflict,
  surface it, never resolve it unilaterally. Negotiate with the founder and
  keep the resolution traceable to them (their call, recorded).
- Scope tension is product requirements vs project constraints (cost,
  schedule, staffing). Name which side each statement belongs to; constraints
  limit the design space, they are not requirements.
- Explicit out-of-scope is load-bearing: silence about the boundary is how
  specs balloon. Candidate exclusions are always inferable; "none" must be
  said out loud, not left blank.

## 5. Lifecycle mapping (how this pack lands in the V-model)

Interview elicits needs (founder language). Distillation classifies them and
draws the scope boundary. Spec-generator derives verifiable requirements from
approved needs. Verification-loop checks each requirement by its criterion.
The traceability chain (SN -> N -> R -> SPEC -> T) is what makes "where did
this come from" answerable at every stage.
