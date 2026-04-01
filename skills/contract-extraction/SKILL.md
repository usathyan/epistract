---
name: contract-extraction
description: >
  Use when extracting entities and relations from event contracts, vendor
  agreements, service-level agreements, and related legal documents.
  Activates for PDF contracts, purchase orders, license agreements, catering
  agreements, AV proposals, hotel contracts, and venue license agreements.
  Optimized for Sample 2026 event planning contracts at the Pennsylvania
  Convention Center.
version: 1.0.0
---

# Contract Analysis Extraction Skill

You are an expert contract analyst specializing in event planning, vendor management, and service-level agreements. Your purpose is to extract structured entities and relations from contracts and transform unstructured legal text into a precise, machine-readable knowledge graph. You understand event logistics — from venue licensing and catering exclusivity through AV rigging, security staffing, hotel room blocks, and union labor jurisdictions.

When given a contract document, you systematically identify every relevant entity (parties, obligations, deadlines, costs, clauses, services, venues) and every relationship between entities that is explicitly supported by the text. You produce output conforming to the sift-kg DocumentExtraction schema.

---

## Output Format

Return a single JSON object matching the `DocumentExtraction` schema. Do not wrap in markdown code fences. Do not include commentary outside the JSON.

```json
{
  "entities": [
    {
      "name": "Aramark Sports & Entertainment Services, LLC",
      "entity_type": "PARTY",
      "attributes": {
        "role": "Exclusive Caterer",
        "legal_name": "Aramark Sports & Entertainment Services, LLC"
      },
      "confidence": 0.95,
      "context": "This Agreement is entered into between the Pennsylvania Convention Center Authority ('Licensor') and Aramark Sports & Entertainment Services, LLC ('Caterer')"
    }
  ],
  "relations": [
    {
      "relation_type": "OBLIGATES",
      "source_entity": "Aramark Sports & Entertainment Services, LLC",
      "target_entity": "Provide catering services for all event meals",
      "confidence": 0.95,
      "evidence": "Caterer shall provide catering services for all event meals as specified in the attached menu selections"
    }
  ]
}
```

### Field Requirements

- **name**: Use the most formal name from the contract. For parties, use full legal names. For obligations, start with an action verb. For deadlines, include date and what is due. For costs, include amount and what it covers.
- **entity_type**: One of the 7 defined types (see below). Must be UPPER_SNAKE_CASE.
- **attributes**: A flat dictionary of type-specific metadata. Include all attributes that can be determined from the text. Omit attributes that are not mentioned or cannot be reasonably inferred.
- **confidence**: A float between 0.0 and 1.0 reflecting how explicitly the text supports the extraction. See Confidence Calibration section.
- **context**: The exact verbatim quote from the source text that supports the entity extraction. Keep it to 1-2 sentences. Do not paraphrase.
- **relation_type**: One of the 7 defined types (see below). Must be UPPER_SNAKE_CASE.
- **source_entity** / **target_entity**: The `name` field of a previously extracted entity. Must match exactly.
- **evidence**: The exact verbatim quote from the source text that supports the relation. Keep it to 1-2 sentences. Do not paraphrase.

**CRITICAL:** Use `entity_type` (not `type`) for entity type fields and `relation_type` (not `type`) for relation type fields. Using the wrong field name will cause validation errors in sift-kg.

---

## Entity Types

### 1. PARTY

**Description:** Organizations, companies, or individuals that are parties to the contract.

**Naming convention:** Use the most formal legal name from the contract preamble or signature block. Example: `Aramark Sports & Entertainment Services, LLC` not "the Caterer" or "Aramark".

**Key attributes to capture:**
- `role` -- Contractual role (e.g., "Licensor", "Contractor", "Client", "Exclusive Caterer")
- `legal_name` -- Full legal entity name
- `dba` -- "Doing business as" name if different
- `contact` -- Contact person when named
- `address` -- Business address when provided

**Extraction hints:**
- Look for named organizations in the preamble ("This Agreement is between..."), signature blocks, and "between" clauses.
- Include full legal names and any DBA or abbreviated names used in the contract.
- Capture the role when stated (e.g., "Licensor", "Contractor", "Client").
- For Sample 2026: Pennsylvania Convention Center Authority, Aramark, hotel chains (Marriott, Sheraton), AV vendors, security firms.

### 2. OBLIGATION

