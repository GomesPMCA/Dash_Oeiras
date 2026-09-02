import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

DB_NAME = "visitas_campo_v2.db"

# Configuração da página
st.set_page_config(
    page_title="Painel & Consulta - Visitas v2",
    page_icon="📊",
    layout="wide"
)

@st.cache_data(ttl=5)
def carregar_dados():
    """Conecta ao banco e carrega os dados atualizados das visitas."""
    if not os.path.exists(DB_NAME):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM visitas_v2 ORDER BY id ASC", conn)
    conn.close()
    
    if not df.empty:
        # Garante conversão correta da coluna de data
        df['data_dt'] = pd.to_datetime(df['data_registro'], errors='coerce')
    return df

df = carregar_dados()

if df.empty:
    st.warning("⚠️ Nenhum registro encontrado no banco de dados 'visitas_campo_v2.db'.")
    st.stop()

# --- BARRA LATERAL: MENU DE NAVEGAÇÃO ---
st.sidebar.title("📌 Navegação")
pagina = st.sidebar.radio("Selecione a Visualização:", ["🔍 Ficha / Consulta por Entrevista", "📊 Dashboard Geral"])


# ==============================================================================
# PÁGINA 1: CONSULTA INDIVIDUAL COM FILTRO DE DATA E BOTÕES DE NAVEGAÇÃO
# ==============================================================================
if pagina == "🔍 Ficha / Consulta por Entrevista":
    st.title("🔎 Consulta Detalhada da Entrevista")

    # --- CONTROLE 1: DATA INICIAL DA ENTREVISTA ---
    col_filtro1, col_filtro2 = st.columns([2, 2])
    with col_filtro1:
        data_minima_banco = df['data_dt'].min().date() if not df['data_dt'].isna().all() else datetime.now().date()
        data_inicio_filtro = st.date_input(
            "📅 Exibir entrevistas a partir de:",
            value=data_minima_banco,
            format="DD/MM/YYYY"
        )

    # Filtragem dos dados pelo período selecionado
    df_filtrado_data = df[df['data_dt'].dt.date >= data_inicio_filtro].reset_index(drop=True)

    if df_filtrado_data.empty:
        st.info("ℹ️ Nenhuma entrevista encontrada a partir da data selecionada.")
        st.stop()

    # Inicialização da variável de índice de navegação na sessão
    if 'indice_entrevista' not in st.session_state:
        st.session_state.indice_entrevista = 0

    # Garante que o índice permanece dentro dos limites após aplicar o filtro
    if st.session_state.indice_entrevista >= len(df_filtrado_data):
        st.session_state.indice_entrevista = 0

    # --- CONTROLE 2: BOTÕES PARA AVANÇAR E RETROCEDER ---
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

    with col_nav1:
        if st.button("◀ Anterior", use_container_width=True):
            if st.session_state.indice_entrevista > 0:
                st.session_state.indice_entrevista -= 1
                st.rerun()

    with col_nav3:
        if st.button("Próximo ▶", use_container_width=True):
            if st.session_state.indice_entrevista < len(df_filtrado_data) - 1:
                st.session_state.indice_entrevista += 1
                st.rerun()

    with col_nav2:
        opcoes_visita = [
            f"ID {row['id']} - {row['nome_anfitriao']} ({row['localidade']})" 
            for _, row in df_filtrado_data.iterrows()
        ]
        
        # Sincroniza a caixa de seleção com o índice atual
        id_selecionado = st.selectbox(
            "Entrevista atual:", 
            opcoes_visita, 
            index=st.session_state.indice_entrevista
        )
        # Atualiza o índice na sessão se o usuário alterar diretamente no dropdown
        st.session_state.indice_entrevista = opcoes_visita.index(id_selecionado)

    visita = df_filtrado_data.iloc[st.session_state.indice_entrevista]

    # --- MÍDIAS NA BARRA LATERAL (BUSCA MAIS ROBUSTA) ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎥 Vídeo de Apoio")
    video_apoio = str(visita['caminho_video_apoio'])

    if video_apoio and video_apoio not in ["None", "NaN", "Não enviado", "Pular"]:
        # Limpa o caminho do Windows e pega apenas o nome base
        nome_limpo_v = os.path.basename(video_apoio.replace('\\', '/'))
        
        # Procura em todas as pastas possíveis
        pastas_busca = [".", "midias_visitas_v2"]
        encontrado_v = None
        
        for pasta in pastas_busca:
            caminho_teste = os.path.join(pasta, nome_limpo_v)
            if os.path.exists(caminho_teste):
                encontrado_v = caminho_teste
                break
        
        if encontrado_v:
            st.sidebar.video(encontrado_v)
        else:
            st.sidebar.caption("Nenhum vídeo de apoio localizado.")
    else:
        st.sidebar.caption("Nenhum vídeo registrado para esta visita.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🖼️ Mídia da Casa")
    midia_casa = str(visita['caminho_midia_casa'])

    if midia_casa and midia_casa not in ["None", "NaN"]:
        # Limpa o caminho do Windows e pega apenas o nome base
        nome_limpo_m = os.path.basename(midia_casa.replace('\\', '/'))
        
        pastas_busca = [".", "midias_visitas_v2"]
        encontrado_m = None
        
        for pasta in pastas_busca:
            caminho_teste = os.path.join(pasta, nome_limpo_m)
            if os.path.exists(caminho_teste):
                encontrado_m = caminho_teste
                break
        
        if encontrado_m:
            if encontrado_m.lower().endswith(('.jpg', '.jpeg', '.png')):
                st.sidebar.image(encontrado_m, use_container_width=True)
            elif encontrado_m.lower().endswith(('.mp4', '.mov', '.avi')):
                st.sidebar.video(encontrado_m)
        else:
            st.sidebar.caption(f"📷 Arquivo '{nome_limpo_m}' não encontrado.")
    else:
        st.sidebar.caption("📷 Foto/Vídeo da casa não encontrado.")

    # --- CABEÇALHO DA FICHA ---
    col_c1, col_c2, col_c3 = st.columns(3)
    col_c1.subheader(f"👤 {visita['nome_anfitriao']}")
    col_c1.caption(f"**Apelido:** {visita['apelido_anfitriao']}")
    col_c2.subheader(f"📍 {visita['localidade']}")
    col_c2.caption(f"**Data do Registro:** {visita['data_registro']}")
    col_c3.subheader(f"Status: {visita['status']}")

    st.markdown("---")

    # --- CORPO: FORMULÁRIO E MAPA ---
    col_esquerda, col_direita = st.columns([1, 1])

    # 📋 COLUNA DA ESQUERDA: RESPOSTAS DO QUESTIONÁRIO
    with col_esquerda:
        st.markdown("### 📋 Respostas do Formulário")
        
        st.markdown(f"**1. Integrantes na Família:** {visita['num_integrantes']} pessoa(s)")
        st.markdown(f"**2. Eleitores na Casa:** {visita['num_eleitores']}")
        st.markdown(f"**3. Sem Documentação (+16 anos):** {visita['num_sem_doc_16plus']}")
        st.markdown(f"**4. Crianças (até 11 anos):** {visita['num_criancas_ate11']}")
        st.markdown(f"**5. Recebe Bolsa Família:** `{visita['bolsa_familia']}`")
        st.markdown(f"**6. Fontes de Renda:** {visita['fontes_renda']}")
        st.markdown(f"**7. Frequentam a Escola:** {visita['num_frequentam_escola']}")
        st.markdown(f"**8. Pessoas com Curso Superior:** {visita['num_curso_superior']}")
        
        if visita['num_curso_superior'] > 0:
            st.info(f"🎓 **Detalhes do Ensino Superior:**\n{visita['detalhes_curso_superior']}")

        st.markdown("---")
        st.markdown("### 🗣️ Anseios e Necessidades da Família/Comunidade")
        st.warning(visita['anseios_necessidades'])

    # 🗺️ COLUNA DA DIREITA: MAPA DE LOCALIZAÇÃO GPS
    with col_direita:
        st.markdown("### 🗺️ Localização GPS")
        
        lat, lon = visita['lat_inicio'], visita['lon_inicio']
        if pd.notnull(lat) and pd.notnull(lon):
            df_mapa = pd.DataFrame({'lat': [float(lat)], 'lon': [float(lon)]})
            st.map(df_mapa, zoom=13)
            st.caption(f"Coordenadas: `{lat}, {lon}`")
        else:
            st.info("Localização GPS não cadastrada.")


