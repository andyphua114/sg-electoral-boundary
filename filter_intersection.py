def filter_polygons(geo_df):

    gdf_filtered = geo_df[geo_df.geometry.type != "GeometryCollection"]

    return gdf_filtered
