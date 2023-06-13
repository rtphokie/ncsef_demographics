import unittest

import pandas as pd

filename = 'NCSEF_2023_demographic_raw.xlsx'

from ncsef_regional_demographics import getschools, get_child_fair_normalized_regional_data, \
    school_pop_and_race, get_school_type, fairs_by_county_pop, \
    get_longitude, fairs_by_race_by_county
from NCmap import NCPlot
from pprint import pprint


class MapTests(unittest.TestCase):
    def test_ncmap_fairs(self):
        df_m = fairs_by_county_pop()
        NCPlot(df_m, "fairs per 5k students", plot_local_fairs=True, outputfile='images/fairs_per_5k.png', dpi=600)

    def test_ncmap_gender(self):
        df_population, df_race_all = school_pop_and_race()
        df_race_ncsef = fairs_by_race_by_county()

        # female representation all counties
        NCPlot(df_race_ncsef, 'Female', plot_local_fairs=True, outputfile=f'images/female_representation.png',
               missingcolor='red', cmap='RdYlGn', dpi=200, labelcolorthreshold=40)

        # female representation counties with fairs
        df = get_child_fair_normalized_regional_data(year=2023)
        df = df.drop_duplicates(subset='County', keep="first")
        df = df.County
        df_race_ncsef_partipant_counties = pd.merge(df_race_ncsef, df, on=['County'])
        NCPlot(df_race_ncsef_partipant_counties, 'Female', plot_local_fairs=True,
               outputfile=f'images/female_representation_faircounties.png',
               missingcolor='grey', cmap='RdYlGn', dpi=200, labelcolorthreshold=40)

    def test_ncmap_race(self):
        df_population, df_race_all = school_pop_and_race()
        df_race_ncsef = fairs_by_race_by_county()
        for race in ['INDIAN', 'HISPANIC', 'BLACK', 'WHITE', 'ASIAN']:
            NCPlot(df_race_ncsef, race, plot_local_fairs=True, outputfile=f'images/{race.lower()}_representation.png',
                   missingcolor='black', cmap='coolwarm', dpi=200, labelcolorthreshold=50)


class DataTests(unittest.TestCase):

    def test_school_couty(self):
        df_m = fairs_by_county_pop()
        print(df_m)

    def test_racemap(selfp):
        df_population, df_race = school_pop_and_race()
        print(df_race)

    def test_participating_school_char(self):
        df = get_child_fair_normalized_regional_data(year=2023)
        df = df.drop_duplicates(subset='child fair', keep="first")
        print(df.shape)
        # for col in df.columns:
        #     print(col)
        df = df[['child fair', 'SchoolType']]
        df_SchoolType_fairs = df.groupby(['SchoolType'])['SchoolType'].size().reset_index(name='fairs')
        print(df_SchoolType_fairs)

        sc = getschools()
        df_schools = pd.DataFrame.from_dict(dict(sc), orient='index')
        # print(df_schools)
        df_SchoolType_all = df_schools.groupby(['SchoolType'])['SchoolType'].size().reset_index(name='fairs')
        print(df_SchoolType_all)

    def test_get_fair_coords(self):
        df = get_child_fair_normalized_regional_data(year=2023)
        df = df.drop_duplicates(subset='child fair', keep="first")
        df['SchoolType'] = df.apply(get_school_type, axis=1)
        df['longitude'] = df.apply(get_longitude, axis=1)
        # df['latitude'] = df.apply(get_latitude, axis=1)
        df = df[['child fair', 'SchoolType', 'latitude', 'longitude']]
        print(df.head)

        # jkl = get_school_lng(row[''])

        # groceries.plot(marker='*', color='green', markersize=5);

    #
    # # Check crs
    # groceries = groceries.to_crs(chicago.crs)

    def test_county_demo(self):
        df_pop, df_race = school_pop_and_race()
        df_reg = get_child_fair_normalized_regional_data(year=2023)
        child_fairs = df_reg['child fair'].unique()
        self.assertGreaterEqual(len(child_fairs), 239)

    def test_county_demo_const(self):
        df_pop, df_race = school_pop_and_race()
        self.assertAlmostEqual(df_race[df_race['County'] == 'Robeson']['INDIAN pct'].iloc[0], 38.385, 3)

    def test_school_list(self):
        dict_schools = getschools()

        self.assertTrue('Wescare Christian Academy (Montgomery)' in dict_schools.keys())
        self.assertEqual(dict_schools['Wescare Christian Academy (Montgomery)']['SchoolType'], 'Religious')

        self.assertTrue('Salem Middle (Wake)' in dict_schools.keys())
        self.assertEqual(dict_schools['Salem Middle (Wake)']['SchoolType'], 'Public')
        self.assertEqual(len(dict_schools['Salem Middle (Wake)']['others']), 0)

        self.assertTrue('Salem Elementary (Wake)' in dict_schools.keys())
        self.assertEqual(len(dict_schools['Salem Elementary (Wake)']['others']), 1)

        self.assertTrue('Cherokee High (Cherokee)' in dict_schools.keys())
        self.assertEqual(dict_schools['Cherokee High (Cherokee)']['SchoolType'], 'Federal')
        self.assertEqual(len(dict_schools['Cherokee High (Cherokee)']['others']), 0)

    # def test_ind(self):
    #     row = {'CHILD FAIR': 'Goldsboro High School (Wayne)'}
    #     foo = normalize_child_fair(row)
    #     print(row)
    #     print(foo)
    #
    # def test_normalize_school_names_in_regional_data(self):
    #     df = get_child_fair_normalized_regional_data(year=2023)
    #     df = df[['PROJECT_NAME', 'PROJECT NUMBER', 'DIVISION', 'ASSIGNED CATEGORY', 'CHILD FAIR',
    #              'NAME OF YOUR SCHOOL', 'child fair', 'County', 'region'
    #              ]]
    #     local_fairs = df['child fair'].unique()
    #     print(len(local_fairs))
    #     try:
    #         file = open('schools', 'rb')
    #         schools = pickle.load(file)
    #         file.close()
    #     except:
    #         schools = getschools()
    #     for fair in local_fairs:
    #         if fair not in schools.keys():
    #             print(fair, 'not found')
    #         else:
    #             if 'longitude' not in schools[fair].keys():
    #                 print(fair)
    #                 schools[fair]['longitude'] = geocode_longitude(schools[fair]['address'])
    #                 schools[fair]['latitude'] = geocode_latitude(schools[fair]['address'])
    #     file = open('schools', 'wb')
    #     pickle.dump(schools, file)
    #     file.close()


if __name__ == '__main__':
    unittest.main()
