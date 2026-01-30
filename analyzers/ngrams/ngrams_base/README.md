## About

This is the module for base n-gram analysis (copy pasta test).
(Tables below best viewed with an editor that can render Markdown)

## Main data tables

Assuming the input dataframe:

|user_id|message_id|message_text|timestamp
|------|------|------|------|
|alice|msg_001|go go go now|2024-01-01T10:00:00Z|
|bob|msg_002|go go go it's very bad|2024-01-01T10:05:00Z|
|alice|msg_003|go go go it's very bad it's very bad|2024-01-01T10:10:00Z|


`main_.py` will write the tables with the following schemas to disk.

### `OUTPUT_MESSAGE_NGRAMS`

It provides mapping between each ngram and the messages it was detected in.

| message_surrogate_id | ngram_id |
|-------|-------|
| 1  | 0  |
| 1  | 1  |
| 1  | 2  |
| 2  | 1  |
| 2  | 4  |


### `OUTPUT_NGRAM_DEFS`

Provides mapping between `ngram_id`, the actual string and ngram-length.

| ngram_id | words | n |
|-------|-------| ------- |
| 0  | go go go  | 3 |
| 1  | go go go now  | 4 |
| 2  | go go now  | 3 |


### `OUTPUT_MESSAGE_AUTHORS`

Provides mapping between message id, message text, user id and timestamp.

| message_surrogate_id | message_id | message_text | user_id | timestamp |
|-------|-------|-------|--------|-------|
|1|msg_001|go go go now|alice|2024-01-01 10:00:00 UTC|
|2|msg_002|go go go it's very bad |bob|2024-01-01 10:05:00 UTC|
|3|msg_003|go go go it's very bad it's very bad |alice|2024-01-01 10:10:00 UTC|
