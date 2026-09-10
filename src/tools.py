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

    # Transofrma 'is_active' em bool
    df_catalogo_final['is_active'] = df_catalogo_final['is_active'].fillna(0).astype(bool)

    # Ajusta o preço com desconto se houver promoção ativa
    df_catalogo_final['discount_percent'] = df_catalogo_final['discount_percent'].fillna(0)
    if 'is_active' in df_catalogo_final.columns:
        df_catalogo_final['price_brl'] = df_catalogo_final.apply(
            lambda row: row['price_brl']*((100-row['discount_percent'])/100) if row['is_active'] else row['price_brl'], 
            axis=1
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
        palavras = termo_busca.lower().split()
        for palavra in palavras:
            mascara = (
                df['name'].str.lower().str.contains(palavra, na=False) |
                df['name_cat'].str.lower().str.contains(palavra, na=False)
            )
        df = df[mascara]

    if preco_max is not None:
        df = df[df['price_brl'] <= preco_max] 
        
    if preco_min is not None:
        df = df[df['price_brl'] >= preco_min]

    if df.empty:
        return None

    # Ordena os resultados ordenando do mais barato para o mais caro
    df = df.sort_values(by='price_brl')
    
    linhas = []
    for _, row in df.iterrows():
        linhas.append(
            f"- **{row['name']}** | Categoria: {row['name_cat']} | Preço: R${row['price_brl']:.2f} | Estoque: {row['stock_quantity']} | Promoção: {row['is_active']}"
        )
        
    return "\n".join(linhas)