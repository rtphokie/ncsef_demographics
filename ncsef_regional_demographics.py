import os
import pickle
import re
from difflib import SequenceMatcher

import pandas as pd
import requests_cache

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.options.display.width = 9999

rex = re.compile(r'\W+')
article_words = ['the ', ' ', ' at ', ' IB ']
sl = None

s = requests_cache.CachedSession('httpscache')


def read_school_lists(geocode=False):
    df = pd.read_csv('rawdata/ncdpi/Current Open Private Schools - October 04, 2022.csv', encoding='iso-8859-1')
    df_priv = df[['SchoolName', 'Street', 'City', 'State', 'Zip', 'County', 'SchoolType']].copy()
    df_priv['Official School Name'] = df_priv['SchoolName']
    df_priv.rename(columns={
        'SchoolName': 'School Name',
    }, inplace=True)
    df = pd.read_csv('rawdata/ncdpi/eddie_nc_schools_list.csv', encoding='iso-8859-1')
    df_pub = df[['LEA Name',
                 'Address Line1',
                 'City',
                 'State',
                 'Grade Level Current',
                 'Zip Code 5',
                 'County Description',
                 'School Designation Desc',
                 'Official School Name',
                 'School Name']].copy()
    df_pub.rename(columns={
        'Address Line1': 'Street',
        'Zip Code 5': 'Zip',
        'School Designation Desc': 'SchoolType',
        'County Description': 'County',
    }, inplace=True)
    df2 = pd.concat([df_priv, df_pub])
    df2['address'] = df2['Street'].map(str) + ', ' + df2['City'].map(str) + ', ' + df2['State'].map(str) + ' ' + \
                     df2['Zip'].map(str)
    df2.set_index('School Name')

    return df2


def geocode_address(address):
    url = f'http://api.positionstack.com/v1/forward?access_key=41a52893fc1c7bed592c22a044b3bfcd&query={address}'
    longitude = None
    latitude = None
    county = None
    try:
        file = open('geocode_address.pickle', 'rb')
        d = pickle.load(file)
        file.close()
    except Exception as e:
        d = {}
    if address not in d.keys():
        try:
            r = s.get(url)
            data = r.json()
            d[address] = data
            file = open('geocode_address.pickle', 'wb')
            pickle.dump(d, file)
            file.close()
        except:
            print(f"could not geocode {address}")
    else:
        data = d[address]
    longitude = data['data'][0]['longitude']
    latitude = data['data'][0]['latitude']
    county = data['data'][0]['county']
    return latitude, longitude


def get_child_fair_normalized_regional_data(year=2023):
    try:
        # raise
        file = open('regional_data', 'rb')
        df = pickle.load(file)
        file.close()
        unique_fairs = len(df['child fair'].unique())
        if unique_fairs > 250:
            print(f"{unique_fairs} fairs found, normaliing")
            raise Exception(f"{unique_fairs} fairs found, normaliing")
    except:
        df = get_regional_data()
        print("normalizing school names")
        df['child fair'] = df.apply(normalize_child_fair, axis=1)
        print("normalizing school counties and types")
        df['County'] = df.apply(get_school_county, axis=1)
        df['SchoolType'] = df.apply(get_school_type, axis=1)
        print("geolocating schools")
        df['longitude'] = df.apply(get_longitude, axis=1)
        df['latitude'] = df.apply(get_latitude, axis=1)

        file = open('regional_data', 'wb')
        pickle.dump(df, file)
        file.close()
    return df


def get_regional_data(year=2023, df=None):
    dfs = []
    for root, dirs, files in os.walk(f"rawdata/{year}", topdown=False):
        if 'state' in root.lower() or root == 'rawdata/2023':
            continue
        atoms = root.split('/')
        region = atoms[-1].replace('2023 Region', '').strip()
        for filename in files:
            if '~' in filename:
                continue
            if 'student' in filename.lower():
                dfthis = pd.read_excel(f"{root}/{filename}")
                dfthis['region'] = region
                if 'COUNTY OF HOME RESIDENCE' in dfthis.columns:
                    dfthis['County'] = dfthis['COUNTY OF HOME RESIDENCE']
                    dfthis.drop(columns=['COUNTY OF HOME RESIDENCE'])
                dfs.append(dfthis.copy())
    df = pd.concat(dfs, ignore_index=True)
    # df['CHILD FAIR'] = df['CHILD FAIR'].apply(normalize_child_fair)
    # for attr in ['TYPE OF SCHOOL:', 'region', 'CHILD FAIR']:
    #     print()
    #     print(attr,'-'*20)
    #     foo=df.groupby(by=[attr])[attr].count()
    #     print(foo)
    return df


