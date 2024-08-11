import geopandas as gpd
import pandas as pd
from bs4 import BeautifulSoup

# function to extract electoral name from description column in raw data
def ed_desc(x):
    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(x, 'lxml')

    # Find the <td> element that follows the <th> element with text 'ED_DESC'
    return soup.find('th', string='ED_DESC').find_next_sibling('td').text.strip()

def process():
  # Load GeoJSON data
  # exclude 2020 first as it has different column structure
  year = ["2006", "2011", "2015"]

  for idx, y in enumerate(year):
      if idx == 0:
          raw_gdf = gpd.read_file("data/ElectoralBoundary{}GEOJSON.geojson".format(str(y))).to_crs(4326)
          raw_gdf['year'] = y
      else:
          temp_gdf = gpd.read_file("data/ElectoralBoundary{}GEOJSON.geojson".format(str(y))).to_crs(4326)
          temp_gdf['year'] = y
          raw_gdf = pd.concat([raw_gdf, temp_gdf], axis=0)

  raw_gdf['ED_DESC'] = raw_gdf['Description'].apply(ed_desc)

  gdf = raw_gdf[['year', 'ED_DESC','geometry']].copy()

  # process 2020 data
  raw_gdf_2020 = gpd.read_file("data/ElectoralBoundary{}GEOJSON.geojson".format(str(2020))).to_crs(4326)
  raw_gdf_2020['year'] = "2020"

  gdf_2020 = raw_gdf_2020[['year','ED_DESC','geometry']].copy()

  # combine to get overall data
  gdf = pd.concat([gdf, gdf_2020], axis=0)

  gdf['ED_DESC'] = gdf['ED_DESC'].str.replace(" - ", "-").str.replace("-", " - ")

  # load constituency data; such as GRC/SMC, voting results
  constituency_df = pd.read_csv("data/constituency_info_2006to2020.csv")
  constituency_df['year'] = constituency_df['year'].astype(str)

  gdf = gdf.merge(constituency_df, how='left', on=['year','ED_DESC'])

  return gdf