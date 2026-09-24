---
title: The hidden trade-offs in corporate culture?
description: Exploration of the CultureX data on corporate culture using psychometric network analysis.
date: '2025-09-17'
tags:
- organizational-culture
- network-analysis
- employee-experience
- glassdoor
original: https://blog-about-people-analytics.netlify.app/posts/2025-09-17-corporate-culture-trade-offs/
---

Recently, I came across an [article in *The Economist*](https://www.economist.com/business/2025/07/07/does-working-from-home-kill-company-culture) analyzing ~890 firms, which suggested that employee experiences in flexible vs. full-time office setups might involve a trade-off between agility and other elements of corporate culture.

Specifically, the authors found that companies mandating five days in the office scored higher on agility, but at the cost of work-life balance, support, candor, leadership trust, and a non-toxic culture (see the plot below).


<div style="text-align:center">

![](./corporate-culture-trade-offs/economist_plot.png)

</div>

That got me wondering how these different dimensions of culture relate to each other more broadly—regardless of work arrangement—and what kinds of trade-offs might exist.

To explore this, I used the same dataset referenced in [another related *Economist* piece](https://www.economist.com/interactive/business/2025/06/16/corporate-culture) comparing cultures across companies from different industries, as measured by [*CultureX*](https://www.culturex.com/) through anonymous [Glassdoor](https://www.glassdoor.com) reviews between Jan 1, 2023 and Apr 4, 2025, and applied [psychometric network analysis](https://www.nature.com/articles/s43586-021-00055-w) (EBICglasso) to estimate regularized partial correlations between individual cultural factors in the sample.

```r
library(tidyverse)
library(bootnet)
library(igraph)
library(tidygraph)
library(ggraph)

# uploading the data
data <- read.delim("culturex_data.txt", sep = ",", header = TRUE)

# changing the data format
wide_data <- data %>%
  pivot_wider(
    names_from = topic,
    values_from = post_covid_score
  ) %>% 
  # indicating that the toxic culture score were (very probably) reversed
  rename(`Toxic culture (R)` = `Toxic culture`)

# Psychometric Network Analysis

# estimating the network
network_estimate <- estimateNetwork(
  wide_data[, 4:12],
  default = "EBICglasso",
  corMethod = "cor_auto", 
  tuning = 0.5, # the LASSO penalty / regularization parameter
  threshold = TRUE # removes edges that are not statistically significant, thereby increasing specificity
)

# converting the qgraph object to a tidygraph object
graph_obj <- as_tbl_graph(network_estimate$graph, directed = FALSE) %>%
  activate(nodes)

# getting the edge weights from the graph object
edge_weights <- E(graph_obj)$weight

# creating the network plot
# setting seed for reproducibility
set.seed(2024)
ggraph_plot <- ggraph(
  graph_obj, 
  layout = 'fr', 
  weights = abs(edge_weights) 
  ) +
  geom_edge_link(
    aes(color = weight, linewidth = abs(weight)), 
    show.legend = TRUE
  ) +
  scale_edge_color_gradient2(
    low = "#f28e2b", mid = "gray90", high = "#4e79a7", 
    midpoint = 0, name = "Regularized Partial Correlations"
  ) +
  scale_edge_width(name = "Abs. Regularized Partial Correlations") +
  geom_node_point(
    fill = "black", color = "black", stroke = 1, size = 4
  ) +
  geom_node_text(aes(label = name),, size=5, repel = TRUE) +
  theme_graph(base_family = 'sans') +
  labs(
    title = "Psychometric Network Analysis of Corporate Culture",
    subtitle = "As measured by CultureX through anonymous reviews submitted by employees to Glassdoor between Jan 1st 2023-Apr 4th 2025",
    caption = "\nThe toxic culture score is supposed to be reversed."
  )

# printing the final plot
print(ggraph_plot)


```

![](./corporate-culture-trade-offs/unnamed-chunk-1-1.png)

The resulting network chart shows a few interesting patterns:

* Leadership sits at the center, with strong positive connections to most other cultural dimensions.
* Innovation appears relatively isolated compared to the rest.
* Work-life balance shows negative associations with several factors, including innovation, strategy, and agility.
* Agility is negatively related to non-toxic culture, supportive culture, work-life balance, and transparency, but positively associated with leadership and strategy. 

Sure, the correlations are far from perfect, so you can find plenty of exceptions to these patterns in the data. But still, imo, it’s interesting food for thought and potentially useful input into considerations about shaping corporate culture in one direction or another, as prioritizing one dimension may carry opportunity costs and unintended consequences.

---

P.S. If you want to replicate the analysis, run your own, or add additional external data, you can use the table below. ⚠️ But please keep in mind that I did not obtain the data officially from *CultureX*—I scraped/downloaded them from [*The Economist's* webpage](https://www.economist.com/interactive/business/2025/06/16/corporate-culture), so I cannot guarantee that the data are 100% accurate.

```r
# user-friendly table with the data in wide format
library(DT)

datatable(
  wide_data %>% 
    select(name, description, industry, everything()) %>% 
    rename(
      'Company name' = name, 
      'Company description' = description, 
      'Industry' = industry
    ) %>% 
    mutate(Industry = as.factor(Industry)),
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

<div class="data-table-preview"><p>Showing 20 of 889 rows and all 12 columns. <a href="https://blog-about-people-analytics.netlify.app/posts/2025-09-17-corporate-culture-trade-offs/">View the full interactive table in the original post</a>.</p><div style="overflow-x:auto;max-width:100%"><table><thead><tr><th>Company name</th><th>Company description</th><th>Industry</th><th>Work-life balance</th><th>Transparency</th><th>Toxic culture (R)</th><th>Supportive culture</th><th>Strategy</th><th>Leadership</th><th>Innovation</th><th>Open to feedback</th><th>Agility</th></tr></thead><tbody><tr><td>3M</td><td>Industrial conglomerate known for innovation</td><td>Industrials</td><td>-0.066430491</td><td>-0.475452788</td><td>-0.208192446</td><td>-0.041766744</td><td>-1.979745633</td><td>-0.680374267</td><td>0.09244682</td><td>-0.621825476</td><td>-1.034820942</td></tr><tr><td>7-Eleven</td><td>Global convenience store chain</td><td>Grocery Stores</td><td>-0.259798401</td><td></td><td>0.025971506</td><td>-0.6990403</td><td></td><td>0.215904289</td><td></td><td></td><td></td></tr><tr><td>A&amp;W Restaurants</td><td>Fast-food chain known for root beer</td><td>Restaurants &amp; Fast Food</td><td>0.610936578</td><td></td><td>1.349883077</td><td>2.308311649</td><td></td><td>1.878193433</td><td></td><td></td><td></td></tr><tr><td>AB InBev</td><td>World&#x27;s largest beer producer</td><td>Consumer Products</td><td>-0.921735902</td><td>-0.144622154</td><td>-1.210834059</td><td>0.0827137</td><td>-0.401477903</td><td>-0.187719793</td><td></td><td>-1.326305311</td><td>0.200843695</td></tr><tr><td>ABB</td><td>Automation and robotics</td><td>Industrials</td><td>0.319941254</td><td>0.542802428</td><td>0.969496092</td><td>1.566900491</td><td>0.094106262</td><td>0.792155479</td><td>-0.237650218</td><td>0.67948563</td><td>-0.381309845</td></tr><tr><td>Abbott</td><td>Healthcare and diagnostics company</td><td>Life Sciences &amp; Biopharma</td><td>-0.899724724</td><td>0.043727505</td><td>-1.068616318</td><td>-1.007490178</td><td>0.621015897</td><td>-0.442805035</td><td>-0.408066206</td><td>0.049701975</td><td>0.062024776</td></tr><tr><td>AbbVie</td><td>Biopharma firm best known for Humira</td><td>Life Sciences &amp; Biopharma</td><td>-0.059915596</td><td>-0.238398178</td><td>-0.354981094</td><td>-0.359020472</td><td>1.326781662</td><td>-0.097696226</td><td>-0.071840622</td><td>0.503595204</td><td>-0.876685816</td></tr><tr><td>Abercrombie &amp; Fitch</td><td>Preppy American clothing brand</td><td>Specialty Retail &amp; Apparel</td><td>0.672486408</td><td></td><td>0.56091717</td><td>0.634155774</td><td></td><td>0.898789043</td><td></td><td></td><td></td></tr><tr><td>ABM Industries</td><td>Facility management and services</td><td>Outsourcing &amp; Staffing</td><td>-0.374363267</td><td></td><td>-0.639342211</td><td>-1.07553922</td><td></td><td>-1.081290126</td><td></td><td></td><td></td></tr><tr><td>Academy Sports + Outdoors</td><td>Sports and outdoor goods retailer</td><td>Specialty Retail &amp; Apparel</td><td>-0.114106338</td><td></td><td>-0.106508532</td><td>0.159191257</td><td></td><td>-0.043169556</td><td></td><td></td><td></td></tr><tr><td>Accenture</td><td>Consulting and technology services</td><td>Business Consulting</td><td>0.544642648</td><td>0.233807946</td><td>0.79762367</td><td>-1.159603731</td><td>0.106979884</td><td>0.136349989</td><td></td><td>0.036506226</td><td>-0.584888442</td></tr><tr><td>Ace Hardware</td><td>Co-op of independent hardware stores</td><td>Specialty Retail &amp; Apparel</td><td>1.119199321</td><td></td><td>0.273524396</td><td>0.649571271</td><td></td><td>1.71059534</td><td></td><td></td><td></td></tr><tr><td>Acosta</td><td>Marketing agency for consumer goods</td><td>Business Services</td><td>2.060383483</td><td>-1.585123197</td><td>0.686542396</td><td>-0.825348381</td><td>1.218658179</td><td>-0.197603569</td><td></td><td>-0.200992139</td><td>0.563256997</td></tr><tr><td>Actalent</td><td>Staffing firm for engineers and scientists</td><td>Outsourcing &amp; Staffing</td><td>-1.19838897</td><td></td><td>0.227725716</td><td>0.565463755</td><td></td><td>0.333694094</td><td></td><td></td><td></td></tr><tr><td>Adecco</td><td>Global staffing and HR services</td><td>Outsourcing &amp; Staffing</td><td>0.53571192</td><td></td><td>0.810606354</td><td>0.183804862</td><td></td><td>0.446663882</td><td></td><td></td><td></td></tr><tr><td>adidas</td><td>German sportswear brand</td><td>Specialty Retail &amp; Apparel</td><td>0.646918403</td><td></td><td>0.550680236</td><td>1.399862815</td><td></td><td>0.410082661</td><td></td><td></td><td></td></tr><tr><td>Adobe</td><td>Creator of Photoshop and digital tools</td><td>Software &amp; IT Services</td><td>0.497063503</td><td>0.690587774</td><td>-0.098857715</td><td>0.783656928</td><td>-0.132724477</td><td>0.20893445</td><td>1.552811491</td><td>0.180150621</td><td>-2.396603423</td></tr><tr><td>ADP</td><td>Payroll and human resources</td><td>Business Services</td><td>-0.489467804</td><td>1.697550392</td><td>0.144198888</td><td>0.438344313</td><td>0.362103692</td><td>0.582559903</td><td></td><td>0.356213507</td><td>-0.529422785</td></tr><tr><td>ADT</td><td>Home and business security</td><td>Outsourcing &amp; Staffing</td><td>-0.024646872</td><td></td><td>-0.990235433</td><td>-1.222689509</td><td></td><td>-0.913891077</td><td></td><td></td><td></td></tr><tr><td>Advance Auto Parts</td><td>American car parts retailer</td><td>Specialty Retail &amp; Apparel</td><td>0.918495408</td><td></td><td>-0.036241182</td><td>-1.296934767</td><td></td><td>-0.48334263</td><td></td><td></td><td></td></tr></tbody></table></div></div>

<!-- RELATED:BEGIN -->
## Related notes
- [[company-culture-and-financial-performance|Company culture as a forward signal of financial performance?]]
- [[culture-500|How does your company stack up in the Big Nine Cultural Values?]]
- [[hofstede-wfh|What does national culture have to do with working from home?]]
- [[tas-c-suit-teams|Insights from the Team Assessment Survey results of C-suite teams]]
- [[instrumental-and-expressive-networks|Not all workplace relationships are created equal when it comes to retaining talent]]
<!-- RELATED:END -->

---
> 📄 Read the [original post with full outputs](https://blog-about-people-analytics.netlify.app/posts/2025-09-17-corporate-culture-trade-offs/) on my blog.
