---
title: Personas based on ML local interpretation algorithms
description: A demonstration of one method useful for sharing insights from fitted ML models.
date: '2023-11-09'
tags:
- machine-learning
- interpretability
- data-visualization
- r
- python
original: https://blog-about-people-analytics.netlify.app/posts/2023-11-09-personas-based-on-ml-local-interpretation-algos/
---

There is one very useful albeit relatively underused method of sharing insights from fitted ML models, at least in my professional bubble.

It's a method of identifying personas based on outputs from ML local interpretation algorithms, which provide information about the specific drivers of predictions for individual observations.

Its implementation is pretty straightforward:

1. Fit a ML model.
2. Generate predictions for each observation using the fitted model.
3. Identify drivers of predictions for individual observation units using a ML local interpretation algorithm, e.g., LIME or SHAP.
4. Use the data points from steps 2 and 3 to identify clusters with similar characteristics.
5. Name and describe personas corresponding to the identified clusters.

Let's see this in action using the Python code below. First, we need to create an artificial dataset on which we will demonstrate the method described above. We'll create a classification dataset - imagine, for example, that we're trying to predict sales performance based on some collaboration metrics, but feel free to imagine any scenario you like - and prepare a training and testing set to train our ML.   

```python
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
import pandas as pd


# defining the number of samples and features for the dataset
n_samples = 10000
n_features = 10

# creating the dataset
X, y = make_classification(n_samples=n_samples, n_features=n_features, n_informative=6, n_redundant=4, n_clusters_per_class=3, flip_y=0.27, class_sep=1, random_state=1979)

# creating a df from X and y
df = pd.DataFrame(X, columns=['feature_{}'.format(i) for i in range(n_features)])
df['criterion'] = y

# splitting the dataset into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1979)

```

```r
library(DT)
library(tidyverse)
library(reticulate)

# table dataviz
DT::datatable(
  py$df,
  class = 'cell-border stripe', 
  filter = 'top',
  extensions = 'Buttons',
  fillContainer = FALSE,
  rownames= FALSE,
  options = list(
    pageLength = 5, 
    autoWidth = TRUE,
    dom = 'Bfrtip',
    buttons = c('copy'), 
    scrollX = TRUE, 
    selection="multiple"
  )
)

```

