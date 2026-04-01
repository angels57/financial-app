# Plantilla Base Python

Este proyecto fue generado usando `personal-cli`. Está configurado con las mejores prácticas modernas de Python, con gestión inteligente de dependencias mediante `uv`, validación y linters configurados, y listo para ser adaptado a aplicaciones robustas, de consola (CLI), scripts avanzados o APIs.

## 🚀 Inicio Rápido

### Requisitos Previos
* [Python 3.12+](https://www.python.org/)
* [uv](https://github.com/astral-sh/uv) (Gestor de dependencias ultrarrápido escrito en Rust)
* [pre-commit](https://pre-commit.com/) (Recomendado para comprobaciones antes de cada commit)

### Desarrollo Local

1. Instalar las dependencias y sincronizar entorno:
   ```bash
   uv sync
   ```

2. Ejecutar la aplicación:
   ```bash
   uv run python app/main.py
   ```

3. (Opcional) Instalar hooks de validación en tu repositorio local Git:
   ```bash
   pre-commit install
   ```

4. Ejecutar linters manualmente o validar formatos:
   ```bash
   uv run ruff check .
   uv run ruff format .
   ```

5. Ejecutar la suite de pruebas:
   ```bash
   uv run pytest
   ```

## 📁 Estructura del Proyecto

La estructura promueve que el código pueda escalar sin perder de vista los estándares (basado parcialmente en Clean Architecture / Modular):

```text
├── app/
│   ├── core/         # Configuración central (ej. variables de entorno, sistema de logging)
│   ├── domain/       # Modelos de dominio y entidades de la lógica (Agregraciones / Tipo)
│   ├── services/     # Lógica de negocio (casos de uso de tu aplicación)
│   ├── utils/        # Herramientas misceláneas y helpers genéricos
│   └── main.py       # Archivo de entrada de ejecución del código
├── config/           # Contiene recursos ajenos directamente a las clases Python
├── tests/            # Tests unitarios y de integración mediante pytest
├── .pre-commit-config.yaml # Ganchos del repositorio (linting automático)
├── .python-version   # Señaliza a 'uv' la versión a usar para este proyecto base
├── uv.lock           # Resolve de dependencias emulando un requeriments.txt fijado
└── pyproject.toml    # Metadatos del proyecto y configuraciones globales (Ruff, pytest)
```

## 🛠️ Herramientas y Patrones Listos para Usarse

* **pydantic-settings**: Se incluye en `settings.py` para cargar de manera estrictamente tipada las variables de tu archivo `.env`. Si falta un parámetro obligatorio o tiene un tipo incorrecto, la app caerá a tiempo e intencionalmente señalando qué error corregir.
* **Logging Estructurado**: Expone un logger central (`app/core/logging.py`) con formato estético para tu consola en desarrollo (vía `rich`), y un format JSON en archivo paralelo para fácil ingestión en producción.
* **uv**: Un gestor completo escrito en Rust. Un `uv run` asegura que siempre corras el script dentro del entorno virtual exacto de la aplicación abstraído del sistema operativo.
* **Ruff**: En el `pyproject.toml` se configuró Ruff abarcando no solo sus reglas elementales (como flake8), sino también resolventes de sintaxis perezosas o anticuadas (`pyupgrade`), lo que fuerza el código al estándar de modernidad Python actual.
