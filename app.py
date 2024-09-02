import streamlit as st
import yfinance as yf
from textblob import TextBlob
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import os
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

# Expanded list of popular and volatile tickers
TICKERS = [
    "AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NFLX", "NVDA", "BA", "IBM",
    "INTC", "WMT", "DIS", "AMD", "CSCO", "ORCL", "MCD", "PFE", "V", "MA",
    "JPM", "UNH", "HD", "KO", "PEP", "T", "VZ", "XOM", "CVX", "GS",
    "NIO", "BYND", "PLTR", "RBLX", "CRSP", "EDIT", "SGMO", "TIGR", "ZM", "DOCU"
]

# Files for storing predictions, outcomes, and feedback
PREDICTIONS_FILE = 'predictions.csv'
FEEDBACK_FILE = 'feedback.csv'
COLLECTED_DATA_FILE = 'collected_data.csv'

# Email settings
EMAIL_ADDRESS = 'your_email@gmail.com'
EMAIL_PASSWORD = 'your_password'
ALERT_RECIPIENT = 'recipient_email@gmail.com'

# Initialize sentiment analyzer
def analyze_sentiment_textblob(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    return "Positive" if sentiment > 0 else "Negative"

# Fetch dummy news headlines
def get_news_headlines(ticker):
    # Replace with real news fetching logic
    return [
        f"Example news headline 1 for {ticker}",
        f"Example news headline 2 for {ticker}"
    ]

# Predict price function (dummy implementation)
def predict_price(ticker, days):
    # Replace with actual model prediction logic
    return random.uniform(100, 200)

# Predict multiple timeframes
def predict_multiple_timeframes(ticker, timeframes):
    predictions = {}
    for days in timeframes:
        predictions[days] = predict_price(ticker, days)
    return predictions

# Fetch options volatility data
def get_options_volatility(ticker):
    try:
        stock = yf.Ticker(ticker)
        options = stock.options
        if not options:
            return "No options data available"
        
        # Fetch the first available options chain
        options_chain = stock.option_chain(options[0])
        calls = options_chain.calls
        puts = options_chain.puts
        
        # Calculate average implied volatility for calls and puts
        call_volatility = calls['impliedVolatility'].mean() if 'impliedVolatility' in calls.columns else None
        put_volatility = puts['impliedVolatility'].mean() if 'impliedVolatility' in puts.columns else None
        
        return {
            'call_volatility': call_volatility,
            'put_volatility': put_volatility
        }
    except Exception as e:
        return str(e)

# Send email alert
def send_email_alert(ticker, confidence):
    subject = f"High Confidence Alert for {ticker}"
    body = f"The confidence level for {ticker} is very high: {confidence * 100:.2f}%."
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ALERT_RECIPIENT
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(EMAIL_ADDRESS, ALERT_RECIPIENT, text)
        print(f"Alert email sent to {ALERT_RECIPIENT}.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Track and analyze prediction performance
def track_performance(ticker, predicted_price, actual_price, confidence):
    if not os.path.isfile(PREDICTIONS_FILE):
        # Create file with headers if it does not exist
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
    
    # Calculate accuracy
    correct_predictions = df[
        (df['Predicted Price'] * 0.95 <= df['Actual Price']) &
        (df['Actual Price'] <= df['Predicted Price'] * 1.05)
    ]
    
    accuracy = len(correct_predictions) / len(df) * 100 if len(df) > 0 else 0
    st.write(f"Prediction Accuracy: {accuracy:.2f}%")
    
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
            # Create file with headers if it does not exist
            feedback_data.to_csv(FEEDBACK_FILE, index=False)
        else:
            feedback_data.to_csv(FEEDBACK_FILE, mode='a', header=False, index=False)

        st.write("Thank you for your feedback. We will use it to improve the predictions.")
    else:
        st.write("Thank you for confirming the prediction was correct.")

# Collect data every minute
def collect_data_periodically():
    for ticker in TICKERS:
        try:
            data = yf.download(ticker, period="1d")
            current_price = data['Close'].iloc[-1]
            collected_data = pd.DataFrame([{
                'Timestamp': datetime.datetime.now(),
                'Ticker': ticker,
                'Current Price': current_price
            }])
            
            if not os.path.isfile(COLLECTED_DATA_FILE):
                # Create file with headers if it does not exist
                collected_data.to_csv(COLLECTED_DATA_FILE, index=False)
            else:
                collected_data.to_csv(COLLECTED_DATA_FILE, mode='a', header=False, index=False)
        except Exception as e:
            print(f"Failed to collect data for {ticker}: {e}")

# Initialize and start the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(collect_data_periodically, 'interval', minutes=1)
scheduler.start()

# Streamlit app
def main():
    st.title("Stock Prediction App")

    tab1, tab2, tab3 = st.tabs(["Prediction", "News Analysis", "Options Volatility"])

    with tab1:
        st.write("Select from popular and volatile tickers or enter your own.")
        selected_tickers = st.multiselect(
            "Select Tickers",
            options=TICKERS,
            default=TICKERS[:5]  # Default to first 5 tickers
        )
        custom_tickers = st.text_area("Or Enter Your Custom Tickers (comma-separated)", "")
        if custom_tickers:
            custom_tickers = [ticker.strip() for ticker in custom_tickers.split(",")]
            selected_tickers.extend(custom_tickers)

        if st.button("Get Predictions"):
            timeframes = [1, 5, 10, 30]
            for ticker in set(selected_tickers):  # Ensure unique tickers
                data = yf.download(ticker, period="1mo")
                confidence = random.uniform(0, 1)
                headlines = get_news_headlines(ticker)
                sentiment_results = [analyze_sentiment_textblob(headline) for headline in headlines]
                sentiment_scores = sum(1 if result == "Positive" else -1 for result in sentiment_results) / len(sentiment_results)
                adjusted_confidence = confidence + sentiment_scores * 0.1

                st.write(f"{ticker} - Original Model confidence: {confidence * 100:.2f}%")
                st.write(f"{ticker} - Adjusted Model confidence based on news sentiment: {adjusted_confidence * 100:.2f}%")

                if adjusted_confidence >= 0.8:
                    predictions = predict_multiple_timeframes(ticker, timeframes)
                    for days, prediction in predictions.items():
                        st.write(f"Predicted price for {ticker} in {days} days: ${prediction:.2f}")
                    
                    # Send email alert if confidence is very high
                    send_email_alert(ticker, adjusted_confidence)
                    
                    # Track performance (mock actual price for illustration)
                    actual_price = prediction  # Replace with actual price fetching logic
                    accuracy = track_performance(ticker, prediction, actual_price, adjusted_confidence)

                    # Collect feedback
                    collect_feedback(ticker, actual_price, adjusted_confidence)
                else:
                    st.write(f"Confidence for {ticker} is too low. Skipping prediction.")
        else:
            st.write("Select tickers and click 'Get Predictions'.")

    with tab2:
        ticker = st.text_input("Enter Stock Ticker for News Analysis (e.g., AAPL)", "AAPL")

        if st.button("Analyze News"):
            headlines = get_news_headlines(ticker)
            st.write(f"Found {len(headlines)} news articles for {ticker}.")

            sentiment_results = [analyze_sentiment_textblob(headline) for headline in headlines]
            st.write("Sentiment Analysis Results:")
            for headline, sentiment in zip(headlines, sentiment_results):
                st.write(f"{headline} - Sentiment: {sentiment}")

    with tab3:
        ticker = st.text_input("Enter Stock Ticker for Options Volatility (e.g., AAPL)", "AAPL")

        if st.button("Get Options Volatility"):
            volatility = get_options_volatility(ticker)
            if isinstance(volatility, dict):
                st.write(f"Call Option Volatility for {ticker}: {volatility['call_volatility']:.2f}" if volatility['call_volatility'] is not None else "No call option volatility data")
                st.write(f"Put Option Volatility for {ticker}: {volatility['put_volatility']:.2f}" if volatility['put_volatility'] is not None else "No put option volatility data")
            else:
                st.write(f"Error fetching options data: {volatility}")

if __name__ == "__main__":
    main()