<div class="data-table-preview"><p>Showing 20 of 10,000 rows and all 11 columns. <a href="https://blog-about-people-analytics.netlify.app/posts/2023-11-09-personas-based-on-ml-local-interpretation-algos/">View the full interactive table in the original post</a>.</p><div style="overflow-x:auto;max-width:100%"><table><thead><tr><th>feature_0</th><th>feature_1</th><th>feature_2</th><th>feature_3</th><th>feature_4</th><th>feature_5</th><th>feature_6</th><th>feature_7</th><th>feature_8</th><th>feature_9</th><th>criterion</th></tr></thead><tbody><tr><td>2.098614352501542</td><td>1.374719480592108</td><td>-0.9191645782888094</td><td>-0.780918072120477</td><td>-1.599227594254533</td><td>-0.7959120853730702</td><td>-3.259179232465449</td><td>-0.9171428223933069</td><td>-0.1772930426394639</td><td>0.2255819435781583</td><td>1</td></tr><tr><td>1.67632562812557</td><td>1.38138189193838</td><td>1.056923897711844</td><td>2.538712262949502</td><td>-0.3525579135354033</td><td>3.212385404787221</td><td>3.011549280312139</td><td>0.7267812372957051</td><td>1.852244086858446</td><td>-0.4091471619081193</td><td>0</td></tr><tr><td>-1.720584103015059</td><td>-1.409491002912926</td><td>-2.199964705148227</td><td>-0.8653154854725879</td><td>2.774751926323326</td><td>-0.7166501985332208</td><td>2.625182995059781</td><td>-0.6660550129148989</td><td>-0.5452189810712971</td><td>-1.350845012035189</td><td>0</td></tr><tr><td>-1.985919703292777</td><td>-2.86072367291261</td><td>2.580147825466496</td><td>1.821873705565894</td><td>-3.752535481063338</td><td>-2.27915984632977</td><td>0.1064296454221614</td><td>-1.934946929986992</td><td>3.057431424091343</td><td>0.9235282359680914</td><td>1</td></tr><tr><td>-1.545153755119047</td><td>0.270433562252925</td><td>-0.1789652574864389</td><td>-2.58056813121976</td><td>-1.938940120845749</td><td>-0.9571457502431397</td><td>1.889375801812126</td><td>-5.671503753856408</td><td>1.730339896885641</td><td>-3.478797011089272</td><td>1</td></tr><tr><td>0.606255068598204</td><td>3.878402561069994</td><td>4.664872516639435</td><td>-2.427904739527241</td><td>-3.791593527509868</td><td>2.199072555342731</td><td>-2.777137002053879</td><td>-1.124762664967311</td><td>-0.5114295458971684</td><td>-0.5110140914213703</td><td>1</td></tr><tr><td>1.653044426289712</td><td>-0.08117254034093846</td><td>1.917457896565276</td><td>1.956250785120067</td><td>-0.9744261555055936</td><td>0.3056329483916884</td><td>-3.640233172248263</td><td>4.182496661077225</td><td>-1.250577236068326</td><td>3.331828032158904</td><td>0</td></tr><tr><td>-0.6039952326830209</td><td>-3.235164260477323</td><td>-0.9664178137339166</td><td>1.015270542868404</td><td>0.5549362184179625</td><td>-1.445015351887999</td><td>1.095351393630706</td><td>0.6513625544504575</td><td>-0.5977569814907753</td><td>-0.1641608960899147</td><td>1</td></tr><tr><td>-0.339537721298507</td><td>-0.1843999592465024</td><td>-0.1156959843551293</td><td>0.4314816856919246</td><td>0.5817290397768387</td><td>-0.1046952305861542</td><td>0.1208612826161675</td><td>0.5553734891591451</td><td>0.196231277594596</td><td>0.6150134653199353</td><td>1</td></tr><tr><td>2.144298526193534</td><td>0.0001764719029658801</td><td>-0.2843396717690671</td><td>5.064113395081752</td><td>0.682726609169388</td><td>2.424825980958504</td><td>3.056600980307955</td><td>2.491195339577589</td><td>2.797612170450239</td><td>1.509942929749928</td><td>0</td></tr><tr><td>1.982499617534076</td><td>2.167663549424566</td><td>0.1108676147194623</td><td>-0.4976773866800654</td><td>-1.875746547831598</td><td>-0.350101368251314</td><td>-3.907801328955293</td><td>-0.3196587710827962</td><td>0.1893025277889508</td><td>1.170763822879558</td><td>1</td></tr><tr><td>-0.9104055685250202</td><td>-0.08411953760408653</td><td>1.443909862072889</td><td>0.0462888633196945</td><td>-1.088690513277234</td><td>-1.162621661835367</td><td>-2.362028042238262</td><td>0.4331062780050637</td><td>0.3901848940816154</td><td>1.917779532718156</td><td>1</td></tr><tr><td>-0.3383588060299922</td><td>0.02343326320221784</td><td>1.060601691999946</td><td>0.2243893393241443</td><td>-2.897626300316894</td><td>0.858208661593379</td><td>3.940767512879623</td><td>-4.640702186808283</td><td>3.24612235374303</td><td>-3.273428217491637</td><td>0</td></tr><tr><td>1.388330152284588</td><td>0.3746859657682847</td><td>-3.046824105075081</td><td>-3.349942339988245</td><td>-2.007714887581449</td><td>-4.478221805294153</td><td>-6.665544926572675</td><td>-3.023133899371105</td><td>-1.233724164212285</td><td>0.1300880814919325</td><td>1</td></tr><tr><td>-1.664177260884212</td><td>1.705678110687599</td><td>4.619958192778183</td><td>-1.337389076735545</td><td>-0.9591416084461636</td><td>2.052938113536521</td><td>-0.5339339574007115</td><td>1.211419217961552</td><td>-1.088087808546039</td><td>0.4929198458129632</td><td>1</td></tr><tr><td>-2.82045679716152</td><td>-0.2445475259223269</td><td>4.474394511903276</td><td>-0.2446814063745327</td><td>-1.099364216549322</td><td>1.52306351355223</td><td>2.139602661441118</td><td>0.09344208891136398</td><td>0.3504152489265583</td><td>-0.3168708295285273</td><td>1</td></tr><tr><td>-0.1313040817480355</td><td>-3.030843804479429</td><td>1.096123362088401</td><td>3.47833694402167</td><td>0.4287551049545435</td><td>-0.3501095450604308</td><td>0.04472353983269112</td><td>4.088879682828755</td><td>-0.2932330527920979</td><td>2.743900866035954</td><td>0</td></tr><tr><td>-2.111896301735312</td><td>2.307300089301307</td><td>1.633827741022214</td><td>-4.648719903798532</td><td>-0.2159202322438495</td><td>0.0333113132084939</td><td>-1.574828780598303</td><td>-2.079278387464681</td><td>-1.785971610236544</td><td>-1.418855767281632</td><td>0</td></tr><tr><td>-0.1764243280454234</td><td>2.574152406872238</td><td>2.716899185303378</td><td>-6.255151494713817</td><td>-5.246608746156207</td><td>-3.719869443773562</td><td>-10.56680120102019</td><td>-2.817839726674779</td><td>-2.919540515465989</td><td>0.9967564528818011</td><td>1</td></tr><tr><td>3.409578524747143</td><td>-2.445081300965736</td><td>-7.664062011833757</td><td>3.080482909459106</td><td>4.241655824264384</td><td>0.5431805052224026</td><td>6.159623292036074</td><td>-0.2329258747419958</td><td>0.6629857529783925</td><td>-3.123139875453357</td><td>0</td></tr></tbody></table></div></div>

