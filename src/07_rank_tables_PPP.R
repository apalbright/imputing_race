# =============================================================================
# 07_rank_tables_PPP.R
# Rank-order summary table comparing race imputation methods
# PPP sample (uses fintech-coded gaps; BIRDiE merged into the full table)
# =============================================================================

library(tidyverse)
library(gt)

# --- Configuration -----------------------------------------------------------

METHODS <- c("Last Name", "ZIP", "BISG", "BIFSG", "ZRP", "NamePrism")
BIRDIE_METHODS <- "BIRDiE"
NOT_APPLICABLE <- "--"
DISPLAY_METHOD_LABELS <- c("Last Name" = "Surname", "ZIP" = "Zip")

base_dir <- here::here()
plots_dir <- file.path(base_dir, "Results", "Plots")


# --- Helper: format ranks with ties and exclusions ---------------------------

format_rank <- function(rank_vec) {
  counts <- table(rank_vec[!is.na(rank_vec)])
  result <- rep(NOT_APPLICABLE, length(rank_vec))
  for (i in seq_along(rank_vec)) {
    if (is.na(rank_vec[i])) {
      result[i] <- NOT_APPLICABLE
    } else if (counts[as.character(rank_vec[i])] > 1) {
      result[i] <- paste0(rank_vec[i], " (tie)")
    } else {
      result[i] <- as.character(rank_vec[i])
    }
  }
  result
}

get_metric_value <- function(df, method, column) {
  row <- df %>% filter(Method == method)
  if (nrow(row) == 0 || !column %in% names(row)) {
    return(NA_real_)
  }
  as.numeric(row[[column]][1])
}

display_method_names <- function(methods) {
  unname(ifelse(methods %in% names(DISPLAY_METHOD_LABELS), DISPLAY_METHOD_LABELS[methods], methods))
}

# --- Step 1: Load data -------------------------------------------------------

f1_race <- read_csv(file.path(plots_dir, "PPP_04_F1_race.csv"),
                    show_col_types = FALSE) %>%
  filter(Method %in% METHODS)

f1_agg <- read_csv(file.path(plots_dir, "PPP_05_F1_aggregated.csv"),
                   show_col_types = FALSE) %>%
  filter(Method %in% METHODS)

gaps_raw <- read_csv(file.path(plots_dir, "PPP_07_all_gaps.csv"),
                     show_col_types = FALSE)
real_gaps <- gaps_raw %>% filter(Method == "Real")
gaps <- gaps_raw %>% filter(Method %in% METHODS)

pop_raw <- read_csv(file.path(plots_dir, "PPP_08_population.csv"),
                    show_col_types = FALSE)
real_pop <- pop_raw %>% filter(Method == "Real")
pop <- pop_raw %>% filter(Method %in% METHODS)

available_methods <- Reduce(
  intersect,
  list(
    METHODS,
    unique(f1_race$Method),
    unique(f1_agg$Method),
    unique(gaps$Method),
    unique(pop$Method)
  )
)

missing_methods <- setdiff(METHODS, available_methods)
if (length(missing_methods) > 0) {
  warning(
    "Skipping methods missing from one or more PPP input tables: ",
    paste(missing_methods, collapse = ", ")
  )
}
if (length(available_methods) == 0) {
  stop("No PPP methods are present across all required input tables.")
}
METHODS <- available_methods

# --- Step 2: Gap setup -------------------------------------------------------

race_cols <- c("White", "Black", "Hispanic", "Asian", "Other")

# Map each gap column to the races it involves
gap_race_map <- list(
  Black_White    = c("Black", "White"),
  Black_Hispanic = c("Black", "Hispanic"),
  Black_Asian    = c("Black", "Asian"),
  Hispanic_White = c("Hispanic", "White"),
  Hispanic_Asian = c("Hispanic", "Asian"),
  Asian_White    = c("Asian", "White")
)

# --- Helper: rank a metric across methods (returns character vector) ----------
# values: named numeric vector (one per method), higher_better: TRUE for F1

