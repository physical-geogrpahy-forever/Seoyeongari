# ============================================================
# Distance vs Age plot
# - 1000 dpi TIFF
# - width = 5000 px
# - height = previous height x 1.5
# - Font changed to Arial-like sans-serif
# - 점/삼각형이 축 경계에서 잘리지 않도록 x/y 범위 확장
# ============================================================

# 0) Packages -------------------------------------------------
if (!requireNamespace("ggplot2", quietly = TRUE)) install.packages("ggplot2")
if (!requireNamespace("ragg", quietly = TRUE)) install.packages("ragg")

suppressPackageStartupMessages(library(ggplot2))

# 1) Data -----------------------------------------------------
df <- data.frame(
  ID  = c("A1", "A2", "A3", "B1", "B2", "B3"),
  dis = c(2, 6.6, 12.3, 0.5, 3.7, 12),
  age = c(10, 12, 27, 8, 11, 29)
)

df$group <- substr(df$ID, 1, 1)

# 2) Export size setting --------------------------------------
# width 5 inch * 1000 dpi = 5000 px
# height는 기존 높이의 1.5배
fig_width_in  <- 5.0
fig_height_in <- 5.0 * 850 / 1307 * 1.5

# 3) Font setting ---------------------------------------------
# 첨부 그림과 유사한 산세리프체
# Windows에서는 Arial 사용 가능
font_family <- "Arial"

# 만약 Arial이 깨지거나 적용되지 않으면 아래처럼 바꿔도 됩니다.
# font_family <- "sans"

# 4) Plot -----------------------------------------------------
p <- ggplot(df, aes(x = dis, y = age)) +
  
  geom_line(
    aes(group = group),
    linewidth = 1.15,
    color = "#4A78C2"
  ) +
  
  geom_point(
    aes(shape = group),
    size = 5.2,
    stroke = 0.9,
    color = "black"
  ) +
  
  scale_shape_manual(
    values = c("A" = 16, "B" = 17),
    labels = c("A", "B")
  ) +
  
  scale_x_continuous(
    limits = c(0, 13),
    breaks = seq(0, 12.5, by = 2.5),
    expand = expansion(mult = c(0, 0))
  ) +
  
  scale_y_continuous(
    limits = c(7, 31),
    breaks = seq(10, 30, by = 5),
    expand = expansion(mult = c(0, 0))
  ) +
  
  labs(
    x = "Distance to the pond (m)",
    y = "Age (years)"
  ) +
  
  theme_classic(
    base_size = 18,
    base_family = font_family
  ) +
  
  theme(
    text = element_text(
      family = font_family,
      color = "black"
    ),
    
    panel.border = element_rect(
      color = "black",
      fill = NA,
      linewidth = 0.85
    ),
    
    axis.line = element_line(
      color = "black",
      linewidth = 0.65
    ),
    
    axis.ticks = element_line(
      color = "black",
      linewidth = 0.65
    ),
    
    axis.ticks.length = unit(0.20, "cm"),
    
    axis.title.x = element_text(
      family = font_family,
      size = 19,
      color = "black",
      margin = margin(t = 10)
    ),
    
    axis.title.y = element_text(
      family = font_family,
      size = 19,
      color = "black",
      margin = margin(r = 10)
    ),
    
    axis.text.x = element_text(
      family = font_family,
      size = 17,
      color = "black"
    ),
    
    axis.text.y = element_text(
      family = font_family,
      size = 17,
      color = "black"
    ),
    
    legend.title = element_blank(),
    
    legend.text = element_text(
      family = font_family,
      size = 17,
      color = "black"
    ),
    
    legend.position = "bottom",
    legend.direction = "horizontal",
    
    legend.key = element_blank(),
    legend.key.width = unit(1.0, "cm"),
    legend.key.height = unit(0.45, "cm"),
    
    legend.background = element_rect(
      color = "black",
      fill = "white",
      linewidth = 0.6
    ),
    
    legend.box.background = element_rect(
      color = "black",
      fill = NA,
      linewidth = 0.6
    ),
    
    plot.margin = margin(
      t = 15,
      r = 15,
      b = 15,
      l = 15
    ),
    
    panel.grid = element_blank()
  ) +
  
  guides(
    shape = guide_legend(
      override.aes = list(
        size = 5.2,
        stroke = 0.9
      )
    )
  )

# 5) Print ----------------------------------------------------
print(p)

# 6) Save as 1000 dpi TIFF ------------------------------------
ggsave(
  filename = "distance_age_plot_1000dpi_no_clipping_height_1p5x_arial.tif",
  plot = p,
  device = ragg::agg_tiff,
  width = fig_width_in,
  height = fig_height_in,
  units = "in",
  dpi = 1000,
  compression = "lzw",
  background = "white"
)





# ============================================================
# FULL CODE — Core-wise example-style boxplot (NO clustering)
# Export:
# - TIFF
# - 1000 dpi
# - Full-page-width line drawing 기준 충족
# - width ≈ 7500 px, height ≈ 3125 px
# - 글자 크기, 선 굵기, 점 크기 비율 유지
# ============================================================

# ============================================================
# 0) Packages
# ============================================================
if (!requireNamespace("dplyr", quietly = TRUE)) install.packages("dplyr")
if (!requireNamespace("ggplot2", quietly = TRUE)) install.packages("ggplot2")
if (!requireNamespace("ragg", quietly = TRUE)) install.packages("ragg")

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
})

# ============================================================
# 1) Data input
# ============================================================
df <- data.frame(
  코어 = c(
    1,1,1,1,1,1,1,1, 2,2,2,2,2,2,2,2, 3,3,3,3,3,3,3,3,
    4,4,4,4, 5,5,5,5,5,5,5,5, 6,6,6,6,6,6,6,6,
    7,7,7,7,7,7,7,7, 8,8,8,8,8,8,8,8, 9,9,9,9,9,9,9,9,
    10,10,10,10,10,10,10,10, 11,11,11,11,11,11,11,11,
    12,12,12, 13,13,13,13,13,13,13,13,13,
    14,14,14,14, 15,15,15,15,15,15, 16,16,
    17,17,17, 18,18,18,18,18,18, 19,19,19
  ),
  유기물함량 = c(
    0.4365, 0.4170, 0.4131, 0.4419, 0.4281, 0.4352, 0.3874, 0.4080,
    0.5017, 0.4219, 0.4268, 0.3849, 0.4507, 0.4396, 0.4932, 0.4228,
    0.4088, 0.3400, 0.3232, 0.3920, 0.3758, 0.3792, 0.3767, 0.3500,
    0.3846, 0.3510, 0.3581, 0.3256,
    0.4700, 0.4784, 0.4899, 0.5084, 0.5485, 0.5150, 0.5150, 0.5101,
    0.4950, 0.5033, 0.5182, 0.5733, 0.5418, 0.5233, 0.5017, 0.5367,
    0.5385, 0.5024, 0.4596, 0.7437, 0.5124, 0.4916, 0.4181, 0.5200,
    0.5110, 0.5199, 0.5604, 0.5926, 0.5625, 0.5400, 0.5183, 0.5433,
    0.5567, 0.5839, 0.6346, 0.5852, 0.6447, 0.6258, 0.6431, 0.5515,
    0.6667, 0.6254, 0.6458, 0.6656, 0.5987, 0.5842, 0.6192, 0.6601,
    0.4818, 0.4799, 0.4834, 0.6258, 0.6238, 0.6349, 0.5518, 0.5470,
    0.4765, 0.4718, 0.4800,
    0.4539, 0.5300, 0.5855, 0.5449, 0.6433, 0.7384, 0.7303, 0.6567, 0.6711,
    0.5249, 0.5083, 0.5728, 0.6601,
    0.5000, 0.4112, 0.4603, 0.4356, 0.4186, 0.4073,
    0.5033, 0.5385,
    0.4035, 0.6458, 0.6611,
    0.7000, 0.5946, 0.6391, 0.5629, 0.6238, 0.7000,
    0.5300, 0.5122, 0.5049
  )
)

# ============================================================
# 2) Convert to content (%) and factor
# ============================================================
df <- df %>%
  mutate(
    유기물함량 = 유기물함량 * 100,
    코어 = factor(코어, levels = as.character(1:19))
  )

# ============================================================
# 3) Example-style box stats: 10/25/50/75/90 percentiles
# ============================================================
box_df_core <- df %>%
  group_by(코어) %>%
  summarise(
    ymin   = as.numeric(quantile(유기물함량, 0.10, na.rm = TRUE)),
    lower  = as.numeric(quantile(유기물함량, 0.25, na.rm = TRUE)),
    middle = as.numeric(quantile(유기물함량, 0.50, na.rm = TRUE)),
    upper  = as.numeric(quantile(유기물함량, 0.75, na.rm = TRUE)),
    ymax   = as.numeric(quantile(유기물함량, 0.90, na.rm = TRUE)),
    .groups = "drop"
  )

# ============================================================
# 4) Export size and figure-element settings
# ============================================================
# Full-page-width line drawing 기준:
# 1000 dpi에서 가로 7.5 inch = 7500 px
# 출판사 기준 full page width 최소 7480 px 충족
fig_width_in  <- 7.5
fig_height_in <- 3.125
fig_dpi       <- 1000

# 글자와 그래프 요소는 inch 단위 출력 크기에 맞춰 조정
base_size     <- 12
axis_title_sz <- 17
axis_text_sz  <- 13

box_line_w    <- 0.45
border_line_w <- 0.65
tick_line_w   <- 0.45
grid_line_w   <- 0.35

point_size    <- 1.7
point_alpha   <- 0.45
box_width     <- 0.55

# ============================================================
# 5) Plot
# ============================================================
p_core_no_cluster <- ggplot() +
  
  geom_boxplot(
    data = box_df_core,
    aes(
      x = 코어,
      ymin = ymin,
      lower = lower,
      middle = middle,
      upper = upper,
      ymax = ymax
    ),
    stat = "identity",
    width = box_width,
    alpha = 0.9,
    fill = "grey75",
    color = "black",
    linewidth = box_line_w
  ) +
  
  geom_point(
    data = df,
    aes(x = 코어, y = 유기물함량),
    position = position_jitter(width = 0.10, height = 0),
    size = point_size,
    alpha = point_alpha,
    color = "black"
  ) +
  
  scale_x_discrete(
    expand = expansion(add = 0.7)
  ) +
  
  scale_y_continuous(
    limits = c(30, 78),
    breaks = seq(30, 75, by = 5),
    expand = expansion(mult = c(0, 0.03))
  ) +
  
  labs(
    x = "Sampling points",
    y = "Organic matter content (%)"
  ) +
  
  coord_cartesian(clip = "off") +
  
  theme_classic(
    base_size = base_size,
    base_family = "Times New Roman"
  ) +
  
  theme(
    plot.title = element_blank(),
    legend.position = "none",
    
    panel.border = element_rect(
      color = "black",
      fill = NA,
      linewidth = border_line_w
    ),
    
    axis.line = element_line(
      color = "black",
      linewidth = tick_line_w
    ),
    
    axis.ticks = element_line(
      color = "black",
      linewidth = tick_line_w
    ),
    
    axis.ticks.length = unit(0.16, "cm"),
    
    panel.grid.major.y = element_line(
      color = "grey80",
      linewidth = grid_line_w
    ),
    
    panel.grid.minor.y = element_blank(),
    panel.grid.major.x = element_blank(),
    panel.grid.minor.x = element_blank(),
    
    axis.title.x = element_text(
      size = axis_title_sz,
      margin = margin(t = 10),
      color = "black"
    ),
    
    axis.title.y = element_text(
      size = axis_title_sz,
      margin = margin(r = 10),
      color = "black"
    ),
    
    axis.text.x = element_text(
      size = axis_text_sz,
      color = "black"
    ),
    
    axis.text.y = element_text(
      size = axis_text_sz,
      color = "black"
    ),
    
    plot.margin = margin(
      t = 12,
      r = 16,
      b = 12,
      l = 16
    )
  )

