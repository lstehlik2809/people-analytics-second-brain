---
title: Turning 152 Directionally Correct podcast episodes into an interactive topic explorer
description: On using GenAI, topic analysis, and network visualization to make 152 Directionally Correct podcast episodes easier to explore.
date: '2026-08-18'
tags:
- knowledge-management
- topic-analysis
- network-analysis
- data-visualization
- generative-ai
- embeddings
- people-analytics
original: https://blog-about-people-analytics.netlify.app/posts/2026-08-18-directionally-correct-podcast-topic-explorer/
---

Currently, I’m exploring different ways to represent, visualize, and make knowledge and ideas easier to consume and navigate. As part of that, I recently shared the result of my attempt to build [a second brain rooted in my People Analytics blog](https://lstehlik2809.github.io/people-analytics-second-brain/), accessible to both people and AI agents.

This time, I wanted to try something a bit different: a visual knowledge interface that turns a collection of content into an interactive network, complementary charts, and a searchable catalog.

So I needed a good knowledge source to test it on. Being a big fan of the [Directionally Correct podcast](https://www.youtube.com/@directionallycorrect), I quickly converged on its archive as a perfect test case. The episodes contain a huge amount of interesting and useful material for people analytics practitioners, but a lot of that knowledge is buried inside individual episodes and can be hard to rediscover later.

The result is a webpage where you can explore 152 episodes published between April 9, 2023, and August 17, 2026. A user can…️

* Explore a network of topics based on how often they appear together in the same episodes. ️
* Select a topic to read an AI synthesis of the extracted topic-related ideas - including shared ground, divergence, tensions, and distinctive perspectives - and see its strongest connections and relevant episodes. From there, you can open an episode, read its main ideas, or follow the link to the original source.️
* Search for topics and filter the exploration by publication date, guest, or thematic cluster.️
* Browse charts to see which topics occurred most often, which were relatively niche, and how the share of episodes containing each topic changed over time.️
* Search and filter the complete episode catalog by guest, topic, title, or summary content. Open any episode to explore its topics and main ideas, along with five semantically related episodes that can take you further through the archive.

Here is a [link to the webpage](https://lstehlik2809.github.io/directionally-correct-topic-map/).

<object
  data="./directionally-correct-podcast-topic-explorer/directionally_correct_topic_map_carousel_pdf.pdf"
  type="application/pdf"
  width="100%"
  height="800px">

  <p>

    Your browser cannot display this PDF.
    <a href="./directionally-correct-podcast-topic-explorer/directionally_correct_topic_map_carousel_pdf.pdf" download>Download the PDF</a>.

  </p>
</object>

<p>

  <a href="./directionally-correct-podcast-topic-explorer/directionally_correct_topic_map_carousel_pdf.pdf" download>
    Download the PDF
  </a>

</p>

⚠️ The topic assignments, topic syntheses, cluster labels, structured summaries, and related-episode recommendations were created with the help of GenAI. That makes it possible to process this amount of material, but it also means there will almost inevitably be some mistakes and imprecisions. So, treat the explorer as a tool for exploration rather than a substitute for the original episodes, which are linked throughout the app.

Have a look and let me know whether it helps you get more out of the podcast - which view is most useful, what works, what’s missing, what’s confusing, or what could be improved. And who knows - if Cole Napper likes it, maybe he’ll decide to polish it, push it further, and turn it into a live, continuously updated companion to his awesome podcast 😉

P.S. To be clear: any mistakes, omissions, or rough edges in the topic assignments, summaries, methodology, recommendations, or visualizations are mine alone 🙋

P.P.S. The [repo](https://github.com/lstehlik2809/directionally-correct-topic-map) for this explorer is public, with an asterisk: it contains the deployed app and browser-ready data, but not the raw transcripts or local processing code. The stack used was fairly lean: Apify for YouTube transcripts, the OpenAI API for structured idea extraction, controlled topic tagging, embeddings, and evidence-linked syntheses, and Codex for building the pipeline and interface. The explorer itself is React/TypeScript with a force-graph library, hosted on GitHub Pages. For more details, check a proper pipeline write-up in the README.

<!-- RELATED:BEGIN -->
## Related notes
- [[people-analytics-second-brain|My second People Analytics brain - both for people and AI agents]]
- [[agentic-ai-for-visual-data-exploration|Agentic AI for visual data exploration]]
- [[linkedin-contacts-job-positions|Analyzing LinkedIn connections' jobs using LLMs and the BERTopic package]]
- [[employee-feedback-analysis-using-openai|Employee feedback analysis using tools from OpenAI]]
- [[searching-and-querying-aihr-blog-posts|Searching & querying AIHR blog posts on People Analytics topics]]
<!-- RELATED:END -->

---
> 📄 Read the [original post with full outputs](https://blog-about-people-analytics.netlify.app/posts/2026-08-18-directionally-correct-podcast-topic-explorer/) on my blog.
