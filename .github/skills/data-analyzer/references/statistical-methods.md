# Statistical Methods Reference

## Descriptive Statistics

### Central Tendency

| Measure | Use                     | Notes                 |
| ------- | ----------------------- | --------------------- |
| Mean    | Symmetric distributions | Sensitive to outliers |
| Median  | Skewed distributions    | Robust to outliers    |
| Mode    | Categorical data        | Can be multimodal     |

### Dispersion

| Measure            | Formula / Notes                     |
| ------------------ | ----------------------------------- |
| Range              | max − min                           |
| Variance           | Average squared deviation from mean |
| Standard Deviation | √Variance; same units as data       |
| IQR                | Q3 − Q1; robust to outliers         |

### Distribution Shape

- **Skewness** — positive (right tail), negative (left tail)
- **Kurtosis** — leptokurtic (heavy tails), platykurtic (light tails); excess kurtosis = kurtosis − 3

### Percentiles

- Quartiles: Q1 (25th), Q2 (50th / median), Q3 (75th)
- Outlier bounds (Tukey): below Q1 − 1.5×IQR or above Q3 + 1.5×IQR

---

## Inferential Statistics — Test Selection

### Comparing Means

| Scenario                   | Test               | Assumptions                               |
| -------------------------- | ------------------ | ----------------------------------------- |
| One sample vs. known value | One-sample t-test  | Normality                                 |
| Two independent groups     | Independent t-test | Normality, equal variance (Levene's test) |
| Two paired groups          | Paired t-test      | Normality of differences                  |
| 3+ independent groups      | One-way ANOVA      | Normality, homogeneity of variance        |
| 3+ groups, 2 factors       | Two-way ANOVA      | Same as one-way                           |
| Non-parametric 2-group     | Mann-Whitney U     | No normality required                     |
| Non-parametric 3+ groups   | Kruskal-Wallis     | No normality required                     |

### Comparing Proportions

| Scenario                            | Test                            |
| ----------------------------------- | ------------------------------- |
| Single proportion vs. expected      | Chi-square goodness of fit      |
| Two categorical variables (large n) | Chi-square test of independence |
| Two categorical variables (small n) | Fisher's exact test             |

### Correlation

| Type                | Test       | When to Use                         |
| ------------------- | ---------- | ----------------------------------- |
| Linear (continuous) | Pearson r  | Both variables normally distributed |
| Rank-based          | Spearman ρ | Non-normal, ordinal, or monotonic   |
| Concordance         | Kendall τ  | Small samples or many ties          |

### Distribution Tests

| Test               | Purpose                           |
| ------------------ | --------------------------------- |
| Shapiro-Wilk       | Test normality (n < 50 preferred) |
| Kolmogorov-Smirnov | Compare distribution to reference |
| Levene's test      | Test homogeneity of variance      |

---

## Effect Size Measures

Effect size answers "how big is the difference?" — independent of sample size.

| Measure          | Formula              | Context                 | Thresholds (Cohen)                      |
| ---------------- | -------------------- | ----------------------- | --------------------------------------- |
| Cohen's d        | (μ1 − μ2) / SDpooled | Mean differences        | Small: 0.2, Medium: 0.5, Large: 0.8     |
| Eta-squared (η²) | SSeffect / SStotal   | ANOVA                   | Small: 0.01, Medium: 0.06, Large: 0.14  |
| Odds Ratio       | (a/b) / (c/d)        | Categorical association | OR=1 (no effect), OR>1 (increased odds) |
| Pearson r²       | r²                   | Correlation             | % of variance explained                 |
| Cramér's V       | √(χ²/n·min(r−1,c−1)) | Chi-square              | 0–1 scale; > 0.3 = moderate             |

**Rule of thumb:** Always report effect size alongside p-value. A statistically significant result with a tiny effect size may not matter practically.

---

## Regression Quick Reference

| Type            | Use                                      | Key Output                |
| --------------- | ---------------------------------------- | ------------------------- |
| Simple linear   | One predictor → continuous outcome       | Slope, R²                 |
| Multiple linear | Multiple predictors → continuous outcome | Coefficients, adjusted R² |
| Logistic        | Predictors → binary outcome              | Odds ratios, ROC/AUC      |

**Check:** Residual plots for linearity, homoscedasticity, normality of residuals; VIF for multicollinearity (VIF > 10 is problematic).
