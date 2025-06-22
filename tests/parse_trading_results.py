from bs4 import BeautifulSoup
# from datetime import datetime
from datetime import datetime

def calculate_kpis(trades):
    total_profit = 0.0
    profitable_trades = 0
    losing_trades = 0
    profits = []

    for trade in trades:
        profit_str = trade.get('Profit', '0').replace(',', '').strip()
        try:
            profit = float(profit_str)
        except ValueError:
            profit = 0.0
        total_profit += profit
        profits.append(profit)
        if profit > 0:
            profitable_trades += 1
        elif profit < 0:
            losing_trades += 1

    total_trades = len(trades)
    win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
    avg_profit = total_profit / total_trades if total_trades > 0 else 0

    # Approximate max drawdown as max cumulative loss streak (simplified)
    max_drawdown = 0
    cum_profit = 0
    peak = 0
    for p in profits:
        cum_profit += p
        if cum_profit > peak:
            peak = cum_profit
        drawdown = peak - cum_profit
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return {
        'total_profit': total_profit,
        'total_trades': total_trades,
        'profitable_trades': profitable_trades,
        'losing_trades': losing_trades,
        'win_rate_percent': win_rate,
        'average_profit_per_trade': avg_profit,
        'max_drawdown': max_drawdown
    }



def parse_trading_results(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    table = soup.find('table')

    trades = []
    headers = []
    header_found = False

    for row in table.find_all('tr'):
        cells = row.find_all(['th', 'td'])
        cell_texts = [cell.text.strip() for cell in cells]

        # Detect header row by matching expected column names
        expected_headers = {"Ticket", "Open Time", "Type", "Size", "Item", "Price", "S / L", "T / P", "Close Time", "Commission", "Swap", "Profit"}
        if not header_found and expected_headers.intersection(set(cell_texts)):
            headers = cell_texts
            header_found = True
            continue

        # After header found, parse rows with matching number of columns
        if header_found:
            if len(cells) != len(headers):
                continue
            trade = {headers[i]: cell_texts[i] for i in range(len(headers))}
            trades.append(trade)

    return trades

if __name__ == "__main__":
    with open('../files/DetailedStatement.htm', 'r', encoding='utf-8') as f:
        html_content = f.read()

    trades = parse_trading_results(html_content)
    print(f"Extracted {len(trades)} trades")

    kpis = calculate_kpis(trades)
    print("KPIs:")
    for k, v in kpis.items():
        print(f"  {k}: {v:.2f}")