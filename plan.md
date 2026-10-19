# Development Plan: NHANES Health Correlation Explorer (`app.py`)

## Context
We're building a single-file Streamlit app for exploring correlations among health measures in `nhanes_health.csv` (CDC NHANES 2017–2018, adults 20+). It needs five features: a data preview, a pairwise explorer, a heatmap, sex/age filters and a Pearson/Spearman toggle. Every r has to be computed from the **currently filtered** data with **pairwise** missing-value exclusion, and every r is shown next to its own n. The numbers will be checked by hand in pandas afterward (the M9 verification table), so getting them right matters more than anything else.

## What the data looks like (inspected, read-only)
- **4,433 rows × 11 columns, no duplicate rows.**
- `sex`: text, `Female` 2,263 / `Male` 2,170. Used only for filtering.
- Numeric columns: `age` (int, 20–80, **80 means 80+**, 271 people), `bmi`, `waist_cm`, `systolic_bp`, `diastolic_bp`, `hba1c`, `sleep_hours` (float), and `total_chol`, `hdl_chol`, `sedentary_minutes` (int).
- **There are no missing values in any column.** The pairwise-n logic is still required and will be built, but on this file n will always equal the number of filtered rows. We'll test that logic on a copy of the data with missing values added on purpose (see Testing).
- No sentinel codes such as 7777 or 9999. Ranges look plausible: SBP 74–234, HbA1c 4.1–16.2, sedentary 0–1320 min.
- `sleep_hours` and `age` are discrete with many ties, which matters for binned means and for Spearman.
- 1,628 participants have SBP ≥ 130.
- Reference value: Pearson r for age vs systolic_bp across all participants is 0.4627 (n = 4433). Spearman is 0.4802.
- Package note: pandas `DataFrame.corr(method="spearman")` works **without scipy**, but `Series.corr(method="spearman")` needs scipy. The plan only uses `DataFrame.corr`, so scipy isn't needed.

## Architecture: one file, one filtered DataFrame
`app.py` runs top to bottom in this order:

1. **Constants:** `DATA_PATH = "nhanes_health.csv"`, `NUMERIC_COLS` (the 10 listed columns, explicitly), `LABELS` (display name + units), `THRESHOLDS` (from the data dictionary), and `MIN_N = 3`.
2. **`load_data()`**, wrapped in `@st.cache_data`. It reads the CSV from the relative path, checks that the expected columns exist, and converts the numeric columns with `pd.to_numeric(errors="coerce")` so a bad value becomes NaN instead of crashing the app. It never drops rows.
3. **Sidebar → `fdf`.** The sidebar builds the sex mask and age mask once and produces a single filtered DataFrame, `fdf`, plus `method` (`"pearson"`/`"spearman"`).
4. **Every section gets only `fdf` and `method`.** The table, scatter, r, n and heatmap all read from `fdf`, and nothing downstream touches the unfiltered `df`. This is how the filters reach every view: there is one place where filtering happens, and every view reads its output.
5. If `fdf` is empty, show `st.warning` and stop with `st.stop()`.

`sex` is never in `NUMERIC_COLS`, so it can't be offered in a dropdown or the heatmap picker, and it can't enter any `.corr()` call.

## Missing values and n (one rule, two helpers)
- **`pair_corr(fdf, x, y, method) → (r, n, reason)`**
  - `sub = fdf[[x, y]].dropna()`. This is the pairwise deletion step, and `n = len(sub)`.
  - If `n < MIN_N`, the result is insufficient: "Insufficient data: n = {n} complete pairs (need ≥ 3)".
  - If either column is constant in `sub` (`nunique() < 2`, e.g. age range set to 80–80), the result is insufficient: "{var} has no variation in the filtered data."
  - Otherwise `r = sub.corr(method=method).iloc[0, 1]`.
- **`corr_matrix(fdf, cols, method) → (r_df, n_df)`**
  - `r_df = fdf[cols].corr(method=method, min_periods=MIN_N)`. pandas already applies pairwise-complete deletion and re-ranks each pair for Spearman.
  - `n_df = M.T @ M`, where `M = fdf[cols].notna().astype(int)`. This gives the complete-pair count for every cell.
  - Cells with no defined r (too few pairs or a constant column) stay NaN and are labeled "n/a".
- **Consistency guarantee:** for the same filters and method, `pair_corr(x, y)` must equal `r_df.loc[x, y]` and `n_df.loc[x, y]`. This is tested explicitly, and it's the same comparison as verification check #6.
- **Display:** r is rounded to 3 decimals and n is always shown right next to it.

## Build order (small steps, each runnable)
1. **Data and filters first.**
   - Load the data. Build the sidebar with a sex radio (`All / Female / Male`) and an age range slider (20–80, with a caption saying 80 = 80+). Show "Showing N of 4,433 participants" in the sidebar.
   - Data preview section: a short description (source, adults 20+, one row per participant), the data dictionary with units and thresholds, `st.dataframe(fdf)`, and a per-column missing-count table for the filtered data.
   - *Check:* switching to Female shows 2,263 rows.
2. **Method toggle.** Add a sidebar radio for Pearson or Spearman. It's stored once and passed to every later section.
3. **Pairwise numbers, before the plot.**
   - X and Y dropdowns limited to `NUMERIC_COLS`, defaulting to age and systolic_bp.
   - `pair_corr` feeds `st.metric` tiles for r, n and method, or an `st.warning` when the data is insufficient.
   - If X and Y are the same variable, show a note that r = 1 by definition.
   - *Check:* the result matches the pandas reference value above.
