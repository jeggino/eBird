import streamlit as st
import pandas as pd
from ebird.api import get_observations
import requests
from streamlit_option_menu import option_menu
import pydeck as pdk
from shapely.geometry import Point
from streamlit_extras.mandatory_date_range import date_range_picker
import geocoder
import wikipedia








st.set_page_config(
    page_title="Ebird Cool App",
    page_icon="🪶",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)


selected2 = option_menu(None, ["Charts", "Maps"], 
    icons=['bi-bar-chart-fill', 'bi bi-map'], 
    menu_icon="cast", default_index=0, orientation="horizontal")




URL = "http://fasteri.com/list/2/short-names-of-countries-and-iso-3166-codes"
API_KEY = 'm37q4mkeq3fj'
BACK = 30
COLUMNS = ['comName', 'date', 'lat', 'lng', 'locId', 'sciName', 'subId']


r = requests.get(URL)
df_code = pd.read_html(r.content)[0]
list_ = {}
for index, column in df_code.iterrows():
    list_[column["Country name"]] = column["ISO 3166 code"]

COUNTRIES = st.sidebar.multiselect("Select one o more countries", df_code["Country name"].unique(), max_selections=10, placeholder="Choose an option")

try:
    b = []
    for country in COUNTRIES:
        b.append(list_[country])
        
    records = get_observations(API_KEY, b,back=BACK)

except:
    st.sidebar.warning('Select a country', icon="⚠️")
    st.stop()

