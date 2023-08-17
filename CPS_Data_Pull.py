'''
What is the Current Population Survey (CPS)?

    The Current Population Survey (CPS), sponsored jointly by the U.S. Census Bureau and the U.S. Bureau of Labor Statistics (BLS),
is the primary source of labor force statistics for the population of the United States.
https://www.census.gov/programs-surveys/cps.html


Why are we briniging this in?

    The CPS is what the BLS primarily bases their data releases off of. The BLS API is (at least currently) very bad.
Thus, we can use the source data and get monthly releases of semi-official BLS data. Additionally, CPS data
allows us to look at state level by a bunch of cool demographics.



What are you bringing in?
    This pull is primarily interested with bringing in state level CLF data with demographic fields that align with 
Workforce Profile Demographic data. For a full list of variables that can be brought in, though, refer to this link:
https://api.census.gov/data/2021/cps/basic/jan/variables.html


Below is the list of what we're bringing in and what it all means

Variable | Definition | Suggested Weight
PREMPNOT | Employment Status | PWCMPWGT
PRCIVLF | In Civilian Labor Force  | PWCMPWGT
PRTAGE | Age | PWSSWGT
PESEX | Sex | PWSSWGT
PTDTRACE | Race | PWSSWGT
PEHSPNON | Hispanic | PWSSWGT
PRDISFLG | Disability | PWCMPWGT
PEEDUCA | Education | PWSSWGT
PEAFEVER | Veteran | PWVETWGT
PWCMPWGT | Person Weight | NA
HWHHWGT | Household Weight | NA
PWSSWGT | Weight-second stage weight (rake 6 final step weight) | NA

Appendix:

What is weighting?
https://www.census.gov/programs-surveys/cps/technical-documentation/methodology/weighting.html

'''

import pandas as pd
import numpy as np
import datetime


#Config Items
month_list = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
              'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

min_year = 2021


'''
API data comes in as random numbers which we have to translate into something useful

What follows are the dicts to do that
'''

PREMPNOT_remap = {
      "-1": None, #"In Universe, Met No Conditions To Assign",
      "4": "Not in labor force", #"Other Not in labor force (NILF)",
      "3": "Not in labor force", #"Discouraged-Not in labor force (NILF)",
      "2": "Unemployed",
      "1": "Employed"
    }

PRCIVLF_remap = {
      "-1": None, #"In Universe, Met No Conditions To Assign",
      "2": "Not In Civilian Labor Force",
      "1": "In Civilian Labor Force"
    }

PESEX_remap = {
      "2": "Female",
      "1": "Male"
    }

#Page 26
#https://www2.census.gov/programs-surveys/cps/datasets/2021/march/asec2021_ddl_pub_full.pdf
#This is being changed to the NFC definition of race
PTDTRACE_remap = {
      "07": "American Indian, Alaskan Native", #"White-AI",
      "20": "Two or More Races", #"W-AI-HP",
      "08": "Asian", #"White-Asian",
      "17": "Two or More Races", #"W-B-A",
      "16": "Two or More Races", #"W-B-AI",
      "06": "Black or African American", #"White-Black",
      "12": "Two or More Races", #"Black-HP",
      "18": "Two or More Races", #"W-B-HP",
      "21": "Two or More Races", #"W-A-HP",
      "02": "Black or African American", #"Black only",
      "05": "Native Hawaiian and Other Pacific Islander", #"Hawaiian/Pacific Islander Only",
      "22": "Two or More Races", #"B-AI-A",
      "09": "Native Hawaiian and Other Pacific Islander", #"White-HP",
      "14": "Two or More Races", #"AI-HP",
      "10": "Two or More Races", #"Black-AI",
      "23": "Two or More Races", #"W-B-AI-A",
      "11": "Two or More Races", #"Black-Asian",
      "13": "Two or More Races", #"AI-Asian",
      "04": "Asian", #"Asian only",
      "15": "Two or More Races", #"Asian-HP",
      "25": "Two or More Races", #"Other 3 Race Combinations",
      "01": "White", #"White only",
      "26": "Two or More Races", #"Other 4 and 5 Race Combinations",
      "19": "Two or More Races", #"W-AI-A",
      "24": "Two or More Races", #"W-AI-A-HP",
      "03": "American Indian or Alaskan Native" #"American Indian, Alaskan Native Only"
    }

PEHSPNON_remap = {
      "1": "Hispanic",
      "2": "Non-Hispanic"
    }

PRDISFLG_remap = {
      "2": "No Disability", #"No",
      "-1": None, #"Not in Universe",
      "1": "Disabled" #"Yes"
    }

