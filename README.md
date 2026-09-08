A Empório da Música é uma loja fictícia de instrumentos musicais localizada em Campo
Grande/MS. Hoje, o atendimento é inteiramente realizado pela equipe, que está
sobrecarregada com perguntas recorrentes: horários de funcionamento, status de pedido,
preço e disponibilidade de produtos, etc.

O objetivo deste projeto é prototipar um agente de atendimento que irá auxiliar a equipe no
atendimento. 
Para isso, a loja forneceu os seguintes materiais para uso do agente:
´data/*.csv´: Tabelas com dados da operação, como produtos, pedidos,
clientes e promoções
´data/políticas_da_loja.pdf´: Manual interno de políticas e procedimentos de atendimento ao
cliente.


### Decisões Técnicas e Estrutura do Projeto
1. Arquitetura do Agente: Orquestração via Tool Calling (ReAct)
Em vez de criar uma rede complexa de múltiplos agentes com um supervisor — o que adicionaria latência e custo desnecessários para este escopo — ou de engessar a lógica em regras condicionais (if/else), optei por um agente único baseado no padrão ReAct.

O modelo atua como orquestrador central: ele analisa a mensagem do cliente e decide, de forma autônoma, se pode responder diretamente (como em saudações ou dúvidas genéricas) ou se precisa acionar uma ferramenta específica para buscar informações reais antes de formular a resposta.

2. Escolha do Modelo: ChatMistralAI (mistral-small-latest)
Escolhi o mistral-small-latest (via SDK langchain-mistralai) por três razões práticas:

- Precisão em Chamadas de Função: Ele lida muito bem com a formatação JSON exigida pelo .bind_tools() do LangChain, sem "alucinar" argumentos.
- Qualidade em Português: Compreende nuances e mantém a persona de forma natural em PT-BR.
- Viabilidade Financeira: O plano gratuito de desenvolvedores da Mistral permite rodar este MVP com ótima velocidade e custo zero.

3. Arquitetura de Retrieval & Tratamento Híbrido de Dados
A arquitetura foi desenhada separando estritamente dados não estruturados de dados estruturados, pois aplicar busca vetorial (RAG) em tabelas relacionais pode resultar em perda de precisão em filtros exatos.

                         ┌──────────────────────────────┐
                         │      Entrada do Usuário      │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │   Agente Mistral (ReAct)     │
                         └──────────────┬───────────────┘
                                        │
         ┌──────────────────────────────┼──────────────────────────────┐
         ▼                              ▼                              ▼
┌──────────────────┐           ┌──────────────────────┐           ┌────────────────────┐
│  Tool 1: RAG     │           │   Tool 2: Catálogo   │           │   Tool 3: Pedidos  │
│  (PDF Políticas) │           │   (CSVs categories,  |           |   (CSVs customers, |
|                  |           | products, promotions)│           │orders, order_items)│
└────────┬─────────┘           └──────────┬───────────┘           └────────┬───────────┘
         │                                │                                │
         ▼                                ▼                                ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│ VectorStore      │             │ DataFrames       │             │ DataFrames       │
│ (FAISS/Chroma)   │             │ (Pandas)         │             │ (Pandas)         │
└──────────────────┘             └──────────────────┘             └──────────────────┘
Documentos Textuais (Políticas em PDF): Pretendo usar RAG clássico. O PDF é fatiado em trechos (RecursiveCharacterTextSplitter) e indexado em um banco vetorial local (FAISS/Chroma). A ferramenta busca os trechos relevantes por similaridade semântica para embasar respostas sobre regras da loja, trocas e garantias.

Dados Estruturados (6 CSVs de Produtos e Pedidos): Os arquivos serão carregados com Pandas, e as ferramentas expostas ao agente recebem parâmetros tipados. O modelo apenas extrai essas variáveis da conversa e delega a consulta para funções Python determinísticas, garantindo precisão nos valores retornados.

4. Estratégia de Prompting, Persona e Guardrails
Defini o agente com a persona de um atendente apaixonado por música: prestativo, descontraído e especialista nos produtos da loja. Para garantir que ele não fuja do escopo, vamos aplicar uma proteção em duas camadas:

- No Prompt, instruções explícitas indicam que o agente deve recusar educadamente qualquer assunto alheio à loja, sempre usando o tom de voz da persona para puxar o assunto de volta para instrumentos musicais.

- Na Infraestrutura, o agente simplesmente não possui ferramentas com acesso à internet ou a bases externas. Ele só consegue "enxergar" o que está no catálogo e nas políticas da loja.

5. Interface Visual e Deploy (Streamlit)
Escolhi o Streamlit por ser a forma mais rápida de entregar uma interface de chat funcional e pronta para uso, podendo aproveitando o st.session_state para manter o histórico da conversa.

Para a distribuição, pretendo configurar o deploy no Streamlit Cloud integrando as chaves de API (MISTRAL_API_KEY) via Secrets Management. No ambiente local, as chaves ficam isoladas no .env (ignorado pelo Git), garantindo que nenhuma credencial seja exposta no repositório.