import os, re, string, emoji
import pandas as pd
import numpy as np
from urlextract import URLExtract
from langdetect import detect, detect_langs
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist

from googletrans import Translator
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors

nltk.download('punkt')
nltk.download('stopwords')
cwd = os.getcwd()
project_dir = os.path.join(cwd)
chat = ""


class WordsProcessor:
    def __init__(self):
        self.translator = Translator()

    def get_stop_words_list(self):
        stop_words = stopwords.words('english')
        roman_urdu = self.read_txtfile(os.path.join(project_dir, "data", "roman-urdu-stopwords.txt")).split('\n')
        stop_words.extend(roman_urdu)
        return stop_words
    
    def read_txtfile(self, filepath):
        if self.path_exists(filepath):
            with open(filepath, 'r') as file:
                contents = file.read()
                return contents
            
    def path_exists(self, filepath):
        if os.path.exists(filepath):
            return True
        else:
            raise Exception(f"Stopwords file doesn't exist. Provided path: {filepath}")

    def translate_urdu_words(self, words: list):
        for index, word in enumerate(words):
            print(f"processing word: {word}")
            if self.detect_urdu_word(word):
                translation = self.translate_word(word)
                words[index] = translation
        return words

    def detect_urdu_word(self, word: str):
        try:
            lang = self.detect(word)
            if lang=='ur':
                return True
        except:
            lang = False

    def translate_word(self, urdu_text: str):
        for entry_no in range(3):
            try:
                translation = self.translator.translate(urdu_text, src='ur', dest='en').text
                return translation
            except:
                continue
        return urdu_text

    def separate_urdu_nonurdu_words(self, words: list):
        urdu_words = []
        nonurdu_words = []
        for word in words:
            print(word)
            try:
                lang = self.detect(word)
            except:
                lang = "null"
            
            if lang == 'ur':
                urdu_words.append(word)
            elif lang != 'ur' and lang != 'null':
                nonurdu_words.append(word)

        return (urdu_words, nonurdu_words)

    def map_urdu_word_to_na(self, word: str):
        if self.detect_urdu_word(word):
            return pd.NA
        else:
            return word
words_processor = WordsProcessor()

class DetailsProvider:
    def __init__(self):
        self.urlextract = URLExtract()

    def get_month_year_str(self, datetime_val):
        month_name = datetime_val.month_name()
        year = datetime_val.year
        return f"{month_name}-{year}"

    def get_day_month_year_str(self, datetime_val):
        day = datetime_val.day
        month_name =datetime_val.month_name()
        year = datetime_val.year
        return f'{day}-{month_name}-{year}'
    
    def get_all_member(self, df):
        members = list(df['username'].unique())
        members.insert(0, "All members")
        return members
    
    def filter_df(self, df, selected_member):
        if selected_member == 'All members':
            return df
        else:
            return df[df['username'] == selected_member]

    def get_total_messages_count(self, df):
        return len(df['message'])
    
    def get_total_words_count(self, df):
        num_words = 0
        for message in df['message']:
            message_num_words = len(word_tokenize(message))
            num_words += message_num_words

        return num_words    

    def get_media_messages_count(self, df):
        total_media_count = 0
        for message in df['message']:
            if message.__contains__('<Media omitted>\n'):
                total_media_count+=1
        return total_media_count

    def get_urls_count(self, df):
        urls_count = 0
        for message in df['message']:
            urls = self.urlextract.find_urls(message)
            num_urls = len(urls)
            urls_count+=num_urls
        return urls_count
    
    def get_monthly_activity_df(self, df):
        monthly_activity = pd.DataFrame(df.groupby('month-year')['message'].count().reset_index())
        return monthly_activity.rename(columns={'month-year': 'month', 'message': 'num_messages'})
    
    def get_daily_activity_df(self, df):
        daily_activity = pd.DataFrame(df.groupby('day-month-year')['message'].count().reset_index())
        return daily_activity.rename(columns={'day-month-year': 'day', 'message': 'num_messages'})
    
    def get_most_busy_months_activity_df(self, df):
        u_months_activity = pd.DataFrame(df.groupby('month')['message'].count().reset_index())
        return u_months_activity.rename(columns={'month': 'month', 'message': 'num_messages'})
    
    def get_most_busy_days_activity_df(self, df):
        u_days_activity = pd.DataFrame(df.groupby('day-name')['message'].count().reset_index())
        return u_days_activity.rename(columns={'day-name': 'day', 'message': 'num_messages'})
    
    def get_hourwise_activity_df(self, df):
        df['hour'] = df['datetime'].dt.hour
        df['period'] = df['hour'].apply(self.generate_time_periods)
        hourwise_activity = pd.DataFrame(df.groupby(['day-name', 'period'])['message'].count().reset_index())
        hourwise_activity = hourwise_activity.rename(columns={'day-name': 'day', 'period': 'period', 'message': 'num_messages'})
        return hourwise_activity.pivot(index='day', columns='period', values='num_messages').fillna(0)
    
    def generate_time_periods(self, hour_val):
        if hour_val == '23':
            return f"{str(hour_val)} - {'00'}"
        elif hour_val == '00':
            return f"{'00'} - {str(hour_val + 1)}"
        else:
            return f"{str(hour_val)} - {str(hour_val + 1)}"
    
    def get_10_most_busy_users_activity_df(self, df):
        users_activity = pd.DataFrame(df.groupby('username')['message'].count().sort_values(ascending=False))
        users_activity = users_activity.head(20).reset_index()
        return users_activity.rename(columns={'message': 'num_messages'})
    
    def get_top_words_dict(self, words: list, limit: int):
        # perform words transformation here
        words = self.perform_occurence_count(words)
        return dict(words[:limit])

    def perform_occurence_count(self, words: list):
        occurence_count = dict(FreqDist(words))
        occurence_count = sorted(occurence_count.items(), key = lambda item: item[1], reverse=True)
        return occurence_count
    
    def get_wordcloud(self, df):
        # dict of most common words will be provided and return wordcloud
        return []
