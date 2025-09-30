import streamlit as st
import pandas as pd
import escavador
from escavador.v2 import Processo

st.set_page_config(page_title="Consulta de Processos - Escavador", page_icon="⚖️")
st.title("Consulta de Processos - Escavador")

# --- Token no input (com opção de lembrar na sessão) ---
with st.expander("Configurar acesso (token do Escavador)", expanded=True):
    # Se já lembramos o token na sessão, pré-carrega
    default_token = st.session_state.get("ESCAVADOR_TOKEN", "")
    token = st.text_input("Insira seu ESCAVADOR_TOKEN", value=default_token, type="password", help="Cole aqui o token gerado na sua conta do Escavador.")
    lembrar = st.checkbox("Lembrar token nesta sessão (não persiste após recarregar a página)", value=bool(default_token))

    if lembrar and token:
        st.session_state["ESCAVADOR_TOKEN"] = token
    elif not lembrar and "ESCAVADOR_TOKEN" in st.session_state:
        del st.session_state["ESCAVADOR_TOKEN"]

# Configura o SDK somente quando tivermos token válido
if token:
    try:
        escavador.config(token)
    except Exception as e:
        st.error(f"Falha ao configurar o Escavador. Verifique o token. Detalhes: {e}")

# --- Entrada de CPF/CNPJ ---
cnpj = st.text_input("CPF ou CNPJ do envolvido", placeholder="Somente números (com ou sem máscara)")

# --- Ação ---
if st.button("Consultar"):
    if not token:
        st.error("Informe o ESCAVADOR_TOKEN para continuar.")
        st.stop()
    if not cnpj:
        st.error("Informe um CPF ou CNPJ.")
        st.stop()

    with st.spinner("Consultando processos..."):
        processos = []
        try:
            _, processos_escavador = Processo.por_envolvido(cpf_cnpj=cnpj)
        except Exception as e:
            st.error(f"Erro na consulta inicial: {e}")
            st.stop()

        # Paginação
        while processos_escavador:
            for processo in processos_escavador:
                for fonte in processo.fontes:
                    temp_dict = {
                        "numero": getattr(processo, "numero_cnj", ""),
                        "data_inicio": getattr(processo, "data_inicio", ""),
                        "titulo_polo_ativo": getattr(processo, "titulo_polo_ativo", ""),
                        "titulo_polo_passivo": getattr(processo, "titulo_polo_passivo", ""),
                        "descricao": getattr(fonte, "descricao", ""),
                        "nome": getattr(fonte, "nome", ""),
                        "sigla": getattr(fonte, "sigla", ""),
                        "tipo": getattr(fonte, "tipo", ""),
                        "grau": getattr(fonte, "grau", ""),
                        "grau_formatado": getattr(fonte, "grau_formatado", ""),
                        "tribunal": getattr(getattr(fonte, "tribunal", {}), "nome", ""),
                        "segredo_justica": getattr(fonte, "segredo_justica", ""),
                        "arquivado": getattr(fonte, "arquivado", ""),
                        "status_predito": getattr(fonte, "status_predito", ""),
                        "data_ultima_movimentacao": getattr(fonte, "data_ultima_movimentacao", ""),
                        "url": getattr(fonte, "url", ""),
                    }

                    tipos = getattr(fonte, "tipos_envolvido_pesquisado", [])
                    if tipos:
                        temp_dict["tipo_99_normalizado"] = getattr(tipos[0], "tipo_normalizado", "")
                        temp_dict["polo_99"] = getattr(tipos[0], "polo", "")
                    else:
                        temp_dict["tipo_99_normalizado"] = ""
                        temp_dict["polo_99"] = ""

                    capa = getattr(fonte, "capa", None)
                    if capa:
                        temp_dict["assuntos_normalizados"] = getattr(capa, "assuntos_normalizados", "")
                        temp_dict["classe"] = getattr(capa, "classe", "")
                        temp_dict["assunto"] = getattr(capa, "assunto", "")
                        temp_dict["area"] = getattr(capa, "area", "")
                        temp_dict["orgao_julgador"] = getattr(capa, "orgao_julgador", "")
                        temp_dict["data_distribuicao"] = getattr(capa, "data_distribuicao", "")
                        temp_dict["data_arquivamento"] = getattr(capa, "data_arquivamento", "")

                        assunto_principal = getattr(capa, "assunto_principal_normalizado", None)
                        if assunto_principal:
                            temp_dict["nome_assunto"] = getattr(assunto_principal, "nome", "")
                            temp_dict["nome_assunto_com_pai"] = getattr(assunto_principal, "nome_com_pai", "")
                            temp_dict["path_completo_assunto"] = getattr(assunto_principal, "path_completo", "")
                        else:
                            temp_dict["nome_assunto"] = ""
                            temp_dict["nome_assunto_com_pai"] = ""
                            temp_dict["path_completo_assunto"] = ""

                        valor_causa = getattr(capa, "valor_causa", None)
                        temp_dict["valor_causa"] = getattr(valor_causa, "valor", "") if valor_causa else ""
                    else:
                        temp_dict.update({
                            "assuntos_normalizados": "",
                            "classe": "",
                            "assunto": "",
                            "area": "",
                            "orgao_julgador": "",
                            "data_distribuicao": "",
                            "data_arquivamento": "",
                            "nome_assunto": "",
                            "nome_assunto_com_pai": "",
                            "path_completo_assunto": "",
                            "valor_causa": "",
                        })

                    for i, envolvido in enumerate(getattr(fonte, "envolvidos", []), start=1):
                        temp_dict[f"envolvido{i}_nome"] = getattr(envolvido, "nome", "")
                        temp_dict[f"envolvido{i}_tipo_normalizado"] = getattr(envolvido, "tipo_normalizado", "")
                        temp_dict[f"envolvido{i}_tipo"] = getattr(envolvido, "tipo", "")

                    processos.append(temp_dict)

            try:
                processos_escavador = processos_escavador.continuar_busca()
            except Exception:
                break

        if not processos:
            st.warning("Nenhum processo encontrado para o documento informado.")
            st.stop()

        df = pd.DataFrame(processos)
        st.success(f"{len(df)} registros encontrados.")
        st.dataframe(df, use_container_width=True)

        # Download CSV
        st.download_button(
            label="Baixar CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="processos.csv",
            mime="text/csv",
        )
