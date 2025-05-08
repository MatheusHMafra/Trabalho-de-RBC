import csv
import datetime  # Import para nomear o arquivo com data/hora

# --- 1. Representação do Caso e Base de Casos ---
#! Atributos: titulo, genero, ano_lancamento, classificacao_etaria, duracao_minutos, avaliacao_critica, tem_sequencia

# Valores possíveis para atributos categóricos (para geração e validação)
GENEROS_POSSIVEIS = ["Ação", "Comédia", "Drama", "Ficção Científica", "Suspense", "Romance",
                     "Animação", "Terror", "Aventura", "Crime", "Fantasia", "Guerra", "Faroeste", "Mistério"]
CLASSIFICACOES_POSSIVEIS = ["Livre", "10", "12", "14", "16", "18"]
BOOLEANOS_POSSIVEIS = ["Sim", "Não"]

# Mapeamento para similaridade ordinal da classificação etária
CLASSIFICACAO_MAPA_ORDINAL = {val: i for i,
                              val in enumerate(CLASSIFICACOES_POSSIVEIS)}
MAX_DIFF_CLASSIFICACAO = len(CLASSIFICACOES_POSSIVEIS) - 1

# Ranges para normalização (podem ser calculados dinamicamente da base ou definidos)
MIN_ANO = 1940
MAX_ANO = 2025
MAX_DIFF_ANOS = MAX_ANO - MIN_ANO

MIN_DURACAO = 60
MAX_DURACAO = 240
MAX_DIFF_DURACAO = MAX_DURACAO - MIN_DURACAO

MIN_AVALIACAO = 1.0
MAX_AVALIACAO = 10.0
MAX_DIFF_AVALIACAO = MAX_AVALIACAO - MIN_AVALIACAO


def carregar_base_de_casos_csv(caminho_arquivo="filmes_base.csv"):
    """Carrega a base de casos de um arquivo CSV."""
    base = []
    try:
        with open(caminho_arquivo, mode='r', encoding='utf-8') as arquivo_csv:
            leitor_csv = csv.DictReader(arquivo_csv)
            for linha in leitor_csv:
                try:
                    caso = {
                        "titulo": linha["titulo"],
                        "genero": linha["genero"],
                        "ano_lancamento": int(linha["ano_lancamento"]),
                        "classificacao_etaria": linha["classificacao_etaria"],
                        "duracao_minutos": int(linha["duracao_minutos"]),
                        # Trata vírgula como decimal
                        "avaliacao_critica": float(linha["avaliacao_critica"].replace(',', '.')),
                        "tem_sequencia": linha["tem_sequencia"]
                    }
                    # Validações simples (poderiam ser mais robustas)
                    if caso["genero"] not in GENEROS_POSSIVEIS:
                        print(
                            f"Aviso: Gênero '{caso['genero']}' do filme '{caso['titulo']}' não está na lista de gêneros conhecidos. Será usado como está.")
                    if caso["classificacao_etaria"] not in CLASSIFICACOES_POSSIVEIS:
                        print(
                            f"Aviso: Classificação '{caso['classificacao_etaria']}' do filme '{caso['titulo']}' não é padrão. Será usado como está.")
                    if caso["tem_sequencia"] not in BOOLEANOS_POSSIVEIS:
                        print(
                            f"Aviso: Valor para 'tem_sequencia' ('{caso['tem_sequencia']}') do filme '{caso['titulo']}' não é padrão. Será usado como está.")

                    base.append(caso)
                except ValueError as e:
                    print(
                        f"Erro ao converter dados para o filme {linha.get('titulo', 'DESCONHECIDO')}: {e}. Pulando este filme.")
                except KeyError as e:
                    print(
                        f"Coluna ausente {e} para o filme {linha.get('titulo', 'DESCONHECIDO')}. Pulando este filme.")
            if not base:
                print(
                    f"Aviso: NENHUM filme carregado de '{caminho_arquivo}'. Verifique o arquivo e seu conteúdo.")
            else:
                print(f"{len(base)} filmes carregados de '{caminho_arquivo}'.")

    except FileNotFoundError:
        print(
            f"Erro: Arquivo CSV '{caminho_arquivo}' não encontrado. Crie o arquivo ou verifique o caminho.")
    except Exception as e:
        print(f"Erro inesperado ao carregar o arquivo CSV: {e}.")
    return base


