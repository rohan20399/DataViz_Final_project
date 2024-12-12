import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import json

# Load Data
listings = pd.read_csv("new_york_listings_2024.csv")
points_of_interest = pd.read_csv("Points_of_Interest_20241211.csv")
geojson_file = "nyc_boroughs.json"  # Updated GeoJSON file
with open(geojson_file, 'r') as file:
    geojson_data = json.load(file)

# Map numeric BOROUGH codes to borough names
borough_mapping = {
    1: "Brooklyn",
    2: "Queens",
    3: "Bronx",
    4: "Staten Island",
    5: "Manhattan"
}
points_of_interest['BOROUGH'] = points_of_interest['BOROUGH'].map(borough_mapping)

# Extract latitude and longitude from the_geom column
points_of_interest[['Longitude', 'Latitude']] = points_of_interest['the_geom'].str.extract(r'\(([-0-9.]+) ([-0-9.]+)\)').astype(float)

# App Title
st.title("Exploring Airbnb Listings in NYC Boroughs")
st.markdown("**Authors:** Raghav Kharosekar, Shreyash Shinkar & Rohan Deshpande")
st.markdown("**Data source:** [Link](https://raw.githubusercontent.com/rohan20399/DataViz_Final_project/refs/heads/main/new_york_listings_2024.csv)")
st.markdown("**Streamlit app source code:** [Link](https://github.com/rohan20399/DataViz_Final_project/blob/main/app.py)")

# Initialize a session state variable to store the selected borough
if 'selected_borough' not in st.session_state:
    st.session_state['selected_borough'] = None

# Interactive Map with Borough Colors and Interactivity
borough_colors = {
    "Manhattan": "#1f77b4",
    "Brooklyn": "#ff7f0e",
    "Queens": "#2ca02c",
    "Bronx": "#d62728",
    "Staten Island": "#9467bd"
}

map_obj = folium.Map(location=[40.7128, -74.0060], zoom_start=10)

# Add GeoJSON and names to the map
geojson_layer = folium.GeoJson(
    geojson_data,
    name="NYC Boroughs",
    style_function=lambda feature: {
        "fillColor": borough_colors.get(feature['properties']['name'], "#3186cc"),
        "color": "black",
        "weight": 2,
        "fillOpacity": 0.5,
    },
    highlight_function=lambda feature: {
        "weight": 3,
        "color": "yellow",
    },
    tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Borough"]),
).add_to(map_obj)

# Display the map and capture user interactions
map_data = st_folium(map_obj, width=700, height=500, returned_objects=["last_active_drawing"])

# Update selected borough based on user interaction
if map_data and "last_active_drawing" in map_data and map_data["last_active_drawing"]:
    st.session_state['selected_borough'] = map_data["last_active_drawing"]["properties"]["name"]

# Filter Data Based on Selected Borough
selected_borough = st.session_state['selected_borough']
st.write(f"**Selected Borough:** {selected_borough}")

if selected_borough:
    filtered_data = listings[listings['neighbourhood_group'] == selected_borough]
    filtered_poi = points_of_interest[points_of_interest['BOROUGH'] == selected_borough]

    # Display Metrics
    total_listings = len(filtered_data)
    average_price = filtered_data['price'].mean()
    total_hosts = filtered_data['host_id'].nunique()
    total_reviews = filtered_data['number_of_reviews_ltm'].sum()

    # Display metrics in tabular format
    st.markdown(
        f"""
        <style>
        .metric-container {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .metric-box {{
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background-color: #f9f9f9;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
        }}
        .metric-box h1 {{
            margin: 0;
            font-size: 2em;
            color: #333;
        }}
        .metric-box p {{
            margin: 0;
            font-size: 1em;
            color: #666;
        }}
        </style>
        <div class="metric-container">
            <div class="metric-box">
                <h1>{total_listings}</h1>
                <p>Total Listings</p>
            </div>
            <div class="metric-box">
                <h1>{average_price:.2f}</h1>
                <p>Average Price ($)</p>
            </div>
            <div class="metric-box">
                <h1>{total_hosts}</h1>
                <p>Total Hosts</p>
            </div>
            <div class="metric-box">
                <h1>{total_reviews}</h1>
                <p>Total Reviews</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Average Price by Property Type (Bar Chart)
    st.subheader("Average Price by Property Type")
    avg_price_by_type = filtered_data.groupby("room_type")["price"].mean().reset_index()
    bar_chart = px.bar(avg_price_by_type, x="room_type", y="price", labels={"room_type": "Property Type", "price": "Price ($)"})
    st.plotly_chart(bar_chart)

    # Rating Distribution (Histogram)
    st.subheader("Rating Distribution")
    rating_histogram = px.histogram(filtered_data, x="rating", nbins=20, labels={"rating": "Review Rating"})
    st.plotly_chart(rating_histogram)

    # Visualization: Contextual Visualisation
    st.subheader("Contextual Visualisations")
    st.markdown("These visualisations have been done by us, code to which can be found in the link below")
    st.markdown("**Contextual data source:** [Link](https://data.cityofnewyork.us/City-Government/Points-of-Interest/rxuy-2muj)")
    st.markdown("**Streamlit app source code:** [Link](https://github.com/rohan20399/DataViz_Final_project/blob/main/app.py)")

    # Treemap of Points of Interest by Borough
    st.subheader("Treemap of Points of Interest by Borough")
    poi_counts = points_of_interest.groupby('BOROUGH').size().reset_index(name='poi_count')
    treemap = px.treemap(
        poi_counts,
        path=["BOROUGH"],
        values="poi_count",
        color="poi_count",
        color_continuous_scale="Viridis"
    )

    st.plotly_chart(treemap)

    # Visualization: Dual-Axis Bar and Line Plot for Average Price and Points of Interest Count
    st.subheader("Average Price and Points of Interest Count by Borough")
    avg_prices = listings.groupby('neighbourhood_group')['price'].mean().reset_index()
    avg_prices = avg_prices.rename(columns={'neighbourhood_group': 'BOROUGH'})
    poi_counts = points_of_interest.groupby('BOROUGH').size().reset_index(name='poi_count')
    merged_data = pd.merge(avg_prices, poi_counts, on='BOROUGH', how='inner')

    dual_axis_plot = px.bar(
        merged_data,
        x='BOROUGH',
        y='poi_count',
        labels={'poi_count': 'Points of Interest Count'}
    )
    dual_axis_plot.add_scatter(
        x=merged_data['BOROUGH'],
        y=merged_data['price'],
        mode='lines+markers',
        name='Average Price ($)',
        yaxis='y2'
    )

    dual_axis_plot.update_layout(
        yaxis=dict(title='Points of Interest Count'),
        yaxis2=dict(title='Average Price ($)', overlaying='y', side='right'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(dual_axis_plot)

else:
    st.write("Click on a borough for detailed analysis.")

# Explanatory Paragraphs
st.markdown("""
### Understanding the Data and Visualizations

This application explores Airbnb listings across the boroughs of New York City. User can select a borough of interest by clicking on the map to see the related metrics, such as average price by property type and what is the usual ratings distribution of listing in that borough. These metrics give an idea of the pricing of airbnbs and also how they have been rated.

The second part of the application uses data on points of interest and relates it with the listings. The treemap visualization displays the distribution of points of interest across boroughs, helping users identify areas with cultural and tourist attractions. This contextual dataset adds depth to the analysis by correlating these attractions with Airbnb trends.

The dual-axis chart juxtaposes the average Airbnb prices with the number of points of interest. This visualization reveals insights into how proximity to popular attractions might influence pricing, providing actionable data for hosts and travelers alike.
""")
