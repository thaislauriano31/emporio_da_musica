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
MISTRAL_API_KEY="sua_chave_mistral_aqui"
CHAT_MODEL="mistral-small-latest"
HF_TOKEN="seu_token_huggingface_aqui"

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
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
pip install -r requirements.txt
streamlit run app.py

```

---

## Justificativa das Decisões Técnicas

* **LLM & Provedor (`Mistral AI` / `mistral-small-latest`):** Apresenta excelente suporte nativo a *Tool Calling* (chamada determinística de funções), baixa latência e ótimo custo-benefício para fluxos conversacionais estruturados em português.
* **Orquestração (`LangChain`):** Permite abstrair a passagem de mensagens, o vínculo de ferramentas (`bind_tools`) e a renderização do histórico no padrão `SystemMessage`, `HumanMessage`, `AIMessage` e `ToolMessage`.
* **Arquitetura de Retrieval (RAG Híbrido):**
* Para dados não estruturados (`politicas_da_loja.pdf`), foi utilizado o modelo de embeddings **`multilingual-e5-small`**, escolhido com base na MTEB (com o prefixo `passage:` na ingestão e `query:` na busca) salvo em um índice **FAISS** local.
* Para dados estruturados (catálogo, estoque, promoções e pedidos em CSV), evitou-se o uso de RAG tradicional para prevenir alucinações de preços/quantidades. Em vez disso, foram criadas **ferramentas determinísticas em Pandas** com cruzamento relacional (*JOINs*) em memória.


* **Busca no Catálogo com Resiliência em Python:** A ferramenta de busca no catálogo divide termos em múltiplos *tokens* (palavras separadas) e consulta de forma cumulativa tanto os nomes dos produtos quanto as categorias. Isso garante que buscas como `"violões nylon"` encontrem com precisão produtos que combinam a categoria "Violões" com o modelo "Nylon".
* **Estratégia de Prompt (Persona & Escopo):** O prompt do sistema define a persona do "Tom", um entusiasta prestativo e especialista no mundo da música. Ele possui travas estritas de segurança para recusar perguntas fora do escopo (evitando responder sobre assuntos alheios) e diretrizes para direcionar o cliente ao suporte humano caso os sistemas não retornem dados.


## Limitações Conhecidas e Próximos Passos

Por se tratar de um MVP voltado a um cenário técnico de teste, algumas simplificações foram adotadas. Com mais tempo de desenvolvimento, as seguintes melhorias seriam priorizadas:

1. **Gestão da Janela de Contexto (Histórico):** Atualmente, todo o histórico de mensagens da sessão é enviado ao prompt. Em conversas muito longas, isso pode exceder a janela de contexto ou elevar custos/latência. *Solução futura:* Limitar o histórico por quantidade de turnos ou tamanho total de tokens (janela deslizante).
2. **Autenticação e Segurança em Pedidos:** A verificação de pedidos aceita apenas o nome do cliente ou o ID do pedido. Em produção, seria indispensável exigir validações adicionais (CPF, e-mail ou confirmação via SMS/OTP).
3. **Múltiplos Itens por Pedido:** O agrupamento atual nas ferramentas assume 1 item principal por linha/pedido. Ajustaria a modelagem para listar um *array* de itens dentro de um mesmo `order_id`.
4. **Cálculo de Parcelamento e Financiamento:** Criaria uma ferramenta dedicada para simulação de pagamentos, permitindo calcular regras de parcelamento sem juros ou descontos no Pix.
5. **Automação de Prazos e Datas:** Uma *tool* utilitária de data/hora ajudaria o agente a calcular com exatidão prazos limite de devolução/troca (ex: comparar a data da entrega do pedido com a data atual para saber se os 30 dias de garantia ainda são válidos).
6. **Otimização de Latência:** Implementar chamadas assíncronas para consultas de ferramentas e aplicar *cache* (`st.cache_data`) na leitura inicial dos DataFrames do Pandas.

---

## Workflow e Uso de Assistentes de Código

O desenvolvimento deste projeto contou com o apoio assistido de IA (**Gemini**) atuando como um acelerador de desenvolvimento nas seguintes etapas do workflow:

* **Estruturação de Código e ReAct:** Discussão da arquitetura do loop de *Tool Calling* e garantia do protocolo de IDs de ferramentas (`tool_call_id`) exigido pela API do Mistral.
* **Manipulação e Sanitização de DataFrames:** Elaboração da lógica de tratamento de strings no Pandas (quebra de tokens e busca cumulativa em colunas de nome e categoria).