# Substitui a geração aleatória e manual pela carga do CSV
BASE_DE_CASOS = carregar_base_de_casos_csv()

# Se a base estiver vazia após tentar carregar, adicione alguns para o programa não quebrar
if not BASE_DE_CASOS:
    print("Base de casos está vazia. Adicionando alguns exemplos para demonstração.")
    BASE_DE_CASOS.extend([
        {"titulo": "Matrix (Exemplo Padrão)", "genero": "Ficção Científica", "ano_lancamento": 1999,
         "classificacao_etaria": "14", "duracao_minutos": 136, "avaliacao_critica": 8.7, "tem_sequencia": "Sim"},
        {"titulo": "O Poderoso Chefão (Exemplo Padrão)", "genero": "Drama", "ano_lancamento": 1972,
         "classificacao_etaria": "16", "duracao_minutos": 175, "avaliacao_critica": 9.2, "tem_sequencia": "Sim"},
        {"titulo": "Toy Story (Exemplo Padrão)", "genero": "Animação", "ano_lancamento": 1995,
         "classificacao_etaria": "Livre", "duracao_minutos": 81, "avaliacao_critica": 8.3, "tem_sequencia": "Sim"}
    ])


# --- 2. Métricas de Similaridade ---

#! Métricas de Similaridade
def similaridade_categorica(val1, val2):
    """Similaridade para atributos categóricos (ex: genero, tem_sequencia)."""
    return 1.0 if val1 == val2 else 0.0


def similaridade_numerica_normalizada(val1, val2, max_diff):
    """Similaridade para atributos numéricos normalizada (ex: ano, duracao, avaliacao)."""
    if max_diff == 0:  # Evita divisão por zero se o range for 0
        return 1.0 if val1 == val2 else 0.0
    # Certifique-se que val1 e val2 são numéricos antes de subtrair
    if not (isinstance(val1, (int, float)) and isinstance(val2, (int, float))):
        return 0.0  # Se algum não for numérico, similaridade é 0 ou tratar como erro
    return 1.0 - (abs(val1 - val2) / max_diff)


def similaridade_ordinal_classificacao(val1_str, val2_str):
    """Similaridade para classificação etária (ordinal)."""
    val1_num = CLASSIFICACAO_MAPA_ORDINAL.get(val1_str)
    val2_num = CLASSIFICACAO_MAPA_ORDINAL.get(val2_str)

    if val1_num is None or val2_num is None:
        return 0.0  # Valor desconhecido

    return 1.0 - (abs(val1_num - val2_num) / MAX_DIFF_CLASSIFICACAO)

# --- 3. Função de Similaridade Global ---


#! Pesos padrão
PESOS_PADRAO = {
    "genero": 0.25,
    "ano_lancamento": 0.15,
    "classificacao_etaria": 0.15,
    "duracao_minutos": 0.15,
    "avaliacao_critica": 0.20,
    "tem_sequencia": 0.10
}


