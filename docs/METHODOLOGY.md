# Brand Decision System — Methodology Document

> **STATUS:** Awaiting agency expert input. This document is the contract between the expert's brand-discovery methodology and the engineering implementation. Engineering sessions that need methodology will pause at the CLAUDE.md §7 stop-and-ask gate until this document contains the relevant section.

## 1. Purpose

This document captures the WHY of the Brand Decision System's input layer. Every question in the canonical questionnaire, every entry in the pain taxonomy, every rule in the rules engine, and every line in the language register resolver derives from methodology recorded here.

The audience for this document is:
- The technical lead implementing the system
- Future contributors who need to evolve the questionnaire or rules
- The agency expert revisiting their own decisions later

## 2. Question Typology

> *To be authored by the agency expert.* Captures the categories of questions used in the questionnaire (e.g., factual, perceptual, aspirational, comparative, tensional) and what each type captures.

## 3. Answer Mechanics

> *To be authored by the agency expert.* Captures slider mechanics, multi-choice mechanics, free-text usage, and conditional branching rules.

## 4. Insight-Design Principles

> *To be authored by the agency expert.* Captures the implicit rules the expert applies when authoring a question — e.g., no leading questions, tension surfaces insight, no jargon for the client.

## 5. Section Structure

> *To be authored by the agency expert.* Captures the thematic sections of the questionnaire and why they exist in that order.

## 6. The Questionnaire

> *To be authored by the agency expert.* Full content of the questionnaire, both languages, with rationale per question. Authoritative copy lives in `content/questionnaires/<version>/`; this section may reference those files rather than duplicating them.

## 7. The Pain Taxonomy

> *To be authored by the agency expert.* The fixed set of pain categories, each with identifier, description, and example brand-situation that matches.

## 8. Pain-Tagging Logic

> *To be authored by the agency expert.* High-level explanation of how questionnaire answers map to pain categories. Authoritative rules live in `content/pain_rules.yaml`; this section explains the why.

## 9. Language Register Resolver Logic

> *To be authored by the agency expert.* High-level explanation of how Brand DNA Profile fields map to a Language Register directive. Authoritative rules live in `content/register_rules.yaml`; this section explains the why.

## 10. Session System Prompt Structure

> *To be authored by the agency expert and engineering jointly.* Captures the unified preamble template, the per-module extensions, and the slot semantics.

## 11. Glossary

> *To be authored as terms emerge.*

## 12. Change Log

| Date | Author | Change |
|---|---|---|
| 2026-04-28 | engineering | PainAnalysis: llm_call_record_id → llm_call_record_ids (multi-call support); added register_id (audit traceability). Decided before first migration to avoid retroactive data migration. |
