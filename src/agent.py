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

[USO DE FERRAMENTAS]
- Para perguntas sobre regras, trocas, garantias ou frete: use `consultar_politicas`.
- Para perguntas sobre produtos, preços, marcas, categorias e estoque: use `consultar_catalogo`.
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
        Se a LLM decidir chamar uma ferramenta, ela retornará uma solicitação de tool_call.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("user", "{input}")
        ])
        
        chain = prompt | self.model_with_tools
        
        mensagens = [HumanMessage(content=pergunta)]
        resposta_inicial = chain.invoke({"input": pergunta})
        
        if resposta_inicial.tool_calls:
            # Para cada tool solicitada, executa a função Python correspondente
            for tool_call in resposta_inicial.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                tool_func = self.tools_map[tool_name]
                resultado_tool = tool_func.invoke(tool_args)
                
                print(resultado_tool)
                
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


if __name__ == "__main__":
    bot = LLM(settings=AppSettings())
    
    pergunta_teste = "Me arrependi da minha compra, posso devolver meu pedido?"
    print(f"PERGUNTA: {pergunta_teste}\n")
    
    resposta = bot.responder(pergunta_teste)
    print("\nRESPOSTA FINAL DO TOM:")
    print(resposta)  