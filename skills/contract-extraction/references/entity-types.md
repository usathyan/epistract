# Entity Types Quick Reference

12 entity types for the Contract Analysis extraction domain.

| Type | Description | Naming Standard | Key Attributes | Example |
|---|---|---|---|---|
| PARTY | Organizations, companies, or individuals that are parties to the contract | Full legal name from preamble/signature block | role, legal_name, dba, contact | Aramark Sports & Entertainment Services, LLC |
| OBLIGATION | Actionable requirements, duties, or commitments a party must fulfill | Action verb + what must be done | responsible_party, action, condition, section_reference | Provide catering services for all event meals |
| DEADLINE | Specific dates, time periods, or temporal milestones | Date + what is due | date, what_is_due, responsible_party, consequence | Final headcount due by August 1, 2026 |
| COST | Financial amounts, fees, rates, and payment terms | Amount + what it covers | amount, currency, unit, payment_terms, is_penalty | $45 per person for lunch service |
| CLAUSE | Legal terms, conditions, provisions, and boilerplate | Clause type or section header | clause_type, section_number, key_terms | Force Majeure provision |
| SERVICE | Services, products, or deliverables being provided | Description of what is provided | provider, scope, exclusions, category | Full-service catering for 500 guests |
| VENUE | Physical locations, spaces, rooms, and facilities | Specific space name | facility, room_or_space, capacity, dimensions | Hall A, Pennsylvania Convention Center |
| COMMITTEE | Organizational committees responsible for event planning areas | Committee name | name, responsibility_area, volunteer_count, source_document | Food Committee |
| PERSON | Named individuals with roles in event planning or contracts | Full name with role | name, title, role, committee, contact | Jane Smith, Chair Food Committee |
| EVENT | Scheduled programs, shows, forums, dining events, or activities | Event name | name, date, time, expected_attendance, location, requirements | Main Stage Show Friday Night |
| STAGE | Performance or presentation stages within the venue | Stage name | name, location, dimensions, equipment | Stage A Main Hall |
| ROOM | Specific rooms, ballrooms, or meeting spaces within the venue | Room name or number | name, number, capacity, floor, facility | Ballroom B |

## Detailed Attributes

### PARTY

| Attribute | Description | Example |
|---|---|---|
| `role` | Contractual role | "Exclusive Caterer", "Licensor", "Client" |
| `legal_name` | Full legal entity name | "Aramark Sports & Entertainment Services, LLC" |
| `dba` | Doing business as | "Aramark" |
| `contact` | Contact person | "John Smith, Event Coordinator" |
| `address` | Business address | "1101 Market Street, Philadelphia, PA 19107" |

### OBLIGATION

| Attribute | Description | Example |
|---|---|---|
| `responsible_party` | Who must fulfill | "Aramark" |
| `action` | What must be done | "Provide all food and beverage services" |
| `condition` | Trigger or prerequisite | "Upon receipt of final headcount" |
| `priority` | Mandatory vs optional | "mandatory" |
| `section_reference` | Contract section | "Article IV, Section 4.2" |

### DEADLINE

| Attribute | Description | Example |
|---|---|---|
| `date` | Specific date or period | "August 1, 2026" |
| `what_is_due` | Tied action/deliverable | "Final headcount submission" |
| `responsible_party` | Who must meet this | "Sample 2026 Planning Committee" |
| `consequence` | If missed | "Menu selections revert to standard package" |
| `type` | Deadline category | "milestone", "cutoff", "effective_date" |

### COST

| Attribute | Description | Example |
|---|---|---|
| `amount` | Dollar amount or rate | "$45.00" |
| `currency` | Currency | "USD" |
| `unit` | Rate basis | "per person", "per hour", "flat fee" |
| `covers` | What cost pays for | "Lunch service including setup and cleanup" |
| `payment_terms` | Payment schedule | "Net 30 days from invoice" |
| `is_penalty` | Penalty flag | "true" for cancellation fees, late charges |
| `tax_status` | Tax treatment | "plus 8% sales tax" |

