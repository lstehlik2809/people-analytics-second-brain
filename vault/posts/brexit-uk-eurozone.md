---
title: Divorce usually impacts both sides - but does that hold true for Brexit?
description: We can often come across analyses highlighting the negative effects of Brexit on the UK’s economic performance as measured by GDP. But what about the reverse perspective? How has Brexit impacted the economies of EU member countries?
date: '2024-12-15'
tags:
- causal-inference
- fun-with-data
original: https://blog-about-people-analytics.netlify.app/posts/2024-12-15-brexit-uk-eurozone/
---

This gap in the conversation provides a great opportunity to try out a causal inference method from the [CausalPy](https://causalpy.readthedocs.io/en/latest/?s=09) package, specifically, the [synthetic control method](https://en.wikipedia.org/wiki/Synthetic_control_method) (with the caveat that its implementation is still a wip, so the outputs should be taken with a grain of salt). Generally, this technique constructs a weighted combination of control units to mimic the characteristics of a treated unit, enabling us to estimate the causal effect of an intervention without a traditional control group.

For the analysis, I looked at the combined GDP of 20 eurozone countries from 2007 to 2023 as the outcome of interest. To construct the synthetic control group for counterfactual comparison, I used GDP data from selected OECD countries (non-EU, non-eurozone, non-UK) over the same period.

<div style="text-align:center">

![](./brexit-uk-eurozone/uk_eu_chart.png)

</div>

To my surprise, the results for the eurozone countries contrast pretty starkly with those for the UK (see the charts above). There doesn’t seem to be strong evidence of a significant negative impact from Brexit on eurozone GDP. Of course, this is just one facet of Brexit’s potential effects. There may be many other consequences - beyond what GDP metrics reveal - that apply to the eurozone as well. Still, it’s interesting to observe such a stark difference using the same type of data and methodology. 

Maybe it reflects what we often see in personal relationships: divorce usually affects both sides, but the costs are only rarely distributed equally and/or in the same ways 🤔

P.S. If interested, the data from the [OECD Data Explorer](https://data-explorer.oecd.org/) and the code for replicating this analysis are provided below.


```r
# reticulate library for running Python in .Rmd file
library(reticulate)
# libraries for data manipulation and visualization
library(tidyverse)
library(DT)

# uploading the data from the OECD Data Explorer at https://data-explorer.oecd.org/
df <- readr::read_csv("oecd_data.csv")

# table view of two rows of the data
DT::datatable(
  df,
  class = 'cell-border stripe', 
  filter = 'top',
  extensions = 'Buttons',
  fillContainer = FALSE,
  rownames= FALSE,
  options = list(
    pageLength = 2, 
    autoWidth = TRUE,
    dom = 'Bfrtip',
    buttons = c('copy', 'csv', 'excel'),
    buttons = c('copy'), 
    scrollX = TRUE, 
    selection="multiple"
  )
)

```

<div class="data-table-preview"><p>Showing 20 of 3,968 rows and all 48 columns. <a href="https://blog-about-people-analytics.netlify.app/posts/2024-12-15-brexit-uk-eurozone/">View the full interactive table in the original post</a>.</p><div style="overflow-x:auto;max-width:100%"><table><thead><tr><th>STRUCTURE</th><th>STRUCTURE_ID</th><th>STRUCTURE_NAME</th><th>ACTION</th><th>FREQ</th><th>Frequency of observation</th><th>ADJUSTMENT</th><th>Adjustment</th><th>REF_AREA</th><th>Reference area</th><th>SECTOR</th><th>Institutional sector</th><th>COUNTERPART_SECTOR</th><th>Counterpart institutional sector</th><th>TRANSACTION</th><th>Transaction</th><th>INSTR_ASSET</th><th>Financial instruments and non-financial assets</th><th>ACTIVITY</th><th>Economic activity</th><th>EXPENDITURE</th><th>Expenditure</th><th>UNIT_MEASURE</th><th>Unit of measure</th><th>PRICE_BASE</th><th>Price base</th><th>TRANSFORMATION</th><th>Transformation</th><th>TABLE_IDENTIFIER</th><th>Table identifier</th><th>TIME_PERIOD</th><th>Time period</th><th>OBS_VALUE</th><th>Observation value</th><th>REF_YEAR_PRICE</th><th>Price reference year</th><th>BASE_PER</th><th>Base period</th><th>CONF_STATUS</th><th>Confidentiality status</th><th>DECIMALS</th><th>Decimals</th><th>OBS_STATUS</th><th>Observation status</th><th>UNIT_MULT</th><th>Unit multiplier</th><th>CURRENCY</th><th>Currency</th></tr></thead><tbody><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>TUR</td><td>Türkiye</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2020-Q2</td><td></td><td>2128318.1</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2013-Q2</td><td></td><td>13306591.6</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2013-Q3</td><td></td><td>13451259.5</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>NOR</td><td>Norway</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2017-Q2</td><td></td><td>338596.8</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2007-Q3</td><td></td><td>11664361.8</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2007-Q4</td><td></td><td>11825294.7</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2008-Q1</td><td></td><td>12009899.7</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2008-Q2</td><td></td><td>12086395.2</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2008-Q3</td><td></td><td>12171946.9</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2008-Q4</td><td></td><td>12064306.4</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2012-Q4</td><td></td><td>13005144.7</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>LTU</td><td>Lithuania</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2020-Q2</td><td></td><td>109874.3</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2010-Q2</td><td></td><td>12127749.2</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2010-Q3</td><td></td><td>12227268</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2010-Q4</td><td></td><td>12395836.1</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2011-Q1</td><td></td><td>12618512.2</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2011-Q2</td><td></td><td>12729609.1</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2011-Q3</td><td></td><td>12820502.9</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2011-Q4</td><td></td><td>12797395.4</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr><tr><td>DATAFLOW</td><td>OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD(1.1)</td><td>Quarterly GDP and components - expenditure approach, US Dollars</td><td>I</td><td>Q</td><td>Quarterly</td><td>Y</td><td>Calendar and seasonally adjusted</td><td>EA20</td><td>Euro area (20 countries)</td><td>S1</td><td>Total economy</td><td>S1</td><td>Total economy</td><td>B1GQ</td><td>Gross domestic product</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>_Z</td><td>Not applicable</td><td>USD_PPP</td><td>US dollars, PPP converted</td><td>V</td><td>Current prices</td><td>LA</td><td>Annual levels</td><td>T0102</td><td>Table 0102 - GDP identity from the expenditure side</td><td>2012-Q1</td><td></td><td>12817163.5</td><td></td><td></td><td></td><td></td><td></td><td>False</td><td>Free (free for publication)</td><td>1</td><td>One</td><td>A</td><td>Normal value</td><td>6</td><td>Millions</td><td>USD</td><td>US dollar</td></tr></tbody></table></div></div>

```python
# uploading libraries for data manipulation, visualization, and causal inference
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import arviz as az
import causalpy as cp
az.style.use("arviz-white")

# uploading the data from the OECD Data Explorer at https://data-explorer.oecd.org/
data = pd.read_csv('oecd_data.csv')
data.info()
data.head()

# keeping only relevant variables
data = data[[
    'Reference area',
    'TIME_PERIOD',
    'OBS_VALUE'
]]

# cleaning the quarter column
# function to calculate the last day of the quarter
def quarter_to_date(q):
    year, quarter = q.split('-')
    quarter_month_map = {
        'Q1': '03-31',
        'Q2': '06-30',
        'Q3': '09-30',
        'Q4': '12-31'
    }
    return f"{year}-{quarter_month_map[quarter]}"

data['TIME_PERIOD'] = data['TIME_PERIOD'].apply(quarter_to_date)
data['TIME_PERIOD'] = pd.to_datetime(data['TIME_PERIOD'], format='%Y-%m-%d')

# cleaning the country names
data['Reference area'] = data['Reference area'].str.replace('- ', '', regex=True).str.replace(' ', '_', regex=True).str.replace(r'[()]', '', regex=True)

# putting data on the trillion/billion (10^12) unit scale
data['OBS_VALUE'] = data['OBS_VALUE']/1000000

# getting data from long to wide format
melted_df = data.melt(id_vars=['Reference area', 'TIME_PERIOD'], var_name='Variable', value_name='Value')
pivoted_df = melted_df.pivot(index='TIME_PERIOD', columns='Reference area', values='Value')
pivoted_df.info()

# removing countries with missing values in the time series data
pivoted_df.drop(columns=['Saudi_Arabia', 'Russia'], inplace=True)

# removing row for date where we have data for only one country
pivoted_df = pivoted_df[pivoted_df.index != pd.to_datetime('2024-09-30')]

# identifying countries (that didn't left EU) GDP of which most strongly correlated with UK's GDP before actual Brexit (2020 January 31)
correlation_df = pivoted_df[pivoted_df.index <= pd.to_datetime("2020 January 31")].corr()
print(correlation_df[['United_Kingdom']].drop('United_Kingdom').sort_values(by='United_Kingdom', ascending=False))



# Analysis 1: The impact of Brexit on UK GDP

# target country of interest
target_country = 'United_Kingdom'
# control countries (top 15)
other_countries = [
    "United_States",
    "Costa_Rica",
    "Germany",
    "New_Zealand",
    "Sweden",
    "Austria",
    "Luxembourg",
    "Denmark",
    "Belgium",
    "Korea",
    "Canada",
    "Lithuania",
    "France",
    "India",
    "Estonia"
]

# formula
formula = target_country + " ~ " + "0 + " + " + ".join(other_countries)
print(formula)

# modeling data preparation
treatment_time = pd.to_datetime("2020 January 31")
modeling_data = pivoted_df.copy()
modeling_data = modeling_data[[target_country] + other_countries]
modeling_data.dropna(axis='rows', inplace=True, how='all')

# fitting the model
result = cp.SyntheticControl(
    modeling_data,
    treatment_time,
    formula=formula,
    model=cp.pymc_models.WeightedSumFitter(
        sample_kwargs={
        "random_seed": 2024, 
        "draws": 10000,
        "tune": 5000, 
        "target_accept": 0.99,
        "chains": 4 
      }
    )
)

# results summary
az.summary(result.idata, var_names=["~mu"])

# visualization of the posterior samples
az.plot_trace(result.idata, var_names="~mu", compact=False)
plt.show()

# visualization of the estimated causal effect
fig, ax = result.plot(plot_predictors=False)
for i in [0, 1, 2]:
    ax[i].set(ylabel="Trillion USD")
plt.show()




# Analysis 2: The impact of Brexit on the GDP of eurozone countries

# identifying countries (non-EU, non-eurozone, non-UK) GDP of which most strongly correlated with eurozone countries' GDP before actual Brexit (2020 January 31)
correlation_df = pivoted_df[pivoted_df.index <= pd.to_datetime("2020 January 31")].corr()
print(correlation_df[['Euro_area_20_countries']].drop('Euro_area_20_countries').sort_values(by='Euro_area_20_countries', ascending=False))

# target country of interest
target_country = 'Euro_area_20_countries'
# control countries (top 12)
other_countries = [
    "Costa_Rica",
    "New_Zealand",
    "United_States",
    "India",
    "Korea",
    "Colombia",
    "Canada",
    "Israel",
    "Iceland",
    "Switzerland",
    "Indonesia",
    "Australia"
]

# formula
formula = target_country + " ~ " + "0 + " + " + ".join(other_countries)
print(formula)

# modeling data preparation
treatment_time = pd.to_datetime("2020 January 31")
modeling_data = pivoted_df.copy()
modeling_data = modeling_data[[target_country] + other_countries]
modeling_data.dropna(axis='rows', inplace=True, how='all')

# fitting the model
result = cp.SyntheticControl(
    modeling_data,
    treatment_time,
    formula=formula,
    model=cp.pymc_models.WeightedSumFitter(
        sample_kwargs={
        "random_seed": 2024, 
        "draws": 10000,
        "tune": 5000, 
        "target_accept": 0.99,
        "chains": 4 
      }
    )
)

# results summary
az.summary(result.idata, var_names=["~mu"])

# visualization of the posterior samples
az.plot_trace(result.idata, var_names="~mu", compact=False)
plt.show()

# visualization of the estimated causal effect
fig, ax = result.plot(plot_predictors=False)
for i in [0, 1, 2]:
    ax[i].set(ylabel="Trillion USD")
plt.show()

```

<!-- RELATED:BEGIN -->
## Related notes
- [[causal-inference-in-people-analytics|Beyond prediction: Exploiting organizational events for causal inference in people analytics]]
- [[visual-diff-in-diff|Causal insights with no code?]]
- [[nobel-prize-and-causal-inference-popularity|Did the Nobel Prize put causal inference on the public radar?]]
- [[segmentedregression|Modeling impact of the COVID-19 pandemic on people’s interest in work-life balance and well-being]]
- [[doppelganger-for-career-pathing|Using Doppelgänger for career pathing?]]
<!-- RELATED:END -->

---
> 📄 Read the [original post with full outputs](https://blog-about-people-analytics.netlify.app/posts/2024-12-15-brexit-uk-eurozone/) on my blog.
