# Bitcoin Transaction Analyzer

A desktop application for tracking and analyzing Bitcoin transactions with simple filtering and visualization capabilities.

## Features

- **Real-time Transaction Fetching**: Retrieve transaction history for any Bitcoin address using the Blockchain API
- **Advanced Filtering**: Filter transactions by:
  - Time period (Last 7/30/90 days, Year to date, Last year, All time)
  - Transaction hash (search functionality)
  - Amount range (min/max BTC values)
- **Visual Analytics**: Generate interactive charts showing transaction frequency:
  - Group by Day, Week, Month, or Year
  - Line charts for daily, weekly, and monthly views
  - Bar charts for yearly overview
- **User-Friendly Interface**: Modern GUI with intuitive controls and data table
- **Multi-threaded**: Non-blocking UI during API requests

## Screenshots

The application provides:
- A simple interface for entering Bitcoin addresses
- A comprehensive data table showing transaction hashes, dates, and amounts
- Interactive filtering controls for customized analysis
- Dynamic charts for visualizing transaction patterns over time

## Prerequisites

- Python 3.7 or higher
- Internet connection (for API access)

## Dependencies

The application requires the following Python packages:

```
requests
tkinter (usually included with Python)
matplotlib
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/luokaci05/Bitcoin_Transactions_Tracker.git
cd Bitcoin_Transactions_Tracker
```

2. (Optional) Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:
   - **Windows**:
     ```bash
     .venv\Scripts\activate
     ```
   - **Linux/macOS**:
     ```bash
     source .venv/bin/activate
     ```

4. Install required dependencies:
```bash
pip install requests matplotlib
```

## Usage

1. Run the application:
```bash
python BCtransaction_Tracker.py
```

   Or, if using a virtual environment on Windows:
```bash
.venv\Scripts\python.exe BCtransaction_Tracker.py
```

2. **Enter a Bitcoin Address**: Type or paste a Bitcoin address in the input field (a sample address is pre-filled)

3. **Get Transactions**: Click the "Get Transactions" button to fetch transaction data

4. **Apply Filters** (optional):
   - Select a time period from the dropdown
   - Choose how to group data (Day/Week/Month/Year)
   - Search for specific transaction hashes
   - Set minimum/maximum amount filters
   - Click "Apply Filters" to update the view

5. **View Results**:
   - Transaction data appears in the table below
   - A chart automatically displays showing transaction frequency over time

## Technical Details

### Architecture

- **Backend**: Uses the Blockchain.info API to fetch transaction data
- **Frontend**: Built with tkinter for cross-platform compatibility
- **Visualization**: matplotlib for generating charts and graphs
- **Threading**: Multi-threaded design prevents UI freezing during API calls

### Data Processing

- Transactions are fetched in real-time from `https://blockchain.info/rawaddr/{address}`
- Transaction amounts are converted from satoshis to BTC
- Timestamps are converted to human-readable dates
- Data is cached locally for filtering without additional API calls


## Troubleshooting

- **"Network error"**: Check your internet connection
- **"Bitcoin address not found"**: Verify the address is correct and has transaction history
- **No data after filtering**: Try adjusting your filter criteria
- **Import errors**: Ensure all dependencies are installed correctly

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Notes

This project is available for educational and personal use.
