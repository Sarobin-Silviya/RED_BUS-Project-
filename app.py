import streamlit as st
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
import plotly.express as px

# Function to fetch data from the database
def fetch_data(query, params):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="silviya123",
        database="red_bus"
    )
    try:
        data = pd.read_sql(query, conn, params=params)
    finally:
        conn.close()
    return data

# Function to fetch distinct routes for dropdown
def fetch_routes():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="silviya123",
        database="red_bus"
    )
    query = "SELECT DISTINCT route_name FROM bus_routes"
    routes = pd.read_sql(query, conn)
    conn.close()
    return routes['route_name'].tolist()

# Main function for Streamlit app
def main():
    st.set_page_config(page_title="RedBus Data", page_icon=r"C:\Users\SAROBIN SILVIYA\Downloads\red_bus_logo.webp", layout='wide')

    # Sidebar for filters
    st.sidebar.title("Filter Options")

    min_price = st.sidebar.number_input('Min Price', min_value=0)
    max_price = st.sidebar.number_input('Max Price', min_value=0)
    min_departing_time = st.sidebar.time_input('Min Departing Time', value=pd.Timestamp('09:00').time())
    max_departing_time = st.sidebar.time_input('Max Departing Time', value=pd.Timestamp('21:00').time())
    min_reaching_time = st.sidebar.time_input('Min Reaching Time', value=pd.Timestamp('10:00').time())
    max_reaching_time = st.sidebar.time_input('Max Reaching Time', value=pd.Timestamp('22:00').time())
    
    # Using expander for additional filters
    with st.sidebar.expander("Advanced Filters"):
        min_duration = st.text_input('Min Duration', '0 hours')
        max_duration = st.text_input('Max Duration', '24 hours')
        star_rating = st.slider('Star Rating', 0.0, 5.0, (0.0, 5.0))
        bus_type = st.selectbox('Bus Type', ['All', 'Seater', 'Sleeper', 'AC', 'Non-AC'])

    # Fetch routes dynamically from the database
    routes = fetch_routes()
    route = st.sidebar.selectbox('Bus Route', [''] + routes)  # Adding an empty option for no route filter

    # Main title and instructions
    st.title("RedBus Data Filtering and Visualization")
    st.markdown("**Use the sidebar filters to explore bus routes, prices, and travel times.**")

    # Define the SQL query with additional filters
    query = """
    SELECT * 
    FROM bus_routes 
    WHERE price BETWEEN %s AND %s 
      AND departing_time BETWEEN %s AND %s 
      AND reaching_time BETWEEN %s AND %s 
      AND duration BETWEEN %s AND %s
      AND star_rating BETWEEN %s AND %s
      AND (bustype = %s OR %s = 'All')
      AND route_name LIKE %s
    """
    
    # Prepare parameters for the query
    params = (
        min_price,
        max_price,
        min_departing_time.strftime('%H:%M:%S'),
        max_departing_time.strftime('%H:%M:%S'),
        min_reaching_time.strftime('%H:%M:%S'),
        max_reaching_time.strftime('%H:%M:%S'),
        min_duration,
        max_duration,
        star_rating[0],
        star_rating[1],
        bus_type,
        bus_type,
        f'%{route}%' if route else '%'
    )

    # Fetch and display data based on user inputs
    if st.sidebar.button('Get Data'):
        with st.spinner('Fetching data...'):
            filtered_data = fetch_data(query, params)
            st.write(filtered_data)

            # Data Visualization Section
            if not filtered_data.empty:
                st.subheader("Data Visualization")
                
                # Price Distribution with Bar Chart
                st.write("Price Distribution")
                price_counts = filtered_data['price'].value_counts().sort_index()
                fig, ax = plt.subplots()
                ax.bar(price_counts.index, price_counts.values, edgecolor='black')
                ax.set_xlabel('Price')
                ax.set_ylabel('Frequency')
                ax.set_title('Price Distribution')
                st.pyplot(fig)

                # Star Rating Distribution with Bar Chart
                st.write("Star Rating Distribution")
                star_rating_counts = filtered_data['star_rating'].value_counts().sort_index()
                fig, ax = plt.subplots()
                ax.bar(star_rating_counts.index, star_rating_counts.values, edgecolor='black')
                ax.set_xlabel('Star Rating')
                ax.set_ylabel('Frequency')
                ax.set_title('Star Rating Distribution')
                st.pyplot(fig)

                # Bus Type distribution with Pie Chart
                st.write("Bus Type Distribution")
                bus_type_counts = filtered_data['bustype'].value_counts()
                fig = px.pie(values=bus_type_counts.values, names=bus_type_counts.index, title="Bus Type Distribution")
                st.plotly_chart(fig)

                # Allow downloading the filtered data as a CSV
                csv = filtered_data.to_csv(index=False)
                st.download_button("Download CSV", data=csv, file_name='filtered_data.csv', mime='text/csv')

if __name__ == "__main__":
    main()
