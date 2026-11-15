#!/usr/bin/env Rscript
# Draw a Kaplan-Meier curve for one feature in one cancer type / ancestry.
#
# Usage: Rscript survival.R <cancer> <ancestry> <feature> <tag> <HR> <FDR_HR> <n_high> <n_low> <out_dir> <data_dir>
# e.g.   Rscript survival.R BLCA eur ENSG00000227036 lncRNA 0.986 0.934 124 199 ./ ../static/ADTC/data
#
# Writes <out_dir>/survival.jpeg and <out_dir>/survival.pdf.

library(survival)
library(survminer)
options(stringsAsFactors = FALSE)

args <- commandArgs(TRUE)
cancertypes <- args[1]
race        <- args[2]
feature     <- args[3]
tag         <- args[4]
HR          <- args[5]
HR_p        <- args[6]
n1          <- args[7]   # size of the high group
n2          <- args[8]   # size of the low group
outdir      <- args[9]
datadir     <- args[10]

# Legend labels: low group first, matching the factor levels below.
group_names <- switch(tag,
  lncRNA  = c("Low", "High"),
  AS      = c("Low", "High"),
  APA     = c("Shortening", "Lengthening"),
  Editing = c("Underediting", "Overediting")
)
labs <- c(paste0(group_names[1], " (n = ", n2, ")"),
          paste0(group_names[2], " (n = ", n1, ")"))

# ---- Load data (provides `merge_data`) ----
load(file.path(datadir, paste(cancertypes, tag, "RData", sep = ".")))

# ---- Split samples into High / Low around the mean ----
data_select <- as.data.frame(merge_data[, c("barcode", "ancestry", "OS", "Status", feature)])
data_select <- dplyr::filter(data_select, ancestry == race)
data_select <- dplyr::filter(data_select, !is.na(.data[[feature]]))

value <- as.numeric(as.character(data_select[, feature]))
data_select$label <- ifelse(value >= mean(value), "High",
                            ifelse(value < mean(value), "Low", "NA"))
data_select <- dplyr::filter(data_select, label != "NA")
data_select$label <- factor(data_select$label, levels = c("Low", "High"))  # Low group as control
data_select <- dplyr::filter(data_select, !is.na(OS))

# ---- Fit and plot (OS is in days; plotted in months) ----
fit <- survfit(Surv(as.numeric(OS) / 30, as.numeric(Status)) ~ label,
               data = data_select, na.action = na.exclude)

p <- ggsurvplot(fit,
  fontsize       = 4,
  font.main      = c(16, "bold", "darkgreen"),
  font.x         = c(14, "bold.italic", "darkgreen"),
  font.y         = c(14, "bold.italic", "darkgreen"),
  font.tickslab  = c(12, "bold", "black"),
  font.legend    = list(size = 12, color = "black", face = "bold"),
  pval.size      = 8,
  pval           = FALSE,
  palette        = c("blue", "red"),
  conf.int       = TRUE,
  xlab           = "Survival months",
  legend.title   = "",
  title          = paste(feature, "in", cancertypes, sep = " "),
  legend.labs    = labs,
  risk.table     = FALSE,
  risk.table.col = "strata",  # risk table colour by group
  linetype       = "strata",  # line type by group
  ggtheme        = theme_bw() +
    theme(
      plot.title       = element_text(hjust = 0.5, vjust = 1),
      panel.background = element_rect(color = "black", size = 1),
      panel.grid.major = element_blank(),
      panel.grid.minor = element_blank()
    )
)

p$plot <- p$plot +
  ggplot2::annotate("text",
    x = 1, y = 0.25, vjust = 0.5, hjust = 0,
    label = paste0("HR = ", HR, "\n",
                   "FDR (HR) = ", signif(as.numeric(HR_p), 3), "\n"),
    size = 5, family = "Times", fontface = "bold.italic"
  )

# ---- Save ----
jpeg(file.path(outdir, "survival.jpeg"), width = 550, height = 550, units = "px",
     pointsize = 12, quality = 100, bg = "#e5ecff", res = 100)
print(p)
dev.off()

pdf(file.path(outdir, "survival.pdf"), width = 5.5, height = 5.5, onefile = FALSE)
print(p)
dev.off()
