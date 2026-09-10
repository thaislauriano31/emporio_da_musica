from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from settings import AppSettings, missing_required_env
from rag import consultar_politicas
from tools import consultar_catalogo, consultar_pedidos

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
- Seja simpático, mas sem ser prolixo.
- Evite adicionar muita formatação no texto como negrito ou itálico para evitar problemas na renderização do chat.
- Nunca invente itens ou serviços que não foram confirmados pelas suas ferramentas ou base de dados.
- Nunca deixe uma resposta final em aberto. Se não souber a resposta, informe que não tem essa informação e sugira que o cliente entre em contato com o suporte da loja.

[USO DE FERRAMENTAS]
- Para perguntas sobre regras, trocas, garantias ou frete: use `consultar_politicas`.
- Para perguntas sobre produtos, preços, marcas, categorias: use `consultar_catalogo`. 
Nesse caso, gere todos os termos_busca que julgar relevantes e chame a função 1x para cada termo.
Se a pergunta for geral sobre todos os produtos, envie termo_busca vazio para receber a lista completa.
- Para perguntas sobre promoções e estoque: use `consultar_catalogo` com os filtros de preço e categoria adequados. Essas informações são retornadas ao consultar os produtos.
- Para perguntas sobre pedidos, rastreio e status: use `consultar_pedidos`, mas peça sempre que o cliente forneça o nome completo ou id do pedido para poder consultar.
- Você pode acionar múltiplas ferramentas ou fazer várias consultas seguidas se a dúvida do cliente exigir.
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

        self.tools = [consultar_politicas, consultar_catalogo, consultar_pedidos]
        self.tools_map = {tool.name: tool for tool in self.tools}
        self.model_with_tools = self.model.bind_tools(self.tools)

    def responder(self, pergunta: str, historico: str) -> str:
        """Recebe o histórico de mensagens e retorna a resposta da LLM.
        Se a LLM decidir chamar uma ferramenta, ela retornará uma ou mais solicitações de tool_call.
        """
        mensagens = [SystemMessage(content=SYSTEM_PROMPT)]
        
        if historico:
            for msg in historico:
                if msg["role"] == "user":
                    mensagens.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    mensagens.append(AIMessage(content=msg["content"]))
        
        if not historico or historico[-1]["content"] != pergunta:
            mensagens.append(HumanMessage(content=pergunta))

        max_iterations = 3
        for _ in range(max_iterations):
            resposta = self.model_with_tools.invoke(mensagens)
            mensagens.append(resposta)
            
            if not resposta.tool_calls:
                return resposta.content
            
            for tool_call in resposta.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]
                print(f"LLM solicitou a ferramenta {tool_name} com argumentos: {tool_args}")
                tool_func = self.tools_map.get(tool_name)
                if tool_func:
                    resultado_tool = tool_func.invoke(tool_args)
                else:
                    resultado_tool = f"Erro: Ferramenta {tool_name} não encontrada."
                
                if not resultado_tool or not str(resultado_tool).strip():
                    return "Desculpe, não consegui obter informações relevantes para responder sua pergunta. Por favor tente reformular ou entre em contato com a loja."

                mensagens.append(
                    ToolMessage(
                        content=str(resultado_tool),
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                )
        
        # Caso atinja o limite máximo de iterações por segurança
        return "Consultei os sistemas, mas a busca foi muito complexa. Como posso ajudar com uma pergunta mais específica?"