from googleapiclient.discovery import build
import pymongo
import mysql.connector
import pandas as pd
from datetime import datetime
import streamlit as st
import plotly.express as px
import re
import time 

# API ID connection
def api_connect():
    Api_Key = "AIzaSyC8icDLRtZdgomA4pbkSAXMg2czvwP2U4A"
    Api_service_name = "youtube"
    Api_version = "v3"
    youtube = build(Api_service_name,Api_version,developerKey = Api_Key)
    return youtube
youtube = api_connect()

#Get Channel Information

def get_channel_info(channel_id):
    request = youtube.channels().list(
                part = "snippet,ContentDetails,statistics",
                id = channel_id
    )
    response = request.execute()
    for i in response['items']:
            data = dict(Channel_Name = i['snippet']['title'],
                        Channel_Id = i['id'],
                        Subscribers = i['statistics']['subscriberCount'],
                        Views = i['statistics']['viewCount'],
                        Total_videos = i['statistics']['videoCount'],
                        Channel_Description = i['snippet']['description'],
                        Playlist_Id = i['contentDetails']['relatedPlaylists']['uploads'])
    return data


#Get Video ID

def get_video_ids(channel_id):
    video_ids = []
    response = youtube.channels().list(id = channel_id,
                                      part = 'contentDetails').execute()
    Playlist_Id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    next_page_token = None

    while True:
        response1 = youtube.playlistItems().list(
                                                part = 'snippet',
                                                playlistId = Playlist_Id,
                                                maxResults = 50,
                                                pageToken = next_page_token).execute()
        for i in range(len(response1['items'])):
            video_ids.append(response1['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = response1.get('nextPageToken')

        if next_page_token is None:
            break
    return video_ids

# Get Video Infromation

def get_video_info(video_ids):
    video_data = []
    for video_id in video_ids:
        request = youtube.videos().list(
                        part = "snippet,contentDetails,statistics",
                        id = video_id)
        response = request.execute()
        for item in response['items']:
            data = dict(Channel_Name = item['snippet']['channelTitle'],
                        Channel_Id = item['snippet']['channelId'],
                        Video_Id = item['id'],
                        Title = item['snippet']['title'],
                        Thumbnails = item['snippet']['thumbnails']['default']['url'],
                        Description = item['snippet'].get('description'),
                        Publish_At = item['snippet']['publishedAt'],
                        Duration = item['contentDetails']['duration'],
                        Views = item['statistics'].get('viewCount'),
                        Comments = item['statistics'].get('commentCount'),
                        Favorite = item['statistics']['favoriteCount'],
                        Definition = item['contentDetails']['definition'],
                        Caption = item['contentDetails']['caption'],
                        Likes = item['statistics'].get('likeCount'),
                        Tags = item['snippet'].get('tags')) 
            video_data.append(data)
    return video_data

# Get Comment Information

def get_comment_info(video_ids):
    Comment_data = []
    try:
        for video_id in video_ids:
            request = youtube.commentThreads().list(
                            part = 'snippet',
                            videoId = video_id,
                            maxResults = 100
            )
            response = request.execute()
            for item in response['items']:
                data = dict(Comment_Id = item['snippet']['topLevelComment']['id'],
                            Video_Id = item['snippet']['topLevelComment']['snippet']['videoId'],
                            Comment_Text = item['snippet']['topLevelComment']['snippet']['textDisplay'],
                            Comment_Author = item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                            comment_Published_Date = item['snippet']['topLevelComment']['snippet']['publishedAt'])
                Comment_data.append(data)
    except:
        pass
    return Comment_data

#Get Playlist Details

def get_playlist_info(channel_id):
    
    next_page_token = None

    All_Data = []

    while True:
        request = youtube.playlists().list(
                        part = 'snippet,contentDetails',
                        channelId = channel_id,
                        maxResults = 50,
                        pageToken = next_page_token)
        response = request.execute()

        for item in response['items']:
            data = dict(Playlist_Id = item['id'],
                        Channel_Id = item['snippet']['channelId'],
                        Playlist_Name = item['snippet']['title'],
                        Channel_Name = item['snippet']['channelTitle'],
                        Published_At = item['snippet']['publishedAt'],
                        Video_count = item['contentDetails']['itemCount'])
            All_Data.append(data)

        next_page_token = response.get('nextPageToken')
        if next_page_token is None:
                break
    return All_Data

#Upload to MongoDB

client = pymongo.MongoClient("mongodb+srv://rashmi:rashmidb@cluster1.q48isro.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1")
db = client["youtube_data"]

def channel_details(channel_id):
    ch_details = get_channel_info(channel_id)
    pl_details = get_playlist_info(channel_id)
    vi_ids = get_video_ids(channel_id)
    vi_details = get_video_info(vi_ids)
    com_details = get_comment_info(vi_ids)
    
    coll1 = db["channel_details"]
    coll1.insert_one({"Channel_information":ch_details,"Playlist_information":pl_details,"Video_information":vi_details,"Comment_information":com_details})
    
    return "upload completed successfully"

#MySQL Tabel creation migrated from Mongodb

#Table creation for channel

def channels_tabel():

    config = {'host' : 'localhost',
              'user' : 'rashmi',
              'password' : 'rashmidb',
              'database' : 'youtube_data'}

    conn = mysql.connector.connect(**config)

    cursor = conn.cursor()

    # Insert Many values in the table

    drop_query = '''drop table IF EXISTS channels'''
    cursor.execute(drop_query)
    conn.commit()

    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS channels (
        Channel_Name VARCHAR(255),
        Channel_Id VARCHAR(255) PRIMARY KEY,
        Subscribers BIGINT,
        Views BIGINT,
        Total_videos INT,
        Channel_Description TEXT,
        Playlist_Id VARCHAR(255)
    );
    '''

    cursor.execute(create_table_sql)

    conn.commit()


    ch_list = []
    db = client["youtube_data"]
    coll1 = db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"Channel_information":1}):
        ch_list.append(ch_data["Channel_information"])
    df = pd.DataFrame(ch_list)

    # Insert values in the MySQL table

    for index,row in df.iterrows():
        insert_qurey = '''INSERT INTO channels (Channel_Name,
                                                Channel_Id,
                                                Subscribers,
                                                Views,
                                                Total_videos,
                                                Channel_Description,
                                                Playlist_Id)

                                                VALUES (%s, %s, %s, %s, %s, %s, %s)'''
        values = (row['Channel_Name'],
                  row['Channel_Id'],
                  row['Subscribers'],
                  row['Views'],
                  row['Total_videos'],
                  row['Channel_Description'],
                  row['Playlist_Id'])

        try:
            cursor.execute(insert_qurey, values)
            conn.commit()

        except:
            print("Channel values are already exists")

#Table creation for playlists

def playlist_table():
    
    config = {'host' : 'localhost',
              'user' : 'rashmi',
              'password' : 'rashmidb',
              'database' : 'youtube_data'}

    conn = mysql.connector.connect(**config)

    cursor = conn.cursor()

    # Insert Many values in the table

    drop_query = '''drop table IF EXISTS playlists'''
    cursor.execute(drop_query)
    conn.commit()

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS playlists (
            Playlist_Id VARCHAR(255) PRIMARY KEY,
            Playlist_Name VARCHAR(255),
            Channel_Id VARCHAR(255),
            Channel_Name VARCHAR(255),
            Published_At TIMESTAMP,
            Video_count INT
    );
    '''

    cursor.execute(create_table_sql)

    conn.commit()
    
    pl_list = []
    db = client["youtube_data"]
    coll1 = db["channel_details"]
    for pl_data in coll1.find({},{"_id":0,"Playlist_information":1}):
        for i in range(len(pl_data["Playlist_information"])):
            pl_list.append(pl_data["Playlist_information"][i])

    df1 = pd.DataFrame(pl_list)
    
# Table connecting to MSQL :

    for index,row in df1.iterrows():
        insert_qurey = '''INSERT INTO playlists (Playlist_Id,
                                                Playlist_Name,
                                                Channel_Id,
                                                Channel_Name,
                                                Published_At,
                                                Video_count)
                                                
                                                VALUES (%s, %s, %s, %s, %s, %s)'''
        published_at_mysql_format = datetime.strptime(row['Published_At'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')

        values = (row['Playlist_Id'],
                  row['Playlist_Name'],
                  row['Channel_Id'],
                  row['Channel_Name'],
                  published_at_mysql_format,
                  row['Video_count'])
                  
     
        cursor.execute(insert_qurey, values)
        conn.commit()


def convert_duration(duration):
            regex = r'PT(\d+H)?(\d+M)?(\d+S)?'
            match = re.match(regex, duration)
            if not match:
                return '00:00:00'
            hours, minutes, seconds = match.groups()
            hours = int(hours[:-1]) if hours else 0
            minutes = int(minutes[:-1]) if minutes else 0
            seconds = int(seconds[:-1]) if seconds else 0
            total_seconds = hours * 3600 + minutes * 60 + seconds
            time_data ='{:02d}:{:02d}:{:02d}'.format(int(total_seconds / 3600), int((total_seconds % 3600) / 60), int(total_seconds % 60))
            format_data = "%H:%M:%S"
            date = datetime.strptime(time_data, format_data)    
            time = date.time()
            return time

#Table creation for videos in MySQL

def videos_table():

    config = {'host' : 'localhost',
              'user' : 'rashmi',
              'password' : 'rashmidb',
              'database' : 'youtube_data'}

    conn = mysql.connector.connect(**config)

    cursor = conn.cursor()

    # Insert Many values in the table

    drop_query = '''drop table IF EXISTS videos'''
    cursor.execute(drop_query)
    conn.commit()

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS videos (
                            Channel_Name VARCHAR(255),
                            Channel_Id VARCHAR(255),
                            Video_Id VARCHAR(255) PRIMARY KEY,
                            Title VARCHAR(255),
                            Thumbnails VARCHAR(255),
                            Description TEXT,
                            Publish_At TIMESTAMP,
                            Duration VARCHAR(255),
                            Views BIGINT,
                            Comments INT,
                            Favorite INT,
                            Likes BIGINT,
                            Definition VARCHAR(255),
                            Caption VARCHAR(255),                        
                            Tags TEXT 
    );
    '''

    cursor.execute(create_table_sql)

    conn.commit()
    
    
    vi_list = []
    db = client["youtube_data"]
    coll1 = db["channel_details"]
    for vi_data in coll1.find({},{"_id":0,"Video_information":1}):
        for i in range(len(vi_data["Video_information"])):
            vi_list.append(vi_data["Video_information"][i])

    df2 = pd.DataFrame(vi_list)
    
    
    # Table connecting to MSQL :

    for index,row in df2.iterrows():
            insert_qurey = '''INSERT INTO videos (Channel_Name,
                                                    Channel_Id,
                                                    Video_Id,
                                                    Title,
                                                    Thumbnails,
                                                    Description,
                                                    Publish_At,
                                                    Duration,
                                                    Views,
                                                    Comments,
                                                    Favorite,
                                                    Likes,
                                                    Definition,
                                                    Caption,                        
                                                    Tags)

                                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
            published_at_mysql_format = datetime.strptime(row['Publish_At'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')

            Duration_formate = convert_duration(row['Duration'])

            tags_str = ', '.join(row['Tags']) if isinstance(row['Tags'], list) else row['Tags']


            values = (row['Channel_Name'],
                      row['Channel_Id'],
                      row['Video_Id'],
                      row['Title'],
                      row['Thumbnails'],
                      row['Description'],                  
                      published_at_mysql_format,
                      Duration_formate,
                      row['Views'],
                      row['Comments'],
                      row['Favorite'],
                      row['Likes'],
                      row['Definition'],
                      row['Caption'],
                      tags_str)


            cursor.execute(insert_qurey, values)
            conn.commit()


# Table creation for comments in MySQL

def comments_table():

    config = {'host' : 'localhost',
              'user' : 'rashmi',
              'password' : 'rashmidb',
              'database' : 'youtube_data'}

    conn = mysql.connector.connect(**config)

    cursor = conn.cursor()

    # Insert Many values in the table

    drop_query = '''drop table IF EXISTS comments'''
    cursor.execute(drop_query)
    conn.commit()

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS comments (Comment_Id VARCHAR(255) PRIMARY KEY,
                                             Video_Id VARCHAR(255),
                                             Comment_Text TEXT,
                                             Comment_Author VARCHAR(255),
                                             comment_Published_Date TIMESTAMP

    );
    '''

    cursor.execute(create_table_sql)

    conn.commit()

    com_list = []
    db = client["youtube_data"]
    coll1 = db["channel_details"]
    for com_data in coll1.find({},{"_id":0,"Comment_information":1}):
        for i in range(len(com_data["Comment_information"])):
            com_list.append(com_data["Comment_information"][i])
    df3 = pd.DataFrame(com_list)

# Table connecting to MSQL :

    for index,row in df3.iterrows():
            insert_qurey = '''INSERT INTO comments (Comment_Id,
                                                     Video_Id,
                                                     Comment_Text,
                                                     Comment_Author,
                                                     comment_Published_Date)

                                                    VALUES (%s, %s, %s, %s, %s)'''
            published_at_mysql_format = datetime.strptime(row['comment_Published_Date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')

            values = (row['Comment_Id'],
                      row['Video_Id'],
                      row['Comment_Text'],
                      row['Comment_Author'],                  
                      published_at_mysql_format
                      )


            cursor.execute(insert_qurey, values)
            conn.commit()

def tables():
    channels_tabel()
    playlist_table()
    videos_table()
    comments_table()
    
    return "Tables created successfully"

def show_channels_table():
    ch_list = []
    db = client["youtube_data"]
    coll1 = db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"Channel_information":1}):
        ch_list.append(ch_data["Channel_information"])
    df = st.dataframe(ch_list)
    
    return df

def show_playlists_table():
    pl_list = []
    db = client["youtube_data"]
    coll1 = db["channel_details"]
    for pl_data in coll1.find({},{"_id":0,"Playlist_information":1}):
        for i in range(len(pl_data["Playlist_information"])):
            pl_list.append(pl_data["Playlist_information"][i])

    df1 = st.dataframe(pl_list)
    
    return df1

def show_videos_table():
    vi_list = []
    db = client["youtube_data"]
    coll1 = db["channel_details"]
    for vi_data in coll1.find({},{"_id":0,"Video_information":1}):
        for i in range(len(vi_data["Video_information"])):
            vi_list.append(vi_data["Video_information"][i])

    df2 = st.dataframe(vi_list)
    
    return df2

def show_comments_table():
    com_list = []
    db = client["youtube_data"]
    coll1 = db["channel_details"]
    for com_data in coll1.find({},{"_id":0,"Comment_information":1}):
        for i in range(len(com_data["Comment_information"])):
            com_list.append(com_data["Comment_information"][i])
    df3 = st.dataframe(com_list)
    
    return df3

# Streamlit Part

with st.sidebar:
    st.header("Skill Take Away")
    st.caption("Python Scripting")
    st.caption("Data Collection")
    st.caption("MongoDB")
    st.caption("API Integration")
    st.caption("Data Management using MongoDB and SQL")

st.title(":red[YOU TUBE DATA HARVESTING AND WAREHOUSING]")   
channel_id = st.text_input("Enter the Channel ID")

if st.button("Collect and Store Data"):
    ch_ids = []
    db = client["youtube_data"]
    coll1 = db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"Channel_information":1}):
        ch_ids.append(ch_data["Channel_information"]["Channel_Id"])
        
    if channel_id in ch_ids:
        st.success("Channels Details of given Channel ID already Exists")
    else:
        insert = channel_details(channel_id)
        st.success(insert)
        
if st.button("Migrate to SQL"):
    Table = tables()
    st.success(Table)
    st.balloons()
    
show_table = st.radio("SELECT THE TABLE FOR VIEW [MONGODB VALUES IN TABLE FORMATE]",("CHANNALS","PLAYLISTS","VIDEOS","COMMENTS"))

if show_table == "CHANNALS":
    show_channels_table()
    
elif show_table == "PLAYLISTS":
    show_playlists_table()
    
elif show_table == "VIDEOS":
    show_videos_table()
    
elif show_table == "COMMENTS":
    show_comments_table()

#Channel Analysis
# Database connection parameters
config = {'host' : 'localhost',
              'user' : 'rashmi',
              'password' : 'rashmidb',
              'database' : 'youtube_data'}

st.header(':orange[Channel Analysis zone]')
st.write('''(Note:- This zone **Analysis of a collection of channel name** shows your Channel Names and gives in table format.)''')
Check_channel = st.checkbox('**Check available channel name for analysis**')

if Check_channel:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    query = "SELECT Channel_Name FROM channels;"
    cursor.execute(query)

    # Fetch results and create a DataFrame
    results = cursor.fetchall()
    conn.commit()
    df_at_sql = pd.DataFrame(results, columns=['Available channel data']).reset_index(drop=True)
    df_at_sql.index += 1  # Reset index to start from 1 instead of 0

    # Show dataframe
    st.dataframe(df_at_sql)

    # Close cursor and connection
    cursor.close()
    conn.close()

# SQL Connection

config = {'host' : 'localhost',
          'user' : 'rashmi',
          'password' : 'rashmidb',
          'database' : 'youtube_data'}

conn = mysql.connector.connect(**config)

cursor = conn.cursor()

st.markdown('<h1 style="color: #ff33db;">SQL Query</h1>', unsafe_allow_html=True)
sql_query = st.checkbox('**Check SQL Query**')
if sql_query:
    questions = st.selectbox("Select Your Questions",("01. The Names of All the Videos and their corresponding Channels",
                                                    "02. Channels have the most number of Videos",
                                                    "03. The Top 10 most viewed Videos and their respective Channels",
                                                    "04. Comments were made on each Video, and their corresponding Video Names",
                                                    "05. Videos have the highest number of Likes, and their corresponding Channel Names",
                                                    "06. The Total number of Likes for each Video, and their corresponding Video Names",
                                                    "07. The Total number of Views for each Channel, and their corresponding Channel Names",
                                                    "08. The Names of All the Channels that have Published Videos in the Year 2022",
                                                    "09. The Average Duration of All Videos in each Channel, and corresponding Channel Names",
                                                    "10. Videos have the highest number of Comments, and their corresponding Channel Names"))

    if questions == "01. The Names of All the Videos and their corresponding Channels":
        query1 = '''SELECT Title as videos, Channel_Name as ChannelName FROM videos'''
        cursor.execute(query1)
        t1 = cursor.fetchall()  # Fetch all results
        conn.commit()

        df = pd.DataFrame(t1, columns=["VideoTitle", "ChannelName"])
        st.write(df)
        
    elif questions == "02. Channels have the most number of Videos":
        query2 = '''SELECT Channel_Name as ChannelName, Total_videos as No_Of_Videos FROM channels
                    ORDER BY Total_videos DESC'''
        cursor.execute(query2)
        t2 = cursor.fetchall()  # Fetch all results
        conn.commit()

        df2 = pd.DataFrame(t2, columns=["ChannelName","No_Of_Videos"])
        st.write(df2)
        st.write("### :green[Number of videos in each channel :]")
        # Create a Plotly Express bar chart
        fig = px.bar(df2,
                    x="ChannelName",
                    y="No_Of_Videos",
                    orientation='v',
                    color="ChannelName"
                    )

        # Display the Plotly chart using Streamlit
        st.plotly_chart(fig, use_container_width=True)
        
    elif questions == "03. The Top 10 most viewed Videos and their respective Channels":
        query3 = '''SELECT Views as views,Channel_Name as ChannelName, Title as VideoTitle FROM videos
                    WHERE Views IS NOT NULL ORDER BY Views DESC LIMIT 10'''
        cursor.execute(query3)
        t3 = cursor.fetchall()  # Fetch all results
        conn.commit()

        df3 = pd.DataFrame(t3, columns=["Views","ChannelName","VideoTitle"])
        st.write(df3)
        st.write("### :green[Top 10 most viewed videos :]")
        # Create a Plotly Express bar chart
        fig = px.bar(df3,
                    x="Views",
                    y="ChannelName",
                    orientation='h',
                    color="VideoTitle"
                    )

        # Display the Plotly chart using Streamlit
        st.plotly_chart(fig, use_container_width=True)
        
    elif questions == "04. Comments were made on each Video, and their corresponding Video Names":
        query4 = '''SELECT Comments as No_of_Comments, Title as VideoTitle FROM videos WHERE Comments IS NOT NULL'''
        cursor.execute(query4)
        t4 = cursor.fetchall()  # Fetch all results
        conn.commit()

        df4 = pd.DataFrame(t4, columns=["No_of_Comments","VideoTitle"])
        st.write(df4)
        
    elif questions == "05. Videos have the highest number of Likes, and their corresponding Channel Names":
        query5 = '''SELECT Title as VideoTitle, Channel_Name as ChannelName, Likes as No_of_Likes FROM videos
                    WHERE Likes IS NOT NULL ORDER BY Likes DESC'''
        cursor.execute(query5)
        t5 = cursor.fetchall()  # Fetch all results
        conn.commit()

        df5 = pd.DataFrame(t5, columns=["VideoTitle","ChannelName","No_of_Likes"])
        st.write(df5)
        
    elif questions == "06. The Total number of Likes for each Video, and their corresponding Video Names":
        query6 = '''SELECT Likes as LikeCounts, Title as VideoTitle FROM videos'''
        cursor.execute(query6)
        t6 = cursor.fetchall()  # Fetch all results
        conn.commit()

        df6 = pd.DataFrame(t6, columns=["LikeCount","VideoTitle"])
        st.write(df6)
        
    elif questions == "07. The Total number of Views for each Channel, and their corresponding Channel Names":
        query7 = '''SELECT Views as ViewCounts, Channel_Name as ChannelName FROM channels'''
        cursor.execute(query7)
        t7 = cursor.fetchall()  # Fetch all results
        conn.commit()

        df7 = pd.DataFrame(t7, columns=["ViewCount","ChannelName"])
        st.write(df7)
        st.write("### :green[Channels vs Views :]")
        # Create a Plotly Express bar chart
        fig = px.bar(df7,
                    x="ChannelName",
                    y="ViewCount",
                    orientation='v',
                    color="ChannelName"
                    )

        # Display the Plotly chart using Streamlit
        st.plotly_chart(fig, use_container_width=True)
        
    elif questions == "08. The Names of All the Channels that have Published Videos in the Year 2022":
        query8 = '''SELECT Title as VideoTitle, Publish_At as VideoReleasDate, Channel_Name as ChannelName FROM videos
                    WHERE EXTRACT(YEAR FROM Publish_At) = 2022'''
        cursor.execute(query8)
        t8 = cursor.fetchall()  # Fetch all results
        conn.commit()

        df8 = pd.DataFrame(t8, columns=["VideoTitle","VideoReleaseDate","ChannelName"])
        st.write(df8)
        
    elif questions == "09. The Average Duration of All Videos in each Channel, and corresponding Channel Names":
        query9 = '''SELECT Channel_Name as ChannelName, TIME_FORMAT(SEC_TO_TIME(AVG(TIME_TO_SEC(TIME(Duration)))), '%H:%i:%s') as AverageDuration FROM videos GROUP BY Channel_Name'''
        cursor.execute(query9)
        t9 = cursor.fetchall()  # Fetch all results
        conn.commit()

        df9 = pd.DataFrame(t9, columns=["ChannelName","AverageDuration"])
        
        T9 = []
        for index,row in df9.iterrows():
            channel_title = row["ChannelName"]
            average_duration = row["AverageDuration"]
            average_duration_str = str(average_duration)
            T9.append(dict(ChannelTitle = channel_title,AvgDuration = average_duration_str))
        df11 = pd.DataFrame(T9)
        st.write(df11)
        st.write("### :green[Avg video duration for channels :]")
            # Create a Plotly Express bar chart
        fig = px.bar(df9,
                    x="ChannelName",
                    y="AverageDuration",
                    orientation='v',
                    color="ChannelName"
                    )

        # Display the Plotly chart using Streamlit
        st.plotly_chart(fig, use_container_width=True)

    elif questions == "10. Videos have the highest number of Comments, and their corresponding Channel Names":
        query10 = '''SELECT Title as VideoTitle, Channel_Name as ChannelName, Comments as comments FROM videos
                    WHERE Comments IS NOT NULL ORDER BY Comments DESC'''
        cursor.execute(query10)
        t10 = cursor.fetchall()  # Fetch all results
        conn.commit()

        df10 = pd.DataFrame(t10, columns=["videoTitle","ChannelName","comments"])
        st.write(df10)

#Showing MySQL table in streamlit
# Database connection parameters
config = {
    'host': 'localhost',
    'user': 'rashmi',
    'password': 'rashmidb',
    'database': 'youtube_data'
}
# Streamlit app
st.header(':green[MySQL Data Viewer]')

Mysql_table = st.checkbox('**Check MySQL Table**')

if Mysql_table:
    # Function to fetch data from the selected table
    def fetch_data(selected_table):
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        query = f"SELECT * FROM {selected_table};"
        cursor.execute(query)

        data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(data, columns=columns)

        cursor.close()
        conn.close()

        return df
    
    # Radio button to select the table
    selected_table = st.radio("Select a table", ["channels", "playlists", "comments", "videos",])

    # Fetch data based on the selected table
    df = fetch_data(selected_table)

    # Show the entire DataFrame using st.table
    st.table(df)

    # If there's a troublesome column, display it separately
    troublesome_column_name = 'troublesome_column'
    if troublesome_column_name in df.columns:
        st.write(f"Troublesome Column ({troublesome_column_name}):")
        st.table(df[troublesome_column_name])

cursor.close()