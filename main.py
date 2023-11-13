import argparse
import asyncio
from datetime import datetime, timedelta
import httpx
from aiofile import AIOFile, Writer
from aiopath import AsyncPath


async def fetch_exchange_rate(client, date, currency='EUR,USD'):
    url = f'https://api.privatbank.ua/p24api/exchange_rates?json&date={date}'

    response = await client.get(url)
    data = response.json()

    rates = {}
    for item in data['exchangeRate']:
        if item['currency'] in currency:
            rates[item['currency']] = {
                'sale': item['saleRateNB'],
                'purchase': item['purchaseRateNB']
            }

    return rates


async def get_exchange_rates(days, currency='EUR,USD'):
    async with httpx.AsyncClient() as client:
        tasks = [fetch_exchange_rate(client, (datetime.now() - timedelta(days=i)).strftime('%d.%m.%Y'), currency) for i
                 in range(days)]
        results = await asyncio.gather(*tasks)

        return results


async def save_to_log(data):
    async with AIOFile('exchange_log.txt', 'a') as afp:
        await afp.write('\n'.join(str(item) for item in data) + '\n')



def main():
    parser = argparse.ArgumentParser(description='Get exchange rates from PrivatBank API.')
    parser.add_argument('days', type=int, help='Number of days to retrieve exchange rates for (up to 10 days).')
    parser.add_argument('--currency', type=str, default='EUR,USD',
                        help='Comma-separated list of currencies to retrieve.')
    args = parser.parse_args()

    if args.days > 10:
        print("Error: Number of days should not exceed 10.")
        return

    loop = asyncio.get_event_loop()
    exchange_rates = loop.run_until_complete(get_exchange_rates(args.days, args.currency))

    formatted_result = [{'date': (datetime.now() - timedelta(days=i)).strftime('%d.%m.%Y'), 'rates': rate} for i, rate
                        in enumerate(exchange_rates, start=1)]
    print(formatted_result)

    loop.run_until_complete(save_to_log(formatted_result))


if __name__ == '__main__':
    main()
