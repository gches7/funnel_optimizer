import streamlit as st
import pulp as pl

# Estado para controle de etapas
if "etapa" not in st.session_state:
    st.session_state.etapa = 1

st.title("Funil de Marketing Otimizado")

# 1st step - Investment on promotional spreadsheet
with st.expander("Etapa 1: Otimização da Planilha", expanded=True if st.session_state.etapa == 1 else False):
    st.subheader("Investimentos e Despesas")

    total_mkt_plan = st.number_input("Total disponível para marketing", value=3000.0)
    mensalidade_agencia = st.number_input("Mensalidade da agência", value=4500.0)
    min_desp_var = st.number_input("Despesa variável mínima", value=300.0)
    valor_planilha = st.number_input("Valor de venda da planilha", value=197.0)
    tx_plataforma = st.slider("Taxa da plataforma", min_value=0, max_value=100) / 100
    cac_plan = st.number_input("CAC - Custo de aquisição da planilha", value=20.0)

    if st.button("Executar Etapa 1"):
        # Construção do modelo
        planilha = pl.LpProblem('Custo_planilha', pl.LpMaximize)

        despesa_plataforma = tx_plataforma * valor_planilha
        pag_agencia = mensalidade_agencia / 2

        inv_campanha = pl.LpVariable('inv_campanha', lowBound=0, cat='Continuous')
        pg_agencia = pl.LpVariable('pg_agencia', lowBound=0, cat='Continuous')
        desp_var = pl.LpVariable('desp_var', lowBound=0, cat='Continuous')

        planilha += inv_campanha

        planilha += inv_campanha + pg_agencia + desp_var <= total_mkt_plan - despesa_plataforma
        planilha += desp_var >= min_desp_var
        planilha += pg_agencia >= pag_agencia

        planilha.solve()

        if pl.LpStatus[planilha.status] == 'Optimal':
            st.success("Solução ótima encontrada!")
            for variable in planilha.variables():
                st.write(f"{variable.name} = {variable.varValue:.2f}")
            comp1 = inv_campanha.varValue / cac_plan
            lucro_plan = comp1 * (valor_planilha - despesa_plataforma) - total_mkt_plan
            st.write(f"Número de potenciais compradores da planilha: {comp1:.2f}")
            st.write(f"Lucro com a planilha: R$ {lucro_plan:.2f}")
            st.session_state.comp1 = comp1
            st.session_state.pag_agencia = pag_agencia
            st.session_state.etapa = 2
        else:
            st.error("Solução não ótima encontrada.")

# 2nd step - In-person event with minimized cost
if st.session_state.etapa >= 2:
    with st.expander("Evento - minimização de custo total do evento", expanded=True if st.session_state.etapa == 2 else False):
        #st.subheader("Planejamento do Evento")

        d_min_local = st.number_input("Despesa mínima com local", value=7000.0, key='loc1')
        min_camp_evento = st.number_input("Investimento mínimo em campanha do evento", value=1000.0, key='camp1')
        d_min_pub = st.number_input("Despesa mínima com publicidade", value=1000.0, key='min_pub1')
        d_max_pub = st.number_input("Despesa máxima com publicidade", value=2000.0, key='min_pub2')
        d_min_inst = st.number_input("Despesa mínima com instrumentação", value=1000.0, key='min_inst1')
        d_max_inst = st.number_input("Despesa máxima com instrumentação", value=3000.0, key='min_inst2')
        d_min_buffet = st.number_input("Despesa mínima com buffet", value=500.0, key='min_buff1')
        d_max_buffet = st.number_input("Despesa máxima com buffet", value=2000.0, key='min_buff2')
        ingresso_evento = st.number_input("Valor do ingresso", value=700.0, key='ing_ev1')
        conv1 = st.slider("Taxa de conversão da planilha para o evento (%)", 0, 100, 15, key='conv_plan_ev1') / 100
        cac_evento = st.number_input("CAC campanha evento", value=20.0, key='cac_ev1')
        d_total_evento_max = st.number_input("Despesas totais máximas do evento", value=18000.0, key='d_max1')

        if st.button("Minimizar custo"):
            evento = pl.LpProblem("Custo_evento", pl.LpMinimize)

            comp2 = conv1 * st.session_state.comp1
            d_agencia = st.session_state.pag_agencia
            d_plataforma = tx_plataforma * ingresso_evento * comp2

            inv_camp_evento = pl.LpVariable("inv_camp_evento", lowBound=min_camp_evento)
            d_buffet = pl.LpVariable("buffet", lowBound=d_min_buffet, upBound=d_max_buffet)
            d_pub_evento = pl.LpVariable("pub_evento", lowBound=d_min_pub, upBound=d_max_pub)
            d_inst = pl.LpVariable("instrumentacao", lowBound=d_min_inst, upBound=d_max_inst)
            d_local = pl.LpVariable("local", lowBound=d_min_local)
            d_total_evento = pl.LpVariable("total_desp", lowBound=0, upBound=d_total_evento_max)

            evento += d_total_evento
            evento += inv_camp_evento + d_buffet + d_pub_evento + d_inst + d_local <= d_total_evento - d_agencia - d_plataforma
            evento.solve()

            if pl.LpStatus[evento.status] == 'Optimal':
                st.success("Solução ótima encontrada!")
                for variable in evento.variables():
                    st.write(f"{variable.name} = {variable.varValue:.2f}")
                resultado_camp_evento = pl.value(inv_camp_evento) / cac_evento
                compradores_evento = comp2 + resultado_camp_evento
                receita_evento = compradores_evento * ingresso_evento
                lucro_evento = receita_evento - pl.value(d_total_evento)

                st.write(f"Compradores evento: {compradores_evento:.0f}")
                st.write(f"Compradores via campanha: {resultado_camp_evento:.0f}")
                st.write(f"Receita total: R$ {receita_evento:.2f}")
                st.write(f"Lucro do evento: R$ {lucro_evento:.2f}")
                st.write(f'Compradores oriundos da planilha: {round(comp2)}')
                st.session_state.etapa = 3
            else:
                st.error("Solução não ótima encontrada.")

