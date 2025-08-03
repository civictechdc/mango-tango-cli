## Content Domain

The Content domain is where the analysis and visualization happen.

An analysis is added to the application by defining a **Primary Analyzer**, which comes with an interface declaration and an implementation. The interface declaration defines the input data structure and the output tables, which the application depends on for user guidance. The implementation is made workspace-agnostic by means of the "context" object.

The goal of the Primary Analyzer is to produce a set of output tables that can be used by other analyzers, including **Secondary Analyzers** and **Web Presenters**. Primary Analyzer outputs are ideally normalized, non-duplicated, and non-redundant. As such, they are not always suitable for direct user consumption. It is the job of the Secondary Analyzers to produce user-friendly outputs and the job of Web Presenters to produce interactive visualizations.

Both Secondary Analyzers and Web Presenters are also defined using interface objects. Secondary Analyzers will depend on the output of Primary Analyzers, and Web Presenters will depend on the output of both Primary and Secondary Analyzers.

# Next Steps

Once you finish reading this section it would be a good idea to review the other domain sections. Might also be a good idea to review the sections that discuss implementing  [Shiny](https://shiny.posit.co/py/), and [React](https://react.dev) dashboards.

- [Core Domain](./core-domain.md)
- [Edge Domain](./edge-domain.md)
- [Shiny Dashboards](../dashboards/shiny.md)
- [React Dashboards](../dashboards/react.md)
