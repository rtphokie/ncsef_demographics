import pickle
import unittest

import pandas as pd

filename = 'NCSEF_2023_demographic_raw.xlsx'

from ncsef_regional_demographics import getschools, normalize_child_fair, \
    get_child_fair_normalized_regional_data, \
    school_pop_and_race, get_school_type, fairs_by_county_pop, \
    get_longitude, fairs_by_race_by_county
from NCmap import NCPlot
from pprint import pprint



def main():
    dpi=600
    df_m = fairs_by_county_pop()
    print("generating fairs per 5k students")
    NCPlot(df_m, "fairs per 5k students", plot_local_fairs=True, outputfile='images/fairs_per_5k.png', dpi=dpi)

    df_race_ncsef = fairs_by_race_by_county()
    for race in ['INDIAN', 'HISPANIC', 'BLACK', 'WHITE', 'ASIAN']:
        print(f"generating representation by race for {race} students")
        NCPlot(df_race_ncsef, race, plot_local_fairs=True, outputfile=f'images/{race.lower()}_representation.png',
               missingcolor='black', cmap='coolwarm', dpi=dpi, labelcolorthreshold=50)

    # female representation all counties
    print(f"generating female representation for all counties")
    NCPlot(df_race_ncsef, 'Female', plot_local_fairs=True, outputfile=f'images/female_representation.png',
           missingcolor='red', cmap='RdYlGn', dpi=dpi, labelcolorthreshold=40)

    # female representation counties with fairs
    df = get_child_fair_normalized_regional_data(year=2023)
    df = df.drop_duplicates(subset='County', keep="first")
    df = df.County
    df_race_ncsef_partipant_counties = pd.merge(df_race_ncsef, df, on=['County']) # filter out counties without fairs
    print(f"generating female representation for counties with local fairs")
    NCPlot(df_race_ncsef_partipant_counties, 'Female', plot_local_fairs=True,
           outputfile=f'images/female_representation_faircounties.png',
           missingcolor='grey', cmap='RdYlGn', dpi=dpi, labelcolorthreshold=40)



if __name__ == '__main__':
    main()
