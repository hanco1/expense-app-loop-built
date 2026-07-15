# Frontend Inbox Index

Append-only delivery log for inbox/new. One row per atomically delivered
message. Readers process inbox/new, then move each file to inbox/cur.

| delivered_at | message_id | request_id | iteration | from_lane | message_type | state |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-15T09:13:51Z | REQ-20260715-091230-frontend--IMPLEMENTATION_REQUEST--iter-1 | REQ-20260715-091230-frontend | 1 | product | IMPLEMENTATION_REQUEST | cur |
| 2026-07-15T09:48:26Z | REQ-20260715-091230-frontend--FIX_REQUEST--iter-2 | REQ-20260715-091230-frontend | 2 | review | FIX_REQUEST | cur |
| 2026-07-15T19:58:20Z | REQ-20260715-091230-frontend--FIX_REQUEST--iter-3 | REQ-20260715-091230-frontend | 3 | product | FIX_REQUEST | cur |
