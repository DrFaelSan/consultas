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
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=Config.TIMEOUT),
            connector=aiohttp.TCPConnector(limit=10)
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
                        return await resp.json()
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
                return {'fonte': 'BrazilAPI', 'dados': result}
            
            # ReceitaWS
            print(C.t(C.AZUL, "  → ReceitaWS..."))
            url = f"https://www.receitaws.com.br/v1/cpf/{cpf}"
            result = await client.get(url)
            if result and result.get('status') != 'ERROR':
                return {'fonte': 'ReceitaWS', 'dados': result}
            
            # RapidAPI (alternativa)
            print(C.t(C.AZUL, "  → RapidAPI..."))
            url = f"https://consulta-cpf2.p.rapidapi.com/apis/astrahvhdeus/Consultas%20Privadas/HTML/cpf.php?consulta={cpf}"
            headers = {
                'x-rapidapi-key': Config.RAPIDAPI_KEY,
                'x-rapidapi-host': 'consulta-cpf2.p.rapidapi.com'
            }
            result = await client.get(url, headers=headers)
            if result and 'A Consulta Esta Funcionando Normally' not in str(result):
                return {'fonte': 'RapidAPI', 'dados': result}
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'CPF não encontrado em nenhuma fonte'}}
    
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
    """Consulta CNPJ - 2+ fontes (suporta formato alfanumérico 2026+)"""
    
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
                return {'fonte': 'BrasilAPI', 'dados': result}
            
            # ReceitaWS
            print(C.t(C.AZUL, "  → ReceitaWS..."))
            url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
            result = await client.get(url)
            if result and result.get('status') != 'ERROR':
                return {'fonte': 'ReceitaWS', 'dados': result}
            
            # BrazilAPI
            print(C.t(C.AZUL, "  → BrazilAPI..."))
            url = f"https://api.brazilapi.com.br/cnpj/v1/{cnpj}"
            result = await client.get(url)
            if result and 'error' not in result:
                return {'fonte': 'BrazilAPI', 'dados': result}
        
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
    """Consulta Placa - 3 fontes (ApiCarros, PlacaFipy, FIPE)"""
    
    @staticmethod
    async def consultar(placa: str) -> Dict:
        placa = Validators.limpar_placa(placa)
        print(C.t(C.CIANO, f"\n[PLACA] {Validators.formatar_placa(placa)}"))
        
        async with HttpClient() as client:
            # ApiCarros
            print(C.t(C.AZUL, "  → ApiCarros..."))
            try:
                url = f'https://apicarros.com/v1/consulta/{placa}'
                result = await client.get(url)
                if result:
                    return {'fonte': 'ApiCarros', 'dados': result}
            except Exception as e:
                print(C.t(C.AMARELO, f"  ApiCarros: {str(e)[:40]}"))
            
            # PlacaFipy
            print(C.t(C.AZUL, "  → PlacaFipy..."))
            try:
                url = f'https://placafipy.com/api/consulta/{placa}'
                result = await client.get(url)
                if result:
                    return {'fonte': 'PlacaFipy', 'dados': result}
            except Exception as e:
                print(C.t(C.AMARELO, f"  PlacaFipy: {str(e)[:40]}"))
            
            # FIPE API
            print(C.t(C.AZUL, "  → FIPE..."))
            try:
                url = f'https://api.fipe.com.br/api/v1/carros/marcas'
                result = await client.get(url, timeout=5)
                if result:
                    return {'fonte': 'FIPE', 'dados': {'info': 'Consulte via app FIPE'}}
            except Exception as e:
                print(C.t(C.AMARELO, f"  FIPE: {str(e)[:40]}"))
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'Placa não encontrada'}}
    
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
            url = f'https://lookup.binlist.net/{bin_code}'
            result = await client.get(url)
            if result:
                return {'fonte': 'BinList', 'dados': result}
        
        return {'fonte': 'nenhuma', 'dados': {'erro': 'BIN não encontrado'}}
    
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
    │  [1] CPF                                         │
    │  [2] CNPJ                                        │
    │  [3] PLACA                                      │
    │  [4] CEP                                        │
    │  [5] IP                                         │
    │  [6] DDD                                        │
    │  [7] BIN                                        │
    │  [8] BANCO                                      │
    ├──────────────────────────────────────────────────┤
    │  [G] GERAR CPF        [H] HISTÓRICO             │
    │  [C] LIMPAR CACHE     [0] SAIR                  │
    └──────────────────────────────────────────────────┘
        """))
    
    async def health_check(self):
        """Verifica conectividade das APIs"""
        print(C.t(C.CIANO, "\n  Verificando conectividade..."))
        
        apis = [
            ('BrasilAPI', 'https://brasilapi.com.br/api/banks/v1'),
            ('ViaCEP', 'https://viacep.com.br/ws/01001000/json/'),
            ('IP-API', 'http://ip-api.com/json/8.8.8.8'),
        ]
        
        async with HttpClient() as client:
            for nome, url in apis:
                try:
                    result = await client.get(url, timeout=3)
                    if result:
                        print(C.t(C.VERDE, f"  ✓ {nome}: ONLINE"))
                    else:
                        print(C.t(C.AMARELO, f"  ○ {nome}: SEM RESPOSTA"))
                except Exception as e:
                    print(C.t(C.VERMELHO, f"  ✗ {nome}: OFFLINE"))
        
        print(C.t(C.RESET, ""))
    
    async def executar(self, tipo: str, valor: str):
        servicos = {
            'cpf': ConsultaCPF, 'cnpj': ConsultaCNPJ, 'placa': ConsultaPlaca,
            'cep': ConsultaCEP, 'ip': ConsultaIP, 'ddd': ConsultaDDD,
            'bin': ConsultaBIN, 'banco': ConsultaBanco
        }
        
        if tipo.lower() not in servicos:
            print(C.t(C.VERMELHO, f"  Tipo '{tipo}' não reconhecido"))
            return
        
        servico = servicos[tipo.lower()]
        resultado = await servico.consultar(valor)
        print(servico.formatar(resultado))
        
        # Salvar no histórico
        historico = Config.load_json(Config.HISTORY_FILE, [])
        historico.insert(0, {
            'tipo': tipo.upper(),
            'valor': valor,
            'fonte': resultado.get('fonte'),
            'timestamp': datetime.now().isoformat()
        })
        if len(historico) > 100:
            historico = historico[:100]
        Config.save_json(Config.HISTORY_FILE, historico)
    
    async def iniciar(self):
        await self.health_check()
        while True:
            self.limpar()
            self.banner()
            self.menu()
            
            op = input(C.t(C.VERDE, "\n~# Escolha: ")).strip().lower()
            
            if op == '0':
                print(C.t(C.AMARELO, "\n  Até mais!\n"))
                break
            
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