# Common Analytical Pitfalls

## Statistical Pitfalls

### P-hacking

**What it is:** Testing multiple hypotheses and only reporting the significant ones.
**Why it matters:** With α = 0.05, 1 in 20 tests will appear significant by chance. Running 20 tests and reporting the one that "worked" is not valid analysis.
**Fix:** Pre-register hypotheses before looking at data. Apply Bonferroni correction or FDR control when running multiple tests.

### Cherry-picking Data

**What it is:** Selecting the subset of data that supports a predetermined conclusion.
**Fix:** Define your data selection criteria before analysis. Document every exclusion. Test sensitivity — does the finding survive if you include the excluded data?

### Ignoring Assumptions

**What it is:** Using parametric tests (t-test, ANOVA, Pearson) on data that violates their assumptions.
**Fix:** Always check normality (Shapiro-Wilk) and homogeneity of variance (Levene's) before applying parametric tests. Use non-parametric alternatives if violated.

### Misinterpreting P-values

**Common misreading:** "p < 0.05 means there is a 95% chance the hypothesis is true."
**Correct interpretation:** If H0 were true, there is a less than 5% probability of observing results this extreme or more extreme by chance.
**Fix:** Always pair p-value with effect size and confidence interval.

### Focusing Only on Statistical Significance

**What it is:** Reporting "significant" results from large samples where tiny, meaningless differences reach p < 0.05.
**Fix:** Report effect size (Cohen's d, R², η²) alongside p-value. A result can be statistically significant but practically irrelevant.

---

## Logical Pitfalls

### Confusing Correlation and Causation

**What it is:** Assuming A causes B because they are correlated.
**Classic example:** Ice cream sales correlate with drowning rates — both are caused by hot weather.
**Fix:** Identify the mechanism. Look for confounders. Consider natural experiments or controlled comparisons.

### Survivorship Bias

**What it is:** Analyzing only the cases that "made it" and ignoring failures.
**Example:** Studying successful companies to learn what makes companies succeed — failed companies aren't in the sample.
**Fix:** Explicitly ask "what data is missing from this dataset?" before drawing conclusions.

### Simpson's Paradox

**What it is:** A trend that appears in subgroups disappears or reverses when groups are combined.
**Example:** A treatment appears effective in both men and women separately, but ineffective in the combined group (due to different group sizes).
**Fix:** Always segment data before combining. Check whether aggregate conclusions hold within subgroups.

### Base Rate Neglect

**What it is:** Ignoring the baseline frequency when interpreting rates or probabilities.
**Fix:** Always contextualize rates with the base rate population. Ask "what would we expect by chance?"

---

## Data Handling Pitfalls

### Ignoring Missing Data

**What it is:** Assuming data is Missing Completely at Random (MCAR) when it may be Missing at Random (MAR) or Missing Not at Random (MNAR).
**Fix:** Analyze the missingness pattern. Is data more likely to be missing for certain groups? If MNAR, simple imputation will bias results.

### Overfitting

**What it is:** Building a model complex enough to fit the training data perfectly but that fails to generalize.
**Fix:** Use cross-validation. Apply regularization. Prefer simpler models when performance is similar.

### Extrapolating Beyond the Data Range

**What it is:** Making predictions outside the range of observed values.
**Fix:** Clearly state the range of the data. Mark predictions outside that range as extrapolations with explicit uncertainty.

### Data Snooping

**What it is:** Examining the data before deciding on the analysis approach, then choosing the approach that gives the most interesting result.
**Fix:** Separate exploratory analysis (hypothesis generation) from confirmatory analysis (hypothesis testing). Use a holdout set for confirmation.
