---
title: Can observational estimates get close to randomized trial results?
description: What 37 job-training RCTs say about observational estimates in the age of big data.
date: '2026-11-09'
tags:
- causal-inference
- impact-evaluation
- double-machine-learning
- experiments
- machine-learning
- learning-and-development
- labor-economics
- people-analytics
original: https://blog-about-people-analytics.netlify.app/posts/2026-11-09-randomized-trial-vs-observational-estimates/
---

For job-training evaluations, the answer since [LaLonde (1986)](https://www.researchgate.net/publication/4900843_Evaluating_the_Econometric_Evaluations_of_Training_Programs_with_Experiment_Data) has mostly been “not really”. A new [preprint by Raj Chetty and colleagues](https://arxiv.org/abs/2611.03938) revisits this with U.S. tax records covering all adults and 37 randomized trials of 24 job-training and employment programs.

The bit I liked: for each trial, they kept the treatment group and swapped the randomized control group for a machine-learning prediction of what the same people would have earned without the program (the authors call it a “digital twin”). Then they compared the two estimates of the effect on earnings in years 2–5.

For the causal inference crowd: it’s cross-fitted DML (gradient-boosted trees + propensity score) on five years of earnings and employment history, industry, demographics and neighborhood data. Interestingly, the propensity model barely mattered. The gains came from long work histories and flexible models fitted on a huge comparison pool. Restricted to LaLonde’s covariates, or fitted on RCT-sized samples, the same trees did much worse.

What they found:

* The two sets of estimates line up well (*r* = .93, with the two ~$25K programs doing some of the lifting). Year Up United’s nine-site 2013–14 trial: ~$9,600 a year vs. ~$10,100 from the model.
* Rather than assuming no unmeasured confounding, they used the trials to estimate how big the bias typically is: root mean squared bias ≈ $1,700, about 60% less than the LaLonde and Dehejia–Wahba specifications.
* Add sampling noise and the model’s RMSE is $2,257 with the same number of trainees, or $2,073 with the larger cohorts available outside trials, vs. $2,126 for the trials themselves.
* Within Year Up, effects varied by site and year and were larger where more trainees landed jobs in their target field.

![Each dot is one randomized trial. Both axes show the estimated effect of training on average annual earnings in years 2–5. The diagonal marks exact agreement, and vertical bars show 95% confidence intervals for the trial estimates. Figure 2 from Chetty et al. (2026).](./randomized-trial-vs-observational-estimates/Chetty_et_al_2026_Figure_2.png)

⚠️ A few wrinkles, though:

* That’s a margin of error of roughly ±$4,000 a year. Fine for spotting big differences between programs, IMO not for judging a $500 gain.
* For new settings, they assume bias looks like it did in the trials. Drop the welfare-to-work and subsidized-jobs trials and estimated bias falls to ~$0, so who enrolls and how seems to matter. In internal programs, managers often nominate people based on things HR records miss.
* Strong local hiring demand could raise both placement rates and gains (the authors flag this too).
* Most HR datasets are tiny next to national tax records, and scale did a lot of the work here.

For people analytics, I’d try this on an oversubscribed reskilling program: allocate places by lottery and check how well our HR records recover the result before trusting the method elsewhere.

Has anyone benchmarked their observational estimates against an internal experiment? Curious how far off they were 🧐

<!-- RELATED:BEGIN -->
## Related notes
- [[causal-inference-in-people-analytics|Beyond prediction: Exploiting organizational events for causal inference in people analytics]]
- [[dag-and-double-ml|A plausible model of data-generating process eats ML algorithms for breakfast]]
- [[encouragement-design-and-ivs|Encouragement Design using instrumental variables]]
- [[visual-diff-in-diff|Causal insights with no code?]]
- [[did-with-repeated-cross-sectional-data|What a European cigarette tax study taught me about employee listening]]
<!-- RELATED:END -->

---
> 📄 Read the [original post with full outputs](https://blog-about-people-analytics.netlify.app/posts/2026-11-09-randomized-trial-vs-observational-estimates/) on my blog.
