import re
from itertools import accumulate
from typing import Optional

import polars as pl


def create_word_matcher(subject: str, col: pl.Expr) -> Optional[pl.Expr]:
    subject = subject.strip().lower()
    words = re.split(r"[^\w]", subject)
    words = [word for word in words if word]
    if not words:
        return None
    return accumulate(
        (col.str.contains("(^|[^\\w])" + re.escape(word)) for word in words),
        lambda a, b: a & b,
    )
