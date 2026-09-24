---
title: Police cadet evaluation dataset
description: A "new" real-world dataset useful for training in people analytics.
date: '2022-10-24'
tags:
- people-analytics
- data-science
- recruitment
- learning-and-development
original: https://blog-about-people-analytics.netlify.app/posts/2022-10-24-police-cadet-evaluation-dataset/
---

While cleaning out my (very) old computer, I came across a hidden gem: a dataset with real-world data about police cadet evaluation. It was part of a tutorial from [Peltarion](https://en.wikipedia.org/wiki/Peltarion), an AI software company providing specialized software ([Synapse](https://en.wikipedia.org/wiki/Peltarion_Synapse)) for creating, training, evaluating, and deploying artificial neural networks and other adaptive systems (recently acquired by [King](https://en.wikipedia.org/wiki/King_(company))). AFAIK, this dataset is not part of any publicly available database with training datasets, so it may add a bit to the portfolio of possibilities for those involved and interested in people analytics.  

The data were collected as part of an effort by the [National Police Services Agency](https://en.wikipedia.org/wiki/Korps_landelijke_politiediensten) and the [Dutch Ministry of Justice and Security](https://www.government.nl/ministries/ministry-of-justice-and-security) to objectively examine whether the data collected at the time of graduation of police cadets can be used to predict the requirements for passing the standard five-year evaluation. The main reason for the study was to find the key indicators for the then 20% failure rate, which was considered unacceptable (data were collected in the late 1990s), and to study the effects of lowering admission standards (accepting cadets with past criminal records and lowering the minimum grade from 5.5 to 4.0).

The dataset has the following characteristics:

* 2000 observations  
* 9 attributes:
  + **Age**: the age at which the cadet started studying to become a police officer.
  + **AvG**: average grade at the time of graduation (scale 1-10).
  + **Chdn**: number of children at the time of graduation.
  + **ExEd**: extra university-level or equivalent education (years).
  + **CR**: criminal record (0=No, 1=Yes).
  + **Sex**: sex of the cadet (0 = Male, 1 = Female).
  + **SecE**: other experience in the security sector (0 = No, 1 = Yes).
  + **AvgE**: average yearly evaluation score (The average of five years. The evaluation is performed by a committee of 10 senior police officers. Scale 1-5). This is a help attribute and not for use as input.
  + **FinalE**: final evaluation. Fail if average yearly evaluation score (Avg) < 2.0 otherwise pass. (1610 Pass / 390 Fail). This is the target attribute.

Here is a table you can use to check and download the data.

```r
# uploading libraries for data manipulation and making user-friendly data table
library(tidyverse)
library(DT)

# uploading data
data <- readr::read_csv("./policeCadetEvaluation.csv")

# adjusting the data type for some variables for tabulation and visualization purposes
data <- data %>%
  mutate(
    CR = as.factor(CR),
    Sex = as.factor(Sex),
    SecE = as.factor(SecE),
    FinalE = as.factor(FinalE)
  )

# defining the table
DT::datatable(
  data,
  class = 'cell-border stripe', 
  filter = 'top',
  extensions = 'Buttons',
  fillContainer = FALSE,
  rownames= FALSE,
  options = list(
    pageLength = 5, 
    autoWidth = TRUE,
    dom = 'Bfrtip',
    buttons = c('copy', 'csv', 'excel'), 
    scrollX = TRUE, 
    selection="multiple"
    )
  )

```

<div class="data-table-preview"><p>Showing 20 of 2,000 rows and all 9 columns. <a href="https://blog-about-people-analytics.netlify.app/posts/2022-10-24-police-cadet-evaluation-dataset/">View the full interactive table in the original post</a>.</p><div style="overflow-x:auto;max-width:100%"><table><thead><tr><th>Age</th><th>AvgG</th><th>Chdn</th><th>ExEd</th><th>CR</th><th>Sex</th><th>SecE</th><th>AvgE</th><th>FinalE</th></tr></thead><tbody><tr><td>40</td><td>9.7291</td><td>1</td><td>0</td><td>0</td><td>0</td><td>0</td><td>3.995</td><td>Pass</td></tr><tr><td>26</td><td>4.1614</td><td>0</td><td>1</td><td>0</td><td>0</td><td>0</td><td>1.354</td><td>Fail</td></tr><tr><td>33</td><td>5.9848</td><td>2</td><td>0</td><td>0</td><td>0</td><td>0</td><td>1.853</td><td>Fail</td></tr><tr><td>43</td><td>6.5889</td><td>3</td><td>1</td><td>0</td><td>0</td><td>0</td><td>2.251</td><td>Pass</td></tr><tr><td>28</td><td>7.1372</td><td>0</td><td>1</td><td>0</td><td>0</td><td>0</td><td>2.494</td><td>Pass</td></tr><tr><td>22</td><td>6.8328</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>2.305</td><td>Pass</td></tr><tr><td>21</td><td>5.7995</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>1.791</td><td>Fail</td></tr><tr><td>36</td><td>8.8951</td><td>3</td><td>3</td><td>0</td><td>1</td><td>0</td><td>2.911</td><td>Pass</td></tr><tr><td>23</td><td>7.0205</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>2.333</td><td>Pass</td></tr><tr><td>24</td><td>7.6484</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>2.783</td><td>Pass</td></tr><tr><td>23</td><td>8.9347</td><td>0</td><td>2</td><td>0</td><td>1</td><td>0</td><td>4.426</td><td>Pass</td></tr><tr><td>26</td><td>8.7573</td><td>1</td><td>0</td><td>0</td><td>0</td><td>0</td><td>3.811</td><td>Pass</td></tr><tr><td>21</td><td>5.8372</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1.807</td><td>Fail</td></tr><tr><td>25</td><td>6.1926</td><td>0</td><td>1</td><td>0</td><td>0</td><td>0</td><td>1.895</td><td>Fail</td></tr><tr><td>24</td><td>8.0965</td><td>0</td><td>0</td><td>1</td><td>0</td><td>0</td><td>2.761</td><td>Pass</td></tr><tr><td>33</td><td>5.9121</td><td>1</td><td>0</td><td>1</td><td>0</td><td>0</td><td>1.773</td><td>Fail</td></tr><tr><td>25</td><td>8.6375</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>2.961</td><td>Pass</td></tr><tr><td>22</td><td>6.9502</td><td>0</td><td>2</td><td>0</td><td>0</td><td>0</td><td>2.461</td><td>Pass</td></tr><tr><td>24</td><td>7.9337</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>3.257</td><td>Pass</td></tr><tr><td>32</td><td>7.4089</td><td>1</td><td>1</td><td>0</td><td>0</td><td>0</td><td>2.602</td><td>Pass</td></tr></tbody></table></div></div>


And here is a pairplot showing the distribution and relationships between variables in the dataset.
  
```r
# uploading library for the pairplot data visualization
library(GGally)

# defining custom function for diagonal continuous variable chart  
my_dens <- function(data, mapping) {
  ggplot(data = data, mapping = mapping) +
    geom_density(alpha = 0.6, color = NA) 
}

# pairplot
GGally::ggpairs(
  data = data,
  title = "Police cadet evaluation dataset",
  mapping=ggplot2::aes(fill = FinalE),
  lower=list(
    combo = wrap("facethist", binwidth=1, alpha = 0.6),
    continuous = wrap("points", alpha = 0.3, size = 0.7),
    discrete = wrap("facetbar", alpha = 0.6)
    ),
  upper=list(
    discrete = wrap("box", alpha = 0.6),
    combo = wrap("box", alpha = 0.6)
  ),
  diag = list(
    continuous = my_dens,
    discrete = wrap("barDiag", alpha = 0.6)
    )
  ) +
  ggplot2::scale_fill_manual(values=c("Fail" = "#e53935", "Pass" = "#00897b")) +
  labs(caption = "\nThe color indicates the pass/fail result of the final evaluation, the target attribute.") +
  ggplot2::theme(
    plot.title = element_text(color = '#2C2F46', face = "plain", size = 19, margin=margin(0,0,12,0)),
    plot.caption = element_text(color = '#2C2F46', face = "plain", size = 12, hjust = 0),
    plot.title.position = "plot",
    plot.caption.position =  "plot"
  )


```

![](./police-cadet-evaluation-dataset/unnamed-chunk-2-1.png)

If you want to download the dataset, you can do so here via the table above or via [my GitHub page](https://github.com/lstehlik2809/Police-Cadet-Evaluation-Dataset) where you can also find more information about the dataset. Happy analysis 😉

<!-- RELATED:BEGIN -->
## Related notes
- [[econml-and-employee-attriton|How to get causal interpretation for the Employee Attrition dataset?]]
- [[people-analytics-challenge-from-orgnostic|People Analytics Challenge from Orgnostic: Plan for high growth]]
- [[latent-class-analysis|Latent Class Analysis of responses from employee surveys]]
- [[searching-and-querying-aihr-blog-posts|Searching & querying AIHR blog posts on People Analytics topics]]
- [[employee-feedback-analysis-using-openai|Employee feedback analysis using tools from OpenAI]]
<!-- RELATED:END -->

---
> 📄 Read the [original post with full outputs](https://blog-about-people-analytics.netlify.app/posts/2022-10-24-police-cadet-evaluation-dataset/) on my blog.
