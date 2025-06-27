import streamlit as st
import yfinance as yf
import requests
import matplotlib.pyplot as plt
from datetime import date, timedelta

# --- CONFIG ---
NEWS_API_KEY = "254168b4d3e14dbda6836e54bef11447"  # Replace with your NewsAPI key

# --- FUNCTIONS ---
def fetch_stock_data(ticker, period="5y"):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        info = stock.info
        return hist, info
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None, None

def fetch_news_headlines(company_name):
    query = company_name
    url = (
        f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&language=en&pageSize=5&apiKey={NEWS_API_KEY}"
    )
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("status") != "ok":
            return []
        articles = data.get("articles", [])
        return articles[:5]  # return top 5 articles
    except Exception as e:
        st.warning(f"Error fetching news: {e}")
        return []

def plot_price_chart(hist, title):
    fig, ax = plt.subplots(figsize=(10, 4))
    hist['Close'].plot(ax=ax)
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Closing Price")
    ax.grid(True)
    st.pyplot(fig)

def format_large_number(n):
    if n == "N/A" or n is None:
        return "N/A"
    abs_n = abs(n)
    if abs_n >= 1e12:
        return f"{n/1e12:.2f}T"
    elif abs_n >= 1e9:
        return f"{n/1e9:.2f}B"
    elif abs_n >= 1e6:
        return f"{n/1e6:.2f}M"
    elif abs_n >= 1e3:
        return f"{n/1e3:.2f}K"
    else:
        return str(n)

def display_metrics(info):
    current_price = info.get("currentPrice", "N/A")
    pe_ratio = info.get("trailingPE", "N/A")
    market_cap = info.get("marketCap", "N/A")
    dividend_yield = info.get("dividendYield", "N/A")
    currency = info.get("currency", "")

    st.subheader("📌 Key Metrics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Price", f"{currency} {current_price}")
        st.metric("P/E Ratio", pe_ratio)
    with col2:
        st.metric("Market Cap", f"{currency} {format_large_number(market_cap)}")
        st.metric("Dividend Yield", f"{dividend_yield if dividend_yield != 'N/A' else 'N/A'}")

# --- STREAMLIT APP ---
st.set_page_config(page_title="Stock Info App", layout="centered")
st.title("📊 Stock Info and News Viewer")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)")
period_option = st.radio("Select Time Range for Price Chart:", options=["1y", "5y"], horizontal=True)

if ticker:
    with st.spinner("Fetching stock data..."):
        hist, info = fetch_stock_data(ticker, period=period_option)

    if hist is not None and info is not None:
        st.subheader(f"📈 {period_option.upper()} Stock Price Chart")
        plot_price_chart(hist, f"{ticker.upper()} Closing Price ({period_option.upper()})")

        display_metrics(info)

        with st.spinner("Fetching recent news..."):
            company_name = info.get("longName") or info.get("shortName") or ticker
            articles = fetch_news_headlines(company_name)

        if articles:
            st.subheader("📰 Recent News Headlines")
            for article in articles:
                st.markdown(f"**[{article['title']}]({article['url']})**")
                if article.get("description"):
                    st.caption(article['description'])
        else:
            st.write("No news articles found.")
    else:
        st.error("Failed to retrieve stock data. Please check the ticker symbol.")