# 3rd step - Maximize in-person event ads budget
if st.session_state.etapa >= 3:
    with st.expander("Evento - maximização da campanha", expanded=True):
        #st.subheader("Maximizar investimento em campanha")
        d_min_local = st.number_input("Despesa mínima com local", value=7000.0)
        min_camp_evento = st.number_input("Investimento mínimo em campanha do evento", value=1000.0)
        d_min_pub = st.number_input("Despesa mínima com publicidade", value=1000.0)
        d_max_pub = st.number_input("Despesa máxima com publicidade", value=2000.0)
        d_min_inst = st.number_input("Despesa mínima com instrumentação", value=1000.0)
        d_max_inst = st.number_input("Despesa máxima com instrumentação", value=3000.0)
        d_min_buffet = st.number_input("Despesa mínima com buffet", value=500.0)
        d_max_buffet = st.number_input("Despesa máxima com buffet", value=2000.0)
        ingresso_evento = st.number_input("Valor do ingresso", value=700.0)
        #conv1 = st.slider("Taxa de conversão da planilha para o evento (%)", 0, 100, 15) / 100
        cac_evento = st.number_input("CAC do evento", value=20.0)
        d_total_evento_max = st.number_input("Despesas totais máximas do evento", value=18000.0)
        conv1_3 = st.slider("Taxa de conversão planilha → evento (%)", 0, 100, 50) / 100

        if st.button("Maximizar campanha"):
            evento = pl.LpProblem("Custo_evento", pl.LpMaximize)

            comp2 = conv1_3 * st.session_state.comp1
            d_agencia = st.session_state.pag_agencia
            d_plataforma = tx_plataforma * ingresso_evento * comp2

            inv_camp_evento = pl.LpVariable("inv_camp_evento", lowBound=min_camp_evento)
            d_buffet = pl.LpVariable("buffet", lowBound=d_min_buffet, upBound=d_max_buffet)
            d_pub_evento = pl.LpVariable("pub_evento", lowBound=d_min_pub, upBound=d_max_pub)
            d_inst = pl.LpVariable("instrumentacao", lowBound=d_min_inst, upBound=d_max_inst)
            d_local = pl.LpVariable("local", lowBound=d_min_local)
            d_total_evento = pl.LpVariable("total_desp", lowBound=0, upBound=d_total_evento_max)

            evento += inv_camp_evento
            evento += inv_camp_evento + d_buffet + d_pub_evento + d_inst + d_local <= d_total_evento - d_agencia - d_plataforma
            evento.solve()

            if pl.LpStatus[evento.status] == 'Optimal':
                st.success("Solução ótima encontrada!")
                for variable in evento.variables():
                    st.write(f"{variable.name} = {variable.varValue:.2f}")
                resultado_camp_evento = pl.value(inv_camp_evento) / cac_evento
                compradores_evento = comp2 + resultado_camp_evento
                receita_evento = compradores_evento * ingresso_evento
                lucro_evento = receita_evento - pl.value(d_total_evento)

                st.write(f"Compradores evento: {compradores_evento:.2f}")
                st.write(f"Compradores via campanha: {resultado_camp_evento:.2f}")
                st.write(f"Receita total: R$ {receita_evento:.2f}")
                st.write(f"Lucro do evento: R$ {lucro_evento:.2f}")
                st.session_state.etapa = 4
            else:
                st.error("Solução não ótima encontrada.")

# 4th step - Follow-up simulation
if st.session_state.etapa >= 4:
    with st.expander("Simulação acompanhamento", expanded=True):      
        st.title("Simulação do Acompanhamento")

        # Inputs do usuário
        conv2 = st.slider("Taxa de conversão do evento para acompanhamento (%)", 0, 100, 10) / 100
        org = st.number_input("Clientes do orgânico", value=10)
        base_planejador = st.number_input("Custo base por planejador", value=800.0)
        d_comercial = st.number_input("Despesa comercial", value=5000.0)
        n_planejadores = st.number_input("Número de planejadores", value=2)
        valor_acompanhamento = st.number_input("Valor por cliente de acompanhamento", value=3000.0)
        compradores_evento = st.number_input("Número de compradores do evento", value=100)  # necessário como input

        # Cálculos mantidos exatamente como no código original
        n_clientes = conv2 * compradores_evento + org

        receitas_acomp = n_clientes * valor_acompanhamento
        desp_acomp = (d_comercial + n_clientes * base_planejador * n_planejadores)
        lucro_acomp = receitas_acomp - desp_acomp

        # Exibição do resultado
        st.subheader("Resultado")
        st.write("Lucro acompanhamento: R$ {:.2f}".format(lucro_acomp))