def calcular_similaridade_global(caso_novo, caso_base, pesos):
    """Calcula a similaridade global entre dois casos usando média ponderada."""
    if not caso_novo or not caso_base:
        return 0.0

    similaridades_ponderadas = []
    soma_pesos_aplicados = 0.0

    # Gênero
    if 'genero' in pesos and pesos['genero'] > 0 and 'genero' in caso_novo and 'genero' in caso_base:
        sim_gen = similaridade_categorica(
            caso_novo.get('genero'), caso_base.get('genero'))
        similaridades_ponderadas.append(sim_gen * pesos['genero'])
        soma_pesos_aplicados += pesos['genero']

    # Ano Lançamento
    if 'ano_lancamento' in pesos and pesos['ano_lancamento'] > 0 and 'ano_lancamento' in caso_novo and 'ano_lancamento' in caso_base:
        sim_ano = similaridade_numerica_normalizada(
            caso_novo.get('ano_lancamento', MIN_ANO),
            caso_base.get('ano_lancamento', MIN_ANO),
            MAX_DIFF_ANOS
        )
        similaridades_ponderadas.append(sim_ano * pesos['ano_lancamento'])
        soma_pesos_aplicados += pesos['ano_lancamento']

    # Classificação Etária
    if 'classificacao_etaria' in pesos and pesos['classificacao_etaria'] > 0 and 'classificacao_etaria' in caso_novo and 'classificacao_etaria' in caso_base:
        sim_class = similaridade_ordinal_classificacao(
            caso_novo.get('classificacao_etaria'),
            caso_base.get('classificacao_etaria')
        )
        similaridades_ponderadas.append(
            sim_class * pesos['classificacao_etaria'])
        soma_pesos_aplicados += pesos['classificacao_etaria']

    # Duração Minutos
    if 'duracao_minutos' in pesos and pesos['duracao_minutos'] > 0 and 'duracao_minutos' in caso_novo and 'duracao_minutos' in caso_base:
        sim_dur = similaridade_numerica_normalizada(
            caso_novo.get('duracao_minutos', MIN_DURACAO),
            caso_base.get('duracao_minutos', MIN_DURACAO),
            MAX_DIFF_DURACAO
        )
        similaridades_ponderadas.append(sim_dur * pesos['duracao_minutos'])
        soma_pesos_aplicados += pesos['duracao_minutos']

    # Avaliação Crítica
    if 'avaliacao_critica' in pesos and pesos['avaliacao_critica'] > 0 and 'avaliacao_critica' in caso_novo and 'avaliacao_critica' in caso_base:
        sim_aval = similaridade_numerica_normalizada(
            caso_novo.get('avaliacao_critica', MIN_AVALIACAO),
            caso_base.get('avaliacao_critica', MIN_AVALIACAO),
            MAX_DIFF_AVALIACAO
        )
        similaridades_ponderadas.append(sim_aval * pesos['avaliacao_critica'])
        soma_pesos_aplicados += pesos['avaliacao_critica']

    # Tem Sequência
    if 'tem_sequencia' in pesos and pesos['tem_sequencia'] > 0 and 'tem_sequencia' in caso_novo and 'tem_sequencia' in caso_base:
        sim_seq = similaridade_categorica(caso_novo.get(
            'tem_sequencia'), caso_base.get('tem_sequencia'))
        similaridades_ponderadas.append(sim_seq * pesos['tem_sequencia'])
        soma_pesos_aplicados += pesos['tem_sequencia']

    if soma_pesos_aplicados == 0:
        return 0.0

    return sum(similaridades_ponderadas) / soma_pesos_aplicados

# --- 4. Recuperação e Interface com o Usuário ---


