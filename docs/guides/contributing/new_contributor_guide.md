# Welcome to the New Contributor Guide!

The mission of CIB Mango Tree community is to bring peer-reviewed research methods on the detection of coordinated inauthentic behavior (CIB) in social media at the fingertips of journalists, fact-checkers, watchdogs, and researchers. We do this by developing an interactive analysis and dashboard app. You can read the project overview on [cibmangotree.org](https://cibmangotree.org).

The purpose of this guide is to provide a big-picture overview of how to contribute a new test to CIB Mango Tree and a more detailed guide for each individual step. You are welcome to contribute to all and any of the steps described below. Before reading any of the specific subsections you are recommended to read the General review below.


!!! info
    This guide is intended for contributing a new test to the library. If this is not your primary area of interest, there are other ways to contribute to the CIB Mango Project, for example in engagment and outreach activities and project management. See our Engagement Guide for mor information on that (or ask us on Slack).

# Overview of the process

## A library of tests

There is no single test that can provide definitive evidence whether any snapshot of activity in social media is coordinated and/or inauthentic or not. Therefore, at its core, the goal of CIB Mango Tree is to be a library of different, but complementary tests: each test highlights specific aspects of social media activity.

!!! example
    **Test A** might focus on finding post content that is copied verbatim a large number of times by different accounts (signaling coordination). On the other hand, **Test B** ignores the post contents and instead analyzes trending hashtags. The two test are complementary since they analyze different aspects (post content vs. hashtag usage) of the same data.

## Contribution steps

The entire contribution cycle, from idea to implementation, requires sustained commitment. We recognize that not every contributor will have that bandwidth available. Hence the contribution process is broken down into separate stages. Each of these stages has a concrete hand-off, such that you can focus on the concrete deliverable for the specific stage without worrying about the next steps. 

!["A left-to-right box and arrow workflow diagram"](../../img/new_contributor_workflow.svg)
/// caption
Contributing a new test consists of several steps.
///

!!! example
    If you really enjoy diving into a new domain, open-ended problems, and reading papers, you can help us out by doing research and proposing a new test. If instead, you prefer tasks with more clearly defined outputs, you are welcome to review the documentation or implement a currently proposed test.

# I am interested in...

Depending on you interestes and availability, you might want to jump to the section relevant to your goals.

<div class="grid cards" markdown>

-   __1. Not sure yet?__

    Not sure yet, but I'd like to learn more.

    ---
    
    [:octicons-arrow-right-24: Learning more & resources](#learning-more-and-community-resources)
    { .card }

-   __2. Research__
    
    Brainstorming, solve open-ended problems.

    --- 

    [:octicons-arrow-right-24: Researching a new test](#researching-a-new-test)
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

    [:octicons-arrow-right-24: Implementing and integrating](#implementing-and-integrating-into-library)
    { .card }

-   __6. General software engineering__

    Helping with improving code base.

    ---

    [:octicons-arrow-right-24: Improving the code base](#help-with-improving-code-base)
    { .card }

</div>

## Learning more and community resources

That is absolutely fine, we've all been there. If you can, the best way to find your way around the project is to join an in-person event in Washington, DC. If in-person is not an option, you can join us virtually too. You'll need to first [join our Slack space](https://www.civictechdc.org/slack), where you can learn more.

!!! info "Community resources"

    | Platform link | Come here for |
    | --- | --- |
    | [Joining Slack](https://www.civictechdc.org/slack) | Joining the community chat and learn about our weekly virtual calls |
    | [Civic Tech DC website](https://www.civictechdc.org) | Upcoming in-person events |
    | [Civic Tech DC Lu.ma](https://lu.ma/civictechdc) | Following upcoming in-person events |
        

## Researching a new test

It all starts here. CIB Mango Tree wants to make analyses described peer-reviewed research broadly available. There are no set-in-stone processes here, the Internet, literature, and the community are your friends! However, if computational social science and social media data analysis are new domains to you, we provide some of the recent review articles that we think are a good starting point and the relevant communities to keep an eye on below.

!!! info
    Some of the references that can get you started:

    - Mancocci et al. 2024. Detection and Characterization of Coordinated Online Behavior: A Survey. [https://doi.org/10.48550/arXiv.2408.01257](https://doi.org/10.48550/arXiv.2408.01257)
    - EU DisinfoLab. 2024. [CIB Detection Tree](https://www.disinfo.eu/publications/coordinated-inauthentic-behaviour-detection-tree/)

**Hand-off**: You should fill out the Test Outline document on our Google Drive. This will help us have a record of what was done, the key references, and it will provide a good starting point for a new volunteer.

**Getting help**: You can ask around on the `#cib-mango-tree-product` channel. For example, you can share any papers you find interesting to get the conversation going. It is also always great to share short updates in the weekly calls or at the in-person event.

## Designing a test

If a test already has a Test Outline, the best next step is to give a very short presentation of the test and discuss it with the rest of the volunteers in one of the virtual calls (or at in- person events). The goal here is to take the outline and think about how the test in the outline could be made useful for the test library.

While it is often possible to take an outline and start prototyping immediately (see next step), we find it is always worthwhile having a discussion before diving into number crunching. This is a good step if you want to practice presentation skills!

**Hand-off**: A short presentation (preferably in Google Slides) that explains the methodology, and speaks to why the test is useful – what it’s good for, and what it may have uniquely that other currently implemented tests don’t measure well. 

!!! tip
    We recommend keeping the presentation quite brief (e.g. 3-5 slides, 10-15 minutes), so that we can have a rich discussion. We recommend including the following elements: 

    1. The main rationale for including the test.
    1. What type of data is required (e.g. user id, post content, timestamp)
    1. The main output/metric of the test (e.g. a list of identified posts, a list of accounts etc.).

**Getting help:** You are welcome to ask around on Slack for more information as you are preparing this and it’s absolutely fine if not everything is clear – the purpose is to discuss the test together as a community.


## Prototyping a test

Once a test has been discussed and we have a good idea of what insights it could provide, we recommend that you start by creating a "quick and dirty" prototype of the test. In practice this means is creating a local script (or a notebook etc., whatever works for you) that implements the main analysis and provides some basic outputs. This will allow you to quickly get a feel for what works and what does not without having to deal with the details of application codebase.

There are no specific requirments here other that the exploration should be lightweight, only focus on the main ideas and give us a more concrete anchors to decide how we can move forward with integrating into the main codebase.

**Hand-off**: Ideally, the final hand-off for this part is a GitHub issue on our main repository describing the prototyped test as a feature request. The goal here is to have a log of what was done (what worked well, what did not) such that the future you or someone else can read the issue and proceed with implementing the test (see next step)

!!! tip
    When opening the issue, follow the template. We recommend including the following information if possible. This would make it much easier to proceed:  

    - The dataset used to prototype (and providing any public links if we don't have it yet)
    - The required inputs for the prototype  
    - If possible, a publicly accessible link to a notebook (e.g. Google Colab) or analysis scripts, 
    - Describe the dependencies used in the analysis (if applicable)
    - Concise description of the analysis, one or two main figures, and any of the outstanding issues

## Implementing and integrating into library

This step involves implementing the new test using the prototyped test as a reference. The idea here is to take the code that was used to prototype (see [Prototype a test](#prototype-a-test) section) and integrate it into our main repository code base. In our parlance, that means implementing an analyzer.

This is possibly the most technically involved part of the entire process as it requires understanding the data science logic behind the test as well as getting to know the CIB Mango Tree code base and its requirements. We have dedicated guides to help you along the way.

!!! tip
    You can start by following these guides:

    1. [Setting up development environment](../get-started/installation.md)
    1. [Contributing new changes](../contributing/contributing.md) (opening a pull request)


**Hand-off**: The hand-off here is a pull request (PR) to our main repository which introduces the code for the new analyzer.


## Help with improving code base.

You might not be interested in any specific parts of new test development, but instead you are driven by general software engineering problems. We always welcome help.