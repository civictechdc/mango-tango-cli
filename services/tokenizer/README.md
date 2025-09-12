# Tokenizer Service

Unicode-aware text tokenization for social media analytics with multilingual support.

## Overview

The tokenizer service provides configurable text tokenization that handles:

- **Multilingual text**: Latin, CJK (Chinese/Japanese/Korean), and Arabic scripts
- **Social media entities**: Hashtags, mentions, URLs preserved as single tokens
- **Unicode normalization**: Proper handling of combined characters and emojis
- **Configurable processing**: Flexible options for different analysis needs

## Quick Start

### Simple Usage

```python
from services.tokenizer import tokenize_text

text = "Hello @user! Check out #python https://example.com 🚀"
tokens = tokenize_text(text)
# Result: ['hello', '@user', 'check', 'out', '#python', 'https://example.com', '🚀']
```

### Custom Configuration

```python
from services.tokenizer import BasicTokenizer, TokenizerConfig
from services.tokenizer.core import CaseHandling

config = TokenizerConfig(
    case_handling=CaseHandling.PRESERVE,
    extract_hashtags=True,
    include_emoji=True,
    min_token_length=2
)

tokenizer = BasicTokenizer(config)
tokens = tokenizer.tokenize("Social media text #analysis @researcher")
```

## Core Concepts

### Abstract Interface

All tokenizers implement `AbstractTokenizer`:

```python
from services.tokenizer.core.base import AbstractTokenizer

class CustomTokenizer(AbstractTokenizer):
    def tokenize(self, text: str) -> list[str]:
        # Your implementation here
        pass
```

### Configuration-Driven Processing

The `TokenizerConfig` dataclass controls all tokenization behavior:

- **Text preprocessing**: Case handling, Unicode normalization
- **Token filtering**: What types of content to include/exclude
- **Social media handling**: How to treat hashtags, mentions, URLs
- **Output control**: Length limits, whitespace handling

### Single-Pass Tokenization

The `BasicTokenizer` uses a comprehensive regex approach:

- One regex pattern matches all token types
- Tokens extracted in document order
- Social media entities matched before general words

## Configuration Reference

### TokenizerConfig Options

```python
@dataclass
class TokenizerConfig:
    # Language detection
    fallback_language_family: LanguageFamily = LanguageFamily.MIXED

    # Token type filtering
    include_punctuation: bool = False
    include_numeric: bool = True
    include_emoji: bool = False  # Default is False

    # Text preprocessing
    case_handling: CaseHandling = CaseHandling.LOWERCASE
    normalize_unicode: bool = True

    # Social media features
    extract_hashtags: bool = True
    extract_mentions: bool = True
    extract_urls: bool = True
    extract_emails: bool = True

    # Output control
    min_token_length: int = 1
    max_token_length: Optional[int] = None
    strip_whitespace: bool = True
```

### Enum Values

**CaseHandling:**

- `PRESERVE` - Keep original case
- `LOWERCASE` - Convert to lowercase
- `UPPERCASE` - Convert to uppercase
- `NORMALIZE` - Smart case normalization

**LanguageFamily:**

- `LATIN` - Space-separated languages
- `CJK` - Character-based languages
- `ARABIC` - Right-to-left scripts
- `MIXED` - Multiple script families
- `UNKNOWN` - Language detection failed

## API Reference

### Factory Functions

```python
# Simple tokenization with optional config
def tokenize_text(text: str, config: TokenizerConfig = None) -> list[str]

# Create configured tokenizer instance
def create_basic_tokenizer(config: TokenizerConfig = None) -> BasicTokenizer
```

### AbstractTokenizer Interface

```python
class AbstractTokenizer:
    def __init__(self, config: TokenizerConfig = None)
    def tokenize(self, text: str) -> list[str]  # Main tokenization method

    @property
    def config(self) -> TokenizerConfig  # Access configuration

    # Protected methods for subclassing
    def _preprocess_text(self, text: str) -> str
    def _postprocess_tokens(self, tokens: list[str]) -> list[str]
```

