# Domain Relation Types

## EXPERIENCED
A Patient experienced an AdverseEvent.

## TOOK
A Patient took a Drug or Concomitant prior to or during the AdverseEvent window.

## INDICATED_FOR
A Drug is indicated for an Indication (the prescribed reason for use).

## CO_ADMINISTERED_WITH
A Drug was co-administered with a Concomitant during the same exposure window. Symmetric — material to drug-drug interaction signal detection.

## REPORTED_BY
A ReportType / case was reported by a Reporter. Reporter identity (HCP, consumer, lawyer, sponsor) conditions epistemic weight.

## RESULTED_IN
An AdverseEvent resulted in an Outcome (recovered, sequelae, fatal, unknown).

## OCCURRED_AFTER
An AdverseEvent occurred after a Drug exposure with a stated TemporalRelationship. Foundation of the temporality criterion.

## RESOLVED_ON_DECHALLENGE
An AdverseEvent resolved when the suspect Drug was withdrawn — captured via a DechallengeRechallenge entity.

## RECURRED_ON_RECHALLENGE
An AdverseEvent recurred when the suspect Drug was reintroduced — captured via a DechallengeRechallenge entity. Strongest single-case causality signal.

## CAUSED_BY
An AdverseEvent is asserted to be caused by a Drug. Asserted only when Bradford-Hill criteria are met or when the source explicitly attributes causation.

## TRIGGERED
A CausalitySignal or AdverseEvent cluster triggered a RegulatoryAction (label change, withdrawal, REMS).

## CONTRADICTS
A claim from one report or database contradicts a claim from another (e.g., FAERS-asserted causation contradicted by EudraVigilance dechallenge-negative case). Symmetric across the contradicting pair.
