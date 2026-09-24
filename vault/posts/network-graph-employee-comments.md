---
title: Using network graph modeling to capture overarching thematic clusters in employee comments
description: A showcase on how to use network analysis to display the co-occurrence of topics in employee comments.
date: '2024-06-24'
tags:
- employee-survey
- topic-analysis
- network-analysis
- generative-ai
- ai
- python
- r
original: https://blog-about-people-analytics.netlify.app/posts/2024-06-24-network-graph-employee-comments/
---

I recently came across a [qualitative study](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2024.1293171/full?utm_source=F-AAE&utm_source=sfmc&utm_medium=EMLF&utm_medium=email&utm_campaign=MRK_2309690_a0P58000000G0YfEAK_Psycho_20240227_arts_A&utm_campaign=Article%20Alerts%20V4.1-Frontiers&id_mc=312035856&utm_id=2309690&Business_Goal=%25%25__AdditionalEmailAttribute1%25%25&Audience=%25%25__AdditionalEmailAttribute2%25%25&Email_Category=%25%25__AdditionalEmailAttribute3%25%25&Channel=%25%25__AdditionalEmailAttribute4%25%25&BusinessGoal_Audience_EmailCategory_Channel=%25%25__AdditionalEmailAttribute5%25%25) that used interviews with NHS Covid staff to explore the impact of working in COVID during a pandemic on their experience, ability to work effectively together and the impact of social dynamics (e.g. cohesion, social support) on teamwork and mental health.

What particularly caught my attention was usage of network graph modeling for capturing overarching thematic clusters based on the co-occurrences of themes in the thematically coded interview transcripts. 

It inspired me to try to apply this approach to the open-ended comments from the employee survey after identifying the topics present in each comment using the LLM. IMO, this can help with better interpretation of the survey results by providing a broader context of the topics identified and thus help to more wisely select appropriate follow-up actions.

