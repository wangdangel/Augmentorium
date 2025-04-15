# data_analysis.R
library(dplyr)
library(ggplot2)
library(readr)

# Import third-party packages
library(tidyverse)
library(caret)
library(randomForest)

# Load and prepare data
data <- read_csv("data/sales.csv")

# Data preprocessing
clean_data <- data %>%
  filter(!is.na(revenue)) %>%
  mutate(
    date = as.Date(date),
    month = format(date, "%m"),
    year = format(date, "%Y")
  ) %>%
  group_by(year, month) %>%
  summarise(
    total_revenue = sum(revenue),
    average_order = mean(order_value),
    count = n()
  )

# Create visualization
ggplot(clean_data, aes(x = month, y = total_revenue, group = year, color = year)) +
  geom_line() +
  theme_minimal() +
  labs(title = "Monthly Revenue by Year", x = "Month", y = "Total Revenue")