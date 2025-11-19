# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================
# 1. Carregar e preparar dados
# ==========================

@st.cache_data
def load_data(path: str):
    # Lê a primeira aba da planilha
    df = pd.read_excel(path, sheet_name=0)

    # Renomeia colunas para algo mais "amigável" no código
    df = df.rename(columns={
        "Data da Venda": "data_venda",
        "Data de Emissão da NF": "data_nf",
        "Cliente": "cliente",
        "Vendedor Responsável": "vendedor",
        "Tipo de Solução": "tipo_solucao",
        "Descrição do Projeto": "descricao_projeto",
        "Valor da Venda (R$)": "valor_venda",
        "OS.": "os",
        "Proposta": "proposta",
    })

    # Garante que as datas estão em datetime
    df["data_venda"] = pd.to_datetime(df["data_venda"])
    df["data_nf"] = pd.to_datetime(df["data_nf"])

    # Garante que o valor é numérico
    df["valor_venda"] = pd.to_numeric(df["valor_venda"], errors="coerce")

    # Cria colunas de apoio
    df["ano"] = df["data_venda"].dt.year
    df["mes"] = df["data_venda"].dt.month
    df["ano_mes"] = df["data_venda"].dt.to_period("M").astype(str)

    return df

# ==========================
# 2. App Streamlit
# ==========================

st.set_page_config(
    page_title="Dashboard de Vendas ETO - ARV",
    layout="wide"
)

st.title("📊 Dashboard de Vendas - Modelo ETO / B2B (Alto Ticket)")

# Caminho do arquivo (ajuste conforme sua pasta)
file_path = "/app/data/ESTUDO-VENDAS.xlsx"

df = load_data(file_path)

# ==========================
# 3. Filtros laterais
# ==========================

st.sidebar.header("Filtros")

anos = sorted(df["ano"].dropna().unique())
ano_selecionado = st.sidebar.multiselect(
    "Ano da Venda", options=anos, default=anos
)

vendedores = sorted(df["vendedor"].dropna().unique())
vendedor_selecionado = st.sidebar.multiselect(
    "Responsável", options=vendedores, default=vendedores
)

tipos = sorted(df["tipo_solucao"].dropna().unique())
tipo_selecionado = st.sidebar.multiselect(
    "Tipo de Solução", options=tipos, default=tipos
)

clientes = sorted(df["cliente"].dropna().unique())
cliente_selecionado = st.sidebar.multiselect(
    "Cliente", options=clientes, default=clientes
)

# Aplica filtros
df_filtrado = df[
    (df["ano"].isin(ano_selecionado)) &
    (df["vendedor"].isin(vendedor_selecionado)) &
    (df["tipo_solucao"].isin(tipo_selecionado)) &
    (df["cliente"].isin(cliente_selecionado))
].copy()

# ==========================
# 4. KPIs principais
# ==========================

total_vendas = df_filtrado["valor_venda"].sum()
qtd_vendas = df_filtrado.shape[0]
ticket_medio = total_vendas / qtd_vendas if qtd_vendas > 0 else 0

# Ciclo médio (se quiser, entre data_venda e data_nf)
df_filtrado["lead_time_dias"] = (df_filtrado["data_nf"] - df_filtrado["data_venda"]).dt.days
ciclo_medio = df_filtrado["lead_time_dias"].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Faturamento Total", f"R$ {total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col2.metric("📦 Qtde de Vendas", int(qtd_vendas))
col3.metric("🎯 Ticket Médio", f"R$ {ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col4.metric("⏱ Ciclo Médio (dias)", f"{ciclo_medio:.1f}" if not pd.isna(ciclo_medio) else "-")

st.markdown("---")

# ==========================
# 5. Gráfico 1 – Faturamento por mês (linha)
# ==========================

st.subheader("📈 Faturamento por mês (Ano-Mês)")

if not df_filtrado.empty:
    df_mes = (
        df_filtrado
        .groupby("ano_mes", as_index=False)["valor_venda"]
        .sum()
        .sort_values("ano_mes")
    )

    fig_mes = px.line(
        df_mes,
        x="ano_mes",
        y="valor_venda",
        markers=True,
        labels={"ano_mes": "Ano-Mês", "valor_venda": "Faturamento (R$)"},
        title="Faturamento ao longo do tempo"
    )
    fig_mes.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_mes, use_container_width=True)
else:
    st.info("Nenhum dado para os filtros selecionados.")

# ==========================
# 6. Gráfico 2 – Faturamento por Tipo de Solução (barra)
# ==========================

st.subheader("🏗 Faturamento por Tipo de Solução")

if not df_filtrado.empty:
    df_tipo = (
        df_filtrado
        .groupby("tipo_solucao", as_index=False)["valor_venda"]
        .sum()
        .sort_values("valor_venda", ascending=False)
    )

    fig_tipo = px.bar(
        df_tipo,
        x="tipo_solucao",
        y="valor_venda",
        labels={"tipo_solucao": "Tipo de Solução", "valor_venda": "Faturamento (R$)"},
        title="Faturamento por Tipo de Solução"
    )
    fig_tipo.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig_tipo, use_container_width=True)
else:
    st.info("Nenhum dado para os filtros selecionados.")

# ==========================
# 7. Gráfico 3 – Top 10 Clientes (barra horizontal)
# ==========================

st.subheader("👥 Top 10 Clientes por Faturamento")

if not df_filtrado.empty:
    df_cliente = (
        df_filtrado
        .groupby("cliente", as_index=False)["valor_venda"]
        .sum()
        .sort_values("valor_venda", ascending=False)
        .head(10)
    )

    fig_cliente = px.bar(
        df_cliente,
        x="valor_venda",
        y="cliente",
        orientation="h",
        labels={"cliente": "Cliente", "valor_venda": "Faturamento (R$)"},
        title="Top 10 Clientes"
    )
    fig_cliente.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_cliente, use_container_width=True)
else:
    st.info("Nenhum dado para os filtros selecionados.")

# ==========================
# 8. Gráfico 4 – Faturamento por Responsável
# ==========================

st.subheader("👤 Faturamento por Responsável")

if not df_filtrado.empty:
    df_vendedor = (
        df_filtrado
        .groupby("vendedor", as_index=False)["valor_venda"]
        .sum()
        .sort_values("valor_venda", ascending=False)
    )

    fig_vendedor = px.bar(
        df_vendedor,
        x="vendedor",
        y="valor_venda",
        labels={"vendedor": "Responsável", "valor_venda": "Faturamento (R$)"},
        title="Faturamento por Responsável (Comercial)"
    )
    st.plotly_chart(fig_vendedor, use_container_width=True)
else:
    st.info("Nenhum dado para os filtros selecionados.")

# ==========================
# 9. Tabela detalhada
# ==========================

st.subheader("📄 Tabela de Vendas (Detalhes)")
st.dataframe(
    df_filtrado[[
        "data_venda",
        "data_nf",
        "cliente",
        "vendedor",
        "tipo_solucao",
        "descricao_projeto",
        "valor_venda",
        "os",
        "proposta"
    ]].sort_values("data_venda", ascending=False),
    use_container_width=True
)