def obter_caso_entrada_do_usuario(pesos_atuais):
    """Coleta os dados do novo caso e os pesos do usuário."""
    print("\n--- Entrar com Novo Caso (Filme Desejado) ---")
    novo_caso = {}
    pesos_novos = pesos_atuais.copy()

    # Gênero
    print(f"Gêneros disponíveis: {', '.join(GENEROS_POSSIVEIS)}")
    while True:
        val = input(
            f"Gênero desejado (pressione Enter para ignorar): ").strip().title()
        if not val:
            break
        if val in GENEROS_POSSIVEIS:
            novo_caso['genero'] = val
            break
        print(
            f"Gênero '{val}' não está na lista pré-definida. Gêneros comuns: {', '.join(GENEROS_POSSIVEIS)}")

    # Ano Lançamento
    while True:
        try:
            val_str = input(
                f"Ano de lançamento desejado (aprox., {MIN_ANO}-{MAX_ANO}, Enter para ignorar): ").strip()
            if not val_str:
                break
            val = int(val_str)
            # Não restringir estritamente ao range aqui, pois o usuário pode querer algo fora
            novo_caso['ano_lancamento'] = val
            break
        except ValueError:
            print("Entrada inválida para ano. Use um número.")

    # Classificação Etária
    print(
        f"Classificações Etárias disponíveis: {', '.join(CLASSIFICACOES_POSSIVEIS)}")
    while True:
        val = input(f"Classificação etária desejada (Enter para ignorar): ").strip(
        ).title()  # .title()
        if not val:
            break
        if val in CLASSIFICACOES_POSSIVEIS:
            novo_caso['classificacao_etaria'] = val
            break
        print(
            f"Classificação '{val}' não é padrão. Tente novamente ou deixe em branco. Padrões: {', '.join(CLASSIFICACOES_POSSIVEIS)}")

    # Duração Minutos
    while True:
        try:
            val_str = input(
                f"Duração em minutos desejada (aprox., {MIN_DURACAO}-{MAX_DURACAO}, Enter para ignorar): ").strip()
            if not val_str:
                break
            val = int(val_str)
            novo_caso['duracao_minutos'] = val
            break
        except ValueError:
            print("Entrada inválida para duração. Use um número.")

    # Avaliação Crítica
    while True:
        try:
            val_str = input(
                f"Avaliação crítica mínima desejada ({MIN_AVALIACAO}-{MAX_AVALIACAO}, Enter para ignorar): ").strip()
            if not val_str:
                break
            val = float(val_str.replace(',', '.'))
            novo_caso['avaliacao_critica'] = val
            break
        except ValueError:
            print("Entrada inválida para avaliação. Use um número (ex: 7.5).")

    # Tem Sequência
    print(f"Tem sequência? Opções: {', '.join(BOOLEANOS_POSSIVEIS)}")
    while True:
        val = input(
            f"Filme tem sequência (Sim/Não, Enter para ignorar)? ").strip().capitalize()
        if not val:
            break
        if val in BOOLEANOS_POSSIVEIS:
            novo_caso['tem_sequencia'] = val
            break
        print("Opção inválida. Use 'Sim' ou 'Não'.")

    print("\n--- Ajustar Pesos dos Atributos (0.0 a 1.0) ---")
    print("Deixe em branco para usar o valor padrão/atual.")
    for atributo, peso_atual in pesos_atuais.items():
        while True:
            try:
                novo_peso_str = input(
                    f"Peso para '{atributo}' (padrão: {peso_atual:.2f}): ").strip()
                if not novo_peso_str:
                    break
                novo_peso = float(novo_peso_str.replace(',', '.'))
                if 0.0 <= novo_peso <= 1.0:
                    pesos_novos[atributo] = novo_peso
                    break
                else:
                    print("Peso deve estar entre 0.0 e 1.0.")
            except ValueError:
                print("Entrada inválida para peso. Use um número (ex: 0.25).")

    if not novo_caso:
        print("Nenhum critério fornecido para o novo caso. Não é possível buscar.")
        return None, pesos_novos

    return novo_caso, pesos_novos


def exibir_resultados(caso_entrada, casos_ordenados):
    """Exibe o caso de entrada e os casos recuperados em ordem de similaridade."""
    print("\n\n--- RESULTADOS DA BUSCA ---")
    print("\nCaso de Entrada (Filme Buscado):")
    if caso_entrada:
        for chave, valor in caso_entrada.items():
            print(f"  {chave.replace('_', ' ').capitalize()}: {valor}")
    else:
        print("  Nenhum critério de busca fornecido.")

    print("\nFilmes Encontrados (ordenados por similaridade):")
    if not casos_ordenados:
        print(
            "  Nenhum filme encontrado na base ou critérios não permitiram correspondência.")
        return

    for item in casos_ordenados:
        filme = item['caso']
        similaridade = item['similaridade']
        print(f"\n  ------------------------------------")
        print(f"  Título: {filme['titulo']}")
        print(f"  Similaridade com entrada: {similaridade*100:.2f}%")
        for chave, valor in filme.items():
            if chave != 'titulo':
                print(f"    {chave.replace('_', ' ').capitalize()}: {valor}")
    print(f"  ------------------------------------")

# --- NOVA FUNÇÃO PARA SALVAR EM MARKDOWN ---


