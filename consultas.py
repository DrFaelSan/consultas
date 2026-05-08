#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Unificado de Consultas - Versão Completa
Agrega múltiplos endpoints por tipo de dado com fallback automático
Autor: Baseado nas referências do projeto
"""

import os
import sys
import time
import json
import csv
import hashlib
import argparse
import requests
import subprocess
import socket
import atexit
import uuid
import shutil
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from urllib.parse import urlparse
from functools import lru_cache

# ============================================================================
# CONFIGURAÇÕES E VARIÁVEIS DE AMBIENTE
# ============================================================================

class Config:
    """Configurações via variáveis de ambiente"""
    
    # API Keys (configure via variáveis de ambiente)
    RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', 'e01238c690msh74f20bdc84d5dcfp122562jsnc9921fa7c4c1')
    IPGEOLOCATION_KEY = os.environ.get('IPGEOLOCATION_KEY', '9313e7887bad45cea6d4b5845f085464')
    IPFIND_KEY = os.environ.get('IPFIND_KEY', '22e75f18-7853-4227-ac49-3a8a72893210')
    
    # Configurações
    CACHE_ENABLED = os.environ.get('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_TTL = int(os.environ.get('CACHE_TTL', '3600'))  # 1 hora
    HISTORY_ENABLED = os.environ.get('HISTORY_ENABLED', 'true').lower() == 'true'
    TOR_ENABLED = os.environ.get('TOR_ENABLED', 'false').lower() == 'true'
    
    # Arquivos
    CACHE_FILE = os.environ.get('CACHE_FILE', 'cache.json')
    HISTORY_FILE = os.environ.get('HISTORY_FILE', 'historico.json')
    
    @staticmethod
    def carregar_cache() -> Dict:
        """Carrega cache do arquivo"""
        if os.path.exists(Config.CACHE_FILE):
            try:
                with open(Config.CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    @staticmethod
    def salvar_cache(cache: Dict):
        """Salva cache no arquivo"""
        if Config.CACHE_ENABLED:
            try:
                with open(Config.CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cache, f, indent=2, ensure_ascii=False)
            except:
                pass
    
    @staticmethod
    def carregar_historico() -> List:
        """Carrega histórico do arquivo"""
        if os.path.exists(Config.HISTORY_FILE):
            try:
                with open(Config.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    @staticmethod
    def salvar_historico(historico: List):
        """Salva histórico no arquivo"""
        if Config.HISTORY_ENABLED:
            try:
                with open(Config.HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump(historico, f, indent=2, ensure_ascii=False)
            except:
                pass


# ============================================================================
# CORES PARA OUTPUT
# ============================================================================

class Cores:
    """Cores para output formatado"""
    VERMELHO = '\033[31m'
    VERDE = '\033[32m'
    AMARELO = '\033[33m'
    AZUL = '\033[34m'
    CIANO = '\033[36m'
    BRANCO = '\033[37m'
    NEGRITO = '\033[1m'
    RESET = '\033[0m'
    
    @staticmethod
    def texto(cor, texto):
        return f"{cor}{texto}{Cores.RESET}"


# ============================================================================
# GERENCIADOR DE TOR
# ============================================================================

tor_process = None
SESSION = None
TOR_STARTED_BY_ME = False

def is_tor_running(host="127.0.0.1", port=9050, timeout=1):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass

def start_tor(wait_seconds=10):
    try:
        p = subprocess.Popen(['tor'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(wait_seconds)
        return p
    except:
        return None

def init_tor_and_session(auto_start=True):
    global tor_process, SESSION, TOR_STARTED_BY_ME
    
    if SESSION is not None:
        return SESSION, TOR_STARTED_BY_ME
        
    if not is_tor_running():
        if auto_start and Config.TOR_ENABLED:
            tor_process = start_tor()
            if tor_process is None:
                SESSION = requests.Session()
                TOR_STARTED_BY_ME = False
                return SESSION, TOR_STARTED_BY_ME
            else:
                for _ in range(10):
                    if is_tor_running():
                        break
                    time.sleep(1)
                TOR_STARTED_BY_ME = True
        SESSION = requests.Session()
        TOR_STARTED_BY_ME = False
        return SESSION, TOR_STARTED_BY_ME
    
    TOR_STARTED_BY_ME = False
    SESSION = requests.Session()
    SESSION.proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    return SESSION, TOR_STARTED_BY_ME

def _cleanup_tor_on_exit():
    global tor_process, TOR_STARTED_BY_ME
    if TOR_STARTED_BY_ME and tor_process:
        try:
            tor_process.terminate()
            tor_process.wait(timeout=5)
        except:
            try:
                tor_process.kill()
            except:
                pass

atexit.register(_cleanup_tor_on_exit)


# ============================================================================
# VALIDADORES E GERADORES LOCAIS
# ============================================================================

class Validators:
    """Validadores e geradores de dados brasileiros"""
    
    @staticmethod
    def gerar_cpf() -> str:
        """Gera CPF válido aleatório"""
        import random
        while True:
            nums = [random.randint(0, 9) for _ in range(9)]
            
            soma = sum(nums[i] * (10 - i) for i in range(9))
            digito1 = (soma * 10 % 11) % 10
            
            nums.append(digito1)
            soma = sum(nums[i] * (11 - i) for i in range(10))
            digito2 = (soma * 10 % 11) % 10
            
            cpf = ''.join(map(str, nums)) + str(digito2)
            if cpf != cpf[0] * 11:
                return cpf
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        cpf = ''.join(filter(str.isdigit, cpf))
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        soma = 0
        for i in range(9):
            soma += int(cpf[i]) * (10 - i)
        digito1 = (soma * 10 % 11) % 10
        
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10 % 11) % 10
        
        return cpf[9] == str(digito1) and cpf[10] == str(digito2)
    
    @staticmethod
    def gerar_cnpj() -> str:
        """Gera CNPJ válido aleatório"""
        import random
        nums = [random.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
        
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(nums[i] * pesos1[i] for i in range(12))
        digito1 = soma % 11 if soma % 11 < 2 else 11 - soma % 11
        nums.append(digito1)
        
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(nums[i] * pesos2[i] for i in range(13))
        digito2 = soma % 11 if soma % 11 < 2 else 11 - soma % 11
        nums.append(digito2)
        
        return ''.join(map(str, nums))
    
    @staticmethod
    def validar_cnpj(cnpj: str) -> bool:
        cnpj = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj) != 14:
            return False
        return True
    
    @staticmethod
    def validar_cep(cep: str) -> bool:
        cep = ''.join(filter(str.isdigit, cep))
        return len(cep) == 8
    
    @staticmethod
    def formatar_cpf(cpf: str) -> str:
        cpf = ''.join(filter(str.isdigit, cpf))
        if len(cpf) == 11:
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return cpf
    
    @staticmethod
    def formatar_cnpj(cnpj: str) -> str:
        cnpj = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj) == 14:
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        return cnpj
    
    @staticmethod
    def formatar_cep(cep: str) -> str:
        cep = ''.join(filter(str.isdigit, cep))
        if len(cep) == 8:
            return f"{cep[:5]}-{cep[5:]}"
        return cep


# ============================================================================
# CACHE DE RESULTADOS
# ============================================================================

class Cache:
    """Sistema de cache para resultados"""
    
    def __init__(self):
        self.cache = Config.carregar_cache()
    
    def _gerar_chave(self, tipo: str, entrada: str) -> str:
        return hashlib.md5(f"{tipo}:{entrada}".encode()).hexdigest()
    
    def obter(self, tipo: str, entrada: str) -> Optional[Dict]:
        if not Config.CACHE_ENABLED:
            return None
        
        chave = self._gerar_chave(tipo, entrada)
        if chave in self.cache:
            dados = self.cache[chave]
            timestamp = dados.get('timestamp', 0)
            if time.time() - timestamp < Config.CACHE_TTL:
                return dados.get('resultado')
            else:
                del self.cache[chave]
                Config.salvar_cache(self.cache)
        return None
    
    def salvar(self, tipo: str, entrada: str, resultado: Dict):
        if not Config.CACHE_ENABLED:
            return
        
        chave = self._gerar_chave(tipo, entrada)
        self.cache[chave] = {
            'tipo': tipo,
            'entrada': entrada,
            'resultado': resultado,
            'timestamp': time.time()
        }
        Config.salvar_cache(self.cache)
    
    def limpar(self):
        self.cache = {}
        Config.salvar_cache(self.cache)


# ============================================================================
# HISTÓRICO DE CONSULTAS
# ============================================================================

class Historico:
    """Sistema de histórico de consultas"""
    
    def __init__(self):
        self.historico = Config.carregar_historico()
    
    def adicionar(self, tipo: str, entrada: str, resultado: Dict, sucesso: bool):
        if not Config.HISTORY_ENABLED:
            return
        
        self.historico.insert(0, {
            'id': str(uuid.uuid4())[:8],
            'tipo': tipo,
            'entrada': entrada,
            'resultado': resultado,
            'sucesso': sucesso,
            'timestamp': datetime.now().isoformat(),
            'fonte': resultado.get('fonte', 'desconhecida') if resultado else None
        })
        
        if len(self.historico) > 1000:
            self.historico = self.historico[:1000]
        
        Config.salvar_historico(self.historico)
    
    def listar(self, limite: int = 20) -> List:
        return self.historico[:limite]
    
    def buscar(self, termo: str) -> List:
        return [h for h in self.historico if termo.lower() in str(h).lower()]
    
    def limpar(self):
        self.historico = []
        Config.salvar_historico(self.historico)


# ============================================================================
# EXPORTAÇÃO DE RESULTADOS
# ============================================================================

class Exportador:
    """Exporta resultados para diferentes formatos"""
    
    @staticmethod
    def para_json(dados: Dict, arquivo: str = None) -> str:
        json_str = json.dumps(dados, indent=2, ensure_ascii=False)
        if arquivo:
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(json_str)
        return json_str
    
    @staticmethod
    def para_txt(dados: Dict, arquivo: str = None) -> str:
        linhas = ["=" * 50, f"RESULTADO DA CONSULTA", "=" * 50, ""]
        
        if isinstance(dados, dict):
            for chave, valor in dados.items():
                if isinstance(valor, (dict, list)):
                    linhas.append(f"{chave.upper()}:")
                    linhas.append(f"  {json.dumps(valor, ensure_ascii=False)}")
                else:
                    linhas.append(f"{chave.upper()}: {valor}")
        
        txt = "\n".join(linhas)
        if arquivo:
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(txt)
        return txt
    
    @staticmethod
    def para_csv(dados: Dict, arquivo: str = None) -> str:
        linhas = []
        
        if isinstance(dados, dict):
            linhas.append("campo,valor")
            for chave, valor in dados.items():
                if not isinstance(valor, (dict, list)):
                    linhas.append(f'"{chave}","{valor}"')
        
        csv_str = "\n".join(linhas)
        if arquivo:
            with open(arquivo, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_str)
        return csv_str


# ============================================================================
# CLASSE BASE DE SERVIÇO
# ============================================================================

class ConsultaService:
    """Classe base para todos os serviços de consulta"""
    
    def __init__(self, nome: str):
        self.nome = nome
        self.ultima_requisicao = 0
        self.requisicoes_count = 0
        self.fonte_atual = None
        self.cache = Cache()
        self.historico = Historico()
        
    def rate_limit(self, delay: float = 1.0):
        tempo_decorrido = time.time() - self.ultima_requisicao
        if tempo_decorrido < delay:
            time.sleep(delay - tempo_decorrido)
        self.ultima_requisicao = time.time()
        
    def fazer_requisicao(self, url: str, method: str = 'GET', 
                         headers: Dict = None, params: Dict = None,
                         timeout: int = 30, proxy: Dict = None) -> Optional[Dict]:
        try:
            session = requests.Session()
            if proxy:
                session.proxies = proxy
            
            if method.upper() == 'GET':
                response = session.get(url, headers=headers, params=params, timeout=timeout)
            else:
                response = session.post(url, headers=headers, json=params, timeout=timeout)
            
            response.raise_for_status()
            self.fonte_atual = urlparse(url).netloc
            return response.json() if response.headers.get('content-type', '').find('json') >= 0 else response.text
            
        except Exception as e:
            return None
    
    def tentar_fontes(self, fontes: List[Dict], entrada: str, 
                       extractor: callable) -> Optional[Dict]:
        for fonte in fontes:
            nome_fonte = fonte.get('nome', 'desconhecida')
            print(Cores.texto(Cores.AZUL, f"  → Tentando {nome_fonte}..."))
            
            self.rate_limit(fonte.get('delay', 1.0))
            resultado = extractor(fonte, entrada)
            
            if resultado:
                self.fonte_atual = nome_fonte
                print(Cores.texto(Cores.VERDE, f"  ✓ Sucesso via {nome_fonte}"))
                return resultado
        
        print(Cores.texto(Cores.VERMELHO, f"  ✗ Nenhuma fonte disponível"))
        return None


# ============================================================================
# SERVIÇOS DE CONSULTA
# ============================================================================

class ConsultaCPF(ConsultaService):
    def __init__(self):
        super().__init__("CPF")
        self.fontes = [
            {
                'nome': 'Onion (EduxPanel)',
                'url': 'http://pevbdnjjibvsldgavub3opda2m7g36zc5zuaxbillw52jjjqoehghpyd.onion/cpf.php',
                'params': {'token': 'abc', 'cpf': None},
                'delay': 2.0,
                'tipo': 'onion'
            },
            {
                'nome': 'BrazilAPI (nova)',
                'url': 'https://api.brazilapi.com.br/cpf/v1/',
                'delay': 1.0,
                'tipo': 'http'
            },
            {
                'nome': 'RandomAPI',
                'url': 'https://random-data-api.com/api/cpf/random_cpf',
                'delay': 0.5,
                'tipo': 'http'
            },
            {
                'nome': 'RapidAPI (FullP)',
                'url': 'https://consulta-cpf2.p.rapidapi.com/apis/astrahvhdeus/Consultas%20Privadas/HTML/cpf.php',
                'headers': {'x-rapidapi-key': Config.RAPIDAPI_KEY, 'x-rapidapi-host': 'consulta-cpf2.p.rapidapi.com'},
                'params': {'consulta': None},
                'delay': 1.5,
                'tipo': 'http'
            }
        ]
    
    def consultar(self, cpf: str) -> Optional[Dict]:
        cpf = ''.join(filter(str.isdigit, cpf))
        print(Cores.texto(Cores.CIANO, f"\n[CONSULTA CPF] {cpf}"))
        
        # Verifica cache
        cached = self.cache.obter('cpf', cpf)
        if cached:
            print(Cores.texto(Cores.AMARELO, "  ✓ Retornando do cache"))
            return cached
        
        def extractor(fonte, entrada):
            try:
                if fonte['tipo'] == 'onion':
                    session, _ = init_tor_and_session(auto_start=True)
                    if session:
                        params = fonte['params'].copy()
                        params['cpf'] = entrada
                        response = session.get(fonte['url'], params=params, timeout=30)
                        if response.status_code == 200:
                            data = response.json()
                            if data and len(data) > 0:
                                return {'fonte': 'onion', 'dados': data[0]}
                elif 'brazilapi' in fonte['nome'].lower():
                    url = fonte['url'] + entrada
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        return {'fonte': 'brazilapi', 'dados': response.json()}
                elif 'random' in fonte['nome'].lower():
                    response = requests.get(fonte['url'], timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        return {'fonte': 'random', 'dados': data}
                else:
                    params = fonte.get('params', {}).copy()
                    params['consulta'] = entrada
                    response = requests.get(fonte['url'], headers=fonte.get('headers', {}), params=params, timeout=15)
                    if response.status_code == 200:
                        texto = response.text
                        if 'A Consulta Esta Funcionando Normally' not in texto:
                            return {'fonte': 'rapidapi', 'dados': {'raw': texto}}
            except:
                pass
            return None
        
        resultado = self.tentar_fontes(self.fontes, cpf, extractor)
        
        if resultado:
            self.cache.salvar('cpf', cpf, resultado)
            self.historico.adicionar('CPF', cpf, resultado, True)
        else:
            self.historico.adicionar('CPF', cpf, {}, False)
        
        return resultado
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        
        dados = resultado.get('dados', {})
        output = [Cores.texto(Cores.AZUL, "─" * 50)]
        
        if isinstance(dados, dict):
            for chave, valor in dados.items():
                if chave != 'raw':
                    output.append(Cores.texto(Cores.AMARELO, f"  • {chave.upper()}: ") + str(valor))
        else:
            output.append(Cores.texto(Cores.VERDE, str(dados)))
        
        return "\n".join(output)


class ConsultaCNPJ(ConsultaService):
    def __init__(self):
        super().__init__("CNPJ")
        self.fontes = [
            {'nome': 'BrasilAPI (EduxPanel)', 'url': 'https://brasilapi.com.br/api/cnpj/v1/', 'delay': 1.0},
            {'nome': 'ReceitaWS', 'url': 'https://www.receitaws.com.br/v1/cnpj/', 'delay': 2.0},
            {'nome': 'BrazilAPI', 'url': 'https://api.brazilapi.com.br/cnpj/v1/', 'delay': 1.5},
            {'nome': 'CompanySDK', 'url': 'https://api.companysdk.com/v3/cnpj/', 'delay': 1.0},
        ]
    
    def consultar(self, cnpj: str) -> Optional[Dict]:
        cnpj = ''.join(filter(str.isdigit, cnpj))
        print(Cores.texto(Cores.CIANO, f"\n[CONSULTA CNPJ] {cnpj}"))
        
        cached = self.cache.obter('cnpj', cnpj)
        if cached:
            print(Cores.texto(Cores.AMARELO, "  ✓ Retornando do cache"))
            return cached
        
        def extractor(fonte, entrada):
            try:
                url = fonte['url'] + entrada
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and data.get('status') != 'ERROR':
                        return {'fonte': fonte['nome'], 'dados': data}
            except:
                pass
            return None
        
        resultado = self.tentar_fontes(self.fontes, cnpj, extractor)
        
        if resultado:
            self.cache.salvar('cnpj', cnpj, resultado)
            self.historico.adicionar('CNPJ', cnpj, resultado, True)
        else:
            self.historico.adicionar('CNPJ', cnpj, {}, False)
        
        return resultado
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        
        dados = resultado.get('dados', {})
        output = [Cores.texto(Cores.AZUL, "─" * 50)]
        
        campos = ['nome', 'fantasia', 'cnpj', 'abertura', 'situacao', 'logradouro', 'bairro', 'municipio', 'uf', 'cep', 'telefone', 'email', 'porte', 'natureza_juridica', 'capital_social']
        
        for campo in campos:
            if campo in dados:
                valor = dados[campo]
                if campo == 'capital_social':
                    valor = f"R$ {valor}"
                output.append(Cores.texto(Cores.AMARELO, f"  • {campo.upper()}: ") + str(valor))
        
        return "\n".join(output)


class ConsultaCEP(ConsultaService):
    def __init__(self):
        super().__init__("CEP")
        self.fontes = [
            {'nome': 'ViaCEP', 'url': 'https://viacep.com.br/ws/', 'delay': 0.5},
            {'nome': 'Postmon', 'url': 'https://api.postmon.com.br/v1/cep/', 'delay': 1.0},
            {'nome': 'ApiCEP', 'url': 'https://ws.apicep.com/cep/', 'delay': 0.5},
            {'nome': 'BrazilCEP', 'url': 'https://api.brazilapi.com.br/cep/v1/', 'delay': 1.0},
        ]
    
    def consultar(self, cep: str) -> Optional[Dict]:
        cep = ''.join(filter(str.isdigit, cep))
        print(Cores.texto(Cores.CIANO, f"\n[CONSULTA CEP] {cep}"))
        
        cached = self.cache.obter('cep', cep)
        if cached:
            print(Cores.texto(Cores.AMARELO, "  ✓ Retornando do cache"))
            return cached
        
        def extractor(fonte, entrada):
            try:
                if 'viacep' in fonte['nome'].lower():
                    url = f"{fonte['url']}{entrada}/json"
                elif 'apicep' in fonte['nome'].lower():
                    url = f"{fonte['url']}{entrada}.json"
                elif 'brazil' in fonte['nome'].lower():
                    url = f"{fonte['url']}{entrada}"
                else:
                    url = fonte['url'] + entrada
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'erro' not in data:
                        return {'fonte': fonte['nome'], 'dados': data}
            except:
                pass
            return None
        
        resultado = self.tentar_fontes(self.fontes, cep, extractor)
        
        if resultado:
            self.cache.salvar('cep', cep, resultado)
            self.historico.adicionar('CEP', cep, resultado, True)
        
        return resultado
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        
        dados = resultado.get('dados', {})
        output = [Cores.texto(Cores.AZUL, "─" * 50)]
        
        for chave, valor in dados.items():
            if chave != 'erro':
                output.append(Cores.texto(Cores.AMARELO, f"  • {chave.upper()}: ") + str(valor))
        
        return "\n".join(output)


class ConsultaIP(ConsultaService):
    def __init__(self):
        super().__init__("IP")
        self.fontes = [
            {'nome': 'IP-API', 'url': 'http://ip-api.com/json/', 'delay': 0.5},
            {'nome': 'IPGeolocation', 'url': 'https://api.ipgeolocation.io/ipgeo', 'params': {'apiKey': Config.IPGEOLOCATION_KEY}, 'delay': 1.0},
            {'nome': 'IPFind', 'url': 'https://api.ipfind.com/', 'params': {'auth': Config.IPFIND_KEY}, 'delay': 1.0},
            {'nome': 'IPWhois', 'url': 'https://ipwhois.app/json/', 'delay': 1.0},
            {'nome': 'IPInfo', 'url': 'https://ipinfo.io/', 'params': {'json': ''}, 'delay': 0.5},
        ]
    
    def consultar(self, ip: str) -> Optional[Dict]:
        print(Cores.texto(Cores.CIANO, f"\n[CONSULTA IP] {ip}"))
        
        cached = self.cache.obter('ip', ip)
        if cached:
            print(Cores.texto(Cores.AMARELO, "  ✓ Retornando do cache"))
            return cached
        
        def extractor(fonte, entrada):
            try:
                if 'ipfind' in fonte['nome'].lower():
                    url = f"{fonte['url']}?ip={entrada}&auth={fonte['params']['auth']}"
                elif 'ipgeolocation' in fonte['nome'].lower():
                    url = f"{fonte['url']}?apiKey={fonte['params']['apiKey']}&ip={entrada}"
                elif 'ipinfo' in fonte['nome'].lower():
                    url = f"{fonte['url']}{entrada}/json"
                else:
                    url = fonte['url'] + entrada
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'status' not in data or data['status'] == 'success':
                        return {'fonte': fonte['nome'], 'dados': data}
            except:
                pass
            return None
        
        resultado = self.tentar_fontes(self.fontes, ip, extractor)
        
        if resultado:
            self.cache.salvar('ip', ip, resultado)
            self.historico.adicionar('IP', ip, resultado, True)
        
        return resultado
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        
        dados = resultado.get('dados', {})
        output = [Cores.texto(Cores.AZUL, "─" * 50)]
        
        for chave, valor in dados.items():
            output.append(Cores.texto(Cores.AMARELO, f"  • {chave.upper()}: ") + str(valor))
        
        return "\n".join(output)


class ConsultaTelefone(ConsultaService):
    def __init__(self):
        super().__init__("Telefone")
    
    def consultar(self, telefone: str) -> Optional[Dict]:
        telefone = ''.join(filter(str.isdigit, telefone))
        print(Cores.texto(Cores.CIANO, f"\n[CONSULTA TELEFONE] {telefone}"))
        
        try:
            url = f'https://dualityapi.xyz/apis/flex_7/Consultas%20Privadas/HTML/numero.php?consulta={telefone}'
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                texto = response.text
                if 'A Consulta Esta Funcionando Normally' not in texto:
                    resultado = {'fonte': 'dualityapi', 'dados': {'raw': texto}}
                    self.historico.adicionar('Telefone', telefone, resultado, True)
                    return resultado
        except Exception as e:
            print(Cores.texto(Cores.VERMELHO, f"  [ERRO] {e}"))
        
        self.historico.adicionar('Telefone', telefone, {}, False)
        return None
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        return Cores.texto(Cores.AZUL, "─" * 50) + "\n" + Cores.texto(Cores.VERDE, resultado.get('dados', {}).get('raw', 'Sem dados'))


class ConsultaEmail(ConsultaService):
    def __init__(self):
        super().__init__("Email")
    
    def consultar(self, email: str) -> Optional[Dict]:
        print(Cores.texto(Cores.CIANO, f"\n[CONSULTA EMAIL] {email}"))
        
        headers = {'x-rapidapi-key': Config.RAPIDAPI_KEY, 'x-rapidapi-host': 'consulta-e-mail.p.rapidapi.com'}
        
        try:
            url = 'https://consulta-e-mail.p.rapidapi.com/apis/astrahvhdeus/Consultas%20Privadas/HTML/email.php'
            response = requests.get(url, headers=headers, params={'consulta': email}, timeout=15)
            if response.status_code == 200:
                texto = response.text
                if 'A Consulta Esta Funcionando Normally' not in texto:
                    resultado = {'fonte': 'rapidapi', 'dados': {'raw': texto}}
                    self.historico.adicionar('Email', email, resultado, True)
                    return resultado
        except Exception as e:
            print(Cores.texto(Cores.VERMELHO, f"  [ERRO] {e}"))
        
        self.historico.adicionar('Email', email, {}, False)
        return None
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        return Cores.texto(Cores.AZUL, "─" * 50) + "\n" + Cores.texto(Cores.VERDE, resultado.get('dados', {}).get('raw', 'Sem dados'))


class ConsultaNome(ConsultaService):
    def __init__(self):
        super().__init__("Nome")
    
    def consultar(self, nome: str) -> Optional[Dict]:
        print(Cores.texto(Cores.CIANO, f"\n[CONSULTA NOME] {nome}"))
        
        try:
            url = f'https://dualityapi.xyz/apis/flex_7/Consultas%20Privadas/HTML/nome.php?consulta={nome}'
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                texto = response.text
                if 'A Consulta Esta Funcionando Normally' not in texto:
                    resultado = {'fonte': 'dualityapi', 'dados': {'raw': texto}}
                    self.historico.adicionar('Nome', nome, resultado, True)
                    return resultado
        except Exception as e:
            print(Cores.texto(Cores.VERMELHO, f"  [ERRO] {e}"))
        
        self.historico.adicionar('Nome', nome, {}, False)
        return None
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        return Cores.texto(Cores.AZUL, "─" * 50) + "\n" + Cores.texto(Cores.VERDE, resultado.get('dados', {}).get('raw', 'Sem dados'))


class ConsultaRG(ConsultaService):
    def __init__(self):
        super().__init__("RG")
    
    def rg_dv(self, nums: str) -> str:
        soma = sum(int(nums[i]) * (9 - i) for i in range(8))
        resto = soma % 11
        dv = 11 - resto
        if dv == 10:
            return 'X'
        return str(dv % 11)
    
    def consultar(self, rg: str) -> Optional[Dict]:
        rg = ''.join(filter(str.isdigit, rg.replace('.', '').replace('-', '')))
        print(Cores.texto(Cores.CIANO, f"\n[VALIDAÇÃO RG] {rg}"))
        
        if len(rg) != 9:
            print(Cores.texto(Cores.VERMELHO, "  RG deve ter 9 dígitos"))
            return None
        
        rg_sem_dv = rg[:8]
        dv_calculado = self.rg_dv(rg_sem_dv)
        dv_informado = rg[8]
        valido = dv_calculado == dv_informado
        
        resultado = {
            'fonte': 'validador_local',
            'dados': {
                'rg': f"{rg[:2]}.{rg[2:5]}.{rg[5:8]}-{rg[8]}",
                'valido': valido,
                'dv_calculado': dv_calculado
            }
        }
        
        self.historico.adicionar('RG', rg, resultado, valido)
        return resultado
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        
        dados = resultado.get('dados', {})
        output = [Cores.texto(Cores.AZUL, "─" * 50)]
        
        cor = Cores.VERDE if dados.get('valido') else Cores.VERMELHO
        status = Cores.texto(cor, "VÁLIDO" if dados.get('valido') else "INVÁLIDO")
        
        output.append(Cores.texto(Cores.AMARELO, f"  • RG: {dados.get('rg')}"))
        output.append(Cores.texto(Cores.AMARELO, f"  • STATUS: {status}"))
        
        return "\n".join(output)


class ConsultaPlaca(ConsultaService):
    def __init__(self):
        super().__init__("Placa")
    
    def consultar(self, placa: str) -> Optional[Dict]:
        placa = placa.upper().replace('-', '').replace(' ', '')
        print(Cores.texto(Cores.CIANO, f"\n[CONSULTA PLACA] {placa}"))
        
        try:
            url = f'https://apicarros.com/v1/consulta/{placa}'
            response = requests.get(url, verify=False, timeout=15)
            if response.status_code == 200:
                resultado = {'fonte': 'apicarros', 'dados': response.json()}
                self.historico.adicionar('Placa', placa, resultado, True)
                return resultado
        except Exception as e:
            print(Cores.texto(Cores.VERMELHO, f"  [ERRO] {e}"))
        
        self.historico.adicionar('Placa', placa, {}, False)
        return None
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        
        dados = resultado.get('dados', {})
        output = [Cores.texto(Cores.AZUL, "─" * 50)]
        
        for chave, valor in dados.items():
            output.append(Cores.texto(Cores.AMARELO, f"  • {chave.upper()}: ") + str(valor))
        
        return "\n".join(output)


class ConsultaDDD(ConsultaService):
    def __init__(self):
        super().__init__("DDD")
    
    def consultar(self, ddd: str) -> Optional[Dict]:
        ddd = ''.join(filter(str.isdigit, ddd))
        print(Cores.texto(Cores.CIANO, f"\n[CONSULTA DDD] {ddd}"))
        
        try:
            url = f'https://brasilapi.com.br/api/ddd/v1/{ddd}'
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                resultado = {'fonte': 'brasilapi', 'dados': response.json()}
                self.historico.adicionar('DDD', ddd, resultado, True)
                return resultado
        except Exception as e:
            print(Cores.texto(Cores.VERMELHO, f"  [ERRO] {e}"))
        
        self.historico.adicionar('DDD', ddd, {}, False)
        return None
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        
        dados = resultado.get('dados', {})
        output = [Cores.texto(Cores.AZUL, "─" * 50)]
        
        for chave, valor in dados.items():
            if isinstance(valor, list):
                output.append(Cores.texto(Cores.AMARELO, f"  • {chave.upper()}:"))
                for item in valor:
                    output.append(f"    - {item}")
            else:
                output.append(Cores.texto(Cores.AMARELO, f"  • {chave.upper()}: ") + str(valor))
        
        return "\n".join(output)


class ConsultaDDI(ConsultaService):
    def __init__(self):
        super().__init__("DDI")
        self.paises_ddi = {
            '55': ('Brasil', '+55'),
            '1': ('Estados Unidos/Canadá', '+1'),
            '44': ('Reino Unido', '+44'),
            '49': ('Alemanha', '+49'),
            '33': ('França', '+33'),
            '34': ('Espanha', '+34'),
            '31': ('Holanda', '+31'),
            '21': ('Portugal', '+351'),
            '11': ('Japão', '+81'),
            '82': ('Coreia do Sul', '+82'),
            '86': ('China', '+86'),
            '61': ('Austrália', '+61'),
            '27': ('África do Sul', '+27'),
            '52': ('México', '+52'),
            '51': ('Peru', '+51'),
            '54': ('Argentina', '+54'),
            '56': ('Chile', '+56'),
            '593': ('Equador', '+593'),
            '505': ('Nicarágua', '+505'),
            '502': ('Guatemala', '+502'),
        }
    
    def consultar(self, ddi: str) -> Optional[Dict]:
        ddi = ''.join(filter(str.isdigit, ddi))
        print(Cores.texto(Cores.CIANO, f"\n[CONSULTA DDI] +{ddi}"))
        
        pais, formato = self.paises_ddi.get(ddi, ('Desconhecido', f'+{ddi}'))
        
        resultado = {
            'fonte': 'local',
            'dados': {
                'ddi': ddi,
                'pais': pais,
                'formato_internacional': formato
            }
        }
        
        self.historico.adicionar('DDI', ddi, resultado, True)
        return resultado
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        
        dados = resultado.get('dados', {})
        output = [Cores.texto(Cores.AZUL, "─" * 50)]
        
        output.append(Cores.texto(Cores.AMARELO, f"  • DDI: +{dados.get('ddi')}"))
        output.append(Cores.texto(Cores.AMARELO, f"  • PAÍS: {dados.get('pais')}"))
        output.append(Cores.texto(Cores.AMARELO, f"  • FORMATO: {dados.get('formato_internacional')}"))
        
        return "\n".join(output)


class ConsultaBIN(ConsultaService):
    def __init__(self):
        super().__init__("BIN")
    
    def consultar(self, bin_code: str) -> Optional[Dict]:
        bin_code = ''.join(filter(str.isdigit, bin_code))[:6]
        print(Cores.texto(Cores.CIANO, f"\n[CONSULTA BIN] {bin_code}"))
        
        try:
            url = f'https://lookup.binlist.net/{bin_code}'
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                resultado = {'fonte': 'binlist', 'dados': response.json()}
                self.historico.adicionar('BIN', bin_code, resultado, True)
                return resultado
        except Exception as e:
            print(Cores.texto(Cores.VERMELHO, f"  [ERRO] {e}"))
        
        self.historico.adicionar('BIN', bin_code, {}, False)
        return None
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        
        dados = resultado.get('dados', {})
        output = [Cores.texto(Cores.AZUL, "─" * 50)]
        
        campos = ['scheme', 'type', 'brand', 'country', 'bank']
        for campo in campos:
            if campo in dados:
                valor = dados[campo]
                if isinstance(valor, dict):
                    for k, v in valor.items():
                        output.append(Cores.texto(Cores.AMARELO, f"  • {campo.upper()}.{k.upper()}: ") + str(v))
                else:
                    output.append(Cores.texto(Cores.AMARELO, f"  • {campo.upper()}: ") + str(valor))
        
        return "\n".join(output)


class ConsultaBanco(ConsultaService):
    def __init__(self):
        super().__init__("Banco")
    
    def consultar(self, codigo: str = None) -> Optional[Dict]:
        print(Cores.texto(Cores.CIANO, f"\n[CONSULTA BANCO]"))
        
        try:
            url = 'https://brasilapi.com.br/api/banks/v1'
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                bancos = response.json()
                
                if codigo:
                    codigo = ''.join(filter(str.isdigit, codigo))
                    for banco in bancos:
                        if str(banco.get('code')) == codigo:
                            resultado = {'fonte': 'brasilapi', 'dados': banco}
                            self.historico.adicionar('Banco', codigo, resultado, True)
                            return resultado
                    return {'fonte': 'brasilapi', 'dados': {'erro': 'Banco não encontrado'}}
                else:
                    resultado = {'fonte': 'brasilapi', 'dados': {'bancos': bancos[:50]}}
                    self.historico.adicionar('Banco', 'lista', resultado, True)
                    return resultado
        except Exception as e:
            print(Cores.texto(Cores.VERMELHO, f"  [ERRO] {e}"))
        
        return None
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        
        dados = resultado.get('dados', {})
        output = [Cores.texto(Cores.AZUL, "─" * 50)]
        
        if 'bancos' in dados:
            output.append(Cores.texto(Cores.AMARELO, "  Lista de bancos disponíveis:"))
            for banco in dados['bancos']:
                output.append(f"    {banco.get('code')} - {banco.get('name')}")
        else:
            for chave, valor in dados.items():
                output.append(Cores.texto(Cores.AMARELO, f"  • {chave.upper()}: ") + str(valor))
        
        return "\n".join(output)


class ConsultaInstagram(ConsultaService):
    def __init__(self):
        super().__init__("Instagram")
    
    def consultar(self, username: str) -> Optional[Dict]:
        username = username.replace('@', '').strip()
        print(Cores.texto(Cores.CIANO, f"\n[CONSULTA INSTAGRAM] @{username}"))
        
        try:
            url = f'https://api.hyperhuman.io/v1/instagram/user/{username}'
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                resultado = {'fonte': 'hyperhuman', 'dados': response.json()}
                self.historico.adicionar('Instagram', username, resultado, True)
                return resultado
        except Exception as e:
            print(Cores.texto(Cores.VERMELHO, f"  [ERRO] {e}"))
        
        self.historico.adicionar('Instagram', username, {}, False)
        return None
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        
        dados = resultado.get('dados', {})
        output = [Cores.texto(Cores.AZUL, "─" * 50)]
        
        for chave, valor in dados.items():
            output.append(Cores.texto(Cores.AMARELO, f"  • {chave.upper()}: ") + str(valor))
        
        return "\n".join(output)


class ConsultaTikTok(ConsultaService):
    def __init__(self):
        super().__init__("TikTok")
    
    def consultar(self, username: str) -> Optional[Dict]:
        username = username.replace('@', '').strip()
        print(Cores.texto(Cores.CIANO, f"\n[CONSULTA TIKTOK] @{username}"))
        
        try:
            url = f'https://api.hyperhuman.io/v1/tiktok/user/{username}'
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                resultado = {'fonte': 'hyperhuman', 'dados': response.json()}
                self.historico.adicionar('TikTok', username, resultado, True)
                return resultado
        except Exception as e:
            print(Cores.texto(Cores.VERMELHO, f"  [ERRO] {e}"))
        
        self.historico.adicionar('TikTok', username, {}, False)
        return None
    
    def formatar_resultado(self, resultado: Dict) -> str:
        if not resultado:
            return "Nenhum resultado encontrado"
        
        dados = resultado.get('dados', {})
        output = [Cores.texto(Cores.AZUL, "─" * 50)]
        
        for chave, valor in dados.items():
            output.append(Cores.texto(Cores.AMARELO, f"  • {chave.upper()}: ") + str(valor))
        
        return "\n".join(output)


# ============================================================================
# CLI INTERATIVO
# ============================================================================

class CLI:
    def __init__(self):
        self.servicos = {
            '1': ('CPF', ConsultaCPF()),
            '2': ('CNPJ', ConsultaCNPJ()),
            '3': ('CEP', ConsultaCEP()),
            '4': ('IP', ConsultaIP()),
            '5': ('Telefone', ConsultaTelefone()),
            '6': ('Email', ConsultaEmail()),
            '7': ('Nome', ConsultaNome()),
            '8': ('RG', ConsultaRG()),
            '9': ('Placa', ConsultaPlaca()),
            '10': ('DDD', ConsultaDDD()),
            '11': ('DDI', ConsultaDDI()),
            '12': ('BIN', ConsultaBIN()),
            '13': ('Banco', ConsultaBanco()),
            '14': ('Instagram', ConsultaInstagram()),
            '15': ('TikTok', ConsultaTikTok()),
        }
        self.cache = Cache()
        self.historico = Historico()
    
    def limpar_tela(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def banner(self):
        print(Cores.texto(Cores.AZUL, """
    ╔══════════════════════════════════════════════════╗
    ║       CONSULTAS UNIFICADAS - TERMINAL v2.0       ║
    ║       Agrega múltiplas fontes com fallback        ║
    ╚══════════════════════════════════════════════════╝
        """))
    
    def menu(self):
        print(Cores.texto(Cores.CIANO, """
    ┌─────────────────────────────────────────────────┐
    │              MENU PRINCIPAL                     │
    ├─────────────────────────────────────────────────┤
    │  [1] CPF          [8]  RG                      │
    │  [2] CNPJ         [9]  Placa                   │
    │  [3] CEP          [10] DDD                      │
    │  [4] IP           [11] DDI                      │
    │  [5] Telefone    [12] BIN (Cartão)            │
    │  [6] Email        [13] Banco                    │
    │  [7] Nome         [14] Instagram               │
    │                         [15] TikTok            │
    ├─────────────────────────────────────────────────┤
    │  [G] Gerar CPF/CNPJ    [H] Histórico          │
    │  [C] Limpar Cache      [E] Exportar           │
    │  [0] Sair                                      │
    └─────────────────────────────────────────────────┘
        """))
    
    def obter_entrada(self, texto: str) -> Optional[str]:
        while True:
            entrada = input(Cores.texto(Cores.VERDE, f"\n{texto}: ")).strip()
            if entrada.lower() in ['99', 'q', 'sair', 'voltar']:
                return None
            if entrada:
                return entrada
            print(Cores.texto(Cores.VERMELHO, "  Campo obrigatório!"))
    
    def executar_consulta(self, chave: str):
        nome, servico = self.servicos[chave]
        entrada = self.obter_entrada(f"Informe o {nome}")
        if not entrada:
            return
        
        resultado = servico.consultar(entrada)
        print(servico.formatar_resultado(resultado))
        self.opcao_exportar(resultado)
        
        input(Cores.texto(Cores.AZUL, "\n[Enter] para continuar..."))
    
    def gerar_documentos(self):
        print(Cores.texto(Cores.CIANO, """
    ┌─────────────────────────────────────────────────┐
    │           GERAR DOCUMENTOS                     │
    ├─────────────────────────────────────────────────┤
    │  [1] Gerar CPF válido                          │
    │  [2] Gerar CNPJ válido                         │
    │  [3] Validar CPF                               │
    │  [4] Validar CNPJ                               │
    │  [0] Voltar                                     │
    └─────────────────────────────────────────────────┘
        """))
        
        opcao = input(Cores.texto(Cores.VERDE, "\n~# Escolha: ")).strip()
        
        if opcao == '1':
            cpf = Validators.gerar_cpf()
            valido = Validators.validar_cpf(cpf)
            print(Cores.texto(Cores.AZUL, "─" * 50))
            print(Cores.texto(Cores.AMARELO, f"  • CPF GERADO: {Validators.formatar_cpf(cpf)}"))
            print(Cores.texto(Cores.VERDE if valido else Cores.VERMELHO, f"  • VÁLIDO: {valido}"))
        
        elif opcao == '2':
            cnpj = Validators.gerar_cnpj()
            print(Cores.texto(Cores.AZUL, "─" * 50))
            print(Cores.texto(Cores.AMARELO, f"  • CNPJ GERADO: {Validators.formatar_cnpj(cnpj)}"))
        
        elif opcao == '3':
            cpf = self.obter_entrada("CPF a validar")
            if cpf:
                valido = Validators.validar_cpf(cpf)
                print(Cores.texto(Cores.AZUL, "─" * 50))
                print(Cores.texto(Cores.AMARELO, f"  • CPF: {Validators.formatar_cpf(cpf)}"))
                print(Cores.texto(Cores.VERDE if valido else Cores.VERMELHO, f"  • VÁLIDO: {valido}"))
        
        elif opcao == '4':
            cnpj = self.obter_entrada("CNPJ a validar")
            if cnpj:
                valido = Validators.validar_cnpj(cnpj)
                print(Cores.texto(Cores.AZUL, "─" * 50))
                print(Cores.texto(Cores.AMARELO, f"  • CNPJ: {Validators.formatar_cnpj(cnpj)}"))
                print(Cores.texto(Cores.VERDE if valido else Cores.VERMELHO, f"  • VÁLIDO: {valido}"))
        
        input(Cores.texto(Cores.AZUL, "\n[Enter] para continuar..."))
    
    def ver_historico(self):
        print(Cores.texto(Cores.CIANO, "\n[HISTÓRICO DE CONSULTAS]"))
        registros = self.historico.listar(20)
        
        if not registros:
            print(Cores.texto(Cores.AMARELO, "  Nenhuma consulta registrada."))
        else:
            for i, reg in enumerate(registros, 1):
                status = Cores.texto(Cores.VERDE, "✓") if reg.get('sucesso') else Cores.texto(Cores.VERMELHO, "✗")
                print(f"  {i}. {reg['tipo']}: {reg['entrada']} {status}")
        
        input(Cores.texto(Cores.AZUL, "\n[Enter] para continuar..."))
    
    def opcao_exportar(self, resultado: Dict):
        if not resultado:
            return
        
        print(Cores.texto(Cores.CIANO, "\n[E] Exportar resultado? (s/n): "), end='')
        if input().lower() == 's':
            print(Cores.texto(Cores.CIANO, "  Formato: [1] JSON  [2] TXT  [3] CSV"))
            fmt = input(Cores.texto(Cores.VERDE, "  ~# ").strip()
            
            nome = input(Cores.texto(Cores.VERDE, "  Nome do arquivo: ")).strip()
            
            if fmt == '1':
                Exportador.para_json(resultado.get('dados', {}), f"{nome}.json")
            elif fmt == '2':
                Exportador.para_txt(resultado.get('dados', {}), f"{nome}.txt")
            elif fmt == '3':
                Exportador.para_csv(resultado.get('dados', {}), f"{nome}.csv")
            
            print(Cores.texto(Cores.VERDE, f"  ✓ Salvo em {nome}"))
    
    def limpar_cache(self):
        self.cache.limpar()
        print(Cores.texto(Cores.VERDE, "  ✓ Cache limpo!"))
        time.sleep(1)
    
    def iniciar(self):
        while True:
            self.limpar_tela()
            self.banner()
            self.menu()
            
            opcao = input(Cores.texto(Cores.VERDE, "\n~# Escolha uma opção: ")).strip()
            
            if opcao == '0':
                print(Cores.texto(Cores.AMARELO, "\n  Até mais!\n"))
                break
            
            if opcao in self.servicos:
                self.executar_consulta(opcao)
            elif opcao.lower() == 'g':
                self.gerar_documentos()
            elif opcao.lower() == 'h':
                self.ver_historico()
            elif opcao.lower() == 'c':
                self.limpar_cache()
            elif opcao.lower() == 'e':
                print(Cores.texto(Cores.AMARELO, "  Use a opção ao final de cada consulta."))
                time.sleep(1)
            else:
                print(Cores.texto(Cores.VERMELHO, "\n  Opção inválida!"))
                time.sleep(1)


# ============================================================================
# INTERFACE WEB (FLASK)
# ============================================================================

def iniciar_web():
    """Inicia interface web com Flask"""
    try:
        from flask import Flask, request, render_template_string, jsonify
    except ImportError:
        print(Cores.texto(Cores.VERMELHO, "  Flask não instalado. Execute: pip install flask"))
        return
    
    app = Flask(__name__)
    
    HTML_TEMPLATE = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Consultas Unificado</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #1a1a2e; color: #eee; }
            h1 { color: #00d4ff; text-align: center; }
            .menu { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0; }
            .btn { padding: 15px; background: #16213e; border: 1px solid #0f3460; color: #00d4ff; cursor: pointer; text-align: center; border-radius: 5px; }
            .btn:hover { background: #0f3460; }
            input, select { padding: 10px; width: 100%; margin: 5px 0; background: #16213e; color: #fff; border: 1px solid #0f3460; }
            button { padding: 10px 20px; background: #e94560; color: #fff; border: none; cursor: pointer; margin: 5px; }
            button:hover { background: #ff6b6b; }
            #resultado { margin-top: 20px; padding: 15px; background: #16213e; border-radius: 5px; white-space: pre-wrap; }
            .loading { color: #ffd700; }
        </style>
    </head>
    <body>
        <h1>🔍 Consultas Unificado</h1>
        <div class="menu">
            {% for tipo, nome in tipos %}
            <div class="btn" onclick="selecionar('{{ tipo }}')">{{ nome }}</div>
            {% endfor %}
        </div>
        <div id="entrada" style="display:none;">
            <input type="text" id="valor" placeholder="Digite o valor...">
            <button onclick="consultar()">Consultar</button>
        </div>
        <div id="resultado"></div>
        <script>
            let tipoAtual = '';
            const tipos = {{ tipos_json | safe }};
            
            function selecionar(tipo) {
                tipoAtual = tipo;
                document.getElementById('entrada').style.display = 'block';
                document.getElementById('valor').focus();
            }
            
            async function consultar() {
                const valor = document.getElementById('valor').value;
                const resultado = document.getElementById('resultado');
                resultado.innerHTML = '<p class="loading">Consultando...</p>';
                
                try {
                    const response = await fetch('/api/consultar', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({tipo: tipoAtual, valor: valor})
                    });
                    const data = await response.json();
                    resultado.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                } catch(e) {
                    resultado.innerHTML = '<p style="color:red">Erro: ' + e + '</p>';
                }
            }
        </script>
    </body>
    </html>
    '''
    
    @app.route('/')
    def index():
        tipos = [
            ('cpf', 'CPF'), ('cnpj', 'CNPJ'), ('cep', 'CEP'), ('ip', 'IP'),
            ('telefone', 'Telefone'), ('email', 'Email'), ('nome', 'Nome'),
            ('rg', 'RG'), ('placa', 'Placa'), ('ddd', 'DDD'), ('ddi', 'DDI'),
            ('bin', 'BIN'), ('banco', 'Banco'), ('instagram', 'Instagram'), ('tiktok', 'TikTok')
        ]
        return render_template_string(HTML_TEMPLATE, tipos=tipos, tipos_json=json.dumps(tipos))
    
    @app.route('/api/consultar', methods=['POST'])
    def api_consultar():
        dados = request.json
        tipo = dados.get('tipo', '').lower()
        valor = dados.get('valor', '')
        
        servicos = {
            'cpf': ConsultaCPF(), 'cnpj': ConsultaCNPJ(), 'cep': ConsultaCEP(),
            'ip': ConsultaIP(), 'telefone': ConsultaTelefone(), 'email': ConsultaEmail(),
            'nome': ConsultaNome(), 'rg': ConsultaRG(), 'placa': ConsultaPlaca(),
            'ddd': ConsultaDDD(), 'ddi': ConsultaDDI(), 'bin': ConsultaBIN(),
            'banco': ConsultaBanco(), 'instagram': ConsultaInstagram(), 'tiktok': ConsultaTikTok()
        }
        
        if tipo not in servicos:
            return jsonify({'erro': 'Tipo inválido'})
        
        resultado = servicos[tipo].consultar(valor)
        return jsonify(resultado.get('dados', {}) if resultado else {})
    
    print(Cores.texto(Cores.VERDE, "\n  🎉 Interface web iniciada em http://localhost:5000"))
    app.run(host='0.0.0.0', port=5000, debug=False)


# ============================================================================
# MODO LINHA DE COMANDO
# ============================================================================

def modo_cli(tipo: str, valor: str):
    """Executa consulta via linha de comando"""
    servicos = {
        'cpf': ConsultaCPF(), 'cnpj': ConsultaCNPJ(), 'cep': ConsultaCEP(),
        'ip': ConsultaIP(), 'telefone': ConsultaTelefone(), 'email': ConsultaEmail(),
        'nome': ConsultaNome(), 'rg': ConsultaRG(), 'placa': ConsultaPlaca(),
        'ddd': ConsultaDDD(), 'ddi': ConsultaDDI(), 'bin': ConsultaBIN(),
        'banco': ConsultaBanco(), 'instagram': ConsultaInstagram(), 'tiktok': ConsultaTikTok(),
        'gerar-cpf': None, 'gerar-cnpj': None, 'validar-cpf': None, 'validar-cnpj': None
    }
    
    if tipo == 'gerar-cpf':
        cpf = Validators.gerar_cpf()
        print(f"CPF gerado: {Validators.formatar_cpf(cpf)} (válido: {Validators.validar_cpf(cpf)})")
        return
    
    if tipo == 'gerar-cnpj':
        cnpj = Validators.gerar_cnpj()
        print(f"CNPJ gerado: {Validators.formatar_cnpj(cnpj)}")
        return
    
    if tipo == 'validar-cpf':
        print(f"CPF válido: {Validators.validar_cpf(valor)}")
        return
    
    if tipo == 'validar-cnpj':
        print(f"CNPJ válido: {Validators.validar_cnpj(valor)}")
        return
    
    if tipo not in servicos:
        print(f"Tipo '{tipo}' não reconhecido")
        return
    
    servico = servicos[tipo]
    resultado = servico.consultar(valor)
    print(servico.formatar_resultado(resultado))


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Consultas Unificado CLI')
    parser.add_argument('tipo', nargs='?', help='Tipo de consulta (cpf, cnpj, cep, etc)')
    parser.add_argument('valor', nargs='?', help='Valor a consultar')
    parser.add_argument('--web', action='store_true', help='Iniciar interface web')
    parser.add_argument('--clear-cache', action='store_true', help='Limpar cache')
    parser.add_argument('--clear-history', action='store_true', help='Limpar histórico')
    parser.add_argument('--history', action='store_true', help='Ver histórico')
    
    args = parser.parse_args()
    
    if args.clear_cache:
        Cache().limpar()
        print("Cache limpo!")
        return
    
    if args.clear_history:
        Historico().limpar()
        print("Histórico limpo!")
        return
    
    if args.history:
        h = Historico()
        for reg in h.listar(20):
            print(f"{reg['tipo']}: {reg['entrada']} - {reg.get('fonte', 'N/A')}")
        return
    
    if args.web:
        iniciar_web()
        return
    
    if args.tipo and args.valor:
        modo_cli(args.tipo.lower(), args.valor)
        return
    
    # Modo interativo
    cli = CLI()
    cli.iniciar()


if __name__ == '__main__':
    main()