details_provider = DetailsProvider()

class MessageProcessor:
    def __init__(self):
        self.punctuations = string.punctuation
    def preprocess_messages(self, text: str):
        text = self.remove_url(text)
        text = self.replace_emojies(text)
        text = self.remove_punctuations(text)
        text = self.tokenize(text)
        text = self.remove_stopwords(text)
        text = self.remove_numbers(text)
        text = self.remove_1_char_words(text)
        return text

    def remove_url(self, text: str):
        url_pattern = r'https?://\S+|www\.\S+'
        return re.sub(url_pattern, "", text)

    def replace_emojies(self, text: str):
        return emoji.demojize(text)

    def remove_punctuations(self, text: str):
        for mark in self.punctuations:
            if mark in text:
                text = text.replace(mark, "")
        return text

    def tokenize(self, text: str):
        return word_tokenize(text)

    def remove_stopwords(self, text: list):
        stop_words = words_processor.get_stop_words_list()
        text = [word for word in text if word not in stop_words]
        return text

    def remove_numbers(self, text: list):
        return [word for word in text if not str(word).isnumeric()]

    def remove_1_char_words(self, text: str):
        return [word for word in text if not len(word) == 1]    
message_processor = MessageProcessor()

class DFPreparor:
    def __init__(self):
        self.df = pd.DataFrame()
    
    def prepare_df(self, chat):
        self.chat = chat
        self.create_datetime_message_cols_from_chat()
        self.create_message_username_cols()
        self.create_insights_cols()
        return self.df

    def create_datetime_message_cols_from_chat(self):
        regex_for_datetime = "\d{1,2}/\d{1,2}/\d{2}, \d{1,2}:\d{2}\s[AP]M"
        messages = re.split(regex_for_datetime, self.chat)[1:]
        datetime = re.findall(regex_for_datetime, self.chat)
        self.df = pd.DataFrame({'datetime': datetime, 'message': messages})

    def create_message_username_cols(self):
        regex_for_username = '([\w\W]+?):\s'
        usernames = []
        messages = []

        for message in self.df['message']:
            message = re.split(regex_for_username, message)
            if len(message) > 1:
                username = message[1]
                message = message[2]
            else:
                username = 'group notification'
                message = message[0]
            username = self.remove_dash_strip(username)
            username = self.correct_username(username)
            usernames.append(username)
            messages.append(message)

        self.df['username'] = usernames
        self.df['message'] = messages

    def remove_dash_strip(self, text: str):
        return text.replace("-", "").strip()   

    def correct_username(self, username: str):
        group_word_find_res = username.find("group")
        if group_word_find_res == -1:
            return username
        else:
            return "group notification" 

    def create_insights_cols(self):
        self.df['datetime'] = pd.to_datetime(self.df['datetime'], format="%m/%d/%y, %I:%M %p")
        self.df['year'] = self.df['datetime'].dt.year
        self.df['month'] = self.df['datetime'].dt.month_name()
        self.df['day'] = self.df['datetime'].dt.day
        self.df['day-name'] = self.df['datetime'].dt.day_name()
        self.df['time'] = self.df['datetime'].dt.time
        self.df['month-year'] = self.df['datetime'].apply(details_provider.get_month_year_str)
        self.df['day-month-year'] = self.df['datetime'].apply(details_provider.get_day_month_year_str)
df_preparor = DFPreparor()

class InsightsProvider:
    def get_members(self, chat):
        self.df = df_preparor.prepare_df(chat)
        return details_provider.get_all_member(self.df)

    def gather_insights(self, selected_member):
        df = details_provider.filter_df(self.df, selected_member)
        insights = {
        'total_messages' : details_provider.get_total_messages_count(df),
        'total_words' : details_provider.get_total_words_count(df),
        'total_media_shared' : details_provider.get_media_messages_count(df),
        'total_links_shared' : details_provider.get_urls_count(df),
        'monthly_activity' : details_provider.get_monthly_activity_df(df),
        'daily_activity' : details_provider.get_daily_activity_df(df),
        'most_busy_days' : details_provider.get_most_busy_days_activity_df(df),
        'most_busy_months' : details_provider.get_most_busy_months_activity_df(df),
        'periodwise_activity' : details_provider.get_hourwise_activity_df(df),
        'most_busy_users' : details_provider.get_10_most_busy_users_activity_df(df)
        }
        return insights
    
    def get_topwords_dict_and_wordcloud_fig(self):
        all_words = []
        for message in self.df['message']:
            print(message)
            all_words.extend(message_processor.preprocess_messages(message))

        translated_words = words_processor.translate_urdu_words(all_words)

        words = pd.DataFrame()
        words['all_words'] = all_words
        words['translated_words'] = translated_words

        top_100_words_with_dict = details_provider.get_top_words_dict(words['translated_words'], 100)
        top_100_words = " ".join(list(top_100_words_with_dict.keys()))

        wordcloud = WordCloud(height=800, width=1000, background_color='white', colormap='viridis')
        wordcloud = wordcloud.generate(top_100_words)
        plt.axis('off')
        
        return (top_100_words_with_dict, wordcloud)
    
    def generate_colors(self, activity, cmap = 'viridis'):
        norm = mcolors.Normalize(vmin=activity['num_messages'].min(), vmax=activity['num_messages'].max())
        cmap = cm.get_cmap(cmap)
        bar_colors = cmap(norm(activity['num_messages']))
        return bar_colors