4. **Scatter plot (seaborn/matplotlib).**
   - Plot `sub` (the same complete-pairs data behind r and n), with semi-transparent points because there are about 4.4k of them.
   - Trend option, as a radio:
     - **Linear fit** (`sns.regplot(scatter=False)`)
     - **Binned means**: about 10 quantile bins on X with `pd.qcut(..., duplicates="drop")` for tied values. Plot the mean of X against the mean of Y per bin. This shows nonlinear shapes like the U-shaped sleep curve.
     - **None**
   - Optional "Color by health threshold" select. It offers SBP ≥ 130, DBP ≥ 80, BMI ≥ 30, HbA1c ≥ 6.5 and total cholesterol ≥ 240, or no coloring. The threshold variable doesn't have to be X or Y. Rows missing the threshold variable are labeled "Unknown".
   - Coloring changes the display only. r and n stay the same.
5. **Heatmap.**
   - `st.multiselect` over `NUMERIC_COLS` with all selected by default. If fewer than 2 are chosen, show a message instead of a plot.
   - `sns.heatmap(r_df, vmin=-1, vmax=1, center=0, cmap="RdBu_r", annot=labels, fmt="")`, where each label is `"0.46\nn=4433"` or `"n/a\nn=2"`.
   - The figure and font size scale with the number of variables. NaN cells are drawn in gray.
   - The colorbar is always fixed to −1…1, whatever the data range.
6. **Interpretation and cautions.**
   - A short notes block, plus a one-line caption under the scatter and under the heatmap, covering three points:
     - Correlation is not causation.
     - r ≈ 0 does not mean there's no relationship. It can hide a nonlinear one; try sleep_hours with binned means.
     - These are **unweighted** sample correlations. NHANES oversamples some groups, so the results describe this sample and not the US population.
   - The insufficient-data messages are already handled in steps 3 and 5.
7. **Layout polish.** Put the sections in `st.tabs` (Data · Pairwise · Heatmap · About) and close every figure with `plt.close(fig)` so memory doesn't build up across reruns.

## Testing
1. **Syntax:** `python -m py_compile app.py`.
2. **Independent pandas checks:** a scratch script outside the project folder computes the M9 verification values, which are then compared with what the app shows:
   - r for age/SBP, bmi/waist and waist/hdl across all participants
   - r and n for age/SBP for Female and for Male
   - Spearman versions of the same pairs
3. **Headless app test** with `streamlit.testing.v1.AppTest`, which ships with Streamlit, so no new package:
   - Drive the sidebar: Female, age 40–59, Spearman.
   - Assert that the r and n metric values match pandas for that filter.
   - Assert that the heatmap's age/SBP cell agrees with the pairwise result.
4. **Missing-value test:**
   - In the scratchpad, make a copy of the CSV with NaNs injected into a few columns, with different amounts in each.
   - Run the app from that folder with AppTest.
   - Confirm that n differs from pair to pair and equals `df[[x, y]].dropna()` for each pair, and that the heatmap's n cells differ from one another.
5. **Edge cases:**
   - Age range 80–80, where age is constant and age pairs show "insufficient"
   - A very narrow range plus one sex
   - X = Y
   - Heatmap with 0 or 1 variables selected
   - Switching methods updates both views
6. **Manual browser pass:** check that every control visibly updates the table, scatter, metrics and heatmap, and that the colorbar always reads −1 to 1.

## Run locally
```bash
uv run --with streamlit,pandas,seaborn streamlit run app.py
```
(matplotlib comes in automatically as a seaborn dependency. The M9 handout's command also adds `scipy`, which this design doesn't need.)

## Points needing clarification (the plan uses the default shown unless you say otherwise)
1. **scipy.** The handout's run command and `requirements.txt` example include scipy, but this design doesn't need it. *Default: don't use it.*
2. **No missing data in the file.** The pairwise-n rule is implemented and tested with synthetic NaNs, but in the real app every n will equal the filtered row count. Is that what you expect?
3. **"Insufficient data" threshold.** *Default: r is not shown when n < 3 or a variable is constant. A soft "small sample, interpret with caution" note appears when n < 30.* Would you prefer a different cutoff?
4. **Threshold coloring.** *Default: a dropdown of the 5 data-dictionary thresholds,* rather than only SBP ≥ 130.
5. **Sex filter control.** *Default: a radio with All / Female / Male.* A multiselect is the alternative, but it can be left empty.
6. **Trend line.** *Default: let the user choose between linear fit and binned means.* You wrote "trend line or binned means".
7. **Heatmap layout.** With 10 variables, showing both r and n in 100 cells is crowded. *Default: full matrix with r on line 1 and n on line 2 in a smaller font.* The alternative is the lower triangle only.
8. **Data table.** *Default: the table shows the filtered rows,* as the handout says the filters must update the table.
9. **Age 80 = 80+.** It's labeled as top-coded and otherwise treated as numeric 80.
10. **Deliverables.** After you approve, should I also save this plan as `plan.md`? I'd leave `requirements.txt`, `prompts.md` and `verification.md` until later steps, since you're meant to fill in the verification values yourself.
