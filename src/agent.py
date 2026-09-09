from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from settings import AppSettings, missing_required_env
from rag import consultar_politicas

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

        self.tools = [consultar_politicas]
        self.model_with_tools = self.model.bind_tools(self.tools)

    def processar_mensagem(self, mensagens: list):
        """Recebe o histórico de mensagens e retorna a resposta da LLM.
        Se a LLM decidir chamar uma ferramenta, ela retornará uma solicitação de tool_call.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("placeholder", "{messages}")
        ])
        
        chain = prompt | self.model_with_tools
        return chain.invoke({"messages": mensagens})

if __name__ == "__main__":
    settings = AppSettings()
    agent = LLM(settings)   