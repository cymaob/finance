# Financial Data Analysis Application

This application allows users to download historical stock data for a specified ticker symbol and date range, save it to a MySQL database, and retrieve and display the saved data.

## Table of Contents

- Requirements
- Installation
- Usage
- Functions
- Error Handling

## Requirements

- Python 3.8+
- MySQL (or MariaDB's MySQL client)
- Required Python packages:
  - mysql-connector-python
  - yfinance
  - pandas
  - plotly

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/financial-data-analysis.git

2. **Install the required Python packages:**
   ```bash
   pip install mysql-connector-python yfinance pandas plotly
   
3. **Set up the MySQL database:**
   - Install MySQL on your system if you haven't already.
   - Execute database.sql to create the database and user.

4. **Configure the database connection:**
   - Modify the database connection parameters in the connect_to_database() function.

## Usage

1. **Run the application:**
   ```bash
   python financial_analysis.py -t TICKER -s START_DATE -e END_DATE [-v VERBOSITY]
   ```
   Replace TICKER with the stock ticker symbol, START_DATE and END_DATE with the date range (in YYYY-MM-DD format), and optionally set the verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

## Functions

**connect_to_database()**
Connects to the MySQL database using the specified credentials. Exits the application if the connection fails.

**parse_arguments()**
Parses command-line arguments for the ticker symbol, start date, end date, and verbosity level.

**set_logging_level(verbosity)**
Sets the logging level based on the specified verbosity.

**download_data(ticker, start_date, end_date)**
Downloads historical stock data from Yahoo Finance for the specified ticker and date range.

**save_data_to_database(conn, data, ticker)**
Saves the downloaded data to the MySQL database under the specified ticker table.

**create_table(conn, ticker)**
Creates a new table for the specified ticker if it does not already exist in the database.

**check_table_exists(conn, ticker)**
Checks if a table for the specified ticker already exists in the database.

**get_data_from_database(conn, ticker, start_date, end_date)**
Retrieves the saved data from the database for the specified ticker and date range.

**display_data(data)**
Displays the retrieved data using Plotly.

**validate_date(start_date, end_date)**
Validates the format of the start and end dates and ensures the start date is not after the end date.

**get_missing_dates(conn, start_date, end_date, ticker)**
Determines if there are missing dates. If so, they will be collected by get_missing_dates() and returned.

**get_missing_ranges_by_dates(missing_dates)**
Splits the missing dates into ranges with first and last date

## Error Handling

The application includes basic error handling for database connection issues, invalid ticker symbols, and data insertion errors. If an error occurs, the application prints an error message and exits.