# ==============================================================================
# PÁGINA 2: DASHBOARD GERAL E MÉTRICAS AGREGADAS
# ==============================================================================
elif pagina == "📊 Dashboard Geral":
    st.title("📊 Painel de Controle de Visitas de Campo")

    col_f1, _ = st.columns([2, 2])
    with col_f1:
        localidades_opt = ["Todas"] + sorted(list(df['localidade'].dropna().unique()))
        filtro_localidade = st.selectbox("Filtrar por Localidade:", localidades_opt)

    df_filtrado = df[df['localidade'] == filtro_localidade] if filtro_localidade != "Todas" else df.copy()

    # Cartões KPIs
    st.markdown("### 📌 Indicadores Gerais")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Visitas Realizadas", len(df_filtrado))
    kpi2.metric("Pessoas Mapeadas", int(df_filtrado['num_integrantes'].sum()))
    kpi3.metric("Total de Eleitores", int(df_filtrado['num_eleitores'].sum()))
    kpi4.metric("Sem Documentação (+16)", int(df_filtrado['num_sem_doc_16plus'].sum()))
    kpi5.metric("Bolsa Família", int((df_filtrado['bolsa_familia'] == 'SIM').sum()))

    st.markdown("---")

    # Gráficos
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📍 Visitas por Localidade")
        loc_counts = df_filtrado['localidade'].value_counts().reset_index()
        loc_counts.columns = ['Localidade', 'Visitas']
        fig_loc = px.bar(loc_counts, x='Visitas', y='Localidade', orientation='h', text='Visitas', color='Visitas')
        st.plotly_chart(fig_loc, use_container_width=True)

    with col_g2:
        st.subheader("💼 Fontes de Renda Mapeadas")
        rendas_list = [f.strip() for r in df_filtrado['fontes_renda'].dropna() for f in r.split(',')]
        df_renda = pd.Series(rendas_list).value_counts().reset_index()
        df_renda.columns = ['Fonte de Renda', 'Famílias']
        fig_renda = px.pie(df_renda, names='Fonte de Renda', values='Famílias', hole=0.4)
        st.plotly_chart(fig_renda, use_container_width=True)