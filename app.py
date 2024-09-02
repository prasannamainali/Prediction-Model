import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from textblob import TextBlob
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import os
import random

# Configuration
TICKERS = [
    "AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NFLX", "NVDA", "BA", "IBM",
    "INTC", "WMT", "DIS", "AMD", "CSCO", "ORCL", "MCD", "PFE", "V", "MA",
    "JPM", "UNH", "HD", "KO", "PEP", "T", "VZ", "XOM", "CVX", "GS",
    "NIO", "BYND", "PLTR", "RBLX", "CRSP", "EDIT", "SGMO", "TIGR", "ZM", "DOCU"
]

PREDICTIONS_FILE = 'predictions.csv'
FEEDBACK_FILE = 'feedback.csv'
COLLECTED_DATA_FILE = 'collected_data.csv'
KILL_SWITCH_FILE = 'kill_switch.txt'

# Initialize sentiment analyzer
def analyze_sentiment_textblob(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    return "Positive" if sentiment > 0 else "Negative"

# Fetch news headlines using News API
def get_news_headlines(ticker):
    url = f'https://newsapi.org/v2/everything?q={ticker}&apiKey={NEWS_API_KEY}'
    response = requests.get(url)
    news_data = response.json()
    headlines = [article['title'] for article in news_data.get('articles', [])]
    return headlines

# Fetch stock price data from Yahoo Finance
def get_yahoo_finance_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")  # 1 year of data
        if hist.empty:
            return None
        hist.to_csv(f'{ticker}_historical_data.csv')  # Save the historical data
        return hist
    except Exception as e:
        print(f"Failed to fetch data for {ticker}: {e}")
        return None

# Predict price function (dummy implementation)
def predict_price(ticker, days):
    return random.uniform(100, 200)

# Predict multiple timeframes
def predict_multiple_timeframes(ticker, timeframes):
    predictions = {}
    for days in timeframes:
        predictions[days] = predict_price(ticker, days)
    return predictions

# Automatically analyze and predict
def auto_analyze_and_predict(ticker):
    hist = get_yahoo_finance_data(ticker)
    if hist is None:
        st.error(f"Failed to retrieve data for {ticker}.")
        return None

    st.write(f"Historical Data for {ticker}:")
    st.write(hist.tail())  # Display the last few records

    # Simple moving average as an example analysis
    hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
    hist['SMA_50'] = hist['Close'].rolling(window=50).mean()

    st.line_chart(hist[['Close', 'SMA_20', 'SMA_50']])

    timeframes = [1, 5, 14, 30]  # 1 day, 5 days, 2 weeks, 1 month
    predictions = predict_multiple_timeframes(ticker, timeframes)

    st.write("Predictions:")
    st.write(predictions)

    # Saving predictions
    prediction_data = pd.DataFrame([{
        'Timestamp': datetime.datetime.now(),
        'Ticker': ticker,
        'Predictions': predictions
    }])

    if not os.path.isfile(PREDICTIONS_FILE):
        prediction_data.to_csv(PREDICTIONS_FILE, index=False)
    else:
        prediction_data.to_csv(PREDICTIONS_FILE, mode='a', header=False, index=False)

    return predictions

# Collect and save data periodically
def collect_data_periodically():
    if os.path.isfile(KILL_SWITCH_FILE):
        return
    
    for ticker in TICKERS:
        try:
            hist = get_yahoo_finance_data(ticker)
            if hist is not None:
                current_price = hist['Close'].iloc[-1]
                collected_data = pd.DataFrame([{
                    'Timestamp': datetime.datetime.now(),
                    'Ticker': ticker,
                    'Current Price': current_price
                }])
                
                if not os.path.isfile(COLLECTED_DATA_FILE):
                    collected_data.to_csv(COLLECTED_DATA_FILE, index=False)
                else:
                    collected_data.to_csv(COLLECTED_DATA_FILE, mode='a', header=False, index=False)
        except Exception as e:
            print(f"Failed to collect data for {ticker}: {e}")

# Track and analyze prediction performance
def track_performance(ticker, predicted_price, actual_price, confidence):
    if not os.path.isfile(PREDICTIONS_FILE):
        pd.DataFrame(columns=['Ticker', 'Predicted Price', 'Actual Price', 'Confidence']).to_csv(PREDICTIONS_FILE, index=False)
    
    df = pd.read_csv(PREDICTIONS_FILE)
    new_data = pd.DataFrame([{
        'Ticker': ticker,
        'Predicted Price': predicted_price,
        'Actual Price': actual_price,
        'Confidence': confidence
    }])
    
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(PREDICTIONS_FILE, index=False)
    
    correct_predictions = df[
        (df['Predicted Price'] * 0.95 <= df['Actual Price']) &
        (df['Actual Price'] <= df['Predicted Price'] * 1.05)
    ]
    
    accuracy = len(correct_predictions) / len(df) * 100 if len(df) > 0 else 0
    return accuracy

# Collect user feedback
def collect_feedback(ticker, actual_price, confidence):
    feedback = st.radio(f"Was the prediction for {ticker} correct?", ("Yes", "No"))

    if feedback == "No":
        reason = st.text_input("Please provide a reason for the incorrect prediction.")
        feedback_data = pd.DataFrame([{
            'Ticker': ticker,
            'Actual Price': actual_price,
            'Confidence': confidence,
            'Feedback': reason
        }])
        
        if not os.path.isfile(FEEDBACK_FILE):
            feedback_data.to_csv(FEEDBACK_FILE, index=False)
        else:
            feedback_data.to_csv(FEEDBACK_FILE, mode='a', header=False, index=False)

        st.write("Thank you for your feedback. We will use it to improve the predictions.")
    else:
        st.write("Thank you for confirming the prediction was correct.")

# Initialize and start the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(collect_data_periodically, 'interval', minutes=1)
scheduler.start()

# Streamlit app
def main():
    st.title("Stock Prediction App")

    tab1, tab2, tab3, tab4 = st.tabs(["Prediction", "News Analysis", "Options Volatility", "Performance Dashboard"])

    with tab1:
        st.write("Select from popular and volatile tickers or enter your own.")
        selected_tickers = st.multiselect(
            "Select Tickers",
            options=TICKERS
        )
        custom_ticker = st.text_input("Or enter your own ticker:")

        if custom_ticker:
            selected_tickers.append(custom_ticker.upper())

        for ticker in selected_tickers:
            st.subheader(f"Analysis for {ticker}")
            predictions = auto_analyze_and_predict(ticker)
            if predictions:
                st.write(f"Predictions for {ticker}:")
                st.write(predictions)

    with tab2:
        st.subheader("News Analysis")
        selected_ticker_news = st.selectbox("Select Ticker for News Analysis", options=TICKERS)
        headlines = get_news_headlines(selected_ticker_news)
        st.write("Latest News Headlines:")
        for headline in headlines:
            st.write(f"- {headline}")
            sentiment = analyze_sentiment_textblob(headline)
            st.write(f"Sentiment: {sentiment}")

    with tab3:
        st.subheader("Options Volatility")
        selected_ticker_options = st.selectbox("Select Ticker for Options Volatility", options=TICKERS)
        volatility = get_options_volatility(selected_ticker_options)
        st.write(f"Options Volatility for {selected_ticker_options}:")
        st.write(volatility)

    with tab4:
        st.subheader("Performance Dashboard")
        st.write("Track the accuracy of the predictions over time.")
        # Further analysis and performance tracking code here

if __name__ == "__main__":
    main()