Now we can fit and fine-tune our ML (XGBoost) model.

```python
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV

# fitting a XGBoost model with hyperparameter tuning and 10-fold cross-validation
# initializing the XGBoost classifier
xgb_model = XGBClassifier(random_state=1979)

# defining the parameter grid for hyperparameter tuning
param_grid = {
  'n_estimators': [100, 200],
  'max_depth': [3, 5, 7],
  'learning_rate': [0.01, 0.1, 0.2]
}

# setting up the grid search with 10-fold cross-validation
grid_search = GridSearchCV(xgb_model, param_grid, cv=10, scoring='f1')

# fitting the model with hyperparameter tuning
grid_search.fit(X_train, y_train)

# getting the best estimator
best_xgb_model = grid_search.best_estimator_

```
The classification performance metrics below show that the fitted model performs well on the test data, so we can safely proceed further.

```python
from sklearn.metrics import classification_report, roc_auc_score
import numpy as np

# predictions on the test set
y_pred = best_xgb_model.predict(X_test)
y_pred_proba = best_xgb_model.predict_proba(X_test)[:, 1] 

# classification report
report = classification_report(y_test, y_pred)
print(report)

# ROC AUC score
roc_auc = roc_auc_score(y_test, y_pred_proba)
print('ROC AUC score: ', np.round(roc_auc, 2))

```
Now we will generate LIME explanations for each observation in the testing dataset and standardize them for later analysis and visualization (including the predicted probabilities of the positive class).

```python
import lime.lime_tabular
from sklearn.preprocessing import StandardScaler

# using LIME for local interpretation
# initializing the LIME explainer
explainer = lime.lime_tabular.LimeTabularExplainer(
    training_data=X_train,
    feature_names=['Feature_{}'.format(i) for i in range(X_train.shape[1])],
    class_names=['Low Performance', 'High Performance'],
    mode='classification',
    random_state=1234
)


# df for storing the LIME explanations for all observation
explanations_df = pd.DataFrame()
feature_names = df.columns[:-1].tolist()

# generating LIME explanations for each observation in the test set
for i in range(X_test.shape[0]):
    
    # predicted probability for the positive class
    predicted_class_proba = y_pred_proba[i]
    
    # generating the LIME explanation
    exp = explainer.explain_instance(X_test[i], best_xgb_model.predict_proba, num_features=X_train.shape[1])
    exp_list = exp.as_list()
    
    feature_values = {name: 0 for name in feature_names}
    # looping through the employee's conditions and updating feature_values accordingly
    for condition, value in exp_list:
        for feature_name in feature_names:
            if feature_name in condition.lower():
                feature_values[feature_name] = value
                break

    # adding the predicted probability for the positive class
    feature_values['predicted_class_proba'] = predicted_class_proba

    supp_df = pd.DataFrame(feature_values, index=[0])  
    explanations_df = pd.concat([explanations_df, supp_df], ignore_index=True) 

  
# standardizing all features (including the probability for the positive class)
scaler = StandardScaler()
explanations_scaled = scaler.fit_transform(explanations_df)
explanations_scaled_df = pd.DataFrame(explanations_scaled)
explanations_scaled_df.columns = explanations_df.columns

```

Using the UMAP 2D projection of the prediction explanations and predicted probabilities, we can see that that are several clusters of observations with similar predicted probabilities and their drivers.

