import os
import geopandas as gpd
import streamlit as st
import pandas as pd
import os
import folium
import leafmap.foliumap as leafmap
from streamlit_folium import folium_static
import altair as alt

def load_station_shapefile():

    geo_file = 'https://raw.githubusercontent.com/danhamill/delta_stage/main/data/gage_list_lat-lon.csv'
    df_stns = pd.read_csv(geo_file)
    gdf = gpd.GeoDataFrame(df_stns, geometry=gpd.points_from_xy(df_stns.Longitude_D, df_stns.Latitude_D),crs='EPSG:4326')
    gdf.Station = gdf.Station.str.upper()
    return gdf

def load_results():
    data_file = 'https://raw.githubusercontent.com/danhamill/delta_stage/main/data/temp_results.csv'
    df = pd.read_csv(data_file)
    df = df.drop('Unnamed: 0', axis=1)
    df.short_name = df.short_name.str.upper()
    df.long_name = df.long_name.str.upper()
    return df


def save_uploaded_file(file_content, file_name):
    """
    Save the uploaded file to a temporary directory
    """
    import tempfile
    import os
    import uuid

    _, file_extension = os.path.splitext(file_name)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(tempfile.gettempdir(), f"{file_id}{file_extension}")

    with open(file_path, "wb") as file:
        file.write(file_content.getbuffer())

    return file_path
def get_short_site_data(df, gdf, random_site):
    sub_df = df.loc[df.short_name == random_site, :]
    tmp_gdf  = gdf.merge(sub_df, left_on = 'Station', right_on= 'long_name', how='left' )
    tmp_gdf = tmp_gdf[['Station', 'Latitude_D', 'Longitude_D', 'geometry',  'p_hat', 'record_length', 'distance_miles']].drop_duplicates()
    tmp_gdf = tmp_gdf.loc[tmp_gdf.Station.isin([random_site.upper()]+sub_df.long_name.unique().tolist())]
    tmp_gdf.loc[tmp_gdf.Station == random_site.upper(), 'mycolor'] = 'red'
    tmp_gdf.loc[tmp_gdf.Station != random_site.upper(), 'mycolor'] = 'blue'
    tmp_gdf = tmp_gdf.reset_index(drop=True)
    return sub_df, tmp_gdf

def app():

    st.title("Delta Stage")

    row1_col1, row1_col2 = st.columns([2, 1])
    width = 950
    height = 600
    print(os.getcwd())
    with row1_col2:

        gdf = load_station_shapefile()
        df = load_results()

        lon, lat = leafmap.gdf_centroid(gdf)

        container = st.container()
        map = folium.Map(location = [lat, lon], tiles = "OpenStreetMap", zoom_start = 9)


        with row1_col1:

            short_names = df.short_name.unique().tolist()
            random_site = None

            with container:
                plot_site_results = st.checkbox("Plot Site Results", True)
                if plot_site_results:
                    random_site = st.selectbox(
                        "Select a site to plot", short_names
                    )
                    print(random_site)
                    #subset results
                    sub_df, tmp_gdf = get_short_site_data(df, gdf, random_site)

                    geo_df_list = [[point.xy[1][0], point.xy[0][0]] for point in tmp_gdf.geometry ]
                    i = 0
                    for coordinates in geo_df_list:
                        #assign a color marker for the type of volcano, Strato being the most common
                        print(tmp_gdf.iloc[i].Station.upper())
                        if tmp_gdf.iloc[i].Station.upper() == random_site:
                            type_color = "#1a1a1a"
                            print('found true')
                            phat = 0.5
                            marker = f"""
                                        <div><svg>
                                            <circle cx="0" cy="0" r="{100*phat}" fill="{type_color}" opacity=".8"/>
                                        </svg></div>
                                        """
                        elif tmp_gdf.iloc[i].p_hat == tmp_gdf.p_hat.max():
                            type_color = '#e41a1c'
                            phat = tmp_gdf.iloc[i].p_hat
                            marker = f"""
                                        <div><svg>
                                            <circle cx="0" cy="0" r="{100*phat}" fill="{type_color}" opacity=".8"/>
                                        </svg></div>
                                        """
                        
                        else:
                            type_color = "#4daf4a"
                            phat = tmp_gdf.iloc[i].p_hat
                            marker = f"""
                                        <div><svg>
                                            <circle cx="0" cy="0" r="{100*phat}" fill="{type_color}" opacity=".8"/>
                                        </svg></div>
                                        """


                            # Place the markers with the popup labels and data
                        map.add_child(folium.Marker(location = coordinates,
                                                popup =
                                                "P_hat: " + str(phat)+ '<br>'+
                                                "Name: " + str(tmp_gdf.iloc[i].Station),
                                                icon = folium.DivIcon(marker)))

                        i += 1
                        del type_color
            folium_static(map, width = width-100, height = height)
            
            row1_col1.dataframe(pd.DataFrame(tmp_gdf.drop(['Latitude_D','Longitude_D','geometry','mycolor'], axis=1)).dropna().sort_values('p_hat', ascending = False))

            line = alt.Chart(sub_df).mark_line().encode(
                x = alt.X('WY:O', axis = alt.Axis(title = 'Water Year')),
                y = alt.Y('Stage', axis = alt.Axis(title = 'Stage [ft]')),
                color = alt.Color('long_name', legend = None),
                ).interactive()
            

            ts = alt.Chart(sub_df).mark_point().encode(
                x = alt.X('WY:O', axis = alt.Axis(title = 'Water Year')),
                y = alt.Y('Stage', axis = alt.Axis(title = 'Stage [ft]')),
                color = alt.Color('long_name'),
                shape = alt.Shape('long_name')
                ).interactive()
            
            top = alt.layer(line, ts).resolve_scale(color = 'independent',shape = 'independent')
            st.altair_chart(top, use_container_width=True)

            d = alt.Chart(sub_df).mark_point().encode(
                x= alt.X('distance_miles', axis = alt.Axis(title = 'Distance [miles]')),
                y = alt.Y('p_hat', axis = alt.Axis(title = 'rho hat')),
                color = alt.Color('long_name'),
                shape = alt.Shape('long_name', legend=None)
                ).interactive()

            st.altair_chart(d, use_container_width=True)    
            # m = leafmap.Map(center=(lat, lon))
            # m.add_gdf(tmp_gdf, random_color_column='mycolor')
            # # m.add_labels(tmp_gdf, 'Station')

            # # m.add_vector(file_path, layer_name=layer_name)
            # # if backend == "folium":
            # #     m.zoom_to_gdf(tmp_gdf)
            # st.pydeck_chart(m)


