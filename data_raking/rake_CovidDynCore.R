library('anesrake')
library('weights')
library('forcats')

# read census data
census = read.csv("../data/ACS_DemHousingEst2018ACS_2018_censusEstimate.csv")
# read covid-dyn core sample
dat = read.csv("../data/Rake_coreDem.csv")
# output directory
outdir = paste(getwd(), "/rake_output/", sep ='')

# census data includes all states and federal US data -> taking federal data
US_idx = length(census$percente_male)

## AGE ##
# CORE SAMPLE
# age brackets matching census data
dat$agecats <- cut(dat$age, c(15, 19, 24,29,34,39, 33, 49, 54, 59, 64, 69, 99)) 
# age bracket labels
levels(dat$agecats) <- c("age15_19","age20_24", "age25_29", "age30_34","age35_39", 
                         "age40_44", "age45_49","age50_54","age55_59","age60_64", 
                         "age65_69", "age70_100") 
# collapse all ages >60
dat$agecats <-fct_collapse(dat$agecats, age60_100 = c("age60_64","age65_69", "age70_100"))
# collapse 15-19 and 20-24
dat$agecats <-fct_collapse(dat$agecats, age18_24 = c("age15_19","age20_24"))
dat$agecats <- as.factor(dat$agecats)

# TARGET
agetarg <- c(census$precent_total_age_20to24[US_idx],
             census$precent_total_age_25to29[US_idx],
             census$precent_total_age_30to34[US_idx],
             census$precent_total_age_35to39[US_idx],
             census$precent_total_age_40to44[US_idx],
             census$precent_total_age_45to49[US_idx],
             census$precent_total_age_50to54[US_idx],
             census$precent_total_age_55to59[US_idx],
             census$precent_total_age_60to64[US_idx]+ census$precent_total_age_65to69[US_idx]+
               census$precent_total_age_70to74[US_idx]+ census$precent_total_age_75to79[US_idx]+ 
               census$precent_total_age_80to84[US_idx]+ census$precent_total_age_85andOver[US_idx])

names(agetarg) <- levels(dat$agecats)

## SEX ##
# SAMPLE
dat$sex <- as.factor(dat$sex)

# TARGET
sextarg <- c(census$percente_male[US_idx],census$percente_female[US_idx])
names(sextarg) <- c("male","female")

## ETHNICITY ## 
# SAMPLE
# randomly sample values for NaN responses in ethnicity
dat$ethnicity[dat$ethnicity == "Prefer not to disclose"] =  sample(c("Hispanic or Latino","Not Hispanic or Latino"), replace =T,size=sum(dat$ethnicity == "Prefer not to disclose"))
dat$ethnicity <- as.factor(dat$ethnicity)


# TARGET
ethtarg <-c(census$percent_HispOrLat[US_idx],census$percent_NotHispOrLat[US_idx])
names(ethtarg) <- c("Hispanic or Latino","Not Hispanic or Latino")

## race
# SAMPLE
dat$race <- as.factor(dat$race)
# race: Native American/ Alaska Native, Pacific Islander, prefer not to disclose, other, and Multiracial
# have less than 5% in the sample -> collapse
dat$race <-fct_collapse(dat$race, Native_PacIsl_MultiRace_NaN_Other = c("American Indian/Alaska Native", 
                                                              "Native Hawaiian or Other Pacific Islander",
                                                              "Prefer not to disclose", "Other", "Multiracial"))
# TARGET
# factors: more than one race, white, black, asian; collapse native american, pacific islander and other
racetarg <-c(census$percent_oneRace_white[US_idx],
             census$percent_oneRace_black[US_idx], 
             census$percent_oneRace_asian[US_idx],
             census$percent_more1race[US_idx]+census$percent_oneRace_nativeAm[US_idx]+ census$percent_oneRace_pacificIsl[US_idx] + census$percent_oneRace_other[US_idx])
names(racetarg) <-c( "White", "Black", "Asian", "Native_PacIsl_MultiRace_NaN_Other")

# combine demographic categories for raking  
dat$caseid <- 1:length(dat$age)
targets <- list(agetarg, sextarg,ethtarg, racetarg)
names(targets) <- c( "agecats","sex","ethnicity", "race")

## RAKE ##
outsave <- anesrake(targets, dat, caseid=dat$caseid, verbose=TRUE)
rake_summary = summary(outsave)

## SAVE OUTPUT ##
# add weights to data
dat$rake_weights <- outsave$weightvec
row.names(dat)<-NULL
write.csv(dat,paste(outdir,"raked_data.csv",sep=''), row.names = TRUE)


# save race results
rake_race = as.data.frame(rake_summary$race)   
rake_race = round(rake_race,3)
write.csv(rake_race,paste(outdir,"rake_race.csv",sep=''), row.names = TRUE)

# save ethnicity results
rake_eth = as.data.frame(rake_summary$ethnicity)   
rake_eth = round(rake_eth,3)
write.csv(rake_eth,paste(outdir,"rake_ethnicity.csv",sep=''), row.names = TRUE)             

# save sex results
rake_sex = as.data.frame(rake_summary$sex)   
rake_sex = round(rake_sex,3)
write.csv(rake_sex,paste(outdir,"rake_sex.csv",sep=''), row.names = TRUE)      

# save age results
rake_age = as.data.frame(rake_summary$age)   
rake_age = round(rake_age,3)
write.csv(rake_age,paste(outdir,"rake_age.csv",sep=''), row.names = TRUE) 
