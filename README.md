# 📊 Dashboard Interativo com Next.js + FastAPI

Este projeto é um **dashboard analítico interativo** com frontend em **Next.js 14** e backend em **FastAPI**, incluindo **upload de arquivos Excel**, visualização de **gráficos dinâmicos**, componentes reutilizáveis e design responsivo.

---

## 🚀 Funcionalidades

- **Upload de planilhas `.xlsx`** diretamente do frontend.
- Integração com **API FastAPI** para leitura de dados do Excel.
- **Chart Area Gradient** (gráfico de área com gradiente e tooltips).
- **Charts Bar Interativos** (barras com animação e interações).
- **Tabela de dados (Table Demo)** estilizada com componentes modernos.
- Estrutura de componentes reutilizáveis com **ShadCN UI**.
- **Responsivo** para desktop, tablet e mobile.
- Componente de **Sidebar** para navegação estruturada.
- CORS configurado para permitir comunicação entre frontend e backend local.
- Atualização automática dos dados após upload.

---

## 🧱 Tecnologias Utilizadas

### Frontend

- [Next.js 14](https://nextjs.org/)
- [TypeScript](https://www.typescriptlang.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [ShadCN UI](https://ui.shadcn.dev/)
- [Recharts](https://recharts.org/) – gráficos interativos

### Backend

- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/) – servidor ASGI
- [Pandas](https://pandas.pydata.org/) – leitura e manipulação de arquivos `.xlsx`
- `python-multipart` – para suporte a upload de arquivos

---

## 📁 Estrutura do Projeto

dashboard-nextjs-and-fastapi/
├── frontend/ # Projeto Next.js (app/)
│ ├── components/
│ │ ├── sidebar.tsx
│ │ ├── chart-area-gradient.tsx
│ │ ├── bar-charts.tsx
│ │ ├── table-demo.tsx
│ │ └── ...
│ └── app/
│ └── page.tsx
├── backend/
│ ├── main.py # FastAPI com rotas de upload e leitura de dados
│ └── dados.xlsx # Arquivo atualizado via upload


---

## ▶️ Como Rodar o Projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/dashboard-nextjs-and-fastapi.git
cd dashboard-nextjs-and-fastapi

```
### 2. Iniciar o Backend (FastAPI)
```
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

```
Certifique-se de ter o python-multipart instalado:
pip install python-multipart 

### 3. Iniciar o Frontend (Next.js)
```

cd frontend
npm install
npm run dev
```
Acesse: http://localhost:3000

## 📦 Upload de Arquivo
Clique no botão Upload Excel.

Selecione um arquivo .xlsx com colunas apropriadas (ex: month, desktop, mobile).

Após o upload, os gráficos serão atualizados automaticamente com os novos dados.

## 📈 Exemplo de Dados Esperados no Excel

| month | desktop | mobile |
| ----- | ------- | ------ |
| Jan   | 1200    | 900    |
| Feb   | 1500    | 1100   |
| ...   | ...     | ...    |


## 📌 Requisitos
Node.js >=18
Python >=3.8

Navegador moderno (Chrome, Firefox, Edge, etc.)


## 💡 Dica

Você pode gerar um arquivo `requirements.txt` com:
```
bash
pip freeze > requirements.txt


```
## 📌 Próximos passos

- Adicionar testes automatizados
- Melhorar autenticação e segurança
- Adicionar badges e imagens demonstrativas


## 📄 Licença
Este projeto está licenciado sob a MIT License.

## 🙋‍♂️ Contato
Desenvolvido por Igor Matheus
📧 [igorm.fonseca@hotmail.com]
🔗 LinkedIn [https://www.linkedin.com/in/igormatheus]