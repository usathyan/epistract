# Relation Types Quick Reference

7 relation types for the Contract Analysis extraction domain, grouped by category.

## Party-Action Relations

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|---|---|---|---|---|---|
| OBLIGATES | PARTY | OBLIGATION, SERVICE, DEADLINE | No | No | Aramark -> Provide catering for 500 guests |
| PROVIDES | PARTY | SERVICE, VENUE | No | No | PCC Authority -> Hall A for general sessions |

## Financial Relations

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|---|---|---|---|---|---|
| COSTS | COST | SERVICE, OBLIGATION, PARTY | No | No | $45/person -> Lunch catering service |

## Dependency Relations

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|---|---|---|---|---|---|
| DEPENDS_ON | OBLIGATION, SERVICE, DEADLINE | OBLIGATION, SERVICE, DEADLINE, PARTY | No | No | AV rigging -> Loading dock access approval |

## Constraint Relations

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|---|---|---|---|---|---|
| RESTRICTS | CLAUSE, OBLIGATION | PARTY, SERVICE, VENUE, COST | No | No | Exclusive catering clause -> Outside food vendors |

## Conflict Relations

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|---|---|---|---|---|---|
| CONFLICTS_WITH | OBLIGATION, CLAUSE, COST, DEADLINE | OBLIGATION, CLAUSE, COST, DEADLINE | Yes | Yes | Aramark exclusivity -> Outside dessert vendor |

## Fallback

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|---|---|---|---|---|---|
| RELATED_TO | All 7 entity types | All 7 entity types | Yes | No | General association when no specific type fits |

---

## Detailed Relation Descriptions

### OBLIGATES

**Description:** Party is obligated to fulfill an obligation, provide a service, or meet a deadline.

**Direction:** PARTY -> OBLIGATION / SERVICE / DEADLINE

**Trigger phrases:** "shall", "must", "agrees to", "is required to", "will provide", "is obligated to"

**Example triples:**
- `Aramark Sports & Entertainment Services, LLC` OBLIGATES `Provide catering services for all event meals`
- `Pennsylvania Convention Center Authority` OBLIGATES `Make Hall A available by August 30, 2026`
- `Marriott Philadelphia Downtown` OBLIGATES `Hold room block of 200 rooms through July 15, 2026`

---

### PROVIDES

**Description:** Party provides a service or makes a venue available.

**Direction:** PARTY -> SERVICE / VENUE

**Trigger phrases:** "provides", "furnishes", "supplies", "makes available", "offers"

**Example triples:**
- `Pennsylvania Convention Center Authority` PROVIDES `Hall A, Pennsylvania Convention Center`
- `Prime AV` PROVIDES `Audio-visual production for main stage`
- `Marriott Philadelphia Downtown` PROVIDES `Grand Ballroom for welcome reception`

---

### COSTS

**Description:** Links a cost amount to the service, obligation, or party it applies to.

**Direction:** COST -> SERVICE / OBLIGATION / PARTY

**Trigger phrases:** Dollar amounts followed by service descriptions, "fee for", "rate of", "priced at"

**Example triples:**
- `$45 per person for lunch service` COSTS `Full-service catering for 500 guests`
- `$2,500 flat fee for rigging` COSTS `Main stage AV rigging installation`
- `$189 per night room rate` COSTS `Marriott Philadelphia Downtown`

---

### DEPENDS_ON

**Description:** One entity depends on or requires another to be fulfilled first.

**Direction:** OBLIGATION / SERVICE / DEADLINE -> OBLIGATION / SERVICE / DEADLINE / PARTY

**Trigger phrases:** "contingent upon", "subject to", "requires prior", "following completion of", "after", "upon"

**Example triples:**
- `AV rigging installation` DEPENDS_ON `Loading dock access approval`
- `Final menu selection` DEPENDS_ON `Confirmed headcount submission`
- `Event setup` DEPENDS_ON `Pennsylvania Convention Center Authority` (venue must grant access)

---

### RESTRICTS

**Description:** A clause or obligation restricts or limits another entity.

**Direction:** CLAUSE / OBLIGATION -> PARTY / SERVICE / VENUE / COST

**Trigger phrases:** "exclusive", "prohibited", "may not", "restricted to", "limited to", "only authorized"

**Example triples:**
- `Exclusive catering provision` RESTRICTS `Outside food and beverage vendors`
- `Union labor jurisdiction clause` RESTRICTS `Non-union rigging labor`
- `Noise ordinance clause` RESTRICTS `Hall A sound levels after 10 PM`

---

### CONFLICTS_WITH

**Description:** Two entities have contradictory or incompatible terms. **Requires human review.**

**Direction:** Symmetric (bidirectional)

**Trigger phrases:** Identified by comparing terms across contracts -- contradictions, overlaps, incompatibilities

**Example triples:**
- `Aramark exclusivity clause` CONFLICTS_WITH `Outside dessert vendor agreement`
- `Hall A load-in deadline September 2` CONFLICTS_WITH `AV vendor setup requires September 1-3`
- `Security vendor staffing level: 15` CONFLICTS_WITH `PCC minimum security requirement: 20`

**Note:** CONFLICTS_WITH is the most analytically valuable relation for cross-contract analysis. It surfaces risks and contradictions that event planners must resolve.

---

### RELATED_TO

**Description:** General association between entities -- use when a more specific relation does not apply.

**Direction:** Symmetric (bidirectional)

**Trigger phrases:** None specific -- this is the fallback when OBLIGATES, PROVIDES, COSTS, DEPENDS_ON, RESTRICTS, and CONFLICTS_WITH do not fit.

**Example triples:**
- `Aramark Sports & Entertainment Services, LLC` RELATED_TO `Kitchen buyout fee`
- `Hotel room block` RELATED_TO `Event registration deadline`

**Usage note:** Always prefer a specific relation type. Use RELATED_TO only when no other type accurately captures the relationship. This is configured as the `fallback_relation` in domain.yaml.
