<think>
Okay, let's tackle this. The user wants a compressed changelog based on the commit history provided, formatted in markdown, and then a second summary for a lay audience with minimal technical jargon. 

First, I need to parse the commit history. The commits are listed with authors, dates, and messages. The first commit is from VEDA95 about multi-tenancy support. Then there's a commit by Kristijan Armeni with the hashtag dashboard and some code changes. Another commit by Joe Karow about macOS code signing. Then DeanEby's commit about the GitHub action for testing .exe. And finally, another commit by DeanEby with the Excel importer.

I need to extract the key changes from each commit. For example, the multi-tenancy support involved middleware for waitress, updating dependencies, and fixing some issues. The hashtag dashboard had initial commits, adding modules, and enhancements like rolling mean and Gini. The macOS code signing fixes included environment variables, build improvements, and entitlements. The GitHub action for testing .exe was added, and the Excel importer was a feature.

For the lay audience summary, I need to simplify the technical terms. Instead of "multi-tenancy," maybe say "support for different users or environments." Mention the hashtag analyzer, the dashboard, macOS setup, and the Excel importer as key features. Avoid jargon like "polars" or "dependencies."

I also need to mention the contributors: VEDA95, Kristijan Armeni, Joe Karow, DeanEby, and soul-codes. Make sure the second summary is concise and easy to understand, focusing on the main features and benefits without technical details.
</think>

### Compressed Changelog (Markdown)
- **Multi-Tenancy Support** (Veda95, 2025-07-02): Added middleware for multi-tenancy, resolved dependabot issues, and improved code quality.
- **Hashtag Analyzer Dashboard** (Kristijan Armeni, 2025-06-25): Implemented prototype dashboard, added `gini_smooth` output, and enhanced `TimeBinningParam` for time window control.
- **MacOS Code Signing** (Joe Karow, 2025-06-24): Added `.env` files, resolved environment variables, and improved build workflows with `pyinstaller.spec` and entitlements.
- **GitHub Action for .exe Testing** (DeanEby, 2025-04-07): Added test workflow for .exe files, improved macOS build debugging, and fixed file paths.
- **Excel Importer** (DeanEby, 2025-04-07): Implemented basic Excel importer for data loading, with support for multiple sheets and headers.

**Contributors**: VEDA95, Kristijan Armeni, Joe Karow, DeanEby, soul-codes.

---

### Lay Audience Summary (Markdown)
- **Multi-Tenancy**: The app now supports different users or environments, making it easier to use with multiple people.
- **Hashtag Analyzer**: A new dashboard helps analyze hashtags, with features like rolling averages and Gini coefficients to understand data trends.
- **MacOS Fixes**: Improved code signing and build settings for macOS, making the app work better on Apple devices.
- **Testing Tools**: Added a way to test .exe files using GitHub Actions, helping developers check their apps before releasing.
- **Excel Import**: A simple tool to import data from Excel files, assuming data is in a specific format (like headers in row 1).

**Key Features**: Dashboard, multi-tenancy, macOS support, testing tools, and Excel import.  
**Contributors**: VEDA95, Kristijan Armeni, Joe Karow, DeanEby, soul-codes.
