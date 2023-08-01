import pandas as pd
import numpy as np

year_list = [2018, 2019, 2021] 


race = {
    "3": "American Indian alone",
    "1": "White alone",
    "8": "Some Other Race alone",
    "6": "Asian alone",
    "9": "Two or More Races",
    "2": "Black or African American alone",
    "4": "Alaska Native alone",
    "7": "Native Hawaiian and Other Pacific Islander alone",
    "5": "American Indian and Alaska Native tribes specified; or American Indian or Alaska Native, not specified and no other races"
    }

#Sex remap
sex = {
       "1": "Male",
       "2": "Female"
       }

#To do: condense this and replace col values
vps_map = {
      "03": "Gulf War: 9/2001 or later and Gulf War: 8/1990 - 8/2001 and Vietnam Era",
      "14": "Peacetime service before the Korean War only",
      "12": "Between Gulf War and Vietnam Era only",
      "13": "Between Vietnam Era and Korean War only",
      "04": "Gulf War: 8/1990 - 8/2001",
      "05": "Gulf War: 8/1990 - 8/2001 and Vietnam Era",
      "10": "Korean War and WWII",
      "02": "Gulf War: 9/2001 or later and Gulf War: 8/1990 - 8/2001",
      "08": "Vietnam Era, Korean War, and WWII",
      "01": "Gulf War: 9/2001 or later",
      "07": "Vietnam Era and Korean War",
      "11": "WWII",
      "06": "Vietnam Era",
      "09": "Korean War",
      "0": "N/A (less than 17 years old, no active duty)"
    }

#To do, condense this and replace col values
schl_map = {
      "16": "Regular high school diploma",
      "01": "No schooling completed",
      "04": "Grade 1",
      "03": "Kindergarten",
      "07": "Grade 4",
      "23": "Professional degree beyond a bachelor's degree",
      "19": "1 or more years of college credit, no degree",
      "22": "Master's degree",
      "10": "Grade 7",
      "20": "Associate's degree",
      "0": "N/A (less than 3 years old)",
      "02": "Nursery school, preschool",
      "21": "Bachelor's degree",
      "08": "Grade 5",
      "24": "Doctorate degree",
      "06": "Grade 3",
      "14": "Grade 11",
      "17": "GED or alternative credential",
      "12": "Grade 9",
      "15": "12th grade - no diploma",
      "13": "Grade 10",
      "05": "Grade 2",
      "11": "Grade 8",
      "18": "Some college, but less than 1 year",
      "09": "Grade 6"
    }

#Disability remap
disability = {
    "1": "With a disability",
    "2": "Without a disability"
    }


esr_map = {"5": "Armed Forces, With a Job But Not At Work",
"3": "Unemployed",
"6": "Not in Labor Force",
"1": "Civilian employed, at work",
"2": "Civilian employed, with a job but not at work",
"0": "N/A (less than 16 years old)",
"4": "Armed Forces, At Work"}


esr_clean_map = {
 "5": "Labor Force",
 "3": "Civilian Labor Force",
 "6": None,
 "1": "Civilian Labor Force",
 "2": "Civilian Labor Force",
 "0": None,
 "4": "Labor Force"}


acs_list = []

for year in year_list:

    print(year)
    sub_df = pd.read_json(f"https://api.census.gov/data/{year}/acs/acs5/pums?get=SEX,RAC1P,ESR,HISP,AGEP,DIS,SCHL,VPS,PWGTP&for=state:*")
    
    sub_df.columns = sub_df.iloc[0]
    sub_df = sub_df.drop(0, axis=0)
    
    sub_df['Year'] = year
    
    sub_df['AGEP'] = pd.to_numeric(sub_df['AGEP'])
    sub_df['Age_Group'] = np.where(sub_df['AGEP'] <= 20, '0-20', np.NaN)
    sub_df['Age_Group'] = np.where(sub_df['AGEP'].between(21, 30, inclusive= 'both'), '21-30', sub_df['Age_Group'])
    sub_df['Age_Group'] = np.where(sub_df['AGEP'].between(31, 40, inclusive= 'both'), '31-40', sub_df['Age_Group'])
    sub_df['Age_Group'] = np.where(sub_df['AGEP'].between(41, 50, inclusive= 'both'), '41-50', sub_df['Age_Group'])
    sub_df['Age_Group'] = np.where(sub_df['AGEP'].between(51, 60, inclusive= 'both'), '51-60', sub_df['Age_Group'])
    sub_df['Age_Group'] = np.where(sub_df['AGEP'].between(61, 70, inclusive= 'both'), '61-70', sub_df['Age_Group'])
    sub_df['Age_Group'] = np.where(sub_df['AGEP'] >= 71, '71+', sub_df['Age_Group'])
    
    
    
    #Remap our race column
    sub_df['RAC1P'] = sub_df['RAC1P'].replace(race)
    #Rework our hispanic column to be a binary Y/N instead of every type of hispanic
    sub_df['HISP'] = pd.to_numeric(sub_df['HISP'])
    sub_df['HISP'] = np.where(sub_df['HISP'] == 1, 'Not Spanish/Hispanic/Latino',
                            'Spanish/Hispanic/Latino')
    
    #Remap sex
    sub_df['SEX'] = sub_df['SEX'].replace(sex)
    
    #Remap ESR
    sub_df['ESR_clean'] = sub_df['ESR'].replace(esr_clean_map)
    
    #Remap ESR
    sub_df['ESR'] = sub_df['ESR'].replace(esr_map)
    
    #Remap disability
    sub_df['DIS'] = sub_df['DIS'].replace(disability)
    
    sub_df['PWGTP'] = pd.to_numeric(sub_df['PWGTP'])

    acs_list.append(sub_df)


