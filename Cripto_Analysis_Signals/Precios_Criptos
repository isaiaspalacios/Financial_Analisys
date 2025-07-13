# This code fetches and analyzes cryptocurrency data. Please do not delete this cell.
#!pip install pandas numpy pandas_ta

import requests
import pandas as pd
import numpy as np
import pandas_ta as ta
import matplotlib.pyplot as plt

def get_crypto_data(symbols, vs_currency='usd', days='max'):
    """
    Fetches historical price data for multiple cryptocurrencies.

    Args:
        symbols (list): A list of cryptocurrency coin IDs (from CoinGecko).
        vs_currency (str): The currency to compare against.
        days (str or int): The number of days of historical data to fetch ('max' for all available).

    Returns:
        dict: A dictionary where keys are coin IDs and values are pandas DataFrames
              with 'timestamp' and 'price' columns.
    """
    data = {}
    for symbol in symbols:
        url = f'https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency={vs_currency}&days={days}'
        try:
            response = requests.get(url)
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            json_data = response.json()
            if 'prices' in json_data:
                df = pd.DataFrame(json_data['prices'], columns=['timestamp', 'price'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                data[symbol] = df
            else:
                print(f"Warning: No price data found for {symbol}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {symbol}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for {symbol}: {e}")
    return data

def analyze_crypto_data(dataframes_dict):
    """
    Adds technical indicators (MACD, RSI, MAs) to the DataFrames.

    Args:
        dataframes_dict (dict): A dictionary of pandas DataFrames with price data.

    Returns:
        dict: A dictionary with updated DataFrames containing indicators.
    """
    analyzed_data = {}
    ma_periods = [9, 21, 50, 200, 400]

    for symbol, df in dataframes_dict.items():
        if not df.empty:
            # Calculate MACD
            df.ta.macd(close='price', append=True)

            # Calculate RSI
            df.ta.rsi(close='price', append=True)

            # Calculate Moving Averages
            for period in ma_periods:
                df.ta.sma(close='price', length=period, append=True)

            analyzed_data[symbol] = df.dropna() # Drop rows with NaN values introduced by indicators
        else:
            print(f"DataFrame for {symbol} is empty, skipping analysis.")
            analyzed_data[symbol] = df # Include empty df

    return analyzed_data

def safe_print(value):
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return str(value)
    
# List of CoinGecko coin IDs
crypto_symbols = ['bitcoin', 'uniswap', 'vechain', 'aave']

# Fetch data
crypto_data = get_crypto_data(crypto_symbols, days=365) # Fetch 1 year of data

# Analyze data
analyzed_crypto_data = analyze_crypto_data(crypto_data)

# Print current price and some indicators for each crypto
print("\n--- Análisis de Criptomonedas ---")
for symbol, df in analyzed_crypto_data.items():
    if not df.empty:
        latest_data = df.iloc[-1]
        print(f"\nAnálisis para: {symbol.upper()}")
        print(f"  Precio actual: ${latest_data['price']:.2f}")

        # Print MACD and Signal (check if columns exist)
        # pandas_ta creates columns with default names like MACD_12_26_9, MACDH_12_26_9, MACDS_12_26_9
        macd_col = 'MACD_12_26_9'
        macdh_col = 'MACDH_12_26_9'
        macds_col = 'MACDS_12_26_9'

        """ Antiguo codigo original ------
        print(f"  MACD (12, 26, 9): {latest_data.get(macd_col, 'N/A'):.2f}")
        print(f"  MACD Signal (9): {latest_data.get(macds_col, 'N/A'):.2f}")
        print(f"  MACD Histogram: {latest_data.get(macdh_col, 'N/A'):.2f}")
        """
        # A1 - Nuevo codigo Corregido por Copilot 
        print(f"  MACD (12, 26, 9): {safe_print(latest_data.get(macd_col, 'N/A'))}")
        print(f"  MACD Signal (9): {safe_print(latest_data.get(macds_col, 'N/A'))}")
        print(f"  MACD Histogram: {safe_print(latest_data.get(macdh_col, 'N/A'))}")
        # A1 - Fin Nuevo codigo Corregido por Copilot
        
        # Print RSI (check if column exists)
        # pandas_ta creates RSI column with default name RSI_14
        rsi_col = 'RSI_14'

        """ Antiguo codigo original ------
        print(f"  RSI (14): {latest_data.get(rsi_col, 'N/A'):.2f}")

        # Print MAs (check if columns exist)
        print("  Medias Móviles:")
        for period in [9, 21, 50, 200, 400]:
            ma_col = f'SMA_{period}'
            print(f"    MA ({period}): {latest_data.get(ma_col, 'N/A'):.2f}")
        """
        # A2 - Nuevo codigo Corregido por Copilot 
        print(f"  RSI (14): {safe_print(latest_data.get(rsi_col, 'N/A'))}")

        # Print MAs (check if columns exist)
        print("  Medias Móviles:")
        for period in [9, 21, 50, 200, 400]:
            ma_col = f'SMA_{period}'
            print(f"    MA ({period}): {safe_print(latest_data.get(ma_col, 'N/A'))}")
        # A2 - Fin Nuevo codigo Corregido por Copilot

    else:
        print(f"\nNo data available for {symbol.upper()}")


# Optional: You can now access the full DataFrames with indicators
# For example, to see the DataFrame for Bitcoin:
# print("\nBitcoin Data with Indicators:")
# print(analyzed_crypto_data['bitcoin'].tail())

# You can also plot the data and indicators if needed
# Example plot for Bitcoin price and MAs:
# if 'bitcoin' in analyzed_crypto_data and not analyzed_crypto_data['bitcoin'].empty:
#     df_btc = analyzed_crypto_data['bitcoin']
#     plt.figure(figsize=(12, 6))
#     plt.plot(df_btc.index, df_btc['price'], label='Price', alpha=0.8)
#     for period in [9, 21, 50]: # Plot fewer MAs for clarity
#          ma_col = f'SMA_{period}'
#          if ma_col in df_btc.columns:
#               plt.plot(df_btc.index, df_btc[ma_col], label=f'MA {period}', alpha=0.7)
#     plt.title('Bitcoin Price and Moving Averages')
#     plt.xlabel('Date')
#     plt.ylabel('Price (USD)')
#     plt.legend()
#     plt.grid(True)
#     plt.show()