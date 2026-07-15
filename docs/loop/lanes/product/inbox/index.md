# Product Inbox Index

Append-only delivery log for inbox/new. One row per atomically delivered
message. Readers process inbox/new, then move each file to inbox/cur.

| delivered_at | message_id | request_id | iteration | from_lane | message_type | state |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-14T07:13:05Z | REQ-20260714-064051-data-eng--IMPLEMENTATION_DONE--iter-2 | REQ-20260714-064051-data-eng | 2 | data-eng | IMPLEMENTATION_DONE | new |
| 2026-07-14T18:23:36Z | REQ-20260714-064051-data-eng--IMPLEMENTATION_DONE--iter-3 | REQ-20260714-064051-data-eng | 3 | data-eng | IMPLEMENTATION_DONE | cur |
| 2026-07-15T08:14:01Z | REQ-20260714-064051-data-eng--IMPLEMENTATION_DONE--iter-4 | REQ-20260714-064051-data-eng | 4 | data-eng | IMPLEMENTATION_DONE | cur |
| 2026-07-15T08:43:00Z | REQ-20260715-082547-data-eng--IMPLEMENTATION_DONE--iter-1 | REQ-20260715-082547-data-eng | 1 | data-eng | IMPLEMENTATION_DONE | new |
| 2026-07-15T09:03:09Z | REQ-20260715-082547-data-eng--IMPLEMENTATION_DONE--iter-2 | REQ-20260715-082547-data-eng | 2 | data-eng | IMPLEMENTATION_DONE | new |
| 2026-07-15T09:09:45Z | REQ-20260715-082547-data-eng--REVIEW_DONE--iter-2 | REQ-20260715-082547-data-eng | 2 | review | REVIEW_DONE | new |
| 2026-07-15T09:38:19Z | REQ-20260715-091230-frontend--IMPLEMENTATION_DONE--iter-1 | REQ-20260715-091230-frontend | 1 | frontend | IMPLEMENTATION_DONE | new |
| 2026-07-15T10:02:09Z | REQ-20260715-091230-frontend--IMPLEMENTATION_DONE--iter-2 | REQ-20260715-091230-frontend | 2 | frontend | IMPLEMENTATION_DONE | new |
| 2026-07-15T10:08:24Z | REQ-20260715-091230-frontend--REVIEW_DONE--iter-2 | REQ-20260715-091230-frontend | 2 | review | REVIEW_DONE | new |
