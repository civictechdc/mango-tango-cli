"""
Generate synthetic test data for ngrams analyzer tests.

This script creates minimal, human-auditable test datasets that cover:
- Cross-post repetition statistics
- Multi-user coordination patterns
- Single-user behavior
- Within-message deduplication

Run this script to regenerate test data when schemas change as follows:

```
python _generate_test_data.py # writes 'ngrams_test_input.csv' in the same folder
```
"""

from pathlib import Path

import polars as pl

# Column names from the interface
TEST_COL_AUTHOR_ID = "user_id"
TEST_COL_MESSAGE_ID = "message_id"
TEST_COL_MESSAGE_TEXT = "message_text"
TEST_COL_MESSAGE_TIMESTAMP = "timestamp"

# Test data directory
TEST_DATA_DIR = Path(__file__).parent


def _generate_test_input_data():
    """Generate comprehensive test data for ngrams analyzer."""

    # Input dataset: 5 messages, 2 users
    # Designed to test:
    # - "go go go": 3-gram appearing across 2 distinct users
    # - "it's very bad:" 3-gram appearing across 2 distinct users and repeats within message once
    # - other 3-grams (e.g. "later it's very", "go it's very") only occur once and should be filtered out

    df_input = pl.DataFrame(
        {
            TEST_COL_AUTHOR_ID: [
                "alice",
                "bob",
                "alice",
            ],
            TEST_COL_MESSAGE_ID: [
                "msg_001",
                "msg_002",
                "msg_003",
            ],
            TEST_COL_MESSAGE_TEXT: [
                "go go go now",  # alice: "go go go" (appears 3x total)
                "go go go it's very bad",  # bob: "go go go"
                "go go go it's very bad it's very bad",  # alice: "go go go", "it's very bad", "it's very bad"
            ],
            TEST_COL_MESSAGE_TIMESTAMP: [
                "2024-01-01T10:00:00Z",
                "2024-01-01T10:05:00Z",
                "2024-01-01T10:10:00Z",
            ],
        }
    )

    return df_input


if __name__ == "__main__":

    df_input = _generate_test_input_data()

    # Save all files
    df_input.write_csv(TEST_DATA_DIR / "ngrams_test_input.csv")
