import streamlit as st
import preprocessor, helper
import matplotlib.pyplot as plt
import seaborn as sns
from textblob import TextBlob
import emoji
import pyrebase

# Firebase Configuration
firebaseConfig = {
    "apiKey": "AIzaSyDIWx9s4KJitMtUbb1opfbgEOUq6dQBO8o",
    "authDomain": "whatsapp-chat-94f1d.firebaseapp.com",
    "projectId": "whatsapp-chat-94f1d",
    "storageBucket": "whatsapp-chat-94f1d.appspot.com",
    "messagingSenderId": "905197962606",
    "appId": "1:905197962606:web:2d9cc6276bffa5a10aed7f",
    "measurementId": "G-F5Q1ND0YV1",
    "databaseURL": "https://whatsapp-chat-94f1d-default-rtdb.firebaseio.com/"
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# Authentication Functions
def sign_up(email, password):
    try:
        user = auth.create_user_with_email_and_password(email, password)
        return user
    except Exception as e:
        error_str = str(e)
        if "EMAIL_EXISTS" in error_str:
            st.error("Email already exists")
        elif "WEAK_PASSWORD" in error_str:
            st.error("Password must be at least 6 characters long")
        else:
            st.error(f"Signup failed: {e}")
        return None

def sign_in(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return user
    except Exception as e:
        error_str = str(e)
        if "INVALID_LOGIN_CREDENTIALS" in error_str:
            st.error("Invalid login credentials")
        else:
            st.error(f"Login failed: {e}")
        return None

def logout():
    st.session_state.user = None
    st.session_state.auth_mode = "Login"

def login_clicked():
    global email, password
    user = sign_in(email, password)
    if user:
        st.session_state.user = user
        st.sidebar.success("Login successful")

def logout_clicked():
    logout()
    st.sidebar.success("Logout successful")

# Streamlit App
st.sidebar.title("Whatsapp Chat Analyzer")

# Manage Authentication State
if 'user' not in st.session_state:
    st.session_state.user = None
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = "Login"

if st.session_state.user:
    st.sidebar.write(f"Welcome {st.session_state.user['email']}")
    
    st.sidebar.button("Logout", on_click=logout_clicked)
    
    uploaded_file = st.sidebar.file_uploader("Choose a file")
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        data = bytes_data.decode("utf-8")
        df = preprocessor.preprocess(data)

       # Fetch unique users
        user_list = df['user'].unique().tolist()
        user_list.remove('group_notification')
        user_list.sort()
        user_list.insert(0, "Overall")

        selected_user = st.sidebar.selectbox("Show analysis wrt", user_list)

        if st.sidebar.button("Show Analysis"):

            # Stats Area
            num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
            st.title("Top Statistics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.header("Total Messages")
                st.title(num_messages)
            with col2:
                st.header("Total Words")
                st.title(words)
            with col3:
                st.header("Media Shared")
                st.title(num_media_messages)
            with col4:
                st.header("Links Shared")
                st.title(num_links)

            # Sentiment Analysis
            st.title("Sentiment Analysis")
            sentiment = helper.sentiment_analysis(selected_user, df)
            if sentiment > 0:
                st.header(f"Overall Sentiment: Positive {emoji.emojize(':smiley:')} ({sentiment:.2f})")
            elif sentiment < 0:
                st.header(f"Overall Sentiment: Negative {emoji.emojize(':disappointed:')} ({sentiment:.2f})")
            else:
                st.header(f"Overall Sentiment: Neutral {emoji.emojize(':neutral_face:')} ({sentiment:.2f})")

            # Monthly timeline
            st.title("Monthly Timeline")
            timeline = helper.monthly_timeline(selected_user, df)
            fig, ax = plt.subplots()
            ax.plot(timeline['time'], timeline['message'], color='green')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

            # Daily timeline
            st.title("Daily Timeline")
            daily_timeline = helper.daily_timeline(selected_user, df)
            fig, ax = plt.subplots()
            ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='black')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

            # Activity map
            st.title('Activity Map')
            col1, col2 = st.columns(2)

            with col1:
                st.header("Most busy day")
                busy_day = helper.week_activity_map(selected_user, df)
                fig, ax = plt.subplots()
                ax.bar(busy_day.index, busy_day.values, color='purple')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)

            with col2:
                st.header("Most busy month")
                busy_month = helper.month_activity_map(selected_user, df)
                fig, ax = plt.subplots()
                ax.bar(busy_month.index, busy_month.values, color='orange')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)

            st.title("Weekly Activity Map")
            user_heatmap = helper.activity_heatmap(selected_user, df)
            fig, ax = plt.subplots()
            ax = sns.heatmap(user_heatmap)
            st.pyplot(fig)

            # Finding the busiest users in the group (Group level)
            if selected_user == 'Overall':
                st.title('Most Busy Users')
                x, new_df = helper.most_busy_users(df)
                fig, ax = plt.subplots()

                col1, col2 = st.columns(2)

                with col1:
                    ax.bar(x.index, x.values, color='red')
                    plt.xticks(rotation='vertical')
                    st.pyplot(fig)
                with col2:
                    st.dataframe(new_df)

            # WordCloud
            st.title("Wordcloud")
            df_wc = helper.create_wordcloud(selected_user, df)
            fig, ax = plt.subplots()
            ax.imshow(df_wc)
            st.pyplot(fig)

            # Most common words
            most_common_df = helper.most_common_words(selected_user, df)
            fig, ax = plt.subplots()
            ax.barh(most_common_df[0], most_common_df[1])
            plt.xticks(rotation='vertical')

            st.title('Most common words')
            st.pyplot(fig)

            # Emoji analysis
            emoji_df = helper.emoji_helper(selected_user, df)
            st.title("Emoji Analysis")

            col1, col2 = st.columns(2)

            with col1:
                st.dataframe(emoji_df)
            with col2:
                fig, ax = plt.subplots()
                ax.pie(emoji_df[1].head(), labels=emoji_df[0].head(), autopct="%0.2f")
                st.pyplot(fig)

else:
    st.sidebar.title("Login / Signup")
    
    auth_mode = st.sidebar.selectbox("Choose Login/Signup", ["Login", "Signup"])

    if auth_mode == "Signup":
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Signup"):
            user = sign_up(email, password)
            if user:
                st.session_state.user = user
                st.sidebar.success("Signup successful. Please login.")
            else:
                st.sidebar.error("Signup failed. Try again.")
    else:
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Password", type="password")
        login_button = st.sidebar.button("Login", on_click=login_clicked)
