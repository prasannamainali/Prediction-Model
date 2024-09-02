import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import app  # Assuming your script is named `app.py`
import os

class TestApp(unittest.TestCase):

    @patch('app.get_yahoo_finance_data')
    def test_get_yahoo_finance_data(self, mock_get_yahoo_finance_data):
        # Mock response
        mock_get_yahoo_finance_data.return_value = pd.DataFrame({
            'Close': [150, 152, 153],
            'Open': [148, 150, 151],
            'High': [155, 156, 157],
            'Low': [147, 149, 150],
            'Volume': [10000, 11000, 12000]
        }, index=pd.date_range(start='2023-01-01', periods=3))
        
        data = app.get_yahoo_finance_data('AAPL')
        self.assertIsInstance(data, pd.DataFrame)
        self.assertFalse(data.empty)
        self.assertIn('Close', data.columns)

    @patch('app.get_news_headlines')
    def test_get_news_headlines(self, mock_get_news_headlines):
        # Mock response
        mock_get_news_headlines.return_value = [
            "Apple launches new iPhone",
            "Market reacts positively to Apple's new product"
        ]
        
        headlines = app.get_news_headlines('AAPL')
        self.assertEqual(len(headlines), 2)
        self.assertIn("Apple launches new iPhone", headlines)

    @patch('app.predict_price')
    def test_predict_price(self, mock_predict_price):
        # Mock response
        mock_predict_price.return_value = 150.00
        
        prediction = app.predict_price('AAPL', 5)
        self.assertEqual(prediction, 150.00)

    @patch('app.track_performance')
    def test_track_performance(self, mock_track_performance):
        # Mock response
        mock_track_performance.return_value = 85.0
        
        accuracy = app.track_performance('AAPL', 145.00, 146.00, 90)
        self.assertEqual(accuracy, 85.0)

    @patch('app.collect_data_periodically')
    def test_collect_data_periodically(self, mock_collect_data_periodically):
        # Simulate running the collection function
        mock_collect_data_periodically.return_value = None
        
        app.collect_data_periodically()
        # Check that it completes without errors
        self.assertIsNone(mock_collect_data_periodically.return_value)

    @patch('app.analyze_sentiment_textblob')
    def test_analyze_sentiment_textblob(self, mock_analyze_sentiment_textblob):
        # Mock response
        mock_analyze_sentiment_textblob.return_value = "Positive"
        
        sentiment = app.analyze_sentiment_textblob('The stock is going up.')
        self.assertEqual(sentiment, "Positive")

    @patch('app.collect_feedback')
    def test_collect_feedback(self, mock_collect_feedback):
        # Mock feedback collection
        mock_collect_feedback.return_value = None
        
        app.collect_feedback('AAPL', 150.00, 85)
        # Check that it completes without errors
        self.assertIsNone(mock_collect_feedback.return_value)

    def test_fibonacci_retracement_levels(self):
        # Simulate historical data for Fibonacci calculation
        data = pd.DataFrame({
            'Close': [100, 105, 110, 115, 120]
        }, index=pd.date_range(start='2023-01-01', periods=5))
        data.to_csv('AAPL_historical_data.csv')  # Mock file save

        levels = app.fibonacci_retracement_levels('AAPL')
        self.assertIn('0.0%', levels)
        self.assertIn('61.8%', levels)
        self.assertEqual(len(levels), 6)

    @patch('os.path.isfile')
    def test_files_existence(self, mock_isfile):
        # Mock file existence
        mock_isfile.return_value = True
        
        self.assertTrue(os.path.isfile('predictions.csv'))
        self.assertTrue(os.path.isfile('feedback.csv'))
        self.assertTrue(os.path.isfile('collected_data.csv'))
        self.assertTrue(os.path.isfile('kill_switch.txt'))

if __name__ == '__main__':
    unittest.main()