### CLAUSE

| Attribute | Description | Example |
|---|---|---|
| `clause_type` | Type of provision | "force_majeure", "exclusivity", "indemnification" |
| `section_number` | Reference | "Article XII" |
| `key_terms` | Critical terms | "Neither party liable for acts of God" |
| `applies_to` | Scope | "Both parties" |

### SERVICE

| Attribute | Description | Example |
|---|---|---|
| `provider` | Service provider | "Aramark Sports & Entertainment Services, LLC" |
| `scope` | What is included | "All food and beverage for 3-day event" |
| `exclusions` | Not included | "Alcohol service requires separate license" |
| `specifications` | Requirements | "Vegetarian and non-vegetarian options required" |
| `category` | Service type | "catering", "av_production", "security" |

### VENUE

| Attribute | Description | Example |
|---|---|---|
| `facility` | Parent facility | "Pennsylvania Convention Center" |
| `room_or_space` | Specific area | "Hall A" |
| `capacity` | Max occupancy | "3,000 theater-style" |
| `dimensions` | Size | "108,000 sq ft" |
| `access_restrictions` | Access rules | "Loading Dock B only, union labor required" |
| `floor_level` | Level | "Level 1" |

### COMMITTEE

| Attribute | Description | Example |
|---|---|---|
| `name` | Committee name | "Food Committee" |
| `responsibility_area` | Area of oversight | "All catering and food service logistics" |
| `volunteer_count` | Number of volunteers | "25" |
| `source_document` | Planning document reference | "Sample_Conference_Master.md" |

### PERSON

| Attribute | Description | Example |
|---|---|---|
| `name` | Full name | "Jane Smith" |
| `title` | Formal title | "Chair" |
| `role` | Functional role | "Food Committee Chair" |
| `committee` | Committee affiliation | "Food Committee" |
| `contact` | Contact information | "jsmith@example.com" |

### EVENT

| Attribute | Description | Example |
|---|---|---|
| `name` | Event name | "Main Stage Show Friday Night" |
| `date` | Scheduled date | "September 5, 2026" |
| `time` | Scheduled time | "7:00 PM - 10:00 PM" |
| `expected_attendance` | Anticipated attendees | "2,500" |
| `location` | Where held | "Hall A, Main Stage" |
| `requirements` | Event needs | "AV, catering, security, stage setup" |

### STAGE

| Attribute | Description | Example |
|---|---|---|
| `name` | Stage name | "Stage A" |
| `location` | Where in venue | "Hall A, north end" |
| `dimensions` | Stage size | "40ft x 24ft x 4ft" |
| `equipment` | Technical equipment | "16-channel sound board, LED backdrop, 4 follow spots" |

### ROOM

| Attribute | Description | Example |
|---|---|---|
| `name` | Room name | "Ballroom B" |
| `number` | Room number | "201" |
| `capacity` | Max occupancy | "500 theater-style, 300 banquet" |
| `floor` | Floor level | "Level 2" |
| `facility` | Parent facility | "Pennsylvania Convention Center" |

## Disambiguation Quick Reference

| Ambiguity | Rule | Example |
|---|---|---|
| OBLIGATION vs CLAUSE | Use OBLIGATION for actionable requirements with "shall/must/will" and a responsible party. Use CLAUSE for legal terms, conditions, and boilerplate. | "Caterer shall provide all meals" -> OBLIGATION; "Neither party liable for acts of God" -> CLAUSE |
| COST vs PENALTY | Use COST for standard pricing. Use COST with `is_penalty: true` for late fees, cancellation charges. | "$45/person lunch" -> COST; "$5,000 cancellation fee" -> COST (is_penalty: true) |
| SERVICE vs VENUE | Use SERVICE for activities/deliverables (what is done). Use VENUE for physical spaces (where). | "Full-service catering" -> SERVICE; "Hall A" -> VENUE |