```python
import umap
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(style="white")

# visualizing the personas using UMAP
# initializing and fitting UMAP
reducer = umap.UMAP(n_components=2, n_neighbors=50, min_dist=0.01, metric='euclidean', random_state=1979, n_jobs=1)
embedding = reducer.fit_transform(explanations_scaled)  

# plotting the explanations and predicted probability in 2D scatterplot 
plt.close()
plt.figure(figsize=(12, 8))
scatter = plt.scatter(embedding[:, 0], embedding[:, 1], c='lightblue', s=50, alpha=0.5)
plt.title('People with similar predictions and similar prediction drivers\n', fontsize=24)
plt.figtext(0.05, 0.05, "UMAP projection of the LIME prediction explanations and predicted probabilities.", wrap=True, horizontalalignment='left', fontsize=12)
plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
plt.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
plt.show()

```

![](./personas-based-on-ml-local-interpretation-algos/unnamed-chunk-6-1.png)

A clustering algorithm, such as HDBSCAN, can help us identify the clusters.

```python
import hdbscan
import matplotlib.patches as mpatches

# HDBSCAN clustering
clusterer = hdbscan.HDBSCAN(min_cluster_size=25, min_samples=10, cluster_selection_epsilon=0.3, prediction_data=True)
clusterer.fit(embedding)
clusters = clusterer.labels_

# adding the cluster labels to the dataframe
explanations_df['cluster'] = clusters

# plotting the clusters
plt.close()
plt.figure(figsize=(12, 8))
cmap = plt.cm.get_cmap('tab20')
norm = plt.Normalize(clusters.min(), clusters.max())
scatter = plt.scatter(embedding[:, 0], embedding[:, 1], c=clusters, s=50, cmap=cmap, norm=norm, alpha=0.5)
patches = [mpatches.Patch(color=cmap(norm(i)), label=f'Cluster {i}') for i in np.unique(clusters)]
plt.legend(handles=patches, fontsize=12)
plt.title('People with similar predictions and similar prediction drivers\n', fontsize=24)
plt.figtext(0.05, 0.05, "UMAP projection of the LIME prediction explanations and predicted probabilities. The clusters were identified using HDBSCAN.", wrap=True, horizontalalignment='left', fontsize=12)
plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
plt.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
plt.show()

```
There seem to be about eight clusters and some outliers (cluster -1). Let's look at how they differ in terms of predicted probabilities. According to the chart below, there appear to be four clusters with increased predicted probabilities (clusters 3, 5, 6, and 7), three with decreased predicted probabilities (clusters 0, 2, and 4), and one with more mixed predictions (cluster 1).  

```python
import matplotlib.colorbar as colorbar

# plotting the distribution of probability of positive classes
plt.close()
plt.figure(figsize=(12, 8))
scatter = plt.scatter(embedding[:, 0], embedding[:, 1], c=y_pred_proba, cmap='viridis', s=50, alpha = 0.5)
plt.title('People with similar predictions and similar prediction drivers\n', fontsize=24)
plt.figtext(0.05, 0.05, "UMAP projection of the LIME prediction explanations and predicted probabilities.", wrap=True, horizontalalignment='left', fontsize=12)
plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
plt.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
cbar = plt.colorbar(scatter)
cbar.set_label('Predicted class probability', rotation=270, labelpad=15)
plt.show()

```

![](./personas-based-on-ml-local-interpretation-algos/unnamed-chunk-8-5.png)

Now we can check for the selected clusters which features and in which direction most affect their respective predicted probabilities. For example, we can see from the table below that the clusters with lower predicted probabilities (clusters 0, 2 and 4) are driven either by the respective values in features 6 and 9 (cluster 0), or by the respective values in features 0, 3, 7 and 9 (cluster 2), or by the respective values in feature 0 (cluster 4).

```r
# creating a summary for each cluster across all feature drivers of predicted probabilities of the positive class
tab1 <- py$explanations_df %>% 
  dplyr::group_by(cluster) %>% 
  dplyr::summarise_all(~median(., na.rm = TRUE))

# tab dataviz
DT::datatable(
  round(tab1,2),
  class = 'cell-border stripe', 
  filter = 'top',
  extensions = 'Buttons',
  fillContainer = FALSE,
  rownames= FALSE,
  options = list(
    pageLength = 10, 
    autoWidth = TRUE,
    dom = 'Bfrtip',
    buttons = c('copy'), 
    scrollX = TRUE, 
    selection="multiple"
  )
) %>%
  formatStyle(
    names(tab1 %>% dplyr::select(-cluster, -predicted_class_proba)),
    background = styleColorBar(range(tab1 %>% dplyr::select(-cluster, -predicted_class_proba)), 'lightblue'),
    backgroundSize = '98% 90%',
    backgroundRepeat = 'no-repeat',
    backgroundPosition = 'center'
  ) 

```

