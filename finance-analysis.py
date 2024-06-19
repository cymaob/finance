import argparse
import logging
import sys
from datetime import timedelta, datetime
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import mysql.connector as mysql


# Connects to the MySQL database using the specified credentials. Exits the application if the connection fails.
def connect_to_database():
    try:
        db = mysql.connect(
            user="finance",
            password="finance-pass",
            host="localhost",
            port=3306,
            database="financial_analysis"
        )
        logging.debug("Connected to MySQL DB!")
        return db
    except mysql.Error as e:
        logging.error(f"Error connecting to MySQL DB Platform: {e}")
        sys.exit(1)


# Parses command-line arguments for the ticker symbol, start date, end date, and verbosity level.
def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Script for downloading and analyzing stock data. The data is stored in a database and displayed '
                    'using Plotly. Not saved data will be downloaded from Yahoo Finance.')
    parser.add_argument('-t', '--ticker', type=str, help='Ticker symbol der Aktie', required=True)
    parser.add_argument('-s', '--startdate', type=str, help='Start date (YYYY-MM-DD)', required=True)
    parser.add_argument('-e', '--enddate', type=str, help='End date (YYYY-MM-DD)', required=True)
    parser.add_argument('-v', '--verbosity', type=str, help='Verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)',
                        default='CRITICAL')
    return parser.parse_args()


# Sets the logging level based on the specified verbosity.
def set_logging_level(verbosity):
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    level = verbosity.upper()
    if level not in log_levels:
        print("Invalid verbosity level. Please choose from DEBUG, INFO, WARNING, ERROR, CRITICAL.")
        sys.exit(1)
    logging.basicConfig(level=log_levels[level], format='%(asctime)s - %(levelname)s - %(message)s')


# Downloads historical stock data from Yahoo Finance for the specified ticker and date range.
def download_data(ticker, start_date, end_date):
    logging.info("Downloading data...")
    end_date += timedelta(days=1)
    data_full = yf.download(ticker, start=start_date, end=end_date)
    data_filtered = data_full[["Close"]]
    return data_filtered


# Saves the downloaded data to the MySQL database under the specified ticker table.
def save_data_to_database(conn, data, ticker):
    try:
        cursor = conn.cursor()
        counter = 0

        for row in data.iterrows():
            date = row[0].strftime('%Y-%m-%d')
            cursor.execute(f"INSERT INTO `{ticker}` (date, close) VALUES (%s, %s)", (date, row[1]["Close"]))
            counter += 1
        conn.commit()
        logging.debug(f"Inserted {counter} rows of data")
    except mysql.Error as e:
        logging.error(f"Error inserting data: {e}")
        sys.exit(1)


# Creates a new table for the specified ticker if it does not already exist in the database.
def create_table(conn, ticker):
    try:
        logging.debug(f"Creating table {ticker}")
        cursor = conn.cursor()
        cursor.execute(f"CREATE TABLE `{ticker}` (date DATE, close DECIMAL(10, 2))")
        conn.commit()
    except mysql.Error as e:
        logging.error(f"Error creating table: {e}")
        sys.exit(1)


# Checks if a table for the specified ticker already exists in the database.
def check_table_exists(conn, ticker):
    try:
        cursor = conn.cursor()
        cursor.execute(f"SHOW TABLES LIKE '{ticker}'")
        result = cursor.fetchone()
        if result:
            logging.debug(f"Table {ticker} exists")
            return True
        else:
            logging.debug(f"Table {ticker} does not exist")
            return False
    except mysql.Error as e:
        logging.error(f"Error checking table: {e}")
        sys.exit(1)


# Retrieves the saved data from the database for the specified ticker and date range.
def get_data_from_database(conn, ticker, start_date, end_date):
    try:
        logging.debug("Getting data from database...")
        cursor = conn.cursor()
        cursor.execute(f"select * from `{ticker}` where date between %s and %s order by date desc",
                       (start_date, end_date))
        data_from_db = cursor.fetchall()
        return data_from_db
    except mysql.Error as e:
        logging.error(f"Error getting data: {e}")
        sys.exit(1)


# Displays the retrieved data using Plotly.
def display_data(data):
    logging.debug(f"data to display:")
    logging.debug(data)
    logging.info("Creating plot and displaying data...")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[x[0] for x in data], y=[x[1] for x in data], mode='lines', name='close'))
    fig.show()


# Validate ticker symbol and throw error if invalid
def validate_ticker(ticker):
    data = yf.download(ticker, start="2024-06-10", end="2024-06-14")
    try:
        if data["Close"].empty:
            raise ValueError("Invalid ticker symbol")
        return ticker
    except ValueError:
        print("Invalid ticker symbol. Please try again with a valid ticker symbol.")
        sys.exit(1)


# Validates the format of the start and end dates and ensures the start date is not after the end date.
def validate_date(start_date, end_date):
    try:
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        if s_date > e_date:
            print("Start date cannot be greater than end date")
            return False
        return s_date, e_date
    except ValueError:
        print("Invalid date format. Please use the format YYYY-MM-DD")
        sys.exit(1)


# Checks if the data already exists in the database for the given date range
def get_missing_dates(conn, start_date, end_date, ticker):
    user_dates = pd.bdate_range(start=start_date, end=end_date)
    cursor = conn.cursor()
    cursor.execute(f"select date from `{ticker}` where date between %s and %s", (start_date, end_date))
    existing_dates = cursor.fetchall()
    df_existing_dates = pd.DataFrame(existing_dates, columns=['date'])
    df_existing_dates['date'] = pd.to_datetime(df_existing_dates['date'])
    missing_dates = user_dates[~user_dates.isin(df_existing_dates['date'])]
    if missing_dates.empty:
        return None
    else:
        return get_missing_ranges_by_dates(missing_dates)


# Splits the missing dates into ranges with first and last date
def get_missing_ranges_by_dates(missing_dates):
    missing_ranges = []
    start_missing = missing_dates[0]
    end_missing = missing_dates[0]

    for current_date in missing_dates[1:]:
        if (current_date - end_missing).days == 1:
            end_missing = current_date
        else:
            missing_ranges.append((start_missing, end_missing))
            start_missing = current_date
            end_missing = current_date

    # Append the last range
    missing_ranges.append((start_missing.date(), end_missing.date()))
    logging.debug(f"Missing date ranges: {missing_ranges}")
    return missing_ranges


if __name__ == "__main__":
    # arguments are parsed and validated
    args = parse_arguments()
    set_logging_level(args.verbosity)
    ticker = validate_ticker(args.ticker)
    start_date, end_date = validate_date(args.startdate, args.enddate)
    # connect to the database
    conn = connect_to_database()
    # check if table exists, if not call create_table()
    if not check_table_exists(conn, ticker):
        create_table(conn, ticker)

    # check if data exists in the database for the given date range. If not, download and save only the missing data
    missing_dates = get_missing_dates(conn, start_date, end_date, ticker)
    if missing_dates is None:
        logging.debug("Data already exists in the database for the given date range")
    else:
        logging.debug("Data missing for the following date ranges")
        for date_range in missing_dates:
            logging.debug(date_range)
            data = download_data(ticker, date_range[0], date_range[1])
            save_data_to_database(conn, data, ticker)

    # get data from the database and display it
    data_from_db = get_data_from_database(conn, ticker, start_date, end_date)
    display_data(data_from_db)
    # close the connection and exit the program
    conn.commit()
    conn.close()
    sys.exit(0)
