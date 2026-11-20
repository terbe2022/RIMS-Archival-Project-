# gam_richness_v4.R  -- Rafael Quintero, April 2020
# Rarefied richness ~ s(age) + (1|site), offset log(bowl_days)
library(mgcv); library(dplyr)
d <- read.csv("../data/processed/richness_by_site_year.csv")
d$age_c <- pmin(d$years_since_restoration, 40)     # remnant coded as 40
m_all  <- gam(richness ~ s(age_c, k = 5) + s(site, bs = "re"), data = d, family = poisson)
m_spec <- gam(specialist_richness ~ s(age_c, k = 5) + s(site, bs = "re"), data = d, family = poisson)
m_noBRF <- update(m_spec, data = subset(d, site != "BRF"))   # Reviewer 1 sensitivity analysis
summary(m_all); summary(m_spec); summary(m_noBRF)
png("../figures/fig1_richness_age.png", 1200, 800, res = 200); plot(m_all, shade = TRUE); dev.off()
