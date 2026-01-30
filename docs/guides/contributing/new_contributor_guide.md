The mission of CIB Mango Tree community is to bring peer-reviewed research methods on the detection of coordinated inauthentic behavior (CIB) in social media to the fingertips of journalists, fact-checkers, watchdogs, and researchers. We do this by developing an interactive analysis and dashboard app. You can read our project overview on [cibmangotree.org](https://cibmangotree.org).

The purpose of this guide is to provide big-picture instructions on how to contribute a new test to CIB Mango Tree and a more detailed guide for each individual step. You are welcome to take part in any and all of the steps for contributig a new test that are described below. Before reading any of the specific subsections you are recommended to read the Overview section.


!!! info
    This guide is intended for contributing a new test to the library. If this is not your primary area of interest, there are other ways to contribute to the CIB Mango Project, for example in engagement and outreach activities and project management. See our Engagement Guide for more information on contributing in these ways (or ask us on Slack).

# Overview

## A library of tests

There is no single test that can provide definitive evidence that a snapshot of activity on social media is coordinated and/or inauthentic or not. Therefore -- at its core -- the goal of CIB Mango Tree is to be a library of different, but complementary tests. Each test highlights specific aspects of social media activity.

!!! example
    **Test A** might focus on finding post content that is copied verbatim a large number of times by different accounts (signaling coordination). On the other hand, **Test B** ignores the post contents and instead analyzes trending hashtags. The two tests are complementary since they analyze different aspects (post content vs. hashtag usage) of the same data.

## Contribution cycle

Completing the entire test contribution cycle, from ideation to implementation, requires sustained commitment. We recognize that not every contributor will have that level of bandwidth available. Hence the contribution process is broken down into separate stages. Each of these stages has a concrete hand-off, such that you can focus on the concrete deliverable for the specific stage without worrying about the next steps. 

!["A left-to-right box and arrow workflow diagram"](../../img/new_contributor_workflow.svg)
/// caption
Contributing a new test consists of several steps.
///

!!! example
    If you really enjoy diving into a new domain, open-ended problems, and reading papers, you can help us out by doing research and proposing a new test. If instead, you prefer tasks with more clearly defined outputs, you are welcome to review the documentation or implement a currently proposed test.

# I am interested in...

Depending on you interests and availability, you might want to jump to the section relevant to your goals.

<div class="grid cards" markdown>

-   __1. Learning more__

    Getting to know the community.

    ---
    
    [:octicons-arrow-right-24: Learning more & community resources](#not-sure-yet-i-want-to-learn-more)
    { .card }

-   __2. Research__
    
    Discovering new tests.

    --- 

    [:octicons-arrow-right-24: Researching a new test](#doing-research)
    { .card }

-   __3. Design__

    Thinking about the big picture.

    ---

    [:octicons-arrow-right-24: Designing a test](#designing-a-test)
    { .card }

-   __4. Prototype__

    Turning ideas into proof-of-concepts.

    ---

    [:octicons-arrow-right-24: Protoyping a test](#prototyping-a-test)
    { .card }

-   __5. Implement__

    From proof-of-concept to production.

    ---

    [:octicons-arrow-right-24: Implementing and integrating](#implementing-a-test-into-the-library)
    { .card }

-   __6. General software engineering__

    Helping with improving code base.

    ---

    [:octicons-arrow-right-24: Improving the code base](#helping-with-general-software-engineering)
    { .card }

</div>

## Not sure yet, I want to learn more.

That is absolutely fine, we've all been there. If you can, the best way to find your way around the project is to join an Civic Tech DC project night in Washington, DC. You can see upcoming events and [register on Luma](https://lu.ma/civic-tech-dc). If in-person attendence is not an option, you can join us virtually too. You'll need to first [join our Slack space](https://www.civictechdc.org/slack) (look for the `#cib-mango-tree-*` channels), where you can learn more.

!!! info "Community resources"

    | Platform link | Come here for |
    | --- | --- |
    | [Joining Slack](https://www.civictechdc.org/slack) | Joining the community chat and learn about our weekly virtual calls |
    | [Civic Tech DC website](https://www.civictechdc.org) | Upcoming in-person events |
    | [Civic Tech DC Luma](https://lu.ma/civic-tech-dc) | Following upcoming in-person events |
        

## Doing research

It all starts here. CIB Mango Tree wants to make pre-existing social media analysis methods, descripted in peer-reviewed research broadly available. There are no set-in-stone processes here, the Internet, literature, and the community are your friends! However, if computational social science and social media data analysis are new domains to you, we provide some of the recent review articles that we think are a good starting point and the relevant communities to keep an eye on below.

!!! info
    Some of the references that can get you started:

    - Mancocci et al. 2024. Detection and Characterization of Coordinated Online Behavior: A Survey. [https://doi.org/10.48550/arXiv.2408.01257](https://doi.org/10.48550/arXiv.2408.01257)
    - EU DisinfoLab. 2024. [CIB Detection Tree](https://www.disinfo.eu/publications/coordinated-inauthentic-behaviour-detection-tree/)

**Hand-off**: You should fill out the test outline [template document](https://docs.google.com/document/d/1eO2pbMfBZNznnCo4s3E9eINaR-2qxCLedo7EbaRmHsA/edit?tab=t.0#heading=h.35g3nbbzlngs) on our Google Drive to propose a new test for our library. This will help us have a record of what was done, the key references, and it will provide a good starting point for a new volunteer.

**Getting help**: You can ask around on the `#cib-mango-tree-product` channel. For example, you can share any papers you find interesting to get the conversation going. It is also always great to share short updates in the weekly calls or at the in-person event.

## Designing a test

If a test already has a test outline document that has been completed, the best next step is to give a very short presentation of the test and discuss it with the rest of the volunteers in one of the virtual calls (or at in-person events). The goal here is to take the outline and think about how:  

1. The analysis method in the outline could be made useful for the test library and  
1. what are the possible implementations.  

While it is often possible to take an outline and start prototyping immediately (see next step), we find it is always worthwhile having a discussion before diving into number crunching. This is a good step if you want to hone in your data science and presentation skills!

**Hand-off**: A short presentation (preferably in Google Slides) that explains the methodology, and speaks to why the test is useful – what it’s good for, and what it may have uniquely that other currently implemented tests don’t measure well. 

!!! tip
    We recommend keeping the presentation quite brief (e.g. 3-5 slides, 10-15 minutes), so that we can have a rich discussion. We recommend including the following elements: 

    1. The main rationale for including the test.
    1. What type of data is required (e.g. user id, post content, timestamp)
    1. The main output/metric of the test (e.g. a list of identified posts, a list of accounts etc.).

**Getting help:** You are welcome to ask around on Slack for more information as you are preparing this and it’s absolutely fine if not everything is clear – the purpose is to discuss the test together as a community.


## Prototyping a test

Once a test has been discussed and we have a good idea of what insights it could provide, we recommend that you start by creating a "quick and dirty" prototype of the test. In practice this means creating a local script (or a notebook etc., whatever works for you) that implements the main analysis and provides some basic outputs. This will allow you to quickly get a feel for what works and what does not without having to deal with the details of application codebase.

There are no specific requirements here, other than that the exploration should be lightweight, focus only on the main ideas and give us a more concrete idea regarding how we can move forward with integrating into the main codebase.

**Hand-off**: Ideally, the final hand-off for this part is a GitHub issue on our [main repository](https://github.com/civictechdc/cib-mango-tree) describing the prototyped test as a feature request. The goal here is to have a log of what was done (what worked well, what did not) such that in the future you or someone else can read the issue and proceed with implementing the test (see next step)

!!! tip
    When opening the issue, follow the template (you we'll be able to select it after you click the "New Issue" button). We recommend including the following information if possible. This would make it much easier to proceed:  

    - The dataset used to prototype the test (and providing any public link to the dataset if we don't have it in our Drive yet)
    - The required inputs for the prototype  
    - If possible, a publicly-accessible link to a notebook (e.g. Google Colab) or analysis scripts, 
    - Describe the dependencies used in the analysis (if applicable)
    - Concise description of the analysis, one or two main figures, and any of the outstanding issues

## Implementing a test into the library

This step involves implementing the new test using the prototyped test as a reference. The idea here is to take the code that was used to prototype (see [Prototype a test](#prototype-a-test) section) and integrate it into our main repository code base. In our parlance, that means implementing _an analyzer_.

This is possibly the most technically involved part of the entire process as it requires understanding the data science logic behind the test as well as getting to know the CIB Mango Tree code base and its requirements. We have dedicated technical guides to help you along the way.

!!! tip
    You can start by following these more specific guides:

    1. [Setting up development environment](../get-started/installation.md)
    1. [Contributing new changes](../contributing/contributing.md) (opening a pull request)
    1. [Implementing Analyzers](../contributing/analyzers.md)


**Hand-off**: The hand-off here is a pull request (PR) to our [main repository](https://github.com/civictechdc/cib-mango-tree) which introduces the code for the new analyzer.


## Helping with general software engineering

You might not be interested in any specific parts of new test development, but are instead driven by general software engineering problems. We always welcome help in any of the following areas:

- Reviewing pull requests
- Improving our existing [test suite](./testing.md)
- Testing the general performance of analyzers (speed, memory, data science code)
- Helping with the interactive side (terminal, GUI, other frontend)
- Improving the application's storage system (backend, databases)
