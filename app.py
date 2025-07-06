import streamlit as st
import yfinance as yf
import requests
import plotly.graph_objs as go
from yahooquery import search
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()


NEWS_API_KEY = os.getenv("NEWS_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def summarize_news_with_gemini(articles, company_name):
    if not articles:
        return "No recent news to summarize."

    combined_text = "\n".join([f"- {a['title']}: {a.get('description', '')}" for a in articles])
    prompt = f"Summarize the following news about {company_name} in 3-4 sentences:\n{combined_text}"

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error summarizing news: {e}"

def display_company_description(info):  
    description = info.get("longBusinessSummary", "No company description available.")  
    st.subheader("🏢 Company Overview")  

    # Show toggle switch  
    show_full_desc = st.toggle("Show full description", value=False)  

    if show_full_desc:  
        st.write(description)  
    else:  
        short_desc = description[:300].rstrip() + "..."  
        st.write(short_desc)  

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
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Closing Price', line=dict(color='royalblue')))
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Closing Price',
        hovermode='x unified',
        template='plotly_dark',
        height=500,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

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

def search_tickers(query):
    try:
        result = search(query)
        if 'quotes' in result:
            return [f"{item['shortname']} ({item['symbol']})" for item in result['quotes']]
        return []
    except Exception as e:
        st.warning(f"Error searching tickers: {e}")
        return []

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
        st.metric("Dividend Yield", f"{dividend_yield if dividend_yield != 'N/A' else 'N/A'}%")

# --- STREAMLIT APP ---
st.set_page_config(page_title="Stock Info App", layout="centered")
st.title("📊 Investor Terminal")

company_query = st.text_input("Search for a company (e.g., Reliance)")
ticker = ""
if company_query:
    matches = search_tickers(company_query)
    if matches:
        ticker_choice = st.selectbox("Select a ticker:", matches)
        if ticker_choice:
            ticker = ticker_choice.split("(")[-1].strip(")")
    else:
        st.warning("No tickers found for your query.")

period_option = st.radio("Select Time Range for Price Chart:", options=["1y", "5y"], horizontal=True)

if ticker:
    with st.spinner("Fetching stock data..."):
        hist, info = fetch_stock_data(ticker, period=period_option)


    if info is not None:
        display_company_description(info)
    

    if hist is not None and info is not None:
        
        st.subheader(f"📈 {period_option.upper()} Stock Price Chart")
        plot_price_chart(hist, f"{ticker.upper()} Closing Price ({period_option.upper()})")

        display_metrics(info)

        with st.spinner("Fetching recent news..."):
            company_name = info.get("longName") or info.get("shortName") or ticker
            articles = fetch_news_headlines(company_name)

        if articles:
            st.subheader("🤖 Gemini News Summary")
            with st.spinner("Generating summary..."):
                summary = summarize_news_with_gemini(articles, company_name)
            st.write(summary)

            st.subheader("📰 Recent News Headlines")
            for article in articles:
                st.markdown(f"**[{article['title']}]({article['url']})**")
                if article.get("description"):
                    st.caption(article['description'])
        else:
            st.write("No news articles found.")
    else:
        st.error("Failed to retrieve stock data. Please check the ticker symbol.")


