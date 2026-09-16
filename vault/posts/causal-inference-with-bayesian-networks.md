---
title: Causal Inference with Bayesian Networks
description: A short book review.
date: '2026-09-06'
tags:
- causal-inference
- bayesian-statistics
- bayesian-networks
- research-methods
original: https://blog-about-people-analytics.netlify.app/posts/2026-09-06-causal-inference-with-bayesian-networks/
---

I recently got early access to [*Causal Inference with Bayesian Networks*](https://www.packtpub.com/en-us/product/causal-inference-with-bayesian-networks-9781835084984) by Yousri El Fattah and Reza Bagheri and was asked to review it. Here are a few thoughts in case they’re useful.

The book starts with probability and Bayesian networks, then moves into causal models and estimating intervention effects, with practical R and Python examples in economics, epidemiology, and social science, and [accompanying code available on GitHub](https://github.com/PacktPublishing/Causal-Inference-with-Bayesian-Networks).

I’d say it’s best suited to readers who are already comfortable with probability and causal graphs and want a detailed treatment of exact inference in Bayesian networks. Chapters 5–8 devote considerable space to relational representations, variable elimination, and join-tree inference.

The worked examples are probably the strongest part. The connection between graphical inference and relational tables gives the book a distinctive angle, with factor operations and intermediate results laid out in detail. The faulty-circuit diagnosis in Chapter 7 is a nice example: it retains the full posterior over 16 fault configurations, making the competing explanations available for inspection (pp. 342–352).

There are also useful sections on causal identification. Chapter 9 examines alternative valid adjustment sets and works through a front-door derivation using explicit graph modifications (pp. 415–429, 450–457). Chapter 10 distinguishes modeling, identification, and estimation, and discusses exchangeability, treatment versions, and interference. These parts deserve credit, especially because some later applications don’t consistently follow through on them.

One thing I found a little odd is that, despite the title, Bayesian networks become less prominent later in the book. The focus shifts more toward regression, matching, and survival analysis. Those methods can certainly be used alongside causal graphs, but the connection to the earlier network material was sometimes hard to follow.

For example, in Chapter 10’s smoking and birthweight application, standardization adjusts for the mother’s education, while weighting replaces it with her age (pp. 483, 486). The transition doesn’t justify the causal sufficiency of either adjustment set. Given the earlier graphical material, I’d have expected those choices to be discussed explicitly.

I also noticed a few methodological problems. Some advice on which variables to control for is, imo, incorrect and conflicts with explanations elsewhere in the book.

On page 95, the book states that any superset of a d-separating set, disjoint from the endpoints, will also d-separate them. Conditioning on a collider is an immediate counterexample; see [Pearl’s d-separation rules](https://bayes.cs.ucla.edu/BOOK-2K/d-sep.html). The book explains the collider case correctly on page 94 and warns about collider bias again on page 470. That contradiction concerns a foundational rule readers are expected to apply throughout the book.

A few applications also lose track of the target estimand. The nearest-neighbor matching example on pages 493–494 targets the average treatment effect among the treated (ATT), under the required assumptions, but reports it as the population average treatment effect (ATE). The book defines both correctly earlier in Chapter 10. The mismatch then carries into comparisons between methods: Chapter 12 compares matching with population-ATE weighting without establishing a common target (pp. 572–576). The [MatchIt documentation](https://kosukeimai.github.io/MatchIt/articles/estimating-effects.html#identifying-the-estimand) gives the relevant distinctions, including how discarding treated units changes the target further.

Some conclusions go further than the statistical checks really support. On page 574, measured covariate balance is used to justify assuming that confounding is no longer present. That goes beyond what balance diagnostics establish and sits awkwardly with the same chapter’s sensitivity analysis for unmeasured confounding. The assumptions and diagnostics are covered, but the interpretation of the results doesn’t consistently respect their limits.

For those reasons, I wouldn’t choose this as a first book for learning causal inference on your own, even with a solid statistics background. But if you already know the causal framework and are especially interested in the computational treatment of Bayesian networks, it could still be a useful supplement.

If you decide to give it a go, happy reading & learning 🤓

P.S. The page references above use the printed page numbers in the review copy I received.

<!-- RELATED:BEGIN -->
## Related notes
- [[causal-inference-in-people-analytics|Beyond prediction: Exploiting organizational events for causal inference in people analytics]]
- [[bayesian-thinking-for-people-analytics|Bayesian Thinking for People Analytics]]
- [[nobel-prize-and-causal-inference-popularity|Did the Nobel Prize put causal inference on the public radar?]]
- [[dag-and-double-ml|A plausible model of data-generating process eats ML algorithms for breakfast]]
- [[bayesian-networks-in-people-analytics|Use of Bayesian networks in people analytics?]]
<!-- RELATED:END -->

---
> 📄 Read the [original post with full outputs](https://blog-about-people-analytics.netlify.app/posts/2026-09-06-causal-inference-with-bayesian-networks/) on my blog.