Let’s check out how this works on sample comments taken from [Glassdoor](https://www.glassdoor.com). You can download the data from Kaggle [here](https://www.kaggle.com/datasets/davidgauthier/glassdoor-job-reviews/data). To preserve the anonymity of the company whose reviews I will be analyzing, I will not show all the filters used and will upload the pre-prepared data directly. This data consists of the cons reported by previous or current employees of one specific company at one specific location during the first half of 2021. Our input data looks as follows.


```python
# uploading data
import pandas as pd

df = pd.read_csv('company_cons.csv')

```

```r
library(reticulate)
library(DT)

DT::datatable(
  py$df,
  rownames = FALSE, 
  options = list(pageLength = 5)
)

```

<div class="data-table-preview"><p>Showing 20 of 562 rows and all 2 columns. <a href="https://blog-about-people-analytics.netlify.app/posts/2024-06-24-network-graph-employee-comments/">View the full interactive table in the original post</a>.</p><div style="overflow-x:auto;max-width:100%"><table><thead><tr><th>id</th><th>cons</th></tr></thead><tbody><tr><td>0</td><td>Poor Compensation and bonus null</td></tr><tr><td>1</td><td>A lot of pressure in the job</td></tr><tr><td>2</td><td>progression is too set in stone</td></tr><tr><td>3</td><td>Poor work life balance and pressures</td></tr><tr><td>4</td><td>Limit on bonus, not so great pension benefits as compared to other companies</td></tr><tr><td>5</td><td>Progression can be quite strictly regimented</td></tr><tr><td>6</td><td>The pay is relatively low</td></tr><tr><td>7</td><td>Gruelling path to progression
Long hours and high expectations</td></tr><tr><td>8</td><td>Salary relative to peers, less community</td></tr><tr><td>9</td><td>Lowest pay on the street</td></tr><tr><td>10</td><td>clients can be very rude at times</td></tr><tr><td>11</td><td>Nothing of significance to point out.</td></tr><tr><td>12</td><td>No comment here - not applicable</td></tr><tr><td>13</td><td>Some projects can be very intense with long hours</td></tr><tr><td>14</td><td>It is hard work and might feel like a lot of you are not used to it or not fully engaged</td></tr><tr><td>15</td><td>Lower salaries
Harder to make director/partner than before</td></tr><tr><td>16</td><td>Pay could be higher bonus is low</td></tr><tr><td>17</td><td>- poor salary
- long unpaid overtime
- people are fake</td></tr><tr><td>18</td><td>No boundaries, impossible expectations on client delivery and practice development</td></tr><tr><td>19</td><td>No work life balance
Pay not commensurate with workload</td></tr></tbody></table></div></div>


Now let's extract individual pain points from employee feedback using LLM, specifically [Mixtral-8x7B-Instruct-v0.1](https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1) from [Mistral AI](https://mistral.ai/). 


```python
from huggingface_hub import login
login(token="your_token", add_to_git_credential=True)
from transformers import AutoTokenizer, pipeline, AutoModelForCausalLM
import torch
import accelerate
import bitsandbytes
import re
import ast
import numpy as np

# specifying the llm model
model_id = 'mistralai/Mixtral-8x7B-Instruct-v0.1'
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
  model_id, 
  device_map="auto", 
  load_in_4bit=True, 
  torch_dtype=torch.float32
)

generator = pipeline(
    task='text-generation',
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=2048,
    repetition_penalty=1.1,
    device_map="auto",
    torch_dtype=torch.float32,
    do_sample=True,
    temperature=0.001
)

```

We will loop over individual comments and extract pain points using the following prompt.

```python
# looping over individual comments
responses = []
for row in range(0, df.shape[0]):
    comment = df.loc[row, 'cons']
    prompt = f'''[INST]
    You are a first-class expert in analyzing feedback provided by employees.
    Your task is to identify main pain points (negative feedback) in the comment.
    Be short and precise: use short phrases or sentences only to record main pain points, i.e. what employee does not like or complaint about.
    Use only those phrases or sentences that closely relate to the employee's feedback in the comment. Do not include points that indirectly or remotely relate to the employee's feedback.
    Always return a json file with the following key-value pair: pain points - a string of short sentences or phrases separated by commas describing what employee does not like or complaint about. Don't use brackets or parentheses in the value part.
    If there is no pain point mentioned in the comment or if you do not know which value to assign, always return an empty string with the key, i.e. {{"pain points": ""}}.
    As an example, the following comment "Poor decision-making. People who make decisions don't know much about the topic, and usually they don't consult experts. However, the workload is appropriate. I would like to see a more professional approach." will return the following json file: {{"pain points": "poor decision-making, missing expertise in decision-making"}}; the following comment "My direct manager was completely incompetent." will return the following json file: {{"pain points": "incompetent direct manager"}}.
    Return a json file as instructed. Always include the name of the key and its corresponding value, even if it is an empty string! Don't use brackets or parentheses in the value part.
    Avoid duplications or similar phrases or sentences. Don't provide any alternative solutions. Don't make any comments or notes on the output, just provide me the json file in the format I asked for, i.e. {{"pain points": "a string of short sentences or phrases separated by commas describing what employee does not like or complaint about"}}!!!
    Here is a comment to analyze: {comment}
    [/INST]'''
    response = generator(prompt)
    extracted_content = response[0]["generated_text"].split("[/INST]")[-1].strip()
    extracted_dict = re.search(r"\{.*\}", extracted_content, re.DOTALL).group()
    cleaned_dict = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', extracted_dict)
    proper_dict = ast.literal_eval(cleaned_dict)
    current_key = list(proper_dict.keys())[0]
    proper_dict['pain points'] = proper_dict.pop(current_key)
    responses.append(proper_dict)

# enriching the original dataset with identified pain points
pain_points_df = pd.DataFrame(responses)
pain_points_df['pain points'].replace('', np.nan, inplace=True)
pain_points_df = pd.concat([pain_points_df, df], axis=1)

```


Before the next step, we need to explode the enriched dataset on a pain point basis to get them on separate lines while preserving information about the original comments from which they were extracted.

```python
# exploading the df by pain points
pain_points_df['pain points'] = pain_points_df['pain points'].str.split(', ')
pain_points_df_exploaded = pain_points_df.explode('pain points')

```

We get the following resulting table.

```r
pain_points_df_exploaded = read.csv('pain_points_exploaded.csv')

DT::datatable(
  pain_points_df_exploaded,
  rownames = FALSE, 
  options = list(pageLength = 5)
)

```

<div class="data-table-preview"><p>Showing 20 of 1,046 rows and all 3 columns. <a href="https://blog-about-people-analytics.netlify.app/posts/2024-06-24-network-graph-employee-comments/">View the full interactive table in the original post</a>.</p><div style="overflow-x:auto;max-width:100%"><table><thead><tr><th>id</th><th>cons</th><th>pain.points</th></tr></thead><tbody><tr><td>0</td><td>Poor Compensation and bonus null</td><td>poor compensation</td></tr><tr><td>0</td><td>Poor Compensation and bonus null</td><td>lack of bonuses</td></tr><tr><td>1</td><td>A lot of pressure in the job</td><td>pressure in the job</td></tr><tr><td>2</td><td>progression is too set in stone</td><td>progression is too rigid</td></tr><tr><td>2</td><td>progression is too set in stone</td><td>lack of flexibility in progression</td></tr><tr><td>3</td><td>Poor work life balance and pressures</td><td>poor work life balance</td></tr><tr><td>3</td><td>Poor work life balance and pressures</td><td>pressures</td></tr><tr><td>4</td><td>Limit on bonus, not so great pension benefits as compared to other companies</td><td>limit on bonus</td></tr><tr><td>4</td><td>Limit on bonus, not so great pension benefits as compared to other companies</td><td>poor pension benefits</td></tr><tr><td>5</td><td>Progression can be quite strictly regimented</td><td>strictly regimented progression</td></tr><tr><td>6</td><td>The pay is relatively low</td><td>low pay</td></tr><tr><td>7</td><td>Gruelling path to progression
Long hours and high expectations</td><td>grueling path to progression</td></tr><tr><td>7</td><td>Gruelling path to progression
Long hours and high expectations</td><td>long hours</td></tr><tr><td>7</td><td>Gruelling path to progression
Long hours and high expectations</td><td>high expectations</td></tr><tr><td>8</td><td>Salary relative to peers, less community</td><td>low salary compared to peers</td></tr><tr><td>8</td><td>Salary relative to peers, less community</td><td>lack of community</td></tr><tr><td>9</td><td>Lowest pay on the street</td><td>lowest pay</td></tr><tr><td>10</td><td>clients can be very rude at times</td><td>rude clients</td></tr><tr><td>11</td><td>Nothing of significance to point out.</td><td></td></tr><tr><td>12</td><td>No comment here - not applicable</td><td></td></tr></tbody></table></div></div>

Now we can proceed further and use the pre-prepared list of topic labels to classify all the extracted pain points.

```python
# list of employee experience topic labels
employee_experience_topics = pd.read_csv("employee_experience_topics.csv")
employee_experience_topics['topic_description'] = employee_experience_topics['topic'] + ": " + employee_experience_topics['description']

```

```r
library(tidyverse)

DT::datatable(
  py$employee_experience_topics %>% dplyr::select(topic, description),
  rownames = FALSE, 
  options = list(pageLength = 5)
)

```

<div class="data-table-preview"><p>Showing 20 of 56 rows and all 2 columns. <a href="https://blog-about-people-analytics.netlify.app/posts/2024-06-24-network-graph-employee-comments/">View the full interactive table in the original post</a>.</p><div style="overflow-x:auto;max-width:100%"><table><thead><tr><th>topic</th><th>description</th></tr></thead><tbody><tr><td>Company Brand, Prestige &amp; Reputation</td><td>The perception and image of the company in the marketplace, including its credibility, reliability, and status.</td></tr><tr><td>Company Strategy</td><td>The company&#x27;s long-term plan and vision for achieving its goals and maintaining competitive advantage.</td></tr><tr><td>Company Innovativeness</td><td>The ability of the company to develop new ideas, products, and processes to stay ahead of the competition.</td></tr><tr><td>Staffing &amp; Recruitment</td><td>The process of attracting, selecting, and appointing suitable candidates for jobs within the company.</td></tr><tr><td>Capacity Planning</td><td>The process of determining the production capacity needed by an organization to meet changing demands for its products or services.</td></tr><tr><td>Employee Turnover</td><td>The rate at which employees leave the company and are replaced by new hires.</td></tr><tr><td>Employee Onboarding</td><td>The process of integrating new employees into the company, including orientation and training.</td></tr><tr><td>Promotion &amp; Succession</td><td>The processes for advancing employees to higher positions and preparing for future leadership transitions.</td></tr><tr><td>Lateral Moves, Transfers &amp; Relocations</td><td>The movement of employees within or across roles, departments, or locations to enhance skills, meet organizational needs, and support career growth.</td></tr><tr><td>Working Tools &amp; Equipment</td><td>The physical and digital tools and resources provided to employees to perform their work effectively.</td></tr><tr><td>Relationship With Peers &amp; Colleagues</td><td>The quality of interactions and collaborations between employees at the same organizational level.</td></tr><tr><td>Relationship With Direct Manager</td><td>The quality of the working relationship and communication between an employee and their immediate supervisor.</td></tr><tr><td>Leadership &amp; Higher Management</td><td>The effectiveness and approachability of the company&#x27;s senior leaders and their ability to inspire and guide the organization.</td></tr><tr><td>Support From Manager</td><td>The assistance and encouragement provided by a manager to their team members.</td></tr><tr><td>Management Practices</td><td>The manner in which managers lead their teams, including their decision-making and interpersonal approach.</td></tr><tr><td>HR Support</td><td>The effectiveness of the Human Resources department in addressing employee needs and issues.</td></tr><tr><td>IT Support</td><td>The responsiveness and competence of the IT department in resolving technical issues and providing technological assistance.</td></tr><tr><td>Support &amp; Resources</td><td>The overall availability and quality of assistance and resources provided to employees to help them succeed.</td></tr><tr><td>Compensation &amp; Benefits</td><td>The salary, bonuses, and benefits packages provided to employees in exchange for their work.</td></tr><tr><td>Recognition</td><td>The acknowledgment and appreciation of employees&#x27; contributions, achievements and value they bring to the company.</td></tr></tbody></table></div></div>


For topic labeling, we will use the LLM again with the following prompt.

```python
# making from topic labels one string that will be used in the prompt
response_topic_bank = employee_experience_topics['topic_description'].to_list()
pain_points_topic_list_str = "\n".join(response_topic_bank)

responses_topics = []

# looping over individual pain points
for index, row in pain_points_df_exploaded.iterrows():
    text = row['pain points']
    if not text or pd.isna(text):
        responses_topics.append(np.nan)
    else:
        prompt = f'''[INST]
        You are a first-class expert in analyzing feedback provided by employees.
        Your task is to select from the provided list and assign one specific topic label that best captures the general meaning of short snippet of text extracted from employee's feedback during exit interview while leaving the company.
        Don't make up your own topic labels and use only the topic labels from the following list: {pain_points_topic_list_str}
        If you consider more options from the provided list of labels, always choose only one of them!!! Don't provide me more alternatives, I want just one solution!
        If you are not sure about the meaning of the text or you don't know what label from the provided list to assign to the text, use the label 'Other', nothing more.
        Assign always only one label to the text. Don't provide any additional comment, note, or explanation of your reasoning before or after the suggested label. Don't provide me more alternatives, I want just one solution!
        Don't mix two different labels into one label.
        You are provided with the topic labels together with their description, but put into your output only the name of the topic, not its description!
        Return a json file in the format {{"topic": "suggested topic label"}}.
        As an example, the following text 'lack of sufficient staff in functional positions' will return the following json file: {{"topic": "Staffing & Recruitment"}}; text 'not selected for positions' will return the following json file: {{"topic": "Career Development & Growth Opportunities"}}; text 'lack of feedback' will return the following json file: {{"topic": "Performance Management"}}; text 'recognition based solely on sales results' will return the following json file: {{"topic": "Recognition"}}; text 'perceived threat from employee' will return the following json file: {{"topic": "Psychological Safety"}}; if you are not sure about the meaning of the text or you don't know what label from the provided list to assign to the text, you will return the following json file: {{"topic": "Other"}}.
        Return a json file in the required format. Assign always only one label that matches the meaning of the text best!!! Provide me only with the topic label name, not its description!!!
        Don't make any comment, note, description of your reasoning, or explanation of your reasoning. Don't provide me more alternatives. If there are more options, choose only one of them - the one you think is the best option!!! Avoid using any brackets or parentheses in your output! Return just one json file.
        Remember, before giving me required output, check if you are giving one proper json file I can immediately process in Python! If not, wait and redo your work so I get what I asked for!!!
        Now give me the best label available in the provided list of labels for the following text: {text}
        [/INST]'''
        response = generator(prompt)
        extracted_content = response[0]["generated_text"].split("[/INST]")[-1].strip()
        extracted_dict = re.search(r"\{.*?\}", extracted_content, re.DOTALL).group()
        proper_dict = ast.literal_eval(extracted_dict)
        responses_topics.append(proper_dict)

# enriching dataset with pain points with selected topic labels
responses_topics_df = pd.DataFrame([x if isinstance(x, dict) else {'topic': np.nan} for x in responses_topics])
pain_points_df_exploaded['topic_label'] = responses_topics_df['topic'].values

```

Now we have for each pain point also a corresponding topic label. 

```r
pain_points_topics_exploaded = read.csv('pain_points_topics_exploaded.csv')

DT::datatable(
  pain_points_topics_exploaded,
  rownames = FALSE, 
  options = list(pageLength = 5)
)

```

<div class="data-table-preview"><p>Showing 20 of 1,046 rows and all 4 columns. <a href="https://blog-about-people-analytics.netlify.app/posts/2024-06-24-network-graph-employee-comments/">View the full interactive table in the original post</a>.</p><div style="overflow-x:auto;max-width:100%"><table><thead><tr><th>id</th><th>cons</th><th>pain.points</th><th>topic_label</th></tr></thead><tbody><tr><td>0</td><td>Poor Compensation and bonus null</td><td>poor compensation</td><td>Compensation &amp; Benefits</td></tr><tr><td>0</td><td>Poor Compensation and bonus null</td><td>lack of bonuses</td><td>Compensation &amp; Benefits</td></tr><tr><td>1</td><td>A lot of pressure in the job</td><td>pressure in the job</td><td>Workload, Stress &amp; Exhaustion</td></tr><tr><td>2</td><td>progression is too set in stone</td><td>progression is too rigid</td><td>Promotion &amp; Succession</td></tr><tr><td>2</td><td>progression is too set in stone</td><td>lack of flexibility in progression</td><td>Career Development &amp; Growth Opportunities</td></tr><tr><td>3</td><td>Poor work life balance and pressures</td><td>poor work life balance</td><td>Work Life Balance</td></tr><tr><td>3</td><td>Poor work life balance and pressures</td><td>pressures</td><td>Workload, Stress &amp; Exhaustion</td></tr><tr><td>4</td><td>Limit on bonus, not so great pension benefits as compared to other companies</td><td>limit on bonus</td><td>Compensation &amp; Benefits</td></tr><tr><td>4</td><td>Limit on bonus, not so great pension benefits as compared to other companies</td><td>poor pension benefits</td><td>Compensation &amp; Benefits</td></tr><tr><td>5</td><td>Progression can be quite strictly regimented</td><td>strictly regimented progression</td><td>Career Development &amp; Growth Opportunities</td></tr><tr><td>6</td><td>The pay is relatively low</td><td>low pay</td><td>Compensation &amp; Benefits</td></tr><tr><td>7</td><td>Gruelling path to progression
Long hours and high expectations</td><td>grueling path to progression</td><td>Career Development &amp; Growth Opportunities</td></tr><tr><td>7</td><td>Gruelling path to progression
Long hours and high expectations</td><td>long hours</td><td>Workload, Stress &amp; Exhaustion</td></tr><tr><td>7</td><td>Gruelling path to progression
Long hours and high expectations</td><td>high expectations</td><td>Performance Management</td></tr><tr><td>8</td><td>Salary relative to peers, less community</td><td>low salary compared to peers</td><td>Compensation &amp; Benefits</td></tr><tr><td>8</td><td>Salary relative to peers, less community</td><td>lack of community</td><td>Team Climate</td></tr><tr><td>9</td><td>Lowest pay on the street</td><td>lowest pay</td><td>Compensation &amp; Benefits</td></tr><tr><td>10</td><td>clients can be very rude at times</td><td>rude clients</td><td>Relationship With Peers &amp; Colleagues</td></tr><tr><td>11</td><td>Nothing of significance to point out.</td><td></td><td></td></tr><tr><td>12</td><td>No comment here - not applicable</td><td></td><td></td></tr></tbody></table></div></div>

In the final step, we need to obtain descriptive statistics for the co-occurrence of all pairs of topics across all employee comments and in a format suitable for network analysis.

```python
from itertools import combinations
from collections import Counter

# counter for storing co-occurrence counts
co_occurrence_counter = Counter()

# finding topic combinations within each employee comment
for _, group in pain_points_df_exploaded.groupby('id'):
    topics = group['topic_label'].tolist()
    for combo in combinations(sorted(topics), 2):
        co_occurrence_counter[combo] += 1

# converting the counter to a df
co_occurrence_df = pd.DataFrame(
    list(co_occurrence_counter.items()),
    columns=['topic_pair', 'weight']
)

# splitting the tuple into separate columns
co_occurrence_df[['from', 'to']] = pd.DataFrame(co_occurrence_df['topic_pair'].tolist(), index=co_occurrence_df.index)

# dropping the original topic_pair column
co_occurrence_df = co_occurrence_df.drop(columns='topic_pair')

# removing edges between the same topic labels
co_occurrence_df = co_occurrence_df[co_occurrence_df['from']!=co_occurrence_df['to']]
co_occurrence_df.reset_index(drop=True, inplace=True)

# changing order of cols
co_occurrence_df = co_occurrence_df[['from', 'to', 'weight']]
co_occurrence_df.sort_values(by='weight', ascending=False)

```

And this is how the final table looks like. 

```r
pain_points_cooccurrence = read.csv('pain_points_cooccurrence.csv')

DT::datatable(
  pain_points_cooccurrence,
  rownames = FALSE, 
  options = list(pageLength = 5)
)

```

<div class="data-table-preview"><p>Showing 20 of 277 rows and all 3 columns. <a href="https://blog-about-people-analytics.netlify.app/posts/2024-06-24-network-graph-employee-comments/">View the full interactive table in the original post</a>.</p><div style="overflow-x:auto;max-width:100%"><table><thead><tr><th>from</th><th>to</th><th>weight</th></tr></thead><tbody><tr><td>Career Development &amp; Growth Opportunities</td><td>Promotion &amp; Succession</td><td>2</td></tr><tr><td>Work Life Balance</td><td>Workload, Stress &amp; Exhaustion</td><td>28</td></tr><tr><td>Career Development &amp; Growth Opportunities</td><td>Performance Management</td><td>1</td></tr><tr><td>Career Development &amp; Growth Opportunities</td><td>Workload, Stress &amp; Exhaustion</td><td>5</td></tr><tr><td>Performance Management</td><td>Workload, Stress &amp; Exhaustion</td><td>9</td></tr><tr><td>Compensation &amp; Benefits</td><td>Team Climate</td><td>1</td></tr><tr><td>Company Climate</td><td>Workload, Stress &amp; Exhaustion</td><td>4</td></tr><tr><td>Career Development &amp; Growth Opportunities</td><td>Compensation &amp; Benefits</td><td>17</td></tr><tr><td>Compensation &amp; Benefits</td><td>Workload, Stress &amp; Exhaustion</td><td>63</td></tr><tr><td>Compensation &amp; Benefits</td><td>Workplace Harassment</td><td>2</td></tr><tr><td>Workload, Stress &amp; Exhaustion</td><td>Workplace Harassment</td><td>3</td></tr><tr><td>Performance Management</td><td>Unclear Expectations</td><td>2</td></tr><tr><td>Compensation &amp; Benefits</td><td>Work Life Balance</td><td>16</td></tr><tr><td>Workload, Stress &amp; Exhaustion</td><td>Workplace Safety</td><td>1</td></tr><tr><td>Organizational Processes Efficiency</td><td>Workload, Stress &amp; Exhaustion</td><td>12</td></tr><tr><td>Communication</td><td>Workload, Stress &amp; Exhaustion</td><td>1</td></tr><tr><td>Career Development &amp; Growth Opportunities</td><td>Company Structure &amp; Organization</td><td>1</td></tr><tr><td>Compensation &amp; Benefits</td><td>Workplace Culture</td><td>8</td></tr><tr><td>Workload, Stress &amp; Exhaustion</td><td>Workplace Culture</td><td>4</td></tr><tr><td>Employee Training &amp; Development</td><td>Quality of Work</td><td>1</td></tr></tbody></table></div></div>

The above table can then be used to create an undirected network object and visualize it using, for example, the [d3Network package](https://christophergandrud.github.io/networkD3/) for D3 JavaScript network graphs. The resulting network graph shows the relationships between topics such that topics that are closer together and connected by stronger edges tend to appear more frequently in employee comments together. The node size indicates how often the topic occurs with other topics in employee comments ([degree centrality](https://en.wikipedia.org/wiki/Centrality)), and the colors represent the communities (clusters) of topics as detected by the [Louvain method for community detection](https://en.wikipedia.org/wiki/Louvain_method). The graph is interactive, so you can zoom in/out and highlight specific parts of the graph you're interested in.

```r
library(igraph)
library(networkD3)

# creating network object
network <- graph_from_data_frame(pain_points_cooccurrence, directed=FALSE)

# computing degree centrality and community detection using Louvain method
V(network)$degree <- degree(network)
clusters <- cluster_louvain(network) 
V(network)$community <- clusters$membership

# preparing data for networkD3 dataviz
networkD3_data <- igraph_to_networkD3(network)
networkD3_data$nodes$group <- V(network)$community
networkD3_data$nodes$degree <- V(network)$degree
networkD3_data$nodes$reporting_name <- V(network)$name
# specifying custom color scale
colors <- c("#1b39a6", "#b13aa0", "#72a239", "#895f22", "#d08311", "#ca4f1a", "#8764d9")

# networkD3 dataviz
networkD3::forceNetwork(
  Links = networkD3_data$links,
  Nodes = networkD3_data$nodes,
  Source = 'source',
  Target = 'target',
  NodeID = 'reporting_name',
  Value = "value",
  Group = "group",
  Nodesize = 'degree',
  arrows = FALSE,
  legend = FALSE,
  opacity = 1,
  zoom = TRUE,
  fontSize = 20,
  opacityNoHover = 1,
  linkDistance = 60,
  charge = -900,
  colourScale = JS(paste0("d3.scaleOrdinal().range([\"", paste(colors, collapse = "\", \""), "\"])"))
)

```

<iframe src="./network-graph-employee-comments/widget-forcenetwork-01.htm" title="Interactive forceNetwork widget" loading="lazy" style="width:100%;height:384px;border:0"></iframe>

<!-- RELATED:BEGIN -->
## Related notes
- [[psychometric-network-analysis|Psychometric network analysis & employee survey data]]
- [[employee-feedback-analysis-using-openai|Employee feedback analysis using tools from OpenAI]]
- [[linkedin-contacts-job-positions|Analyzing LinkedIn connections' jobs using LLMs and the BERTopic package]]
- [[directionally-correct-podcast-topic-explorer|Turning 152 Directionally Correct podcast episodes into an interactive topic explorer]]
- [[latent-class-analysis|Latent Class Analysis of responses from employee surveys]]
<!-- RELATED:END -->

---
> 📄 Read the [original post with full outputs](https://blog-about-people-analytics.netlify.app/posts/2024-06-24-network-graph-employee-comments/) on my blog.
