import pandas as pd
import requests_cache

from ncsef_regional_demographics import fairs_by_county_pop, get_child_fair_normalized_regional_data

s = requests_cache.CachedSession('geocache')

import pickle
import matplotlib.pyplot as plt
import geopandas
from ncsef_regional_demographics import get_latitude, get_longitude


def NCPlot():
    fig = plt.figure(1, figsize=(16, 9))
    ax = fig.add_subplot()

    df_m = fairs_by_county_pop()
    print(df_m['fairs per 5k students'].median(skipna=True))
    return
    df_fairs = get_child_fair_normalized_regional_data(year=2023)
    df_fairs = df_fairs.drop_duplicates(subset='child fair', keep="first")
    df_fairs = df_fairs[['child fair', 'longitude', 'latitude']]
    df_fairs['longitude'] = df_fairs.apply(get_longitude, axis=1)
    df_fairs['latitude'] = df_fairs.apply(get_latitude, axis=1)
    df_fairs['size']=1
    df_fairs.dropna(inplace=True)
    try:
        file = open('nc_geopandas', 'rb')
        ncmap = pickle.load(file)
        file.close()
        print('from cache')
    except Exception as e:
        print(f'redoing {e}')
        name = 'North_Carolina_State_and_County_Boundary_Polygons'
        ncmap = geopandas.read_file(f'{name}/{name}.shp')
        ncmap = ncmap.to_crs("EPSG:3395")

        file = open('nc_geopandas', 'wb')
        pickle.dump(ncmap, file)
        file.close()
    df = ncmap.merge(df_m, on='County', how='left')
    gdf = geopandas.GeoDataFrame(geometry=geopandas.points_from_xy(df_fairs.longitude, df_fairs.latitude),
                                 crs="EPSG:4326")
    gdf = gdf.to_crs(ncmap.crs)

    base = df.plot(ax=ax, column="fairs per 5k students", cmap='YlGnBu', edgecolor= 'black',
                   missing_kwds={"color": "grey", "edgecolor": "black", "alpha": 0.1},
                   legend=False,
                   legend_kwds={"label": "Population in 2010", "orientation": "horizontal"},
                   )
    gdf.plot(ax=base, color='r', zorder=1, markersize=2)
    df.apply(lambda x: ax.annotate(text=x.County, xy=x.geometry.centroid.coords[0], ha='center', fontsize=6, color='grey'), axis=1)

    gdf.boundary.plot(ax=ax, color='Black', linewidth=5)
    # https://matplotlib.org/tutorials/colors/colormaps.html
    plt.axis('off')
    # plt.rcParams['savefig.dpi'] = 600
    plt.rcParams['savefig.dpi'] = 200
    plt.savefig('images/fig1.png', bbox_inches='tight')
