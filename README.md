📲 WhatsApp API Manager (Flask)

Aplicação em Flask para integração com a API do WhatsApp Business (Meta), permitindo:

📩 Envio de mensagens via template

🧩 Criação de templates

📥 Recebimento de eventos via webhook

📄 Interface básica com páginas HTML

🚀 Tecnologias utilizadas

Python 3

Flask

Requests

API Graph (WhatsApp Business)

📁 Estrutura do projeto
/project
│── app.py
│── /templates
│    ├── index.html
│    ├── privacy.html
│    ├── terms.html
│    ├── send.html
│    └── create_template.html
⚙️ Configuração
1. Clone o projeto
git clone https://github.com/ekballo.git
cd seu-repo
2. Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
3. Instale as dependências
pip install flask requests
🔐 Variáveis importantes

No arquivo app.py, configure:

OBS: Solitar dados abaixo ao gestor ou criar app no developers meta

VERIFY_TOKEN = "seu_token_de_verificacao"
WHATSAPP_TOKEN = "seu_token_da_meta"
PHONE_NUMBER_ID = "seu_phone_number_id"
BUSINESS_ACCOUNT_ID = "seu_business_account_id"
▶️ Executando o projeto
python app.py

A aplicação estará disponível em:

http://localhost:5000
🔗 Rotas disponíveis
📄 Páginas
Rota	Descrição
/	Página inicial
/privacy	Política de privacidade
/terms	Termos de uso
/send	Página de envio de mensagens
/create-template	Página de criação de templates
📡 API
📥 Webhook (Meta)

GET /webhook → Verificação do webhook

POST /webhook → Recebimento de eventos

📩 Enviar Template

POST /send-template

{
  "numero": "5511999999999",
  "template": "nome_do_template"
}
🧩 Criar Template

POST /create-template-api

{
  "name": "meu_template",
  "language": "pt_BR",
  "category": "MARKETING",
  "header": "Título",
  "message": "Mensagem principal",
  "button": "https://link.com"
}
📋 Listar Templates

GET /get-templates

📲 Integração com WhatsApp (Meta)

Esta aplicação utiliza a API oficial da Meta via Graph API.

Para funcionamento completo, é necessário:

Conta no Meta Business Manager

App configurado no Meta for Developers

Número aprovado no WhatsApp Business API

⚠️ Observações importantes

Templates precisam ser aprovados pela Meta antes do uso

O número deve estar no formato internacional (ex: 5511999999999)

Tokens possuem validade e podem expirar

Webhook deve estar em HTTPS em produção

🔒 Segurança

⚠️ Nunca exponha seus tokens em repositórios públicos

Recomendado usar:

Variáveis de ambiente (.env)

Serviços como Docker Secrets ou Vault