# ============================================================
# 6) Print
# ============================================================
print(p_core_no_cluster)

# ============================================================
# 7) Save as 1000 dpi TIFF
# ============================================================
ggsave(
  filename = "om_boxplot_core_no_cluster_percent_1000dpi.tif",
  plot = p_core_no_cluster,
  device = ragg::agg_tiff,
  width = fig_width_in,
  height = fig_height_in,
  units = "in",
  dpi = fig_dpi,
  compression = "lzw",
  background = "white"
)







# ============================================================
# FULL CODE — Vertical profile of organic matter content by core
# - Facet version
# - y-axis depth labels shown every 20 cm
# - CV added to each facet strip
# - TIFF export at 1000 dpi
# - Font changed to Arial-like sans-serif
# ============================================================

# ============================================================
# 0) Packages
# ============================================================
if (!requireNamespace("dplyr", quietly = TRUE)) install.packages("dplyr")
if (!requireNamespace("ggplot2", quietly = TRUE)) install.packages("ggplot2")
if (!requireNamespace("ragg", quietly = TRUE)) install.packages("ragg")

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
})

# ============================================================
# 1) Data input
# ============================================================
df <- data.frame(
  core = c(
    1,1,1,1,1,1,1,1, 2,2,2,2,2,2,2,2, 3,3,3,3,3,3,3,3,
    4,4,4,4, 5,5,5,5,5,5,5,5, 6,6,6,6,6,6,6,6,
    7,7,7,7,7,7,7,7, 8,8,8,8,8,8,8,8, 9,9,9,9,9,9,9,9,
    10,10,10,10,10,10,10,10, 11,11,11,11,11,11,11,11,
    12,12,12, 13,13,13,13,13,13,13,13,13,
    14,14,14,14, 15,15,15,15,15,15, 16,16,
    17,17,17, 18,18,18,18,18,18, 19,19,19
  ),
  om_frac = c(
    0.4365, 0.4170, 0.4131, 0.4419, 0.4281, 0.4352, 0.3874, 0.4080,
    0.5017, 0.4219, 0.4268, 0.3849, 0.4507, 0.4396, 0.4932, 0.4228,
    0.4088, 0.3400, 0.3232, 0.3920, 0.3758, 0.3792, 0.3767, 0.3500,
    0.3846, 0.3510, 0.3581, 0.3256,
    0.4700, 0.4784, 0.4899, 0.5084, 0.5485, 0.5150, 0.5150, 0.5101,
    0.4950, 0.5033, 0.5182, 0.5733, 0.5418, 0.5233, 0.5017, 0.5367,
    0.5385, 0.5024, 0.4596, 0.7437, 0.5124, 0.4916, 0.4181, 0.5200,
    0.5110, 0.5199, 0.5604, 0.5926, 0.5625, 0.5400, 0.5183, 0.5433,
    0.5567, 0.5839, 0.6346, 0.5852, 0.6447, 0.6258, 0.6431, 0.5515,
    0.6667, 0.6254, 0.6458, 0.6656, 0.5987, 0.5842, 0.6192, 0.6601,
    0.4818, 0.4799, 0.4834, 0.6258, 0.6238, 0.6349, 0.5518, 0.5470,
    0.4765, 0.4718, 0.4800,
    0.4539, 0.5300, 0.5855, 0.5449, 0.6433, 0.7384, 0.7303, 0.6567, 0.6711,
    0.5249, 0.5083, 0.5728, 0.6601,
    0.5000, 0.4112, 0.4603, 0.4356, 0.4186, 0.4073,
    0.5033, 0.5385,
    0.4035, 0.6458, 0.6611,
    0.7000, 0.5946, 0.6391, 0.5629, 0.6238, 0.7000,
    0.5300, 0.5122, 0.5049
  )
)

# ============================================================
# 2) Convert organic matter to percent and assign depth
# ============================================================
depth_interval_cm <- 10

df <- df %>%
  group_by(core) %>%
  mutate(
    sample_order = row_number(),
    depth_cm = (sample_order - 1) * depth_interval_cm + depth_interval_cm / 2,
    om_percent = om_frac * 100
  ) %>%
  ungroup()

# ============================================================
# 3) Calculate CV by core
# ============================================================
cv_df <- df %>%
  group_by(core) %>%
  summarise(
    n = n(),
    mean_om = mean(om_percent, na.rm = TRUE),
    sd_om = sd(om_percent, na.rm = TRUE),
    cv_percent = sd_om / mean_om * 100,
    .groups = "drop"
  ) %>%
  mutate(
    facet_label = paste0(core, "\nCV=", sprintf("%.1f", cv_percent), "%")
  )

print(cv_df)

# ============================================================
# 4) Join CV label to main data
# ============================================================
df <- df %>%
  left_join(
    cv_df %>% select(core, cv_percent, facet_label),
    by = "core"
  ) %>%
  mutate(
    core = factor(core, levels = 1:19),
    facet_label = factor(
      facet_label,
      levels = cv_df$facet_label[order(cv_df$core)]
    )
  ) %>%
  arrange(core, depth_cm)

# ============================================================
# 5) Axis limits
# ============================================================
x_min <- floor(min(df$om_percent, na.rm = TRUE) / 5) * 5
x_max <- ceiling(max(df$om_percent, na.rm = TRUE) / 5) * 5

y_max <- ceiling(max(df$depth_cm, na.rm = TRUE) / 10) * 10
y_breaks <- seq(0, y_max, by = 20)

# ============================================================
# 6) Figure settings
# ============================================================
fig_width_in  <- 7.5
fig_height_in <- 6.2
fig_dpi       <- 1000

# 첨부 예시와 유사한 산세리프체
font_family <- "Arial"

# Arial이 적용되지 않으면 아래 한 줄로 교체
# font_family <- "sans"

base_size      <- 11
strip_text_sz  <- 10.5
axis_title_sz  <- 18
axis_text_sz   <- 12.5

line_w         <- 0.45
point_size     <- 1.8
panel_border_w <- 0.45
grid_line_w    <- 0.25

# ============================================================
# 7) Plot
# ============================================================
p_profile_cv <- ggplot(df, aes(x = om_percent, y = depth_cm)) +
  
  geom_path(
    linewidth = line_w,
    color = "black"
  ) +
  
  geom_point(
    size = point_size,
    color = "black",
    alpha = 0.9
  ) +
  
  facet_wrap(
    ~ facet_label,
    ncol = 5
  ) +
  
  scale_x_continuous(
    limits = c(x_min, x_max),
    breaks = seq(x_min, x_max, by = 10),
    expand = expansion(mult = c(0.03, 0.03))
  ) +
  
  scale_y_reverse(
    limits = c(y_max, 0),
    breaks = y_breaks,
    expand = expansion(mult = c(0.02, 0.02))
  ) +
  
  labs(
    x = "Organic matter content (%)",
    y = "Depth (cm)"
  ) +
  
  theme_bw(
    base_size = base_size,
    base_family = font_family
  ) +
  
  theme(
    text = element_text(
      family = font_family,
      color = "black"
    ),
    
    plot.title = element_blank(),
    legend.position = "none",
    
    panel.border = element_rect(
      color = "black",
      fill = NA,
      linewidth = panel_border_w
    ),
    
    panel.grid.major.y = element_line(
      color = "grey85",
      linewidth = grid_line_w
    ),
    panel.grid.major.x = element_line(
      color = "grey90",
      linewidth = grid_line_w
    ),
    panel.grid.minor = element_blank(),
    
    axis.title.x = element_text(
      family = font_family,
      size = axis_title_sz,
      margin = margin(t = 12),
      color = "black"
    ),
    axis.title.y = element_text(
      family = font_family,
      size = axis_title_sz,
      margin = margin(r = 12),
      color = "black"
    ),
    
    axis.text.x = element_text(
      family = font_family,
      size = axis_text_sz,
      color = "black"
    ),
    axis.text.y = element_text(
      family = font_family,
      size = axis_text_sz,
      color = "black"
    ),
    
    axis.ticks = element_line(
      linewidth = 0.35,
      color = "black"
    ),
    axis.ticks.length = unit(0.14, "cm"),
    
    strip.background = element_rect(
      fill = "grey90",
      color = "black",
      linewidth = 0.35
    ),
    strip.text = element_text(
      family = font_family,
      size = strip_text_sz,
      face = "bold",
      color = "black",
      lineheight = 0.95
    ),
    
    panel.spacing = unit(0.18, "cm"),
    
    plot.margin = margin(
      t = 10,
      r = 12,
      b = 10,
      l = 12
    )
  )

# ============================================================
# 8) Print
# ============================================================
print(p_profile_cv)

# ============================================================
# 9) Save as TIFF, 1000 dpi
# ============================================================
ggsave(
  filename = "organic_matter_vertical_profiles_by_core_cv_1000dpi_arial.tif",
  plot = p_profile_cv,
  device = ragg::agg_tiff,
  width = fig_width_in,
  height = fig_height_in,
  units = "in",
  dpi = fig_dpi,
  compression = "lzw",
  background = "white"
)










# ============================================================
# Area time-series plot (line + points)
# - TIFF 1000 dpi export
# - 각 점 옆 면적값 숫자 표시 제거
# - Arial font forcibly registered from Windows font file
# ============================================================

# 0) Packages -------------------------------------------------
pkgs <- c("ggplot2", "dplyr", "ragg", "systemfonts")

for (p in pkgs) {
  if (!requireNamespace(p, quietly = TRUE)) install.packages(p)
}

suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
  library(systemfonts)
})

# 0-1) Force-register Arial font ------------------------------
# Windows Arial font files
arial_plain_candidates <- c(
  "C:/Windows/Fonts/arial.ttf",
  "C:/Windows/Fonts/Arial.ttf"
)

arial_bold_candidates <- c(
  "C:/Windows/Fonts/arialbd.ttf",
  "C:/Windows/Fonts/Arialbd.ttf",
  "C:/Windows/Fonts/ARIALBD.TTF"
)

arial_italic_candidates <- c(
  "C:/Windows/Fonts/ariali.ttf",
  "C:/Windows/Fonts/Ariali.ttf",
  "C:/Windows/Fonts/ARIALI.TTF"
)

