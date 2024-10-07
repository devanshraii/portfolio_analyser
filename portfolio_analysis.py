import json
from datetime import datetime
from scipy.optimize import newton

# Load transaction data from JSON file with error handling for missing keys
def load_transactions(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

        # Check if the required key exists
        if 'data' in data and len(data['data']) > 0 and 'dtTransaction' in data['data'][0]:
            return data['data'][0]['dtTransaction']
        else:
            raise KeyError("The key 'dtTransaction' is missing in the JSON file or has a different structure.")

# Parse the transaction data for cash flows
def prepare_cash_flows(transactions):
    processed_transactions = []
    for trxn in transactions:
        trxn_date = datetime.strptime(trxn['trxnDate'], '%d-%b-%Y')
        trxn_amount = float(trxn['trxnAmount'])
        processed_transactions.append({'date': trxn_date, 'amount': -trxn_amount})  # Investments are negative

    return processed_transactions

# Get current NAV value (Mock function)
def get_current_nav(isin):
    current_navs = {
        "INF209K01UN8": 67.58,
        "INF090I01JR0": 76.4465,
        "INF194K01Y29": 179.550,
    }
    return current_navs.get(isin, 0.0)

# Calculate total portfolio value
def calculate_portfolio_value(transactions):
    portfolio_value = 0
    units_held = {}

    for trxn in transactions:
        isin = trxn['isin']
        nav = get_current_nav(isin)
        units = float(trxn['trxnUnits'])

        if isin not in units_held:
            units_held[isin] = 0
        units_held[isin] += units

        portfolio_value += units_held[isin] * nav

    return portfolio_value

# Calculate portfolio gain
def calculate_portfolio_gain(transactions):
    portfolio_gain = 0

    for trxn in transactions:
        units = float(trxn['trxnUnits'])
        purchase_price = float(trxn['purchasePrice'])
        current_nav = get_current_nav(trxn['isin'])
        acquisition_cost = units * purchase_price
        current_value = units * current_nav
        portfolio_gain += current_value - acquisition_cost

    return portfolio_gain

# Calculate XIRR using Newton-Raphson method
def calculate_xirr(cash_flows):
    def xirr_func(rate):
        total = 0
        for cash_flow in cash_flows:
            days = (cash_flow['date'] - cash_flows[0]['date']).days / 365
            if days < 0:
                return float('inf')  # Prevents invalid calculations
            total += cash_flow['amount'] / (1 + rate) ** days
        return total

    try:
        return newton(xirr_func, 0.1)
    except Exception as e:
        print(f"Error calculating XIRR: {e}")
        return None

# Main function to calculate portfolio and XIRR
def main():
    # Load transactions from JSON
    try:
        transactions = load_transactions('transaction_detail.json')
    except KeyError as e:
        print(f"Error loading transactions: {e}")
        return

    # Prepare cash flows for XIRR
    cash_flows = prepare_cash_flows(transactions)

    # Calculate Total Portfolio Value
    portfolio_value = calculate_portfolio_value(transactions)
    print(f"Total Portfolio Value: {portfolio_value:.2f}")

    # Calculate Total Portfolio Gain
    portfolio_gain = calculate_portfolio_gain(transactions)
    print(f"Total Portfolio Gain: {portfolio_gain:.2f}")

    # Add current portfolio value as a cash flow
    cash_flows.append({
        'date': datetime.now(),
        'amount': portfolio_value  # Current portfolio value as a positive cash flow
    })

    # Filter out cash flows with zero amounts
    cash_flows = [cf for cf in cash_flows if cf['amount'] != 0]

    # Ensure there's at least one positive cash flow for XIRR calculation
    if not any(cf['amount'] > 0 for cf in cash_flows):
        print("Error: No valid positive cash flows for XIRR calculation.")
        return

    # Calculate XIRR
    xirr_result = calculate_xirr(cash_flows)
    if xirr_result is not None:
        print(f"XIRR: {xirr_result * 100:.2f}%")
    else:
        print("XIRR calculation failed.")

if __name__ == "__main__":
    main()
