# Build Desktop

## Desenvolvimento

Instalar dependências:

```bash
pip install -r requirements.txt
```

Executar desktop app:

```bash
python app.py
```

Streamlit permanece disponível apenas como protótipo:

```bash
streamlit run src/sidct/ui/streamlit_app.py
```

## PyInstaller

Script recomendado:

```bash
python scripts/build_desktop.py
```

Comando equivalente:

```bash
pyinstaller --noconfirm --windowed --name SIDCT --distpath dist_desktop_adaptive_v7 --workpath build_desktop --paths src --add-data "project_profiles.yaml;." --add-data "service_matrix.yaml;." --add-data "standards_registry.yaml;." --add-data "assumptions.yaml;." --add-data "system_pipe_mapping.yaml;." --add-data "form_behavior_matrix.yaml;." --add-data "data/catalogs;data/catalogs" --add-data "data/templates;data/templates" app.py
```

## Nota

PySide6 deve estar instalado no ambiente de build. O executável gerado fica em `dist_desktop_adaptive_v7/SIDCT`.