arial_bolditalic_candidates <- c(
  "C:/Windows/Fonts/arialbi.ttf",
  "C:/Windows/Fonts/Arialbi.ttf",
  "C:/Windows/Fonts/ARIALBI.TTF"
)

pick_font_file <- function(candidates, label) {
  hit <- candidates[file.exists(candidates)]
  if (length(hit) == 0) {
    stop(
      "Arial font file not found for: ", label, "\n",
      "Tried:\n",
      paste(candidates, collapse = "\n")
    )
  }
  hit[1]
}

arial_plain      <- pick_font_file(arial_plain_candidates, "plain")
arial_bold       <- pick_font_file(arial_bold_candidates, "bold")
arial_italic     <- pick_font_file(arial_italic_candidates, "italic")
arial_bolditalic <- pick_font_file(arial_bolditalic_candidates, "bold italic")

systemfonts::register_font(
  name = "ArialForced",
  plain = arial_plain,
  bold = arial_bold,
  italic = arial_italic,
  bolditalic = arial_bolditalic
)

font_family <- "ArialForced"

# 확인용 출력
print(systemfonts::match_font(font_family))

# 1) Input data ------------------------------------------------
df <- data.frame(
  year = c(2011, 2013, 2015, 2017, 2019, 2021, 2023),
  area = c(2242.974, 2154.43, 2147.678, 2051.218, 2045.159, 1965.256, 1882.7)
) %>%
  arrange(year)

# 2) Output settings ------------------------------------------
out_tif <- "area_timeseries_1000dpi_ARIAL_FORCED.tif"

fig_width_in  <- 6.2
fig_height_in <- 4.7
fig_dpi       <- 1000

base_size      <- 16
axis_title_sz  <- 18
axis_text_sz   <- 18

line_width     <- 1.1
point_size     <- 5
point_stroke   <- 0.6

# 3) Build plot ------------------------------------------------
p <- ggplot(df, aes(x = year, y = area)) +
  geom_line(
    color = "black",
    linewidth = line_width
  ) +
  geom_point(
    shape = 21,
    fill = "black",
    color = "black",
    size = point_size,
    stroke = point_stroke
  ) +
  scale_x_continuous(
    breaks = df$year,
    limits = c(2010.5, 2024.3),
    expand = expansion(mult = c(0, 0))
  ) +
  scale_y_continuous(
    limits = c(1850, 2275),
    breaks = seq(1900, 2250, by = 100),
    expand = expansion(mult = c(0, 0))
  ) +
  labs(
    x = "Year",
    y = "Area (m²)"
  ) +
  theme_bw(
    base_size = base_size,
    base_family = font_family
  ) +
  theme(
    text = element_text(
      family = font_family,
      color = "black"
    ),
    
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    
    axis.title.x = element_text(
      family = font_family,
      size = axis_title_sz,
      margin = margin(t = 10),
      color = "black"
    ),
    axis.title.y = element_text(
      family = font_family,
      size = axis_title_sz,
      margin = margin(r = 10),
      color = "black"
    ),
    
    axis.text.x = element_text(
      family = font_family,
      size = axis_text_sz,
      color = "black"
    ),
    axis.text.y = element_text(
      family = font_family,
      size = axis_text_sz,
      color = "black"
    ),
    
    axis.ticks = element_line(
      linewidth = 0.5,
      color = "black"
    ),
    
    plot.margin = margin(
      t = 12,
      r = 28,
      b = 12,
      l = 12
    )
  )

# 4) Print -----------------------------------------------------
print(p)

# 5) Save as TIFF, 1000 dpi -----------------------------------
# ggsave 대신 ragg 장치를 직접 열어서 저장
ragg::agg_tiff(
  filename = out_tif,
  width = fig_width_in,
  height = fig_height_in,
  units = "in",
  res = fig_dpi,
  compression = "lzw",
  background = "white"
)

print(p)
dev.off()

message(
  "\nSaved TIFF file:\n",
  normalizePath(out_tif, winslash = "/", mustWork = FALSE),
  "\n"
)







# ============================================================
# V5 shared-relax pond water-balance model
# - R driver + Python/NumPy/Rasterio watershed calculation
# - NO grid search: fixed final parameters from Python v5
# - Watershed area is recalculated from DEM + 2011 pond polygon
# - Annual forcing is recalculated from AWS/ASOS using the Python v5 formulas
# - Simplified FAO-56 dual crop coefficient representation for riparian ET
# - Shared relaxation coefficient for water-depth and bottom-rise adjustment
# - Final plot exported as TIFF, 1000 dpi
# ============================================================

# -----------------------------
# 0. R packages
# -----------------------------
r_pkgs <- c("reticulate", "ggplot2", "dplyr", "readr", "ragg")

for (p in r_pkgs) {
  if (!requireNamespace(p, quietly = TRUE)) install.packages(p)
}

suppressPackageStartupMessages({
  library(reticulate)
  library(ggplot2)
  library(dplyr)
  library(readr)
  library(ragg)
})

# -----------------------------
# 1. User paths: keep original Windows data locations
# -----------------------------
dem_path  <- "C:/Users/ASUS/Desktop/Eco-Geo-Hydro/데이터/dem.tif"
pond_path <- "C:/Users/ASUS/Desktop/학사졸업논문/산림 졸논/data/plot_2011.shp"
aws_path  <- "C:/Users/ASUS/Desktop/Eco-Geo-Hydro/데이터/OBS_AWS_DD_20250930013603.csv"
asos_path <- "C:/Users/ASUS/Desktop/Eco-Geo-Hydro/데이터/OBS_ASOS_DD_20250930041037.csv"

out_dir <- file.path(dirname(aws_path), "veslem_v5_bottomrelax_outputs")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# -----------------------------
# 2. Python package check / install
# -----------------------------
ensure_py_pkg <- function(pkg) {
  ok <- py_module_available(pkg)
  if (!ok) {
    message("Installing missing Python package: ", pkg)
    reticulate::py_install(pkg, pip = TRUE)
  }
}

ensure_py_pkg("numpy")
ensure_py_pkg("pandas")
ensure_py_pkg("rasterio")
ensure_py_pkg("geopandas")
ensure_py_pkg("shapely")

# -----------------------------
# 3. Python model code
# -----------------------------
py_code <- r"(
import os, math, heapq
from collections import deque
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import rasterize

# -----------------------------
# Constants exactly following the Python v5 logic
# -----------------------------
lat_deg = 33.30456
alt_m = 188.42
a_s = 0.25
b_s = 0.50
wind_height_m = 2
alpha_veg = 0.23
alpha_water = 0.08
f_ET_reduction = 0.20
I_P = 0.13
I_C = 0.0
# Simplified FAO-56 dual crop coefficient representation
# ET_R,i = (K_cb,i + K_e,i) * ETo
# Forest and grassland are assumed to be fully covered by vegetation,
# so soil evaporation coefficients are set to zero.
# Bare ground is assumed to have no basal transpiration; its evaporative
# contribution is represented by K_e_bare.
K_cb_forest = 0.95
K_e_forest  = 0.00
K_cb_grass  = 0.90
K_e_grass   = 0.00
K_cb_bare   = 0.00
K_e_bare    = 0.30
cn_val = 68
S_mm = 25400.0 / cn_val - 254.0
Ia_mm = 0.2 * S_mm
f_QS = 0.01
h_init = 1.2
h_base = h_init
bottom_rise = 0.003
damping_factor = 0.7

# fixed final parameter set from v5 shared-relax Python code
FINAL_BUFFER_WIDTH_M = 17.5
FINAL_RELAX = 0.035
FINAL_SCALE_RELAX = FINAL_RELAX
FINAL_ALPHA_SHAPE = 1.3
FINAL_BOTTOM_RELAX = FINAL_RELAX

plot_years = np.array([2011, 2013, 2015, 2017, 2019, 2021, 2023], dtype=int)
obs_y = np.array([2242.974, 2154.43, 2147.678, 2051.218, 2045.159, 1965.256, 1882.7], dtype=float)
obs_diff = np.diff(obs_y)


def e0(Tc):
    return 0.6108 * np.exp(17.27 * Tc / (Tc + 237.3))


def delta_fun(Tc):
    return 4098 * e0(Tc) / (Tc + 237.3) ** 2


def P_kPa(z):
    return 101.3 * ((293 - 0.0065 * z) / 293) ** 5.26


def u2_from_uz(u_z, z_m):
    return np.where(z_m > 0, u_z * 4.87 / np.log(67.8 * z_m - 5.42), u_z)


def Ra_N(doy, lat):
    Gsc = 0.0820
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    delta = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(lat) * np.tan(delta), -1, 1))
    Ra = (24 * 60 / np.pi) * Gsc * dr * (
        ws * np.sin(lat) * np.sin(delta) +
        np.cos(lat) * np.cos(delta) * np.sin(ws)
    )
    N = (24 / np.pi) * ws
    return Ra, N


def load_annual(aws_path, asos_path):
    aws = pd.read_csv(aws_path)
    date = pd.to_datetime(aws['time'])
    df = pd.DataFrame({
        'DATE': date,
        'DOY': date.dt.dayofyear,
        'TMEAN': pd.to_numeric(aws['tmean'], errors='coerce'),
        'TMIN': pd.to_numeric(aws['tmin'], errors='coerce'),
        'TMAX': pd.to_numeric(aws['tmax'], errors='coerce'),
        'PRE': pd.to_numeric(aws['pre'], errors='coerce'),
        'U_raw': pd.to_numeric(aws['wind'], errors='coerce')
    })

    try:
        asos = pd.read_csv(asos_path, encoding='cp949')
    except Exception:
        asos = pd.read_csv(asos_path)

    if '지점' in asos.columns:
        asos = asos[asos['지점'] == 189]

    sun = pd.DataFrame({
        'DATE': pd.to_datetime(asos['time'], errors='coerce'),
        'SUNH': pd.to_numeric(asos['hour'], errors='coerce')
    }).dropna(subset=['DATE'])
    sun = sun.groupby('DATE', as_index=False)['SUNH'].mean()

    df = df.merge(sun, on='DATE', how='left')
    df['SUNH'] = df['SUNH'].fillna(0)

    lat = np.deg2rad(lat_deg)
    P = P_kPa(alt_m)
    ga = 0.000665 * P
    lam = 2.45

    Ra, N = Ra_N(df['DOY'].values, lat)
    U2 = u2_from_uz(df['U_raw'].values, wind_height_m)
    Rso = (0.75 + 2e-5 * alt_m) * Ra
    nN = np.clip(df['SUNH'].values / np.maximum(N, 1e-6), 0, 1)
    Rs = (a_s + b_s * nN) * Ra

    es = (e0(df['TMAX'].values) + e0(df['TMIN'].values)) / 2
    ea = e0(df['TMIN'].values)
    D = delta_fun(df['TMEAN'].values)

    sigma = 4.903e-9
    Tmax_K = df['TMAX'].values + 273.16
    Tmin_K = df['TMIN'].values + 273.16
    f = np.clip(Rs / np.maximum(Rso, 1e-6), 0, 1)
    kC = 1.35 * f - 0.35
    Rnl = sigma * ((Tmax_K ** 4 + Tmin_K ** 4) / 2) * (0.34 - 0.14 * np.sqrt(np.maximum(ea, 0))) * kC

    Rn_veg = (1 - alpha_veg) * Rs - Rnl
    Rn_water = (1 - alpha_water) * Rs - Rnl

    ETo = np.maximum(
        (0.408 * D * Rn_veg + ga * (900 / (df['TMEAN'].values + 273)) * U2 * (es - ea)) /
        (D + ga * (1 + 0.34 * U2)),
        0
    )

    E_P = np.maximum(
        (D / (D + ga)) * (Rn_water / lam) +
        (ga / (D + ga)) * (6.43 * (1 + 0.536 * U2) / lam) * (es - ea),
        0
    )

    P_C = (1 - I_C) * df['PRE'].values
    P_ES = np.where(
        (np.isnan(P_C)) | (P_C <= Ia_mm),
        0,
        (P_C - Ia_mm) ** 2 / (P_C + 0.8 * S_mm)
    )

    out = pd.DataFrame({
        'YEAR': df['DATE'].dt.year,
        'PRE': df['PRE'].values,
        'E_P': E_P,
        'ETo': ETo,
        'P_ES': P_ES,
        'P_P': (1 - I_P) * df['PRE'].values,
        'Q_S': f_QS * (1 - I_P) * df['PRE'].values
    })

    ann = out.groupby('YEAR').agg({
        'PRE': 'sum',
        'E_P': 'sum',
        'ETo': 'sum',
        'P_ES': 'sum',
        'P_P': 'sum',
        'Q_S': 'sum'
    }).reset_index()

    annual = {int(r.YEAR): r for _, r in ann.iterrows()}
    return annual, ann


