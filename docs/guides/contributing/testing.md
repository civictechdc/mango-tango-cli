## Runing the Tests

You can run all tests invoking the `pytest` command from project root:
```bash
# Run all test
pytest
```

To run a specific test file. This is useful when you're developing a specific feature and don't want to run the whole test suite:
```
pytest analyzers/hashtags/test_hashtags_analyzer.py
```

Run specific test function:
```
pytest analyzers/hashtags/test_hashtags_analyzer.py::test_gini
```

To get more information, run with verbose output:
```
pytest -v
```


## Implementing tests

The `testing` module provides testers for the primary and
secondary analyzer modules. See the [example](https://github.com/civictechdc/mango-tango-cli/blob/develop/analyzers/example/README.md) for further references.


### Test Data

- Test data is co-located with analyzers folders in `test_data/` directories
- Each analyzer should include its own test files
- Tests use sample data to verify functionality