def getschools():
    df_schools = read_school_lists()
    schooldata = {}
    schoolnamemap = {}
    for n, row in df_schools.iterrows():
        key = f"{row['School Name']} ({row['County']})".replace(' School', '')
        if row['School Name'] not in schoolnamemap:
            schoolnamemap[row['School Name']] = []
        if key in schooldata:
            raise ValueError(f"a value for {key} already found")
        schooldata[key] = dict(row)
        schooldata[key]['key'] = key
        schoolnamemap[row['School Name']].append(key)

    # note schools with the same name
    for k, v in schooldata.items():
        v['others'] = schoolnamemap[v['School Name']].copy()
        schooldata[k]['others'].remove(k)

    return schooldata


def get_longitude(row, columnname='child fair'):
    d = get_school_details(row, columnname='child fair', geocode=True)
    return d['longitude']


def get_latitude(row, columnname='child fair'):
    d = get_school_details(row, columnname='child fair', geocode=True)
    return d['latitude']


def get_school_type(row, columnname='child fair'):
    d = get_school_details(row, columnname='child fair')
    return d['SchoolType']


def get_school_county(row, columnname='child fair'):
    d = get_school_details(row, columnname='child fair')
    return d['County']


def get_school_details(row, columnname='child fair', geocode=False):
    name = row[columnname]
    global sl
    if sl is None:
        sl = getschools()
    if name in sl.keys():
        if geocode and 'latitude' not in sl[name].keys():
            if name == 'Johnsonville Elementary (Harnett)':  # compensating for errors from geocoding service
                sl[name]['latitude'] = 35.3003442
                sl[name]['longitude'] = -79.0983509
            elif name == 'Macon Middle (Macon)':
                sl[name]['latitude'] = 35.1611022
                sl[name]['longitude'] = -83.3604421
            elif name == 'Shoals Elementary (Surry)':
                sl[name]['latitude'] = 36.333182
                sl[name]['longitude'] = -80.5062663
            elif name == 'Western Rockingham Middle (Rockingham)':
                sl[name]['latitude'] = 36.4023186
                sl[name]['longitude'] = -79.9813976
            elif name == 'John W Dillard Academy (Rockingham)':
                sl[name]['latitude'] = 36.3991173
                sl[name]['longitude'] = -79.9804079
            elif name == 'Huntsville Elementary (Rockingham)':
                sl[name]['latitude'] = 36.330923
                sl[name]['longitude'] = -79.949532
            elif name == 'Heyward C Bellamy Elem (New Hanover)':
                sl[name]['latitude'] = 34.1230024
                sl[name]['longitude'] = -77.9113507
            elif name == 'Manteo Middle (Dare)':  # compensating for errors from geocoding service
                sl[name]['latitude'] = 35.9202705
                sl[name]['longitude'] = -75.680876
            elif name == 'Warren County High (Warren)':  # compensating for errors from geocoding service
                sl[name]['latitude'] = 36.4324177
                sl[name]['longitude'] = -78.1681031
            else:
                sl[name]['latitude'], sl[name]['longitude'] = geocode_address(sl[name]['address'])
        # if round(sl[name]['latitude'],2) == 35.86:
        #     print(name, round(sl[name]['latitude'], 2), round(sl[name]['longitude'], 2))
        #     return {'County': 'unknown', 'SchoolType': 'unknown', 'latitude': None, 'longitude': None}
        # else:
        return sl[name]
    else:
        return {'County': 'unknown', 'SchoolType': 'unknown', 'latitude': None, 'longitude': None}


