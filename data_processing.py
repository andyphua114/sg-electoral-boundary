import geopandas as gpd
import pandas as pd
from bs4 import BeautifulSoup


# function to extract electoral name from description column in raw data
def ed_desc(x):
    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(x, "lxml")

    # Find the <td> element that follows the <th> element with text 'ED_DESC'
    return soup.find("th", string="ED_DESC").find_next_sibling("td").text.strip()


def process():
    # Load GeoJSON data
    # exclude 2020 first as it has different column structure
    # 2006 to 2015 - 'Name', 'Description', 'geometry'
    year = ["2006", "2011", "2015"]

    for idx, y in enumerate(year):
        if idx == 0:
            raw_gdf = gpd.read_file(
                "data/ElectoralBoundary{}GEOJSON.geojson".format(str(y))
            ).to_crs(4326)
            raw_gdf["year"] = y
        else:
            temp_gdf = gpd.read_file(
                "data/ElectoralBoundary{}GEOJSON.geojson".format(str(y))
            ).to_crs(4326)
            temp_gdf["year"] = y
            raw_gdf = pd.concat([raw_gdf, temp_gdf], axis=0)

    raw_gdf["ED_DESC"] = raw_gdf["Description"].apply(ed_desc)

    gdf = raw_gdf[["year", "ED_DESC", "geometry"]].copy()

    # process 2020 data
    # 2020 - 'FID', 'ED_DESC', 'ED_CODE', 'geometry'
    raw_gdf_2020 = gpd.read_file(
        "data/ElectoralBoundary{}GEOJSON.geojson".format(str(2020))
    ).to_crs(4326)
    raw_gdf_2020["year"] = "2020"

    gdf_2020 = raw_gdf_2020[["year", "ED_DESC", "geometry"]].copy()

    # process 2025 data
    # 2025 - 'FID', 'ED_DESC', 'ED_DESC_FU', 'Name', 'NEW_ED', 'geometry'
    raw_gdf_2025 = gpd.read_file(
        "data/ElectoralBoundary{}GEOJSON.geojson".format(str(2025))
    ).to_crs(4326)
    raw_gdf_2025["year"] = "2025"

    gdf_2025 = raw_gdf_2025[["year", "ED_DESC", "geometry"]].copy()

    # combine to get overall data
    gdf = pd.concat([gdf, gdf_2020, gdf_2025], axis=0)

    gdf["ED_DESC"] = gdf["ED_DESC"].str.replace(" - ", "-").str.replace("-", " - ")

    # load constituency data; such as GRC/SMC, voting results
    constituency_df = pd.read_csv("data/constituency_info_2006to2020.csv")
    constituency_df["year"] = constituency_df["year"].astype(str)

    # 2025 does not have results yet - year,ED_DESC,constituency_type,pax_number,result
    constituency_2025_df = raw_gdf_2025[["year", "ED_DESC", "ED_DESC_FU"]].copy()
    constituency_df["year"] = constituency_df["year"].astype(str)
    constituency_2025_df["constituency_type"] = constituency_2025_df[
        "ED_DESC_FU"
    ].apply(lambda x: x.split(" ")[-1])
    constituency_2025_df["pax_number"] = "-"
    constituency_2025_df["result"] = "-"
    constituency_2025_df.drop("ED_DESC_FU", inplace=True, axis=1)

    constituency_2025_df["ED_DESC"] = (
        constituency_2025_df["ED_DESC"].str.replace(" - ", "-").str.replace("-", " - ")
    )

    constituency_df = pd.concat([constituency_df, constituency_2025_df], axis=0)

    gdf = gdf.merge(constituency_df, how="left", on=["year", "ED_DESC"])

    return gdf
