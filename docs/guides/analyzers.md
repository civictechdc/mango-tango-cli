### Implementing Analyzers

The Primary Analyzer, the Secondary Analyzer, and the Web Presenter are all defined as functions that take a "context" object as their only argument. These context objects are provided by the application. The context object is there to support a contract that is expected between each module and the application.

- The Primary Analyzer context provides the path to the input file and a method to apply the user's preprocessing, which must be called on the input data so that the analyzer receives the columns it expects. It also provides the output path for the analyzer to write its results, which must match the interface declaration. The files are parquet files, and the implementation can use whichever library it prefers to read and write these files.

- The Secondary Analyzer context provides the path to the output file of the Primary Analyzer and the path to the output file that the Secondary Analyzer should write to. The Secondary Analyzer should read the output of the Primary Analyzer and write its output in a way that is suitable for user consumption.

- The Web Presenter context provides the path to the output file of the Primary Analyzer and the paths to the output files of the Secondary Analyzers. which is then used by the Web Presenter define its visualizations through the [Shiny](https://shiny.posit.co/py/), and the [React](https://react.dev) dashboards.

### Contributing a New Analysis

To contribute a new analysis, you should:
- Think about what you need from the user as input and what you want to show the user as output.
- Define a new Primary Analyzer interface and implementation. To start, you might want to output the exportable tables directly. However, as soon as you want to offer a dashboard or more elaborate sets of exportable outputs, you should consider outputting a more normalized set of tables in the Primary Analyzer and then define a Secondary Analyzer to produce the user-friendly outputs.

  > 💚 Using the Primary Analyzer in this way means that other contributors can build on your work. It is a great way to get started if you want to focus on the data science but let others handle data presentation.

- When defining a Secondary Analyzer, be sure to import and provide the Primary Analyzer interface as the "base" interface.
- When defining a Web Presenter, be sure to specify the "base" Primary Analyzer **and** all Secondary Analyzers that your dashboard needs.
- Mark any output not intended for user consumption as "internal" in the interface.
- Add all the defined modules to the [suite](../analyzers/__init__.py).

If you're new to the project, check out
[this directory](../analyzers/example/README.md) for a
workable example.

# Next Steps

Once you finish reading this it would be a good idea to review the sections for each domain. Might also be a good idea to review the sections that discuss implementing  [Shiny](https://shiny.posit.co/py/), and [React](https://react.dev) dashboards.

- [Core Domain](./domains/core-domain.md)
- [Edge Domain](./domains/edge-domain.md)
- [Content Domain](./domains/content-domain.md)
- [Shiny Dashboards](./dashboards/shiny.md)
- [React Dashboards](./dashboards/react.md)
