import geopandas as gpd

def compute_intersect(gdf_compare, gdf_chosen, constituency):
     # get the interesection areas between the two selection years
      intersect_idx = []
      same_idx = None
      for idx, row in gdf_compare.iterrows():
          if gdf_compare.iloc[idx].ED_DESC != constituency:
              if gdf_compare.iloc[idx:idx+1].reset_index().intersects(gdf_chosen.reset_index()).bool():
                  intersect_idx.append(idx)

      intersect_polygon = []
      ed_desc = []

      for i in intersect_idx:
          intersect_polygon.append(gdf_chosen.geometry.intersection(gdf_compare.iloc[i].geometry).values[0])
          ed_desc.append(gdf_compare.iloc[i].ED_DESC)

      return intersect_polygon, ed_desc
