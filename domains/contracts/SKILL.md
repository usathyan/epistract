# Contract Analysis Domain

Extract structured knowledge from event contracts, vendor agreements, and service-level agreements.

## Entity Types

| Type | Description |
|------|-------------|
| PARTY | Organization or individual signatory |
| CONTRACT | Formal agreement between parties |
| OBLIGATION | Required action or compliance requirement |
| DEADLINE | Date or time constraint |
| COST | Monetary amount or payment term |
| VENUE | Physical location |
| SERVICE | Service provided under contract |
| INSURANCE | Insurance requirement or coverage |
| PENALTY | Consequence for breach |

## Relation Types

| Type | Description |
|------|-------------|
| OBLIGATED_TO | Party must fulfill obligation |
| HAS_DEADLINE | Obligation has a deadline |
| COSTS | Service has associated cost |
| SIGNED_BY | Contract signed by party |
| PROVIDES_SERVICE | Party provides service |
| HELD_AT | Event at venue |
| REQUIRES_INSURANCE | Contract requires insurance |
| CROSS_REFERENCES | Contract references another |
| PENALIZES | Breach triggers penalty |

## Extraction Guidelines

1. Every obligation must link to a responsible party and a deadline if specified
2. Costs should be extracted with currency and payment terms
3. Cross-contract references are high-value -- they reveal dependencies between vendors
4. Insurance requirements should capture coverage type and minimum amounts
5. Penalties should link to the specific obligation they enforce
