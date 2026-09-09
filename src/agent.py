from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from settings import AppSettings, missing_required_env

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

        return ChatMistralAI(
            model=settings.chat_model,
            api_key=settings.mistral_api_key,
            temperature=0.2,
        )

    def generate_response(self, user_input: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{input}")
        ])
        chain = prompt | self.model
        response = chain.invoke({"input": user_input})
        return response.content

if __name__ == "__main__":
    settings = AppSettings()
    llm = LLM(settings) 
    resposta_saudacao = llm.generate_response("Olá, tudo bem? Quem é você?")
    print("TESTE 1: Saudação")
    print(resposta_saudacao)

    resposta_fora_escopo = llm.generate_response("Qual é a receita de um bolo de cenoura?")
    print("\nTeste 2: Fora do Escopo")
    print(resposta_fora_escopo)