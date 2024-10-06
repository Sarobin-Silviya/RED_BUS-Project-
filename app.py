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
    st.set_page_config(page_title="RedBus Data", layout='wide')

    # Add color styling to the sidebar and button
    st.sidebar.markdown(
        """
        <style>
        .sidebar .sidebar-content {
            background-color: #f4f4f4;
            color: #333333;
            padding: 10px;
        }
        .stButton>button {
            background-color: #FF6347;
            color: white;
            border-radius: 10px;
            transition: background-color 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #FF7F7F;
            color: white;
        }
        .stButton>button:focus {
            background-color: #FF7F7F;  /* Lighter shade when clicked */
            color: white;  /* Keep text white */
            border-radius: 10px;
        }
        </style>
        """, unsafe_allow_html=True
    )

    # Sidebar for filters
    st.sidebar.title("Filter Options")
    st.sidebar.markdown("### Customize your search")

    min_price = st.sidebar.number_input('Min Price', min_value=0)
    max_price = st.sidebar.number_input('Max Price', min_value=0)
    min_departing_time = st.sidebar.time_input('Min Departing Time', value=pd.Timestamp('09:00').time())
    max_departing_time = st.sidebar.time_input('Max Departing Time', value=pd.Timestamp('21:00').time())
    min_reaching_time = st.sidebar.time_input('Min Reaching Time', value=pd.Timestamp('10:00').time())
    max_reaching_time = st.sidebar.time_input('Max Reaching Time', value=pd.Timestamp('22:00').time())

    # Using expander for additional filters
    with st.sidebar.expander("Advanced Filters", expanded=True):
        min_duration = st.text_input('Min Duration', '0 hours')
        max_duration = st.text_input('Max Duration', '24 hours')
        star_rating = st.slider('Star Rating', 0.0, 5.0, (0.0, 5.0))
        
        # Add "All" as an option for bus types in the multi-select
        bus_type = st.multiselect('Bus Type', ['All', 'Seater', 'Sleeper', 'AC', 'Non-AC'], default=['All'])

    # Fetch routes dynamically from the database
    routes = fetch_routes()
    route = st.sidebar.selectbox('Bus Route', [''] + routes)

    # Main title and instructions
    st.title("🚍 RedBus Data Visualization Dashboard")
    st.markdown("**Use the sidebar filters to explore bus routes, prices, and travel times.**")

    # Adjust SQL query to handle 'All' in bus_type
    query = """
    SELECT * 
    FROM bus_routes 
    WHERE price BETWEEN %s AND %s 
      AND departing_time BETWEEN %s AND %s 
      AND reaching_time BETWEEN %s AND %s 
      AND duration BETWEEN %s AND %s
      AND star_rating BETWEEN %s AND %s
    """

    # Modify query to handle specific bus type selections
    if 'All' not in bus_type:
        bus_type_placeholder = ','.join(['%s'] * len(bus_type))
        query += f" AND bustype IN ({bus_type_placeholder})"

    query += " AND route_name LIKE %s"

    # Prepare parameters for the query
    params = [
        min_price,
        max_price,
        min_departing_time.strftime('%H:%M:%S'),
        max_departing_time.strftime('%H:%M:%S'),
        min_reaching_time.strftime('%H:%M:%S'),
        max_reaching_time.strftime('%H:%M:%S'),
        min_duration,
        max_duration,
        star_rating[0],
        star_rating[1]
    ]

    if 'All' not in bus_type:
        params.extend(bus_type)

    params.append(f'%{route}%' if route else '%')

    # Fetch and display data based on user inputs
    if st.sidebar.button('Get Data'):
        with st.spinner('Fetching data...'):
            filtered_data = fetch_data(query, params)
            
            if filtered_data.empty:
                st.warning("No data found. Try adjusting your filters.")
            else:
                st.write(filtered_data)

                st.subheader("🧩 Data Visualization")

                # Price Distribution with Bar Chart (increase size slightly, color adjusted)
                st.write("Price Distribution")
                price_counts = filtered_data['price'].value_counts().sort_index()
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(price_counts.index, price_counts.values, color='orange', edgecolor='black')
                ax.set_xlabel('Price')
                ax.set_ylabel('Frequency')
                ax.set_title('Price Distribution')
                st.pyplot(fig)

                # Bus Type distribution with Pie Chart (increase size, color improved)
                st.write("Bus Type Distribution")
                bus_type_counts = filtered_data['bustype'].value_counts()
                fig = px.pie(
                    values=bus_type_counts.values, names=bus_type_counts.index,
                    title="Bus Type Distribution", width=900, height=600,
                    color_discrete_sequence=px.colors.qualitative.Vivid
                )
                st.plotly_chart(fig)

                # New Insight: Revenue per Route (Bar Chart - larger size and horizontal x-axis labels)
                st.write("Revenue per Route")
                filtered_data['revenue'] = filtered_data['price'] * filtered_data.groupby('route_name')['route_name'].transform('count')
                revenue_per_route = filtered_data.groupby('route_name')['revenue'].sum().reset_index()
                fig, ax = plt.subplots(figsize=(10, 5))  # Larger bar chart
                ax.bar(revenue_per_route['route_name'], revenue_per_route['revenue'], color='skyblue', edgecolor='black')
                ax.set_xlabel('Route Name')
                ax.set_ylabel('Revenue (Sum of Price x Number of Buses)')
                ax.set_title('Revenue per Route')
                plt.xticks(rotation=0, ha='center')  # Horizontal labels
                st.pyplot(fig)

                # Allow downloading the filtered data as a CSV
                csv = filtered_data.to_csv(index=False)
                st.download_button("Download CSV", data=csv, file_name='filtered_data.csv', mime='text/csv')

if __name__ == "__main__":
    main()