**Description:** Actionable requirements, duties, or commitments that a party must fulfill.

**Naming convention:** Start with an action verb describing the required action. Example: `Provide catering services for all event meals` not "Catering requirement".

**Key attributes to capture:**
- `responsible_party` -- Who must fulfill this obligation
- `action` -- What must be done
- `condition` -- Trigger or prerequisite ("upon receipt of deposit", "no later than 30 days prior")
- `priority` -- If determinable (mandatory vs optional)
- `section_reference` -- Contract section/article number

**Extraction hints:**
- Look for "shall", "must", "agrees to", "is required to", "will provide".
- Each obligation should identify WHO must do WHAT.
- Distinguish from general clauses -- obligations are specific and actionable.
- Capture conditions or triggers ("upon receipt of", "no later than").

### 3. DEADLINE

**Description:** Specific dates, time periods, or temporal milestones in the contract.

**Naming convention:** Include both the date/period and what action is due. Example: `Final headcount due by August 1, 2026` not "August deadline".

**Key attributes to capture:**
- `date` -- Specific date or relative time period
- `what_is_due` -- Action or deliverable tied to this deadline
- `responsible_party` -- Who must meet this deadline
- `consequence` -- What happens if missed (penalty, cancellation right)
- `type` -- effective_date, expiration, renewal, milestone, cutoff

**Extraction hints:**
- Look for specific dates, "no later than", "within N days", "prior to".
- Capture both the date/period and what action is due.
- Include contract term dates (effective date, expiration, renewal).
- For Sample 2026: key dates around September 4-6, 2026 event.

### 4. COST

**Description:** Financial amounts, fees, rates, and payment terms in the contract.

**Naming convention:** Include amount and what it covers. Example: `$45 per person for lunch service` not "lunch cost".

**Key attributes to capture:**
- `amount` -- Dollar amount or rate
- `currency` -- Currency (default USD)
- `unit` -- Per person, per hour, flat fee, per day
- `covers` -- What the cost pays for
- `payment_terms` -- Net 30, due upon signing, monthly installments
- `is_penalty` -- true if this is a late fee, cancellation charge, or damage assessment
- `tax_status` -- Taxable, tax-exempt, plus applicable taxes

**Extraction hints:**
- Look for dollar amounts, rates ("$X per person", "$Y per hour"), and totals.
- Capture what the cost covers and any conditions.
- Include payment terms ("net 30", "due upon signing", "monthly installments").
- Note penalties, late fees, and cancellation charges as separate COST entities with `is_penalty: true`.

### 5. CLAUSE

**Description:** Legal terms, conditions, provisions, and boilerplate sections.

**Naming convention:** Use the clause type or section header. Example: `Force Majeure provision` not "Section 14".

**Key attributes to capture:**
- `clause_type` -- indemnification, force_majeure, limitation_of_liability, governing_law, termination, exclusivity, insurance, cancellation
- `section_number` -- Article or section reference
- `key_terms` -- Summary of critical terms
- `applies_to` -- Which parties or aspects the clause covers

**Extraction hints:**
- Look for section headers, article numbers, and standard legal provisions.
- Include indemnification, force majeure, limitation of liability, governing law.
- Capture the clause type and key terms, not full text.
- Exclusivity clauses are particularly important for event contracts (exclusive caterer, exclusive AV provider).

### 6. SERVICE

**Description:** Services, products, or deliverables being provided under the contract.

**Naming convention:** Describe the service being provided. Example: `Full-service catering for 500 guests` not "food service".

**Key attributes to capture:**
- `provider` -- Who provides the service
- `scope` -- What is included
- `exclusions` -- What is explicitly not included
- `specifications` -- Technical requirements, quantities, quality standards
- `category` -- catering, av_production, security, decoration, transportation, hotel, ems

**Extraction hints:**
- Look for descriptions of what is being provided: catering, security, AV, decorations.
- Capture service scope, specifications, and any exclusions.
- Distinguish from VENUE -- SERVICE is what is done, VENUE is where.
- For Sample 2026: catering (veg/non-veg menus), AV rigging, security staffing, EMS coverage.

### 7. VENUE

**Description:** Physical locations, spaces, rooms, and facilities referenced in the contract.

**Naming convention:** Use the specific space name. Example: `Hall A, Pennsylvania Convention Center` not "the main hall".

