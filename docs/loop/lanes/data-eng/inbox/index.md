# Data Eng Inbox Index

Append-only delivery log for inbox/new. One row per atomically delivered
message. Readers process inbox/new, then move each file to inbox/cur.

| delivered_at | message_id | request_id | iteration | from_lane | message_type | state |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-14T06:42:36Z | REQ-20260714-064051-data-eng--IMPLEMENTATION_REQUEST--iter-1 | REQ-20260714-064051-data-eng | 1 | product | IMPLEMENTATION_REQUEST | new |
