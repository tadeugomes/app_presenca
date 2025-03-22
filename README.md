# Sistema de Registro de Presença

Sistema para registro de presença em aulas da Especialização em Gestão Portuária.

## Configuração

1. Clone o repositório:
```bash
git clone [URL_DO_SEU_REPOSITORIO]
cd [NOME_DO_DIRETORIO]
```

2. Crie um ambiente virtual e instale as dependências:
```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
- Crie um arquivo `.env` na raiz do projeto
- Adicione as seguintes variáveis:
```
GOOGLE_SHEETS_CREDENTIALS='seu_json_de_credenciais_aqui'
SPREADSHEET_ID='seu_id_da_planilha_aqui'
```

4. Configure o calendário:
- Adicione o arquivo `calendario_pos.ics` na raiz do projeto

## Executando o sistema

Para executar o sistema, use o comando:
```bash
streamlit run app.py
```

## Notas de Segurança

- Nunca compartilhe ou commite o arquivo `.env` ou arquivos de credenciais
- Mantenha suas credenciais do Google Sheets em segurança
- O arquivo `.gitignore` está configurado para excluir arquivos sensíveis 