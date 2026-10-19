"""NHANES Health Correlation Explorer.

Explore correlations between health measures in the CDC's 2017-2018 NHANES
survey (nhanes_health.csv). Run with:

    uv run --with streamlit,pandas,seaborn streamlit run app.py
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATA_PATH = "nhanes_health.csv"

# The only columns allowed in correlations. `sex` is deliberately excluded.
NUMERIC_COLS = [
    "age",
    "bmi",
    "waist_cm",
    "systolic_bp",
    "diastolic_bp",
    "hba1c",
    "total_chol",
    "hdl_chol",
    "sleep_hours",
    "sedentary_minutes",
]

LABELS = {
    "age": "Age (years, 80 = 80+)",
    "bmi": "BMI (kg/m²)",
    "waist_cm": "Waist circumference (cm)",
    "systolic_bp": "Systolic BP (mmHg)",
    "diastolic_bp": "Diastolic BP (mmHg)",
    "hba1c": "HbA1c (%)",
    "total_chol": "Total cholesterol (mg/dL)",
    "hdl_chol": "HDL cholesterol (mg/dL)",
    "sleep_hours": "Sleep on workdays (hours)",
    "sedentary_minutes": "Sedentary time (min/day)",
}

DATA_DICTIONARY = pd.DataFrame(
    [
        ("age", "Age at screening (80 means 80 or older)", "years", ""),
        ("sex", "Female or Male (filter only, never correlated)", "text", ""),
        ("bmi", "Body mass index", "kg/m²", "Obesity: ≥ 30"),
        ("waist_cm", "Waist circumference", "cm", "Abdominal obesity"),
        ("systolic_bp", "Mean of up to 3 systolic readings", "mmHg", "High BP: ≥ 130"),
        ("diastolic_bp", "Mean of up to 3 diastolic readings", "mmHg", "High BP: ≥ 80"),
        ("hba1c", "Glycohemoglobin (avg. blood sugar, ~3 months)", "%", "Diabetes: ≥ 6.5"),
        ("total_chol", "Total cholesterol", "mg/dL", "High cholesterol: ≥ 240"),
        ("hdl_chol", 'HDL ("good") cholesterol', "mg/dL", "Low HDL is a risk factor"),
        ("sleep_hours", "Usual sleep on workdays (self-reported)", "hours", ""),
        ("sedentary_minutes", "Time sitting on a typical day (self-reported)", "minutes", ""),
    ],
    columns=["Column", "Meaning", "Units", "Health threshold"],
)

# Health thresholds for coloring the scatter plot: label -> (column, cutoff).
THRESHOLDS = {
    "Systolic BP ≥ 130 mmHg": ("systolic_bp", 130),
    "Diastolic BP ≥ 80 mmHg": ("diastolic_bp", 80),
    "BMI ≥ 30 kg/m²": ("bmi", 30),
    "HbA1c ≥ 6.5 %": ("hba1c", 6.5),
    "Total cholesterol ≥ 240 mg/dL": ("total_chol", 240),
}

MIN_N = 3  # fewer complete pairs than this -> no correlation is reported
SMALL_N = 30  # below this, show a "small sample" caution

CAUTION_CAPTION = (
    "Correlation is not causation · r ≈ 0 can hide a non-linear relationship · "
    "unweighted sample correlations, not US-population estimates."
)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in NUMERIC_COLS + ["sex"] if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing expected columns: {missing}")
    # Unparseable values become NaN (handled pairwise later) instead of crashing.
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# ---------------------------------------------------------------------------
# Correlation helpers (pairwise deletion; n = complete pairs actually used)
# ---------------------------------------------------------------------------
def pair_corr(data: pd.DataFrame, x: str, y: str, method: str):
    """Return (r, n, reason). r is None when it cannot be computed."""
    sub = data[[x, y]].dropna()
    n = len(sub)
    if n < MIN_N:
        return None, n, f"Insufficient data: n = {n} complete pairs (need at least {MIN_N})."
    for col in (x, y):
        if sub[col].nunique() < 2:
            return None, n, f"Insufficient data: `{col}` has no variation in the filtered data."
    r = sub.corr(method=method).iloc[0, 1]
    if pd.isna(r):
        return None, n, "Insufficient data: correlation is undefined for these values."
    return float(r), n, None


def corr_matrix(data: pd.DataFrame, cols: list, method: str):
    """Pairwise-complete correlation matrix and matching complete-pair counts."""
    r_df = data[cols].corr(method=method, min_periods=MIN_N)
    present = data[cols].notna().astype(int)
    n_df = present.T @ present
    return r_df, n_df


# ---------------------------------------------------------------------------
# Page setup and sidebar filters
# ---------------------------------------------------------------------------
st.set_page_config(page_title="NHANES Correlation Explorer", layout="wide")
st.title("NHANES Health Correlation Explorer")
st.caption("CDC National Health and Nutrition Examination Survey, 2017–2018 · adults aged 20+")

df = load_data(DATA_PATH)

st.sidebar.header("Filters")
sex_options = ["All"] + sorted(df["sex"].dropna().unique().tolist())
sex_choice = st.sidebar.radio("Sex", sex_options, horizontal=True)

age_min, age_max = int(df["age"].min()), int(df["age"].max())
age_range = st.sidebar.slider("Age range (years)", age_min, age_max, (age_min, age_max))
st.sidebar.caption("Age 80 means 80 or older (top-coded by NHANES).")

st.sidebar.header("Correlation method")
method_label = st.sidebar.radio(
    "Method",
    ["Pearson", "Spearman"],
    help="Pearson measures linear association; Spearman measures monotonic "
    "association using ranks. Applies to both the pairwise view and the heatmap.",
)
method = method_label.lower()

# The ONE place filtering happens. Every view below uses `fdf`, never `df`.
mask = df["age"].between(age_range[0], age_range[1])
if sex_choice != "All":
    mask &= df["sex"] == sex_choice
fdf = df[mask]

st.sidebar.markdown(f"**Showing {len(fdf):,} of {len(df):,} participants**")

if fdf.empty:
    st.warning("No participants match the current filters. Widen the age range or change the sex filter.")
    st.stop()

tab_data, tab_pair, tab_heat, tab_about = st.tabs(
    ["Data preview", "Pairwise explorer", "Correlation heatmap", "About & cautions"]
)

# ---------------------------------------------------------------------------
# 1. Data preview
# ---------------------------------------------------------------------------
with tab_data:
    st.subheader("Dataset")
    st.markdown(
        f"Each row is one participant in the CDC's 2017–2018 NHANES survey. The full file has "
        f"**{len(df):,} adults aged 20 and over**, with body measurements, blood pressure, lab "
        f"results and self-reported sleep and sitting time. The table below reflects the current "
        f"sidebar filters (**{sex_choice}**, ages **{age_range[0]}–{age_range[1]}**): "
        f"**{len(fdf):,} rows**."
    )
    st.dataframe(fdf, hide_index=True)

    col_dict, col_missing = st.columns([3, 1])
    with col_dict:
        st.markdown("**Data dictionary**")
        st.dataframe(DATA_DICTIONARY, hide_index=True)
    with col_missing:
        st.markdown("**Missing values (filtered rows)**")
        st.dataframe(
            fdf.isna().sum().rename("missing").to_frame(),
        )

# ---------------------------------------------------------------------------
# 2. Pairwise explorer
# ---------------------------------------------------------------------------
with tab_pair:
    st.subheader(f"Pairwise correlation ({method_label})")

    c1, c2 = st.columns(2)
    x = c1.selectbox(
        "X variable", NUMERIC_COLS, index=NUMERIC_COLS.index("age"), format_func=LABELS.get
    )
    y = c2.selectbox(
        "Y variable", NUMERIC_COLS, index=NUMERIC_COLS.index("systolic_bp"), format_func=LABELS.get
    )

    c3, c4 = st.columns(2)
    trend = c3.radio("Trend", ["Linear fit", "Binned means", "None"], horizontal=True)
    color_choice = c4.selectbox("Color points by health threshold", ["None"] + list(THRESHOLDS))

    if x == y:
        st.info("X and Y are the same variable, so r = 1 by definition. Pick two different variables.")
    else:
        r, n, reason = pair_corr(fdf, x, y, method)

        m1, m2, m3 = st.columns(3)
        m1.metric(f"{method_label} r", "n/a" if r is None else f"{r:.3f}")
        m2.metric("n (complete pairs)", f"{n:,}")
        m3.metric("Filtered participants", f"{len(fdf):,}")

        if reason:
            st.warning(reason)
        elif n < SMALL_N:
            st.info(f"Small sample (n = {n}): interpret this correlation with caution.")

        if n > 0:
            # Plot exactly the complete pairs that produced r and n.
            sub = fdf[[x, y]].dropna()
            plot_df = sub.copy()
            hue = None
            if color_choice != "None":
                thr_col, cutoff = THRESHOLDS[color_choice]
                thr_vals = fdf.loc[sub.index, thr_col]
                group = pd.Series("Unknown", index=sub.index)
                group[thr_vals >= cutoff] = f"{thr_col} ≥ {cutoff}"
                group[thr_vals < cutoff] = f"{thr_col} < {cutoff}"
                plot_df["group"] = group
                hue = "group"

            fig, ax = plt.subplots(figsize=(8, 5))
            sns.scatterplot(
                data=plot_df, x=x, y=y, hue=hue, alpha=0.35, s=14, edgecolor=None, ax=ax
            )
            if trend == "Linear fit" and n >= 2 and sub[x].nunique() > 1:
                sns.regplot(
                    data=sub, x=x, y=y, scatter=False, ci=None, color="black",
                    label="Linear fit (all points)", line_kws={"linewidth": 2}, ax=ax,
                )
            elif trend == "Binned means" and sub[x].nunique() > 1:
                bins = pd.qcut(sub[x], q=10, duplicates="drop")
                binned = sub.groupby(bins, observed=True)[[x, y]].mean()
                ax.plot(
                    binned[x], binned[y], color="black", marker="o", linewidth=2,
                    label="Binned means (deciles of X)",
                )
            ax.set_xlabel(LABELS[x])
            ax.set_ylabel(LABELS[y])
            r_text = "n/a" if r is None else f"{r:.3f}"
            ax.set_title(f"{method_label} r = {r_text}, n = {n:,}")
            if ax.get_legend_handles_labels()[0]:
                ax.legend(loc="best", fontsize=8)
            st.pyplot(fig)
            plt.close(fig)

            st.caption(
                "Point colors are for display only; r and n use all plotted points. "
                + CAUTION_CAPTION
            )

# ---------------------------------------------------------------------------
# 3. Correlation heatmap
# ---------------------------------------------------------------------------
with tab_heat:
    st.subheader(f"Correlation heatmap ({method_label})")
    cols = st.multiselect(
        "Variables to include", NUMERIC_COLS, default=NUMERIC_COLS, format_func=LABELS.get
    )

    if len(cols) < 2:
        st.info("Select at least two variables to draw the heatmap.")
    else:
        r_df, n_df = corr_matrix(fdf, cols, method)
        k = len(cols)
        fig, ax = plt.subplots(figsize=(1.1 * k + 3, 0.9 * k + 2))
        ax.set_facecolor("lightgray")  # undefined (NaN) cells show as gray
        sns.heatmap(
            r_df, vmin=-1, vmax=1, center=0, cmap="RdBu_r", annot=False,
            square=True, linewidths=0.5, cbar_kws={"label": f"{method_label} r"}, ax=ax,
        )
        # Annotate every cell (including NaN ones) with r and its own n.
        font = max(6, 11 - k // 2)
        for i, row in enumerate(cols):
            for j, col in enumerate(cols):
                r_val = r_df.loc[row, col]
                n_val = int(n_df.loc[row, col])
                text = f"n/a\nn={n_val}" if pd.isna(r_val) else f"{r_val:.2f}\nn={n_val}"
                color = "white" if pd.notna(r_val) and abs(r_val) > 0.6 else "black"
                ax.text(j + 0.5, i + 0.5, text, ha="center", va="center",
                        fontsize=font, color=color)
        ax.set_xticklabels(cols, rotation=45, ha="right")
        ax.set_yticklabels(cols, rotation=0)
        st.pyplot(fig)
        plt.close(fig)

        if r_df.isna().to_numpy().any():
            st.warning(
                f"Cells marked n/a have too few complete pairs (fewer than {MIN_N}) or a "
                "variable with no variation in the filtered data."
            )
        st.caption(
            "Color scale fixed from −1 to 1. Each cell's n is the number of participants with "
            "values for both variables. " + CAUTION_CAPTION
        )

# ---------------------------------------------------------------------------
# 4. About & cautions
# ---------------------------------------------------------------------------
with tab_about:
    st.subheader("How to read these correlations")
    st.markdown(
        f"""
- **Correlation does not establish causation.** Two measures can move together because of a
  shared cause (age, for example), reverse causation, or chance.
- **A correlation near zero does not mean there is no relationship.** Pearson r captures only
  *linear* association and Spearman only *monotonic* association. A U-shaped pattern, like the
  one between sleep and many health outcomes, can give r ≈ 0. Try `sleep_hours` with
  **Binned means** in the pairwise view.
- **These are unweighted sample correlations.** NHANES deliberately oversamples some groups
  and provides survey weights for population estimates. This app ignores the weights, so its
  results describe *this sample* and should not be generalized to the US population.
- **Missing values are excluded pairwise.** Each correlation uses only participants with values
  for both variables, and the n shown next to every r is that count of complete pairs. When
  fewer than {MIN_N} complete pairs remain, or a variable has no variation (e.g. an age range of
  80–80), no correlation is reported.
- **Filters apply everywhere.** The sex and age filters, and the Pearson/Spearman choice, apply
  to the table, the scatter plot, r, n and the heatmap.
"""
    )
