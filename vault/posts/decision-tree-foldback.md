---
title: What probability would change your mind about Sam?
description: A practical look at decision analysis in People Analytics, and a simple tool for comparing options, propagating uncertainty, and finding the assumptions that would actually change a people decision.
date: '2026-10-06'
tags:
- decision-analysis
- decision-making
- people-analytics
- simulation
- performance-management
original: https://blog-about-people-analytics.netlify.app/posts/2026-10-06-decision-tree-foldback/
---

Andrew Marritt recently published a very useful article, [*Should you replace Sam?*](https://andrewmarritt.substack.com/p/should-you-replace-sam), that shows how to bring People Analytics insights closer to real impact on people-related decisions.

It shows how an old tool from decision analysis - a decision tree, but not the ML one most of us know - can turn an endless argument about a person into a disagreement about a number. A manager wants to exit an underperforming Sam, the HRBP believes in coaching, and it all boils down to whether the chance coaching works is above or below roughly 43%.

While I highly appreciated the ideas in the article, I also wondered whether HR people will find enough time and patience in their day-to-day jobs to put them into practice. Drawing trees, eliciting ranges and running simulations is not exactly something you do between two meetings 😅

So I was thinking about how to make these ideas easier to use (or remove the friction, as it's popular to say these days) for people who aren't analysts by training but still want their decisions to be more data-informed.

One option I gave a try is Foldback, a simple app where you build the tree by typing into cards or by answering one question at a time (it asks for the two ends of each range before the most likely value, so you're less tempted to anchor on a single number):

* You type the options (e.g., keep, coach, exit), what could happen after each, and the chances and costs.
* Not sure about a number? Type a range, e.g. "-37k to -25k", and it gets simulated across 10,000 plausible worlds.
* You see which option leads, by how much, how often it comes out best across those worlds, and whether that makes the lead safe or far from settled.
* For key estimates, you see the value that would change your mind, flagged when it falls inside your own range. IMO, this is the number the discussion should be about.
* It tells you which estimate is most worth pinning down first, and whether a "diagnostic month" (e.g., a month of coaching with a clear check-in) is worth its cost.
* You get a plain-text note to paste into meeting minutes or an email.

```
<video controls preload="metadata" style="width: 100%; display: block; margin-bottom: 1.5rem;">
  <source src="./decision-tree-foldback/foldback_demo.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>
```

⚠️ A few things to keep in mind: The app catches mechanical slips (chances that don't add up to 100% stop the result instead of giving you a confident verdict), but it doesn't make your inputs any better - as Andrew puts it, a confident, narrow, invented range produces a confident, narrow, invented answer, only a more rigorous-looking one. It works with averages only, treats your estimates as independent, allows one decision at the start of the tree, and prices only what you put into it, so fairness or the impact on people stays outside unless you add it. And as Andrew stresses, the tree should be built with the decision-maker, not presented at them. Andrew, who saw an early version, also thinks users will need a knowledgeable facilitator, and the step-by-step guide may not be enough on its own: it makes the tree easier to build, but it won't tell you that you've missed an option or that your ranges are too narrow.

Everything runs in your browser, nothing you type is sent anywhere, and the tree is gone when you close the tab, which is probably not unimportant when the tree is about a real person.

If you want to play with it, go 👉 [here](https://lstehlik2809.github.io/foldback/).

Let me know what works, what's confusing, or what's missing. I'd especially like to hear from HRBPs and managers whether they could imagine using it in a real conversation about a real Sam 🤔

<!-- RELATED:BEGIN -->
## Related notes
- [[job-comparator|A bet on a new job]]
- [[turnover-signal-and-noise|Nothing changed. The dashboard disagrees.]]
- [[bayesian-simulation|Harnessing Bayesian analysis for business process simulation]]
- [[doppelganger-for-career-pathing|Using Doppelgänger for career pathing?]]
- [[the-triple-filter-test|The Triple-Filter Test: How to prioritize HR interventions with panel data]]
<!-- RELATED:END -->

---
> 📄 Read the [original post with full outputs](https://blog-about-people-analytics.netlify.app/posts/2026-10-06-decision-tree-foldback/) on my blog.
