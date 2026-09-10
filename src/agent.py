from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, ToolMessage
from settings import AppSettings, missing_required_env
from rag import consultar_politicas
from tools import consultar_catalogo

SYSTEM_PROMPT = """
Você é Tom, um atendente da loja de instrumentos musicais Empório da Música.
É apaixonado por música, prestativo, atencioso, e especialista nos produtos da loja.

[REGRAS DE ESCOPO E SEGURANÇA]
1. Seu conhecimento e atendimento se limitam estritamente a: instrumentos musicais, acessórios de som, equipamentos de áudio, políticas da loja e status de pedidos.
2. Se o cliente perguntar sobre qualquer assunto fora desse escopo:
   - Recuse educadamente o assunto mantendo o tom da persona.
   - Nunca tente inventar conexões com a loja ou oferecer produtos fictícios.
   - Reencaminhe o cliente para o universo dos instrumentos musicais.

[DIRETRIZES DE RESPOSTA]
- Mantenha respostas diretas, claras e sem rodeios.
- Seja simpático, mas sem ser excessivamente prolixo.
- Nunca invente itens ou serviços que não foram confirmados pelas suas ferramentas ou base de dados.
- Nunca deixe uma resposta final em aberto. Se não souber a resposta, informe que não tem essa informação e sugira que o cliente entre em contato com o suporte da loja.

[USO DE FERRAMENTAS]
- Para perguntas sobre regras, trocas, garantias ou frete: use `consultar_politicas`.
- Para perguntas sobre produtos, preços, marcas, categorias e estoque: use `consultar_catalogo`. Nesse caso, gere todos os termos_busca que julgar relevantes e chame a função 1x para cada termo.
- Se uma pergunta misturar assuntos de política da loja e produtos, use ambas as ferramentas.
"""

class LLM:
    def __init__(self, settings: AppSettings):
        self.model = self.build_llm(settings)
    
    def build_llm(self, settings: AppSettings) -> ChatMistralAI:
        if missing_required_env(settings):
            raise ValueError("MISTRAL_API_KEY não encontrada. Verifique o arquivo .env na raiz do projeto.")

        self.model = ChatMistralAI(
            model=settings.chat_model,
            api_key=settings.mistral_api_key,
            temperature=0.2,
        )

        self.tools = [consultar_politicas, consultar_catalogo]
        self.tools_map = {tool.name: tool for tool in self.tools}
        self.model_with_tools = self.model.bind_tools(self.tools)

    def responder(self, pergunta: str) -> str:
        """Recebe o histórico de mensagens e retorna a resposta da LLM.
        Se a LLM decidir chamar uma ferramenta, ela retornará uma ou mais solicitações de tool_call.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("user", "{input}")
        ])
        
        chain = prompt | self.model_with_tools
        
        resposta_inicial = chain.invoke({"input": pergunta})
        print("DEBUG INICIO")
        print(resposta_inicial)
        if resposta_inicial.tool_calls:
            # Para cada tool solicitada, executa a função Python correspondente
            for tool_call in resposta_inicial.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                tool_func = self.tools_map[tool_name]
                resultado_tool = tool_func.invoke(tool_args)
                print(f"DEBUG RESULTADO TOOL {tool_name}:")
                print(resultado_tool)
                if not resultado_tool:
                    return "Desculpe, não consegui obter informações relevantes para sua pergunta. Tente reformular sua pergunta ou entre em contato com o suporte da loja."
                
                # Passando o contexto obtido pela ferramenta
                prompt_sintese = ChatPromptTemplate.from_messages([
                    ("system", SYSTEM_PROMPT),
                    ("user", "{input}"),
                    ("system", f"Resultado obtido da consulta ao banco/sistema: {resultado_tool}\nCom base nesses dados, responda ao cliente.")
                ])
                chain_sintese = prompt_sintese | self.model_with_tools
                resposta_final = chain_sintese.invoke({"input": pergunta})
                return resposta_final.content
                
        return resposta_inicial.content 