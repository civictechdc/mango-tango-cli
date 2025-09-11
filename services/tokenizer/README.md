# Tokenizer Service

Text tokenization service for social media analytics with multilingual support and entity preservation.

## Purpose

The tokenizer service provides text tokenization that handles multiple languages and preserves social media entities. It supports:

- **Multilingual Content**: Unicode-aware tokenization for Latin, CJK, and Arabic script families
- **Social Media Entities**: Preservation of hashtags, mentions, URLs, and email addresses as single tokens
- **Unicode Normalization**: Handling of Unicode characters, emojis, and combined characters
- **Configurable Processing**: Configuration options for different analysis requirements

## Features

### Language Support

- **Latin Scripts**: English, French, German, Spanish, and other space-separated languages
- **CJK Scripts**: Chinese, Japanese, Korean with character-level tokenization
- **Arabic Scripts**: Arabic, Persian, Urdu with proper RTL handling
- **Mixed Content**: Regex patterns handle mixed-script content
- **Language Detection**: Automatic script family detection for appropriate tokenization

### Social Media Processing

- **Hashtag Preservation**: `#trending` remains as single token
- **Mention Extraction**: `@username` preserved with proper boundaries
- **URL Handling**: Complete URLs maintained as single tokens
- **Email Detection**: Email addresses extracted as entities
- **Emoji Support**: Unicode emoji characters properly tokenized

### Text Preprocessing

- **Case Handling**: Configurable case normalization (preserve, lowercase, uppercase, smart)
- **Unicode Normalization**: NFKC normalization for consistent character representation
- **Space Processing**: Handling of various Unicode space characters
- **Length Filtering**: Configurable minimum and maximum token length limits

## Basic Usage

### Simple Tokenization

```python
from services.tokenizer import tokenize_text

# Basic tokenization with default configuration
text = "Hello world! Check out #python @user https://example.com 🚀"
tokens = tokenize_text(text)
# Result: ['hello', 'world', '#python', '@user', 'https://example.com', '🚀']
```

### Using BasicTokenizer Directly

```python
from services.tokenizer import BasicTokenizer, TokenizerConfig
from services.tokenizer.core import CaseHandling

# Create tokenizer with custom configuration
config = TokenizerConfig(
    case_handling=CaseHandling.PRESERVE,
    extract_hashtags=True,
    include_emoji=True,
    min_token_length=2
)

tokenizer = BasicTokenizer(config)
tokens = tokenizer.tokenize("Social media text #analysis @researcher")
```

### Tokenization with Type Classification

```python
from services.tokenizer import create_basic_tokenizer

tokenizer = create_basic_tokenizer()
result = tokenizer.tokenize_with_types("Visit https://example.com #cool @user!")

# Result structure:
# {
#     'word': ['visit'],
#     'url': ['https://example.com'],
#     'hashtag': ['#cool'],
#     'mention': ['@user']
# }
```

## Configuration

### TokenizerConfig Options

#### Language Handling

- `fallback_language_family: LanguageFamily = LanguageFamily.MIXED` - Default language family for tokenization patterns

#### Token Filtering

- `include_punctuation: bool = False` - Include punctuation marks as tokens
- `include_numeric: bool = True` - Include numeric tokens
- `include_emoji: bool = True` - Include emoji characters

#### Text Preprocessing Options

- `case_handling: CaseHandling = CaseHandling.LOWERCASE` - Case transformation strategy
- `normalize_unicode: bool = True` - Apply Unicode NFKC normalization

#### Social Media Features

- `extract_hashtags: bool = True` - Preserve hashtags as single tokens
- `extract_mentions: bool = True` - Preserve mentions as single tokens
- `extract_urls: bool = True` - Preserve URLs as single tokens
- `extract_emails: bool = False` - Extract email addresses

#### Output Control

- `min_token_length: int = 1` - Minimum token length (characters)
- `max_token_length: int = None` - Maximum token length (None for no limit)
- `strip_whitespace: bool = True` - Remove leading/trailing whitespace from tokens

### Configuration Examples

#### Social Media Analysis

```python
from services.tokenizer import TokenizerConfig
from services.tokenizer.core import CaseHandling

social_config = TokenizerConfig(
    case_handling=CaseHandling.LOWERCASE,
    extract_hashtags=True,
    extract_mentions=True,
    extract_urls=True,
    include_emoji=True,
    min_token_length=2
)
```

#### Multilingual Content Processing

```python
multilingual_config = TokenizerConfig(
    normalize_unicode=True,
    case_handling=CaseHandling.NORMALIZE,
    include_punctuation=False,
    fallback_language_family=LanguageFamily.MIXED  # For mixed content
)
```

#### N-gram Analysis Preparation

```python
ngram_config = TokenizerConfig(
    case_handling=CaseHandling.LOWERCASE,
    include_punctuation=False,
    include_numeric=False,
    extract_hashtags=False,  # Split hashtags for n-gram analysis
    min_token_length=3
)
```

