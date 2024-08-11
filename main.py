import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.features import GeoJsonPopup, GeoJsonTooltip
import geopandas as gpd

from data_processing import process
from compute_intersection import compute_intersect

gdf = process()

st.set_page_config(layout="wide")
st.title('Electoral Boundary')

# year selection for baseline reference
chosen_year = st.selectbox(
    "Select the year as baseline",
    (gdf['year'].unique()),
    index=None,
)

# year selection for comparison against baseline reference
compare_year = st.selectbox(
    "Select the year for comparison",
    (gdf['year'].unique()),
    index=None
)


if chosen_year and compare_year:

  # choose between display boundaries year vs year,
  # or display the changes from baseline reference in second map
  compare_type = st.radio("Select type of comparison",
                          ["Static Year vs Year", "Changes Year over Year"],
                          horizontal=True)

  constituency_list = sorted(gdf['ED_DESC'].unique().tolist())

  # Initialize session state for selected constituency if not already set
  if 'selected_constituency' not in st.session_state:
    st.session_state.selected_constituency = None

  # Ensure the selected value is in the updated list
  if st.session_state.selected_constituency not in constituency_list:
    st.session_state.selected_constituency = None
 
  # select the constituency
  constituency = st.selectbox(
      "Select the desired constituency",
      (constituency_list),
      index=constituency_list.index(st.session_state.selected_constituency) if st.session_state.selected_constituency in constituency_list else None
  )

  # Store the selected constituency in session state
  st.session_state.selected_constituency = constituency

  if constituency:

    # map setting
    map = {"StreetMap":"OpenStreetMap", "Grayscale":"CartoDB positron"}
    map_setting = st.radio("Select type of map",
                          ["StreetMap", "Grayscale"],
                          index=0,
                          horizontal=True
                          )

    map_chosen = map[map_setting]

    # COMPUTE AREAS THAT WERE REMOVED (from baseline reference year)
    gdf_chosen = gdf[(gdf['year'] == chosen_year) & (gdf['ED_DESC'] == constituency)].copy().reset_index(drop=True)
    gdf_compare = gdf[(gdf['year'] == compare_year)].copy().reset_index(drop=True)

    if len(gdf_chosen) > 0:
      intersect_polygon, ed_desc = compute_intersect(gdf_compare, gdf_chosen, constituency)

      # convert to geodataframe
      intersected_gpd = gpd.GeoDataFrame({'ED_DESC':ed_desc, 'geometry':intersect_polygon}, crs="4326")
      # get constituency info
      intersected_gpd = intersected_gpd.merge(gdf_compare[['year','ED_DESC','constituency_type','pax_number','result']], how='left', on=['ED_DESC'])

    # AREAS THAT WERE ADDED (to baseline reference year to get compare year boundary)
    gdf_chosen_added = gdf[(gdf['year'] == compare_year) & (gdf['ED_DESC'] == constituency)].copy().reset_index(drop=True)

    if len(gdf_chosen_added) > 0:
      gdf_compare_added = gdf[(gdf['year'] == chosen_year)].copy().reset_index(drop=True)

      intersect_polygon, ed_desc = compute_intersect(gdf_compare_added, gdf_chosen_added, constituency)

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
            max_zoom=21,
            tiles=map_chosen  # Use a greyscale tile layer
        )

        tooltip = GeoJsonTooltip(
            fields=["year", "ED_DESC", "constituency_type", "pax_number", "result"],
            aliases=["Year: ","ED: ","Type: ", "Pax: ", "Result: "],
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
              max_zoom=21,
              tiles=map_chosen)

          tooltip = GeoJsonTooltip(
              fields=["year", "ED_DESC", "constituency_type", "pax_number", "result"],
              aliases=["Year: ","ED: ","Type: ", "Pax: ", "Result: "],
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
              max_zoom=21,
              tiles=map_chosen)

          tooltip1 = GeoJsonTooltip(
              fields=["year", "ED_DESC", "constituency_type", "pax_number", "result"],
              aliases=["Year: ","ED: ","Type: ", "Pax: ", "Result: "],
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
              aliases=["Year: ","ED: ","Type: ", "Pax: ", "Result: "],
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