PEEDUCA_remap = {
      "46": "Doctorate Degree", #"DOCTORATE DEGREE(EX:PhD,EdD)",
      "33": "Less than High School", #"5th Or 6th Grade",
      "44": "Masters or Professional Degree", #"MASTER'S DEGREE(EX:MA,MS,MEng,MEd,MSW)",
      "39": "High School", #"High School Grad-Diploma Or Equiv (ged)",
      "42": "Less than Bachelors", #"Associate Deg.-Academic Program",
      "31": "Less than High School", #"Less Than 1st Grade",
      "38": "Less than High School", #"12th Grade No Diploma",
      "40": "Less than Bachelors", #"Some College But No Degree",
      "-1": None, #"Not in Universe",
      "32": "Less than High School", #"1st,2nd,3rd Or 4th Grade",
      "43": "Bachelors degree", #"Bachelor's Degree(ex:ba,ab,bs)",
      "37": "Less than High School", #"11th Grade",
      "45": "Masters or Professional Degree", #"Professional School Deg(ex:md,dds,dvm)",
      "36": "Less than High School", #"10th Grade",
      "35": "Less than High School", #"9th Grade",
      "34": "Less than High School", #"7th Or 8th Grade",
      "41": "Less than Bachelors" #"Associate Degree-Occupational/Vocationl"
    }

PEAFEVER_remap = {
      "2": "Non-Veteran", #"No",
      "1": "Veteran", #"Yes",
      '-1': None
    }


def clean_data(df):
    
    
    df['date'] = pd.to_datetime(df['date'])
    
    #Convert our person weight to numeric
    df['PWCMPWGT'] = pd.to_numeric(df['PWCMPWGT'])
    
    #Make our age group column
    df['PRTAGE'] = pd.to_numeric(df['PRTAGE'])
    df['Age_Group'] = np.where(df['PRTAGE'] <= 20, '0-20', np.NaN)
    df['Age_Group'] = np.where(df['PRTAGE'].between(21, 30, inclusive= 'both'), '21-30', df['Age_Group'])
    df['Age_Group'] = np.where(df['PRTAGE'].between(31, 40, inclusive= 'both'), '31-40', df['Age_Group'])
    df['Age_Group'] = np.where(df['PRTAGE'].between(41, 50, inclusive= 'both'), '41-50', df['Age_Group'])
    df['Age_Group'] = np.where(df['PRTAGE'].between(51, 60, inclusive= 'both'), '51-60', df['Age_Group'])
    df['Age_Group'] = np.where(df['PRTAGE'].between(61, 70, inclusive= 'both'), '61-70', df['Age_Group'])
    df['Age_Group'] = np.where(df['PRTAGE'] >= 71, '71+', df['Age_Group'])

    #Man, why you look so serious. We gotta bounce this out. REMAP!!!
    #https://www.youtube.com/watch?v=J0Wgz7auLAk&ab_channel=JuanLaFonta
    
    
    df['PREMPNOT'] = df['PREMPNOT'].replace(PREMPNOT_remap)
    df['PRCIVLF'] = df['PRCIVLF'].replace(PRCIVLF_remap)
    df['PTDTRACE'] = (df['PTDTRACE'].str.pad(width=2, side='left', fillchar= '0')).replace(PTDTRACE_remap)
    df['PEHSPNON'] = df['PEHSPNON'].replace(PEHSPNON_remap)
    df['PRDISFLG'] = df['PRDISFLG'].replace(PRDISFLG_remap)
    df['PEEDUCA'] = df['PEEDUCA'].replace(PEEDUCA_remap)
    df['PEAFEVER'] = df['PEAFEVER'].replace(PEAFEVER_remap)
    df['PESEX'] = df['PESEX'].replace(PESEX_remap)
    
    
    df = df.groupby(['Age_Group', 'state', 'PREMPNOT', 'PRCIVLF', 'PESEX',
                     'PTDTRACE', 'PEHSPNON', 'date',
                     'PRDISFLG', 'PEEDUCA', 'PEAFEVER'])['PWCMPWGT'].sum().reset_index(drop=False)


    df = df[['date', 'state', 'PESEX', 'PTDTRACE', 'PEHSPNON', 'Age_Group', 'PRDISFLG',
             'PEEDUCA', 'PEAFEVER', 'PREMPNOT', 'PRCIVLF', 'PWCMPWGT']]

    df.columns = ['Date', 'State_Code', 'Sex', 'Race', 'Hispanic', 'Age_Group', 
                  'Disability_Status', 'Education_Group', 'Veteran_Status',
                  'Employment_Status', 'Labor_Force_Status', 'Number_of_Persons']


    #Round since we can't have partial persons
    df['Number_of_Persons'] = df['Number_of_Persons'].round(0)

    return(df)


#Fill in da blanks
def historical_pull():
    print("idk")



#Function for pulling the last month
#I assume this is what we will default to 
def present_pull():
    last_month  = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
    month_name = month_list[last_month.month - 1]
    year = last_month.year

    #Pull for last month's data
    sub_api = pd.read_json(f"https://api.census.gov/data/{year}/cps/basic/{month_name}?get=PREMPNOT,PRCIVLF,PRTAGE,PESEX,PTDTRACE,PEHSPNON,PRDISFLG,PEEDUCA,PEAFEVER,PWCMPWGT&for=state:*")

    sub_api.columns = sub_api.iloc[0]
    sub_api = sub_api.drop(0, axis=0)
    
    sub_api['date'] = last_month.replace(day=1)
    
    return(sub_api)


#Pull the data for the last month
df = present_pull()

#Clean said data
df = clean_data(df)


df.to_csv(r'/Users/jackogozaly/Desktop/Python_Directory/CPS_Labor_Force.csv', index=False)
