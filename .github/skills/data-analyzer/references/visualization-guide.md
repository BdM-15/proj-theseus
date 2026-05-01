# Data Visualization Guide

## Chart Selection

| Data Type                      | Use Case      | Recommended Chart                                   |
| ------------------------------ | ------------- | --------------------------------------------------- |
| Single continuous variable     | Distribution  | Histogram, density plot, box plot                   |
| Continuous over time           | Trend         | Line chart, area chart                              |
| Part-to-whole (≤6 categories)  | Composition   | Pie chart, donut chart                              |
| Part-to-whole (>6 or stacked)  | Composition   | Stacked bar chart                                   |
| Comparing categories           | Comparison    | Bar chart (horizontal if many labels), column chart |
| Two continuous variables       | Relationship  | Scatter plot                                        |
| Three variables (size matters) | Relationship  | Bubble chart                                        |
| Many variables                 | Multivariate  | Small multiples, heatmap, parallel coordinates      |
| Geographic data                | Spatial       | Choropleth map, dot map                             |
| Hierarchical data              | Structure     | Tree map, sunburst                                  |
| Distribution across groups     | Comparison    | Box plot, violin plot                               |
| Correlation matrix             | Relationships | Heatmap with values                                 |

## Choosing the Right Chart — Decision Questions

1. **How many variables?** 1 → distribution chart; 2 → scatter/line/bar; 3+ → small multiples or heatmap
2. **Are the variables continuous or categorical?** Continuous → scatter/line; categorical → bar/pie
3. **Is time involved?** Yes → line chart
4. **Am I comparing groups or showing composition?** Groups → bar; composition → stacked bar or pie
5. **What is the message?** Match the chart type to the message (trend, comparison, distribution, relationship)

---

## Design Principles

### Clarity

- Remove chart junk: gridlines, borders, unnecessary tick marks, 3D effects
- One message per chart
- Use direct labeling instead of legends when possible

### Accuracy

- Start axes at zero for bar charts (never truncate)
- Use consistent scales when comparing charts
- Don't distort proportions (avoid 3D pie charts)

### Efficiency (Data-Ink Ratio)

- Every pixel should convey information
- Remove redundant labels, decorative colors, and background patterns

### Accessibility

- Use colorblind-friendly palettes (e.g., ColorBrewer, Okabe-Ito)
- Don't rely on color alone to convey meaning — use shape or texture too
- Minimum font size: 11pt

### Annotation

- Annotate the key insight directly on the chart
- Highlight the data point or region being discussed
- Use a caption that states the takeaway, not just the variable names

---

## Common Chart Mistakes

| Mistake                         | Fix                                         |
| ------------------------------- | ------------------------------------------- |
| Truncated y-axis on bar chart   | Start at zero                               |
| Too many colors                 | Use 2–3 colors max; gray out non-focus data |
| Legend instead of direct labels | Label the lines/bars directly               |
| 3D charts                       | Use 2D — 3D distorts perception             |
| Pie chart with >6 slices        | Use a bar chart                             |
| Dual y-axes                     | Use two separate charts                     |
| Missing units/context           | Always label axes with units and date range |
