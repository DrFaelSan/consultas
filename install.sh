#!/bin/bash
# Script de instalação para Termux

echo "=========================================="
echo "  CONSULTAS UNIFICADO - INSTALAÇÃO"
echo "=========================================="

# Atualiza pacotes
echo ""
echo "[1/3] Atualizando pacotes..."
pkg update -y

# Instala Python (se necessário)
echo ""
echo "[2/3] Verificando Python..."
if ! command -v python &> /dev/null; then
    pkg install -y python
fi

# Instala dependências
echo ""
echo "[3/3] Instalando dependências..."
pip install -r requirements.txt

# Verifica instalação
echo ""
echo "=========================================="
echo "  INSTALAÇÃO CONCLUÍDA!"
echo "=========================================="
echo ""
echo "Para executar:"
echo "  python main.py"
echo ""
echo "Modo interativo:"
echo "  python main.py"
echo ""
echo "Modo linha de comando:"
echo "  python main.py cpf 12345678900"
echo "  python main.py cnpj 12345678000100"
echo "  python main.py cep 01001000"
echo "  python main.py ip 8.8.8.8"
echo ""
echo "Ver histórico:"
echo "  python main.py --history"
echo ""