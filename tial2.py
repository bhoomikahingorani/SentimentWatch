import streamlit as st
import requests
import pandas as pd
import plotly.graph_objs as go
import mplfinance as mpf
from newsapi import NewsApiClient
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import base64
import matplotlib.pyplot    as plt
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

# nltk.download('vader_lexicon')

st.set_page_config(page_title="Sentiment Watch", layout="wide")

# Define API keys (for security, consider storing these in environment variables)
ALPHA_VANTAGE_API_KEY = st.secrets["api_keys"]["ALPHA_VANTAGE_API_KEY"]
NEWSAPI_API_KEY = st.secrets["api_keys"]["NEWSAPI_API_KEY"]

try:
    from transformers import pipeline
    transformers_available = True
except ImportError:
    transformers_available = False
    st.error("Transformers library is not available. Please install it using 'pip install transformers'")

def fetch_stock_data(api_key, symbol, function, interval=None):
    if function == 'TIME_SERIES_INTRADAY':
        url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&interval={interval}&apikey={api_key}'
    else:
        url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={api_key}'
    r = requests.get(url, verify=False)
    data = r.json()
    return data

def process_data(data, function):
    time_series_key = {
        'TIME_SERIES_INTRADAY': 'Time Series (5min)',
        'TIME_SERIES_DAILY': 'Time Series (Daily)',
        'TIME_SERIES_WEEKLY': 'Weekly Time Series',
        'TIME_SERIES_MONTHLY': 'Monthly Time Series',
    }

    if time_series_key[function] in data:
        time_series = data[time_series_key[function]]
        df = pd.DataFrame.from_dict(time_series, orient='index', dtype=float)
        df.index = pd.to_datetime(df.index)
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume'][:len(df.columns)]
        return df
    else:
        return None

def fetch_news(api_key, query, num_articles=10):
    newsapi = NewsApiClient(api_key=api_key)
    all_articles = newsapi.get_everything(q=query, language='en', sort_by='relevancy', page_size=num_articles)
    return all_articles

def analyze_sentiment_vader(text):
    sid = SentimentIntensityAnalyzer()
    sentiment = sid.polarity_scores(text)
    return sentiment

def analyze_sentiment_roberta(text):
    if transformers_available:
        sentiment_pipeline = pipeline("sentiment-analysis")
        sentiment = sentiment_pipeline(text)
        return sentiment
    else:
        return "Transformers library not available"

def plot_vader_sentiment(sentiment):
    labels = ['Negative', 'Neutral', 'Positive']
    scores = [sentiment['neg'], sentiment['neu'], sentiment['pos']]
    
    fig, ax = plt.subplots()
    ax.bar(labels, scores, color=['red', 'grey', 'green'])
    ax.set_ylabel('Scores')
    ax.set_title('VADER Sentiment Analysis')
    st.pyplot(fig)

def plot_roberta_sentiment(sentiment):
    labels = ['Positive', 'Negative']
    if sentiment['label'] == 'POSITIVE':
        scores = [sentiment['score'], 1 - sentiment['score']]
    else:
        scores = [1 - sentiment['score'], sentiment['score']]
    
    fig, ax = plt.subplots()
    ax.pie(scores, labels=labels, autopct='%1.1f%%', colors=['green', 'red'])
    ax.set_title('RoBERTa Sentiment Analysis')
    st.pyplot(fig)

def extract_sentiment(roberta_output):
    if isinstance(roberta_output, dict) and 'score' in roberta_output:
        return roberta_output['score']  # Return the 'score' from the RoBERTa output
    else:
        return None 


