# Consultas Unificado - Async v3.0

Script Python async otimizado para Termux que agrega múltiplos endpoints de consulta com fallback automático.

## Características

- **Async/Await** - Consultas paralelas com `aiohttp`
- **Timeout** - 10-20 segundos por request
- **Retry** - 2 tentativas automáticas em caso de falha
- **Fallback** - Tenta múltiplas fontes automaticamente
- **Cloudflare Bypass** - Usa cloudscraper com perfil Desktop
- **Leve** - Apenas `aiohttp` + `cloudscraper` como dependências

## Tipos de Consulta

| Código | Tipo | Fontes |
|--------|------|--------|
| 1 | CPF | BrazilAPI, ReceitaWS |
| 2 | CNPJ | BrasilAPI, ReceitaWS |
| 3 | Placa | PlacaIPVA, KePlaca, PlacaFIPE, ApiCarros |
| 4 | CEP | ViaCEP, Postmon, ApiCEP |
| 5 | IP | IP-API, IPInfo, IPWhois |
| 6 | DDD | BrasilAPI |
| 7 | BIN | BinList |
| 8 | Banco | BrasilAPI |
| 9 | Clima | IPGeolocation, OpenWeatherMap |
| A | NCM | BrasilAPI |
| B | ISBN | BrasilAPI |
| C | Feriado | BrasilAPI |
| D | Taxa | BrasilAPI |
| E | Câmbio | BrasilAPI |
| F | IBGE | BrasilAPI |
| G | PIX | BrasilAPI |
| H | Corretora | CVM |
| I | Domínio | Registro.br |
| J | FIPE | BrasilAPI |
| K | Ticker | BrasilAPI |
| L | Fundo CVM | CVM |
| M | Distância | BrasilAPI |
| N | CNPJ Simples | ReceitaWS |
| O | CNH | Detran (requer chave) |
| P | Loterica | BrasilAPI |

## Desinstalação

```bash
cd ..
rm -rf consultas
```

Ou manualmente:

```bash
pip install -r requirements.txt
```

## Instalação

Requisitos

- Python 3.8+
- Internet
- (Opcional) Termux no Android

```bash
pkg update && pkg upgrade
pkg install ca-certificates openssl
git clone https://github.com/DrFaelSan/consultas.git
cd consultas
chmod +x install.sh
./install.sh
```

Ou manualmente:

```bash
pip install -r requirements.txt
pip install cloudscraper
cp .env.example .env
# Edite o arquivo .env com suas chaves de API
```

### Configuração de API Keys (opcional)

Copie o arquivo `.env.example` para `.env` e adicione suas chaves:

```bash
cp .env.example .env
nano .env
```

Variáveis disponíveis:
- `BRASIL_API_KEY` - API Brasil (https://brasilapi.com.br)
- `OPENWEATHER_API_KEY` - OpenWeatherMap (https://openweathermap.org)
- `IPGEOLOCATION_KEY` - IPGeolocation (https://ipgeolocation.io)
- `API_BRASIL_PLACA_KEY` - API Brasil Placa (https://apibrasil.com.br)

## Troubleshooting (Termux)

Se houver erro de conexão:

```bash
# Atualizar certificados
pkg update && pkg upgrade
pkg install ca-certificates openssl

# Testar conectividade
curl -L -A "Mozilla/5.0" https://placaipva.com.br/placa/ABC1234

# Forçar DNS do Google
echo "nameserver 8.8.8.8" > $PREFIX/etc/resolv.conf
```

## Menu

```
[1] CPF/GERAR CPF  → Consulta, Gera ou Valida CPF
[2] CNPJ
[3] VEÍCULO     → Placa, Chassi, Renavam, Motor
[4] CEP
[5] IP
[6] DDD
[7] BIN
[8] BANCO
[9] CLIMA
[A] NCM    [E] CÂMBIO
[B] ISBN   [F] IBGE
[C] FERIADO[G] PIX
[D] TAXA   [H] CORRETORA
[I] DOMÍNIO[J] FIPE
[K] TICKER[L] FUNDO CVM
[M] DISTÂNCIA
[N] CNPJS [O] CNH
[P] LOTÉRICA

[G] GERAR CPF    [H] HISTÓRICO    [C] LIMPAR    [0] SAIR
```

# CNPJ
python main.py cnpj 12345678000100

# CEP
python main.py cep 01001000

# IP
python main.py ip 8.8.8.8

# Placa
python main.py placa ABC1234

# DDD
python main.py ddd 11

# BIN
python main.py bin 453201

# Banco (lista)
python main.py banco

# Clima
python main.py clima

# NCM
python main.py ncm 85176200

# ISBN
python main.py isbn 9788522034567

# Feriado
python main.py feriado 2026

# Taxa
python main.py taxa selic
python main.py taxa  # lista todas

# Câmbio
python main.py cambio usd
python main.py cambio  # lista moedas

# IBGE
python main.py ibge sp  # municipios de SP
python main.py ibge  # lista estados

# PIX
python main.py pix nubank
python main.py pix  # lista participantes

# Corretora
python main.py corretora 12345678000100

# Domínio
python main.py dominio google.com.br

# FIPE
python main.py fipe  # lista marcas
python main.py fipe carros 123  # modelos

# Ticker
python main.py ticker acoes
python main.py ticker fundos

# Fundo CVM
python main.py fundos 12345678000112
python main.py fundos  # lista fundos

# Distância
python main.py distancia "São Paulo, SP" "Rio de Janeiro, RJ"

# CNPJ Simples
python main.py cnpjs 12345678000100

# CNH
python main.py cnh 12345678901

# Lotérica
python main.py loterica mega-sena
python main.py loterica  # lista jogos
```

### Outras Opções
```bash
# Ver histórico
python main.py --history

# Limpar cache
python main.py --clear-cache
```

## Requisitos

- Python 3.7+
- aiohttp>=3.8.0
- cloudscraper>=1.2.71

## Arquivos

- `main.py` - Script principal
- `requirements.txt` - Dependências
- `install.sh` - Script de instalação para Termux
- `cache.json` - Cache de resultados (criado automaticamente)
- `historico.json` - Histórico de consultas (criado automaticamente)

## Nota

consultas de Placa dependem de scraping de sites públicos. Se todos falharem, os sites podem estar temporariamente offline ou bloqueando seu IP.

---

Autor: Baseado nas referências do projeto
Licença: MIT