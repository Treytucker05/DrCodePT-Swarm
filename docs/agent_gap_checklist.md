# DrCodePT-Swarm Agent Gap Checklist

## 0) Mode Separation (Critical)
- [ ] Planning/reflection uses reason_json (no exec profile)
- [ ] Tool execution only uses exec profile

## 1) Perception (GUI Grounding)
- [ ] web_find_elements / web_click / web_type / web_close_modal available
- [ ] desktop_som_snapshot / desktop_click available
- [ ] Post-action verification screenshot for GUI actions

## 2) Execution Reliability
- [ ] PlanStep supports preconditions/postconditions
- [ ] Preconditions enforced before tool calls
- [ ] Postconditions verified after tool calls
- [ ] Alternate grounding attempted on failure

## 3) Planning Upgrades
- [ ] DPPM-lite decomposition → plan → merge
- [ ] ToT-lite multi-plan scoring with fallback

## 4) Reflection → Learning
- [ ] Reflection schema includes failure_type, lesson, memory_write
- [ ] Lessons stored as procedure/experience memory

## 5) Memory (RAG)
- [ ] Embedding-backed memory store
- [ ] Semantic top‑k + recency retrieval

## 6) Robustness
- [ ] Stuck detection for unchanged state
- [ ] Popup handler + resnapshot
- [ ] Exploration policy (scroll/search/rescan)

## 7) Evaluation Harness
- [ ] `tasks/` has ≥10 tasks
- [ ] Benchmark runner saves traces and metrics

## 8) Safety Hardening
- [ ] Approval required for delete/move outside workspace
- [ ] Shell allowlist + approval
- [ ] Credential entry approval gate
- [ ] Global kill switch