rank_metric <- function(values, higher_better = TRUE, excluded = rep(FALSE, length(values))) {
  stopifnot(length(values) == length(excluded))

  result <- rep(NOT_APPLICABLE, length(values))
  included_idx <- which(!excluded)

  if (length(included_idx) == 0) {
    return(result)
  }

  vals <- values[included_idx]
  if (all(is.na(vals))) {
    return(result)
  }

  if (higher_better) {
    vals[is.na(vals)] <- -Inf
    ranks <- match(vals, sort(unique(vals), decreasing = TRUE))
  } else {
    vals[is.na(vals)] <- Inf
    ranks <- match(vals, sort(unique(vals)))
  }

  result[included_idx] <- format_rank(ranks)
  result
}

rank_gap_table <- function(methods, gaps_df, real_gaps_df) {
  methods <- setdiff(methods, "Real")

  gap_cols <- names(gap_race_map)
  gap_labels <- c("Black-White", "Black-Hispanic", "Black-Asian",
                  "Hispanic-White", "Hispanic-Asian", "Asian-White")

  ranked_df <- tibble(Metric = gap_labels, group = "Racial Gaps (vs. Ground Truth)")
  for (m in methods) ranked_df[[m]] <- NA_character_

  for (j in seq_along(gap_cols)) {
    col <- gap_cols[j]
    real_val <- as.numeric(real_gaps_df[[col]])

    devs <- numeric(length(methods))
    for (k in seq_along(methods)) {
      method <- methods[k]
      devs[k] <- abs(get_metric_value(gaps_df, method, col) - real_val)
    }

    ranked <- rank_metric(devs, higher_better = FALSE)
    for (k in seq_along(methods)) {
      ranked_df[[methods[k]]][j] <- ranked[k]
    }
  }

  ranked_df
}

build_gt_table <- function(df, methods, title, subtitle, footnote) {
  tbl <- df %>%
    group_by(group) %>%
    gt(rowname_col = "Metric") %>%
    tab_header(
      title = md(title),
      subtitle = subtitle
    ) %>%
    tab_footnote(md(footnote)) %>%
    tab_options(
      table.font.names = c("Palatino", "serif"),
      table.font.size = px(14),
      heading.title.font.size = px(20),
      heading.subtitle.font.size = px(14),
      row_group.font.weight = "bold",
      column_labels.font.weight = "bold",
      table.width = pct(100)
    ) %>%
    cols_align(align = "center", columns = all_of(methods))

  for (col_name in methods) {
    for (row_idx in seq_len(nrow(df))) {
      cell_val <- df[[col_name]][row_idx]
      if (!is.na(cell_val) && grepl("^1($| )", cell_val)) {
        tbl <- tbl %>%
          tab_style(
            style = list(
              cell_fill(color = "#B2DFDB"),
              cell_text(weight = "bold")
            ),
            locations = cells_body(
              columns = !!sym(col_name), rows = row_idx
            )
          )
      }
    }
  }

  tbl
}

save_gt_png <- function(tbl, path) {
  if (!requireNamespace("webshot2", quietly = TRUE)) {
    warning("Skipping PNG export because the webshot2 package is not installed.")
    return(invisible(FALSE))
  }

  gtsave(tbl, path, expand = 10)
  cat("PNG saved to:", path, "\n")
  invisible(TRUE)
}

# --- Step 3: Rank F1 by race -------------------------------------------------

table_methods <- unique(c(METHODS, intersect(BIRDIE_METHODS, unique(gaps_raw$Method))))
birdie_methods <- intersect(table_methods, BIRDIE_METHODS)

display_race_cols <- setdiff(race_cols, "Other")

f1_race_mat <- matrix(NA, nrow = length(table_methods), ncol = length(race_cols),
                      dimnames = list(table_methods, race_cols))
for (k in seq_along(table_methods)) {
  for (rc in race_cols) f1_race_mat[k, rc] <- get_metric_value(f1_race, table_methods[k], rc)
}

f1_race_ranked <- tibble(Metric = display_race_cols, group = "F1 by Race")
for (m in table_methods) f1_race_ranked[[m]] <- NOT_APPLICABLE

for (j in seq_along(display_race_cols)) {
  rc <- display_race_cols[j]
  vals <- f1_race_mat[, rc]
  ranked <- rank_metric(vals, higher_better = TRUE, excluded = table_methods %in% birdie_methods)
  for (k in seq_along(table_methods)) {
    f1_race_ranked[[table_methods[k]]][j] <- ranked[k]
  }
}

# --- Step 4: Rank F1 aggregated -----------------------------------------------

