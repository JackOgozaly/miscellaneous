
import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup
import numpy as np


current_year = datetime.date.today().year

min_year = 2018
root_url = 'https://www.opm.gov/policy-data-oversight/pay-leave/salaries-wages/'
report = '/locality-pay-area-definitions/'

location_df_list = []

for i in range((current_year - min_year) + 1):
    
    #Construct our URL for that year
    year = min_year + i
    URL = f"{root_url}{year}{report}"
    
    #Grab HTML
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    
    #Find all table names
    results = soup.find_all(['h3', 'h4'])

    all_locations = []
    
    for result in results:
        all_locations.append(result.text.strip())
        
    #Remove the first two since they're irrelevant for us
    all_locations = all_locations[2:]

    #Find the list of locations for that year
    location = soup.find_all('div', class_= 'TwoColContainer')
    location = [location.text.strip() for location in location]
    location = '\n'.join(location)
    location =  location.splitlines()
    location = list(filter(None, location))
    
    
    #Basically what happens is if a pay location is just one unique state area
    #It's just presented as that table, But say our pay location overlaps with another
    #pay location in that state or into another state, then the the counties are split
    #Over many tables but on our end we want to group them. What we do here is just that.
    #Find table names that are fine and remove ones that are dupes and will throw off
    #Our assignment
    location_df = pd.DataFrame(all_locations, columns = ['location'])
    location_df["ref_index"] = range(0, 0 + len(location_df))
    pay_locations = [i for i, e in enumerate(all_locations) if e in location]
    location_df['pay_location'] = np.where(location_df['ref_index'].isin(pay_locations),
                                           location_df['location'],
                                           None)
    location_df['pay_location']  = location_df['pay_location'].ffill()

    no_table = location_df.groupby(['pay_location']).ref_index.count().reset_index(drop=False)
    no_table = no_table[no_table['ref_index'] > 1]
    dataframe_names = location_df[~location_df['location'].isin(no_table['pay_location'])]
    dataframe_names = list(dataframe_names['location'])
    
    
    #Grab every table from that webpage
    url_list = pd.read_html(page.text, converters={'FIPS': str})

    #Empty list to put our cleaned dataframes
    filtered_dataframes = []

    #Location counter
    i = 0
    for df in url_list:
        # Check if all desired column names are present in the DataFrame
        if all(col in df.columns for col in ['PLACE NAME', 'FIPS']):
            #Add our location to these rows            
            df['location'] = dataframe_names[i]
            #Append to our list
            filtered_dataframes.append(df)
            #Update our counter
            i+=1


    df1 = pd.concat(filtered_dataframes)

    df1 = pd.merge(df1, location_df,
                   how = "left",
                   on = 'location')
    
    df1 = df1.drop(['ref_index'], axis = 1)


    df1['Year'] = year
    
    location_df_list.append(df1)
    

df = pd.concat(location_df_list)
df.columns = ['Location', 'FIPS', 'Region', 'Pay_Region', 'Year']

df['FIPS'] = df['FIPS'].str.pad(width=5, fillchar = '0', side= 'right')

df['state_code'] = df['FIPS'].str[:2]
df['county_code'] = df['FIPS'].str[2:]

