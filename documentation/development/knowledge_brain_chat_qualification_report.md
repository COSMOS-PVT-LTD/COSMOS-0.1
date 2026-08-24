# Knowledge Brain Chat Qualification Report

**Document ID:** `COSMOS-KB-CHAT-QUAL-001`  
**Date:** 2026-08-24  
**Freeze ID:** `KG-KF-WORKSPACE-BRAIN-2026-08-24`

```text
PRODUCTION-READY = NO
```

## Surface

`knowledge.brain.chat.KnowledgeConversationService` persists conversations under `{root}/conversations/`. Each turn records user/assistant messages, active sources, a `QueryPlan`, and an `EngineeringAnswer`.

There is **no generative LLM**. Answers are assembled from:

- `KnowledgeFoundationService.search` / `answer` (approved-ranked hybrid retrieval)
- workspace document evidence index (candidate ingested text)
- explicit solver-routing refusal when the user asks to calculate

## Multi-turn acceptance

Covered by `tests/unit_tests/knowledge/brain/test_chat_planner.py` and HTTP chat in `test_e2e_workspace.py`:

1. Ingest COSMOS cooling notes.
2. Ask what the document says about regenerative cooling → document evidence IDs returned.
3. Ask to compare sources → `COMPARISON_QUERY`, prior `active_sources` retained.
4. Ask which cooling correlation applies → seed Bartz evidence may appear; not fabricated.
5. Ask to run the calculation → `routed_to_solver=True`, no numeric invention.

Conversation `validation_state` remains `CONVERSATION` / answer `CANDIDATE` when document evidence is included. Chat text is not written into equation/law repositories.

## Residual

- No production assistant model, streaming, or multi-user auth.
- Planner is keyword/heuristic.
- Calculation routing does not invoke physics solvers; it only refuses to fake arithmetic.