def compute_internal_outlet_watershed(dem_path, pond_path):
    with rasterio.open(dem_path) as src:
        dem = src.read(1).astype('float64')
        transform = src.transform
        crs = src.crs
        nodata = src.nodata
        res_x = abs(src.res[0])
        res_y = abs(src.res[1])

    if nodata is not None:
        dem[dem == nodata] = np.nan

    dem[dem == -9999] = np.nan

    valid = np.isfinite(dem)
    nrow, ncol = dem.shape

    pond = gpd.read_file(pond_path).to_crs(crs)
    pond_area = float(pond.area.sum())

    pond_mask = rasterize(
        [(geom, 1) for geom in pond.geometry],
        out_shape=dem.shape,
        transform=transform,
        fill=0,
        dtype='uint8',
        all_touched=False
    ).astype(bool)

    pond_mask &= valid

    d8_dr = np.array([0, -1, -1, -1, 0, 1, 1, 1], dtype=int)
    d8_dc = np.array([1, 1, 0, -1, -1, -1, 0, 1], dtype=int)
    d8_code = np.array([1, 2, 4, 8, 16, 32, 64, 128], dtype=np.int16)
    d8_dist = np.array(
        [1, math.sqrt(2), 1, math.sqrt(2), 1, math.sqrt(2), 1, math.sqrt(2)],
        dtype='float64'
    ) * res_x

    rev_map = {
        1: 16,
        2: 32,
        4: 64,
        8: 128,
        16: 1,
        32: 2,
        64: 4,
        128: 8
    }

    def priority_flood_epsilon(dem_array, outlet_mask):
        z = dem_array.copy()
        valid_local = np.isfinite(z)
        filled = z.copy()
        visited = np.zeros(z.shape, dtype=bool)
        heap = []

        for rr in [0, z.shape[0] - 1]:
            for cc in range(z.shape[1]):
                if valid_local[rr, cc] and not visited[rr, cc]:
                    visited[rr, cc] = True
                    heapq.heappush(heap, (filled[rr, cc], int(rr), int(cc)))

        for cc in [0, z.shape[1] - 1]:
            for rr in range(z.shape[0]):
                if valid_local[rr, cc] and not visited[rr, cc]:
                    visited[rr, cc] = True
                    heapq.heappush(heap, (filled[rr, cc], int(rr), int(cc)))

        for rr, cc in np.argwhere(outlet_mask & valid_local):
            if not visited[rr, cc]:
                visited[rr, cc] = True
                heapq.heappush(heap, (filled[rr, cc], int(rr), int(cc)))

        while heap:
            elev, rr, cc = heapq.heappop(heap)
            for dr, dc in zip(d8_dr, d8_dc):
                nr, nc = rr + dr, cc + dc
                if (
                    0 <= nr < z.shape[0] and
                    0 <= nc < z.shape[1] and
                    valid_local[nr, nc] and
                    not visited[nr, nc]
                ):
                    visited[nr, nc] = True
                    new_elev = filled[nr, nc]
                    if new_elev <= elev:
                        new_elev = np.nextafter(elev, np.inf)
                        filled[nr, nc] = new_elev
                    heapq.heappush(heap, (new_elev, int(nr), int(nc)))

        return filled

    def d8_flowdir(elev):
        valid_local = np.isfinite(elev)
        best = np.full(elev.shape, -np.inf, dtype='float64')
        fdir = np.zeros(elev.shape, dtype=np.int16)
        fdir[~valid_local] = -1

        for dr, dc, code, dist in zip(d8_dr, d8_dc, d8_code, d8_dist):
            neigh = np.full_like(elev, np.nan)

            src_r0 = max(0, dr)
            src_r1 = elev.shape[0] + min(0, dr)
            src_c0 = max(0, dc)
            src_c1 = elev.shape[1] + min(0, dc)

            dst_r0 = max(0, -dr)
            dst_r1 = elev.shape[0] - max(0, dr)
            dst_c0 = max(0, -dc)
            dst_c1 = elev.shape[1] - max(0, dc)

            neigh[dst_r0:dst_r1, dst_c0:dst_c1] = elev[src_r0:src_r1, src_c0:src_c1]
            slope = (elev - neigh) / dist
            mask = valid_local & np.isfinite(neigh) & (slope > best)

            best[mask] = slope[mask]
            fdir[mask] = code

        fdir[(best <= 0) & valid_local] = 0
        return fdir

    filled = priority_flood_epsilon(dem, pond_mask)
    fdir = d8_flowdir(filled)

    visited = np.zeros(dem.shape, dtype=bool)
    external = np.zeros(dem.shape, dtype=np.uint8)
    q = deque()

    for rr, cc in np.argwhere(pond_mask & valid):
        visited[rr, cc] = True
        q.append((int(rr), int(cc)))

    while q:
        rr, cc = q.popleft()
        for dr, dc, code in zip(d8_dr, d8_dc, d8_code):
            nr, nc = rr + dr, cc + dc
            if (
                0 <= nr < nrow and
                0 <= nc < ncol and
                valid[nr, nc] and
                not visited[nr, nc]
            ):
                if fdir[nr, nc] == rev_map[int(code)]:
                    visited[nr, nc] = True
                    q.append((int(nr), int(nc)))
                    if not pond_mask[nr, nc]:
                        external[nr, nc] = 1

    total = ((external == 1) | pond_mask)

    pond_cells = int(np.sum(pond_mask))
    external_cells = int(np.sum(external))
    total_cells = int(np.sum(total))
    cell_area = float(res_x * res_y)

    return {
        'pond_polygon_area_m2': pond_area,
        'pond_raster_cells': pond_cells,
        'external_cells': external_cells,
        'total_cells': total_cells,
        'external_area_m2': external_cells * cell_area,
        'total_area_m2': total_cells * cell_area,
        'cell_area_m2': cell_area
    }