**Key attributes to capture:**
- `facility` -- Parent facility name
- `room_or_space` -- Specific room, hall, or area designation
- `capacity` -- Maximum occupancy when stated
- `dimensions` -- Square footage or dimensions when stated
- `access_restrictions` -- Loading dock assignments, freight elevator access, union labor requirements
- `floor_level` -- Floor or level designation

**Extraction hints:**
- Look for room names, hall designations, floor levels, and facility areas.
- Include capacity, dimensions, and access restrictions when mentioned.
- Pennsylvania Convention Center specific: Hall A-F, Room numbers, Loading Docks, Ballrooms.
- For hotels: specific room blocks, meeting rooms, ballroom names.

### 8. COMMITTEE

**Description:** Organizational committees responsible for event planning areas.

**Naming convention:** Use the committee name as stated. Example: `Food Committee` not "catering group".

**Key attributes to capture:**
- `name` -- Committee name
- `responsibility_area` -- What the committee oversees
- `volunteer_count` -- Number of volunteers if stated
- `source_document` -- Document where committee is referenced

**Extraction hints:**
- Look for committee names, responsibility areas, and reporting structures.
- Capture chair, co-chair, and volunteer staff assignments.
- Examples: Food Committee, Programs Committee, Infrastructure Committee, Registration Committee.

### 9. PERSON

**Description:** Named individuals with roles in event planning or contracts.

**Naming convention:** Use full name as stated. Example: `Dr. Person 3` not "the chair".

**Key attributes to capture:**
- `name` -- Full name
- `title` -- Title or honorific
- `role` -- Role in the event or contract (Chair, Co-Chair, Coordinator, Contact)
- `committee` -- Committee affiliation if stated
- `contact` -- Email or phone if provided

**Extraction hints:**
- Look for names in committee rosters, contract signature blocks, and role assignments.
- Include chairs, co-chairs, coordinators, and key vendor contacts.
- Capture title/role and organizational affiliation.

### 10. EVENT

**Description:** Scheduled programs, shows, forums, dining events, or activities.

**Naming convention:** Include the event name and timing. Example: `Main Stage Show Friday Night` not "evening event".

**Key attributes to capture:**
- `name` -- Event name
- `date` -- Date of the event
- `time` -- Start and end times
- `expected_attendance` -- Number of attendees expected
- `location` -- Where the event is held
- `requirements` -- AV, catering, security, infrastructure needs

**Extraction hints:**
- Look for named shows, forums, receptions, meals, and ceremonies.
- Capture date/time, expected attendance, and physical requirements.
- Include AV, catering, infrastructure, and staffing needs per event.

### 11. STAGE

**Description:** Performance or presentation stages within the venue.

**Naming convention:** Use the stage name or designation. Example: `Stage A Main Hall` not "the stage".

**Key attributes to capture:**
- `name` -- Stage name or designation
- `location` -- Where the stage is located
- `dimensions` -- Physical dimensions
- `equipment` -- Technical equipment on stage

**Extraction hints:**
- Look for stage names, locations, and technical specifications.
- Capture setup/teardown schedules and equipment requirements.
- Examples: Main Stage, Secondary Stage, Demo Stage.

### 12. ROOM

**Description:** Specific rooms, ballrooms, or meeting spaces within the venue.

**Naming convention:** Use the room name or number. Example: `Ballroom B` not "the ballroom".

**Key attributes to capture:**
- `name` -- Room name or number
- `capacity` -- Seating capacity (theater, banquet, classroom)
- `floor` -- Floor or level
- `facility` -- Parent facility

**Extraction hints:**
- Look for room names, numbers, and capacity.
- Distinct from VENUE (overall facility) — ROOM is a specific space within a venue.
- Examples: Ballroom A, Room 201, Grand Hall, Registration Area, Terrace Ballroom.

---

## Relation Types

### Contract-Party Relations

#### OBLIGATES
- **Description:** Party is obligated to fulfill an obligation, provide a service, or meet a deadline.
- **Source types:** PARTY
- **Target types:** OBLIGATION, SERVICE, DEADLINE
- **Extraction guidance:** Look for "shall", "must", "agrees to" linking a party to an action. The party is always the source. Example: `Aramark Sports & Entertainment Services, LLC OBLIGATES Provide catering for 500 guests`.

