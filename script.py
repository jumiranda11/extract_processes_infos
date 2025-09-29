import streamlit as st
import pandas as pd
import escavador
from escavador.v2 import Processo
import os

# Configuração segura do token via secrets
TOKEN = st.secrets["ESCAVADOR_TOKEN"]
escavador.config(TOKEN)

st.title("Consulta de Processos - Escavador")

# Entrada do CPF/CNPJ
cnpj = st.text_input("Digite o CPF ou CNPJ")

# Botão para executar
if st.button("Consultar"):
    if not cnpj:
        st.error("Por favor, preencha o CPF/CNPJ e o caminho da pasta.")
    else:
        with st.spinner("Consultando processos..."):
            processos = []
            try:
                _, processos_escavador = Processo.por_envolvido(cpf_cnpj=cnpj)
            except Exception as e:
                st.error(f"Erro na consulta: {e}")
                st.stop()

            while processos_escavador:
                for processo in processos_escavador:
                    for fonte in processo.fontes:
                        temp_dict = {
                            'numero': getattr(processo, 'numero_cnj', ''),
                            'data_inicio': getattr(processo, 'data_inicio', ''),
                            'titulo_polo_ativo': getattr(processo, 'titulo_polo_ativo', ''),
                            'titulo_polo_passivo': getattr(processo, 'titulo_polo_passivo', ''),
                            'descricao': getattr(fonte, 'descricao', ''),
                            'nome': getattr(fonte, 'nome', ''),
                            'sigla': getattr(fonte, 'sigla', ''),
                            'tipo': getattr(fonte, 'tipo', ''),
                            'grau': getattr(fonte, 'grau', ''),
                            'grau_formatado': getattr(fonte, 'grau_formatado', ''),
                            'tribunal': getattr(getattr(fonte, 'tribunal', {}), 'nome', ''),
                            'segredo_justica': getattr(fonte, 'segredo_justica', ''),
                            'arquivado': getattr(fonte, 'arquivado', ''),
                            'status_predito': getattr(fonte, 'status_predito', ''),
                            'data_ultima_movimentacao': getattr(fonte, 'data_ultima_movimentacao', ''),
                            'url': getattr(fonte, 'url', ''),
                        }

                        tipos = getattr(fonte, 'tipos_envolvido_pesquisado', [])
                        if tipos:
                            temp_dict['tipo_99_normalizado'] = getattr(tipos[0], 'tipo_normalizado', '')
                            temp_dict['polo_99'] = getattr(tipos[0], 'polo', '')
                        else:
                            temp_dict['tipo_99_normalizado'] = ''
                            temp_dict['polo_99'] = ''

                        capa = getattr(fonte, 'capa', None)
                        if capa:
                            temp_dict['assuntos_normalizados'] = getattr(capa, 'assuntos_normalizados', '')
                            temp_dict['classe'] = getattr(capa, 'classe', '')
                            temp_dict['assunto'] = getattr(capa, 'assunto', '')
                            temp_dict['area'] = getattr(capa, 'area', '')
                            temp_dict['orgao_julgador'] = getattr(capa, 'orgao_julgador', '')
                            temp_dict['data_distribuicao'] = getattr(capa, 'data_distribuicao', '')
                            temp_dict['data_arquivamento'] = getattr(capa, 'data_arquivamento', '')

                            assunto_principal = getattr(capa, 'assunto_principal_normalizado', None)
                            if assunto_principal:
                                temp_dict['nome_assunto'] = getattr(assunto_principal, 'nome', '')
                                temp_dict['nome_assunto_com_pai'] = getattr(assunto_principal, 'nome_com_pai', '')
                                temp_dict['path_completo_assunto'] = getattr(assunto_principal, 'path_completo', '')
                            else:
                                temp_dict['nome_assunto'] = ''
                                temp_dict['nome_assunto_com_pai'] = ''
                                temp_dict['path_completo_assunto'] = ''

                            valor_causa = getattr(capa, 'valor_causa', None)
                            temp_dict['valor_causa'] = getattr(valor_causa, 'valor', '') if valor_causa else ''
                        else:
                            temp_dict.update({
                                'assuntos_normalizados': '',
                                'classe': '',
                                'assunto': '',
                                'area': '',
                                'orgao_julgador': '',
                                'data_distribuicao': '',
                                'data_arquivamento': '',
                                'nome_assunto': '',
                                'nome_assunto_com_pai': '',
                                'path_completo_assunto': '',
                                'valor_causa': ''
                            })

                        for i, envolvido in enumerate(getattr(fonte, 'envolvidos', []), start=1):
                            temp_dict[f'envolvido{i}_nome'] = getattr(envolvido, 'nome', '')
                            temp_dict[f'envolvido{i}_tipo_normalizado'] = getattr(envolvido, 'tipo_normalizado', '')
                            temp_dict[f'envolvido{i}_tipo'] = getattr(envolvido, 'tipo', '')

                        processos.append(temp_dict)

                try:
                    processos_escavador = processos_escavador.continuar_busca()
                except Exception:
                    break

            df = pd.DataFrame(processos)

            # Gerar CSV para download
            csv_bytes = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label= "Baixar CSV",
                data=csv_bytes,
                file_name="processos.csv",
                mime="text/csv"
            )