def run_model(dem_path, pond_path, aws_path, asos_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)

    annual, annual_df = load_annual(aws_path, asos_path)
    annual_df.to_csv(os.path.join(out_dir, 'annual_forcing_python_exact.csv'), index=False)

    ws_info = compute_internal_outlet_watershed(dem_path, pond_path)

    A_P_obs_2011 = float(ws_info['pond_polygon_area_m2'])
    A_ws_external = float(ws_info['external_area_m2'])

    with rasterio.open(dem_path) as src:
        crs = src.crs

    pond = gpd.read_file(pond_path).to_crs(crs)

    r_buf = (
        float(pond.buffer(FINAL_BUFFER_WIDTH_M).area.sum()) -
        A_P_obs_2011
    ) / A_P_obs_2011

    def A_h(h, alpha, eff=None):
        hb = h_base if eff is None else eff
        return 0.0 if h <= 0 else A_P_obs_2011 * (h / hb) ** alpha

    def V_h(h, alpha, eff=None):
        hb = h_base if eff is None else eff
        return 0.0 if h <= 0 else A_P_obs_2011 * hb / (alpha + 1) * (h / hb) ** (alpha + 1)

    def calc_et(cohorts, A_R, ETo, hydro):
        """
        Riparian evapotranspiration loss based on a simplified FAO-56
        dual crop coefficient representation.

        ET_R,i = (K_cb,i + K_e,i) * ETo

        Forest and grassland are assumed to be fully covered by vegetation,
        so K_e is set to zero for these cover types. Bare ground is assumed
        to have no basal transpiration, so its evaporation is represented by K_e.

        ETo is an annual total in mm at this stage. The returned value is
        volumetric water loss in m3 for the annual time step.
        """
        if A_R <= 0:
            return 0.0

        K_forest = K_cb_forest + K_e_forest
        K_grass  = K_cb_grass  + K_e_grass
        K_bare   = K_cb_bare   + K_e_bare

        Aco = sum(c[0] for c in cohorts)
        Abase = max(A_R - Aco, 0)

        if not hydro:
            return (Abase * K_forest + Aco * K_bare) * ETo / 1000

        Af = sum(a for a, age, t in cohorts if t == 'forest')
        Ag = sum(a for a, age, t in cohorts if t == 'grass')
        Ab = sum(a for a, age, t in cohorts if t == 'bare')

        return (
            Abase * K_forest +
            Af * K_forest +
            Ag * K_grass +
            Ab * K_bare
        ) * ETo / 1000

    def update_cohorts(cohorts, dA, A_R, hydro):
        cohorts = [list(c) for c in cohorts]

        if dA > 0 and cohorts:
            absorb = dA
            for c in cohorts[::-1]:
                if absorb <= 0:
                    break
                take = min(c[0], absorb)
                c[0] -= take
                absorb -= take
            cohorts = [c for c in cohorts if c[0] > 0.01]

        if dA < 0:
            cur = sum(c[0] for c in cohorts)
            new = min(-dA, max(A_R - cur, 0))
            if new > 0.01:
                cohorts.append([new, 0, 'bare'])

        for c in cohorts:
            c[1] += 1
            if hydro:
                if c[2] == 'bare' and c[1] >= 1:
                    c[2] = 'grass'
                if c[2] == 'grass' and c[1] >= 5:
                    c[2] = 'forest'

        return [tuple(c) for c in cohorts]

    def simulate(hydro, rise):
        alpha = FINAL_ALPHA_SHAPE
        relax = FINAL_SCALE_RELAX
        bottom_relax = FINAL_BOTTOM_RELAX

        h = h_init
        W = V_h(h, alpha)
        Aprev = A_P_obs_2011

        bottom_raw = 0.0
        bottom_applied = 0.0
        cohorts = []
        rows = []

        for yr in range(2012, 2024):
            r = annual.get(yr, None)

            if r is None:
                E_P = ETo = PES = PP = QS = 0.0
            else:
                E_P = float(r.E_P)
                ETo = float(r.ETo)
                PES = float(r.P_ES)
                PP = float(r.P_P)
                QS = float(r.Q_S)

            A = A_h(h, alpha)
            AR = A * r_buf

            dW = (
                A_ws_external * PES / 1000 +
                A * PP / 1000 -
                calc_et(cohorts, AR, ETo, hydro) -
                A * (1 - f_ET_reduction) * E_P / 1000 -
                A * QS / 1000
            )

            Wnew = max(W + dW, 0)

            bottom_raw += rise
            bottom_applied = bottom_applied + bottom_relax * (bottom_raw - bottom_applied)

            eff = h_base + damping_factor * bottom_applied

            hraw = (
                0.0 if Wnew <= 0
                else ((Wnew * (alpha + 1)) / (A_P_obs_2011 * eff)) ** (1 / (alpha + 1)) * eff
            )

            hnext = h + relax * (max(hraw, 0) - h)
            Anext = A_h(hnext, alpha, eff)
            Wnext = V_h(hnext, alpha, eff)

            cohorts = update_cohorts(cohorts, Anext - Aprev, AR, hydro)

            Aprev = Anext

            rows.append((
                yr,
                Anext,
                AR,
                Wnext,
                hnext,
                eff,
                bottom_raw,
                bottom_applied
            ))

            h = hnext
            W = Wnext

        return np.array(rows, dtype=float)

    def metric(arr):
        d = {2011: A_P_obs_2011}

        for row in arr:
            d[int(row[0])] = row[1]

        y = np.array([d[int(yy)] for yy in plot_years], dtype=float)
        dy = np.diff(y)

        rmse = float(np.sqrt(np.mean((y - obs_y) ** 2)))
        nrmse = float(rmse / obs_y.mean() * 100)

        corr = float(np.corrcoef(y, obs_y)[0, 1]) if np.std(y) > 1e-9 else -1.0
        dcorr = float(np.corrcoef(dy, obs_diff)[0, 1]) if np.std(dy) > 1e-9 else -1.0

        return {
            'y': y,
            'dy': dy,
            'rmse': rmse,
            'nrmse': nrmse,
            'corr': corr,
            'dcorr': dcorr,
            'rebound': float(np.maximum(dy, 0).sum()),
            'diff_rmse': float(np.sqrt(np.mean((dy - obs_diff) ** 2))),
            'slope': float(y[-1] - y[0])
        }

    sims = {
        'Baseline Model': simulate(False, 0.0),
        'Hydrosere Only Model': simulate(True, 0.0),
        'Eco-Geo Only Model': simulate(False, bottom_rise),
        'Integrated Model': simulate(True, bottom_rise)
    }

    mets = {k: metric(v) for k, v in sims.items()}

    rm = []
    plot_rows = []
    diff_rows = []

    for name, arr in sims.items():
        m = mets[name]

        rm.append({
            'Scenario': name,
            'RMSE_m2': m['rmse'],
            'NRMSE_pct': m['nrmse'],
            'trend_corr': m['corr'],
            'diff_corr': m['dcorr'],
            'rebound_m2': m['rebound'],
            'change_2011_2023_m2': m['slope'],
            'Area_2023_m2': m['y'][-1]
        })

        scenario_file = name.lower().replace(' ', '_').replace('-', '') + '_wb_python.csv'

        pd.DataFrame(
            arr,
            columns=[
                'Year',
                'LakeArea_m2',
                'Buf_m2',
                'LakeStorage_m3',
                'h',
                'eff_hb',
                'BottomRaw_m',
                'BottomApplied_m'
            ]
        ).to_csv(os.path.join(out_dir, scenario_file), index=False)

        d = {2011: A_P_obs_2011}

        for row in arr:
            d[int(row[0])] = row[1]

        plot_rows.append(pd.DataFrame({
            'Year': plot_years,
            'LakeArea_m2': [d[int(yy)] for yy in plot_years],
            'Scenario': name
        }))

        diff_rows.append(pd.DataFrame({
            'Scenario': name,
            'Interval': [
                f'{plot_years[i]}-{plot_years[i + 1]}'
                for i in range(len(plot_years) - 1)
            ],
            'dArea_m2': m['dy']
        }))

    rmse = pd.DataFrame(rm).sort_values('NRMSE_pct')
    plot_df = pd.concat(plot_rows, ignore_index=True)
    observed = pd.DataFrame({'Year': plot_years, 'Area_m2': obs_y})
    diffs = pd.concat(diff_rows, ignore_index=True)

    settings = pd.DataFrame([{
        'buffer_width_m': FINAL_BUFFER_WIDTH_M,
        'buffer_area_m2': A_P_obs_2011 * r_buf,
        'buffer_area_ratio': r_buf,
        'relax_shared': FINAL_RELAX,
        'scale_relax': FINAL_SCALE_RELAX,
        'alpha_shape': FINAL_ALPHA_SHAPE,
        'bottom_relax': FINAL_BOTTOM_RELAX,
        'K_cb_forest': K_cb_forest,
        'K_e_forest': K_e_forest,
        'K_cb_grass': K_cb_grass,
        'K_e_grass': K_e_grass,
        'K_cb_bare': K_cb_bare,
        'K_e_bare': K_e_bare,
        'K_total_forest': K_cb_forest + K_e_forest,
        'K_total_grass': K_cb_grass + K_e_grass,
        'K_total_bare': K_cb_bare + K_e_bare,
        'h_init_m_fixed': h_init,
        'external_contributing_area_m2': A_ws_external,
        'total_contributing_area_including_pond_m2': ws_info['total_area_m2'],
        'pond_polygon_area_m2': A_P_obs_2011,
        'pond_raster_cells': ws_info['pond_raster_cells'],
        'external_cells': ws_info['external_cells'],
        'total_cells': ws_info['total_cells']
    }])

    rmse.to_csv(os.path.join(out_dir, 'rmse_table_python_exact.csv'), index=False)
    plot_df.to_csv(os.path.join(out_dir, 'plot_df_python_exact.csv'), index=False)
    observed.to_csv(os.path.join(out_dir, 'observed_area.csv'), index=False)
    diffs.to_csv(os.path.join(out_dir, 'year_to_year_differences_python_exact.csv'), index=False)
    settings.to_csv(os.path.join(out_dir, 'model_settings_summary_python_exact.csv'), index=False)

    pd.DataFrame(
        sims['Integrated Model'],
        columns=[
            'Year',
            'LakeArea_m2',
            'Buf_m2',
            'LakeStorage_m3',
            'h',
            'eff_hb',
            'BottomRaw_m',
            'BottomApplied_m'
        ]
    ).to_csv(os.path.join(out_dir, 'integrated_wb_python_exact.csv'), index=False)

    return {
        'rmse': rmse,
        'plot_df': plot_df,
        'observed': observed,
        'settings': settings,
        'watershed': pd.DataFrame([ws_info])
    }
)"

reticulate::py_run_string(py_code)

# Run Python model.
# Python writes all outputs as CSV; R reads those CSVs back.
# This avoids pandas DataFrames staying as Python refs.
invisible(reticulate::py$run_model(dem_path, pond_path, aws_path, asos_path, out_dir))

rmse <- read.csv(
  file.path(out_dir, "rmse_table_python_exact.csv"),
  stringsAsFactors = FALSE
)

plot_df <- read.csv(
  file.path(out_dir, "plot_df_python_exact.csv"),
  stringsAsFactors = FALSE
)

observed_area <- read.csv(
  file.path(out_dir, "observed_area.csv"),
  stringsAsFactors = FALSE
)

settings <- read.csv(
  file.path(out_dir, "model_settings_summary_python_exact.csv"),
  stringsAsFactors = FALSE
)

watershed <- settings[, c(
  "external_contributing_area_m2",
  "total_contributing_area_including_pond_m2",
  "pond_polygon_area_m2",
  "pond_raster_cells",
  "external_cells",
  "total_cells"
)]



# -----------------------------
# 4. R plot
# -----------------------------
TEXT_SCALE <- 0.9

# 글씨체 설정
font_family <- "Arial"

# Arial이 적용되지 않으면 아래처럼 교체
# font_family <- "sans"

label_map <- setNames(
  paste0(rmse$Scenario, " (", sprintf("%.2f", rmse$NRMSE_pct), "%)"),
  rmse$Scenario
)

plot_df$ScenarioLabel <- unname(label_map[plot_df$Scenario])

legend_breaks <- c(
  unname(label_map["Baseline Model"]),
  unname(label_map["Hydrosere Only Model"]),
  unname(label_map["Eco-Geo Only Model"]),
  unname(label_map["Integrated Model"]),
  "Observed"
)

color_values <- setNames(
  c("#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "black"),
  legend_breaks
)

p <- ggplot() +
  geom_line(
    data = plot_df,
    aes(
      x = Year,
      y = LakeArea_m2,
      color = ScenarioLabel,
      group = ScenarioLabel
    ),
    linewidth = 1.2
  ) +
  geom_point(
    data = plot_df,
    aes(
      x = Year,
      y = LakeArea_m2,
      color = ScenarioLabel
    ),
    size = 3.2
  ) +
  geom_line(
    data = observed_area,
    aes(
      x = Year,
      y = Area_m2,
      color = "Observed"
    ),
    linewidth = 2.2
  ) +
  geom_point(
    data = observed_area,
    aes(
      x = Year,
      y = Area_m2,
      color = "Observed"
    ),
    size = 3.8
  ) +
  scale_x_continuous(
    breaks = c(2011, 2013, 2015, 2017, 2019, 2021, 2023)
  ) +
  scale_color_manual(
    values = color_values,
    breaks = legend_breaks,
    name = NULL
  ) +
  labs(
    x = "Year",
    y = expression("Pond area (m"^2*")")
  ) +
  theme_classic(
    base_size = 22 * TEXT_SCALE,
    base_family = font_family
  ) +
  theme(
    text = element_text(
      family = font_family,
      color = "black"
    ),
    
    axis.title = element_text(
      family = font_family,
      size = 26,
      color = "black"
    ),
    
    axis.text = element_text(
      family = font_family,
      size = 18,
      color = "black"
    ),
    
    axis.text.x = element_text(
      family = font_family,
      angle = 45,
      hjust = 1,
      color = "black"
    ),
    
    axis.text.y = element_text(
      family = font_family,
      color = "black"
    ),
    
    axis.title.x = element_text(
      family = font_family,
      margin = margin(t = 14),
      color = "black"
    ),
    
    axis.title.y = element_text(
      family = font_family,
      margin = margin(r = 10),
      color = "black"
    ),
    
    # 범례 포함
    legend.position = c(0.04, 0.06),
    legend.justification = c("left", "bottom"),
    
    legend.text = element_text(
      family = font_family,
      size = 16,
      color = "black"
    ),
    
    legend.background = element_rect(
      fill = "white",
      color = "grey70",
      linewidth = 0.5
    ),
    
    legend.key.width = unit(1.25, "cm"),
    legend.key.height = unit(0.55, "cm"),
    
    panel.border = element_rect(
      color = "black",
      fill = NA,
      linewidth = 0.8
    ),
    
    plot.margin = margin(
      t = 16,
      r = 22,
      b = 18,
      l = 18
    )
  ) +
  guides(
    color = guide_legend(
      override.aes = list(
        linewidth = c(1.2, 1.2, 1.2, 1.2, 2.2),
        size = c(3.2, 3.2, 3.2, 3.2, 3.8)
      )
    )
  )

print(p)

# -----------------------------
# 5. Save plot as high-resolution TIFF
# -----------------------------
fig_width_in  <- 11.5
fig_height_in <- 7.2
fig_dpi       <- 1000

ggsave(
  filename = file.path(out_dir, "pond_area_model_comparison_R_1000dpi_final_balanced_arial_legend.tif"),
  plot = p,
  device = ragg::agg_tiff,
  width = fig_width_in,
  height = fig_height_in,
  units = "in",
  dpi = fig_dpi,
  compression = "lzw",
  background = "white"
)

cat("\nRMSE table\n")
print(rmse)

cat("\nSettings\n")
print(settings)

cat("\nWatershed\n")
print(watershed)

cat("\nOutputs written to:\n", out_dir, "\n")

















# ============================================================
# Climate-only indicators
# - 3 x 2 layout
#   Top row   : Temperature / Rainfall / Pond ET
#   Bottom row: Forest ET / Grass ET / Bare ET
# - Exclude YEAR == 2025
# - Show only odd years on x-axis
# - Show x-axis year labels also on the top row
# - Larger year labels
# - Move each variable title to the y-axis side
# - All panels have identical width and area
# - Font changed to Arial-like sans-serif
# - Open plot in independent graphics window
# - Export as TIFF, 1000 dpi
# - Export as PDF
# - IMPORTANT:
#   1) showtext is forcibly disabled
#   2) ggsave() is not used for TIFF export
# ============================================================

# ------------------------------------------------------------
# 0) Packages
# ------------------------------------------------------------
pkgs <- c("dplyr", "ggplot2", "readr", "ragg", "tidyr")

for (p in pkgs) {
  if (!requireNamespace(p, quietly = TRUE)) install.packages(p)
}

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(readr)
  library(ragg)
  library(tidyr)
})

