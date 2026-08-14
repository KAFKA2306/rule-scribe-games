# Issue #100 perceived-performance audit

Date: 2026-08-14

This document records the client-side request waterfall found while auditing `/games/:slug` and `/lists`, together with the regression gates added by #100. Counts below are request initiations implied by the pre-change code and are verified after the change by Playwright route counters.

## Before

| Flow | Pre-change request shape | Problem |
| --- | --- | --- |
| Open `/games/:slug` | `GamePage` GET `/api/games/:slug` + `GameListSavePortal` GET of the same path | 2 client GET initiations for one canonical game |
| Initial `/lists` | GET `/api/lists`, then GET selected list/owned detail | 2 dependent stages; detail waits for index |
| Switch custom list | GET `/api/lists`, then GET `/api/lists/:id` | Index is fetched again although already known |
| Mutation feedback | Component-specific `busy` coverage | rename/delete/reorder/remove did not share a complete single-flight contract |
| Failed request | fetch had no client deadline | UI could wait indefinitely on a stalled request |

## After / release gates

| Metric | Gate |
| --- | --- |
| Same game GET while `GamePage` and action portal resolve | exactly **1 underlying fetch**; concurrent GETs are coalesced and a successful GET is reusable for 2 seconds |
| `/lists` bootstrap | index and selected detail start within **100 ms** of each other in controlled E2E |
| Custom-list switch | **0 additional `/api/lists` index fetches**; only selected detail is requested |
| Mutation duplicate-click | identical method/path/body is **single-flight**; controlled double click produces exactly **1 mutation request** |
| Operation feedback | button enters busy state by the next animation frame, asserted **<100 ms** |
| API wait bound | production default **15,000 ms**; timeout raises a retryable error instead of waiting indefinitely |
| Auth/list layout stability | controlled E2E cumulative layout shift **CLS < 0.1** |

## Instrumentation

Every API request dispatches an `api:timing` browser event containing path, method, duration, HTTP status, success/failure, timeout state, and whether the result came from the short-lived GET cache. This is intentionally browser-local telemetry: no user token or response payload is emitted.

Mutations clear the GET cache after success, so the 2-second reuse window cannot serve pre-mutation list state. Server-side uniqueness/RLS constraints remain the authority for data integrity; client single-flight is only a perceived-performance and duplicate-submit guard.