agg_metrics <- c("Micro", "Macro", "Weighted")
f1_agg_mat <- matrix(NA, nrow = length(table_methods), ncol = length(agg_metrics),
                     dimnames = list(table_methods, agg_metrics))
for (k in seq_along(table_methods)) {
  for (am in agg_metrics) f1_agg_mat[k, am] <- get_metric_value(f1_agg, table_methods[k], am)
}

f1_agg_ranked <- tibble(Metric = paste("F1", agg_metrics), group = "F1 Aggregated")
for (m in table_methods) f1_agg_ranked[[m]] <- NOT_APPLICABLE

for (j in seq_along(agg_metrics)) {
  am <- agg_metrics[j]
  vals <- f1_agg_mat[, am]
  ranked <- rank_metric(vals, higher_better = TRUE, excluded = table_methods %in% birdie_methods)
  for (k in seq_along(table_methods)) {
    f1_agg_ranked[[table_methods[k]]][j] <- ranked[k]
  }
}

# --- Step 5: Rank racial gaps -------------------------------------------------

gap_methods <- table_methods
gap_ranked <- rank_gap_table(gap_methods, gaps_raw, real_gaps)

# --- Step 6: Rank population --------------------------------------------------

pop_metrics <- c("White", "Black", "Hispanic", "Asian", "Other")
display_pop_metrics <- setdiff(pop_metrics, "Other")
pop_labels <- c(paste("Pop:", display_pop_metrics), "Distance")

pop_ranked <- tibble(Metric = pop_labels, group = "Population Accuracy")
for (m in table_methods) pop_ranked[[m]] <- NOT_APPLICABLE

# Population percentages: closest to Real = best
for (j in seq_along(display_pop_metrics)) {
  race <- display_pop_metrics[j]
  real_val <- as.numeric(real_pop[[race]])

  devs <- numeric(length(table_methods))
  for (k in seq_along(table_methods)) {
    devs[k] <- abs(get_metric_value(pop, table_methods[k], race) - real_val)
  }
  ranked <- rank_metric(devs, higher_better = FALSE, excluded = table_methods %in% birdie_methods)
  for (k in seq_along(table_methods)) {
    pop_ranked[[table_methods[k]]][j] <- ranked[k]
  }
}

# Distance: lower is better, no exclusion
dist_vals <- numeric(length(table_methods))
for (k in seq_along(table_methods)) {
  dist_vals[k] <- get_metric_value(pop, table_methods[k], "Distance")
}
ranked <- rank_metric(dist_vals, higher_better = FALSE, excluded = table_methods %in% birdie_methods)
row_idx <- length(pop_labels) # last row = Distance
for (k in seq_along(table_methods)) {
  pop_ranked[[table_methods[k]]][row_idx] <- ranked[k]
}

# --- Step 7: Assemble ---------------------------------------------------------

result_df <- bind_rows(f1_race_ranked, f1_agg_ranked, gap_ranked, pop_ranked) %>%
  select(group, Metric, all_of(table_methods))

display_table_methods <- display_method_names(table_methods)
display_result_df <- result_df %>%
  rename_with(display_method_names, all_of(table_methods))

# --- Step 8a: Export as CSV ---------------------------------------------------

table_dir <- file.path(base_dir, "Results", "Table")
dir.create(table_dir, recursive = TRUE, showWarnings = FALSE)
out_csv <- file.path(table_dir, "07_rank_table_PPP.csv")
write_csv(display_result_df, out_csv)
cat("CSV saved to:", out_csv, "\n")

# --- Step 8b: Export as PNG via gt --------------------------------------------

figs_dir <- file.path(plots_dir, "Figs")
dir.create(figs_dir, recursive = TRUE, showWarnings = FALSE)

tbl <- build_gt_table(
  display_result_df,
  display_table_methods,
  "**Rank-Order of Approaches**",
  "PPP Sample",
  paste0(
    "Rank 1 = best. **F1**: highest value. ",
    "**Gaps**: closest to ground truth. ",
    "**Population**: closest to observed. ",
    "**Distance**: lowest. ",
    "Missing inputs are ranked last. ",
    "`--` = not ranked outside the racial gaps panel."
  )
)

out_png <- file.path(figs_dir, "07_rank_table_PPP.png")
save_gt_png(tbl, out_png)
