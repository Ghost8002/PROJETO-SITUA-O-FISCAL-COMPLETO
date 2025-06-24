import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Dashboard Fiscal", layout="wide")

st.title("Dashboard Fiscal - Situação de Parcelamento")

st.markdown("""
Este dashboard permite analisar e exportar os resultados do processamento dos PDFs fiscais.
Utilize os filtros abaixo para refinar a visualização dos dados.
""")

dados = st.session_state.get('dados_processados', None)

if not dados or not dados.get('all_results'):
    st.warning("Nenhum dado processado encontrado. Por favor, faça o upload e processamento dos PDFs na página inicial.")
    st.stop()

all_results = dados['all_results']
matched_files = dados.get('matched_files', [])
df = pd.DataFrame([{
    'Empresa': r['empresa'],
    'Parcelamento RF': 'Sim' if r['rf'] else 'Não',
    'Parcelamento PGFN': 'Sim' if r['pgfn'] else 'Não'
} for r in all_results])

# Busca e download de PDF por empresa
st.markdown("---")
st.subheader("Buscar e baixar PDF de uma empresa específica")
empresas = sorted(df['Empresa'].unique())
empresa_selecionada = st.selectbox("Selecione a empresa para baixar o PDF renomeado:", ["(Selecione)"] + empresas)
if empresa_selecionada and empresa_selecionada != "(Selecione)":
    # Procurar o PDF renomeado correspondente
    nome_pdf = f"{empresa_selecionada}.pdf"
    pdf_bytes = None
    for fname, fbytes in matched_files:
        if fname == nome_pdf:
            pdf_bytes = fbytes
            break
    if pdf_bytes:
        st.success(f"PDF encontrado: {nome_pdf}")
        st.download_button(
            label=f"Baixar PDF de {empresa_selecionada}",
            data=pdf_bytes,
            file_name=nome_pdf,
            mime="application/pdf"
        )
    else:
        st.error("PDF não encontrado para esta empresa.")

st.markdown("---")

# Filtros interativos
with st.expander("Filtros avançados", expanded=False):
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        filtro_empresas = st.multiselect("Filtrar por empresa", empresas, default=empresas)
    with col2:
        status_rf = st.selectbox("Parcelamento RF", options=["Todos", "Sim", "Não"])
    with col3:
        status_pgfn = st.selectbox("Parcelamento PGFN", options=["Todos", "Sim", "Não"])

# Aplicar filtros
df_filtrado = df[df['Empresa'].isin(filtro_empresas)]
if status_rf != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Parcelamento RF'] == status_rf]
if status_pgfn != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Parcelamento PGFN'] == status_pgfn]

# KPIs
col1, col2, col3, col4 = st.columns(4)
total_empresas = len(df_filtrado)
rf_sim = (df_filtrado['Parcelamento RF'] == 'Sim').sum()
pgfn_sim = (df_filtrado['Parcelamento PGFN'] == 'Sim').sum()
ambos_sim = ((df_filtrado['Parcelamento RF'] == 'Sim') & (df_filtrado['Parcelamento PGFN'] == 'Sim')).sum()
col1.metric("Total de Empresas Filtradas", total_empresas)
col2.metric("Parcelamento RF (Sim)", rf_sim)
col3.metric("Parcelamento PGFN (Sim)", pgfn_sim)
col4.metric("Parcelamento em Ambos", ambos_sim)

st.markdown("---")

# Gráficos
colg1, colg2 = st.columns(2)
with colg1:
    fig_rf = px.pie(df_filtrado, names='Parcelamento RF', title='Distribuição Parcelamento Receita Federal', color='Parcelamento RF', color_discrete_map={"Sim": "#2ecc71", "Não": "#e74c3c"})
    st.plotly_chart(fig_rf, use_container_width=True)
with colg2:
    fig_pgfn = px.pie(df_filtrado, names='Parcelamento PGFN', title='Distribuição Parcelamento PGFN', color='Parcelamento PGFN', color_discrete_map={"Sim": "#2980b9", "Não": "#f1c40f"})
    st.plotly_chart(fig_pgfn, use_container_width=True)

# Gráfico de barras - Empresas com parcelamento em ambos
df_ambos = df_filtrado[(df_filtrado['Parcelamento RF'] == 'Sim') & (df_filtrado['Parcelamento PGFN'] == 'Sim')]
if not df_ambos.empty:
    st.markdown("#### Empresas com Parcelamento em RF e PGFN")
    fig_ambos = px.bar(df_ambos, x='Empresa', title='Empresas com Parcelamento em RF e PGFN', color='Empresa', color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_ambos, use_container_width=True)

st.markdown("---")

# Exportação Excel
excel_buffer = BytesIO()
df_filtrado.to_excel(excel_buffer, index=False)
excel_buffer.seek(0)
st.download_button(
    label="Exportar para Excel",
    data=excel_buffer,
    file_name="dashboard_situacao_fiscal.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Exportação PDF (tabela)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def gerar_pdf_dashboard(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elems = []
    elems.append(Paragraph("Relatório de Parcelamento - Dashboard", styles['Heading1']))
    elems.append(Spacer(1, 12))
    data = [list(df.columns)] + df.values.tolist()
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkgray),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    elems.append(table)
    doc.build(elems)
    buffer.seek(0)
    return buffer

pdf_buffer = gerar_pdf_dashboard(df_filtrado)
st.download_button(
    label="Exportar para PDF (tabela)",
    data=pdf_buffer,
    file_name="dashboard_situacao_fiscal.pdf",
    mime="application/pdf"
)

st.markdown("---")
st.dataframe(df_filtrado, use_container_width=True) 