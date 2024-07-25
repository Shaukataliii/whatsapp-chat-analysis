from wordcloud import WordCloud
import streamlit as st
from src.data_operations import InsightsProvider
from io import StringIO
from matplotlib import pyplot as plt
import seaborn as sns


st.set_page_config("analyzer", page_icon=":bar_chart:")
insights_provider = InsightsProvider()

st.title("Whatsapp chat analyzer :bar_chart:")
with st.sidebar:
    chat_file = st.file_uploader("Choose a file", type="txt", accept_multiple_files=False)

if chat_file is not None:
    string_obj = StringIO(chat_file.getvalue().decode("utf-8"))
    chat = string_obj.read()
    members = insights_provider.get_members(chat)

    # displaying member names and getting selected member
    with st.sidebar:
        selected_member = st.selectbox("Choose member", options=members)
        analyze_btn = st.button("Analyze", type="primary")

    # header information
    if analyze_btn:
        insights = insights_provider.gather_insights(selected_member)
        insights_keys = list(insights.keys())
        insights_values = list(insights.values())

        # 1st section - header
        for col_no, col in enumerate(st.columns(4)):
           with col:
               heading = insights_keys[col_no].replace("_", " ").title()
               st.write(heading)
               st.write(str(insights_values[col_no]))
    
        # monthly activity
        st.subheader("Monthyly Activity")
        activity = insights['monthly_activity']

        fig, ax = plt.subplots()
        ax.plot(activity['month'], activity['num_messages'], marker = 'o')
        ax.set_xlabel('Month')
        ax.set_ylabel('Number of Messages')
        ax.set_title('Messages per Month')
        ax.set_xticklabels(activity['month'], rotation=90)
        st.pyplot(fig)

        # daily activity
        st.subheader("Daily Activity")
        activity = insights['daily_activity']

        fig, ax = plt.subplots()
        ax.plot(activity['day'], activity['num_messages'], marker = 'o', color='red')
        ax.set_xlabel('Day')
        ax.set_ylabel('Number of Messages')
        ax.set_title('Messages per Day')
        ax.xaxis.set_ticklabels([])
        st.pyplot(fig)

        # most busy day and month
        for col_no, col in enumerate(st.columns(2)):
            with col:
                if col_no == 0:
                    st.subheader("Most busy Day")
                    activity = insights['most_busy_days']
                    timeline = "day"
                    colormap = "cool_r"
                else:
                    st.subheader("Most busy Month")
                    activity = insights['most_busy_months']
                    timeline = "month"
                    colormap = "cool"

                fig, ax = plt.subplots()
                ax.bar(activity[timeline], activity['num_messages'], color = insights_provider.generate_colors(activity, colormap))
                ax.set_xlabel(timeline.title())
                ax.set_ylabel("Number of Messages")
                ax.set_title(f"Most busy {timeline.title()}")
                ax.set_xticklabels(activity[timeline], rotation=90)
                st.pyplot(fig)

        # Period-wise Activity
        st.subheader("Period-wise Activity")
        activity = insights['periodwise_activity']
        
        fig, ax = plt.subplots()
        ax = sns.heatmap(activity)
        ax.set_xlabel('Period')
        ax.set_ylabel('Day')
        ax.set_title('Period-wise Activity')
        st.pyplot(fig)

        # busy users
        st.subheader("Most busy users")

        activity = insights['most_busy_users']
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots()
            ax.barh(activity['username'], activity['num_messages'], color = insights_provider.generate_colors(activity, 'prism'))
            ax.set_xlabel('Number of Messages')
            ax.set_ylabel('Username')
            ax.set_title('Number of messages by each user')
            st.pyplot(fig)

        with col2:
            st.dataframe(activity)

        # wordcloud
        st.subheader("Most common words")
        top_words_dict, wordcloud_img = insights_provider.get_topwords_dict_and_wordcloud_fig()
        st.image(wordcloud_img.to_array())