tidy_df = pd.concat(acs_list)


tidy_df = sub_df.groupby(['SEX', 'RAC1P', 'ESR_clean', 'HISP', 'DIS',
                          'state', 'Year', 'SCHL', 'VPS',
                          'Age_Group'])['PWGTP'].sum().reset_index(drop=False)


tidy_df = tidy_df[tidy_df['ESR_clean'] == 'Civilian Labor Force']
tidy_df['state'] = pd.to_numeric(tidy_df['state'])


fips_map = pd.read_csv(r'https://gist.githubusercontent.com/dantonnoriega/bf1acd2290e15b91e6710b6fd3be0a53/raw/11d15233327c8080c9646c7e1f23052659db251d/us-state-ansi-fips.csv')
fips_map.columns = ['State_Name', 'state', 'state_abbreviation']


tidy_df = pd.merge(tidy_df, fips_map,
                   on = 'state',
                   how = 'left')


tidy_df.columns = ['sex', 'race', 'esr_clean', 'hispanic', 'disability_status',
                   'state_code', 'year','school', 'veteran_status', 'age_group', 'number_of_persons', 'state_name',
                   'state_abbreviation']


tidy_df = tidy_df[['state_name', 'year', 'sex', 'race', 'hispanic', 'disability_status', 'school', 'veteran_status',
                   'age_group', 'number_of_persons', 'state_code', 'state_abbreviation'
                   ]]


schl_map = {
      "16": "High School",
      "01": "Less than High School",
      "04": "Less than High School",
      "03": "Less than High School",
      "07": "Less than High School",
      "23": "Masters or Professional Degree",
      "19": "Less than Bachelors",
      "22": "Masters or Professional Degree",
      "10": "Less than High School",
      "20": "Less than Bachelors",
      "0": "Less than High School",
      "02": "Less than High School",
      "21": "Bachelors degree",
      "08": "Less than High School",
      "24": "Doctorate Degree",
      "06": "Less than High School",
      "14": "Less than High School",
      "17": "High School",
      "12": "Less than High School",
      "15": "Less than High School",
      "13": "Less than High School",
      "05": "Less than High School",
      "11": "Less than High School",
      "18": "Less than Bachelors",
      "09": "Less than High School"
    }



tidy_df['school'] = tidy_df['school'].astype(str).str.pad(2, side= "left", fillchar = "0")
tidy_df['veteran_status'] = np.where(tidy_df['veteran_status'] != "0", "Veteran", "Non-Veteran")
tidy_df['school'] = tidy_df['school'].replace(schl_map)


tidy_df = tidy_df.groupby(['state_name', 'year', 'sex', 'race', 'hispanic', 'disability_status', 'school', 'veteran_status',
                   'age_group', 'state_code', 'state_abbreviation'])['number_of_persons'].sum().reset_index(drop=False)

data_2020 = tidy_df[tidy_df['year'].isin([2019, 2021])]


data_2020 = data_2020.groupby(['state_name', 'year', 'sex', 'race', 'hispanic', 'disability_status', 'school', 'veteran_status',
                   'age_group', 'state_code', 'state_abbreviation'])['number_of_persons'].mean().reset_index(drop=False)


data_2020['year'] = 2020


tidy_df = pd.concat([tidy_df, data_2020])