<div class="data-table-preview"><p>Showing 9 of 9 rows and all 12 columns. <a href="https://blog-about-people-analytics.netlify.app/posts/2023-11-09-personas-based-on-ml-local-interpretation-algos/">View the full interactive table in the original post</a>.</p><div style="overflow-x:auto;max-width:100%"><table><thead><tr><th>cluster</th><th>feature_0</th><th>feature_1</th><th>feature_2</th><th>feature_3</th><th>feature_4</th><th>feature_5</th><th>feature_6</th><th>feature_7</th><th>feature_8</th><th>feature_9</th><th>predicted_class_proba</th></tr></thead><tbody><tr><td>-1</td><td>0.05</td><td>-0.03</td><td>0</td><td>-0.01</td><td>0.01</td><td>0</td><td>0.08</td><td>0.03</td><td>0.01</td><td>-0.02</td><td>0.76</td></tr><tr><td>0</td><td>0.04</td><td>-0.02</td><td>0</td><td>0.02</td><td>-0.01</td><td>0</td><td>-0.18</td><td>0</td><td>0</td><td>-0.08</td><td>0.13</td></tr><tr><td>1</td><td>0.05</td><td>0.03</td><td>0</td><td>-0.02</td><td>0.02</td><td>0</td><td>0.05</td><td>-0.03</td><td>0.01</td><td>-0.04</td><td>0.67</td></tr><tr><td>2</td><td>-0.12</td><td>0.01</td><td>-0.02</td><td>-0.03</td><td>0.01</td><td>0</td><td>0.07</td><td>-0.03</td><td>0.01</td><td>-0.04</td><td>0.22</td></tr><tr><td>3</td><td>0.03</td><td>0.03</td><td>0.06</td><td>0</td><td>0.02</td><td>0</td><td>0.06</td><td>0</td><td>0</td><td>0.05</td><td>0.81</td></tr><tr><td>4</td><td>-0.12</td><td>-0.01</td><td>-0.01</td><td>-0.01</td><td>-0.01</td><td>0</td><td>0.06</td><td>0.02</td><td>0</td><td>0.04</td><td>0.34</td></tr><tr><td>5</td><td>-0.12</td><td>0</td><td>0.06</td><td>0</td><td>-0.01</td><td>0</td><td>0.07</td><td>0</td><td>0.02</td><td>0.05</td><td>0.86</td></tr><tr><td>6</td><td>0.04</td><td>0</td><td>-0.01</td><td>0.02</td><td>0.01</td><td>0</td><td>0.07</td><td>0.02</td><td>0.03</td><td>0.05</td><td>0.85</td></tr><tr><td>7</td><td>0.04</td><td>0</td><td>-0.02</td><td>0</td><td>-0.01</td><td>0</td><td>0.06</td><td>0.01</td><td>-0.01</td><td>0.04</td><td>0.67</td></tr></tbody></table></div></div>
Combined with information on the median values of these specific features, we can get a good idea of the people who tend to under-perform and "why". For example, people in cluster 0 score too high in feature 6 and too low in feature 9; people in cluster 2 score too low in features 0, 3, 7 and 9; and people in cluster 4 score too low in features 0. Given these differences, it would be useful to consider different approaches to try to improve the sales performance of people based on information about which persona they belong to. We could also repeat a similar analysis for clusters with higher predicted probabilities to see which combination of features tends to be associated with higher performance.

```python
# creating a df with X and y from testing part of the dataset
test_df = pd.DataFrame(X_test, columns=['feature_{}'.format(i) for i in range(n_features)])
test_df['predicted_class_proba'] = y_pred_proba
test_df['cluster'] = clusters

```

```r
# creating a summary for each cluster across all raw data and predicted probability of the positive class
tab2 <- py$test_df %>% 
  dplyr::group_by(cluster) %>% 
  dplyr::summarise_all(~median(., na.rm = TRUE))

# tab dataviz
DT::datatable(
  round(tab2,2),
  class = 'cell-border stripe', 
  filter = 'top',
  extensions = 'Buttons',
  fillContainer = FALSE,
  rownames= FALSE,
  options = list(
    pageLength = 10, 
    autoWidth = TRUE,
    dom = 'Bfrtip',
    buttons = c('copy'), 
    scrollX = TRUE, 
    selection="multiple"
  )
) %>%
  formatStyle(
    names(tab2 %>% dplyr::select(-cluster, -predicted_class_proba)),
    background = styleColorBar(range(tab2 %>% dplyr::select(-cluster, -predicted_class_proba)), 'lightblue'),
    backgroundSize = '98% 90%',
    backgroundRepeat = 'no-repeat',
    backgroundPosition = 'center'
  ) 

```

