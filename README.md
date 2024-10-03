# Project Title - YouTube Data Harvesting and Warehousing using SQL and Streamlit

## Problem Statement:
The problem statement is to create a Streamlit application that allows users to access and analyze data from multiple YouTube channels. The application should have the following features:
- Ability to input a YouTube channel ID and retrieve all the relevant data (Channel name, subscribers, total video count, playlist ID, video ID, likes, dislikes, comments of each video) using Google API.
- Ability to collect data for up to 10 different YouTube channels and store them in the data lake by clicking a button.
- Option to store the data in a MYSQL or PostgreSQL.
- Ability to search and retrieve data from the SQL database using different search options, including joining tables to get channel details.

## Approach:
- **Set up a Streamlit app:** used Streamlit to create a simple UI where users can enter a YouTube channel ID, view the channel details, and select channels to migrate to the data warehouse.
- **Connect to the YouTube API:** used the YouTube API to retrieve channel and video data. Used the Google API client library for Python to make requests to the API.
- **Store and Clean data :** Once the data is retrieved from the YouTube API, stored it in a suitable format for temporary storage before migrating to the data warehouse. Used pandas DataFrames.
- **Migrate data to a SQL data warehouse:** After collecting the data for multiple channels, migrated the data to a SQL data warehouse. Used MySQL for this.
- **Query the SQL data warehouse:** Used SQL queries to join the tables in the SQL data warehouse and retrieve data for specific channels based on user input. Also, used a Python SQL library such as SQLAlchemy to interact with the SQL database.
- **Display data in the Streamlit app:** Finally, displayed the retrieved data in the Streamlit app. Used Streamlit's data visualization features to create charts and graphs to help users analyze the data.

## Overall:
This approach involved building a simple UI with Streamlit, retrieving data from the YouTube API, storing the data SQL as a warehouse, querying the data warehouse with SQL, and displaying the data in the Streamlit app.

