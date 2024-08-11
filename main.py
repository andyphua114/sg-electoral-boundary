import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.features import GeoJsonPopup, GeoJsonTooltip
import geopandas as gpd

from data_processing import process

gdf = process()

st.set_page_config(layout="wide")
st.title('Electoral Boundary')

chosen_year = st.selectbox(
    "Select the year as baseline",
    (gdf['year'].unique()),
    index=None,
)


compare_year = st.selectbox(
    "Select the year for comparison",
    (gdf['year'].unique()),
    index=None
)


if chosen_year and compare_year:

  compare_type = st.radio("Select type of comparison",
                          ["Static Year vs Year", "Changes Year over Year"])

  constituency_list = sorted(gdf['ED_DESC'].unique().tolist())

  # Initialize session state for selected constituency if not already set
  if 'selected_constituency' not in st.session_state:
    st.session_state.selected_constituency = None

  # Ensure the selected value is in the updated list
  if st.session_state.selected_constituency not in constituency_list:
    st.session_state.selected_constituency = None
 
  constituency = st.selectbox(
      "Select the desired constituency",
      (constituency_list),
      index=constituency_list.index(st.session_state.selected_constituency) if st.session_state.selected_constituency in constituency_list else None
  )

  # Store the selected constituency in session state
  st.session_state.selected_constituency = constituency

  if constituency:

    # AREAS THAT WERE REMOVED
    gdf_chosen = gdf[(gdf['year'] == chosen_year) & (gdf['ED_DESC'] == constituency)].copy().reset_index(drop=True)
    gdf_compare = gdf[(gdf['year'] == compare_year)].copy().reset_index(drop=True)

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

    # convert to geodataframe
    intersected_gpd = gpd.GeoDataFrame({'ED_DESC':ed_desc, 'geometry':intersect_polygon}, crs="4326")
    # get constituency info
    intersected_gpd = intersected_gpd.merge(gdf_compare[['year','ED_DESC','constituency_type','pax_number','result']], how='left', on=['ED_DESC'])

    # AREAS THAT WERE ADDED
    gdf_chosen_added = gdf[(gdf['year'] == compare_year) & (gdf['ED_DESC'] == constituency)].copy().reset_index(drop=True)

    if len(gdf_chosen_added) > 0:
      gdf_compare_added = gdf[(gdf['year'] == chosen_year)].copy().reset_index(drop=True)

      # get the interesection areas between the two selection years
      intersect_idx = []
      same_idx = None
      for idx, row in gdf_compare_added.iterrows():
          if gdf_compare_added.iloc[idx].ED_DESC != constituency:
              if gdf_compare_added.iloc[idx:idx+1].reset_index().intersects(gdf_chosen_added.reset_index()).bool():
                  intersect_idx.append(idx)

      intersect_polygon = []
      ed_desc = []

      for i in intersect_idx:
          intersect_polygon.append(gdf_chosen_added.geometry.intersection(gdf_compare_added.iloc[i].geometry).values[0])
          ed_desc.append(gdf_compare_added.iloc[i].ED_DESC)

      # convert to geodataframe
      intersected_gpd_added = gpd.GeoDataFrame({'ED_DESC':ed_desc, 'geometry':intersect_polygon}, crs="4326")
      # get constituency info
      intersected_gpd_added = intersected_gpd_added.merge(gdf_compare_added[['year','ED_DESC','constituency_type','pax_number','result']], how='left', on=['ED_DESC'])    

    #intersected_gpd.area
    col1, col2 = st.columns(2)

    with col1:
      if len(gdf_chosen) == 0:
        st.write("No such constituency in year {}".format(chosen_year))
      else:
        st.write("Electoral Boundaries for Year {}".format(chosen_year))
        m_chosen = folium.Map(
            location=[gdf_chosen.geometry.centroid.y.mean(), gdf_chosen.geometry.centroid.x.mean()],
            zoom_start=12,
            max_zoom=21)

        tooltip = GeoJsonTooltip(
            fields=["year", "ED_DESC", "constituency_type", "pax_number", "result"],
            #aliases=["State:", "2015 Median Income(USD):", "Median % Change:"],
            localize=True,
            sticky=True,
            labels=True,
            style="""
                background-color: #F0EFEF;
                border: 2px solid black;
                border-radius: 3px;
                box-shadow: 3px;
            """,
            max_width=300,
        )

        folium.GeoJson(gdf_chosen, tooltip=tooltip).add_to(m_chosen)

        st_folium(
            m_chosen,
            width=650,
            height=550,
            returned_objects=[],
            #feature_group_to_add=fg_dict[fg],
            #debug=True,
            #layer_control=layer_dict[layer],
            key='map1'
        )

    with col2:
      if compare_type == "Static Year vs Year":
        if len(gdf_chosen_added) == 0:
          st.write("No such constituency in year {}".format(compare_year))
        else:
          st.write("Electoral Boundaries for Year {}".format(compare_year))
          m = folium.Map(
              location=[gdf_chosen_added.geometry.centroid.y.mean(), gdf_chosen_added.geometry.centroid.x.mean()],
              zoom_start=12,
              max_zoom=21)

          tooltip = GeoJsonTooltip(
              fields=["year", "ED_DESC", "constituency_type", "pax_number", "result"],
              #aliases=["State:", "2015 Median Income(USD):", "Median % Change:"],
              localize=True,
              sticky=True,
              labels=True,
              style="""
                  background-color: #F0EFEF;
                  border: 2px solid black;
                  border-radius: 3px;
                  box-shadow: 3px;
              """,
              max_width=300,
          )

          folium.GeoJson(gdf_chosen_added, tooltip=tooltip).add_to(m)

          st_folium(
              m,
              width=650,
              height=550,
              returned_objects=[],
              #feature_group_to_add=fg_dict[fg],
              #debug=True,
              #layer_control=layer_dict[layer],
              key='map2.1'
          )         
         
      elif compare_type == "Changes Year over Year":
        if len(gdf_chosen) == 0:
          st.write("No such constituency in year {}. Hence no change comparison.".format(chosen_year))
        elif len(gdf_chosen_added) == 0:
          st.write("No such constituency in year {}. Hence no change comparison.".format(compare_year))
        else:
          st.write("Electoral Boundaries Changes from {} to {}".format(chosen_year, compare_year))
          m = folium.Map(
              location=[gdf_chosen.geometry.centroid.y.mean(), gdf_chosen.geometry.centroid.x.mean()],
              zoom_start=12,
              max_zoom=21)

          tooltip1 = GeoJsonTooltip(
              fields=["year", "ED_DESC", "constituency_type", "pax_number", "result"],
              #aliases=["State:", "2015 Median Income(USD):", "Median % Change:"],
              localize=True,
              sticky=True,
              labels=True,
              style="""
                  background-color: #F0EFEF;
                  border: 2px solid black;
                  border-radius: 3px;
                  box-shadow: 3px;
              """,
              max_width=300,
          )

          tooltip2 = GeoJsonTooltip(
              fields=["year", "ED_DESC", "constituency_type", "pax_number", "result"],
              #aliases=["State:", "2015 Median Income(USD):", "Median % Change:"],
              localize=True,
              sticky=True,
              labels=True,
              style="""
                  background-color: #F0EFEF;
                  border: 2px solid black;
                  border-radius: 3px;
                  box-shadow: 3px;
              """,
              max_width=300,
          )

          folium.GeoJson(intersected_gpd, tooltip=tooltip1, name='m1', color='red').add_to(m)

          if (len(gdf_chosen_added)) > 0:
            folium.GeoJson(intersected_gpd_added, tooltip=tooltip2, name='m2', color='green').add_to(m)
          

          st_folium(
              m,
              width=650,
              height=550,
              returned_objects=[],
              #feature_group_to_add=fg_dict[fg],
              #debug=True,
              #layer_control=layer_dict[layer],
              key='map2.2'
          )