# ------------------------------------------------------------
# 0-1) Disable showtext if it was previously enabled
# ------------------------------------------------------------
if ("showtext" %in% loadedNamespaces()) {
  showtext::showtext_auto(FALSE)
}

# ------------------------------------------------------------
# 1) Load annual forcing
# ------------------------------------------------------------
if (exists("annual_forcing")) {
  
  annual_raw <- annual_forcing
  message("Using existing object: annual_forcing")
  
} else {
  
  candidate_files <- character(0)
  
  if (exists("out_dir")) {
    candidate_files <- c(
      candidate_files,
      file.path(out_dir, "annual_forcing_python_exact.csv")
    )
  }
  
  candidate_files <- c(
    candidate_files,
    "annual_forcing_python_exact.csv"
  )
  
  candidate_files <- candidate_files[file.exists(candidate_files)]
  
  if (length(candidate_files) == 0) {
    stop(
      "annual_forcing object was not found, and annual_forcing_python_exact.csv was not found.\n",
      "Run the model first or provide annual_forcing."
    )
  }
  
  annual_raw <- readr::read_csv(candidate_files[1], show_col_types = FALSE)
  message("Loaded annual forcing file: ", candidate_files[1])
}

# ------------------------------------------------------------
# 2) Helper: flexible column picker
# ------------------------------------------------------------
pick_col <- function(data, candidates, label, required = TRUE) {
  
  hit <- intersect(candidates, names(data))
  
  if (length(hit) == 0) {
    
    if (required) {
      stop(
        "Could not find column for: ", label, "\n",
        "Tried: ", paste(candidates, collapse = ", "), "\n",
        "Available columns: ", paste(names(data), collapse = ", ")
      )
    } else {
      return(NA_character_)
    }
  }
  
  hit[1]
}

# ------------------------------------------------------------
# 3) Identify main annual forcing columns
# ------------------------------------------------------------
year_col <- pick_col(
  annual_raw,
  c("YEAR", "Year", "year"),
  "year"
)

rain_col <- pick_col(
  annual_raw,
  c(
    "precip_mm",
    "PRE",
    "pre",
    "Rain_mm_yr",
    "precip",
    "precipitation_mm",
    "P_mm",
    "P"
  ),
  "annual precipitation"
)

lake_evap_col <- pick_col(
  annual_raw,
  c(
    "evap_lake_mm",
    "E_P",
    "EP",
    "lake_evap_mm",
    "open_water_evap_mm",
    "evaporation_mm",
    "PoolEvap_mm_yr"
  ),
  "open-water evaporation"
)

eto_col <- pick_col(
  annual_raw,
  c(
    "eto_veg_mm",
    "ETo",
    "ETO",
    "ET0",
    "reference_et_mm",
    "ref_et_mm"
  ),
  "reference ET"
)

temp_col <- pick_col(
  annual_raw,
  c(
    "tmean_C",
    "mean_temp_C",
    "temp_mean_C",
    "MAT_C",
    "annual_mean_temp_C",
    "TMEAN_C",
    "TMEAN",
    "Temp_C"
  ),
  "annual mean temperature",
  required = FALSE
)

message("Column mapping used:")
message("  Year column      : ", year_col)
message("  Rainfall column  : ", rain_col)
message("  Lake evap column : ", lake_evap_col)
message("  ETo column       : ", eto_col)
message("  Temp column      : ", ifelse(is.na(temp_col), "not found in annual_forcing", temp_col))

# ------------------------------------------------------------
# 4) Prepare annual climate table
# ------------------------------------------------------------
clim_base <- annual_raw %>%
  transmute(
    Year = as.integer(.data[[year_col]]),
    Rain_mm_yr = as.numeric(.data[[rain_col]]),
    OpenWaterEvap_mm_yr = as.numeric(.data[[lake_evap_col]]),
    ETo_mm_yr = as.numeric(.data[[eto_col]])
  ) %>%
  filter(!is.na(Year)) %>%
  distinct()

# ------------------------------------------------------------
# 5) Prepare annual temperature
# ------------------------------------------------------------
if (!is.na(temp_col)) {
  
  temp_annual <- annual_raw %>%
    transmute(
      Year = as.integer(.data[[year_col]]),
      MeanTemp_C = as.numeric(.data[[temp_col]])
    ) %>%
    filter(!is.na(Year)) %>%
    distinct()
  
  message("Annual mean temperature taken from annual_forcing.")
  
} else {
  
  if (!exists("aws_path")) {
    stop(
      "No annual temperature column was found in annual_forcing,\n",
      "and aws_path does not exist in the current session."
    )
  }
  
  if (!file.exists(aws_path)) {
    stop(
      "No annual temperature column was found in annual_forcing,\n",
      "and aws_path file does not exist:\n", aws_path
    )
  }
  
  aws_raw <- readr::read_csv(aws_path, show_col_types = FALSE)
  
  aws_time_col <- pick_col(
    aws_raw,
    c("time", "TIME", "date", "DATE", "Date"),
    "AWS date/time"
  )
  
  aws_tmean_col <- pick_col(
    aws_raw,
    c("tmean", "TMEAN", "mean_temp", "temp_mean", "temperature_mean"),
    "AWS daily mean temperature"
  )
  
  temp_annual <- aws_raw %>%
    transmute(
      Date = as.Date(.data[[aws_time_col]]),
      MeanTemp_C_daily = as.numeric(.data[[aws_tmean_col]])
    ) %>%
    filter(!is.na(Date)) %>%
    mutate(
      Year = as.integer(format(Date, "%Y"))
    ) %>%
    group_by(Year) %>%
    summarise(
      MeanTemp_C = mean(MeanTemp_C_daily, na.rm = TRUE),
      .groups = "drop"
    )
  
  message("Annual mean temperature computed from aws_path.")
}

# ------------------------------------------------------------
# 6) Model-consistent constants
# ------------------------------------------------------------
K_cb_forest <- 0.95
K_cb_grass  <- 0.90
K_cb_bare   <- 0.30

lake_evap_reduction_frac <- 0.20

# ------------------------------------------------------------
# 7) Build final indicator table
# ------------------------------------------------------------
ind_clim <- clim_base %>%
  left_join(temp_annual, by = "Year") %>%
  filter(Year != 2025) %>%
  mutate(
    Pond_ET_mm_yr   = (1 - lake_evap_reduction_frac) * OpenWaterEvap_mm_yr,
    Forest_ET_mm_yr = K_cb_forest * ETo_mm_yr,
    Grass_ET_mm_yr  = K_cb_grass  * ETo_mm_yr,
    Bare_ET_mm_yr   = K_cb_bare   * ETo_mm_yr
  ) %>%
  arrange(Year)

print(ind_clim)

# ------------------------------------------------------------
# 8) Figure settings
# ------------------------------------------------------------
out_tif <- "Fig_climate_only_3x2_ytitle_topx_1000dpi_arial.tif"
out_pdf <- "Fig_climate_only_3x2_ytitle_topx_arial.pdf"

fig_width_in  <- 14.2
fig_height_in <- 8.0
fig_dpi       <- 1000

# 첨부 예시와 유사한 산세리프체
font_family <- "Arial"

# Arial이 적용되지 않으면 아래 한 줄로 교체
# font_family <- "sans"

base_size        <- 16
strip_text_sz    <- 20
axis_text_x_sz   <- 17
axis_text_y_sz   <- 14
axis_title_x_sz  <- 22

line_width      <- 1.10
point_size      <- 2.6
panel_border_w  <- 0.65
tick_line_w     <- 0.45

# ------------------------------------------------------------
# 9) Convert to long format for identical 3 x 2 panels
# ------------------------------------------------------------
ind_long <- ind_clim %>%
  select(
    Year,
    MeanTemp_C,
    Rain_mm_yr,
    Pond_ET_mm_yr,
    Forest_ET_mm_yr,
    Grass_ET_mm_yr,
    Bare_ET_mm_yr
  ) %>%
  pivot_longer(
    cols = -Year,
    names_to = "Variable",
    values_to = "Value"
  ) %>%
  mutate(
    Variable = factor(
      Variable,
      levels = c(
        "MeanTemp_C",
        "Rain_mm_yr",
        "Pond_ET_mm_yr",
        "Forest_ET_mm_yr",
        "Grass_ET_mm_yr",
        "Bare_ET_mm_yr"
      ),
      labels = c(
        "Mean temp. (°C)",
        "Rainfall (mm yr-1)",
        "Pond ET (mm yr-1)",
        "Forest ET (mm yr-1)",
        "Grass ET (mm yr-1)",
        "Bare ET (mm yr-1)"
      )
    )
  )

# ------------------------------------------------------------
# 10) X-axis breaks
# ------------------------------------------------------------
x_breaks_vec <- sort(unique(ind_clim$Year[ind_clim$Year %% 2 == 1]))
x_limits_vec <- range(ind_clim$Year, na.rm = TRUE) + c(-0.3, 0.3)

