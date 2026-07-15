# Review Inbox Index

Append-only delivery log for inbox/new. One row per atomically delivered
message. Readers process inbox/new, then move each file to inbox/cur.

| delivered_at | message_id | request_id | iteration | from_lane | message_type | state |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-14T07:01:20Z | REQ-20260714-064051-data-eng--LOOP_STATUS--iter-1 | REQ-20260714-064051-data-eng | 1 | product | LOOP_STATUS | new |
| 2026-07-14T07:13:05Z | REQ-20260714-064051-data-eng--REVIEW_REQUEST--iter-2 | REQ-20260714-064051-data-eng | 2 | data-eng | REVIEW_REQUEST | new |
| 2026-07-14T17:57:45Z | REQ-20260714-064051-data-eng--REVIEW_REQUEST--iter-3 | REQ-20260714-064051-data-eng | 3 | product | REVIEW_REQUEST | new |
| 2026-07-15T07:47:09Z | REQ-20260714-064051-data-eng--REVIEW_REQUEST--iter-4 | REQ-20260714-064051-data-eng | 4 | product | REVIEW_REQUEST | new |
| 2026-07-15T08:43:00Z | REQ-20260715-082547-data-eng--REVIEW_REQUEST--iter-1 | REQ-20260715-082547-data-eng | 1 | data-eng | REVIEW_REQUEST | new |
| 2026-07-15T09:03:09Z | REQ-20260715-082547-data-eng--REVIEW_REQUEST--iter-2 | REQ-20260715-082547-data-eng | 2 | data-eng | REVIEW_REQUEST | new |
| 2026-07-15T09:38:19Z | REQ-20260715-091230-frontend--REVIEW_REQUEST--iter-1 | REQ-20260715-091230-frontend | 1 | frontend | REVIEW_REQUEST | new |
| 2026-07-15T09:42:51Z | REQ-20260715-091230-frontend--VERIFY-MANIFEST--iter-1 | REQ-20260715-091230-frontend | 1 | product | IMPLEMENTATION_REQUEST | new |
| 2026-07-15T10:02:09Z | REQ-20260715-091230-frontend--REVIEW_REQUEST--iter-2 | REQ-20260715-091230-frontend | 2 | frontend | REVIEW_REQUEST | new |
