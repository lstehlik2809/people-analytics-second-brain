---
title: Nothing changed. The dashboard disagrees.
description: Sharing an app that grew as a byproduct of an internal discussion about how to report and interpret turnover rates.
date: '2026-09-28'
tags:
- employee-turnover
- hr-metrics
- statistics
- time-series
- simulation
original: https://blog-about-people-analytics.netlify.app/posts/2026-09-28-turnover-signal-and-noise/
---

The question sounded simple: is it OK to show monthly turnover rate (TR) annualized, next to the annual number, and react when it jumps? To make the answer tangible, I built a small interactive app. It simulates a company of 1,000 people with a true turnover of 10% that never changes, and then measures it annually, quarterly and monthly (the latter two annualized).

A few things it shows:

1. The shorter the window, the noisier the number. What drives precision is the number of leavers behind the number: ~100 a year, ~25 a quarter, ~8 a month. With 8 leavers, one person more or less moves the annualized monthly rate by 1.2 pp. The typical swing (1 SD) is about ±1 pp for annual, ±2 pp for quarterly and ±3.5 pp for monthly TR.
2. Things go wrong when we read monthly numbers with an annual sense of "normal". Using the annual mean ±2 SD as the normal range for TR, about 37% of quarters and 60% of months fall outside it - in a company where nothing changed. Each of them can trigger a meeting or an intervention, and because the next month usually drifts back toward normal anyway (hello, regression to the mean), the intervention then looks like it worked.
3. Small teams are the same trap in disguise. A team of ~80 people measured once a year is about as noisy as the whole 1,000-person company measured monthly.
4. So the issue is less how often we look and more which yardstick we use. A rolling 12-month TR is as stable as the annual one, but it reacts to real change with months of delay. Limits sized to the window, e.g. XmR charts (which I was asking about a [while back](https://blog-about-people-analytics.netlify.app/posts/2024-10-30-xmr-charts-in-people-analytics/)), fix the yardstick, but there's no free lunch. With XmR limits based on one year of data, relying only on points outside the limits misses ~58% of real 25-60% relative shifts starting between months 7 and 18 of a 24-month dashboard: no signal at or after the change before the dashboard ends. Adding the other two rules used here cuts those misses to ~20%, but then at least one rule also fires in ~4 in 10 dashboards where nothing changed at all. More ways to look, more chances to see something.

<figure style="text-align:center;">

  ![](./turnover-signal-and-noise/app_pic.png)

</figure>

The second part of the app is a small game: 24 months of a monthly dashboard, half the time with a hidden real change, and a scoreboard comparing your calls with the XmR rules. Telling signal from noise by eye is harder than it looks, yet the signal is there - an approximate model that knows the true baseline and how the rounds are generated gets ~94% right. It uses that knowledge to combine evidence across months rather than relying on individual dots.

<figure style="text-align:center;">

  ![](./turnover-signal-and-noise/app_pic2.png)

</figure>

You can play with it [here](https://lstehlik2809.github.io/turnover-signal-noise/).

How do you report TR in your org - monthly annualized, rolling 12 months, control charts, something else? And how do you keep people from reacting to every wiggle? 🤔

P.S. The first part builds on a neat Monte Carlo illustration credited to Lipinski (2017).

<!-- RELATED:BEGIN -->
## Related notes
- [[change-detection|How to quickly navigate dashboard users to what they need to know?]]
- [[bayesian-shrinkage|Using Bayesian shrinkage in reporting employee turnover]]
- [[contagious-turnover|Is contagious turnover overrated? Probably only if you ignore the managers.]]
- [[tenure-vs-satisfaction|Simulating the "survivorship" effect in employee satisfaction data over time]]
- [[xmr-charts-in-people-analytics|Do you use XmR charts for People Analytics use cases?]]
<!-- RELATED:END -->

---
> 📄 Read the [original post with full outputs](https://blog-about-people-analytics.netlify.app/posts/2026-09-28-turnover-signal-and-noise/) on my blog.