def get_base64_image(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def load_css():
    title_bg_image_file = 'D:/Project/SentimentWatch/stock.png'
    base64_title_image = get_base64_image(title_bg_image_file)

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
    body {{
        background-color: #f4f4f9;
        color: #2c3e50;
        font-family: 'Montserrat', sans-serif;
    }}

    .title-container {{
        background-image: url("data:image/png;base64,{base64_title_image}");
        background-size: cover;
        background-position: center;
        text-align: center;
        padding: 60px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        animation: fadeIn 1.5s;
    }}

    .title-container h1 {{
        color: #fff;
        font-size: 3em;
        font-weight: 700;
        margin: 0;
    }}

    .sidebar {{
        background-color: #1abc9c;
        color: #ecf0f1;
        padding: 20px;
        border-radius: 10px;
        animation: fadeInLeft 1.5s;
    }}

    .sidebar input, .sidebar select, .sidebar button {{
        margin: 10px 0;
        padding: 10px;
        width: 100%;
        border-radius: 5px;
        border: 1px solid #ccc;
        background-color: #16a085;
        color: #ecf0f1;
        transition: all 0.3s ease;
    }}

    .sidebar button {{
        background-color: #e74c3c;
        font-weight: 700;
    }}

    .sidebar button:hover {{
        background-color: #c0392b;
    }}

    .stSpinner > div {{
        border-top-color: #e74c3c;
        animation: spin 1s linear infinite;
    }}

    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}

    .main-container {{
        padding: 20px;
        border-radius: 10px;
        background-color: #ecf0f1;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        animation: fadeInRight 1.5s;
        display: flex;
        justify-content: space-between;
    }}

    .news-container {{
        width: 300px;
        margin-left: 20px;
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}

    @keyframes fadeInLeft {{
        from {{ opacity: 0; transform: translateX(-50px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}

    @keyframes fadeInRight {{
        from {{ opacity: 0; transform: translateX(50px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}

    h2 {{
        color: #34495e;
        font-weight: 700;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def load_html():
    with open("D:/Project/SentimentWatch/index.html") as f:
        st.markdown(f.read(), unsafe_allow_html=True)

load_css()
load_html()

st.markdown('<div class="title-container"><h1>Sentiment Watch</h1></div><br>', unsafe_allow_html=True)

# Layout with columns
col1, col2 = st.columns((2, 1), gap='large')  # Adjust column widths if necessary

# Sidebar for filters
with st.sidebar:
    st.header("Filters")
    symbol = st.text_input("Stock Symbol (e.g., IBM):")
    function = st.selectbox("Data Interval:", [
        'TIME_SERIES_INTRADAY',
        'TIME_SERIES_DAILY',
        'TIME_SERIES_WEEKLY',
        'TIME_SERIES_MONTHLY'
    ])
    interval = None
    if function == 'TIME_SERIES_INTRADAY':
        interval = st.selectbox("Intraday Interval:", ['1min', '5min', '15min', '30min', '60min'])

    st.subheader("Technical Indicators")
    ma_window = st.number_input("Moving Average Window (days)", min_value=1, max_value=100, value=20)
    show_bollinger_bands = st.checkbox("Show Bollinger Bands")

    st.subheader("News")
    num_articles = st.number_input("Number of Articles", min_value=1, max_value=100, value=10)

    st.subheader("Actions")
    fetch_data_button = st.button("Fetch Data")


with col1:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    if fetch_data_button:
        with st.spinner(''):
            # Fetch stock data
            data = fetch_stock_data(ALPHA_VANTAGE_API_KEY, symbol, function, interval)
            df = process_data(data, function)
            
            if df is not None:
                df.index = pd.to_datetime(df.index)
                df['timestamp'] = df.index  # Creating a 'timestamp' column for merging
                st.success("Data fetched successfully!")
                
                # Calculating Moving Average
                df[f'MA{ma_window}'] = df['Close'].rolling(window=ma_window).mean()

                # Bollinger Bands Calculation
                if show_bollinger_bands:
                    df['BB_upper'] = df[f'MA{ma_window}'] + 2 * df['Close'].rolling(window=ma_window).std()
                    df['BB_lower'] = df[f'MA{ma_window}'] - 2 * df['Close'].rolling(window=ma_window).std()

                st.subheader(f"{symbol} Data ({function})")
                st.write(df)

                # Plotly Candlestick Chart
                st.subheader("Candlestick Chart with Plotly")
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='Candlesticks'
                )])

                fig.add_trace(go.Scatter(x=df.index, y=df[f'MA{ma_window}'], mode='lines', name=f'MA{ma_window}'))

                if show_bollinger_bands:
                    fig.add_trace(go.Scatter(x=df.index, y=df['BB_upper'], mode='lines', name='BB Upper', line=dict(color='rgba(0, 0, 255, 0.2)')))
                    fig.add_trace(go.Scatter(x=df.index, y=df['BB_lower'], mode='lines', name='BB Lower', line=dict(color='rgba(0, 0, 255, 0.2)')))

                fig.update_layout(
                    title=f"{symbol} Candlestick Chart ({function})",
                    xaxis_title='Date',
                    yaxis_title='Price',
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig)

                # mplfinance Candlestick Chart
                
                st.subheader("Candlestick Chart with mplfinance")
                ap = [mpf.make_addplot(df[f'MA{ma_window}'], color='orange')]
                if show_bollinger_bands:
                    ap.append(mpf.make_addplot(df['BB_upper'], color='blue'))
                    ap.append(mpf.make_addplot(df['BB_lower'], color='blue'))

                fig_mpf, ax = mpf.plot(df, type='candle', style='charles', title=f'{symbol} Candlestick Chart ({function})', ylabel='Price', addplot=ap, returnfig=True)
                st.pyplot(fig_mpf)

                # Closing Prices
                st.subheader("Closing Prices")
                st.line_chart(df['Close'])

                news_data = fetch_news(NEWSAPI_API_KEY, symbol, num_articles)
                articles = news_data.get("articles", [])
                df_news = pd.DataFrame(articles)

                df_news['publishedAt'] = pd.to_datetime(df_news['publishedAt']).dt.tz_localize(None)

                df_news['title'] = df_news['title'].astype(str)

                # VADER Sentiment 
                df_news['vader_compound'] = df_news['title'].apply(lambda title: analyze_sentiment_vader(title)['compound'])

                # Merge DataFrames on timestamp for VADER
                merged_df_vader = pd.merge_asof(df.sort_values('timestamp'), df_news.sort_values('publishedAt'), left_on='timestamp', right_on='publishedAt', direction='backward')

                # Calculate price change percentage for VADER
                merged_df_vader['price_change'] = merged_df_vader['Close'].pct_change()

                #st.write(merged_df_vader)

                #correlation for VADER
                st.subheader("VADER Sentiment Score vs. Stock Price Change")
                fig_vader, ax_vader = plt.subplots(figsize=(10, 6))
                ax_vader.scatter(merged_df_vader['vader_compound'], merged_df_vader['price_change'])
                ax_vader.set_title("VADER Sentiment Score vs. Stock Price Change")
                ax_vader.set_xlabel("Sentiment Score")
                ax_vader.set_ylabel("Stock Price Change (%)")
                st.pyplot(fig_vader)

                # RoBERTa Sentiment 
                df_news['roberta_sentiment'] = df_news['title'].apply(lambda title: analyze_sentiment_roberta(title))
                #st.write(roberta_sentiment)

                df_news['roberta_sentiment_score'] = df_news['roberta_sentiment'].apply(extract_sentiment)
                #st.write(extract_sentiment(roberta_output)) 

                st.write(df_news)
                # Ensure the RoBERTa sentiment score is a scalar (e.g., float)
                df_news['roberta_sentiment_score'] = df_news['roberta_sentiment_score'].apply(lambda x: float(x) if isinstance(x, (int, float)) else None)
                

                # Merge DataFrames on timestamp for RoBERTa
                merged_df_roberta = pd.merge_asof(df.sort_values('timestamp'), df_news.sort_values('publishedAt'), left_on='timestamp', right_on='publishedAt', direction='backward')

                # Calculate price change percentage for RoBERTa
                merged_df_roberta['price_change'] = merged_df_roberta['Close'].pct_change()

                #st.write(merged_df_roberta)
                #Visualize the correlation for RoBERTa
                st.subheader("RoBERTa Sentiment Score vs. Stock Price Change")
                fig_roberta, ax_roberta = plt.subplots(figsize=(10, 6))
                ax_roberta.scatter(merged_df_roberta['roberta_sentiment_score'], merged_df_roberta['price_change'])
                ax_roberta.set_title("RoBERTa Sentiment Score vs. Stock Price Change")
                ax_roberta.set_xlabel("Sentiment Score")
                ax_roberta.set_ylabel("Stock Price Change (%)")
                st.pyplot(fig_roberta)
            else:
                st.error("Error fetching data or data not available.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="news-container">', unsafe_allow_html=True)
    
    if fetch_data_button and news_data:
        st.success("News fetched successfully!")
        with st.expander("Click here for news articles"):
            for article in news_data['articles']:
                st.markdown(f"### {article['title']}")
                st.markdown(f"**Source**: {article['source']['name']}")
                st.markdown(f"**Published At**: {article['publishedAt']}")
                st.markdown(f"**Description**: {article['description']}")
                st.markdown(f"[Read more]({article['url']})")

                vader_sentiment = analyze_sentiment_vader(article['description'])
                st.markdown(f"**VADER Sentiment**: {vader_sentiment}")
                plot_vader_sentiment(vader_sentiment)

                if transformers_available:
                    roberta_sentiment = analyze_sentiment_roberta(article['description'])
                    roberta_result = roberta_sentiment[0]
                    st.markdown(f"**RoBERTa Sentiment**: {roberta_result}")
                    plot_roberta_sentiment(roberta_result)

    st.markdown('</div>', unsafe_allow_html=True)
