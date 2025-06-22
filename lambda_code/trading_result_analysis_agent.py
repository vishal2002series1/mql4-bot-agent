import boto3
import os
import json
from bs4 import BeautifulSoup

s3 = boto3.client('s3')
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

def parse_trading_results(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    table = soup.find('table')

    trades = []
    headers = []
    header_found = False

    for row in table.find_all('tr'):
        cells = row.find_all(['th', 'td'])
        cell_texts = [cell.text.strip() for cell in cells]

        expected_headers = {"Ticket", "Open Time", "Type", "Size", "Item", "Price", "S / L", "T / P", "Close Time", "Commission", "Swap", "Profit"}
        if not header_found and expected_headers.intersection(set(cell_texts)):
            headers = cell_texts
            header_found = True
            continue

        if header_found:
            if len(cells) != len(headers):
                continue
            trade = {headers[i]: cell_texts[i] for i in range(len(headers))}
            trades.append(trade)

    return trades

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

def get_bedrock_summary(kpis, trades):
    # Convert trades list to JSON string (pretty-printed)
    trades_json = json.dumps(trades, indent=2)

    prompt = (
        f"Analyze the following trading performance KPIs and the detailed trade records. "
        f"Provide a summary with suggestions to improve the trading bot, focusing on what kind of trades are causing issues.\n\n"
        f"KPIs:\n"
        f"Total Profit: {kpis['total_profit']}\n"
        f"Total Trades: {kpis['total_trades']}\n"
        f"Profitable Trades: {kpis['profitable_trades']}\n"
        f"Losing Trades: {kpis['losing_trades']}\n"
        f"Win Rate (%): {kpis['win_rate_percent']:.2f}\n"
        f"Average Profit per Trade: {kpis['average_profit_per_trade']:.2f}\n"
        f"Max Drawdown: {kpis['max_drawdown']:.2f}\n\n"
        f"Trade Records:\n{trades_json}\n"
    )

    system_prompt = "You are a helpful assistant specialized in trading performance analysis."

    body = json.dumps({
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "system": system_prompt,
        "max_tokens": 15000,
        "temperature": 0.5,
        "anthropic_version": "bedrock-2023-05-31"
    })

    response = bedrock_runtime.invoke_model(
        modelId=os.environ.get('BEDROCK_MODEL_ID'),
        body=body,
        contentType="application/json",
        accept="application/json"
    )

    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']

def lambda_handler(event, context):
    bucket = os.environ.get('BUCKET_NAME')
    key = os.environ.get('TRADING_RESULTS_FILE')

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        html_content = response['Body'].read().decode('utf-8')

        trades = parse_trading_results(html_content)
        kpis = calculate_kpis(trades)

        summary = get_bedrock_summary(kpis, trades)

        return {
            'statusCode': 200,
            'body': {
                'kpis': kpis,
                'summary': summary
            }
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': str(e)
        }