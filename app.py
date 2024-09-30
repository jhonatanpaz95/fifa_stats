import streamlit as st
import pandas as pd
import sqlite3
from matplotlib import pyplot
import seaborn as sns

# Conectando ao SQLite
conn = sqlite3.connect('data.db')
c = conn.cursor()

# Criando as tabelas se não existirem
c.execute('''CREATE TABLE IF NOT EXISTS dados 
             (nome TEXT, valor REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS dados_jogos 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              jogador1 TEXT, placar_jogador1 INTEGER, 
              jogador2 TEXT, placar_jogador2 INTEGER)''')

# Título do App
st.title("FIFA Parças, Gráficos e Registro de Jogos")

# ---- Parte 1: Registro de placares de jogos ----

st.subheader("Registro de Resultados de Jogos")

# Lista de jogadores (exemplo)
jogadores = ["Luiz", "Mateus", "Jhonatan"]

# Selecionando os jogadores e placar
jogador1 = st.selectbox("Selecione o primeiro jogador:", jogadores)
placar_jogador1 = st.number_input(f"Placar do {jogador1}:", min_value=0, step=1)

jogador2 = st.selectbox("Selecione o segundo jogador:", [j for j in jogadores if j != jogador1])
placar_jogador2 = st.number_input(f"Placar do {jogador2}:", min_value=0, step=1)

# Botão para salvar o resultado do jogo
if st.button("Salvar Resultado do Jogo"):
    c.execute('''INSERT INTO dados_jogos (jogador1, placar_jogador1, jogador2, placar_jogador2)
                 VALUES (?, ?, ?, ?)''', 
              (jogador1, placar_jogador1, jogador2, placar_jogador2))
    conn.commit()
    st.success(f"Resultado salvo: {jogador1} ({placar_jogador1}) x ({placar_jogador2}) {jogador2}")

# ---- Parte 2: Excluir um resultado ----

st.subheader("Excluir um Resultado")

# Exibir os resultados dos jogos
df_jogos = pd.read_sql("SELECT * FROM dados_jogos", conn)

# Se houver registros de jogos
if not df_jogos.empty:
    # Exibe os dados na tabela
    st.write(df_jogos)

    # Verifica se a coluna 'id' existe no DataFrame
    if 'id' in df_jogos.columns:
        # Selecionar o jogo para excluir
        jogo_id = st.selectbox("Selecione o ID do jogo que deseja excluir:", df_jogos['id'])

        # Botão para excluir o jogo selecionado
        if st.button("Excluir Jogo"):
            c.execute("DELETE FROM dados_jogos WHERE id = ?", (jogo_id,))
            conn.commit()
            st.success(f"Jogo com ID {jogo_id} excluído com sucesso!")
    else:
        st.write("A coluna 'id' não foi encontrada nos dados dos jogos.")
else:
    st.write("Nenhum jogo registrado ainda.")

# ---- Parte 3: Estatísticas ----

# Função para calcular as estatísticas
def calcular_estatisticas(jogadores, df_jogos):
    stats = {jogador: {'Jogador': jogador, 'Jogos': 0, 'Gols Feitos': 0, 'Gols Sofridos': 0, 
                       'Vitórias': 0, 'Empates': 0, 'Derrotas': 0, 'Pontuação': 0}
             for jogador in jogadores}
    
    for _, row in df_jogos.iterrows():
        # Jogador 1
        jogador1 = row['jogador1']
        jogador2 = row['jogador2']
        placar1 = row['placar_jogador1']
        placar2 = row['placar_jogador2']
        
        # Atualizando estatísticas para jogador 1
        stats[jogador1]['Jogos'] += 1
        stats[jogador1]['Gols Feitos'] += placar1
        stats[jogador1]['Gols Sofridos'] += placar2
        
        # Atualizando estatísticas para jogador 2
        stats[jogador2]['Jogos'] += 1
        stats[jogador2]['Gols Feitos'] += placar2
        stats[jogador2]['Gols Sofridos'] += placar1
        
        # Calculando resultado (vitória, empate, derrota)
        if placar1 > placar2:
            stats[jogador1]['Vitórias'] += 1
            stats[jogador1]['Pontuação'] += 3
            stats[jogador2]['Derrotas'] += 1
        elif placar1 < placar2:
            stats[jogador2]['Vitórias'] += 1
            stats[jogador2]['Pontuação'] += 3
            stats[jogador1]['Derrotas'] += 1
        else:
            stats[jogador1]['Empates'] += 1
            stats[jogador2]['Empates'] += 1
            stats[jogador1]['Pontuação'] += 1
            stats[jogador2]['Pontuação'] += 1
    
    return stats

# Carregar os resultados dos jogos
df_jogos = pd.read_sql("SELECT * FROM dados_jogos", conn)

# Se houver jogos registrados, calcular estatísticas
if not df_jogos.empty:
    stats = calcular_estatisticas(jogadores, df_jogos)
    
    # Convertendo as estatísticas para um DataFrame
    df_stats = pd.DataFrame.from_dict(stats, orient='index')
    
    # Exibindo as estatísticas em uma tabela
    st.subheader("Tabela de Estatísticas dos Jogadores")
    st.dataframe(df_stats)  # Exibe a tabela com as estatísticas

    # ---- Parte 4: Gráficos ----

    st.subheader("Gráficos dos Resultados")

    # Gráfico de Linhas - Pontuação
    st.write("### Gráfico de Linhas - Pontuação")
    fig, ax = pyplot.subplots()
    for jogador in jogadores:
        pontuacao_acumulada = df_jogos.apply(lambda row: 3 if row['jogador1'] == jogador and row['placar_jogador1'] > row['placar_jogador2'] else
                                             3 if row['jogador2'] == jogador and row['placar_jogador2'] > row['placar_jogador1'] else
                                             1 if (row['jogador1'] == jogador or row['jogador2'] == jogador) and row['placar_jogador1'] == row['placar_jogador2'] else
                                             0, axis=1).cumsum()
        ax.plot(pontuacao_acumulada.index, pontuacao_acumulada, label=jogador)
    ax.set_xlabel('Partidas')
    ax.set_ylabel('Pontuação Acumulada')
    ax.legend()
    st.pyplot(fig)

    # Gráfico de Barras - Outras Estatísticas
    st.write("### Gráfico de Barras - Outras Estatísticas")
    fig, ax = pyplot.subplots()
    df_stats_melted = pd.melt(df_stats.reset_index(), id_vars=['Jogador'], 
                              value_vars=['Gols Feitos', 'Gols Sofridos', 'Vitórias', 'Empates', 'Derrotas'], 
                              var_name='Estatística', value_name='Valor')
    sns.barplot(x='Jogador', y='Valor', hue='Estatística', data=df_stats_melted, ax=ax)
    ax.set_xlabel('Jogadores')
    ax.set_ylabel('Valor')
    st.pyplot(fig)
else:
    st.write("Nenhum jogo registrado ainda.")

# Fechando a conexão
conn.close()