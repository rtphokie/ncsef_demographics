import random

import numpy as np
import requests_cache

from ncsef_regional_demographics import fairs_by_county_pop, get_child_fair_normalized_regional_data

s = requests_cache.CachedSession('geocache')

import pickle
import matplotlib.pyplot as plt
import geopandas
from ncsef_regional_demographics import get_latitude, get_longitude


def NCPlot(df_m, column, plot_local_fairs=True, outputfile="images/fig1.png",
           label_counties=True, label_fairs=False, dpi=200, labelcolorthreshold=.5,
           missingcolor='#808080', missingedge='#585858', cmap='Blues', hatch='////'):
    fig = plt.figure(1, figsize=(16, 9))
    ax = fig.add_subplot()


    if plot_local_fairs:
        df_fairs = get_child_fair_normalized_regional_data(year=2023)
        df_fairs = df_fairs.drop_duplicates(subset='child fair', keep="first")
        df_fairs = df_fairs[['child fair', 'longitude', 'latitude']]
        df_fairs['longitude'] = df_fairs.apply(get_longitude, axis=1)
        df_fairs['latitude'] = df_fairs.apply(get_latitude, axis=1)
        df_fairs['size'] = 1
        df_fairs.dropna(inplace=True)
    try:
        file = open('nc_geopandas.cache', 'rb')
        ncmap = pickle.load(file)
        file.close()
    except Exception as e:
        print(f'redoing {e}')
        name = 'North_Carolina_State_and_County_Boundary_Polygons'
        ncmap = geopandas.read_file(f'{name}/{name}.shp')
        ncmap = ncmap.to_crs("EPSG:3395")
        file = open('nc_geopandas.cache', 'wb')
        pickle.dump(ncmap, file)
        file.close()
    df = ncmap.merge(df_m, on='County', how='left')

    base = df.plot(ax=ax, column=column, cmap=cmap, edgecolor='black',
                   missing_kwds={"color": missingcolor, "edgecolor": missingedge, "hatch": hatch},
                   legend=True, legend_kwds={"label": f"NCSEF 2023 {column}", "orientation": "horizontal"},
                   )
    if label_counties:
        if cmap in ['coolwarm', 'RdYlGn']: # diverging colormaps
            df.apply( lambda x: ax.annotate(text=x.County, zorder=5, xy=x.geometry.centroid.coords[0], ha='center', fontsize=6, color='black'), axis=1)
            df[df[column] > labelcolorthreshold].apply( lambda x: ax.annotate(text=x.County, zorder=5, xy=x.geometry.centroid.coords[0], ha='center', fontsize=6, color='white'), axis=1)
            df[df[column] < labelcolorthreshold*-1].apply( lambda x: ax.annotate(text=x.County, zorder=5, xy=x.geometry.centroid.coords[0], ha='center', fontsize=6, color='white'), axis=1)
            # df[df[column] <= 20 & df[column] >= -20].apply( lambda x: ax.annotate(text=x.County, zorder=5, xy=x.geometry.centroid.coords[0], ha='center', fontsize=6, color='black'), axis=1)
        else:
            df[df[column] > 0].apply( lambda x: ax.annotate(text=x.County, zorder=5, xy=x.geometry.centroid.coords[0], ha='center', fontsize=6, color='#383838'), axis=1)
            df[df[column] > df[column].max() * labelcolorthreshold].apply( lambda x: ax.annotate(text=x.County, zorder=5, xy=x.geometry.centroid.coords[0], ha='center', fontsize=6, color='white'), axis=1)
        df[df[column].isna()].apply( lambda x: ax.annotate(text=x.County, zorder=5, xy=x.geometry.centroid.coords[0], ha='center', fontsize=6, color='#D3D3D3'), axis=1)

    if plot_local_fairs:
        gdf = geopandas.GeoDataFrame(geometry=geopandas.points_from_xy(df_fairs.longitude, df_fairs.latitude), crs="EPSG:4326")
        gdf = gdf.to_crs(ncmap.crs)
        gdf.plot(ax=base, color='r', zorder=1, markersize=2)
        gdf.boundary.plot(ax=ax, color='Black', linewidth=5)
        if label_fairs:
            for x, y, label in zip(gdf.geometry.x, gdf.geometry.y, df_fairs['child fair']):
                ax.annotate(label, xy=(x, y), xytext=(random.randint(1,5), random.randint(1,5)), textcoords="offset points", fontsize=2)

    plt.axis('off')
    plt.rcParams['savefig.dpi'] = dpi
    plt.savefig(outputfile, bbox_inches='tight')
    print(f"wrote {outputfile} for {column} metrics")
