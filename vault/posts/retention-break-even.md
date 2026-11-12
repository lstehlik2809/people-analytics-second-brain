---
title: How many fewer people would have to quit for a retention pilot to pay for itself?
description: What Chicago’s ShotSpotter study can teach us about using Bayesian analysis to make rollout decisions when the pilot data are noisy.
date: '2026-11-13'
tags:
- bayesian-statistics
- causal-inference
- impact-evaluation
- decision-analysis
- employee-turnover
- people-analytics
original: https://blog-about-people-analytics.netlify.app/posts/2026-11-12-retention-break-even/
---

Say you’ve piloted a retention programme in a handful of teams. Voluntary attrition was lower than in the comparison group, but the estimate was noisy and the result wasn’t statistically significant. The budget meeting is next week.

I liked how [Terence Chau and colleagues](https://www.nber.org/papers/w36005) tackled a version of this problem in a new NBER working paper on ShotSpotter, a gunshot detection system Chicago used.

They used a [geographic regression discontinuity design](https://www.researchgate.net/publication/228163308_Geographic_Boundaries_as_Regression_Discontinuities), comparing shooting fatality rates just inside and just outside the coverage boundary. Their best estimate was a 2.5 percentage point drop in the share of shooting victims who died (p = .286). If that estimate held across the covered districts, it would translate to about 49 fewer deaths at 2024 shooting levels. By their calculation, you’d need roughly 87 years of Chicago data to have 80% power to detect an effect that size with the same design.

The authors used a Bayesian model to turn that noisy estimate into a range of possible net benefits. The estimated chance of coming out ahead ranged from 70.1% to 99.6% across the four scenarios in Figure 3. The 99.6% scenario uses the higher dollar value for a statistical life and assumes up front that ShotSpotter can’t increase the risk of dying after a shooting.

![Two panels show estimated annual net benefits for Chicago’s ShotSpotter. At a $0.5 million value per statistical life, the chance that benefits exceed costs is 70.1% with a flat prior and 87.9% with a no-harm prior. At $13.6 million, those probabilities are 79.6% and 99.6%, respectively. White dots mark means. The dark bars show the middle 50%, and the lighter bars span the 10th to 90th percentiles. A dashed line marks break-even in each panel. Figure 3 from Chau, Cook, Lopez, Ludwig, Roemer & Soliman (2026), NBER Working Paper 36005, p. 12. © 2026 by the authors.](./retention-break-even/shotspotter-figure-3.png)

Back to the retention pilot. Say a rollout costs $100k a year and each avoided departure saves about $20k. Five fewer departures a year would cover the cost. I’d want to see how likely we are to beat that number and how much we might lose if we fall short. I’d also rerun the numbers with a lower estimate of turnover costs and a prior that allows the programme to backfire.

P.S. If you’d like to try this with people data, Andrew Marritt’s free online book [Bayesian Thinking for People Analytics](https://bayesian-thinking.andrewmarritt.ch/) explains the approach in plain English and provides the code as well. I wrote about it recently [here](https://blog-about-people-analytics.netlify.app/posts/2026-09-16-bayesian-thinking-for-people-analytics/).

<!-- RELATED:BEGIN -->
## Related notes
- [[bayesian-simulation|Harnessing Bayesian analysis for business process simulation]]
- [[randomized-trial-vs-observational-estimates|Can observational estimates get close to randomized trial results?]]
- [[causal-inference-in-people-analytics|Beyond prediction: Exploiting organizational events for causal inference in people analytics]]
- [[bayesian-shrinkage|Using Bayesian shrinkage in reporting employee turnover]]
- [[value-added-modeling|Goals saved above expected… for managers?]]
<!-- RELATED:END -->

---
> 📄 Read the [original post with full outputs](https://blog-about-people-analytics.netlify.app/posts/2026-11-12-retention-break-even/) on my blog.