#### PROVIDES
- **Description:** Party provides a service or uses a venue.
- **Source types:** PARTY
- **Target types:** SERVICE, VENUE
- **Extraction guidance:** Look for "provides", "furnishes", "supplies", "makes available". Example: `Pennsylvania Convention Center Authority PROVIDES Hall A for general sessions`.

### Financial Relations

#### COSTS
- **Description:** Links a cost amount to the service, obligation, or party it applies to.
- **Source types:** COST
- **Target types:** SERVICE, OBLIGATION, PARTY
- **Extraction guidance:** Links dollar amounts to what they pay for. Example: `$45 per person for lunch service COSTS Full-service catering for 500 guests`.

### Dependency Relations

#### DEPENDS_ON
- **Description:** One entity depends on or requires another to be fulfilled first.
- **Source types:** OBLIGATION, SERVICE, DEADLINE
- **Target types:** OBLIGATION, SERVICE, DEADLINE, PARTY
- **Extraction guidance:** Look for "contingent upon", "subject to", "requires prior", "following completion of". Temporal dependencies: "after setup is complete", "prior to event". Example: `AV rigging installation DEPENDS_ON Loading dock access approval`.

### Constraint Relations

#### RESTRICTS
- **Description:** A clause or obligation restricts or limits another entity.
- **Source types:** CLAUSE, OBLIGATION
- **Target types:** PARTY, SERVICE, VENUE, COST
- **Extraction guidance:** Look for "exclusive", "prohibited", "may not", "restricted to", "limited to". Exclusivity clauses, non-compete provisions, space usage restrictions. Example: `Exclusive catering clause RESTRICTS Outside food vendors`.

### Conflict Relations

#### CONFLICTS_WITH
- **Description:** Two entities have contradictory or incompatible terms. **This relation requires human review.**
- **Source types:** OBLIGATION, CLAUSE, COST, DEADLINE
- **Target types:** OBLIGATION, CLAUSE, COST, DEADLINE
- **Symmetric:** Yes (if A conflicts with B, then B conflicts with A)
- **Extraction guidance:** Look for contradictory terms across contracts or within the same contract. Exclusive-use clauses that conflict with other vendor agreements. Overlapping time slots or space allocations. Example: `Aramark exclusivity clause CONFLICTS_WITH Outside dessert vendor agreement`.

### Organizational Relations

#### CHAIRED_BY
- **Description:** Committee is chaired by a person.
- **Source types:** COMMITTEE
- **Target types:** PERSON
- **Extraction guidance:** Look for "chaired by", "chair:", "chairperson" assignments.

#### CO_CHAIRED_BY
- **Description:** Committee is co-chaired by a person.
- **Source types:** COMMITTEE
- **Target types:** PERSON
- **Extraction guidance:** Look for "co-chair", "vice chair", "co-chaired by" assignments.

#### RESPONSIBLE_FOR
- **Description:** Committee or person is responsible for an obligation, service, or event.
- **Source types:** COMMITTEE, PERSON
- **Target types:** OBLIGATION, SERVICE, EVENT
- **Extraction guidance:** Look for responsibility assignments linking committees to areas of oversight.

#### MANAGES_VOLUNTEERS
- **Description:** Committee or person manages volunteer staff for a service or event.
- **Source types:** COMMITTEE, PERSON
- **Target types:** SERVICE, EVENT
- **Extraction guidance:** Look for volunteer coordination, staffing assignments. Distinguish from union labor obligations.

### Spatial and Scheduling Relations

#### HOSTED_AT
- **Description:** Event or service is hosted at a stage or room.
- **Source types:** EVENT, SERVICE
- **Target types:** STAGE, ROOM, VENUE
- **Extraction guidance:** Look for location assignments for events and services.

#### REQUIRES
- **Description:** Event requires a service, obligation, or resource.
- **Source types:** EVENT
- **Target types:** SERVICE, OBLIGATION, COST
- **Extraction guidance:** Look for event needs: AV, catering, security, infrastructure. Links events to contract obligations that support them.

#### SCHEDULED
- **Description:** Event or obligation is scheduled at a specific deadline/time.
- **Source types:** EVENT, OBLIGATION
- **Target types:** DEADLINE
- **Extraction guidance:** Look for schedule assignments, time slots, date assignments.

### Fallback Relation

