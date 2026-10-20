# Research coverage and evaluation

Use this checklist in every run. An explicit limitation completes a coverage record but does not turn missing research into a finding. Brief/standard/deep change the number of pages, competitors and observed states, not the mandatory categories. Standard research normally includes 3–5 journeys; deep research expands relevant states, devices, independent cross-checks and competitor coverage. Never promise a complete WCAG or security audit from a public product review.

| Schema category | Required questions and evidence |
| --- | --- |
| overview | Company, product type, geographic availability, background, purpose. Separate legal entity from brand. Attribute company history. |
| positioning | Messaging, value proposition, differentiation and promised benefits. Separate marketing claims from demonstrated differences. |
| audience_jtbd | Segments, jobs, needs, motivations, pains/gains. Distinguish stated audience, observed affordances and inferred personas. |
| customer_problems | Problems addressed and solutions offered. Attribute efficacy claims, particularly healthcare/finance. |
| functionality | Features, limits, integrations, workflows, access level and tested versus advertised capabilities. |
| products_services | Service categories, delivery methods, geography, eligibility, conditions and exclusions. |
| pricing | Price, currency, tax treatment, billing interval, region, plan limits, trials, renewals, commissions, cancellation and refund terms. Capture exact date/state, avoid annual/monthly equivalence without explicit calculation. |
| business_model | Revenue streams, monetization, subsidies, commissions and verified public finances. No estimated revenue labeled as actual. |
| marketing | Observed SEO/content/ads, public ad libraries, partnerships, referrals and channel evidence. A blog, pixel or social profile is not proof of acquisition performance. |
| user_journeys | Navigation, onboarding, search, registration/selection and checkout/conversion flows, plus industry-specific journeys. Record stop boundaries. |
| ux | All 10 Nielsen heuristics, friction, error handling, consistency, cognitive load; evidence and severity for each issue. Record untested heuristics in section limitations. |
| ui | Typography, spacing, hierarchy, contrast/colors, consistency, components and interaction states. Distinguish screenshot inspection from DOM measurement. |
| accessibility | Desktop/mobile states, keyboard, focus, contrast, semantics, labels, errors, zoom/reflow and relevant WCAG criteria. Include tested viewport, input method and measurement limits. |
| trust | Entity/contact transparency, credentials, reviews, reputation, privacy/security disclosures. A policy or badge alone does not establish security/compliance or clinical efficacy. |
| strengths_weaknesses_opportunities | Evidence-backed characteristics and limitations, competitive advantages, differentiation and market opportunities. Separate hypotheses using status/kind and facet. |

For custom requirements preserve the user's wording, create stable requirement IDs and dedicated sections/records. Split compound requests into independently checkable criteria without losing the original request. Missing data is a documented gap. For competitor comparisons, each product gets full coverage; use a shared comparison group and custom comparison criteria. For a comparative claim, include evidence for all compared sides in the same dataset (URLs may belong to competitors).

## Nielsen heuristics

1. Visibility of system status.
2. Match between system and the real world.
3. User control and freedom.
4. Consistency and standards.
5. Error prevention.
6. Recognition rather than recall.
7. Flexibility and efficiency of use.
8. Aesthetic and minimalist design.
9. Help users recognize, diagnose and recover from errors.
10. Help and documentation.

Severity anchors: **0** no usability problem; **1** cosmetic; **2** minor task friction with a reasonable workaround; **3** major obstruction or repeated recovery cost; **4** blocks a critical task in the tested conditions. Explain task importance, impact, persistence and observed reproducibility; unknown user frequency stays unknown. P0 immediate critical concern; P1 high impact; P2 planned improvement; P3 low priority. Severity and priority are related judgments, not measured conversion impact.

## Accessibility

Use the applicable WCAG version and level explicitly. WCAG 2.2 AA is a useful evaluation reference when the user does not specify another standard; verify current authoritative criteria when evaluating. Relevant examples include 1.1.1 text alternatives, 1.3.1 information/relationships, 1.4.3 contrast, 1.4.10 reflow, 1.4.11 non-text contrast, 2.1.1 keyboard, 2.4.3 focus order, 2.4.7 focus visible, 2.4.11 focus not obscured, 2.5.8 target size, 3.3.1 error identification, 3.3.2 labels/instructions and 4.1.2 name/role/value. Never infer keyboard or semantic support from screenshots. Distinguish automated results, manual observations and untested criteria. Reference: https://www.w3.org/TR/WCAG22/

## Evidence ledger and contradictions

Capture atomic observations, source location, date, method, viewport/state, access limits and screenshot where possible. `independence_group` identifies the underlying editorial/source origin: syndication or copies share a group. Independent domains alone do not prove independent evidence. A company page is appropriate for its published pricing and terms, not for proving revenue, user outcomes or channel effectiveness. A single review is evidence of that reviewer's account, not representative customer sentiment. Public review scores need platform, date and count; do not extrapolate demographics.

Resolve contradictions by inspecting timing, geography, plan/access level and authority. Keep qualifications and contradictory evidence attached to the claim. Explicitly mention unresolved differences. Protect sensitive data, respect access controls and stop before unauthorized side effects.
