# Real-Agent Validation Data

This directory contains the healthcare-relevant sandbox validation data used for the lightweight real-agent experiments.

## Structure

- `raw_mimic_subset/`: small curated subset of deidentified MIMIC-IV-Note radiology reports
- `taxonomy_mapping.csv`: scenario taxonomy used in the paper
- `cases/`: case-specific workflow environments for the real-agent validation layer

## Design principles

- Real report text is used as the document substrate.
- Each case is a sandbox workflow task with local emails and document files.
- The case set is aligned with three axes:
  - Outcome
  - Mechanism
  - Structure

## Intended use

These cases are used only for lightweight real-agent validation and do not replace the main deterministic simulator.
