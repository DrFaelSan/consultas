#!/usr/bin/env python3
"""Teste das APIs do projeto"""
import asyncio
import aiohttp

APIS = [
    ('BrasilAPI - Banks', 'https://brasilapi.com.br/api/banks/v1'),
    ('BrasilAPI - DDD', 'https://brasilapi.com.br/api/ddd/v1/11'),
    ('BrasilAPI - FIPE Marcas', 'https://brasilapi.com.br/api/fipe/marcas/v1/carros'),
    ('BrasilAPI - Taxas', 'https://brasilapi.com.br/api/taxas/v1'),
    ('BrasilAPI - Feriados', 'https://brasilapi.com.br/api/feriados/v1/2026'),
    ('ViaCEP', 'https://viacep.com.br/ws/01001000/json/'),
    ('IP-API', 'http://ip-api.com/json/8.8.8.8'),
    ('IPGeolocation', 'https://api.ipgeolocation.io/ipgeo?apiKey=demo'),
    ('OpenWeatherMap', 'https://api.openweathermap.org/data/2.5/weather?q=London&appid=demo'),
    ('BinList', 'https://lookup.binlist.net/453201'),
]

async def test_api(session, name, url):
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                print(f'✓ {name}: OK ({resp.status})')
                return True
            else:
                print(f'✗ {name}: HTTP {resp.status}')
                return False
    except Exception as e:
        print(f'✗ {name}: {str(e)[:40]}')
        return False

async def main():
    print('=' * 50)
    print('TESTE DE APIs')
    print('=' * 50)
    
    async with aiohttp.ClientSession() as session:
        for name, url in APIS:
            await test_api(session, name, url)
    
    print('=' * 50)
    print('Teste concluído!')

if __name__ == '__main__':
    asyncio.run(main())