# ------------------------------------------------------------
# 11) Build 3 x 2 equal-area panel figure
# ------------------------------------------------------------
p <- ggplot(ind_long, aes(x = Year, y = Value)) +
  geom_line(
    linewidth = line_width,
    color = "black"
  ) +
  geom_point(
    size = point_size,
    color = "black"
  ) +
  facet_wrap(
    ~ Variable,
    ncol = 3,
    scales = "free_y",
    strip.position = "left",
    axes = "all_x",
    axis.labels = "all_x"
  ) +
  scale_x_continuous(
    breaks = x_breaks_vec,
    limits = x_limits_vec
  ) +
  labs(
    x = "Year",
    y = NULL
  ) +
  theme_classic(
    base_size = base_size,
    base_family = font_family
  ) +
  theme(
    text = element_text(
      family = font_family,
      color = "black"
    ),
    
    strip.background = element_blank(),
    strip.placement = "outside",
    
    strip.text.y.left = element_text(
      family = font_family,
      size = strip_text_sz,
      color = "black",
      face = "plain",
      angle = 90,
      margin = margin(r = 8)
    ),
    
    axis.title.x = element_text(
      family = font_family,
      size = axis_title_x_sz,
      margin = margin(t = 10),
      color = "black"
    ),
    
    axis.title.y = element_blank(),
    
    axis.text.x = element_text(
      family = font_family,
      size = axis_text_x_sz,
      angle = 45,
      hjust = 1,
      vjust = 1,
      color = "black"
    ),
    
    axis.text.y = element_text(
      family = font_family,
      size = axis_text_y_sz,
      color = "black"
    ),
    
    axis.ticks = element_line(
      linewidth = tick_line_w,
      color = "black"
    ),
    
    axis.ticks.length = unit(0.11, "cm"),
    
    panel.border = element_rect(
      color = "black",
      fill = NA,
      linewidth = panel_border_w
    ),
    
    panel.spacing.x = unit(1.4, "lines"),
    panel.spacing.y = unit(1.6, "lines"),
    
    plot.margin = margin(
      t = 18,
      r = 18,
      b = 18,
      l = 18
    )
  )

# ------------------------------------------------------------
# 12) Print to current plot pane
# ------------------------------------------------------------
print(p)

# ------------------------------------------------------------
# 13) Open in independent graphics window
# ------------------------------------------------------------
if (interactive()) {
  if (.Platform$OS.type == "windows") {
    windows(
      width = fig_width_in,
      height = fig_height_in
    )
  } else {
    grDevices::dev.new(
      width = fig_width_in,
      height = fig_height_in
    )
  }
  
  print(p)
}

# ------------------------------------------------------------
# 14) Save combined 3 x 2 figure as TIFF
# ------------------------------------------------------------
ragg::agg_tiff(
  filename = out_tif,
  width = fig_width_in,
  height = fig_height_in,
  units = "in",
  res = fig_dpi,
  compression = "lzw",
  background = "white"
)

print(p)
dev.off()

message(
  "\nSaved TIFF file:\n",
  normalizePath(out_tif, winslash = "/", mustWork = FALSE),
  "\n"
)

# ------------------------------------------------------------
# 15) Save combined 3 x 2 figure as PDF
# ------------------------------------------------------------
grDevices::cairo_pdf(
  filename = out_pdf,
  width = fig_width_in,
  height = fig_height_in,
  family = font_family
)

print(p)
dev.off()

message(
  "\nSaved PDF file:\n",
  normalizePath(out_pdf, winslash = "/", mustWork = FALSE),
  "\n"
)












# ============================================================
# FULL CODE: Separate outputs for 3 plots
#  - Plot 1: Vegetation type vs Organic matter content (%)
#  - Plot 2: Vegetation type vs Distance to centroid (m)
#  - Plot 3: Organic matter content (%) vs Distance to centroid (m)
#
# 수정 사항:
# 1) patchwork로 합치지 않음
# 2) (a), (b), (c) 패널 문자 완전 제거
# 3) 각 그래프를 독립 실행창에 별도로 출력
# 4) 각 그래프를 TIFF 1000 dpi와 PDF로 각각 저장
# 5) 긴 학명은 두 줄 유지
# 6) 글자 크기 확대
# ============================================================

# 0) Clean graphics devices ------------------------------------

graphics.off()

# 1) Packages --------------------------------------------------

pkgs <- c(
  "dplyr", "tidyr", "ggplot2", "ggpubr", "tibble"
)

for (p in pkgs) {
  if (!requireNamespace(p, quietly = TRUE)) {
    install.packages(p, dependencies = TRUE)
  }
}

if (!requireNamespace("ragg", quietly = TRUE)) {
  install.packages("ragg", dependencies = TRUE)
}

suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(ggpubr)
  library(tibble)
})

# 2) Figure size and output paths ------------------------------

FIG_BOXPLOT_WIDTH_IN  <- 7.8
FIG_BOXPLOT_HEIGHT_IN <- 6.6

FIG_SCATTER_WIDTH_IN  <- 8.8
FIG_SCATTER_HEIGHT_IN <- 6.2

OUT_TIF_OM      <- "Fig_OM_by_vegetation_1000dpi.tif"
OUT_PDF_OM      <- "Fig_OM_by_vegetation.pdf"

OUT_TIF_DIST    <- "Fig_distance_by_vegetation_1000dpi.tif"
OUT_PDF_DIST    <- "Fig_distance_by_vegetation.pdf"

OUT_TIF_SCATTER <- "Fig_OM_distance_correlation_1000dpi.tif"
OUT_PDF_SCATTER <- "Fig_OM_distance_correlation.pdf"

# Text settings
X_LABEL_ANGLE <- 35
X_LABEL_SIZE  <- 17

FS_X_AXIS_TITLE <- 21
FS_Y_AXIS_TITLE <- 21
FS_AXIS_TEXT    <- 17
FS_PVALUE       <- 5.8
FS_TUKEY        <- 5.8

# 3) Direct data input -----------------------------------------

df <- tibble::tribble(
  ~id, ~left, ~top, ~syar_deep, ~`1`, ~`2`, ~`3`, ~`4`, ~`5`, ~`6`, ~`7`, ~`8`, ~veg, ~distance1,
  4, 143852.8709, 81682.0398, 40, 0.384615385, 0.350993377, 0.358064516, 0.325581395, NA, NA, NA, NA, "육상식생", 25.61347389,
  1, 143862.8709, 81692.0398, 80, 0.436507937, 0.416988417, 0.413114754, 0.441947566, 0.428104575, 0.435215947, 0.387417219, 0.408026756, "육상식생", 25.73033142,
  5, 143862.8709, 81682.0398, 80, 0.47, 0.478405316, 0.489932886, 0.508403361, 0.548494983, 0.514950166, 0.514950166, 0.510067114, "마름", 17.60823631,
  8, 143862.8709, 81672.0398, 80, 0.511013216, 0.51986755, 0.560402685, 0.592592593, 0.5625, 0.54, 0.518272425, 0.543333333, "마름", 12.57179356,
  12, 143862.8709, 81662.0398, 40, 0.476510067, 0.471760797, 0.48, 0.453947368, NA, NA, NA, NA, "마름", 14.35444164,
  16, 143862.8709, 81652.0398, 20, 0.503333333, 0.538461538, NA, NA, NA, NA, NA, NA, "송이고랭이", 21.30844879,
  2, 143872.8709, 81692.0398, 80, 0.501672241, 0.42192691, 0.426791277, 0.38490566, 0.450657895, 0.439597315, 0.493197279, 0.422794118, "송이고랭이", 22.71673393,
  6, 143872.8709, 81682.0398, 80, 0.494983278, 0.503311258, 0.518151815, 0.573333333, 0.54180602, 0.523333333, 0.50166113, 0.536666667, "송이고랭이", 12.80820084,
  9, 143872.8709, 81672.0398, 80, 0.556666667, 0.583850932, 0.634615385, 0.585185185, 0.644736842, 0.625827815, 0.643097643, 0.551495017, "마름", 3.471311092,
  13, 143872.8709, 81662.0398, 80, 0.53, 0.585526316, 0.544850498, 0.643333333, 0.738410596, 0.730337079, 0.656666667, 0.671096346, "마름", 7.749193668,
  17, 143872.8709, 81652.0398, 30, 0.403508772, 0.645756458, 0.661073826, NA, NA, NA, NA, NA, "마름", 17.55135345,
  3, 143882.8709, 81692.0398, 80, 0.408783784, 0.34, 0.323232323, 0.392026578, 0.375838926, 0.379194631, 0.376666667, 0.35, "육상식생", 23.87571907,
  7, 143882.8709, 81682.0398, 80, 0.538461538, 0.502439024, 0.459574468, 0.743718593, 0.512437811, 0.491638796, 0.418060201, 0.52, "송이고랭이", 14.76651573,
  10, 143882.8709, 81672.0398, 80, 0.666666667, 0.62541806, 0.645756458, 0.665562914, 0.598684211, 0.584158416, 0.619205298, 0.660066007, "마름", 8.12711525,
  14, 143882.8709, 81662.0398, 40, 0.524916944, 0.508305648, 0.572847682, 0.660066007, NA, NA, NA, NA, "마름", 10.67941952,
  18, 143882.8709, 81652.0398, 80, 0.7, 0.594594595, 0.636723954, 0.636723954, 0.639072848, 0.562913907, 0.623762376, 0.7, "마름", 19.02761078,
  19, 143882.8709, 81642.0398, 30, 0.53, 0.512195122, 0.504885993, NA, NA, NA, NA, NA, "송이고랭이", 28.4613781,
  11, 143892.8709, 81672.0398, 80, 0.481848185, 0.479865772, 0.483443709, 0.625827815, 0.623762376, 0.634868421, 0.551839465, 0.546979866, "송이고랭이", 17.88994217,
  15, 143892.8709, 81662.0398, 60, 0.5, 0.411184211, 0.460264901, 0.435643564, 0.418604651, 0.407284768, NA, NA, "송이고랭이", 19.18462944
)

# 4) Derived variables -----------------------------------------

df2 <- df %>%
  mutate(
    om_frac = rowMeans(dplyr::select(., `1`:`8`), na.rm = TRUE),
    om_pct  = 100 * om_frac
  ) %>%
  mutate(
    veg_en = dplyr::case_when(
      veg == "마름"       ~ "Trapa japonica",
      veg == "송이고랭이" ~ "Schoenoplectiella\ntriangulata",
      veg == "육상식생"   ~ "Terrestrial herbs",
      TRUE                ~ veg
    ),
    veg_en = factor(
      veg_en,
      levels = c(
        "Trapa japonica",
        "Schoenoplectiella\ntriangulata",
        "Terrestrial herbs"
      )
    )
  )

# 5) Helper functions ------------------------------------------

format_p_label <- function(pval) {
  pval <- as.numeric(pval)
  if (is.na(pval)) return("p = NA")
  if (pval < 0.001) return("p < .001")
  paste0("p = ", sprintf("%.3f", pval))
}

