# Phone Nexora - R analytics driver (Module 8)
# Run from the project root:  Rscript R/analysis.R
# Needs: dplyr, ggplot2, tidyr   (plotly optional, for interactive HTML charts)

suppressPackageStartupMessages({ library(dplyr); library(ggplot2); library(tidyr) })

# Allow `Rscript R/analysis.R` from any working directory.
file_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(file_arg)) {
  script_path <- normalizePath(sub("^--file=", "", file_arg[[1]]), mustWork = TRUE)
  setwd(dirname(dirname(script_path)))
}

OUT <- file.path("static", "r_output")
dir.create(OUT, recursive = TRUE, showWarnings = FALSE)

palette <- c(camera = "#E45D91", performance = "#536FD0", battery = "#20A486", storage = "#3998C7",
             display = "#E7A33E", software = "#D77D54", value = "#178F83")
rupee <- function(x) paste0("\u20b9", format(x, big.mark = ",", scientific = FALSE))

theme_spm <- function() {
  theme_minimal(base_size = 12) +
    theme(plot.title = element_text(face = "bold", color = "#19344c"),
          plot.subtitle = element_text(color = "#65798B"),
          axis.title = element_text(color = "#40566a"),
          panel.grid.minor = element_blank(), panel.grid.major = element_line(color = "#e5edf2"),
          legend.position = "bottom", plot.background = element_rect(fill = "white", color = NA))
}
save_plot <- function(p, name, w = 8, h = 5) {
  ggsave(file.path(OUT, paste0(name, ".png")), p, width = w, height = h, dpi = 150, bg = "white")
  if (requireNamespace("plotly", quietly = TRUE) && requireNamespace("htmlwidgets", quietly = TRUE)) {
    htmlwidgets::saveWidget(plotly::ggplotly(p), file.path(OUT, paste0(name, ".html")),
                            selfcontained = FALSE)
  }
}

phones <- read.csv("data/phones.csv", stringsAsFactors = FALSE)

# ---- specification vs price ---------------------------------------------------
scatter <- function(x, xlab, name) {
  p <- ggplot(phones, aes(x = .data[[x]], y = price)) +
    geom_point(aes(color = brand), size = 2.4, alpha = .8) +
    geom_smooth(method = "lm", se = FALSE, color = "#178F83", linewidth = 1) +
    scale_y_continuous(labels = rupee) +
    labs(title = paste(xlab, "vs indicative price"), subtitle = "Each point is one catalogue model", x = xlab, y = "Indicative price", color = "Brand") +
    theme_spm()
  save_plot(p, name)
}
scatter("camera_main", "Main camera (MP)", "spec_camera_vs_price")
scatter("battery", "Battery (mAh)", "spec_battery_vs_price")
scatter("benchmark", "Benchmark score (K)", "spec_performance_vs_price")
p_ram <- ggplot(phones, aes(x = factor(ram), y = price, fill = factor(ram))) +
  geom_boxplot(alpha = .85, show.legend = FALSE) + scale_y_continuous(labels = rupee) +
  scale_fill_manual(values = c("#FF4D8D", "#7A5CFF", "#19C37D", "#18A0FB", "#FFB020", "#FF7A3D")) +
  labs(title = "RAM vs price", x = "RAM (GB)", y = "Price") + theme_spm()
save_plot(p_ram, "spec_ram_vs_price")

source("R/price_analysis.R")
source("R/recommendation_analysis.R")
cat("R analysis finished. Charts are in", normalizePath(OUT), "\n")