def salvar_resultados_em_markdown(caso_entrada, casos_ordenados, nome_arquivo_base="resultado_busca_filmes"):
    """Salva o caso de entrada e os casos recuperados em um arquivo Markdown."""
    if not caso_entrada and not casos_ordenados:
        print("Nada para salvar.")
        return

    # Adiciona timestamp ao nome do arquivo para evitar sobrescrever
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"{nome_arquivo_base}_{timestamp}.md"

    try:
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            f.write("# Resultados da Busca de Filmes\n\n")

            f.write("## Caso de Entrada (Filme Buscado)\n\n")
            if caso_entrada:
                for chave, valor in caso_entrada.items():
                    f.write(
                        f"- **{chave.replace('_', ' ').capitalize()}**: {valor}\n")
            else:
                f.write("- Nenhum critério de busca fornecido.\n")
            f.write("\n")

            f.write("## Filmes Encontrados (ordenados por similaridade)\n")
            if not casos_ordenados:
                f.write(
                    "- Nenhum filme encontrado na base ou critérios não permitiram correspondência.\n")
            else:
                for item in casos_ordenados:
                    filme = item['caso']
                    similaridade = item['similaridade']
                    f.write("\n---\n\n")  # Separador horizontal
                    f.write(f"### Título: {filme['titulo']}\n\n")
                    f.write(
                        f"- **Similaridade com entrada**: {similaridade*100:.2f}%\n")
                    for chave, valor in filme.items():
                        if chave != 'titulo':
                            f.write(
                                f"  - **{chave.replace('_', ' ').capitalize()}**: {valor}\n")
        print(f"\nResultados salvos com sucesso no arquivo: {nome_arquivo}")
    except IOError as e:
        print(f"Erro ao salvar o arquivo '{nome_arquivo}': {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao tentar salvar o arquivo: {e}")


# --- Função Principal ---
def main():
    print("Bem-vindo ao Protótipo de RBC para Recomendação de Filmes!")

    if not BASE_DE_CASOS:
        print(
            "ERRO CRÍTICO: A base de casos está vazia e não foi possível carregar exemplos.")
        print("Verifique se o arquivo 'filmes_base.csv' existe e está formatado corretamente ou descomente o fallback no código.")
        return  # Termina o programa se não houver casos

    pesos_atuais = PESOS_PADRAO.copy()

    while True:
        novo_caso, pesos_modificados = obter_caso_entrada_do_usuario(
            pesos_atuais)
        pesos_atuais = pesos_modificados

        casos_ordenados_para_salvar = []  # Inicializa para o caso de não haver busca

        if novo_caso is None:
            print("Nenhum caso de entrada fornecido para comparação.")
        else:
            resultados_similaridade = []
            for caso_base in BASE_DE_CASOS:
                sim = calcular_similaridade_global(
                    novo_caso, caso_base, pesos_atuais)
                resultados_similaridade.append(
                    {'caso': caso_base, 'similaridade': sim})

            casos_ordenados = sorted(
                resultados_similaridade, key=lambda x: x['similaridade'], reverse=True)
            casos_ordenados_para_salvar = casos_ordenados  # Guarda para possível salvamento

            exibir_resultados(novo_caso, casos_ordenados)

            # --- PERGUNTAR SE DESEJA SALVAR ---
            while True:
                salvar = input(
                    "\nVocê deseja salvar o resultado em arquivo? (s/N): ").strip().lower()
                if salvar == 's':
                    salvar_resultados_em_markdown(
                        novo_caso, casos_ordenados_para_salvar)
                    break
                # Aceita 'n' ou Enter (vazio) como não
                elif salvar == 'n' or not salvar:
                    print("Resultado não será salvo.")
                    break
                else:
                    print("Opção inválida. Digite 's' para sim ou 'n' para não.")

        continuar = input(
            "\nDeseja realizar outra busca? (s/N): ").strip().lower()
        if continuar != 's':
            break

    print("Obrigado por usar o sistema de recomendação!")


if __name__ == "__main__":
    main()