p_stars <- function(pval) {
  pval <- as.numeric(pval)
  if (is.na(pval)) return("ns")
  if (pval < 0.001) return("***")
  if (pval < 0.01)  return("**")
  if (pval < 0.05)  return("*")
  "ns"
}

theme_boxplot_panel <- function() {
  theme_bw(base_size = 17, base_family = "Arial") +
    theme(
      legend.position = "none",
      panel.grid.minor = element_blank(),
      panel.grid.major.x = element_blank(),
      
      axis.title.x = element_blank(),
      axis.title.y = element_text(
        size = FS_Y_AXIS_TITLE,
        lineheight = 0.90,
        margin = margin(r = 10)
      ),
      axis.text.y = element_text(size = FS_AXIS_TEXT),
      axis.text.x = element_text(
        size = X_LABEL_SIZE,
        angle = X_LABEL_ANGLE,
        hjust = 1,
        vjust = 1,
        lineheight = 0.82
      ),
      
      plot.title = element_blank(),
      plot.margin = margin(14, 18, 20, 18)
    )
}

theme_scatter_panel <- function() {
  theme_bw(base_size = 17, base_family = "Arial") +
    theme(
      panel.grid.minor = element_blank(),
      
      axis.title.x = element_text(
        size = FS_X_AXIS_TITLE,
        margin = margin(t = 10)
      ),
      axis.title.y = element_text(
        size = FS_Y_AXIS_TITLE,
        lineheight = 0.90,
        margin = margin(r = 10)
      ),
      axis.text = element_text(size = FS_AXIS_TEXT),
      
      plot.title = element_blank(),
      plot.margin = margin(14, 18, 14, 18)
    )
}

add_positioned_label <- function(
    plot_obj,
    label_text,
    x_pos,
    y_pos,
    hjust_val = 0,
    vjust_val = 0.5,
    text_size = FS_PVALUE,
    fontface_val = "plain"
) {
  plot_obj +
    annotate(
      "text",
      x = x_pos,
      y = y_pos,
      label = label_text,
      hjust = hjust_val,
      vjust = vjust_val,
      family = "Arial",
      fontface = fontface_val,
      size = text_size
    )
}

make_tukey_df <- function(aov_obj, term_name, y_positions) {
  tuk <- TukeyHSD(aov_obj, which = term_name)
  
  tuk_df <- as.data.frame(tuk[[term_name]])
  tuk_df$comparison <- rownames(tuk_df)
  
  tuk_df %>%
    tidyr::separate(
      comparison,
      into = c("group1", "group2"),
      sep = "-",
      remove = FALSE
    ) %>%
    mutate(
      p.adj = `p adj`,
      p.adj.signif = vapply(p.adj, p_stars, character(1)),
      y.position = y_positions[seq_len(n())]
    ) %>%
    dplyr::select(group1, group2, p.adj, p.adj.signif, y.position)
}

open_independent_plot_window <- function(width, height) {
  if (.Platform$OS.type == "windows") {
    grDevices::windows(width = width, height = height)
  } else if (capabilities("aqua")) {
    grDevices::quartz(width = width, height = height)
  } else if (capabilities("X11")) {
    grDevices::X11(width = width, height = height)
  } else {
    grDevices::dev.new(width = width, height = height)
  }
  invisible(TRUE)
}

save_plot_tif_pdf <- function(plot_obj, tif_path, pdf_path, width_in, height_in) {
  ggsave(
    filename = tif_path,
    plot = plot_obj,
    width = width_in,
    height = height_in,
    units = "in",
    dpi = 1000,
    device = ragg::agg_tiff,
    compression = "lzw",
    background = "white"
  )
  
  if (capabilities("cairo")) {
    ggsave(
      filename = pdf_path,
      plot = plot_obj,
      width = width_in,
      height = height_in,
      units = "in",
      device = grDevices::cairo_pdf,
      bg = "white"
    )
  } else {
    ggsave(
      filename = pdf_path,
      plot = plot_obj,
      width = width_in,
      height = height_in,
      units = "in",
      device = grDevices::pdf,
      bg = "white"
    )
  }
}

# 6) Plot 1: OM by vegetation ----------------------------------

p1_aov <- aov(om_pct ~ veg_en, data = df2)
p1_p   <- unname(summary(p1_aov)[[1]][["Pr(>F)"]][1])
p1_label <- format_p_label(p1_p)

tukey_om <- make_tukey_df(
  aov_obj = p1_aov,
  term_name = "veg_en",
  y_positions = c(63.5, 67.0, 70.5)
)

p_om <- ggplot(df2, aes(x = veg_en, y = om_pct, fill = veg_en)) +
  geom_boxplot(
    width = 0.55,
    color = "black",
    outlier.shape = NA,
    linewidth = 0.55
  ) +
  geom_jitter(
    shape = 21,
    color = "black",
    size = 2.8,
    width = 0.10,
    alpha = 0.90,
    stroke = 0.35
  ) +
  scale_fill_grey(start = 0.88, end = 0.35) +
  labs(
    x = NULL,
    y = "Organic matter\ncontent (%)"
  ) +
  ggpubr::stat_pvalue_manual(
    data = tukey_om,
    label = "p.adj.signif",
    xmin = "group1",
    xmax = "group2",
    y.position = "y.position",
    tip.length = 0.01,
    bracket.size = 0.45,
    size = FS_TUKEY,
    family = "Arial",
    hide.ns = FALSE,
    inherit.aes = FALSE
  ) +
  theme_boxplot_panel() +
  coord_cartesian(clip = "off") +
  scale_y_continuous(
    limits = c(33, 76),
    breaks = c(40, 50, 60, 70),
    expand = expansion(mult = c(0.03, 0.08))
  )

p_om <- add_positioned_label(
  plot_obj = p_om,
  label_text = p1_label,
  x_pos = 0.55,
  y_pos = 38.0,
  hjust_val = 0,
  vjust_val = 0.5
)

# 7) Plot 2: Distance by vegetation ----------------------------

p2_aov <- aov(distance1 ~ veg_en, data = df2)
p2_p   <- unname(summary(p2_aov)[[1]][["Pr(>F)"]][1])
p2_label <- format_p_label(p2_p)

tukey_dist <- make_tukey_df(
  aov_obj = p2_aov,
  term_name = "veg_en",
  y_positions = c(28.5, 31.0, 33.5)
)

p_dist <- ggplot(df2, aes(x = veg_en, y = distance1, fill = veg_en)) +
  geom_boxplot(
    width = 0.55,
    color = "black",
    outlier.shape = NA,
    linewidth = 0.55
  ) +
  geom_jitter(
    shape = 21,
    color = "black",
    size = 2.8,
    width = 0.10,
    alpha = 0.90,
    stroke = 0.35
  ) +
  scale_fill_grey(start = 0.88, end = 0.35) +
  labs(
    x = NULL,
    y = "Distance to\ncentroid (m)"
  ) +
  ggpubr::stat_pvalue_manual(
    data = tukey_dist,
    label = "p.adj.signif",
    xmin = "group1",
    xmax = "group2",
    y.position = "y.position",
    tip.length = 0.01,
    bracket.size = 0.45,
    size = FS_TUKEY,
    family = "Arial",
    hide.ns = FALSE,
    inherit.aes = FALSE
  ) +
  theme_boxplot_panel() +
  coord_cartesian(clip = "off") +
  scale_y_continuous(
    limits = c(2, 37),
    breaks = c(10, 20, 30),
    expand = expansion(mult = c(0.03, 0.08))
  )

p_dist <- add_positioned_label(
  plot_obj = p_dist,
  label_text = p2_label,
  x_pos = 2.45,
  y_pos = 6.0,
  hjust_val = 0,
  vjust_val = 0.5
)

# 8) Plot 3: OM vs distance ------------------------------------

cor_out <- cor.test(df2$om_pct, df2$distance1, method = "pearson")

r_val <- unname(cor_out$estimate)
p_val <- unname(cor_out$p.value)

cor_label <- paste0("r = ", sprintf("%.2f", r_val), p_stars(p_val))

p_scatter <- ggplot(df2, aes(x = distance1, y = om_pct)) +
  geom_point(
    shape = 21,
    fill = "grey75",
    color = "black",
    size = 2.8,
    alpha = 0.90,
    stroke = 0.35
  ) +
  geom_smooth(
    method = "lm",
    se = FALSE,
    color = "black",
    linewidth = 0.9
  ) +
  labs(
    x = "Distance to centroid (m)",
    y = "Organic matter\ncontent (%)"
  ) +
  theme_scatter_panel() +
  coord_cartesian(clip = "off") +
  scale_x_continuous(
    limits = c(2, 29.5),
    breaks = c(10, 20, 30),
    expand = expansion(mult = c(0.03, 0.03))
  ) +
  scale_y_continuous(
    limits = c(33, 68),
    breaks = c(40, 50, 60),
    expand = expansion(mult = c(0.03, 0.06))
  )

p_scatter <- add_positioned_label(
  plot_obj = p_scatter,
  label_text = cor_label,
  x_pos = 3.2,
  y_pos = 38.5,
  hjust_val = 0,
  vjust_val = 0.5
)

# 9) Save each plot separately ---------------------------------

save_plot_tif_pdf(
  plot_obj = p_om,
  tif_path = OUT_TIF_OM,
  pdf_path = OUT_PDF_OM,
  width_in = FIG_BOXPLOT_WIDTH_IN,
  height_in = FIG_BOXPLOT_HEIGHT_IN
)

save_plot_tif_pdf(
  plot_obj = p_dist,
  tif_path = OUT_TIF_DIST,
  pdf_path = OUT_PDF_DIST,
  width_in = FIG_BOXPLOT_WIDTH_IN,
  height_in = FIG_BOXPLOT_HEIGHT_IN
)

save_plot_tif_pdf(
  plot_obj = p_scatter,
  tif_path = OUT_TIF_SCATTER,
  pdf_path = OUT_PDF_SCATTER,
  width_in = FIG_SCATTER_WIDTH_IN,
  height_in = FIG_SCATTER_HEIGHT_IN
)

# 10) Print each plot in separate independent windows -----------

open_independent_plot_window(FIG_BOXPLOT_WIDTH_IN, FIG_BOXPLOT_HEIGHT_IN)
print(p_om)

open_independent_plot_window(FIG_BOXPLOT_WIDTH_IN, FIG_BOXPLOT_HEIGHT_IN)
print(p_dist)

open_independent_plot_window(FIG_SCATTER_WIDTH_IN, FIG_SCATTER_HEIGHT_IN)
print(p_scatter)

cat("\nSaved files:\n")
cat(" - ", normalizePath(OUT_TIF_OM, winslash = "/"), "\n", sep = "")
cat(" - ", normalizePath(OUT_PDF_OM, winslash = "/"), "\n", sep = "")
cat(" - ", normalizePath(OUT_TIF_DIST, winslash = "/"), "\n", sep = "")
cat(" - ", normalizePath(OUT_PDF_DIST, winslash = "/"), "\n", sep = "")
cat(" - ", normalizePath(OUT_TIF_SCATTER, winslash = "/"), "\n", sep = "")
cat(" - ", normalizePath(OUT_PDF_SCATTER, winslash = "/"), "\n", sep = "")















