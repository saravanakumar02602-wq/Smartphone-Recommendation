# Recommendation analytics from the Python evaluation exports (uses variables from analysis.R)
# Create the exports first:  python -m analytics.evaluation

if (file.exists("data/eval_summary.csv") && file.exists("data/eval_recommendations.csv")) {
  summ <- read.csv("data/eval_summary.csv", stringsAsFactors = FALSE)
  recs <- read.csv("data/eval_recommendations.csv", stringsAsFactors = FALSE)

  # Preference distribution across the evaluation profiles
  w <- summ %>% select(profile, starts_with("w_")) %>%
    pivot_longer(-profile, names_to = "criterion", values_to = "weight") %>%
    mutate(criterion = sub("^w_", "", criterion))
  p_pref <- ggplot(w, aes(profile, weight, fill = criterion)) + geom_col(width = .75) +
    scale_fill_manual(values = palette) + coord_flip() +
    labs(title = "Preference weights by user profile", x = NULL, y = "Weight (%)", fill = NULL) + theme_spm()
  save_plot(p_pref, "reco_preference_distribution")

  # Personal score distribution
  p_score <- ggplot(recs, aes(profile, match, fill = profile)) +
    geom_boxplot(alpha = .85, show.legend = FALSE) + geom_jitter(width = .15, alpha = .5, show.legend = FALSE) +
    labs(title = "Personal match scores in each Top-10", x = NULL, y = "Match score (0-100)") +
    theme_spm() + theme(axis.text.x = element_text(angle = 20, hjust = 1))
  save_plot(p_score, "reco_score_distribution")

  # Recommendation consistency: dominant priority should score high in the Top-10
  long <- recs %>% pivot_longer(starts_with("s_"), names_to = "criterion", values_to = "score") %>%
    mutate(criterion = sub("^s_", "", criterion))
  avg <- long %>% group_by(profile, criterion) %>% summarise(score = mean(score), .groups = "drop")
  p_heat <- ggplot(avg, aes(criterion, profile, fill = score)) + geom_tile(color = "white") +
    geom_text(aes(label = round(score)), color = "white", fontface = "bold") +
    scale_fill_gradient(low = "#DCE8EF", high = "#3157D5") +
    labs(title = "Average criterion score of each Top-10", subtitle = "Each profile's top priorities should be the darkest tiles",
         x = NULL, y = NULL, fill = "Score") + theme_spm()
  save_plot(p_heat, "reco_consistency_heatmap")

  # Price vs match
  p_pm <- ggplot(recs, aes(price, match, color = profile)) + geom_point(size = 2.5, alpha = .85) +
    scale_x_continuous(labels = rupee) +
    labs(title = "Recommended phones: price vs match", x = "Price", y = "Match score", color = NULL) + theme_spm()
  save_plot(p_pm, "reco_price_vs_match")

  # Constraint compliance, priority consistency, and explanation quality by profile.
  checks <- summ %>% transmute(
    profile,
    `Constraint compliance` = ifelse(top_n > 0, pmax(0, (top_n - constraint_violations) / top_n * 100), 100),
    `Priority consistency` = priority_consistent * 100,
    `Explanation accuracy` = explanation_accuracy * 100
  ) %>% pivot_longer(-profile, names_to = "check", values_to = "percent")
  p_checks <- ggplot(checks, aes(profile, percent, fill = check)) +
    geom_col(position = position_dodge(width = .78), width = .7) +
    scale_fill_manual(values = c("Constraint compliance" = "#20A486", "Priority consistency" = "#536FD0",
                                 "Explanation accuracy" = "#E7A33E")) +
    coord_cartesian(ylim = c(0, 100)) +
    labs(title = "Recommendation quality checks", x = NULL, y = "Passed (%)", fill = NULL) +
    theme_spm() + theme(axis.text.x = element_text(angle = 20, hjust = 1))
  save_plot(p_checks, "reco_quality_checks", 9, 5)

  p_runtime <- ggplot(summ, aes(reorder(profile, avg_response_ms), avg_response_ms)) +
    geom_col(fill = "#178F83", width = .72) + coord_flip() +
    labs(title = "Evaluation time by profile", x = NULL, y = "Average response time (ms)") + theme_spm()
  save_plot(p_runtime, "reco_response_time")
} else {
  message("Evaluation exports not found. Run: python -m analytics.evaluation")
}
