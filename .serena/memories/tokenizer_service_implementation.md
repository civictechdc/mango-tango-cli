# Tokenizer Service Implementation

## Overview

The tokenizer service provides Unicode-aware text tokenization for social media analytics with support for multilingual content and entity preservation. Implemented in the `services/tokenizer/` package with a clean plugin architecture.

## Architecture

### Core Components

- **AbstractTokenizer** (`services/tokenizer/core/base.py`) - Plugin base class
- **TokenizerConfig** (`services/tokenizer/core/types.py`) - Configuration dataclass
- **BasicTokenizer** (`services/tokenizer/basic/tokenizer.py`) - Unicode-aware implementation
- **Language Detection** (`services/tokenizer/basic/language_detection.py`) - Script classification
- **Patterns** (`services/tokenizer/basic/patterns.py`) - Regex patterns with fallback

### Plugin Architecture

```python
from services.tokenizer import tokenize_text, create_basic_tokenizer, TokenizerConfig

# Simple usage
tokens = tokenize_text("Hello @user #hashtag https://example.com")

# Advanced configuration
config = TokenizerConfig(
    case_handling=CaseHandling.LOWERCASE,
    extract_hashtags=True,
    extract_mentions=True,
    extract_urls=True,
    min_token_length=2
)
tokenizer = create_basic_tokenizer(config)
```

## Features

### Multilingual Support
- **Latin scripts**: English, Spanish, French with accented characters
- **CJK scripts**: Chinese (Hanzi), Japanese (Hiragana/Katakana), Korean (Hangul)
- **Arabic scripts**: Arabic, Persian, Urdu
- **Mixed scripts**: "iPhone用户" → ["iPhone", "用户"]

### Social Media Entities
- **@mentions**: Preserved as complete tokens
- **#hashtags**: Extracted with case normalization
- **URLs**: Complete URL preservation (HTTP/HTTPS)
- **Emojis**: Unicode emoji support with proper ranges

### Configuration Options
- **Case handling**: preserve, lowercase, uppercase
- **Entity extraction**: toggleable for hashtags, mentions, URLs, emojis
- **Token filtering**: min/max length, Unicode normalization
- **Language detection**: automatic script classification

## Integration

### N-gram Analyzer Integration

The tokenizer service is integrated with the n-gram analyzer (`analyzers/ngrams/ngrams_base/`):

```python
from services.tokenizer import tokenize_text, TokenizerConfig

# In ngram analyzer main.py
config = TokenizerConfig(
    case_handling=CaseHandling.LOWERCASE,
    extract_hashtags=True,
    extract_mentions=True,
    extract_urls=True,
    min_token_length=2
)

tokens = tokenize_text(text_string, config)
```

### Configurable Parameters
- **min_n**: Minimum n-gram length (1-15, default: 3)
- **max_n**: Maximum n-gram length (1-15, default: 5)
- Both parameters are now user-configurable through the analyzer interface

## Testing

### Test Coverage (57 tests total)
- **Service tests** (`services/tokenizer/test_service.py`): 19 API/integration tests
- **Implementation tests** (`services/tokenizer/basic/test_basic_tokenizer.py`): 38 algorithm tests
- **Core tests** (`services/tokenizer/core/test_types.py`): Type and config tests
- **N-gram tests** (`analyzers/ngrams/test_ngrams_base.py`): Updated for new service

### Test Scenarios
- Multilingual text processing
- Social media entity preservation
- Configuration flexibility
- Edge cases and error handling
- Performance validation
- Backward compatibility

## Performance Characteristics

- **Memory efficient**: Simplified from complex memory management
- **Script detection**: Unicode-based language family classification
- **Entity preservation**: Regex-based with fallback support
- **Configurable processing**: Opt-in features for performance tuning

## Development Patterns

### Plugin Development
To create a custom tokenizer:

1. Inherit from `AbstractTokenizer`
2. Implement required methods: `tokenize()`, `tokenize_with_types()`, `detect_language_family()`
3. Register with the service factory functions

### Extension Points
- Custom regex patterns in `patterns.py`
- Additional language families in `types.py`
- New tokenization strategies as plugins
- Configuration options in `TokenizerConfig`

## Migration Notes

### From Old Implementation
- **Removed**: Complex memory management (MemoryManager, pressure levels)
- **Simplified**: Chunking and adaptive processing removed
- **Enhanced**: Unicode handling and entity preservation improved
- **Maintained**: Progress reporting patterns and output formats

### Backward Compatibility
- All existing n-gram analyses continue working
- Default parameters preserved (min_n=3, max_n=5)
- Output formats and column structures unchanged
- Test data compatibility maintained

## Future Extensions

The plugin architecture supports:
- **BERT tokenizers**: WordPiece, SentencePiece integration
- **Custom tokenizers**: Domain-specific tokenization strategies
- **Language-specific**: Specialized tokenizers for specific scripts
- **Performance**: GPU-accelerated tokenization for large datasets

## Files and Locations

### Core Implementation
- `services/tokenizer/core/base.py` - AbstractTokenizer base class
- `services/tokenizer/core/types.py` - Configuration and enums
- `services/tokenizer/basic/tokenizer.py` - BasicTokenizer implementation
- `services/tokenizer/basic/language_detection.py` - Script detection
- `services/tokenizer/basic/patterns.py` - Regex patterns

### Integration Points
- `analyzers/ngrams/ngrams_base/main.py` - N-gram analyzer integration
- `analyzers/ngrams/ngrams_base/interface.py` - Configurable parameters

### Documentation
- `services/tokenizer/README.md` - Comprehensive service documentation
- `.ai-context/architecture-overview.md` - Updated with services layer
- `.ai-context/symbol-reference.md` - API reference

This implementation provides a solid foundation for future text processing enhancements while maintaining compatibility with the existing analyzer ecosystem.