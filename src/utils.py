from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATHS = [
    BASE_DIR / "infra" / "config.local.txt",
    BASE_DIR / "infra" / "config.txt",
]


def load_config(config_paths: list[Path] | None = None) -> dict[str, str]:
    config = {}
    paths = config_paths or DEFAULT_CONFIG_PATHS

    for config_path in paths:
        if not config_path.exists():
            continue

        with open(config_path, "r", encoding="utf-8") as arquivo:
            for linha in arquivo:
                linha = linha.strip()

                if not linha or linha.startswith("#") or "=" not in linha:
                    continue

                chave, valor = linha.split("=", 1)
                config[chave.strip()] = valor.strip()

    return config


def get_config_value(variavel: str) -> str:
    config = load_config()
    valor = config.get(variavel)

    if not valor:
        raise KeyError(
            f"Configuracao '{variavel}' nao encontrada em infra/config.local.txt ou infra/config.txt."
        )

    return valor


def resolve_project_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (BASE_DIR / path).resolve()