try:
    df_ebird = pd.DataFrame(records)
    df_ebird['date'] = df_ebird.obsDt.str.split(" ",expand=True)[0]
    df_ebird = df_ebird[COLUMNS]

    @st.cache_resource
    def geo_rev(x):
        g = geocoder.osm([x.lat, x.lng], method='reverse').json
        if g:
            return g.get('country')
        else:
            return 'no country'
    
    df_ebird['country'] = df_ebird[['lat', 'lng']].apply(geo_rev, axis=1)        

    #---
    with st.sidebar:
        from datetime import datetime

        date_1 = datetime.strptime(df_ebird.date.min(), '%Y-%m-%d').date()
        date_2 = datetime.strptime(df_ebird.date.max(), '%Y-%m-%d').date()
        DATE = date_range_picker("Select a date range", default_start = date_1, default_end = date_2, 
                                 min_date = date_1, max_date = date_2, 
                                 error_message = 'Please select start and end date')        

        data_filter = (df_ebird["date"] >= str(DATE[0])) & (df_ebird["date"] <= str(DATE[1]))
        df_filter = df_ebird[data_filter]
        
        SPECIES = st.multiselect("Select one o more species", df_filter["comName"].unique(), max_selections=None, placeholder="Choose an option")
        
        
        species_filter = (df_filter["comName"].isin(SPECIES))
        df_filter = df_filter[species_filter]

        

    #---
        st.divider()

    #---
    

    if len(df_filter) == 0:
        st.sidebar.warning('Select a species', icon="⚠️")
        st.stop()

    #----
    if selected2 == "Charts":
        tab1, tab2, tab3, tab4, tab5, tab6, tab7  = st.tabs(["Chart 1", "Chart 2", "Chart 3", "Chart 4", "Chart 5", "Tab 1", "Info species"])
        import altair as alt

        source = df_filter.groupby(["comName"],as_index=False).size().sort_values('size',ascending=False).reset_index()
        
        bar_chart = alt.Chart(source).mark_bar().encode(
            x=alt.X(field='size', title="Number of observations"),
            y=alt.Y('comName',title="", sort="ascending", ),
        )
        
        tab1.altair_chart(bar_chart, theme=None, use_container_width=True)

        #---
        source = df_filter.groupby("date",as_index=False).size()

        heatmap = alt.Chart(source, title="Number of obsevations per day").mark_rect().encode(
            x=alt.X("date(date):O", title="Day", axis=alt.Axis(format="%e", labelAngle=0)),
            y=alt.Y("month(date):O", title="Month"),
            color=alt.Color("sum(size)", legend=alt.Legend(title=None)),
            tooltip=[
                alt.Tooltip("monthdate(date)", title="Date"),
                alt.Tooltip("max(size)", title="Summ of number of observations"),
            ],
        ).configure_view(step=13, strokeWidth=0).configure_axis(domain=False)

        tab2.altair_chart(heatmap, theme=None, use_container_width=True)


        #---
        source = df_filter.groupby("date",as_index=False).size()

        # Size of the hexbins
        size = 15
        # Count of distinct x features
        xFeaturesCount = 12
        # Count of distinct y features
        yFeaturesCount = 7
        # Name of the x field
        xField = 'date'
        # Name of the y field
        yField = 'date'
        
        # the shape of a hexagon
        hexagon = "M0,-2.3094010768L2,-1.1547005384 2,1.1547005384 0,2.3094010768 -2,1.1547005384 -2,-1.1547005384Z"
        
        hexbin = alt.Chart(source).mark_point(size=size**2, shape=hexagon).encode(
            x=alt.X('xFeaturePos:Q', axis=alt.Axis(title='Month',
                                                   grid=False, tickOpacity=0, domainOpacity=0)),
            y=alt.Y('day(' + yField + '):O', axis=alt.Axis(title='Weekday',
                                                           labelPadding=20, tickOpacity=0, domainOpacity=0)),
            stroke=alt.value('black'),
            strokeWidth=alt.value(0.2),
            fill=alt.Color('sum(size):Q', scale=alt.Scale(scheme='darkblue')),
            tooltip=['month(' + xField + '):O', 'day(' + yField + '):O', 'sum(size):Q']
        ).transform_calculate(
            # This field is required for the hexagonal X-Offset
            xFeaturePos='(day(datum.' + yField + ') % 2) / 2 + month(datum.' + xField + ')'
        ).properties(
            # Exact scaling factors to make the hexbins fit
            width=size * xFeaturesCount * 2,
            height=size * yFeaturesCount * 1.7320508076,  # 1.7320508076 is approx. sin(60°)*2
        ).configure_view(
            strokeWidth=0
        )

        tab3.altair_chart(hexbin, theme=None, use_container_width=True)

        #---
        source = df_filter.groupby("date",as_index=False).size()

        bar = alt.Chart(source).mark_bar().encode(
            x='date:T',
            y='size:Q'
        )
        
        rule = alt.Chart(source).mark_rule(color='red').encode(
            y='mean(size):Q'
        )
        
        tab4.altair_chart((bar + rule), theme=None, use_container_width=True)

        #---
        df_country = df_filter.groupby(["country","comName"], as_index=False).size()

        bar_country = alt.Chart(df_country).mark_bar().encode(
            y='size:Q',
            x=alt.X('comName:N').sort('-y'),
            facet=alt.Facet('country:N', columns=2)
        ).properties(width=200)

        tab5.altair_chart(bar_country, theme=None, use_container_width=True)

        #---
        data_df = pd.DataFrame(
            {
                "sales": [200, 550, 1000, 80],
                "Species": ["A", "B", "C", "D",]
            }
        )
        
        tab6.data_editor(
            data_df,
            column_config={
                "sales": st.column_config.ProgressColumn(
                    "Sales volume",
                    help="The sales volume in USD",
                    format="$%f",
                    min_value=0,
                    max_value=1000,
                ),
            },
            hide_index=True,
        )

        #---
        with tab7:

            for species in SPECIES:
                try:
                    col1,col2 = st.columns([3,2])
        
                    col1.title(species)
                    col2.image(wikipedia.page(species).images[0],width=300)
                
                    st.markdown(f"{wikipedia.summary(species)}",unsafe_allow_html=True)
                    st.markdown(f"link wiki: {wikipedia.page(species).url}",unsafe_allow_html=True)
    
                    st.divider()
                except:
                    st.warning('No infos for this species', icon="⚠️")
                    st.divider()
        

    
    
    elif selected2 == "Maps":

        map1, map2, map3, map4  = st.tabs(["Map 1", "Map 2", "Map 3", "Map 4"])
        
        ICON_URL = "https://cdn4.iconfinder.com/data/icons/twitter-29/512/157_Twitter_Location_Map-1024.png"

        icon_data = {
            "url": ICON_URL,
            "width": 242,
            "height": 242,
            "anchorY": 242,
        }
        
        data = df_filter
        data["icon_data"] = None
        for i in data.index:
            data["icon_data"][i] = icon_data
        
        # Set the viewport location
        view_state = pdk.ViewState(
            longitude=4.885, latitude=52.367, zoom=10.76, min_zoom=1, max_zoom=20, pitch=0, bearing=0,
        )
        
        icon_layer = pdk.Layer(
            type="IconLayer",
            data=data,
            get_icon="icon_data",
            size_scale=40,
            get_position=['lng', 'lat'],
            pickable=True,
        )
        
        r = pdk.Deck(layers=[icon_layer], initial_view_state=view_state, 
                     tooltip={"text": "Species: {comName} \nDate: {date}"},
                    # api_keys={"mapbox":"pk.eyJ1IjoiamVnZ2lubyIsImEiOiJjbDFlMTA3MmowMWV4M2h1Z2ZobWFmZDhvIn0.OYXDSrOZ5vWheUZ1nFSB_Q"},
                    # map_provider='mapbox',
                    # map_style ="mapbox://styles/jeggino/clieqivbp005e01pggw0e5zxh"
                    )

        map1.pydeck_chart(pydeck_obj=r, use_container_width=True)

        #---
        import geopandas as gpd
        from shapely.geometry import Point


        COUNTRIES = "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_scale_rank.geojson"
        df_world = df_filter
        df_world['Coordinates'] = list(zip(df_world.lng, df_world.lat))
        df_world['Coordinates'] = df_world['Coordinates'].apply(Point)
        gdf = gpd.GeoDataFrame(df_world, geometry='Coordinates')
        df = gdf.dissolve(by='subId',aggfunc={"comName":'count'},as_index=False)
        
                
        view_state = pdk.ViewState(latitude=51.47, longitude=0.45, zoom=1, min_zoom=1, bearing=0, pitch=45)
        
        # Set height and width variables
        view = pdk.View(type="_GlobeView", controller=True, width=1000, height=700)
        
        
        layers = [
            pdk.Layer(
                "GeoJsonLayer",
                id="base-map",
                data=COUNTRIES,
                stroked=True,
                filled=True,
                get_fill_color=[200, 200, 200],
            ),
            pdk.Layer(
                "ColumnLayer",
                data=df,
                get_elevation="comName",
                get_position="geometry.coordinates",
                elevation_scale=10000,
                pickable=True,
                auto_highlight=True,
                radius=2000,
                get_fill_color="[(1 - comName / 500) * 255, 255, 100]",
            ),
        ]
        
        deck = pdk.Deck(
            views=[view],
            initial_view_state=view_state,
            tooltip={"text": "SubId: {subId}, \nNumber of observations: {comName}"},
            layers=layers,
            map_provider=None,
            # Note that this must be set for the globe to be opaque
            parameters={"cull": True},
        )

        map2.pydeck_chart(pydeck_obj=deck, use_container_width=True)

        #---
        with map3:
            SIZE = st.sidebar.select_slider( 'Select cell size',options=['small', 'medium', 'big',])
            size_dict = {"small":2000,"medium":20000,"big":100000}
            layer = pdk.Layer(
                "GridLayer",
                gdf,
                pickable=True,
                extruded=True,
                cell_size=size_dict[SIZE],
                elevation_scale=200,
                get_position=['lng', 'lat'],
            )
            
            # view_state = pdk.ViewState(latitude=37.7749295, longitude=-122.4194155, zoom=11, bearing=0, pitch=45)
            
            # Render
            r = pdk.Deck(
                layers=[layer],
                # initial_view_state=view_state,
                tooltip={"text": "Number of observations: {count}"},
            )
    
            st.pydeck_chart(pydeck_obj=r, use_container_width=True)

                    
except:
    st.error('Sorry, no data', icon="🚨")
