# Empório da Música — Agente Virtual de Atendimento

Este repositório contém a implementação do **Tom**, um agente inteligente especialista no atendimento ao cliente da loja **Empório da Música**. Desenvolvido com **Streamlit** e **LangChain**. O assistente é capaz de consultar políticas internas (RAG em PDF), filtrar produtos e promoções (Pandas em CSVs) e acompanhar o status de pedidos.
 **Acesse o App Deployado:** `https://emporio-da-musica.streamlit.app/`

---

## Configuração de Ambiente e Execução

O projeto foi construído utilizando o **`uv`** para um gerenciamento de dependências rápido e determinístico, podendo ser executado via Streamlit Cloud ou rodar localmente.

### Rodar Localmente

Para executar localmente, você precisará configurar as chaves de API necessárias no ambiente.

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/emporio-da-musica.git
cd emporio-da-musica

```

2. **Configure as Variáveis de Ambiente:**
Crie um arquivo `.env` na raiz do projeto com as seguintes credenciais:
```env
MISTRAL_API_KEY="sua_chave_mistral"
CHAT_MODEL="mistral-small-latest"
HF_TOKEN="seu_token_huggingface"
MONGODB_URI="sua_connection_string_mongodb"

```

3. **Instale as dependências e rode a aplicação:**
* Caso utilize o **`uv`** (recomendado):
```bash
uv sync
uv run streamlit run app.py

```

* Caso prefira o **`pip`** convencional:
```bash
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate.ps1 no Windows
pip install -r requirements.txt
streamlit run app.py

