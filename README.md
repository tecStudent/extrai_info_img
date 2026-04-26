# Extrator de Alertas por OCR

Projeto para transformar prints de alertas em dados estruturados a partir de imagens `.png`.

O fluxo atual tem duas etapas:
- `src/extrai_data_png.py`: lê as imagens, executa OCR e gera a base bruta `storage/raw.xlsx`.
- `src/formata_coluna.py`: lê a base bruta e gera a base tratada `storage/silver.xlsx`.

## O que o projeto faz

Na etapa bruta, o projeto:
- lê imagens `.png` da pasta configurada em `PASTA_IMAGENS`;
- aplica pré-processamento para melhorar o OCR;
- extrai texto com `easyocr`;
- monta uma planilha com metadados e texto extraído.

Campos gerados na base bruta incluem:
- `arquivo`
- `caminho_completo`
- `titulo`
- `data_hora`
- `nivel_alerta`
- `origem`
- `codigo`
- `qtd_linhas`
- `urls`
- `emails`
- `ips`
- `texto_bruto`
- `linha_1`, `linha_2`, `linha_3`... conforme o conteúdo extraído

Na etapa tratada, o projeto lê a aba `alertas` do `raw.xlsx` e tenta estruturar campos como:
- `DAG ID`
- `Execution Date`
- `Status`
- `Failed Tasks`
- `Task`
- `Eror`
- `View Logs`
- `Other Failed Tasks`
- `Tasks`

## Estrutura do projeto

- `src/extrai_data_png.py`: pipeline de OCR e geração do `raw.xlsx`
- `src/formata_coluna.py`: normalização dos campos e geração do `silver.xlsx`
- `src/utils.py`: leitura de configuração e resolução de caminhos
- `infra/config.txt`: configuração padrão versionada
- `infra/config.local.txt`: configuração local opcional, com prioridade sobre `config.txt`
- `assets/`: pasta padrão para imagens de entrada
- `storage/`: saída das planilhas geradas

## Configuração

Instale as dependências:

```bash
pip install -r requirements.txt
```

Se precisar de configuração local, copie `infra/config.txt` para `infra/config.local.txt` e ajuste os caminhos.

Configuração padrão atual:

```txt
PASTA_IMAGENS=assets/
ARQUIVO_SAIDA=storage
```

Com isso:
- as imagens de entrada ficam em `assets/`
- o arquivo bruto é gerado em `storage/raw.xlsx`
- o arquivo tratado é gerado em `storage/silver.xlsx`

## Como executar

Gerar a base bruta com OCR:

```bash
python src/extrai_data_png.py
```

Gerar a base tratada a partir do `raw.xlsx`:

```bash
python src/formata_coluna.py
```

## Observações atuais

- O projeto processa apenas arquivos `.png`.
- O OCR é inicializado sob demanda, e não mais no import do módulo.
- A etapa de formatação usa regex pré-compilados para reduzir trabalho repetido durante a extração.
- Se a pasta configurada em `PASTA_IMAGENS` não existir, o script interrompe com `FileNotFoundError`.
- Se não houver imagens `.png`, o script encerra sem gerar processamento.

## Arquivos gerados

- `storage/raw.xlsx`: saída bruta do OCR
- `storage/silver.xlsx`: saída estruturada da segunda etapa

## Privacidade

Este repositório foi preparado para não versionar:
- configuração local com caminhos da máquina;
- planilhas geradas;
- ambiente virtual.

Mantenha dados sensíveis em `infra/config.local.txt` e use `storage/` apenas para artefatos locais.
