# Notes for Discussion with Eric Little

*Private — not part of the public addendum.*

## How My Findings Map to Eric's Core Arguments

1. **Triple-level annotation is insufficient** — confirmed. Confidence scores collapse 5+ distinct epistemic categories into one number.

2. **Graph-level inference patterns exist** — confirmed. The BFS-based hypothesis detection finds connected components of epistemic relations that form coherent conjectures (3-8 relations each).

3. **Scalability concerns are real** — confirmed. Annotating 2,230 relations individually is feasible; the structural value comes from the 6 hypotheses and 2 contradictions that emerge as higher-order patterns.

4. **Base domain / Super Domain separation is natural** — confirmed. **97.7% of the relations are brute facts** (base domain). **The 2.3% that are epistemic** benefit most from being separated into a distinct layer where they can be queried, contested, and evolved independently.

5. **Document type determines epistemic signature** — a novel finding supporting Super Domains. **Patent claims and paper hypotheses occupy fundamentally different epistemic containers**, even when they reference the same entities and relations.

## Open Questions for Eric

1. How should the Super Domain handle "contested" relations — where some sources assert and others hedge? Is this a single Super Domain entry with mixed provenance, or does each perspective get its own entry?

2. Should the Super Domain be queryable independently? (e.g., "Show me all hypotheses about PICALM" vs. "Show me the base domain only")

3. Does the BFS-based hypothesis grouping (connected components of epistemic relations) align with how Super Domains should identify graph-level patterns, or is a more structured approach needed?
