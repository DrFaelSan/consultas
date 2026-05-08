# Consultas Unificado - Async v3.0

Script Python async otimizado para Termux que agrega múltiplos endpoints de consulta com fallback automático.

## Características

- **Async/Await** - Consultas paralelas com `aiohttp`
- **Timeout** - 10 segundos por request
- **Retry** - 2 tentativas automáticas em caso de falha
- **Fallback** - Tenta múltiplas fontes automaticamente
- **Leve** - Apenas `aiohttp` + `cloudscraper` como dependências

## Tipos de Consulta

| Código | Tipo | Fontes |
|--------|------|--------|
| 1 | CPF | BrazilAPI, ReceitaWS |
| 2 | CNPJ | BrasilAPI, ReceitaWS |
| 3 | Placa | ApiCarros (cloudscraper), Sinesp, ConsultaDF |
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
pkg install ca-certificates
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

## Desinstalação

```bash
cd ..
rm -rf consultas
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

APIs governamentais como SINESP podem ficar offline frequentemente. O script tenta outras fontes automaticamente em caso de falha.

---

Autor: Baseado nas referências do projeto
Licença: MIT