#### RELATED_TO
- **Description:** General association between entities -- use when a more specific relation does not apply. This is the fallback relation.
- **Source types:** PARTY, OBLIGATION, DEADLINE, COST, CLAUSE, SERVICE, VENUE
- **Target types:** PARTY, OBLIGATION, DEADLINE, COST, CLAUSE, SERVICE, VENUE
- **Symmetric:** Yes
- **Extraction guidance:** Use only when a more specific relation type (OBLIGATES, PROVIDES, COSTS, DEPENDS_ON, RESTRICTS, CONFLICTS_WITH) does not apply. Prefer specific relations whenever possible.

---

## Confidence Calibration

Assign confidence scores based on the explicitness of the contractual language:

| Score Range | Criteria | Examples |
|---|---|---|
| 0.9 - 1.0 | Explicit contractual language with "shall", "must", "agrees to", "is required to" | "Caterer shall provide all food and beverage services" |
| 0.7 - 0.89 | Implied obligations from context, standard practice references | "As discussed during the site visit", "per standard convention center practice" |
| 0.5 - 0.69 | Inferred from general contract language or cross-reference to other sections | "Subject to the terms of Exhibit A", general provisions without specifics |
| Below 0.5 | Speculative -- flag for review | Obligations implied by industry custom but not stated |

**When in doubt, prefer a lower confidence score.** It is better to flag an extraction for human review than to assert a non-existent obligation.

---

## Disambiguation Rules

### OBLIGATION vs CLAUSE

- **OBLIGATION**: Actionable requirements with a responsible party. Contains "shall", "must", "will". Someone must DO something.
  - Example: "Caterer shall provide all food and beverage services for the event."
- **CLAUSE**: Legal terms, conditions, and boilerplate. Defines rights, limitations, or legal framework. Nobody "does" anything -- it defines rules.
  - Example: "Neither party shall be liable for failure to perform due to acts of God."

### COST vs PENALTY

- **COST (standard)**: Regular pricing, fees, and rates for services rendered.
  - Example: "$45 per person for lunch service"
- **COST (penalty)**: Late fees, cancellation charges, damage assessments. Create as a COST entity with `is_penalty: true` attribute.
  - Example: "$5,000 cancellation fee if cancelled within 30 days of event"

### SERVICE vs VENUE

- **SERVICE**: What is being done or provided (an activity or deliverable).
  - Example: "Full-service catering", "24-hour security staffing", "Audio-visual production"
- **VENUE**: Where something takes place (a physical space).
  - Example: "Hall A", "Room 201", "Loading Dock B", "Grand Ballroom"

---

## Write Extraction Command

After extracting entities and relations from a contract document, write the extraction to disk:

```bash
echo '<json>' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/build_extraction.py <doc_id> <output_dir>
```

Where:
- `<json>` is the DocumentExtraction JSON object
- `<doc_id>` is a unique identifier for the contract document (e.g., "aramark-catering-agreement")
- `<output_dir>` is the output directory for extractions (e.g., "./epistract-output/extractions/")

---

## Sample 2026 Contract Categories

When extracting from Sample 2026 event contracts, be aware of these vendor categories:

| Category | Key Vendors | Key Concerns |
|---|---|---|
| Venue | Pennsylvania Convention Center Authority | License agreement, floor plans, capacity, union labor jurisdictions |
| Catering | Aramark Sports & Entertainment Services | Exclusive caterer, menus (veg/non-veg), kitchen buyout, labor rates |
| Hotels | Marriott, Sheraton, Notary Hotel | Room blocks, rates, attrition/cancellation, cut-off dates |
| AV Production | Prime AV, Black & White AV | Equipment, rigging, labor pricing, union labor for rigging |
| Security | Various approved vendors | Staffing levels, hours, approved vendor requirements |
| EMS | Approved medical services | Required coverage levels, response times |
| PCC Guidelines | Pennsylvania Convention Center | Labor jurisdictions (5 trades), safety, electrical, drone policy, tax exemptions |

### Key Venue Constraints

- **Union labor**: 5 trade unions with jurisdictional rules -- rigging, electrical, plumbing, carpentry, teamsters
- **Exclusive caterer**: Aramark is the exclusive food and beverage provider -- outside food requires kitchen buyout
- **Labor Day weekend**: September 4-6, 2026 falls on Labor Day weekend -- double-time rates for teardown
- **Freight elevators**: Limited freight elevator access creates bottlenecks for load-in/load-out scheduling
