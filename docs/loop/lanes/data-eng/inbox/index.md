# Data Eng Inbox Index

Append-only delivery log for inbox/new. One row per atomically delivered
message. Readers process inbox/new, then move each file to inbox/cur.

| delivered_at | message_id | request_id | iteration | from_lane | message_type | state |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-14T06:42:36Z | REQ-20260714-064051-data-eng--IMPLEMENTATION_REQUEST--iter-1 | REQ-20260714-064051-data-eng | 1 | product | IMPLEMENTATION_REQUEST | new |
| 2026-07-14T18:11:56Z | REQ-20260714-064051-data-eng--FIX_REQUEST--iter-3 | REQ-20260714-064051-data-eng | 3 | product | FIX_REQUEST | new |
| 2026-07-15T08:00:40Z | REQ-20260714-064051-data-eng--FIX_REQUEST--iter-4 | REQ-20260714-064051-data-eng | 4 | product | FIX_REQUEST | new |
| 2026-07-15T08:27:32Z | REQ-20260715-082547-data-eng--IMPLEMENTATION_REQUEST--iter-1 | REQ-20260715-082547-data-eng | 1 | product | IMPLEMENTATION_REQUEST | new |