### BasicTokenizer Implementation

The main implementation provides:

- Unicode-aware multilingual tokenization
- Social media entity preservation
- Configurable preprocessing and postprocessing
- Support for mixed-script content

## Usage Patterns

### Preserving Original Case

```python
config = TokenizerConfig(
    case_handling=CaseHandling.PRESERVE,
    include_emoji=True,
    min_token_length=1
)
```

### Content-Only Tokenization

```python
config = TokenizerConfig(
    extract_hashtags=False,  # Split hashtags to get content words
    extract_mentions=False,  # Split mentions to get usernames
    extract_urls=False,      # Split URLs into components
    include_punctuation=False
)
```

### Strict Filtering

```python
config = TokenizerConfig(
    include_punctuation=False,
    include_numeric=False,
    include_emoji=False,
    min_token_length=3,
    max_token_length=20
)
```

## Integration Examples

### Basic Integration

```python
from services.tokenizer import create_basic_tokenizer, TokenizerConfig

# Use default configuration
tokenizer = create_basic_tokenizer()
tokens = tokenizer.tokenize(text)

# Or with custom configuration
config = TokenizerConfig(min_token_length=2)
tokenizer = create_basic_tokenizer(config)
tokens = tokenizer.tokenize(text)
```

### Configuration Factory Pattern

```python
from services.tokenizer import TokenizerConfig
from services.tokenizer.core import CaseHandling

def create_custom_config():
    return TokenizerConfig(
        case_handling=CaseHandling.PRESERVE,
        include_emoji=True,
        min_token_length=1
    )

config = create_custom_config()
```

## Extending the Service

### Creating Custom Tokenizers

```python
from services.tokenizer.core.base import AbstractTokenizer
from services.tokenizer.core.types import TokenizerConfig

class CustomTokenizer(AbstractTokenizer):
    """Custom tokenizer implementation."""

    def __init__(self, config: TokenizerConfig = None):
        super().__init__(config)
        # Custom initialization

    def tokenize(self, text: str) -> list[str]:
        """Implement custom tokenization logic."""
        if not text:
            return []

        # Apply preprocessing
        processed_text = self._preprocess_text(text)

        # Your tokenization logic here
        tokens = custom_tokenize_logic(processed_text)

        # Apply postprocessing
        return self._postprocess_tokens(tokens)
```

### Plugin Registration

Add new tokenizers to the service interface:

```python
# In services/tokenizer/__init__.py
from .custom_tokenizer import CustomTokenizer
from .core.types import TokenizerConfig

def create_custom_tokenizer(config: TokenizerConfig = None) -> CustomTokenizer:
    return CustomTokenizer(config)
```

## Implementation Notes

### Architecture Decisions

- **Single comprehensive regex**: All token types extracted in one pass
- **Configuration-driven patterns**: Regex built based on enabled features
- **Order preservation**: Tokens returned in document sequence
- **Abstract base class**: Enables multiple tokenizer implementations

### Performance Characteristics

- Single-pass processing for efficiency
- Compiled regex patterns cached per configuration
- Minimal string copying during processing
- Configuration objects are lightweight

### Unicode Handling

- NFKC normalization for consistent character representation
- Proper handling of combining characters and diacritics
- Emoji detection across Unicode ranges
- Mixed-script content support

## Module Structure

```bash
services/tokenizer/
├── __init__.py              # Public API exports
├── core/                    # Core interfaces and types
│   ├── __init__.py         # Core type exports
│   ├── base.py             # AbstractTokenizer interface
│   └── types.py            # Configuration and enums
├── basic/                   # BasicTokenizer implementation
│   ├── __init__.py         # Implementation exports
│   ├── tokenizer.py        # Main BasicTokenizer class
│   └── patterns.py         # Regex pattern construction
└── README.md               # This documentation
```

## Testing

The service includes comprehensive tests:

- `test_service.py` - Integration tests
- `core/test_types.py` - Configuration tests
- `basic/test_basic_tokenizer.py` - Implementation tests

Run tests with:

```bash
pytest services/tokenizer/ -v
```