<div class="data-table-preview"><p>Showing 9 of 9 rows and all 12 columns. <a href="https://blog-about-people-analytics.netlify.app/posts/2023-11-09-personas-based-on-ml-local-interpretation-algos/">View the full interactive table in the original post</a>.</p><div style="overflow-x:auto;max-width:100%"><table><thead><tr><th>cluster</th><th>feature_0</th><th>feature_1</th><th>feature_2</th><th>feature_3</th><th>feature_4</th><th>feature_5</th><th>feature_6</th><th>feature_7</th><th>feature_8</th><th>feature_9</th><th>predicted_class_proba</th></tr></thead><tbody><tr><td>-1</td><td>0.67</td><td>-0.34</td><td>-0.97</td><td>0.06</td><td>-1.02</td><td>-1.32</td><td>-1.27</td><td>-1.09</td><td>0.61</td><td>0.11</td><td>0.76</td></tr><tr><td>0</td><td>0.41</td><td>-0.91</td><td>-0.01</td><td>2.19</td><td>0.09</td><td>1.53</td><td>3.72</td><td>-0.19</td><td>1.47</td><td>-1.28</td><td>0.13</td></tr><tr><td>1</td><td>0.31</td><td>1.21</td><td>-1.4</td><td>-1.55</td><td>-1.47</td><td>-2.15</td><td>-1.94</td><td>-3.08</td><td>1.24</td><td>-0.45</td><td>0.67</td></tr><tr><td>2</td><td>-2.21</td><td>0.22</td><td>0.27</td><td>-2.2</td><td>-1.53</td><td>-2.49</td><td>-0.83</td><td>-3.54</td><td>1.67</td><td>-0.56</td><td>0.22</td></tr><tr><td>3</td><td>-0.45</td><td>1.04</td><td>3.76</td><td>0.1</td><td>-1.89</td><td>1.14</td><td>-1.69</td><td>1.25</td><td>-0.34</td><td>1.53</td><td>0.81</td></tr><tr><td>4</td><td>-1.94</td><td>-0.32</td><td>1.81</td><td>-1.08</td><td>-0.26</td><td>-0.72</td><td>-0.93</td><td>-0.32</td><td>0.21</td><td>0.88</td><td>0.34</td></tr><tr><td>5</td><td>-1.88</td><td>-0.07</td><td>3.86</td><td>-0.06</td><td>-0.33</td><td>1.14</td><td>-0.63</td><td>2.03</td><td>-1.36</td><td>1.32</td><td>0.86</td></tr><tr><td>6</td><td>0.1</td><td>-0.12</td><td>0.68</td><td>1.81</td><td>-0.97</td><td>-0.4</td><td>-0.44</td><td>-0.5</td><td>2.27</td><td>1.4</td><td>0.85</td></tr><tr><td>7</td><td>-0.11</td><td>-0.06</td><td>0.44</td><td>0.47</td><td>-0.34</td><td>-0.42</td><td>-1.17</td><td>0.49</td><td>0.27</td><td>1.17</td><td>0.67</td></tr></tbody></table></div></div>
Maybe you'll find the method described here useful in one of your ML projects. Happy data sleuthing 🙂

## Figures

![](./personas-based-on-ml-local-interpretation-algos/unnamed-chunk-7-3.png)

<!-- RELATED:BEGIN -->
## Related notes
- [[r-and-power-bi|Embedding R (or Python) ML models in Power BI dashboards]]
- [[personality-and-non-linearities|Nonlinear relationships between personality traits and business outcomes seem to be the norm rather than the exception]]
- [[interpretable-ml|Interpretable machine learning with modelStudio]]
- [[dag-and-double-ml|A plausible model of data-generating process eats ML algorithms for breakfast]]
- [[latent-class-analysis|Latent Class Analysis of responses from employee surveys]]
<!-- RELATED:END -->

---
> 📄 Read the [original post with full outputs](https://blog-about-people-analytics.netlify.app/posts/2023-11-09-personas-based-on-ml-local-interpretation-algos/) on my blog.
