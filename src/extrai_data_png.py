from pathlib import Path
import re
import json
import numpy as np
import pandas as pd
from utils import get_config_value, resolve_project_path
from PIL import Image, ImageOps
import easyocr


# =========================
# CONFIGURAÇÕES
# =========================
PASTA_IMAGENS = resolve_project_path(get_config_value("PASTA_IMAGENS"))
ARQUIVO_SAIDA = resolve_project_path(get_config_value("ARQUIVO_SAIDA"))
IDIOMAS_OCR = ["pt", "en"]  # pode manter assim para prints em pt/en


# =========================
# OCR
# =========================
reader: easyocr.Reader | None = None


def get_reader() -> easyocr.Reader:
    global reader
    if reader is None:
        reader = easyocr.Reader(IDIOMAS_OCR, gpu=False)
    return reader


def preprocessar_imagem(caminho_imagem: Path) -> np.ndarray:
    """
    Faz um pré-processamento simples para melhorar o OCR:
    - escala de cinza
    - autocontraste
    - aumento de nitidez por limiar simples
    """
    img = Image.open(caminho_imagem).convert("L")
    img = ImageOps.autocontrast(img)

    # Binarização simples
    img = img.point(lambda p: 255 if p > 160 else 0)

    # Pequeno upscale para melhorar OCR em prints menores
    largura, altura = img.size
    img = img.resize((largura * 2, altura * 2))

    return np.array(img)


def extrair_texto_ocr(caminho_imagem: Path) -> str:
    imagem = preprocessar_imagem(caminho_imagem)
    resultados = get_reader().readtext(imagem, detail=0, paragraph=True)

    texto = "\n".join([linha.strip() for linha in resultados if linha.strip()])
    return texto.strip()


# =========================
# EXTRAÇÃO DE CAMPOS
# =========================
def limpar_texto(texto: str) -> str:
    texto = texto.replace("\u200b", " ")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{2,}", "\n", texto)
    return texto.strip()


def extrair_data_hora(texto: str) -> str | None:
    padroes = [
        r"\b\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\b",
        r"\b\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}\b",
        r"\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\b",
        r"\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\b",
    ]
    for padrao in padroes:
        match = re.search(padrao, texto)
        if match:
            return match.group(0)
    return None


def extrair_nivel_alerta(texto: str) -> str | None:
    niveis = [
        "critical", "critico", "crítico",
        "error", "erro",
        "warning", "warn", "aviso",
        "alert", "alerta",
        "info", "informacao", "informação"
    ]

    texto_lower = texto.lower()
    for nivel in niveis:
        if nivel in texto_lower:
            return nivel
    return None


def extrair_codigo(texto: str) -> str | None:
    padroes = [
        r"\b[A-Z]{2,}-\d{2,}\b",           # EX: ERR-123
        r"\b[A-Z_]{3,}\b",                 # EX: TIMEOUT_ERROR
        r"\bcode[: ]+[A-Za-z0-9._-]+\b",   # EX: code: ABC123
    ]
    for padrao in padroes:
        match = re.search(padrao, texto, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def extrair_urls(texto: str) -> list[str]:
    return re.findall(r"https?://[^\s]+", texto)


def extrair_email(texto: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", texto)


def extrair_ip(texto: str) -> list[str]:
    return re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", texto)


def extrair_titulo(texto: str) -> str | None:
    """
    Tenta usar a primeira linha relevante como título.
    """
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    if not linhas:
        return None

    # ignora linhas que parecem data/hora pura
    for linha in linhas:
        if not re.fullmatch(r"[\d/: -]+", linha):
            return linha
    return linhas[0]


def extrair_origem(texto: str) -> str | None:
    padroes = [
        r"(?:origem|source|sistema|system|host|serviço|servico)[: ]+([^\n]+)",
    ]
    for padrao in padroes:
        match = re.search(padrao, texto, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def montar_registro(caminho_imagem: Path, texto: str) -> dict:
    texto = limpar_texto(texto)
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]

    registro = {
        "arquivo": caminho_imagem.name,
        "caminho_completo": str(caminho_imagem),
        "titulo": extrair_titulo(texto),
        "data_hora": extrair_data_hora(texto),
        "nivel_alerta": extrair_nivel_alerta(texto),
        "origem": extrair_origem(texto),
        "codigo": extrair_codigo(texto),
        "qtd_linhas": len(linhas),
        "urls": json.dumps(extrair_urls(texto), ensure_ascii=False),
        "emails": json.dumps(extrair_email(texto), ensure_ascii=False),
        "ips": json.dumps(extrair_ip(texto), ensure_ascii=False),
        "texto_bruto": texto,
    }

    # adiciona cada linha em uma coluna separada
    for i, linha in enumerate(linhas, start=1):
        registro[f"linha_{i}"] = linha

    return registro


# =========================
# PROCESSAMENTO
# =========================
def processar_pasta(pasta_imagens: Path, arquivo_saida: Path):
    pasta = Path(pasta_imagens)
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

    if not pasta.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {pasta}")

    imagens = sorted(pasta.glob("*.png"))

    if not imagens:
        print("Nenhum arquivo PNG encontrado.")
        return

    registros = []
    erros = []

    for img in imagens:
        try:
            print(f"Lendo: {img.name}")
            texto = extrair_texto_ocr(img)
            registro = montar_registro(img, texto)
            registros.append(registro)
        except Exception as e:
            erros.append({
                "arquivo": img.name,
                "erro": str(e)
            })

    df = pd.DataFrame(registros)

    with pd.ExcelWriter(arquivo_saida, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="alertas", index=False)

        if erros:
            df_erros = pd.DataFrame(erros)
            df_erros.to_excel(writer, sheet_name="erros", index=False)

    print(f"\nArquivo gerado com sucesso: {arquivo_saida}")
    print(f"Total de imagens processadas: {len(registros)}")
    print(f"Total de erros: {len(erros)}")


if __name__ == "__main__":
    path_file = ARQUIVO_SAIDA / "raw.xlsx"
    processar_pasta(PASTA_IMAGENS, path_file)
