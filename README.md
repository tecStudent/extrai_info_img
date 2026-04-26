# Extrator de alertas por OCR

Projeto para transformar prints de alertas salvos em uma pasta em dados estruturados.

O fluxo atual funciona assim:

1. O script lê imagens `.png` de uma pasta local.
2. Aplica pré-processamento para melhorar o OCR.
3. Extrai o texto dos prints com `easyocr`.
4. Organiza os dados em planilhas Excel.
5. Faz uma segunda etapa de normalização para campos específicos de alertas.

## Estrutura

- `src/extrai_data_png.py`: lê os prints e gera a planilha bruta `raw.xlsx`.
- `src/formata_coluna.py`: lê a planilha bruta e gera a planilha tratada `silver.xlsx`.
- `src/utils.py`: utilitários de configuração e caminhos.
- `infra/config.txt`: configuração pública de exemplo.
- `infra/config.local.txt`: configuração local real, não versionada.

## Configuração

1. Crie o ambiente virtual e instale as dependências:

```bash
pip install -r requirements.txt
```

2. Copie `infra/config.txt` para `infra/config.local.txt`.

3. Ajuste os caminhos no arquivo local.

Exemplo:

```txt
PASTA_IMAGENS=storage/input_images
ARQUIVO_SAIDA=storage
```

## Como executar

Gerar a base bruta:

```bash
python src/extrai_data_png.py
```

Gerar a base estruturada:

```bash
python src/formata_coluna.py
```

## Privacidade

Este repositório foi preparado para publicação sem expor:

- caminhos pessoais da máquina local;
- prints reais usados em produção;
- planilhas geradas com dados extraídos.

Os arquivos locais sensíveis devem ficar fora do versionamento em `infra/config.local.txt` e `storage/`.