def normalize_child_fair(row, columnname='CHILD FAIR'):
    name = row[columnname]
    if type(name) is str and '(Wake County)' in name:
        for city in ['Raleigh', 'Cary', 'Wake Forest']:
            name = name.replace(f'{city} (Wake County)', city)
    global sl
    if sl is None:
        sl = getschools()
    school_list = sl

    if type(name) is not str or name == 'nan':  # nothing to go on
        result = 'unknown'
    elif name == 'Lenoir County' or name == 'raleigh' or name == 'NC CENTRAL REGION 3A SCIENCE AND ENGINEERING FAIR':  # not enough to go on
        result = 'unknown'
    elif name == 'Goldsboro High School - Goldsboro':
        result = 'Goldsboro High (Wayne)'
    elif name == 'John W Dillard Elementary - Madison':
        result = 'John W Dillard Academy (Rockingham)'
    elif name == 'Central Elementary - Eden':
        result = 'Central Elementary (Rockingham)'
    elif name == 'Olds Elementary - Raleigh (Wake County)':
        result = 'Olds Elementary (Wake)'
    elif 'home school' in name.lower():
        result = 'home school'
    elif name not in school_list.keys():
        result = 'unknown'
        name_normalized = normalize_name(name)

        name_possible, location = get_possiblename(name)
        name_possible_normalized = normalize_name(name_possible)

        for k, v in school_list.items():
            k_official = v['Official School Name'].lower()
            k_normalized = normalize_name(k)
            if name_normalized in k_normalized:
                pass
            if name_possible_normalized in k_normalized:
                pass
            if name_normalized in k_normalized or \
                    name_normalized in k_official or \
                    name_possible_normalized in k_normalized or \
                    name_possible_normalized in k_official:
                if len(v['others']) == 0 or \
                        location.lower() in (v['City'].lower(), v['County'].lower()):
                    # there's only one school by this name in the state
                    if result == 'unknown':
                        # first find
                        result = k
                    elif location.lower() in (v['City'].lower(), v['County'].lower()):
                        # strong correlation with county or city mentioned
                        result = k
                    else:
                        this_find = SequenceMatcher(None, name, k).ratio()
                        prev_find = SequenceMatcher(None, result, k).ratio()
                        if this_find > prev_find:
                            result = k
                        else:
                            pass
                            # print(f"warning keeping prev result for '{name}'")
                            # print(f" this:   {this_find:.4f} {k}")
                            # print(f" prev:   {prev_find:.4f} {result}")
                            # print(f" county: {v['County']}")
                            # print(f" city:   {v['City']}")
                            # print()

    return result


def normalize_name(name):
    normalized_name = name.replace('&', 'and').replace(' School', '').replace(' school', '').replace('-', ' ').replace(
        '.', ' ')
    normalized_name = school_name_individual_fixes(normalized_name)
    normalized_name = school_name_pattern_fixes(normalized_name)
    return normalized_name.strip().lower()


def get_possiblename(s):
    atoms = s.split(' - ')
    if len(atoms) > 1:
        location = atoms[-1].lower()
        s2 = " ".join(atoms[:-1])
        for word in article_words:
            s2 = s2.lower().replace(word.lower(), ' ')  # remove dashes, articles
        s2 = rex.sub(' ', s2).strip()  # collapse whitespace
    else:
        s2 = s
        location = ''

    return s2, location


def school_name_pattern_fixes(normalized_name):
    result = re.search(r"([\.\-\'\w\s]+) - ([\w\s]+) \(([\w\s]+)\)", normalized_name)
    if result:
        normalized_name = f"{result.group(1)} ({result.group(3).replace(' County', '')})"
    result = re.search(r"([\.\'\w\s]+)[,\-] ([\w\s]+) County", normalized_name)
    if result:
        normalized_name = f"{result.group(1)} ({result.group(2).replace(' County', '')})"
    result = re.search(r"^(\w) (.*)", normalized_name)
    if result:
        normalized_name = f"{result.group(1)}. {result.group(2)}"
    normalized_name = normalized_name.strip()
    normalized_name = re.sub(' +', ' ', normalized_name.strip())
    return normalized_name


