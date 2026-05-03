# Domain Entity Types

## Drug
A pharmaceutical product implicated in or co-administered during an adverse event report. Prefer the WHO ATC code as the canonical identifier when available; record INN, brand names, and manufacturer codes as aliases.

## AdverseEvent
A clinical event experienced by a patient temporally associated with drug exposure. Prefer the MedDRA Preferred Term (PT) as the canonical name; record reporter verbatim, MedDRA Lowest-Level Term (LLT), and ICD-10 cross-walks as aliases.

## Patient
The de-identified subject of an adverse event report. Captures age band, sex, weight band, and relevant medical history. Never store identifying information.

## Reporter
The party who submitted the adverse event report (physician, pharmacist, consumer, lawyer, manufacturer). Reporter type strongly conditions epistemic weight.

## Outcome
The clinical resolution of the adverse event — recovered, recovered with sequelae, not recovered, fatal, or unknown. Maps to ICH E2B outcome categories.

## ReportType
The provenance and structure of the report — spontaneous (FAERS, VAERS, EudraVigilance, MedWatch), case series, RCT meta-analysis, registry, post-marketing study, literature.

## TemporalRelationship
The time-to-onset relationship between drug exposure and event (e.g., immediate, hours, days, weeks, months) and any latency window relevant to causality assessment.

## Concomitant
A drug, supplement, or medical product co-administered with the suspect drug at the time of the adverse event. Material to confounder analysis and drug-drug interaction signal detection.

## Indication
The clinical reason for which the suspect drug was prescribed or taken. Distinguishes signal from underlying disease confounding.

## DechallengeRechallenge
Documentation of whether the event resolved when the drug was withdrawn (dechallenge) and whether it recurred when the drug was reintroduced (rechallenge). Positive dechallenge plus positive rechallenge is the strongest single-case causality signal.

## RegulatoryAction
An action taken by a regulator or sponsor in response to safety signals — label change, boxed warning, Dear Healthcare Provider letter, REMS, market withdrawal, suspension, or recall.

## CausalitySignal
An aggregate causality assessment derived from one or more reports — Bradford-Hill consistency, strength, temporality, biological plausibility, dose-response, specificity, coherence, analogy, and experiment.