```
(Nota: Para reindexar o PDF no MongoDB Atlas, execute `uv run py ingest.py`).

## Arquitetura do Sistema
A solução adota o padrão ReAct (Reasoning + Acting) com Tool Calling nativo.

Para evitar alucinações em dados críticos (como preços, estoque ou status de entrega), desacoplei a camada de raciocínio da camada de dados. O modelo atua como um orquestrador que identifica a intenção, executa chamadas determinísticas a ferramentas específicas e sintetiza a resposta final com base nos dados reais.

                  ┌─────────────────────────────────────────┐
                  │             Interface UI                │
                  │              (Streamlit)                │
                  └────────────────────┬────────────────────┘
                                       │ (Histórico + Prompt)
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │        Orquestrador ReAct / LLM         │
                  │    (Mistral AI via LangChain Protocol)  │
                  └──────┬─────────────┬─────────────┬──────┘
                         │             │             │
        ┌────────────────┘             │             └────────────────┐
        ▼                              ▼                              ▼
┌───────────────────┐        ┌───────────────────┐          ┌───────────────────┐
│consultar_politicas│        │ consultar_catalogo│          │ consultar_pedidos │
│  (RAG / Vector)   │        │      (Pandas)     │          │      (Pandas)     |
└─────────┬─────────┘        └─────────┬─────────┘          └─────────┬─────────┘
          │                            │                              │
          ▼                            ▼                              ▼
┌───────────────────┐        ┌───────────────────┐          ┌───────────────────┐
│   MongoDB Atlas   │        │ products.csv      │          │ customers.csv     │
│   Vector Search   │        │ categories.csv    │          │ orders.csv        │
│ (multilingual-e5) │        │ promotions.csv    │          │ order_items.csv   │
└───────────────────┘        └───────────────────┘          └───────────────────┘
---
Decisões de Engenharia & Raciocínio Técnico
* **Modelo & Provedor (`Mistral AI` / `open-mistral-7b`):** Apresenta bom suporte nativo a chamada determinística de funções, baixa latência e ótimo custo-benefício para fluxos conversacionais estruturados em português (utilizei apenas o tier gratuito).
Precision & Tool Calling: Escolhido por apresentar excelente taxa de acerto no cumprimento de schemas JSON e execução de function calling em português, combinando baixa latência e custo reduzido. A temperatura foi configurada em 0.2 para priorizar saídas determinísticas e evitar desvios no cumprimento do prompt.

* **Orquestração (`LangChain`):** Permite abstrair a passagem de mensagens, o vínculo de ferramentas (`bind_tools`) e a renderização do histórico no padrão `SystemMessage`, `HumanMessage`, `AIMessage` e `ToolMessage`.
* Bandeira de Segurança no Loop ReAct: Implementação de limite explícito de iterações (max_iterations = 3) no agente para prevenir chamadas redundantes ou loops infinitos em falhas de API.

* **Arquitetura de Retrieval (RAG Híbrido):**
* Para dados não estruturados (`politicas_da_loja.pdf`), foi utilizado o modelo de embeddings **`multilingual-e5-small`**, escolhido por ser um modelo pequeno e bem avaliado na MTEB para a tarefa de retrieval (chunks normalizados com o prefixo `passage:` na ingestão e `query:` na busca) integrado ao MongoDB Atlas Vector Search.
* Para dados estruturados (catálogo, estoque, promoções e pedidos em CSV), evitou-se o uso de RAG tradicional para prevenir alucinações de preços/quantidades. Em vez disso, foram criadas ferramentas determinísticas com Pandas fazendo cruzamento relacional (JOINs) em memória. Foram criadas duas funções distintas: uma para lidar com o cenário pré-venda -- catálogo, estoque, promoções -- e outra para o pós-venda (consulta de pedidos; status, data prevista de entrega, valor pago e mais detalhes).

* **Busca no Catálogo com Resiliência:** A ferramenta de busca no catálogo divide termos em múltiplos tokens e consulta de forma cumulativa tanto os nomes dos produtos quanto as categorias. Isso garante que buscas como `"violões nylon"` encontrem com precisão produtos que combinam a categoria "Violões" com o modelo "Nylon".

* **Estratégia de Prompt (Persona & Escopo):** O prompt do sistema define a persona do "Tom", um entusiasta prestativo e especialista no mundo da música. Ele possui travas estritas de segurança para recusar perguntas fora do escopo (evitando responder sobre assuntos alheios) e diretrizes para direcionar o cliente ao suporte humano (telefone e email da loja) caso as ferramentas não retornem dados suficientes para respondê-lo.

## Limitações Conhecidas e Próximos Passos

Por se tratar de um MVP voltado a um cenário técnico de teste, algumas simplificações foram adotadas. Com mais tempo de desenvolvimento, as seguintes melhorias poderiam ser priorizadas:

1. **Gestão da Janela de Contexto (Histórico):** Atualmente, todo o histórico de mensagens da sessão é enviado ao prompt. Em conversas muito longas, isso pode exceder a janela de contexto ou elevar custos/latência. *Solução futura:* Limitar o histórico por quantidade de turnos ou tamanho total de tokens (janela deslizante).
2. **Autenticação e Segurança em Pedidos:** A verificação de pedidos exige apenas o nome do cliente ou o ID do pedido. Em produção, seria indispensável exigir validações adicionais (CPF, e-mail ou confirmação via SMS/OTP).
3. **Múltiplos Itens por Pedido:** O agrupamento atual nas ferramentas assume 1 item por linha/pedido. Se fosse necessário, é possível adaptar a modelagem para listar um *array* de itens dentro de um mesmo `order_id`.
4. **Cálculo de Parcelamento e Financiamento:** Criaria uma ferramenta dedicada para simulação de pagamentos, permitindo calcular regras de parcelamento sem juros ou descontos no Pix.
5. **Automação de Prazos e Datas:** Uma *tool* utilitária de data/hora ajudaria o agente a calcular com exatidão prazos limite de devolução/troca (ex: comparar a data da entrega do pedido com a data atual para saber se os 30 dias de garantia ainda são válidos).
6. **Otimização de Latência:** Implementar chamadas assíncronas para consultas de ferramentas e aplicar *cache* (`st.cache_data`) na leitura inicial dos DataFrames do Pandas.
---

## Uso de Assistentes de Código

A construção deste projeto contou com o apoio de Inteligência Artificial (Gemini) atuando sobretudo como um apoio técnico. A interação ocorreu de forma contínua e iterativa ao longo de todo o desenvolvimento:

* **Iteração e Validação de Soluções:** Discussão aberta sobre caminhos de arquitetura, testando ideias e ajustando a abordagem técnica à medida que o projeto evoluía.
* **Depuração e Resolução de Problemas:** Uso para diagnóstico de erros, identificação de gargalos no código e correção de falhas durante os testes.
* **Refinamento Contínuo:** Apoio na otimização de rotinas, e polimento do projeto, garantindo uma entrega mais robusta.