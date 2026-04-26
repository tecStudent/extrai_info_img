import re
import pandas as pd
from utils import get_config_value, resolve_project_path

# =========================
# CONFIGURAÇÕES
# =========================
PASTA_SAIDA = resolve_project_path(get_config_value("ARQUIVO_SAIDA"))
ARQUIVO_ENTRADA = PASTA_SAIDA / "raw.xlsx"
ARQUIVO_SAIDA = PASTA_SAIDA / "silver.xlsx"
ABA_ENTRADA = "alertas"  # altere se necessário


# =========================
# CAMPOS QUE SERÃO EXTRAÍDOS
# =========================
CAMPOS = [
    "DAG ID",
    "Execution Date",
    "Status",
    "Failed Tasks",
    "Task",
    "Eror",
    "View Logs",
    "Other Failed Tasks",
    "Tasks",
]

# Também aceita "Error:" caso em alguns prints venha corrigido
PADROES_EQUIVALENTES = {
    "DAG ID": [r"DAG ID:"],
    "Execution Date": [r"Execution Date:"],
    "Status": [r"Status:"],
    "Failed Tasks": [r"Failed Tasks:"],
    "Task": [r"Task:"],
    "Eror": [r"Eror:", r"Error:"],
    "View Logs": [r"View Logs"],
    "Other Failed Tasks": [r"Other Failed Tasks:"],
    "Tasks": [r"Tasks:"],
}


def normalizar_texto(texto: str) -> str:
    if pd.isna(texto):
        return ""
    texto = str(texto)
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{2,}", "\n", texto)
    return texto.strip()


def montar_regex_campo(campo_atual: str) -> re.Pattern:
    """
    Extrai o conteúdo após um rótulo até encontrar o próximo rótulo conhecido
    ou o fim do texto.
    """
    rotulos_atuais = PADROES_EQUIVALENTES[campo_atual]

    # junta todos os outros rótulos como delimitadores de parada
    outros_rotulos = []
    for campo, padroes in PADROES_EQUIVALENTES.items():
        if campo != campo_atual:
            outros_rotulos.extend(padroes)

    atual = "|".join(rotulos_atuais)
    proximos = "|".join(outros_rotulos)

    # captura tudo após o rótulo atual até o próximo rótulo conhecido
    pattern = rf"(?is)(?:{atual})\s*(.*?)(?=\n?(?:{proximos})|\Z)"
    return re.compile(pattern)


def extrair_campos(texto: str) -> dict:
    texto = normalizar_texto(texto)

    resultado = {campo: None for campo in CAMPOS}

    for campo in CAMPOS:
        regex = montar_regex_campo(campo)
        match = regex.search(texto)

        if match:
            valor = match.group(1).strip()

            # limpa caracteres sobrando
            valor = re.sub(r"^[\-\:\s]+", "", valor)
            valor = re.sub(r"\s+$", "", valor)

            # para View Logs, caso ele apareça sem valor após ele
            if campo == "View Logs" and not valor:
                valor = "Encontrado"

            resultado[campo] = valor

    # caso "View Logs" exista no texto mas não tenha sido capturado com conteúdo
    if resultado["View Logs"] is None and re.search(r"(?i)\bView Logs\b", texto):
        resultado["View Logs"] = "Encontrado"

    return resultado


def processar_excel():
    df = pd.read_excel(ARQUIVO_ENTRADA, sheet_name=ABA_ENTRADA)

    if "texto_bruto" not in df.columns:
        raise ValueError("A coluna 'texto_bruto' não foi encontrada no Excel de entrada.")

    registros = []

    for idx, row in df.iterrows():
        texto = row["texto_bruto"]
        dados_extraidos = extrair_campos(texto)

        registro = {
            "linha_origem": idx + 2,  # considerando cabeçalho do Excel
            "texto_bruto": texto,
            **dados_extraidos
        }

        # mantém o nome do arquivo, caso exista
        if "arquivo" in df.columns:
            registro["arquivo"] = row["arquivo"]

        registros.append(registro)

    df_saida = pd.DataFrame(registros)

    # organiza colunas
    colunas_finais = []
    if "arquivo" in df_saida.columns:
        colunas_finais.append("arquivo")
    colunas_finais += ["linha_origem", "texto_bruto"] + CAMPOS

    df_saida = df_saida[colunas_finais]

    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df_saida.to_excel(ARQUIVO_SAIDA, index=False)
    print(f"Novo Excel gerado com sucesso em: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    processar_excel()
