import streamlit as st
import requests
import pandas as pd
import re
import urllib.parse
import csv
import os

st.set_page_config(page_title="Prospectador de Empresas", layout="wide")
st.title("🔍 Prospectador de Empresas pelo Google Places")

api_key = st.text_input("🔑 Insira sua Google Places API Key", type="password")

estados = {
    "SP": ["São Paulo", "Campinas", "Santos", "São Bernardo do Campo", "Guarulhos"],
    "RJ": ["Rio de Janeiro", "Niterói", "Duque de Caxias"],
    "MG": ["Belo Horizonte", "Uberlândia", "Contagem"],
    "RS": ["Porto Alegre", "Caxias do Sul"],
    "BA": ["Salvador", "Feira de Santana"],
    "PR": ["Curitiba", "Londrina"]
}

preset_cidades = {
    "SP": ["São Paulo", "Campinas", "Santos", "Guarulhos", "São Bernardo do Campo", "Ribeirão Preto"],
    "RJ": ["Rio de Janeiro", "Niterói", "Duque de Caxias", "Nova Iguaçu", "São Gonçalo"],
    "MG": ["Belo Horizonte", "Uberlândia", "Contagem", "Juiz de Fora", "Betim"],
    "RS": ["Porto Alegre", "Caxias do Sul", "Pelotas", "Canoas", "Santa Maria"],
    "BA": ["Salvador", "Feira de Santana", "Vitória da Conquista", "Camaçari", "Itabuna"],
    "PR": ["Curitiba", "Londrina", "Maringá", "Ponta Grossa", "Cascavel"]
}

st.sidebar.header("Filtros")
usar_preset = st.sidebar.checkbox("✅ Usar maiores cidades do Brasil")
usar_top_n = st.sidebar.checkbox("🔢 Selecionar número de cidades por estado")

if usar_top_n:
    n_cidades = st.sidebar.slider("Número de maiores cidades por estado", 1, 10, 3)
    cidades_selecionadas = []
    for estado, cidades in preset_cidades.items():
        cidades_selecionadas.extend(cidades[:n_cidades])
else:
    estado = st.sidebar.selectbox("📍 Escolha o estado", list(estados.keys()))
    cidades = st.sidebar.multiselect("🏙️ Escolha as cidades", estados[estado])
    cidades_selecionadas = cidades

raio_km = st.sidebar.slider("📏 Raio da busca (em km)", min_value=1, max_value=50, value=20)
termo = st.sidebar.text_input("🔎 O que você está buscando? (ex: imobiliária, pet shop)")
apenas_sem_site = st.sidebar.checkbox("❌ Exibir apenas empresas sem site")

if st.button("🔍 Buscar empresas") and api_key and cidades_selecionadas and termo:
    with st.spinner("🔄 Buscando empresas..."):
        resultados = []

        for cidade in cidades_selecionadas:
            local_query = f"{termo} em {cidade}"
            url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={urllib.parse.quote(local_query)}&radius={raio_km * 1000}&key={api_key}"
            response = requests.get(url)
            data = response.json()

            for place in data.get("results", []):
                place_id = place.get("place_id")
                detalhes_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_phone_number,website&key={api_key}"
                detalhes_res = requests.get(detalhes_url).json()
                detalhes = detalhes_res.get("result", {})

                telefone = detalhes.get("formatted_phone_number", "")
                site = detalhes.get("website", None)

                # Remover tudo que não seja número, e garantir o formato desejado
                telefone_numerico = re.sub(r"\D", "", telefone)

                if len(telefone_numerico) >= 10:
                    if not telefone_numerico.startswith("55"):
                        telefone_numerico = "55" + telefone_numerico

                    mensagem = (
                        "Olá! Me chamo Davi Fernandes e trabalho com criação de sites estratégicos focados no seu nicho. "
                        "Notei que sua empresa está ativa e gostaria de apresentar uma forma de aumentar suas vendas com um site inteligente. Podemos conversar por 15 minutos?"
                    )
                    mensagem_codificada = urllib.parse.quote(mensagem)
                    link_whatsapp = f"https://wa.me/{telefone_numerico}?text={mensagem_codificada}"

                    if apenas_sem_site and site:
                        continue

                    resultados.append({
                        "Nome": detalhes.get("name", "Empresa"),
                        "Telefone": telefone_numerico,
                    })

        if resultados:
            df = pd.DataFrame(resultados)
            st.success(f"✅ {len(resultados)} empresas encontradas!")
            st.dataframe(df, use_container_width=True)

            for item in resultados:
                st.markdown(f"""
                <div style='border:1px solid #ddd; border-radius:10px; padding:10px; margin:10px 0; background-color:#000000'>
                    <strong>{item['Nome']}</strong><br>
                    📞 {item['Telefone']}<br>
                    <a href='{link_whatsapp}' target='_blank'>💬 Enviar mensagem no WhatsApp</a>
                </div>
                """, unsafe_allow_html=True)

            # Salvar em CSV no formato desejado
            arquivo_csv = 'empresas_encontradas.csv'
            with open(arquivo_csv, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Nome', 'Telefone'])
                for item in resultados:
                    writer.writerow([item['Nome'], item['Telefone']])

            st.success(f"📥 Dados salvos com sucesso em {arquivo_csv}!")
        else:
            st.warning("⚠️ Nenhuma empresa encontrada com essas condições.")
