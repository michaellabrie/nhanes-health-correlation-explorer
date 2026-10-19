| # | Check | App shows | pandas gives | Match? |
|---|---|---|---|---|
| 1 | r for `age` vs `systolic_bp`, all participants | r = 0.463, n = 4,433 | r = 0.463, n = 4,433 | Yes |
| 2 | r for `bmi` vs `waist_cm`, all participants | r = 0.903, n = 4,433 | r = 0.903, n = 4,433 | Yes |
| 3 | r for `waist_cm` vs `hdl_chol`, all participants | r = -0.335, n = 4,433 | r = -0.335, n = 4,433 | Yes |
| 4 | r and n for `age` vs `systolic_bp`, Female only | r = 0.555, n = 2,263 | r = 0.555, n = 2,263 | Yes |
| 5 | r and n for `age` vs `systolic_bp`, Male only | r = 0.351, n = 2,170 | r = 0.351, n = 2,170 | Yes |
| 6 | Female-only heatmap `age` vs `systolic_bp` matches row 4 | r = 0.56, n = 2,263 | r = 0.555 (0.56 rounded), n = 2,263 | Yes |

## M9 Correlation Cautions

A correlation close to zero does not necessarily mean that two variables have no relationship. Pearson correlation measures linear relationships, so nonlinear patterns, such as the U-shaped relationship involving sleep, can have correlations near zero.

The heatmap uses a fixed color scale from -1 to 1. This is important because automatically adjusting the colors to the smallest and largest correlations could exaggerate weak relationships.

Correlation does not establish causation. Additionally, because these are unweighted NHANES correlations, the findings describe this sample rather than necessarily representing the US population.

## Code Check

### Independent pandas calculation

The values in the "pandas gives" column were computed outside the app, directly from `nhanes_health.csv`, with no app code involved. This is the script used for check 5 (Male only):

```python
import pandas as pd

df = pd.read_csv("nhanes_health.csv")

male = df[df["sex"] == "Male"]

pair = male[["age", "systolic_bp"]].dropna()

r = pair["age"].corr(pair["systolic_bp"])
n = len(pair)

print("Pearson r:", round(r, 3))
print("Sample size n:", n)
```

The other checks use the same approach: change the sex filter (`"Female"`) or remove it (all participants), and swap in the column pair being checked.

### Review of `app.py`

| What was checked | Where in `app.py` | Result |
|---|---|---|
| Data loads from the relative path `nhanes_health.csv` | `DATA_PATH = "nhanes_health.csv"` (line 17) | Pass |
| `sex` is never used in a correlation | `NUMERIC_COLS` (line 20) lists only the 10 numeric columns; every dropdown, the heatmap picker and every `.corr()` call draw from it | Pass |
| The filters feed every view | A single filtered DataFrame `fdf` is built once (lines 149–152); the table, scatter plot, r, n and heatmap all use `fdf` | Pass |
| Missing values are excluded pairwise and n counts complete pairs | `pair_corr`: `data[[x, y]].dropna()` and `n = len(sub)` (lines 101–102); heatmap n from `notna()` counts (line 118) | Pass |
| The heatmap color scale is fixed from −1 to 1 | `sns.heatmap(..., vmin=-1, vmax=1, center=0, ...)` (line 282) | Pass |
| The heatmap and pairwise view agree | Check 6 above | Pass |