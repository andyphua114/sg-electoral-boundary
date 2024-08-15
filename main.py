import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.features import GeoJsonPopup, GeoJsonTooltip
import geopandas as gpd

from data_processing import process
from compute_intersection import compute_intersect

gdf = process()


st.set_page_config(layout="wide")
st.title("Electoral Boundary")

st.write(
    "The delineation of electoral boundaries in Singapore, managed by the Electoral Boundaries Review Committee (EBRC), plays a crucial role in shaping the political landscape. While the government asserts that these boundaries are drawn to serve the interests of Singaporeans and ensure fair representation, the process has faced scrutiny, with some critics accusing it of being a form of gerrymandering—a tactic where boundaries are altered to favor certain political outcomes."
)
st.write(
    "This dashboard enables users to visualize and analyze changes in electoral boundaries across different election years, providing a tool to explore how shifts in voter distribution and constituency adjustments might impact electoral outcomes. Users can independently assess the implications of boundary changes and draw their own conclusions."
)

# year selection for baseline reference
baseline_year = st.selectbox(
    "Select the year as baseline",
    (gdf["year"].unique()),
    index=None,
)

# year selection for comparison against baseline reference
compare_year = st.selectbox(
    "Select the year for comparison", (gdf["year"].unique()), index=None
)


if baseline_year and compare_year:

    # choose between display boundaries year vs year,
    # or display the changes from baseline reference in second map
    help_text = (
        '"Full Map" enables visualization of all electoral boundaries across two election years\n\n'
        '"Constituency Year vs Year" enables visualization of a specified electorial division/constituency across two election years\n\n'
        '"Constituency Changes Year over Year" enables visualization of the changes in boundaries for a specified electorial division across two election years\n'
    )
    compare_type = st.radio(
        "Select type of comparison",
        [
            "Full Map",
            "Constituency Year vs Year",
            "Constituency Changes Year over Year",
        ],
        help=help_text,
        horizontal=True,
    )

    constituency_list = sorted(gdf["ED_DESC"].unique().tolist())

    if compare_type == "Full Map":
        constituency = None
    else:
        # select the constituency
        constituency = st.selectbox(
            "Select the desired constituency", (constituency_list), index=None
        )

    if compare_type == "Full Map" or constituency:

        # map setting
        map = {"StreetMap": "OpenStreetMap", "Grayscale": "CartoDB positron"}
        map_setting = st.radio(
            "Select type of map", ["Grayscale", "StreetMap"], index=0, horizontal=True
        )

        map_chosen = map[map_setting]

        gdf_baseline = (
            gdf[(gdf["year"] == baseline_year) & (gdf["ED_DESC"] == constituency)]
            .copy()
            .reset_index(drop=True)
        )
        gdf_compare_all = (
            gdf[(gdf["year"] == compare_year)].copy().reset_index(drop=True)
        )

        gdf_compare = (
            gdf[(gdf["year"] == compare_year) & (gdf["ED_DESC"] == constituency)]
            .copy()
            .reset_index(drop=True)
        )

        gdf_baseline_all = (
            gdf[(gdf["year"] == baseline_year)].copy().reset_index(drop=True)
        )

        # COMPUTE AREAS THAT WERE REMOVED (from baseline reference year)
        if len(gdf_baseline) > 0:
            scale_intersect_idx, intersect_polygon, ed_desc = compute_intersect(
                gdf_compare_all, gdf_baseline, constituency
            )

            # convert to geodataframe
            intersected_gpd = gpd.GeoDataFrame(
                {"ED_DESC": ed_desc, "geometry": intersect_polygon}, crs="4326"
            )

            # get constituency info
            intersected_gpd = intersected_gpd.merge(
                gdf_compare_all[
                    ["year", "ED_DESC", "constituency_type", "pax_number", "result"]
                ],
                how="left",
                on=["ED_DESC"],
            )
        else:
            # if the constituency does not exist in baseline year, we find the equivalence of the GRC/SMC
            scale_intersect_idx, intersect_polygon, ed_desc = compute_intersect(
                gdf_baseline_all, gdf_compare, constituency
            )
            # convert to geodataframe
            old_areas_gpd = gdf_baseline_all.iloc[scale_intersect_idx]

        # COMPUTE AREAS THAT WERE ADDED (to baseline reference year to get compare year boundary)
        if len(gdf_compare) > 0:
            scale_intersect_idx, intersect_polygon, ed_desc = compute_intersect(
                gdf_baseline_all, gdf_compare, constituency
            )

            # convert to geodataframe
            intersected_gpd_added = gpd.GeoDataFrame(
                {"ED_DESC": ed_desc, "geometry": intersect_polygon}, crs="4326"
            )

            # get constituency info
            intersected_gpd_added = intersected_gpd_added.merge(
                gdf_baseline_all[
                    ["year", "ED_DESC", "constituency_type", "pax_number", "result"]
                ],
                how="left",
                on=["ED_DESC"],
            )
        else:
            # if the constituency does not exist in baseline year, we find the equivalence of the GRC/SMC
            scale_intersect_idx, intersect_polygon, ed_desc = compute_intersect(
                gdf_compare_all, gdf_baseline, constituency
            )
            # convert to geodataframe
            new_areas_gpd = gdf_compare_all.iloc[scale_intersect_idx]

        # intersected_gpd.area
        col1, col2 = st.columns(2)

        with col1:
            if compare_type == "Constituency Year vs Year":
                if len(gdf_baseline) == 0 and len(gdf_compare) == 0:
                    st.write("No such constituency in year {}".format(baseline_year))
                elif len(gdf_baseline) == 0 and len(gdf_compare) > 0:
                    st.write(
                        "No such constituency in year {}. Showing the GRC/SMC that bounded the same area.".format(
                            baseline_year
                        )
                    )
                    m_chosen = folium.Map(
                        location=[
                            old_areas_gpd.geometry.centroid.y.mean(),
                            old_areas_gpd.geometry.centroid.x.mean(),
                        ],
                        zoom_start=12,
                        max_zoom=21,
                        tiles=map_chosen,  # Use a greyscale tile layer
                    )

                    tooltip = GeoJsonTooltip(
                        fields=[
                            "year",
                            "ED_DESC",
                            "constituency_type",
                            "pax_number",
                            "result",
                        ],
                        aliases=["Year: ", "ED: ", "Type: ", "Pax: ", "Result: "],
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

                    folium.GeoJson(old_areas_gpd, tooltip=tooltip).add_to(m_chosen)

                    st_folium(
                        m_chosen,
                        width=650,
                        height=550,
                        returned_objects=[],
                        # feature_group_to_add=fg_dict[fg],
                        # debug=True,
                        # layer_control=layer_dict[layer],
                        key="map1.1",
                    )
                else:
                    st.write("Electoral Boundaries for Year {}".format(baseline_year))
                    m_chosen = folium.Map(
                        location=[
                            gdf_baseline.geometry.centroid.y.mean(),
                            gdf_baseline.geometry.centroid.x.mean(),
                        ],
                        zoom_start=12,
                        max_zoom=21,
                        tiles=map_chosen,  # Use a greyscale tile layer
                    )

                    tooltip = GeoJsonTooltip(
                        fields=[
                            "year",
                            "ED_DESC",
                            "constituency_type",
                            "pax_number",
                            "result",
                        ],
                        aliases=["Year: ", "ED: ", "Type: ", "Pax: ", "Result: "],
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

                    folium.GeoJson(gdf_baseline, tooltip=tooltip).add_to(m_chosen)

                    st_folium(
                        m_chosen,
                        width=650,
                        height=550,
                        returned_objects=[],
                        # feature_group_to_add=fg_dict[fg],
                        # debug=True,
                        # layer_control=layer_dict[layer],
                        key="map1",
                    )
            elif compare_type == "Constituency Changes Year over Year":
                if len(gdf_baseline) == 0:
                    st.write("No such constituency in year {}.".format(baseline_year))
                elif len(gdf_baseline) > 0:  # and len(gdf_compare) == 0:
                    st.write("Electoral Boundaries for Year {}".format(baseline_year))
                    m = folium.Map(
                        location=[
                            gdf_baseline.geometry.centroid.y.mean(),
                            gdf_baseline.geometry.centroid.x.mean(),
                        ],
                        zoom_start=12,
                        max_zoom=21,
                        tiles=map_chosen,
                    )

                    tooltip = GeoJsonTooltip(
                        fields=[
                            "year",
                            "ED_DESC",
                            "constituency_type",
                            "pax_number",
                            "result",
                        ],
                        aliases=["Year: ", "ED: ", "Type: ", "Pax: ", "Result: "],
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

                    folium.GeoJson(gdf_baseline, tooltip=tooltip).add_to(m)

                    st_folium(
                        m,
                        width=650,
                        height=550,
                        returned_objects=[],
                        # feature_group_to_add=fg_dict[fg],
                        # debug=True,
                        # layer_control=layer_dict[layer],
                        key="map2.1",
                    )
            elif compare_type == "Full Map":
                st.write("Full Electoral Boundaries for Year {}".format(baseline_year))
                m = folium.Map(
                    location=[
                        gdf_baseline_all.geometry.centroid.y.mean(),
                        gdf_baseline_all.geometry.centroid.x.mean(),
                    ],
                    zoom_start=11,
                    max_zoom=21,
                    tiles=map_chosen,
                )

                tooltip = GeoJsonTooltip(
                    fields=[
                        "year",
                        "ED_DESC",
                        "constituency_type",
                        "pax_number",
                        "result",
                    ],
                    aliases=["Year: ", "ED: ", "Type: ", "Pax: ", "Result: "],
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

                folium.GeoJson(gdf_baseline_all, tooltip=tooltip).add_to(m)

                st_folium(
                    m,
                    width=650,
                    height=550,
                    returned_objects=[],
                    # feature_group_to_add=fg_dict[fg],
                    # debug=True,
                    # layer_control=layer_dict[layer],
                    key="map2.2",
                )

        with col2:
            if compare_type == "Constituency Year vs Year":
                if len(gdf_compare) == 0 and len(gdf_baseline) == 0:
                    st.write("No such constituency in year {}".format(compare_year))
                elif len(gdf_compare) == 0 and len(gdf_baseline) > 0:
                    st.write(
                        "No such constituency in year {}. Showing the GRC/SMC that bounded the same area.".format(
                            compare_year
                        )
                    )
                    m_chosen = folium.Map(
                        location=[
                            new_areas_gpd.geometry.centroid.y.mean(),
                            new_areas_gpd.geometry.centroid.x.mean(),
                        ],
                        zoom_start=12,
                        max_zoom=21,
                        tiles=map_chosen,  # Use a greyscale tile layer
                    )

                    tooltip = GeoJsonTooltip(
                        fields=[
                            "year",
                            "ED_DESC",
                            "constituency_type",
                            "pax_number",
                            "result",
                        ],
                        aliases=["Year: ", "ED: ", "Type: ", "Pax: ", "Result: "],
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

                    folium.GeoJson(new_areas_gpd, tooltip=tooltip).add_to(m_chosen)

                    st_folium(
                        m_chosen,
                        width=650,
                        height=550,
                        returned_objects=[],
                        # feature_group_to_add=fg_dict[fg],
                        # debug=True,
                        # layer_control=layer_dict[layer],
                        key="map1.1",
                    )
                else:
                    st.write("Electoral Boundaries for Year {}".format(compare_year))
                    m = folium.Map(
                        location=[
                            gdf_compare.geometry.centroid.y.mean(),
                            gdf_compare.geometry.centroid.x.mean(),
                        ],
                        zoom_start=12,
                        max_zoom=21,
                        tiles=map_chosen,
                    )

                    tooltip = GeoJsonTooltip(
                        fields=[
                            "year",
                            "ED_DESC",
                            "constituency_type",
                            "pax_number",
                            "result",
                        ],
                        aliases=["Year: ", "ED: ", "Type: ", "Pax: ", "Result: "],
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

                    folium.GeoJson(gdf_compare, tooltip=tooltip).add_to(m)

                    st_folium(
                        m,
                        width=650,
                        height=550,
                        returned_objects=[],
                        # feature_group_to_add=fg_dict[fg],
                        # debug=True,
                        # layer_control=layer_dict[layer],
                        key="map2.1",
                    )

            elif compare_type == "Constituency Changes Year over Year":
                if len(gdf_compare) == 0:
                    st.write("No such constituency in year {}.".format(compare_year))
                elif len(gdf_baseline) == 0 and len(gdf_compare) > 0:
                    st.write("Electoral Boundaries for Year {}".format(compare_year))
                    m = folium.Map(
                        location=[
                            gdf_compare.geometry.centroid.y.mean(),
                            gdf_compare.geometry.centroid.x.mean(),
                        ],
                        zoom_start=12,
                        max_zoom=21,
                        tiles=map_chosen,
                    )

                    tooltip = GeoJsonTooltip(
                        fields=[
                            "year",
                            "ED_DESC",
                            "constituency_type",
                            "pax_number",
                            "result",
                        ],
                        aliases=["Year: ", "ED: ", "Type: ", "Pax: ", "Result: "],
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

                    folium.GeoJson(gdf_compare, tooltip=tooltip).add_to(m)

                    st_folium(
                        m,
                        width=650,
                        height=550,
                        returned_objects=[],
                        # feature_group_to_add=fg_dict[fg],
                        # debug=True,
                        # layer_control=layer_dict[layer],
                        key="map2.1",
                    )
                else:
                    st.write(
                        "Electoral Boundaries Changes from {} to {}".format(
                            baseline_year, compare_year
                        )
                    )
                    m = folium.Map(
                        location=[
                            gdf_baseline.geometry.centroid.y.mean(),
                            gdf_baseline.geometry.centroid.x.mean(),
                        ],
                        zoom_start=12,
                        max_zoom=21,
                        tiles=map_chosen,
                    )

                    tooltip1 = GeoJsonTooltip(
                        fields=[
                            "year",
                            "ED_DESC",
                            "constituency_type",
                            "pax_number",
                            "result",
                        ],
                        aliases=["Year: ", "ED: ", "Type: ", "Pax: ", "Result: "],
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
                        fields=[
                            "year",
                            "ED_DESC",
                            "constituency_type",
                            "pax_number",
                            "result",
                        ],
                        aliases=["Year: ", "ED: ", "Type: ", "Pax: ", "Result: "],
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

                    folium.GeoJson(
                        intersected_gpd, tooltip=tooltip1, name="m1", color="red"
                    ).add_to(m)

                    if (len(gdf_compare)) > 0:
                        folium.GeoJson(
                            intersected_gpd_added,
                            tooltip=tooltip2,
                            name="m2",
                            color="green",
                        ).add_to(m)

                    st_folium(
                        m,
                        width=650,
                        height=550,
                        returned_objects=[],
                        # feature_group_to_add=fg_dict[fg],
                        # debug=True,
                        # layer_control=layer_dict[layer],
                        key="map2.2",
                    )
            elif compare_type == "Full Map":
                st.write("Full Electoral Boundaries for Year {}".format(compare_year))
                m = folium.Map(
                    location=[
                        gdf_compare_all.geometry.centroid.y.mean(),
                        gdf_compare_all.geometry.centroid.x.mean(),
                    ],
                    zoom_start=11,
                    max_zoom=21,
                    tiles=map_chosen,
                )

                tooltip = GeoJsonTooltip(
                    fields=[
                        "year",
                        "ED_DESC",
                        "constituency_type",
                        "pax_number",
                        "result",
                    ],
                    aliases=["Year: ", "ED: ", "Type: ", "Pax: ", "Result: "],
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

                folium.GeoJson(gdf_compare_all, tooltip=tooltip).add_to(m)

                st_folium(
                    m,
                    width=650,
                    height=550,
                    returned_objects=[],
                    # feature_group_to_add=fg_dict[fg],
                    # debug=True,
                    # layer_control=layer_dict[layer],
                    key="map2.3",
                )
