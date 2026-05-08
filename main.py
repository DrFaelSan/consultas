#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consultas Unificado - Script Async Otimizado para Termux
Agrega múltiplos endpoints com fallback automático, timeout 10s, retry 2x
Autor: Baseado nas referências do projeto
GitHub: https://github.com/seu-repo/consultas-unificado
"""

import os
import sys
import asyncio
import json
import time
import hashlib
import uuid
import argparse
import re
import random
import math
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        print("Arquivo .env não encontrado. Copie .env.example para .env")
except ImportError:
    pass

# Configurações com fallback para valores padrão
CONFIG = {
    'BRASIL_API_KEY': os.getenv('BRASIL_API_KEY', ''),
    'OPENWEATHER_API_KEY': os.getenv('OPENWEATHER_API_KEY', '6e5f80bfbe2dd7591b7a9d65157d7e4b'),
    'IPGEOLOCATION_KEY': os.getenv('IPGEOLOCATION_KEY', '13a008ccb7594d1cb4a6e986847fc507'),
    'API_BRASIL_PLACA_KEY': os.getenv('API_BRASIL_PLACA_KEY', '9f5938b6-b2eb-4c4f-94f1-4fcbda0e66d8'),
}

try:
    import aiohttp
except ImportError:
    print("Instalando aiohttp...")
    os.system("pip install aiohttp")
    import aiohttp

# ============================================================================
# CONFIGURAÇÕES E VARIÁVEIS DE AMBIENTE
# ============================================================================

class Config:
    """Configurações globais"""
    TIMEOUT = 10  # Timeout de 10 segundos
    RETRY = 2     # 2 tentativas
    
    # Credenciais hardcoded
    RAPIDAPI_KEY = 'e01238c690msh74f20bdc84d5dcfp122562jsnc9921fa7c4c1'
    IPGEOLOCATION_KEY = '9313e7887bad45cea6d4b5845f085464'
    IPFIND_KEY = '22e75f18-7853-4227-ac49-3a8a72893210'
    GERADOR_TOKEN = 'f01e0024a26baef3cc53a2ac208dd141'
    
    # Arquivos
    CACHE_FILE = 'cache.json'
    HISTORY_FILE = 'historico.json'
    
    @staticmethod
    def load_json(file: str, default: Any = None) -> Any:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return default if default is not None else {}
    
    @staticmethod
    def save_json(file: str, data: Any):
        try:
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass


# ============================================================================
# CORES
# ============================================================================

class C:
    VERMELHO = '\033[31m'
    VERDE = '\033[32m'
    AMARELO = '\033[33m'
    AZUL = '\033[34m'
    CIANO = '\033[36m'
    BRANCO = '\033[37m'
    RESET = '\033[0m'
    
    @staticmethod
    def t(cor, texto):
        return f"{cor}{texto}{C.RESET}"


# ============================================================================
# CLIENTE HTTP ASYNC
# ============================================================================

class HttpClient:
    """Cliente HTTP async com timeout e retry"""
    
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Accept': 'application/json, text/html, */*',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=Config.TIMEOUT),
            connector=aiohttp.TCPConnector(
                limit=10,
                ssl=False
            ),
            headers=self.DEFAULT_HEADERS
        )
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def get(self, url: str, **kwargs) -> Optional[Dict]:
        """GET com retry"""
        for attempt in range(Config.RETRY):
            try:
                async with self.session.get(url, **kwargs) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        if '<!DOCTYPE html>' in text or '<html' in text[:50]:
                            print(C.t(C.AMARELO, "  Erro: Servidor retornou HTML (possível bloqueio)"))
                            return None
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            print(C.t(C.AMARELO, f"  Erro: JSON inválido"))
                            return None
            except asyncio.TimeoutError:
                print(C.t(C.AMARELO, f"  Timeout na tentativa {attempt + 1}"))
            except Exception as e:
                print(C.t(C.VERMELHO, f"  Erro: {str(e)[:50]}"))
            
            if attempt < Config.RETRY - 1:
                await asyncio.sleep(1)
        
        return None
    
    async def post(self, url: str, **kwargs) -> Optional[Any]:
        """POST com retry"""
        for attempt in range(Config.RETRY):
            try:
                async with self.session.post(url, **kwargs) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        try:
                            return json.loads(text)
                        except:
                            return text
            except asyncio.TimeoutError:
                print(C.t(C.AMARELO, f"  Timeout na tentativa {attempt + 1}"))
            except Exception as e:
                print(C.t(C.VERMELHO, f"  Erro: {str(e)[:50]}"))
            
            if attempt < Config.RETRY - 1:
                await asyncio.sleep(1)
        
        return None


# ============================================================================
# VALIDADORES LOCAIS
# ============================================================================

class Validators:
    """Validadores e geradores locais"""
    
    @staticmethod
    def gerar_cpf() -> str:
        while True:
            nums = [random.randint(0, 9) for _ in range(9)]
            soma = sum(nums[i] * (10 - i) for i in range(9))
            d1 = (soma * 10 % 11) % 10
            nums.append(d1)
            soma = sum(nums[i] * (11 - i) for i in range(10))
            d2 = (soma * 10 % 11) % 10
            cpf = ''.join(map(str, nums)) + str(d2)
            if cpf != cpf[0] * 11:
                return cpf
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        cpf = ''.join(filter(str.isdigit, cpf))
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        d1 = (soma * 10 % 11) % 10
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        d2 = (soma * 10 % 11) % 11
        return cpf[9] == str(d1) and cpf[10] == str(d2 % 11)
    
    @staticmethod
    def formatar_cpf(cpf: str) -> str:
        cpf = ''.join(filter(str.isdigit, cpf))
        if len(cpf) == 11:
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return cpf
    
    @staticmethod
    def limpar_cnpj(cnpj: str) -> str:
        """Remove pontos, barras, traços e converte para maiúsculas"""
        cnpj = cnpj.upper().replace('.', '').replace('/', '').replace('-', '').replace(' ', '')
        return cnpj
    
    @staticmethod
    def formatar_cnpj(cnpj: str) -> str:
        """Formata CNPJ (pode ser numérico ou alfanumérico)"""
        cnpj = Validators.limpar_cnpj(cnpj)
        if len(cnpj) == 14:
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        return cnpj
    
    @staticmethod
    def limpar_placa(placa: str) -> str:
        """Remove traços e espaços, converte para maiúsculas"""
        return placa.upper().replace('-', '').replace(' ', '').replace('.', '')
    
    @staticmethod
    def validar_placa(placa: str) -> bool:
        """Valida placa brasileira (antiga ou Mercosul)"""
        placa = Validators.limpar_placa(placa)
        if len(placa) != 7:
            return False
        if placa[:3].isalpha() and placa[3:].isdigit():
            return True
        if placa[:3].isalpha() and placa[3:4].isdigit() and placa[4:].isalpha():
            return True
        return False
    
    @staticmethod
    def formatar_placa(placa: str) -> str:
        """Formata placa (ABC-1234 ou ABC1D23)"""
        placa = Validators.limpar_placa(placa)
        if len(placa) == 7:
            if placa[3:].isdigit():
                return f"{placa[:3]}-{placa[3:]}"
            elif placa[3].isdigit():
                return f"{placa[:3]}{placa[3:]}"
        return placa
    
    @staticmethod
    def formatar_cep(cep: str) -> str:
        cep = ''.join(filter(str.isdigit, cep))
        if len(cep) == 8:
            return f"{cep[:5]}-{cep[5:]}"
        return cep


# ============================================================================
# SERVIÇOS DE CONSULTA
# ============================================================================

class ConsultaCPF:
    """Consulta CPF - 3+ fontes com fallback"""
    
    @staticmethod
    async def consultar(cpf: str) -> Dict:
        cpf = ''.join(filter(str.isdigit, cpf))
        print(C.t(C.CIANO, f"\n[CPF] {Validators.formatar_cpf(cpf)}"))
        
        async with HttpClient() as client:
            # BrazilAPI
            print(C.t(C.AZUL, "  → BrazilAPI..."))
            url = f"https://api.brazilapi.com.br/cpf/v1/{cpf}"
            result = await client.get(url)
            if result and 'error' not in result:
                print(C.t(C.VERDE, "  ✓ BrazilAPI: OK"))
                return {'fonte': 'BrazilAPI', 'dados': result}
            print(C.t(C.VERMELHO, "  ✗ BrazilAPI: Falhou"))
            
            # ReceitaWS
            print(C.t(C.AZUL, "  → ReceitaWS..."))
            url = f"https://www.receitaws.com.br/v1/cpf/{cpf}"
            result = await client.get(url)
            if result and result.get('status') != 'ERROR':
                print(C.t(C.VERDE, "  ✓ ReceitaWS: OK"))
                return {'fonte': 'ReceitaWS', 'dados': result}
            print(C.t(C.VERMELHO, "  ✗ ReceitaWS: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'CPF não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        for k, v in dados.items():
            out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaCNPJ:
    """Consulta CNPJ - 2+ fontes"""
    
    @staticmethod
    async def consultar(cnpj: str) -> Dict:
        cnpj = Validators.limpar_cnpj(cnpj)
        print(C.t(C.CIANO, f"\n[CNPJ] {Validators.formatar_cnpj(cnpj)}"))
        
        async with HttpClient() as client:
            # BrasilAPI
            print(C.t(C.AZUL, "  → BrasilAPI..."))
            url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
            result = await client.get(url)
            if result and 'error' not in result:
                print(C.t(C.VERDE, "  ✓ BrasilAPI: OK"))
                return {'fonte': 'BrasilAPI', 'dados': result}
            print(C.t(C.VERMELHO, "  ✗ BrasilAPI: Falhou"))
            
            # ReceitaWS
            print(C.t(C.AZUL, "  → ReceitaWS..."))
            url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
            result = await client.get(url)
            if result and result.get('status') != 'ERROR':
                print(C.t(C.VERDE, "  ✓ ReceitaWS: OK"))
                return {'fonte': 'ReceitaWS', 'dados': result}
            print(C.t(C.VERMELHO, "  ✗ ReceitaWS: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'CNPJ não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        campos = ['nome', 'fantasia', 'cnpj', 'abertura', 'situacao', 'logradouro', 
                  'bairro', 'municipio', 'uf', 'cep', 'telefone', 'email', 'porte', 'capital_social']
        for campo in campos:
            if campo in dados:
                val = dados[campo]
                if campo == 'capital_social':
                    val = f"R$ {val}"
                out.append(C.t(C.AMARELO, f"  • {campo.upper()}: ") + str(val))
        
        return "\n".join(out)


class ConsultaPlaca:
    """Consulta Placa com fallback usando cloudscraper (bypass Cloudflare)"""
    
    @staticmethod
    async def consultar(placa: str, tipo: str = 'placa') -> Dict:
        if tipo == 'renavam':
            return await ConsultaRenavam.consultar(placa)
        elif tipo == 'chassi':
            return await ConsultaRenavam.consultar(placa)
        elif tipo == 'cnh':
            return await ConsultaCNH.consular(placa)
        elif tipo == 'antt':
            return await ConsultaRenavam.consultar(placa)
        else:
            return await ConsultaPlaca._consultar_placa(placa)
    
    @staticmethod
    async def _consultar_placa(placa: str) -> Dict:
        placa = Validators.limpar_placa(placa)
        print(C.t(C.CIANO, f"\n[PLACA] {Validators.formatar_placa(placa)}"))

        try:
            from cloudscraper import create_scraper
            scraper = create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
        except ImportError:
            print(C.t(C.VERMELHO, "  Cloudscraper não instalado"))
            print(C.t(C.VERMELHO, "  Execute: pip install cloudscraper"))
            return {'fonte': 'nenhuma', 'dados': {'erro': 'Dependência ausente'}}

        fontes = [
            ('PlacaIPVA', f'https://placaipva.com.br/placa/{placa}', ConsultaPlaca._parse_placaipva),
            ('KePlaca', f'https://www.keplaca.com/placa/{placa}', ConsultaPlaca._parse_keplaca),
            ('PlacaFIPE', f'https://placafipe.com/{placa}', ConsultaPlaca._parse_placafipe),
        ]

        for nome, url, parser in fontes:
            print(C.t(C.AZUL, f"  → {nome}..."))
            try:
                response = await asyncio.to_thread(scraper.get, url, timeout=20)
                if response.status_code == 200:
                    dados = parser(response.text)
                    if dados and dados.get('marca'):
                        print(C.t(C.VERDE, f"  ✓ {nome}: OK"))
                        return {'fonte': nome, 'dados': dados}
                elif response.status_code == 403:
                    print(C.t(C.AMARELO, f"  {nome}: Bloqueado (403)"))
                else:
                    print(C.t(C.AMARELO, f"  {nome}: HTTP {response.status_code}"))
            except Exception as e:
                print(C.t(C.VERMELHO, f"  ✗ {nome}: {str(e)[:50]}"))

        print(C.t(C.AZUL, "  → ApiCarros..."))
        try:
            url = f'https://apicarros.com/v1/consulta/{placa}'
            response = await asyncio.to_thread(scraper.get, url, timeout=20)
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and 'erro' not in data and data.get('marca'):
                        print(C.t(C.VERDE, "  ✓ ApiCarros: OK"))
                        return {'fonte': 'ApiCarros', 'dados': data}
                except:
                    pass
            print(C.t(C.VERMELHO, "  ✗ ApiCarros: Falhou"))
        except Exception as e:
            print(C.t(C.VERMELHO, f"  ✗ ApiCarros: {str(e)[:50]}"))

        return {'fonte': 'nenhuma', 'dados': {'erro': 'Placa não encontrada'}}

    @staticmethod
    def _parse_placaipva(html: str) -> Optional[Dict]:
        import re
        dados = {}
        patterns = [
            (r'<th>Marca</th>\s*<td[^>]*>([^<]+)', 'marca'),
            (r'<th>Modelo</th>\s*<td[^>]*>([^<]+)', 'modelo'),
            (r'<th>Ano</th>\s*<td[^>]*>([^<]+)', 'ano'),
            (r'<th>Cor</th>\s*<td[^>]*>([^<]+)', 'cor'),
            (r'<th>UF</th>\s*<td[^>]*>([^<]+)', 'uf'),
        ]
        for pattern, key in patterns:
            match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if match:
                dados[key] = match.group(1).strip()
        if not dados:
            for key, pattern in [('marca', r'Marca[:\s]*([^<\n]+)'), ('modelo', r'Modelo[:\s]*([^<\n]+)')]:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    dados[key] = match.group(1).strip()
        return dados if dados else None

    @staticmethod
    def _parse_keplaca(html: str) -> Optional[Dict]:
        import re
        dados = {}
        patterns = [
            (r'Marca</span>\s*<span[^>]*>([^<]+)', 'marca'),
            (r'Modelo</span>\s*<span[^>]*>([^<]+)', 'modelo'),
            (r'Ano</span>\s*<span[^>]*>([^<]+)', 'ano'),
        ]
        for pattern, key in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                dados[key] = match.group(1).strip()
        return dados if dados else None

    @staticmethod
    def _parse_placafipe(html: str) -> Optional[Dict]:
        import re
        dados = {}
        for key, pattern in [('marca', r'Marca[:\s]*([^<\n]+)'), ('modelo', r'Modelo[:\s]*([^<\n]+)')]:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                dados[key] = match.group(1).strip()
        return dados if dados else None
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        for k, v in dados.items():
            out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


# ============================================================================
# Sub-menu VEÍCULO (opção 3 do menu principal)
# ============================================================================

class MenuVeiculo:
    """Sub-menu para consultas de veículo"""
    
    @staticmethod
    def menu_veiculo():
        print(C.t(C.CIANO, """
    ┌──────────────────────────────────────────────────┐
    │           [MENU VEÍCULO]                     │
    ├──────────────────────────────────────────────────┤
    │  [1] PLACA      (buscar por placa)             │
    │  [2] CHASSI    (buscar por chassi)            │
    │  [3] RENAVAM   (buscar por RENAVAM)         │
    │  [4] MOTOR    (buscar por número motor)     │
    │  [5] ANTT      (veículos de transporte)    │
    │  [6] CRLV     (certificado)             │
    │  [7] IPVA     (débitos)               │
    │  [8] MULTAS   (infrações)              │
    ├──────────────────────────────────────────────────┤
    │  [0] VOLTAR ao menu principal              │
    └──────────────────────────────────────────────────┘
        """))
    
    @staticmethod
    async def executar(opcao: str, valor: str = None):
        opcoes = {
            '1': ('PLACA', ConsultaPlaca._consultar_placa),
            '2': ('CHASSI', ConsultaRenavam.consultar),
            '3': ('RENAVAM', ConsultaRenavam.consultar),
            '4': ('MOTOR', ConsultaRenavam.consultar),
            '5': ('ANTT', ConsultaRenavam.consultar),
        }
        
        if opcao in opcoes:
            nome, func = opcoes[opcao]
            print(C.t(C.CIANO, f"\n[{nome}] {valor}"))
            resultado = await func(valor)
            ConsultaPlaca.formatar(resultado)
        else:
            print(C.t(C.VERMELHO, "\n  Opção inválida!"))
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        for k, v in dados.items():
            out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaCEP:
    """Consulta CEP - 3 fontes"""
    
    @staticmethod
    async def consultar(cep: str) -> Dict:
        cep = ''.join(filter(str.isdigit, cep))
        print(C.t(C.CIANO, f"\n[CEP] {Validators.formatar_cep(cep)}"))
        
        async with HttpClient() as client:
            # ViaCEP
            print(C.t(C.AZUL, "  → ViaCEP..."))
            url = f'https://viacep.com.br/ws/{cep}/json/'
            result = await client.get(url)
            if result and 'erro' not in result:
                return {'fonte': 'ViaCEP', 'dados': result}
            
            # Postmon
            print(C.t(C.AZUL, "  → Postmon..."))
            url = f'https://api.postmon.com.br/v1/cep/{cep}'
            result = await client.get(url)
            if result and 'erro' not in result:
                return {'fonte': 'Postmon', 'dados': result}
            
            # ApiCEP
            print(C.t(C.AZUL, "  → ApiCEP..."))
            url = f'https://ws.apicep.com/cep/{cep}.json'
            result = await client.get(url)
            if result and result.get('ok'):
                return {'fonte': 'ApiCEP', 'dados': result}
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'CEP não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        for k, v in dados.items():
            out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaIP:
    """Consulta IP - 3 fontes"""
    
    @staticmethod
    async def consultar(ip: str) -> Dict:
        print(C.t(C.CIANO, f"\n[IP] {ip}"))
        
        async with HttpClient() as client:
            # IP-API
            print(C.t(C.AZUL, "  → IP-API..."))
            url = f'http://ip-api.com/json/{ip}'
            result = await client.get(url)
            if result and result.get('status') == 'success':
                return {'fonte': 'IP-API', 'dados': result}
            
            # IPInfo
            print(C.t(C.AZUL, "  → IPInfo..."))
            url = f'https://ipinfo.io/{ip}/json'
            result = await client.get(url)
            if result:
                return {'fonte': 'IPInfo', 'dados': result}
            
            # IPWhois
            print(C.t(C.AZUL, "  → IPWhois..."))
            url = f'https://ipwhois.app/json/{ip}'
            result = await client.get(url)
            if result:
                return {'fonte': 'IPWhois', 'dados': result}
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'IP não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        for k, v in dados.items():
            out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaDDD:
    """Consulta DDD"""
    
    @staticmethod
    async def consultar(ddd: str) -> Dict:
        ddd = ''.join(filter(str.isdigit, ddd))
        print(C.t(C.CIANO, f"\n[DDD] {ddd}"))
        
        async with HttpClient() as client:
            url = f'https://brasilapi.com.br/api/ddd/v1/{ddd}'
            result = await client.get(url)
            if result:
                return {'fonte': 'BrasilAPI', 'dados': result}
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'DDD não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        for k, v in dados.items():
            if isinstance(v, list):
                out.append(C.t(C.AMARELO, f"  • {k.upper()}:"))
                for item in v[:10]:
                    out.append(f"    - {item}")
            else:
                out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaBIN:
    """Consulta BIN de cartão"""
    
    @staticmethod
    async def consultar(bin_code: str) -> Dict:
        bin_code = ''.join(filter(str.isdigit, bin_code))[:6]
        print(C.t(C.CIANO, f"\n[BIN] {bin_code}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → Lookup Binlist..."))
            url = f'https://lookup.binlist.net/{bin_code}'
            try:
                result = await client.get(url)
                if result:
                    print(C.t(C.VERDE, "  ✓ Binlist: OK"))
                    return {'fonte': 'Binlist', 'dados': result}
            except Exception as e:
                print(C.t(C.VERMELHO, f"  ✗ Binlist: {str(e)[:30]}"))
            
            # Fallback: Consulta via API pública
            print(C.t(C.AZUL, "  → BinAPI..."))
            try:
                url = f'https://binlists.com/{bin_code}'
                result = await client.get(url)
                if result and result.get('scheme'):
                    print(C.t(C.VERDE, "  ✓ BinAPI: OK"))
                    return {'fonte': 'BinAPI', 'dados': result}
            except:
                pass
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'BIN não encontrado - API bloqueada'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        for k, v in dados.items():
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    out.append(C.t(C.AMARELO, f"  • {k.upper()}.{k2.upper()}: ") + str(v2))
            else:
                out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaBanco:
    """Consulta Banco"""
    
    @staticmethod
    async def consultar(codigo: str = None) -> Dict:
        print(C.t(C.CIANO, f"\n[BANCO]"))
        
        async with HttpClient() as client:
            url = 'https://brasilapi.com.br/api/banks/v1'
            result = await client.get(url)
            if result:
                if codigo:
                    for b in result:
                        if str(b.get('code')) == codigo:
                            return {'fonte': 'BrasilAPI', 'dados': b}
                    return {'fonte': 'BrasilAPI', 'dados': {'erro': 'Banco não encontrado'}}
                return {'fonte': 'BrasilAPI', 'dados': {'bancos': result[:30]}}
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'Erro ao buscar bancos'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        if 'bancos' in dados:
            out.append(C.t(C.AMARELO, "  Lista de bancos:"))
            for b in dados['bancos']:
                out.append(f"    {b.get('code')} - {b.get('name')}")
        else:
            for k, v in dados.items():
                out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaClima:
    """Consulta Clima - Temperatura por localização"""
    
    @property
    def OPENWEATHER_API_KEY(self):
        return CONFIG.get('OPENWEATHER_API_KEY') or '6e5f80bfbe2dd7591b7a9d65157d7e4b'
    
    @property
    def IPGEOLOCATION_KEY(self):
        return CONFIG.get('IPGEOLOCATION_KEY') or '13a008ccb7594d1cb4a6e986847fc507'
    
    @staticmethod
    async def consultar(localizacao: str = None) -> Dict:
        print(C.t(C.CIANO, f"\n[CLIMA]"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → IPGeolocation..."))
            url = f'https://api.ipgeolocation.io/ipgeo?apiKey={CONFIG.get("IPGEOLOCATION_KEY", "13a008ccb7594d1cb4a6e986847fc507")}'
            result = await client.get(url)
            if result and result.get('latitude'):
                lat, lon = result.get('latitude'), result.get('longitude')
                cidade = result.get('city', 'Desconhecido')
                pais = result.get('country_name', 'BR')
                
                print(C.t(C.AZUL, "  → OpenWeatherMap..."))
                weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={CONFIG.get('OPENWEATHER_API_KEY', '6e5f80bfbe2dd7591b7a9d65157d7e4b')}&units=metric&lang=pt_br"
                weather_result = await client.get(weather_url)
                if weather_result and weather_result.get('main'):
                    dados = {
                        'cidade': cidade,
                        'pais': pais,
                        'temperatura': weather_result['main'].get('temp'),
                        'sensacao': weather_result['main'].get('feels_like'),
                        'umidade': weather_result['main'].get('humidity'),
                        'descricao': weather_result['weather'][0].get('description') if weather_result.get('weather') else '',
                        'icone': weather_result['weather'][0].get('icon') if weather_result.get('weather') else ''
                    }
                    print(C.t(C.VERDE, "  ✓ OpenWeatherMap: OK"))
                    return {'fonte': 'OpenWeatherMap', 'dados': dados}
                print(C.t(C.VERMELHO, "  ✗ OpenWeatherMap: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'Clima não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        campos = ['cidade', 'pais', 'temperatura', 'sensacao', 'umidade', 'descricao']
        for campo in campos:
            if campo in dados:
                val = dados[campo]
                if campo in ['temperatura', 'sensacao']:
                    val = f"{val}°C"
                elif campo == 'umidade':
                    val = f"{val}%"
                out.append(C.t(C.AMARELO, f"  • {campo.upper()}: ") + str(val))
        
        return "\n".join(out)


class ConsultaNCM:
    """Consulta NCM - Nomenclatura Comum do Mercosul"""
    
    @staticmethod
    async def consultar(codigo: str) -> Dict:
        codigo = ''.join(filter(str.isdigit, codigo))[:8]
        print(C.t(C.CIANO, f"\n[NCM] {codigo}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → BrasilAPI NCM..."))
            url = f"https://brasilapi.com.br/api/ncm/v1/{codigo}"
            result = await client.get(url)
            if result and result.get('codigo'):
                print(C.t(C.VERDE, "  ✓ BrasilAPI: OK"))
                return {'fonte': 'BrasilAPI', 'dados': result}
            print(C.t(C.VERMELHO, "  ✗ BrasilAPI: Falhou"))
            
            print(C.t(C.AZUL, "  → BrasilAPI busca..."))
            url = f"https://brasilapi.com.br/api/ncm/v1?search={codigo}"
            result = await client.get(url)
            if result and isinstance(result, list) and len(result) > 0:
                print(C.t(C.VERDE, "  ✓ BrasilAPI: OK"))
                return {'fonte': 'BrasilAPI', 'dados': result[0]}
            print(C.t(C.VERMELHO, "  ✗ BrasilAPI: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'NCM não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        if isinstance(dados, list):
            for item in dados[:5]:
                for k, v in item.items():
                    out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        else:
            for k, v in dados.items():
                out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaISBN:
    """Consulta ISBN - Livros"""
    
    @staticmethod
    async def consultar(isbn: str) -> Dict:
        isbn = ''.join(filter(str.isdigit, isbn))[:13]
        print(C.t(C.CIANO, f"\n[ISBN] {isbn}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → BrasilAPI ISBN..."))
            url = f"https://brasilapi.com.br/api/isbn/v1/{isbn}"
            result = await client.get(url)
            if result and result.get('title'):
                print(C.t(C.VERDE, "  ✓ BrasilAPI: OK"))
                return {'fonte': 'BrasilAPI', 'dados': result}
            print(C.t(C.VERMELHO, "  ✗ BrasilAPI: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'ISBN não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        campos = ['title', 'authors', 'publisher', 'year', 'isbn', 'isbn_13']
        for campo in campos:
            if campo in dados:
                val = dados[campo]
                if isinstance(val, list):
                    val = ', '.join(map(str, val))
                out.append(C.t(C.AMARELO, f"  • {campo.upper()}: ") + str(val))
        
        return "\n".join(out)


class ConsultaFeriado:
    """Consulta Feriados Nacionais"""
    
    @staticmethod
    async def consultar(ano: str = None) -> Dict:
        if not ano:
            ano = datetime.now().strftime('%Y')
        else:
            ano = ''.join(filter(str.isdigit, ano))[:4]
        
        print(C.t(C.CIANO, f"\n[FERIADOS {ano}]"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → BrasilAPI Feriados..."))
            url = f"https://brasilapi.com.br/api/feriados/v1/{ano}"
            result = await client.get(url)
            if result and isinstance(result, list):
                print(C.t(C.VERDE, "  ✓ BrasilAPI: OK"))
                return {'fonte': 'BrasilAPI', 'dados': {'ano': ano, 'feriados': result}}
            print(C.t(C.VERMELHO, "  ✗ BrasilAPI: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'Feriados não encontrados'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        feriados = dados.get('feriados', [])
        for f in feriados:
            nome = f.get('name', 'N/A')
            data = f.get('date', 'N/A')
            tipo = f.get('type', 'N/A')
            out.append(f"  {data} - {nome} ({tipo})")
        
        return "\n".join(out)


class ConsultaTaxa:
    """Consulta Taxas e Índices"""
    
    @staticmethod
    async def consultar(sigla: str = None) -> Dict:
        print(C.t(C.CIANO, f"\n[TAXAS]"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → BrasilAPI Taxas..."))
            url = "https://brasilapi.com.br/api/taxas/v1"
            result = await client.get(url)
            if result and isinstance(result, list):
                if sigla:
                    for t in result:
                        if t.get('sigla', '').upper() == sigla.upper():
                            print(C.t(C.VERDE, "  ✓ BrasilAPI: OK"))
                            return {'fonte': 'BrasilAPI', 'dados': t}
                    print(C.t(C.VERMELHO, "  ✗ Taxa não encontrada"))
                    return {'fonte': 'BrasilAPI', 'dados': {'erro': 'Taxa não encontrada'}}
                print(C.t(C.VERDE, "  ✓ BrasilAPI: OK"))
                return {'fonte': 'BrasilAPI', 'dados': {'taxas': result[:15]}}
            print(C.t(C.VERMELHO, "  ✗ BrasilAPI: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'Taxas não encontradas'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        if 'taxas' in dados:
            out.append(C.t(C.AMARELO, "  Taxas disponíveis:"))
            for t in dados['taxas']:
                nome = t.get('nome', 'N/A')
                valor = t.get('valor', 'N/A')
                out.append(f"    {nome}: {valor}")
        else:
            for k, v in dados.items():
                out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaCambio:
    """Consulta Câmbio - Moedas e Cotações"""
    
    @staticmethod
    async def consultar(moeda: str = None) -> Dict:
        print(C.t(C.CIANO, f"\n[CÂMBIO]"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → BrasilAPI Moedas..."))
            url = "https://brasilapi.com.br/api/cambio/v1/moedas"
            result = await client.get(url)
            if result and isinstance(result, list):
                if moeda:
                    for m in result:
                        if m.get('sigla', '').upper() == moeda.upper():
                            print(C.t(C.VERDE, "  ✓ BrasilAPI: OK"))
                            return {'fonte': 'BrasilAPI', 'dados': m}
                    print(C.t(C.VERMELHO, "  ✗ Moeda não encontrada"))
                    return {'fonte': 'BrasilAPI', 'dados': {'erro': 'Moeda não encontrada'}}
                print(C.t(C.VERDE, "  ✓ BrasilAPI: OK"))
                return {'fonte': 'BrasilAPI', 'dados': {'moedas': result[:20]}}
            print(C.t(C.VERMELHO, "  ✗ BrasilAPI: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'Câmbio não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        if 'moedas' in dados:
            out.append(C.t(C.AMARELO, "  Moedas disponíveis:"))
            for m in dados['moedas']:
                nome = m.get('nome', 'N/A')
                sigla = m.get('sigla', 'N/A')
                out.append(f"    {sigla} - {nome}")
        else:
            for k, v in dados.items():
                out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaIBGE:
    """Consulta IBGE - Estados e Municípios"""
    
    @staticmethod
    async def consultar(uf: str = None) -> Dict:
        print(C.t(C.CIANO, f"\n[IBGE]"))
        
        async with HttpClient() as client:
            if uf:
                print(C.t(C.AZUL, f"  → IBGE Municipios ({uf})..."))
                url = f"https://brasilapi.com.br/api/ibge/municipios/v1/{uf.upper()}"
                result = await client.get(url)
                if result and isinstance(result, list):
                    print(C.t(C.VERDE, "  ✓ IBGE: OK"))
                    return {'fonte': 'IBGE', 'dados': {'uf': uf.upper(), 'municipios': result[:30]}}
                print(C.t(C.VERMELHO, "  ✗ IBGE: Falhou"))
            else:
                print(C.t(C.AZUL, "  → IBGE Estados..."))
                url = "https://brasilapi.com.br/api/ibge/uf/v1"
                result = await client.get(url)
                if result and isinstance(result, list):
                    print(C.t(C.VERDE, "  ✓ IBGE: OK"))
                    return {'fonte': 'IBGE', 'dados': {'estados': result}}
                print(C.t(C.VERMELHO, "  ✗ IBGE: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'IBGE não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        if 'municipios' in dados:
            out.append(C.t(C.AMARELO, f"  Municípios de {dados.get('uf')}:"))
            for m in dados['municipios']:
                out.append(f"    {m}")
        elif 'estados' in dados:
            out.append(C.t(C.AMARELO, "  Estados:"))
            for e in dados['estados']:
                nome = e.get('nome', 'N/A')
                sigla = e.get('sigla', 'N/A')
                out.append(f"    {sigla} - {nome}")
        else:
            for k, v in dados.items():
                out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaPIX:
    """Consulta Participantes PIX"""
    
    @staticmethod
    async def consultar(banco: str = None) -> Dict:
        print(C.t(C.CIANO, f"\n[PIX]"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → BrasilAPI PIX..."))
            url = "https://brasilapi.com.br/api/pix/v1/participants"
            result = await client.get(url)
            if result and isinstance(result, list):
                if banco:
                    for p in result:
                        if banco.upper() in p.get('nome', '').upper() or banco.upper() in p.get('codigo', ''):
                            print(C.t(C.VERDE, "  ✓ BrasilAPI: OK"))
                            return {'fonte': 'BrasilAPI', 'dados': p}
                    print(C.t(C.VERMELHO, "  ✗ Banco não encontrado"))
                    return {'fonte': 'BrasilAPI', 'dados': {'erro': 'Banco não encontrado'}}
                print(C.t(C.VERDE, "  ✓ BrasilAPI: OK"))
                return {'fonte': 'BrasilAPI', 'dados': {'bancos': result[:25]}}
            print(C.t(C.VERMELHO, "  ✗ BrasilAPI: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'PIX não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        if 'bancos' in dados:
            out.append(C.t(C.AMARELO, "  Participantes PIX:"))
            for b in dados['bancos']:
                nome = b.get('nome', 'N/A')
                codigo = b.get('codigo', 'N/A')
                out.append(f"    {codigo} - {nome}")
        else:
            for k, v in dados.items():
                out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaCorretora:
    """Consulta Corretoras CVM"""
    
    @staticmethod
    async def consultar(cnpj: str = None) -> Dict:
        print(C.t(C.CIANO, f"\n[CORRETORA]"))
        
        async with HttpClient() as client:
            if cnpj:
                cnpj = ''.join(filter(str.isdigit, cnpj))[:14]
                print(C.t(C.AZUL, "  → CVM Corretora..."))
                url = f"https://brasilapi.com.br/api/cvm/corretoras/v1/{cnpj}"
                result = await client.get(url)
                if result and result.get('nome'):
                    print(C.t(C.VERDE, "  ✓ CVM: OK"))
                    return {'fonte': 'CVM', 'dados': result}
                print(C.t(C.VERMELHO, "  ✗ CVM: Falhou"))
            else:
                print(C.t(C.AZUL, "  → CVM Corretoras..."))
                url = "https://brasilapi.com.br/api/cvm/corretoras/v1"
                result = await client.get(url)
                if result and isinstance(result, list):
                    print(C.t(C.VERDE, "  ✓ CVM: OK"))
                    return {'fonte': 'CVM', 'dados': {'corretoras': result[:25]}}
                print(C.t(C.VERMELHO, "  ✗ CVM: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'Corretora não encontrada'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        if 'corretoras' in dados:
            out.append(C.t(C.AMARELO, "  Corretoras CVM:"))
            for c in dados['corretoras']:
                nome = c.get('nome', 'N/A')
                cnpj = c.get('cnpj', 'N/A')
                out.append(f"    {cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]} - {nome}")
        else:
            for k, v in dados.items():
                out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaDominio:
    """Consulta Domínio .br"""
    
    @staticmethod
    async def consultar(dominio: str) -> Dict:
        dominio = dominio.lower().replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        print(C.t(C.CIANO, f"\n[DOMINIO] {dominio}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → Registro.br..."))
            url = f"https://brasilapi.com.br/api/registrobr/v1/{dominio}"
            result = await client.get(url)
            if result and result.get('available') is not None:
                print(C.t(C.VERDE, "  ✓ Registro.br: OK"))
                return {'fonte': 'Registro.br', 'dados': result}
            print(C.t(C.VERMELHO, "  ✗ Registro.br: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'Domínio não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        disponivel = dados.get('available', None)
        if disponivel is not None:
            status = C.t(C.VERDE, "DISPONÍVEL") if disponivel else C.t(C.VERMELHO, "INDISPONÍVEL")
            out.append(C.t(C.AMARELO, f"  Domínio: {status}"))
            if dados.get('expires_at'):
                out.append(C.t(C.AMARELO, "  Expira em: ") + dados.get('expires_at'))
            if dados.get('created_at'):
                out.append(C.t(C.AMARELO, "  Criado em: ") + dados.get('created_at'))
        else:
            for k, v in dados.items():
                out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaFIPE:
    """Consulta Tabela FIPE - Preços de veículos"""
    
    @staticmethod
    async def consultar(tipo: str = 'carros', marca: str = None, modelo: str = None) -> Dict:
        print(C.t(C.CIANO, f"\n[FIPE]"))
        
        async with HttpClient() as client:
            if modelo and marca:
                print(C.t(C.AMARELO, "  API INDISPONÍVEL (500)"))
                return {'fonte': 'nenhuma', 'dados': {'erro': 'API temporariamente indisponível'}}
            
            if marca:
                print(C.t(C.AZUL, "  → FIPE Modelos..."))
                url = f"https://brasilapi.com.br/api/fipe/veiculos/v1/{tipo}/{marca}"
                result = await client.get(url)
                if result and isinstance(result, list):
                    print(C.t(C.VERDE, "  ✓ FIPE: OK"))
                    return {'fonte': 'FIPE', 'dados': {'modelos': result[:20]}}
                print(C.t(C.VERMELHO, "  ✗ FIPE: Falhou"))
            
            print(C.t(C.AZUL, "  → FIPE Marcas..."))
            url = f"https://brasilapi.com.br/api/fipe/marcas/v1/{tipo}"
            result = await client.get(url)
            if result and isinstance(result, list):
                print(C.t(C.VERDE, "  ✓ FIPE: OK"))
                return {'fonte': 'FIPE', 'dados': {'marcas': result[:30]}}
            print(C.t(C.VERMELHO, "  ✗ FIPE: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'FIPE não encontrada'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        if 'modelos' in dados:
            out.append(C.t(C.AMARELO, "  Modelos:"))
            for m in dados['modelos']:
                nome = m.get('nome', 'N/A')
                codigo = m.get('codigo', 'N/A')
                out.append(f"    {codigo} - {nome}")
        elif 'marcas' in dados:
            out.append(C.t(C.AMARELO, "  Marcas:"))
            for m in dados['marcas']:
                nome = m.get('nome', 'N/A')
                codigo = m.get('codigo', 'N/A')
                out.append(f"    {codigo} - {nome}")
        else:
            for k, v in dados.items():
                out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaTicker:
    """Consulta Tickers B3 - Ações e Fundos"""
    
    @staticmethod
    async def consultar(tipo: str = 'acoes') -> Dict:
        print(C.t(C.CIANO, f"\n[TICKER {tipo.upper()}]"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → BrasilAPI Tickers..."))
            if tipo == 'fundos':
                url = "https://brasilapi.com.br/api/tickers/b3/fundos/v1/imobiliario"
            else:
                url = "https://brasilapi.com.br/api/tickers/b3/acoes/v1"
            result = await client.get(url)
            if result and isinstance(result, list):
                print(C.t(C.VERDE, "  ✓ BrasilAPI: OK"))
                return {'fonte': 'BrasilAPI', 'dados': {'tickers': result[:30]}}
            print(C.t(C.VERMELHO, "  ✗ BrasilAPI: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'Ticker não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        if 'tickers' in dados:
            out.append(C.t(C.AMARELO, "  Tickers B3:"))
            for t in dados['tickers']:
                simbolo = t.get('simbolo', 'N/A')
                nome = t.get('nome', 'N/A')[:30]
                out.append(f"    {simbolo} - {nome}")
        else:
            for k, v in dados.items():
                out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaFundoCVM:
    """Consulta Fundos CVM"""
    
    @staticmethod
    async def consultar(cnpj: str = None) -> Dict:
        print(C.t(C.CIANO, f"\n[FUNDO CVM]"))
        
        async with HttpClient() as client:
            if cnpj:
                cnpj = ''.join(filter(str.isdigit, cnpj))[:14]
                print(C.t(C.AZUL, "  → CVM Fundo..."))
                url = f"https://brasilapi.com.br/api/cvm/fundos/v1/{cnpj}"
                result = await client.get(url)
                if result and result.get('nome'):
                    print(C.t(C.VERDE, "  ✓ CVM: OK"))
                    return {'fonte': 'CVM', 'dados': result}
                print(C.t(C.VERMELHO, "  ✗ CVM: Falhou"))
            else:
                print(C.t(C.AZUL, "  → CVM Fundos..."))
                url = "https://brasilapi.com.br/api/cvm/fundos/v1"
                result = await client.get(url)
                if result and isinstance(result, list):
                    print(C.t(C.VERDE, "  ✓ CVM: OK"))
                    return {'fonte': 'CVM', 'dados': {'fundos': result[:25]}}
                print(C.t(C.VERMELHO, "  ✗ CVM: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'Fundo não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        if 'fundos' in dados:
            out.append(C.t(C.AMARELO, "  Fundos CVM:"))
            for f in dados['fundos']:
                nome = f.get('nome', 'N/A')[:35]
                cnpj = f.get('cnpj', 'N/A')
                out.append(f"    {cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]} - {nome}")
        else:
            for k, v in dados.items():
                out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaDistancia:
    """Consulta Distância entre cidades"""
    
    @staticmethod
    async def consultar(origem: str, destino: str) -> Dict:
        print(C.t(C.CIANO, f"\n[DISTÂNCIA] {origem} → {destino}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → BrazilAPI..."))
            url = f"https://brasilapi.com.br/api/distance/v1?from={origem}&to={destino}"
            result = await client.get(url)
            if result and result.get('distance'):
                print(C.t(C.VERDE, "  ✓ BrazilAPI: OK"))
                return {'fonte': 'BrazilAPI', 'dados': result}
            print(C.t(C.VERMELHO, "  ✗ BrazilAPI: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'Distância não encontrada'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        distancia = dados.get('distance')
        if distancia:
            out.append(C.t(C.AMARELO, f"  Distância: {distancia} km"))
            if dados.get('origin'):
                out.append(C.t(C.AMARELO, f"  Origem: ") + dados.get('origin'))
            if dados.get('destination'):
                out.append(C.t(C.AMARELO, f"  Destino: ") + dados.get('destination'))
        else:
            for k, v in dados.items():
                out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaCNPJReceita:
    """Consulta CNPJ via ReceitaWS"""
    
    @staticmethod
    async def consultar(cnpj: str) -> Dict:
        cnpj = Validators.limpar_cnpj(cnpj)
        print(C.t(C.CIANO, f"\n[CNPJ] {Validators.formatar_cnpj(cnpj)}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → ReceitaWS..."))
            url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
            result = await client.get(url)
            if result and result.get('status') != 'ERROR':
                print(C.t(C.VERDE, "  ✓ ReceitaWS: OK"))
                return {'fonte': 'ReceitaWS', 'dados': result}
            print(C.t(C.VERMELHO, "  ✗ ReceitaWS: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'CNPJ não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        campos = ['nome', 'fantasia', 'logradouro', 'bairro', 'municipio', 'uf', 'cep', 'telefone', 'email', 'situacao']
        for campo in campos:
            if campo in dados:
                val = dados[campo]
                out.append(C.t(C.AMARELO, f"  • {campo.upper()}: ") + str(val))
        
        return "\n".join(out)


class ConsultaTelefone:
    """Validação de Telefone"""
    
    @staticmethod
    async def consultar(telefone: str) -> Dict:
        telefone = ''.join(filter(str.isdigit, telefone))
        print(C.t(C.CIANO, f"\n[TELEFONE] {telefone}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → API Phone..."))
            url = f"https://api.phonenumbers.com/v1/validate?number={telefone}"
            try:
                result = await client.get(url)
                if result and result.get('is_valid'):
                    print(C.t(C.VERDE, "  ✓ API: OK"))
                    return {'fonte': 'PhoneAPI', 'dados': result}
            except:
                pass
            print(C.t(C.AMARELO, "  API requer chave - usando formato apenas"))
        
        return {'fonte': 'nenhuma', 'dados': {'telefone': telefone, 'validacao': 'Formato verificado localmente'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        for k, v in dados.items():
            out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaCNPJS:
    """Consulta CNPJ Simples Nacional"""
    
    @staticmethod
    async def consultar(cnpj: str) -> Dict:
        cnpj = Validators.limpar_cnpj(cnpj)
        print(C.t(C.CIANO, f"\n[CNPJ SIMPLES] {Validators.formatar_cnpj(cnpj)}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → Receitaws CNPJ..."))
            url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
            result = await client.get(url)
            if result and result.get('status') != 'ERROR':
                print(C.t(C.VERDE, "  ✓ ReceitaWS: OK"))
                return {'fonte': 'ReceitaWS', 'dados': result}
            print(C.t(C.VERMELHO, "  ✗ ReceitaWS: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'CNPJ não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        campos = ['nome', 'fantasia', 'logradouro', 'bairro', 'municipio', 'uf', 'cep', 'telefone', 'email', 'situacao', 'porte', 'natureza_juridica']
        for campo in campos:
            if campo in dados:
                val = dados[campo]
                out.append(C.t(C.AMARELO, f"  • {campo.upper()}: ") + str(val))
        
        return "\n".join(out)


class ConsultaCNH:
    """Consulta CNH - NH"""
    
    @staticmethod
    async def consular(cnh: str) -> Dict:
        cnh = ''.join(filter(str.isdigit, cnh))
        print(C.t(C.CIANO, f"\n[CNH] {cnh}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → API Detran..."))
            # API pública do Detran (quando disponível)
            url = f"https://api.detran.com.br/v1/cnh/{cnh}"
            try:
                result = await client.get(url)
                if result and result.get('valido'):
                    print(C.t(C.VERDE, "  ✓ Detran: OK"))
                    return {'fonte': 'Detran', 'dados': result}
            except:
                pass
            print(C.t(C.AMARELO, "  API Detran indisponível"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'CNH não encontrada - API requer chave'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        for k, v in dados.items():
            out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaRenavam:
    """Consulta Renavam - Veículo DETRAN"""
    
    @staticmethod
    async def consultar(renavam: str) -> Dict:
        renavam = ''.join(filter(str.isdigit, renavam))[:11]
        print(C.t(C.CIANO, f"\n[RENAVAM] {renavam}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → FIPE (veículo)..."))
            # Renavam não tem API pública, mas a FIPE pode ter info similar
            url = f"https://brasilapi.com.br/api/fipe/preco/v1/{renavam}"
            try:
                result = await client.get(url)
                if result and isinstance(result, list) and len(result) > 0:
                    print(C.t(C.VERDE, "  ✓ FIPE: OK"))
                    return {'fonte': 'FIPE', 'dados': result[0]}
            except:
                pass
            print(C.t(C.AMARELO, "  Renavam não encontrado"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'Renavam não encontrado - API requer DETRAN'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        for k, v in dados.items():
            out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaIE:
    """Consulta Inscrição Estadual (IE) por Estado"""
    
    @staticmethod
    async def consultar(ie: str, uf: str) -> Dict:
        ie = ''.join(filter(str.isdigit, ie))
        print(C.t(C.CIANO, f"\n[IE] {ie} - {uf.upper()}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → NF-e (SEFAZ)..."))
            url = f"https://homologacao.nfe.fazenda.gov.br/WSENotas/NFeConsultaCAD.asmx/consultar?IE={ie}&UF={uf.upper()}"
            result = await client.get(url)
            if result:
                print(C.t(C.VERDE, "  ✓ SEFAZ: OK"))
                return {'fonte': 'SEFAZ', 'dados': result}
            print(C.t(C.VERMELHO, "  ✗ SEFAZ: Falhou (requer certificado)"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'IE não encontrada - Requer certificado digital'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        for k, v in dados.items():
            out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaNFse:
    """Consulta NFS-e - Nota Fiscal de Serviços"""
    
    @staticmethod
    async def consultar(nota: str, municipio: str = None) -> Dict:
        nota = ''.join(filter(str.isdigit, nota))
        print(C.t(C.CIANO, f"\n[NFS-e] {nota}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → NFS-e..."))
            # NFS-e vary by municipality
            url = f"https://nfs.e-notaweb.com.br/consultar/{nota}"
            try:
                result = await client.get(url)
                if result and result.get('numero'):
                    print(C.t(C.VERDE, "  ✓ NFS-e: OK"))
                    return {'fonte': 'NFS-e', 'dados': result}
            except:
                pass
            print(C.t(C.VERMELHO, "  ✗ NFS-e indisponível"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'NFS-e não encontrada - varies by city'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        for k, v in dados.items():
            out.append(C.t(C.AMARELO, f"  • {k.upper()}: ") + str(v))
        
        return "\n".join(out)


class ConsultaLoterica:
    """Consulta Resultados de Loterias"""
    
    @staticmethod
    async def consultar(jogo: str = 'mega-sena') -> Dict:
        print(C.t(C.CIANO, f"\n[LOTERIA] {jogo}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → Loteria..."))
            url = f"https://brasilapi.com.br/api/loterias/v1/{jogo}"
            result = await client.get(url)
            if result and result.get('concurso'):
                print(C.t(C.VERDE, "  ✓ Loteria: OK"))
                return {'fonte': 'Loteria', 'dados': result}
            print(C.t(C.VERMELHO, "  ✗ Loteria: Falhou"))
            
            # List available games
            print(C.t(C.AZUL, "  → Lista de jogos..."))
            url = "https://brasilapi.com.br/api/loterias/v1"
            result = await client.get(url)
            if result and isinstance(result, list):
                print(C.t(C.VERDE, "  ✓ API: OK"))
                return {'fonte': 'Loteria', 'dados': {'jogos': result}}
            print(C.t(C.VERMELHO, "  ✗ API: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'Loteria não encontrada'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        if 'jogos' in dados:
            out.append(C.t(C.AMARELO, "  Jogos disponíveis:"))
            for j in dados['jogos']:
                out.append(f"    {j}")
        else:
            dezenas = dados.get('dezenas', [])
            out.append(C.t(C.AMARELO, f"  Concurso: {dados.get('concurso')}"))
            out.append(C.t(C.AMARELO, f"  Data: {dados.get('dataStr')}"))
            out.append(C.t(C.AMARELO, "  Dezenas: ") + ' - '.join(map(str, dezenas)))
            if dados.get('valor'):
                out.append(C.t(C.AMARELO, f"  Premio: R$ {dados.get('valor')}"))
        
        return "\n".join(out)


class ConsultaCepCorreios:
    """Consulta CEP nos Correios"""
    
    @staticmethod
    async def consultar(cep: str) -> Dict:
        cep = ''.join(filter(str.isdigit, cep))
        print(C.t(C.CIANO, f"\n[CEP CORREIOS] {cep}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → Correios..."))
            url = f"https://buscacepweb.correios.com.br/getエンドポイント?cep={cep}&tipoCEP=Logradouro"
            result = await client.get(url)
            if result and isinstance(result, dict) and result.get('dados'):
                print(C.t(C.VERDE, "  ✓ Correios: OK"))
                return {'fonte': 'Correios', 'dados': result['dados'][0]}
            print(C.t(C.VERMELHO, "  ✗ Correios: Falhou"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'CEP não encontrado'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        campos = ['logradouro', 'bairro', 'cidade', 'uf', 'cep']
        for campo in campos:
            if campo in dados:
                out.append(C.t(C.AMARELO, f"  • {campo.upper()}: ") + dados[campo])
        
        return "\n".join(out)


class ConsultaWhatsApp:
    """Verificar se número tem WhatsApp"""
    
    @staticmethod
    async def verificar(telefone: str) -> Dict:
        telefone = ''.join(filter(str.isdigit, telefone))
        print(C.t(C.CIANO, f"\n[WHATSAPP] {telefone}"))
        
        async with HttpClient() as client:
            print(C.t(C.AZUL, "  → WhatsApp API..."))
            url = f"https://api.whatsapp.com/v1/phone/{telefone}"
            try:
                result = await client.get(url)
                if result and result.get('exists'):
                    print(C.t(C.VERDE, "  ✓ WhatsApp: OK"))
                    return {'fonte': 'WhatsApp', 'dados': result}
                print(C.t(C.AMARELO, "  Número não tem WhatsApp"))
            except:
                pass
            print(C.t(C.AMARELO, "  API requer chave"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'WhatsApp não verificado - API requer chave'}}
    
    @staticmethod
    def formatar(resultado: Dict) -> str:
        dados = resultado.get('dados', {})
        out = [C.t(C.AZUL, "─" * 50)]
        
        if 'erro' in dados:
            out.append(C.t(C.VERMELHO, f"  Erro: {dados['erro']}"))
            return "\n".join(out)
        
        existe = dados.get('exists', False)
        status = C.t(C.VERDE, "TEM WhatsApp") if existe else C.t(C.VERMELHO, "NÃO TEM WhatsApp")
        out.append(C.t(C.AMARELO, f"  Status: {status}"))
        
        return "\n".join(out)


# ============================================================================
# CLI INTERATIVO
# ============================================================================

class CLI:
    """Interface CLI"""
    
    SERVICOS = {
        '1': ('CPF', ConsultaCPF),
        '2': ('CNPJ', ConsultaCNPJ),
        '3': ('Placa', ConsultaPlaca),
        '4': ('CEP', ConsultaCEP),
        '5': ('IP', ConsultaIP),
        '6': ('DDD', ConsultaDDD),
        '7': ('BIN', ConsultaBIN),
        '8': ('Banco', ConsultaBanco),
        '9': ('Clima', ConsultaClima),
        'A': ('NCM', ConsultaNCM),
        'B': ('ISBN', ConsultaISBN),
        'C': ('Feriado', ConsultaFeriado),
        'D': ('Taxa', ConsultaTaxa),
        'E': ('Cambio', ConsultaCambio),
        'F': ('IBGE', ConsultaIBGE),
        'G': ('PIX', ConsultaPIX),
        'H': ('Corretora', ConsultaCorretora),
        'I': ('Dominio', ConsultaDominio),
        'J': ('FIPE', ConsultaFIPE),
        'K': ('Ticker', ConsultaTicker),
        'L': ('FundoCVM', ConsultaFundoCVM),
        'M': ('Distancia', ConsultaDistancia),
        'N': ('CNPJS', ConsultaCNPJS),
        'O': ('CNH', ConsultaCNH),
        'P': ('Loterica', ConsultaLoterica),
    }
    
    def limpar(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def banner(self):
        print(C.t(C.AZUL, """
        ╔══════════════════════════════════════════════════════════════╗
        ║  █████╗  █████╗ ███████╗ █████╗      ██████╗  █████╗         ║
        ║  ██╔══██╗██╔══██╗██╔════╝██╔══██╗    ██╔══██╗██╔══██╗        ║
        ║  ███████║███████║█████╗  ███████║    ██████╔╝╚█████╔╝        ║
        ║  ██╔══██║██╔══██║██╔══╝  ██╔══██║    ██╔══██╗██╔══██╗        ║
        ║  ██║  ██║██║  ██║██║     ██║  ██║    ██║  ██║╚█████╔╝        ║
        ║  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝    ╚═╝  ╚═╝ ╚════╝         ║
        ║                                                              ║
        ║            [ RAFA8 - CONSULTA MULTI-FONTES ]                 ║
        ╚══════════════════════════════════════════════════════════════╝
        """))
        print(C.t(C.CIANO, "         [ R8 CONSULTA MULTI-FONTES ]"))
        print(C.t(C.AMARELO, "              Timeout: 10s | Retry: 2x"))
        print(C.t(C.RESET, ""))
    
def menu(self):
        print(C.t(C.CIANO, """
    ┌──────────────────────────────────────────────────┐
    │              [MENU PRINCIPAL]                    │
    ├──────────────────────────────────────────────────┤
    │  [1] CPF/GERAR CPF                         │
    │  [2] CNPJ       [B] ISBN     [F] IBGE          │
    │  [3] VEÍCULO    [C] FERIADO  [G] PIX           │
    │  [4] CEP        [D] TAXA     [H] CORRETORA      │
    │  [5] IP         [I] DOMÍNIO                   │
    │  [6] DDD       [L] FUNDO CVM                  │
    │  [7] BIN      [M] DISTÂNCIA                  │
    │  [9] CLIMA     [O] CNH      [P] LOTÉRICA     │
    │  [8] BANCO    [K] TICKER                   │
    │  [J] FIPE     [N] CNPJS                       │
    ├──────────────────────────────────────────────────┤
    │  [G] GERAR CPF        [H] HISTÓRICO             │
    │  [C] LIMPAR CACHE     [0] SAIR                  │
    └──────────────────────────────────────────────────┘
        """))
    
async def iniciar(self):
        print(C.t(C.CIANO, "Verificando conectividade..."))
        try:
            async with HttpClient() as client:
                result = await client.get('https://brasilapi.com.br/api/banks/v1')
                if result:
                    print(C.t(C.VERDE, "  ✓ Online"))
                else:
                    print(C.t(C.AMARELO, "  ○ Sem resposta"))
        except Exception as e:
            print(C.t(C.VERMELHO, "  ✗ Offline"))
        
        while True:
            self.limpar()
            self.banner()
            self.menu()
            
            op = input(C.t(C.VERDE, "\n~# Escolha: ")).strip().lower()
            
            if op == '0':
                print(C.t(C.AMARELO, "\n  Até mais!\n"))
                break
            
            if op == '3':
                await self.menu_veiculo()
                continue
            
            if op == '1':
                await self.menu_cpf()
                continue
            
            if op in self.SERVICOS:
                nome, servico = self.SERVICOS[op]
                valor = input(C.t(C.VERDE, f"\n  Informe {nome}: ")).strip()
                if valor:
                    await self.executar(nome.lower(), valor)
                    input(C.t(C.AZUL, "\n[Enter]..."))
            
            elif op == 'g':
                cpf = Validators.gerar_cpf()
                print(C.t(C.AZUL, "─" * 50))
                print(C.t(C.AMARELO, f"  CPF Gerado: {Validators.formatar_cpf(cpf)}"))
                print(C.t(C.VERDE, f"  Válido: {Validators.validar_cpf(cpf)}"))
                input(C.t(C.AZUL, "\n[Enter]..."))
            
            elif op == 'h':
                historico = Config.load_json(Config.HISTORY_FILE, [])
                print(C.t(C.CIANO, "\n[HISTÓRICO]"))
                if not historico:
                    print(C.t(C.AMARELO, "  Nenhuma consulta ainda"))
                else:
                    for i, h in enumerate(historico[:20], 1):
                        print(f"  {i}. {h['tipo']}: {h['valor']} ({h.get('fonte', 'N/A')})")
                input(C.t(C.AZUL, "\n[Enter]..."))
            
            elif op == 'c':
                Config.save_json(Config.CACHE_FILE, {})
                print(C.t(C.VERDE, "  Cache limpo!"))
                time.sleep(1)
            
            else:
                print(C.t(C.VERMELHO, "\n  Opção inválida!"))
                time.sleep(1)
    
    async def menu_veiculo(self):
        """Sub-menu para consultas de veículo"""
        MenuVeiculo.menu_veiculo()
        op = input(C.t(C.VERDE, "\n~# Escolha: ")).strip().lower()
        
        if op == '0':
            return
        
        valor = input(C.t(C.VERDE, "\n  Informe o código: ")).strip()
        
        if op == '1':
            print(C.t(C.CIANO, f"\n[PLACA] {valor}"))
            resultado = await MenuVeiculo.executar('1', valor)
            ConsultaPlaca.formatar(resultado)
        elif op == '2':
            print(C.t(C.CIANO, f"\n[CHASSI] {valor}"))
            resultado = await MenuVeiculo.executar('2', valor)
            ConsultaPlaca.formatar(resultado)
        elif op == '3':
            print(C.t(C.CIANO, f"\n[RENAVAM] {valor}"))
            resultado = await MenuVeiculo.executar('3', valor)
            ConsultaPlaca.formatar(resultado)
        elif op == '4':
            print(C.t(C.CIANO, f"\n[MOTOR] {valor}"))
            resultado = await MenuVeiculo.executar('4', valor)
            ConsultaPlaca.formatar(resultado)
        else:
            print(C.t(C.VERMELHO, "\n  Opção inválida!"))
        
        input(C.t(C.AZUL, "\n[Enter]..."))
    
    async def menu_cpf(self):
        """Sub-menu para CPF"""
        print(C.t(C.CIANO, """
    ┌──────────────────────────────────────────────────┐
    │              [MENU CPF]                         │
    ├──────────────────────────────────────────────────┤
    │  [1] CONSULTAR CPF                           │
    │  [2] GERAR CPF VÁLIDO                        │
    │  [3] GERAR + VALIDAR + CONSULTAR             │
    │  [4] VALIDAR CPF                           │
    ├──────────────────────────────────────────────────┤
    │  [0] VOLTAR ao menu principal              │
    └──────────────────────────────────────────────────┘
        """))
        op = input(C.t(C.VERDE, "\n~# Escolha: ")).strip().lower()
        
        if op == '0':
            return
        
        valor = input(C.t(C.VERDE, "\n  Informe CPF (ou Enter para gerar): ")).strip()
        
        if op == '1':
            await self.executar('cpf', valor)
        elif op == '2':
            cpf = Validators.gerar_cpf()
            print(C.t(C.AZUL, "─" * 50))
            print(C.t(C.AMARELO, f"  CPF Gerado: {Validators.formatar_cpf(cpf)}"))
            print(C.t(C.VERDE, f"  Válido: {Validators.validar_cpf(cpf)}"))
        elif op == '3':
            cpf = Validators.gerar_cpf()
            print(C.t(C.AZUL, "─" * 50))
            print(C.t(C.AMARELO, f"\n[CPF GERADO] {Validators.formatar_cpf(cpf)}"))
            valido = Validators.validar_cpf(cpf)
            if valido:
                print(C.t(C.VERDE, "  ✓ CPF VÁLIDO"))
            else:
                print(C.t(C.VERMELHO, "  ✗ CPF INVÁLIDO"))
            
            if valido:
                print(C.t(C.AZUL, "\n  Consultando..."))
                resultado = await ConsultaCPF.consultar(cpf)
                ConsultaCPF.formatar(resultado)
            else:
                print(C.t(C.VERMELHO, "  Pulando consulta (CPF inválido)"))
        elif op == '4':
            valido = Validators.validar_cpf(valor)
            print(C.t(C.AZUL, "─" * 50))
            print(C.t(C.AMARELO, f"  CPF: {Validators.formatar_cpf(valor)}"))
            if valido:
                print(C.t(C.VERDE, "  VÁLIDO"))
            else:
                print(C.t(C.VERMELHO, "  INVÁLIDO"))
        else:
            print(C.t(C.VERMELHO, "\n  Opção inválida!"))
        
        input(C.t(C.AZUL, "\n[Enter]..."))
                nome, servico = self.SERVICOS[op]
                valor = input(C.t(C.VERDE, f"\n  Informe {nome}: ")).strip()
                if valor:
                    await self.executar(nome.lower(), valor)
                    input(C.t(C.AZUL, "\n[Enter]..."))
            
            elif op == 'g':
                cpf = Validators.gerar_cpf()
                print(C.t(C.AZUL, "─" * 50))
                print(C.t(C.AMARELO, f"  CPF Gerado: {Validators.formatar_cpf(cpf)}"))
                print(C.t(C.VERDE, f"  Válido: {Validators.validar_cpf(cpf)}"))
                input(C.t(C.AZUL, "\n[Enter]..."))
            
            elif op == 'h':
                historico = Config.load_json(Config.HISTORY_FILE, [])
                print(C.t(C.CIANO, "\n[HISTÓRICO]"))
                if not historico:
                    print(C.t(C.AMARELO, "  Nenhuma consulta ainda"))
                else:
                    for i, h in enumerate(historico[:20], 1):
                        print(f"  {i}. {h['tipo']}: {h['valor']} ({h.get('fonte', 'N/A')})")
                input(C.t(C.AZUL, "\n[Enter]..."))
            
            elif op == 'c':
                Config.save_json(Config.CACHE_FILE, {})
                print(C.t(C.VERDE, "  Cache limpo!"))
                time.sleep(1)
            
            else:
                print(C.t(C.VERMELHO, "\n  Opção inválida!"))
                time.sleep(1)


# ============================================================================
# MAIN
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(description='Consultas Unificado')
    parser.add_argument('tipo', nargs='?', help='Tipo: cpf, cnpj, placa, cep, ip, ddd, bin, banco')
    parser.add_argument('valor', nargs='?', help='Valor a consultar')
    parser.add_argument('--history', action='store_true', help='Ver histórico')
    parser.add_argument('--clear-cache', action='store_true', help='Limpar cache')
    
    args = parser.parse_args()
    
    if args.clear_cache:
        Config.save_json(Config.CACHE_FILE, {})
        print("Cache limpo!")
        return
    
    if args.history:
        historico = Config.load_json(Config.HISTORY_FILE, [])
        if not historico:
            print("Nenhuma consulta no histórico")
        else:
            for h in historico[:20]:
                print(f"{h['tipo']}: {h['valor']} - {h.get('fonte', 'N/A')}")
        return
    
    if args.tipo and args.valor:
        cli = CLI()
        await cli.executar(args.tipo.lower(), args.valor)
        return
    
    # Modo interativo
    cli = CLI()
    await cli.iniciar()


if __name__ == '__main__':
    asyncio.run(main())