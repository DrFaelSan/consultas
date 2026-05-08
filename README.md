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
```

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

## Uso

### Modo Interativo
```bash
python main.py
```

### Linha de Comando
```bash
# CPF
python main.py cpf 12345678900

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