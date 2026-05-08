#!/bin/bash
# Teste das APIs - Execute no Termux: bash test_apis.sh

echo "=================================================="
echo "TESTE DE APIs"
echo "=================================================="

# BrasilAPI
echo -n "[1] BrasilAPI Banks: "
curl -s -o /dev/null -w "%{http_code}\n" https://brasilapi.com.br/api/banks/v1

echo -n "[2] BrasilAPI DDD: "
curl -s -o /dev/null -w "%{http_code}\n" https://brasilapi.com.br/api/ddd/v1/11

echo -n "[3] BrasilAPI FIPE: "
curl -s -o /dev/null -w "%{http_code}\n" https://brasilapi.com.br/api/fipe/marcas/v1/carros

echo -n "[4] BrasilAPI Taxas: "
curl -s -o /dev/null -w "%{http_code}\n" https://brasilapi.com.br/api/taxas/v1

echo -n "[5] BrasilAPI Feriados: "
curl -s -o /dev/null -w "%{http_code}\n" https://brasilapi.com.br/api/feriados/v1/2026

# ViaCEP
echo -n "[6] ViaCEP: "
curl -s -o /dev/null -w "%{http_code}\n" https://viacep.com.br/ws/01001000/json/

# IP-API
echo -n "[7] IP-API: "
curl -s -o /dev/null -w "%{http_code}\n" http://ip-api.com/json/8.8.8.8

# Placa APIs
echo -n "[8] PlacaIPVA: "
curl -s -o /dev/null -w "%{http_code}\n" https://placaipva.com.br/placa/ABC1234

echo -n "[9] KePlaca: "
curl -s -o /dev/null -w "%{http_code}\n" https://www.keplaca.com/placa/ABC1234

echo -n "[10] PlacaFIPE: "
curl -s -o /dev/null -w "%{http_code}\n" https://placafipe.com/ABC1234

echo -n "[11] ApiCarros: "
curl -s -o /dev/null -w "%{http_code}\n" https://apicarros.com/v1/consulta/ABC1234

# BinList
echo -n "[12] BinList: "
curl -s -o /dev/null -w "%{http_code}\n" https://lookup.binlist.net/453201

# Teste com detalhes (200 = OK)
echo ""
echo "=================================================="
echo "TESTE DETALHADO"
echo "=================================================="

echo "BrasilAPI - Banks:"
curl -s https://brasilapi.com.br/api/banks/v1 | head -c 200
echo ""

echo ""
echo "ViaCEP - 01001000:"
curl -s https://viacep.com.br/ws/01001000/json/ | head -c 200
echo ""

echo ""
echo "=================================================="
echo "FIM DOS TESTES"
echo "=================================================="