def school_name_individual_fixes(normalized_name):
    map = {
        'Raleigh (Wake County)': '(Wake)',
        'Cary (Wake County)': '(Wake)',
        'Wake Forest (Wake County)': '(Wake)',
        'Accademy': 'Academy',  # mispelling
        'Atkins Academic and Technology High': 'Atkins Academic and Tech High',
        # official name includes Tech not Technology
        'UNC-G Early/Middle College High': 'UNCG Early/Middle College',  # hyphenation
        'Elem': 'Elementary',  # normalize elementary
        'Elementaryentary': 'Elementary',  # normalize elementary
        # 'Piedmont IB Middle': 'Piedmont Middle School', # International Bacholareat not part of the name
        'Brawley Middle': 'Brawley',
        'Barringer Academic': 'Charles H. Parker Academic',
        'Brooks Global Studies': 'Brooks Global Elementary',
        'Moncure Elementary': 'Moncure',
        'Surry Early College HS Design': 'Surry Early College',
        'John W Dillard Elementary': 'John W Dillard Academy',
        'Hanes Middle': 'Hanes Magnet',
        ' Primary': ' Elementary',
        ' Middl ': ' Middle',
        'Isaac Bear Early College HS': 'Isaac M Bear Early College High School',
        ' ECHS': ' Early College High',
        'Central Middle - Dobson': 'Nash Central Middle (Nash)',
        'Codington Elementary': 'Dr John Codington Elem',
        'Western Middle - Elon': 'Western Alamance Middle (Alamance)',
        'Meadowview Middle': 'Meadowview Magnet Middle',
        'Bethany Community Middle': 'Bethany Community',
        'The Academy at Lincoln': 'Lincoln Academy',
        '- Rocky Mount (Nash-Rocky Mt County)': '(Nash)',
        'Central Elementary - Eden': 'Central Elementary (Rockingham)',

    }
    for before, after in map.items():
        normalized_name = normalized_name.replace(before, after)
    return normalized_name.strip()


def school_pop_and_race():
    # NC Dep Pub Instruction metrics on Race and Sex
    df = pd.read_excel('rawdata/ncdpi/Pupils_by_Race_and_Sex.xlsx')
    df.drop(['Year', 'LEA'], axis=1, inplace=True)

    df_race = df.drop_duplicates().groupby('County', sort=False, as_index=False).sum()
    df_race['Male cnt'] = 0
    df_race['Female cnt'] = 0
    df_race.drop(['____LEA Name____'], axis=1, inplace=True)
    for race in ['INDIAN', 'ASIAN', 'HISPANIC', 'BLACK', 'WHITE', 'TWO OR MORE', 'PACIFIC ISLAND']:
        df_race[f"{race} cnt"] = df_race[f"{race} Male"] + df_race[f"{race} Female"]
        df_race[f"{race} pct"] = df_race[f"{race} cnt"] / df_race['Total']
        for gender in ['Male', 'Female']:
            df_race[f"{gender} cnt"] = df_race[f"{race} {gender}"] + df_race[f"{gender} cnt"]
            df_race[f"{gender} pct"] = df_race[f"{gender} cnt"] / df_race['Total']
            df_race.drop([f"{race} {gender}"], axis=1, inplace=True)
    df_race['altotal'] = df_race['Male cnt'] + df_race['Female cnt']
    for column in df_race.columns:
        if ' pct' in column:
            df_race[column]=df_race[column]*100
        if ' cnt' in column:
            df_race.drop([column], axis=1, inplace=True)

    df_nonpub = pd.read_csv('rawdata/ncdpi/nonpublic_populations_2022.txt')

    df_population = pd.concat([df_race[['County', 'Total']], df_nonpub])
    df_population = df_population.drop_duplicates().groupby('County', sort=False, as_index=False).sum()
    return df_population, df_race


def fairs_by_county_pop():
    df = get_child_fair_normalized_regional_data(year=2023)
    df = df.drop_duplicates(subset='child fair', keep="first")
    print(df[df.County == 'Dare']['child fair'])
    df_county = df.groupby(['County'])['County'].size().reset_index(name='fairs')
    df_pop, df_race = school_pop_and_race()
    df_m = pd.merge(df_pop, df_county, on=['County'])
    df_m.rename(columns={"Total": "students"}, inplace=True)
    df_m['fairs per 5k students'] = df_m.students / df_m.fairs / 5000
    return df_m