## API Reference

### Core Types

#### AbstractTokenizer

Base interface for all tokenizer implementations.

**Methods:**

- `tokenize(text: str) -> list[str]` - Basic tokenization
- `tokenize_with_types(text: str) -> dict[str, list[str]]` - Tokenization with type classification
- `preprocess_text(text: str) -> str` - Apply preprocessing (case, normalization)
- `postprocess_tokens(tokens: list[str]) -> list[str]` - Filter and clean tokens

#### BasicTokenizer

Core implementation of AbstractTokenizer with Unicode awareness and multilingual support.

Inherits all AbstractTokenizer methods and provides:

- Multilingual tokenization with automatic language detection
- Social media entity preservation
- Unicode normalization
- Configurable preprocessing and postprocessing

### Enumerations

#### LanguageFamily

- `LATIN` - Space-separated languages (English, French, etc.)
- `CJK` - Chinese, Japanese, Korean
- `ARABIC` - Arabic script languages
- `MIXED` - Mixed content requiring multiple strategies
- `UNKNOWN` - Language detection failed

#### TokenType

- `WORD` - Regular words
- `HASHTAG` - Social media hashtags
- `MENTION` - Social media mentions
- `URL` - URLs and links
- `EMAIL` - Email addresses
- `EMOJI` - Emoji characters
- `NUMERIC` - Numbers
- `PUNCTUATION` - Punctuation marks
- `WHITESPACE` - Whitespace (when preserved)

#### CaseHandling

- `PRESERVE` - Keep original case
- `LOWERCASE` - Convert to lowercase
- `UPPERCASE` - Convert to uppercase
- `NORMALIZE` - Smart case normalization

## Integration with Analyzers

### N-gram Analyzer Integration

The tokenizer service is designed to work seamlessly with the n-gram analyzer:

```python
from services.tokenizer import create_basic_tokenizer, TokenizerConfig
from services.tokenizer.core import CaseHandling

# Configure for n-gram analysis
config = TokenizerConfig(
    case_handling=CaseHandling.LOWERCASE,
    include_punctuation=False,
    extract_hashtags=False,  # Allow hashtag content to be n-grammed
    min_token_length=2
)

tokenizer = create_basic_tokenizer(config)
tokens = tokenizer.tokenize(text)
# Tokens ready for n-gram generation
```

### Hashtag Analysis Integration

For hashtag analysis, preserve hashtags as complete entities:

```python
from services.tokenizer import TokenizerConfig
from services.tokenizer.core import CaseHandling

config = TokenizerConfig(
    extract_hashtags=True,
    case_handling=CaseHandling.PRESERVE,
    include_emoji=True
)
```

## Architecture

### Regex-Based Tokenization

The tokenizer service uses a comprehensive regex approach:

- **Single Pattern**: `get_comprehensive_pattern()` creates one regex that finds all tokens in document order
- **Priority-Based Matching**: Social media entities matched before general words to preserve boundaries
- **Document Order Preservation**: `findall()` returns tokens in their original text sequence
- **Configuration-Driven**: Pattern construction adapts to enabled token types

### Plugin System

The tokenizer service uses an abstract base class pattern that supports extensibility:

```python
from services.tokenizer.core.base import AbstractTokenizer
from services.tokenizer.core.types import TokenizerConfig

class CustomTokenizer(AbstractTokenizer):
    def __init__(self, config: TokenizerConfig = None):
        super().__init__(config)
        # Custom initialization

    def tokenize(self, text: str) -> list[str]:
        # Custom tokenization logic
        pass

    def tokenize_with_types(self, text: str) -> dict[str, list[str]]:
        # Custom type-aware tokenization
        pass
```

### Module Structure

```text
services/tokenizer/
├── __init__.py              # Public API and factory functions
├── core/                    # Core interfaces and types
│   ├── __init__.py         # Core exports
│   ├── base.py             # AbstractTokenizer base class
│   ├── types.py            # Configuration and enums
│   └── test_types.py       # Type system tests
├── basic/                   # BasicTokenizer implementation
│   ├── __init__.py         # Basic tokenizer exports
│   ├── tokenizer.py        # Main BasicTokenizer class
│   ├── patterns.py         # Regex patterns for tokenization
│   └── test_basic_tokenizer.py  # Implementation tests
└── test_service.py         # Integration tests
```

## Implementation Details

### Design Characteristics

- **Single-Pass Regex**: All tokens extracted in document order with one regex pattern
- **Configuration-Driven**: Only compile patterns for enabled token types
- **Custom Pattern Support**: User-defined regex patterns for domain-specific tokenization
- **Script Family Support**: Extensible design for additional language families

### Plugin Architecture

The abstract base class pattern supports adding new tokenizer implementations:

```python
# Future plugin example
from services.tokenizer.core.base import AbstractTokenizer

class MLTokenizer(AbstractTokenizer):
    """Machine learning-based tokenizer implementation."""
    # Custom ML-based tokenization logic
```
