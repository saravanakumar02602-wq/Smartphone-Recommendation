# Price distribution, brand comparison, and price trends (uses variables from analysis.R)

p_hist <- ggplot(phones, aes(price)) +
  geom_histogram(bins = 15, fill = "#536FD0", color = "white") +
  scale_x_continuous(labels = rupee) +
  labs(title = "Indicative price distribution", subtitle = paste(nrow(phones), "India-market models"), x = "Indicative price", y = "Models") +
  theme_spm()
save_plot(p_hist, "price_distribution")

p_brand <- ggplot(phones, aes(x = reorder(brand, price, median), y = price, fill = brand)) +
  geom_boxplot(alpha = .85, show.legend = FALSE) + coord_flip() + scale_y_continuous(labels = rupee) +
  labs(title = "Indicative price range by brand", x = NULL, y = "Indicative price") + theme_spm()
save_plot(p_brand, "price_by_brand")

hist <- read.csv("data/price_history.csv", stringsAsFactors = FALSE)
if (nrow(hist) && all(c("recorded_date", "price") %in% names(hist))) {
  hist$recorded_date <- as.Date(hist$recorded_date)
  trend <- hist %>% group_by(recorded_date) %>% summarise(avg_price = mean(price), .groups = "drop")
  p_trend <- ggplot(trend, aes(recorded_date, avg_price)) +
    geom_line(color = "#178F83", linewidth = 1.2) + geom_point(color = "#3157D5", size = 2.5) +
    scale_y_continuous(labels = rupee) +
    labs(title = "Recorded price history", subtitle = "Historical observations only; no forecast", x = NULL, y = "Average recorded price") +
    theme_spm()
} else {
  p_trend <- ggplot() +
    annotate("text", x = 0, y = 0, label = "No verified historical price observations are available yet.") +
    labs(title = "Recorded price history", subtitle = "A live authorized price feed is needed to populate this chart.", x = NULL, y = NULL) +
    theme_spm() + theme(axis.text = element_blank(), axis.ticks = element_blank(), panel.grid = element_blank())
}
save_plot(p_trend, "price_trend")

if (nrow(hist) && all(c("phone_id", "recorded_date", "price") %in% names(hist))) {
  drops <- hist %>% arrange(phone_id, recorded_date) %>% group_by(phone_id) %>%
    summarise(first = first(price), latest = last(price), drop = first - latest,
              drop_pct = round((first - latest) / first * 100, 1), .groups = "drop") %>%
    left_join(phones[, c("id", "brand", "model")], by = c("phone_id" = "id")) %>%
    arrange(desc(drop_pct)) %>% head(15)
} else {
  drops <- data.frame(phone_id = integer(), first = numeric(), latest = numeric(), drop = numeric(),
                      drop_pct = numeric(), brand = character(), model = character())
}
write.csv(drops, file.path(OUT, "price_drops.csv"), row.names = FALSE)
