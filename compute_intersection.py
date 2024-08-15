import geopandas as gpd
from shapely.geometry import shape
from shapely.affinity import scale


def compute_intersect(gdf_all, gdf_single, constituency):
    # get the interesection areas between the two selection years

    scale_intersect_idx = []
    for idx, row in gdf_all.iterrows():
        if gdf_all.iloc[idx].ED_DESC != constituency:
            scaled_gdf_single = gdf_single.copy()
            scaled_gdf_single["geometry"] = scaled_gdf_single["geometry"].apply(
                lambda x: scale(x, xfact=0.31, yfact=0.31, origin="centroid")
            )
            if (
                gdf_all.iloc[idx : idx + 1]
                .reset_index()
                .intersects(scaled_gdf_single.reset_index())
                .bool()
            ):
                scale_intersect_idx.append(idx)

    intersect_idx = []
    for idx, row in gdf_all.iterrows():
        if gdf_all.iloc[idx].ED_DESC != constituency:
            if (
                gdf_all.iloc[idx : idx + 1]
                .reset_index()
                .intersects(gdf_single.reset_index())
                .bool()
            ):
                intersect_idx.append(idx)

    intersect_polygon = []
    ed_desc = []

    for i in intersect_idx:
        intersect_polygon.append(
            gdf_single.geometry.intersection(gdf_all.iloc[i].geometry).values[0]
        )
        ed_desc.append(gdf_all.iloc[i].ED_DESC)

    return scale_intersect_idx, intersect_polygon, ed_desc
