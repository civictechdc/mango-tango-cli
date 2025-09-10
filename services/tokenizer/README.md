# Unicode Tokenizer Service

Unicode-aware text tokenization service designed for social media analytics with multilingual support and entity preservation.

## Purpose

The tokenizer service provides sophisticated text tokenization capabilities that go beyond simple whitespace splitting. It handles:

- **Multilingual Content**: Automatic detection and appropriate tokenization for Latin, CJK, and Arabic script families
- **Social Media Entities**: Preservation of hashtags, mentions, URLs, and email addresses as single tokens
- **Unicode Normalization**: Proper handling of Unicode characters, emojis, and combined characters
- **Configurable Processing**: Extensive configuration options for different analysis requirements

## Features

### Language Support

- **Latin Scripts**: English, French, German, Spanish, and other space-separated languages
- **CJK Scripts**: Chinese, Japanese, Korean with character-level tokenization
- **Arabic Scripts**: Arabic, Persian, Urdu with proper RTL handling
- **Mixed Content**: Automatic detection and mixed-strategy processing
- **Fallback Handling**: Graceful degradation when language detection fails

### Social Media Processing

- **Hashtag Preservation**: `#trending` remains as single token
- **Mention Extraction**: `@username` preserved with proper boundaries
- **URL Handling**: Complete URLs maintained as single tokens
- **Email Detection**: Email addresses extracted as entities
- **Emoji Support**: Unicode emoji characters properly tokenized

### Text Preprocessing

- **Case Handling**: Configurable case normalization (preserve, lowercase, uppercase, smart)
- **Unicode Normalization**: NFKC normalization for consistent character representation
- **Space Processing**: Intelligent handling of various Unicode space characters
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

#### Language Detection

- `detect_language: bool = True` - Enable automatic language family detection
- `fallback_language_family: LanguageFamily = LanguageFamily.LATIN` - Default when detection fails

#### Space Handling

- `space_type: SpaceType = SpaceType.WHITESPACE` - Type of space characters to recognize
- `custom_spaces: str = None` - Custom space characters when using SpaceType.CUSTOM

#### Token Filtering

- `include_punctuation: bool = False` - Include punctuation marks as tokens
- `include_numeric: bool = True` - Include numeric tokens
- `include_emoji: bool = True` - Include emoji characters
- `include_whitespace: bool = False` - Preserve whitespace as tokens

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
from services.tokenizer import TokenizerConfig, CaseHandling

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
    detect_language=True,
    normalize_unicode=True,
    case_handling=CaseHandling.NORMALIZE,
    include_punctuation=False
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
- `detect_language_family(text: str) -> LanguageFamily` - Language script detection
- `is_space_separated(text: str) -> bool` - Check if text uses space separation
- `preprocess_text(text: str) -> str` - Apply preprocessing
- `postprocess_tokens(tokens: list[str]) -> list[str]` - Filter and clean tokens

#### BasicTokenizer

Core implementation of AbstractTokenizer with Unicode awareness and multilingual support.

Inherits all AbstractTokenizer methods and provides full implementation with:

- Automatic language detection
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

#### SpaceType

- `WHITESPACE` - Standard ASCII whitespace
- `UNICODE_SPACES` - All Unicode space characters
- `CUSTOM` - User-defined space characters

## Integration with Analyzers

### N-gram Analyzer Integration

The tokenizer service is designed to work seamlessly with the n-gram analyzer:

```python
from services.tokenizer import create_basic_tokenizer, TokenizerConfig
from services.tokenizer.core.types import CaseHandling

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
config = TokenizerConfig(
    extract_hashtags=True,
    case_handling=CaseHandling.PRESERVE,
    include_emoji=True
)
```

## Architecture

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
    
    def detect_language_family(self, text: str) -> LanguageFamily:
        # Custom language detection
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
│   ├── language_detection.py  # Language detection utilities
│   ├── patterns.py         # Regex patterns for tokenization
│   └── test_basic_tokenizer.py  # Implementation tests
└── test_service.py         # Integration tests
```

## Performance Characteristics

### Language Detection Performance

- **Script-based detection**: Fast Unicode range analysis
- **Cached results**: Language family detection cached per text
- **Fallback strategy**: Graceful degradation to configured fallback

### Tokenization Speed

- **Latin text**: Optimized regex-based splitting
- **CJK text**: Character-level iteration with boundary detection
- **Mixed content**: Adaptive processing based on detected segments
- **Social media entities**: Single-pass extraction with compiled patterns

### Memory Usage

- **Streaming friendly**: Processes text in single pass
- **Minimal state**: Stateless tokenization (configuration only)
- **Pattern caching**: Compiled regex patterns cached per language family

## Testing

### Test Coverage

- **Unit tests**: Core types and configuration validation
- **Implementation tests**: BasicTokenizer functionality
- **Integration tests**: Service API and factory functions
- **Language tests**: Multilingual tokenization accuracy
- **Social media tests**: Entity preservation verification

### Running Tests

```bash
# Run all tokenizer tests
pytest services/tokenizer/

# Run specific test modules
pytest services/tokenizer/core/test_types.py
pytest services/tokenizer/basic/test_basic_tokenizer.py
pytest services/tokenizer/test_service.py

# Run with verbose output
pytest services/tokenizer/ -v
```

## Development Patterns

### Configuration-Driven Design

All tokenizer behavior is controlled through the `TokenizerConfig` dataclass, enabling:

- Easy testing with different configurations
- Consistent behavior across different use cases
- User customization without code changes

### Abstract Interface Pattern

The `AbstractTokenizer` base class ensures:

- Consistent API across different implementations
- Easy extension with custom tokenizers
- Clear separation of concerns between interface and implementation

### Language-Aware Processing

The tokenizer automatically detects and adapts to different language families:

- Script-based detection using Unicode ranges
- Appropriate tokenization strategies per language family
- Graceful handling of mixed-language content

## Future Extensions

The tokenizer service is designed for extensibility:

### Planned Enhancements

- **Advanced Language Detection**: Statistical language detection for improved accuracy
- **Custom Pattern Support**: User-defined regex patterns for domain-specific tokenization
- **Performance Optimization**: Compiled tokenizer for high-volume processing
- **Additional Languages**: Support for more script families (Indic, Thai, etc.)

### Plugin Architecture

The abstract base class pattern supports adding new tokenizer implementations:

```python
# Future plugin example
from services.tokenizer.core.base import AbstractTokenizer

class MLTokenizer(AbstractTokenizer):
    """Machine learning-based tokenizer implementation."""
    # Custom ML-based tokenization logic
```

## Related Components

- **N-gram Analyzer** (`analyzers/ngrams/`) - Primary consumer of tokenizer service
- **Hashtag Analyzer** (`analyzers/hashtags/`) - Uses social media entity extraction
- **Text Preprocessing** (`app/project_context.py`) - Column semantic mapping integration

## Support and Contributing

The tokenizer service follows the project's established patterns:

- **Code Style**: Black formatting and isort import organization
- **Testing**: pytest with co-located test files
- **Type Hints**: Full type annotation throughout
- **Documentation**: Comprehensive docstrings and technical documentation

For questions or contributions, see the main project development guide and contribution guidelines.
