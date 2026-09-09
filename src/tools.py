# tools.py
import pandas as pd
from langchain_core.tools import tool

def _get_catalogo() -> pd.DataFrame:
    df_produtos = pd.read_csv("../data/products.csv")
    df_categorias = pd.read_csv("../data/categories.csv")
    df_promocoes = pd.read_csv("../data/promotions.csv")
    
    df_merged = df_produtos.merge(
        df_categorias, 
        left_on="category_id", 
        right_on="category_id", 
        suffixes=('', '_cat')
    )

    df_catalogo_final = df_merged.merge(
        df_promocoes,
        left_on="product_id",
        right_on="product_id",
        how="left",
        suffixes=('', '_promo')
    )

    return df_catalogo_final

@tool
def consultar_catalogo(
    termo_busca: str = None,
    preco_min: float = None, 
    preco_max: float = None) -> str:
    """Consulte esta ferramenta para buscar produtos na loja, verificar preços,
    especificações de instrumentos, estoque e promoções.
    Args:
        termo_busca: Um termo ou categoria para filtrar os produtos. Categorias no sistema estarão sempre no plural.
        preco_min: Preço mínimo para filtrar os produtos.
        preco_max: Preço máximo para filtrar os produtos.
    """
    df = _get_catalogo()
    if termo_busca:
        termo = termo_busca.lower()
        mascara_termo = (
            df['name'].str.lower().str.contains(termo, na=False) |
            df['name_cat'].str.lower().str.contains(termo, na=False)
        )
        df = df[mascara_termo]

    if preco_max is not None:
        df = df[df['price_brl'] <= preco_max] 
        
    if preco_min is not None:
        df = df[df['price_brl'] >= preco_min]

    if df.empty:
        return "Nenhum produto encontrado dentro dos critérios informados."

    # Ordena os resultados ordenando do mais barato para o mais caro
    df = df.sort_values(by='price_brl').head(5)
    
    linhas = []
    for _, row in df.iterrows():
        linhas.append(
            f"- **{row['name']}** | Categoria: {row['name_cat']} | Preço: R${row['price_brl']:.2f}"
        )
        
    return "\n".join(linhas)
