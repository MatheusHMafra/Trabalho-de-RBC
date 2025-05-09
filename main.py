import csv
import datetime  # Import para nomear o arquivo com data/hora
import re  # For parsing duration

# --- Mapeamento de Atributos para o CBR (Original Comment) ---
# titulo (title), generos (genre), ano_lancamento (year),
# classificacao_etaria (rating_mpa), duracao_minutos (duration),
# avaliacao_critica (rating_imdb), votos (vote), orcamento (budget),
# bilheteria_mundial (gross_world_wide), diretores (director),
# roteiristas (writer), estrelas (star), pais_origem (country_origin),
# idioma (language), vitorias (win), indicacoes (nomination), oscars_indicados (oscar)

# --- Visão Geral dos Atributos, Pesos e Métricas de Similaridade ---
# Esta seção é inspirada na estrutura tabular para clareza, conforme solicitado.
#
# Colunas:
#   1. Atributo (Chave no Dicionário do Caso): O nome do campo do filme usado no sistema.
#   2. Peso Padrão: A importância padrão do atributo no cálculo da similaridade global (definido em PESOS_PADRAO).
#   3. Métrica de Similaridade Local: A função Python específica usada para calcular a similaridade para este atributo.
#   4. Parâmetros da Métrica: Constantes ou estruturas de dados relevantes usadas pela métrica (e.g., ranges Min/Max
#      para normalização, mapas para valores ordinais, ou indicação de que listas de strings são usadas diretamente).
#
# ------------------------------------------------------------------------------------------------------------------------------------
# | Atributo              | Peso Padrão | Métrica de Similaridade Local        | Parâmetros da Métrica (Constantes/Estruturas)       |
# |-----------------------|-------------|--------------------------------------|-----------------------------------------------------|
# | generos               | 0.20        | similaridade_jaccard                 | (Usa diretamente as listas de gêneros)              |
# | ano_lancamento        | 0.10        | similaridade_numerica_normalizada    | MIN_ANO, MAX_ANO                                    |
# | classificacao_etaria  | 0.10        | similaridade_ordinal_mpaa            | CLASSIFICACAO_MPAA_MAPA_ORDINAL,                    |
# |                       |             |                                      | MAX_DIFF_CLASSIFICACAO_MPAA                         |
# | duracao_minutos       | 0.05        | similaridade_numerica_normalizada    | MIN_DURACAO, MAX_DURACAO                            |
# | avaliacao_critica     | 0.15        | similaridade_numerica_normalizada    | MIN_AVALIACAO_IMDB, MAX_AVALIACAO_IMDB              |
# | votos                 | 0.05        | similaridade_numerica_normalizada    | MIN_VOTOS, MAX_VOTOS                                |
# | orcamento             | 0.05        | similaridade_numerica_normalizada    | MIN_ORCAMENTO, MAX_ORCAMENTO                        |
# | bilheteria_mundial    | 0.05        | similaridade_numerica_normalizada    | MIN_BILHETERIA_MUNDIAL, MAX_BILHETERIA_MUNDIAL      |
# | diretores             | 0.05        | similaridade_jaccard                 | (Usa diretamente as listas de diretores)            |
# | roteiristas           | 0.05        | similaridade_jaccard                 | (Usa diretamente as listas de roteiristas)          |
# | estrelas              | 0.10        | similaridade_jaccard                 | (Usa diretamente as listas de estrelas)             |
# | pais_origem           | 0.02        | similaridade_jaccard                 | (Usa diretamente as listas de países)               |
# | idioma                | 0.02        | similaridade_jaccard                 | (Usa diretamente as listas de idiomas)              |
# | vitorias              | 0.03        | similaridade_numerica_normalizada    | MIN_VITORIAS, MAX_VITORIAS                          |
# | indicacoes            | 0.02        | similaridade_numerica_normalizada    | MIN_INDICACOES, MAX_INDICACOES                      |
# | oscars_indicados      | 0.01        | similaridade_numerica_normalizada    | MIN_OSCARS_INDICADOS, MAX_OSCARS_INDICADOS          |
# ------------------------------------------------------------------------------------------------------------------------------------
#
# Similaridade Jaccard: Usada para atributos categóricos com múltiplos valores (listas), como gêneros, diretores, estrelas, etc.
# Como funciona:
#   1. Converte as duas listas de itens (ex: listas de gêneros de dois filmes) em conjuntos (sets) para remover duplicatas e facilitar a comparação.
#   2. Calcula o número de itens em comum entre os dois conjuntos (interseção).
#   3. Calcula o número total de itens únicos presentes em ambos os conjuntos combinados (união).
#   4. A similaridade é a razão entre o tamanho da interseção e o tamanho da união ($S_{Jaccard}(A, B) = \frac{|A \cap B|}{|A \cup B|}$).
#   5. Se ambas as listas forem vazias ou contiverem apenas itens inválidos, a similaridade é 1.0 (considerados totalmente similares por falta de informação).
#   6. Se uma lista for vazia/inválida e a outra não, a similaridade é 0.0.
#
# Similaridade Numérica Normalizada: Usada para atributos numéricos, como ano de lançamento, duração, avaliação, orçamento, etc.
# Como funciona:
#   1. Recebe dois valores numéricos ($val1$, $val2$) e os valores mínimo ($min\_val$) e máximo ($max\_val$) possíveis para aquele atributo na base de dados.
#   2. Calcula a diferença absoluta entre os dois valores: $diff = |val1 - val2|$.
#   3. Calcula o intervalo total (range) dos valores possíveis para o atributo: $max\_diff = max\_val - min\_val$.
#   4. A similaridade é calculada como $1 - \frac{diff}{max\_diff}$. Isso resulta em um valor entre 0 e 1.
#      - Se $val1$ e $val2$ são iguais, $diff = 0$, e a similaridade é 1.0 (máxima).
#      - Se a diferença entre $val1$ e $val2$ é igual ao $max\_diff$, a similaridade é 0.0 (mínima).
#   5. Se um dos valores for `None` (ausente), a similaridade é 0.0.
#   6. Se $max\_diff$ for 0 (todos os valores na base para esse atributo são iguais), a similaridade é 1.0 se $val1 = val2$, e 0.0 caso contrário.
#
# Similaridade Ordinal MPAA: Usada para classificações etárias (MPAA e outras), que possuem uma ordem intrínseca (ex: G é menos restritivo que PG-13, que é menos restritivo que R).
# Como funciona:
#   1. Utiliza um mapa pré-definido (`CLASSIFICACAO_MPAA_MAPA_ORDINAL`) que atribui um valor numérico (índice) a cada classificação etária, refletindo sua ordem de restrição.
#      Por exemplo, "G" pode ser 0, "PG" pode ser 1, "PG-13" pode ser 2, etc.
#   2. Obtém os valores numéricos ordinais para as duas classificações etárias sendo comparadas ($val1_{num}$, $val2_{num}$).
#   3. Calcula a diferença absoluta entre esses dois valores numéricos ordinais: $diff_{ordinal} = |val1_{num} - val2_{num}|$.
#   4. Normaliza essa diferença dividindo-a pela máxima diferença possível na escala ordinal (`MAX_DIFF_CLASSIFICACAO_MPAA`), que é o número total de classificações menos 1.
#   5. A similaridade é calculada como $1 - \frac{diff_{ordinal}}{MAX\_DIFF\_CLASSIFICACAO\_MPAA}$.
#   6. Se uma ou ambas as classificações não estiverem no mapa ordinal, a função realiza uma comparação direta de strings: 1.0 se forem idênticas, 0.0 caso contrário.
#   7. Valores `None` ou vazios são tratados como "Unrated" para fins de mapeamento.


# --- 1. Representação do Caso e Base de Casos ---

# Valores possíveis para atributos categóricos (para geração e validação)
GENEROS_POSSIVEIS_EXEMPLO = ["Action", "Comedy", "Drama", "Sci-Fi", "Thriller", "Romance",
                             "Animation", "Horror", "Adventure", "Crime", "Fantasy", "War", "Western", "Mystery", "Musical", "Biography", "History", "Family", "Sport"]

# Classificações MPAA e outras encontradas, com uma tentativa de ordenação ordinal
# Do menos restritivo para o mais restritivo. Esta ordem é uma interpretação.
CLASSIFICACOES_MPAA_POSSIVEIS = [
    "Unrated", "Not Rated", "Unknown",  # Não classificado ou desconhecido
    "Approved", "Passed",  # Sistemas antigos, geralmente para todos os públicos
    "K-A",  # Kids to Adults (similar a G) - Antigo
    "TV-Y",  # All Children (TV)
    "G", "TV-G",  # Geral
    "GP",  # Antigo, precursor do PG
    "M",  # Antigo, precursor do PG/PG-13
    "PG", "TV-PG",  # Orientação parental sugerida
    "M/PG",  # Intermediário (Antigo)
    "TV-Y7", "TV-Y7-FV",  # Crianças mais velhas (TV)
    "13+",  # Restrição de idade, similar a PG-13/TV-14
    "PG-13",  # Orientação parental fortemente aconselhada para menores de 13
    "TV-13",  # Similar a TV-14 (Antigo TV)
    # Orientação parental fortemente aconselhada para menores de 14 (TV)
    "TV-14",
    "16+",  # Restrição de idade
    "R",  # Restrito, menores de 17 acompanhados
    "MA-17",  # Mature Audience, 17 and over (similar a NC-17 ou R forte)
    "TV-MA",  # Público Adulto (TV)
    "NC-17",  # Adultos apenas (substituiu o X em muitos casos)
    # Adultos apenas (sistema antigo ou filmes não classificados pela MPAA)
    "X",
    "18+"  # Restrição de idade para adultos
]
CLASSIFICACAO_MPAA_MAPA_ORDINAL = {
    val: i for i, val in enumerate(CLASSIFICACOES_MPAA_POSSIVEIS)}
MAX_DIFF_CLASSIFICACAO_MPAA = len(CLASSIFICACOES_MPAA_POSSIVEIS) - 1

# Ranges para normalização
MIN_ANO = 1920
MAX_ANO = datetime.datetime.now().year
MAX_DIFF_ANOS = MAX_ANO - MIN_ANO

MIN_DURACAO = 30
MAX_DURACAO = 300  # Ajustar se houver filmes mais longos
MAX_DIFF_DURACAO = MAX_DURACAO - MIN_DURACAO

MIN_AVALIACAO_IMDB = 0.0
MAX_AVALIACAO_IMDB = 10.0
MAX_DIFF_AVALIACAO_IMDB = MAX_AVALIACAO_IMDB - MIN_AVALIACAO_IMDB

MIN_VOTOS = 0
MAX_VOTOS = 3000000  # Ajustar conforme o máximo observado no dataset
MAX_DIFF_VOTOS = MAX_VOTOS - MIN_VOTOS

MIN_ORCAMENTO = 1000
MAX_ORCAMENTO = 500000000  # Ajustar
MAX_DIFF_ORCAMENTO = MAX_ORCAMENTO - MIN_ORCAMENTO

MIN_BILHETERIA_MUNDIAL = 0
MAX_BILHETERIA_MUNDIAL = 3000000000  # Ajustar
MAX_DIFF_BILHETERIA_MUNDIAL = MAX_BILHETERIA_MUNDIAL - MIN_BILHETERIA_MUNDIAL

MIN_VITORIAS = 0
MAX_VITORIAS = 200  # Ajustar
MAX_DIFF_VITORIAS = MAX_VITORIAS - MIN_VITORIAS

MIN_INDICACOES = 0
MAX_INDICACOES = 300  # Ajustar
MAX_DIFF_INDICACOES = MAX_INDICACOES - MIN_INDICACOES

MIN_OSCARS_INDICADOS = 0
MAX_OSCARS_INDICADOS = 50  # Ajustar
MAX_DIFF_OSCARS_INDICADOS = MAX_OSCARS_INDICADOS - MIN_OSCARS_INDICADOS


def parse_duration_to_minutes(duration_str):
    """Converte string de duração (ex: "120 min", "PT2H30M", "2h 30m", "150") para minutos."""
    if not duration_str or not isinstance(duration_str, str):
        return None
    duration_str_lower = str(duration_str).lower()

    # Tenta encontrar um número seguido opcionalmente por "min" ou "mins"
    match = re.match(r"(\d+)\s*(min)?s?", duration_str_lower)
    if match:
        return int(match.group(1))

    # Tenta encontrar padrões como "Xh Ym" ou "Xh" ou "Ym"
    hours = 0
    minutes = 0
    h_match = re.search(r"(\d+)h", duration_str_lower)
    if h_match:
        hours = int(h_match.group(1))
    m_match = re.search(r"(\d+)m", duration_str_lower)
    if m_match:
        minutes = int(m_match.group(1))

    if hours > 0 or minutes > 0:
        return hours * 60 + minutes

    # Tenta interpretar o formato ISO 8601 PTxHxMxS (parcialmente)
    if duration_str_lower.startswith("pt"):
        duration_str_iso = duration_str_lower[2:] # Remove "pt"
        h_val = 0
        m_val = 0
        if 'h' in duration_str_iso:
            parts = duration_str_iso.split('h')
            try:
                h_val = int(parts[0])
            except ValueError:
                pass # Ignora se a parte antes de 'h' não for um número
            if len(parts) > 1 and parts[1]: # Se houver algo depois de 'h'
                m_match_iso = re.search(r"(\d+)m", parts[1])
                if m_match_iso:
                    try:
                        m_val = int(m_match_iso.group(1))
                    except ValueError:
                        pass # Ignora se a parte antes de 'm' não for um número
        elif 'm' in duration_str_iso: # Caso não tenha 'h', mas tenha 'm'
            m_match_iso = re.search(r"(\d+)m", duration_str_iso)
            if m_match_iso:
                try:
                    m_val = int(m_match_iso.group(1))
                except ValueError:
                    pass # Ignora se a parte antes de 'm' não for um número
        
        if h_val > 0 or m_val > 0:
            return h_val * 60 + m_val

    # Última tentativa: converter diretamente para int, assumindo que já são minutos
    try:
        return int(duration_str)
    except ValueError:
        print(
            f"Aviso: Formato de duração desconhecido '{duration_str}'. Será ignorado.")
        return None


def parse_comma_separated_string(value_str):
    """Converte uma string separada por vírgulas em uma lista de strings limpas."""
    if not value_str or not isinstance(value_str, str):
        return []
    return [item.strip() for item in value_str.split(',') if item.strip()]


def carregar_base_de_casos_csv(caminho_arquivo="filmes_base_novo.csv"):
    """Carrega a base de casos de um arquivo CSV com o novo schema."""
    base = []
    try:
        with open(caminho_arquivo, mode='r', encoding='utf-8') as arquivo_csv:
            leitor_csv = csv.DictReader(arquivo_csv)
            for linha in leitor_csv:
                try:
                    duracao_min = parse_duration_to_minutes(
                        linha.get("duration"))

                    def to_int(val_str):
                        if val_str is None or val_str == '':
                            return None
                        try:
                            # Remove ".0" se for um float formatado como string (ex: "1999.0")
                            if isinstance(val_str, str) and val_str.endswith(".0"):
                                val_str = val_str[:-2]
                            return int(val_str)
                        except ValueError:
                            return None

                    def to_float(val_str):
                        if val_str is None or val_str == '':
                            return None
                        try:
                            return float(str(val_str).replace(',', '.'))
                        except ValueError:
                            return None

                    ano_lancamento = to_int(linha.get("year"))
                    avaliacao_critica = to_float(linha.get("rating_imdb"))
                    votos = to_int(linha.get("vote"))
                    orcamento = to_float(linha.get("budget")) # Pode ser float devido a valores grandes
                    bilheteria_mundial = to_float(
                        linha.get("gross_world_wide")) # Pode ser float
                    vitorias = to_int(linha.get("win"))
                    indicacoes = to_int(linha.get("nomination"))
                    oscars_indicados = to_int(linha.get("oscar"))

                    classificacao_etaria_raw = linha.get(
                        "rating_mpa", "").strip()
                    classificacao_etaria_final = "Unrated"  # Padrão se vazio ou não reconhecido

                    if classificacao_etaria_raw:  # Processa apenas se não for vazio
                        if classificacao_etaria_raw.lower() in ["none", "na", "n/a", "", "nan"]:
                            classificacao_etaria_final = "Unrated"
                        elif classificacao_etaria_raw in CLASSIFICACOES_MPAA_POSSIVEIS:
                            classificacao_etaria_final = classificacao_etaria_raw
                        else:
                            # Tenta normalizar (ex: "PG 13" -> "PG-13")
                            normalized_rating = classificacao_etaria_raw.upper().replace(" ", "-")
                            if normalized_rating in CLASSIFICACOES_MPAA_POSSIVEIS:
                                classificacao_etaria_final = normalized_rating
                            else:
                                # Mantém o original se não mapeado e imprime aviso
                                classificacao_etaria_final = classificacao_etaria_raw 
                                print(
                                    f"Aviso: Classificação MPAA '{classificacao_etaria_raw}' do filme '{linha.get('title', 'DESCONHECIDO')}' não está na lista padrão. Será usado como está. Padrões: {CLASSIFICACOES_MPAA_POSSIVEIS}")
                    
                    # Adiciona o caso à base
                    caso = {
                        "id": linha.get("id"),
                        "titulo": linha.get("title", "Título Desconhecido"),
                        "link": linha.get("link"),
                        "ano_lancamento": ano_lancamento,
                        "duracao_minutos": duracao_min,
                        "classificacao_etaria": classificacao_etaria_final,
                        "avaliacao_critica": avaliacao_critica,
                        "votos": votos,
                        "orcamento": orcamento,
                        "bilheteria_mundial": bilheteria_mundial,
                        "diretores": parse_comma_separated_string(linha.get("director")),
                        "roteiristas": parse_comma_separated_string(linha.get("writer")),
                        "estrelas": parse_comma_separated_string(linha.get("star")),
                        "generos": parse_comma_separated_string(linha.get("genre")),
                        "pais_origem": parse_comma_separated_string(linha.get("country_origin")),
                        "idioma": parse_comma_separated_string(linha.get("language")),
                        "vitorias": vitorias,
                        "indicacoes": indicacoes,
                        "oscars_indicados": oscars_indicados,
                        # Campos adicionais (não usados no cálculo de similaridade padrão, mas carregados)
                        "gross_us_canada": linha.get("gross_us_canada"),
                        "gross_opening_weekend": linha.get("gross_opening_weekend"),
                        "filming_location": parse_comma_separated_string(linha.get("filming_location")),
                        "production_company": parse_comma_separated_string(linha.get("production_company"))
                    }
                    base.append(caso)
                except ValueError as e:
                    print(
                        f"Erro ao converter dados para o filme {linha.get('title', 'DESCONHECIDO')}: {e}. Pulando este filme.")
                except KeyError as e:
                    print(
                        f"Coluna ausente {e} para o filme {linha.get('title', 'DESCONHECIDO')}. Pulando este filme.")
            
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


# Carrega a base de casos globalmente ao iniciar o script
BASE_DE_CASOS = carregar_base_de_casos_csv()

# Se a base estiver vazia após a tentativa de carregamento, adiciona exemplos
if not BASE_DE_CASOS:
    print("Base de casos está vazia. Adicionando alguns exemplos para demonstração (com o novo schema).")
    BASE_DE_CASOS.extend([
        {"id": "tt0133093", "titulo": "The Matrix (Exemplo)", "link": "link1", "ano_lancamento": 1999, "duracao_minutos": 136,
         "classificacao_etaria": "R", "avaliacao_critica": 8.7, "votos": 1800000, "orcamento": 63000000,
         "bilheteria_mundial": 463517383, "diretores": ["Lana Wachowski", "Lilly Wachowski"], "roteiristas": ["Lana Wachowski", "Lilly Wachowski"],
         "estrelas": ["Keanu Reeves", "Laurence Fishburne", "Carrie-Anne Moss"], "generos": ["Action", "Sci-Fi"],
         "pais_origem": ["USA"], "idioma": ["English"], "vitorias": 40, "indicacoes": 50, "oscars_indicados": 4},
        {"id": "tt0068646", "titulo": "The Godfather (Exemplo)", "link": "link2", "ano_lancamento": 1972, "duracao_minutos": 175,
         "classificacao_etaria": "R", "avaliacao_critica": 9.2, "votos": 1700000, "orcamento": 6000000,
         "bilheteria_mundial": 246120974, "diretores": ["Francis Ford Coppola"], "roteiristas": ["Mario Puzo", "Francis Ford Coppola"],
         "estrelas": ["Marlon Brando", "Al Pacino", "James Caan"], "generos": ["Crime", "Drama"],
         "pais_origem": ["USA"], "idioma": ["English", "Italian"], "vitorias": 30, "indicacoes": 40, "oscars_indicados": 3},
        {"id": "tt0114709", "titulo": "Toy Story (Exemplo)", "link": "link3", "ano_lancamento": 1995, "duracao_minutos": 81,
         "classificacao_etaria": "G", "avaliacao_critica": 8.3, "votos": 950000, "orcamento": 30000000,
         "bilheteria_mundial": 373554033, "diretores": ["John Lasseter"], "roteiristas": ["John Lasseter", "Pete Docter"],
         "estrelas": ["Tom Hanks", "Tim Allen"], "generos": ["Animation", "Adventure", "Comedy"],
         "pais_origem": ["USA"], "idioma": ["English"], "vitorias": 25, "indicacoes": 30, "oscars_indicados": 1}
    ])

# --- 2. Métricas de Similaridade ---


def similaridade_categorica_simples(val1, val2):
    """Similaridade para atributos categóricos de valor único."""
    return 1.0 if val1 == val2 else 0.0

def similaridade_jaccard(lista1, lista2):
    """Similaridade de Jaccard para atributos com múltiplos valores (listas)."""
    # Garante que ambos os inputs sejam listas, mesmo que vazias ou com um único item
    if not isinstance(lista1, list):
        lista1 = [lista1] if lista1 is not None else []
    if not isinstance(lista2, list):
        lista2 = [lista2] if lista2 is not None else []

    # Remove Nones ou strings vazias antes de converter para set para evitar erros
    set1 = set(item for item in lista1 if item and str(item).strip())
    set2 = set(item for item in lista2 if item and str(item).strip())

    if not set1 and not set2:  # Ambas as listas estão vazias ou contêm apenas itens inválidos
        return 1.0 # Considera-se similaridade total se ambos não têm informação válida
    if not set1 or not set2:  # Uma está vazia/inválida e a outra não
        return 0.0 # Nenhuma similaridade se um tem informação e o outro não

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union != 0 else 0.0

def similaridade_numerica_normalizada(val1, val2, min_val, max_val):
    """Similaridade para atributos numéricos normalizada."""
    if val1 is None or val2 is None:
        return 0.0  # Se um dos valores for None, similaridade é 0
    # Adiciona verificação para min_val e max_val não serem None
    if min_val is None or max_val is None:
        # Se min/max não definidos, só há similaridade se os valores forem iguais
        return 0.0 if val1 != val2 else 1.0 

    max_diff = max_val - min_val
    if max_diff == 0: # Evita divisão por zero se todos os valores na base forem iguais
        return 1.0 if val1 == val2 else 0.0
    
    # Garante que os valores são numéricos antes de calcular a diferença
    if not (isinstance(val1, (int, float)) and isinstance(val2, (int, float))):
        return 0.0 # Não numérico, não comparável desta forma
        
    diff = abs(val1 - val2)
    sim = 1.0 - (diff / max_diff)
    return max(0.0, sim) # Garante que a similaridade não seja negativa


def similaridade_ordinal_mpaa(val1_str, val2_str):
    """Similaridade para classificação etária MPAA e outras (ordinal)."""
    # Garante que os valores de entrada sejam strings e trata Nones como "Unrated"
    s_val1 = str(val1_str if val1_str is not None and str(val1_str).strip() else "Unrated")
    s_val2 = str(val2_str if val2_str is not None and str(val2_str).strip() else "Unrated")

    # Tenta normalizar o valor para corresponder às chaves do mapa (ex: "PG 13" -> "PG-13")
    val1_norm = s_val1 if s_val1 in CLASSIFICACAO_MPAA_MAPA_ORDINAL else s_val1.upper().replace(" ", "-")
    val2_norm = s_val2 if s_val2 in CLASSIFICACAO_MPAA_MAPA_ORDINAL else s_val2.upper().replace(" ", "-")
    
    val1_num = CLASSIFICACAO_MPAA_MAPA_ORDINAL.get(val1_norm)
    val2_num = CLASSIFICACAO_MPAA_MAPA_ORDINAL.get(val2_norm)

    if val1_num is None or val2_num is None:
        # Se um ou ambos não estão no mapa ordinal, faz comparação direta de strings.
        # Se forem iguais (ex: ambos são "Not Available" não mapeado), similaridade 1.
        # Se diferentes, similaridade 0.
        return 1.0 if s_val1 == s_val2 else 0.0 

    if MAX_DIFF_CLASSIFICACAO_MPAA == 0: # Improvável com a lista expandida
        return 1.0 if val1_num == val2_num else 0.0
    return 1.0 - (abs(val1_num - val2_num) / MAX_DIFF_CLASSIFICACAO_MPAA)

# --- 3. Função de Similaridade Global ---

# Pesos padrão para cada atributo. Podem ser ajustados pelo usuário.
PESOS_PADRAO = {
    "generos": 0.20,
    "ano_lancamento": 0.10,
    "classificacao_etaria": 0.10,
    "duracao_minutos": 0.05,
    "avaliacao_critica": 0.15,
    "votos": 0.05,
    "orcamento": 0.05,
    "bilheteria_mundial": 0.05,
    "diretores": 0.05,
    "roteiristas": 0.05,
    "estrelas": 0.10,
    "pais_origem": 0.02,
    "idioma": 0.02,
    "vitorias": 0.03,
    "indicacoes": 0.02,
    "oscars_indicados": 0.01
    # Outros campos como 'gross_us_canada' não são usados por padrão, mas poderiam ser adicionados.
}


def calcular_similaridade_global(caso_novo, caso_base, pesos):
    """Calcula a similaridade global entre dois casos usando média ponderada."""
    if not caso_novo or not caso_base: # Casos inválidos
        return 0.0

    similaridades_ponderadas = []
    pesos_efetivamente_usados = 0.0

    # Função auxiliar para adicionar similaridade ponderada se o atributo for relevante
    def adicionar_similaridade(chave_atributo, similaridade_calculada):
        nonlocal pesos_efetivamente_usados # Permite modificar a variável externa
        peso_atributo = pesos.get(chave_atributo, 0) # Pega o peso, default 0 se não existir
        if peso_atributo > 0: # Só considera se o peso for positivo
            similaridades_ponderadas.append(
                similaridade_calculada * peso_atributo)
            pesos_efetivamente_usados += peso_atributo
        # else:
            # print(f"Debug: Atributo '{chave_atributo}' com peso zero ou não encontrado nos pesos.")


    # --- Cálculo de similaridade para cada atributo ---
    # A lógica abaixo verifica se o atributo existe e tem valor em AMBOS os casos (novo e base)
    # E se o atributo tem um peso definido > 0.

    # Gêneros (Jaccard)
    if 'generos' in caso_novo and 'generos' in caso_base and pesos.get("generos", 0) > 0:
        sim_gen = similaridade_jaccard(caso_novo.get(
            'generos', []), caso_base.get('generos', []))
        adicionar_similaridade("generos", sim_gen)

    # Ano Lançamento (Numérico Normalizado)
    if caso_novo.get('ano_lancamento') is not None and caso_base.get('ano_lancamento') is not None and pesos.get("ano_lancamento", 0) > 0:
        sim_ano = similaridade_numerica_normalizada(
            caso_novo['ano_lancamento'], caso_base['ano_lancamento'], MIN_ANO, MAX_ANO
        )
        adicionar_similaridade("ano_lancamento", sim_ano)

    # Classificação Etária (Ordinal MPAA)
    if 'classificacao_etaria' in caso_novo and 'classificacao_etaria' in caso_base and pesos.get("classificacao_etaria", 0) > 0:
        sim_class = similaridade_ordinal_mpaa(
            caso_novo.get('classificacao_etaria'), caso_base.get(
                'classificacao_etaria')
        )
        adicionar_similaridade("classificacao_etaria", sim_class)

    # Duração Minutos (Numérico Normalizado)
    if caso_novo.get('duracao_minutos') is not None and caso_base.get('duracao_minutos') is not None and pesos.get("duracao_minutos", 0) > 0:
        sim_dur = similaridade_numerica_normalizada(
            caso_novo['duracao_minutos'], caso_base['duracao_minutos'], MIN_DURACAO, MAX_DURACAO
        )
        adicionar_similaridade("duracao_minutos", sim_dur)

    # Avaliação Crítica (Numérico Normalizado)
    if caso_novo.get('avaliacao_critica') is not None and caso_base.get('avaliacao_critica') is not None and pesos.get("avaliacao_critica", 0) > 0:
        sim_aval = similaridade_numerica_normalizada(
            caso_novo['avaliacao_critica'], caso_base['avaliacao_critica'], MIN_AVALIACAO_IMDB, MAX_AVALIACAO_IMDB
        )
        adicionar_similaridade("avaliacao_critica", sim_aval)
    
    # Votos (Numérico Normalizado)
    if caso_novo.get('votos') is not None and caso_base.get('votos') is not None and pesos.get("votos", 0) > 0:
        sim_votos = similaridade_numerica_normalizada(
            caso_novo['votos'], caso_base['votos'], MIN_VOTOS, MAX_VOTOS
        )
        adicionar_similaridade("votos", sim_votos)

    # Orçamento (Numérico Normalizado)
    if caso_novo.get('orcamento') is not None and caso_base.get('orcamento') is not None and pesos.get("orcamento", 0) > 0:
        sim_orc = similaridade_numerica_normalizada(
            caso_novo['orcamento'], caso_base['orcamento'], MIN_ORCAMENTO, MAX_ORCAMENTO
        )
        adicionar_similaridade("orcamento", sim_orc)

    # Bilheteria Mundial (Numérico Normalizado)
    if caso_novo.get('bilheteria_mundial') is not None and caso_base.get('bilheteria_mundial') is not None and pesos.get("bilheteria_mundial", 0) > 0:
        sim_bil = similaridade_numerica_normalizada(
            caso_novo['bilheteria_mundial'], caso_base['bilheteria_mundial'], MIN_BILHETERIA_MUNDIAL, MAX_BILHETERIA_MUNDIAL
        )
        adicionar_similaridade("bilheteria_mundial", sim_bil)

    # Diretores (Jaccard)
    if 'diretores' in caso_novo and 'diretores' in caso_base and pesos.get("diretores", 0) > 0:
        sim_dir = similaridade_jaccard(caso_novo.get(
            'diretores', []), caso_base.get('diretores', []))
        adicionar_similaridade("diretores", sim_dir)

    # Roteiristas (Jaccard)
    if 'roteiristas' in caso_novo and 'roteiristas' in caso_base and pesos.get("roteiristas", 0) > 0:
        sim_rot = similaridade_jaccard(caso_novo.get(
            'roteiristas', []), caso_base.get('roteiristas', []))
        adicionar_similaridade("roteiristas", sim_rot)

    # Estrelas (Jaccard)
    if 'estrelas' in caso_novo and 'estrelas' in caso_base and pesos.get("estrelas", 0) > 0:
        sim_star = similaridade_jaccard(caso_novo.get(
            'estrelas', []), caso_base.get('estrelas', []))
        adicionar_similaridade("estrelas", sim_star)

    # País de Origem (Jaccard)
    if 'pais_origem' in caso_novo and 'pais_origem' in caso_base and pesos.get("pais_origem", 0) > 0:
        sim_pais = similaridade_jaccard(caso_novo.get(
            'pais_origem', []), caso_base.get('pais_origem', []))
        adicionar_similaridade("pais_origem", sim_pais)

    # Idioma (Jaccard)
    if 'idioma' in caso_novo and 'idioma' in caso_base and pesos.get("idioma", 0) > 0:
        sim_idioma = similaridade_jaccard(caso_novo.get(
            'idioma', []), caso_base.get('idioma', []))
        adicionar_similaridade("idioma", sim_idioma)
        
    # Vitórias (Numérico Normalizado)
    if caso_novo.get('vitorias') is not None and caso_base.get('vitorias') is not None and pesos.get("vitorias", 0) > 0:
        sim_vit = similaridade_numerica_normalizada(
            caso_novo['vitorias'], caso_base['vitorias'], MIN_VITORIAS, MAX_VITORIAS
        )
        adicionar_similaridade("vitorias", sim_vit)

    # Indicações (Numérico Normalizado)
    if caso_novo.get('indicacoes') is not None and caso_base.get('indicacoes') is not None and pesos.get("indicacoes", 0) > 0:
        sim_ind = similaridade_numerica_normalizada(
            caso_novo['indicacoes'], caso_base['indicacoes'], MIN_INDICACOES, MAX_INDICACOES
        )
        adicionar_similaridade("indicacoes", sim_ind)

    # Oscars Indicados (Numérico Normalizado)
    if caso_novo.get('oscars_indicados') is not None and caso_base.get('oscars_indicados') is not None and pesos.get("oscars_indicados", 0) > 0:
        sim_osc = similaridade_numerica_normalizada(
            caso_novo['oscars_indicados'], caso_base['oscars_indicados'], MIN_OSCARS_INDICADOS, MAX_OSCARS_INDICADOS
        )
        adicionar_similaridade("oscars_indicados", sim_osc)


    if pesos_efetivamente_usados == 0:
        # Se nenhum atributo com peso > 0 foi fornecido ou correspondeu, a similaridade é 0.
        # Isso pode acontecer se o caso_novo tiver apenas atributos não ponderados,
        # ou se os atributos ponderados não existirem no caso_base.
        return 0.0

    return sum(similaridades_ponderadas) / pesos_efetivamente_usados


# --- 4. Recuperação e Interface com o Usuário ---
def obter_caso_entrada_do_usuario(pesos_atuais):
    """Coleta os dados do novo caso e os pesos do usuário."""
    print("\n--- Entrar com Novo Caso (Filme Desejado) ---")
    novo_caso = {}
    pesos_novos = pesos_atuais.copy() # Começa com os pesos atuais (padrão ou da última busca)

    # Coleta de informações para o novo caso (filme desejado)
    val_str = input(
        f"Gêneros desejados (separados por vírgula, ex: Action, Sci-Fi. Enter para ignorar): ").strip()
    if val_str:
        novo_caso['generos'] = parse_comma_separated_string(val_str)

    while True:
        try:
            val_str = input(
                f"Ano de lançamento desejado (aprox., {MIN_ANO}-{MAX_ANO}, Enter para ignorar): ").strip()
            if not val_str:
                break
            novo_caso['ano_lancamento'] = int(val_str)
            break
        except ValueError:
            print("Entrada inválida para ano. Use um número.")

    print(
        f"Classificações disponíveis (exemplos): {', '.join(CLASSIFICACOES_MPAA_POSSIVEIS[:7])}... etc.")
    while True:
        val = input(
            f"Classificação etária desejada (Enter para ignorar): ").strip()
        if not val:
            break
        # Tenta normalizar para melhor correspondência, mas aceita o valor do usuário se não for padrão
        val_norm_input = val.upper().replace(" ", "-")
        if val_norm_input in CLASSIFICACOES_MPAA_POSSIVEIS:
            novo_caso['classificacao_etaria'] = val_norm_input
        elif val in CLASSIFICACOES_MPAA_POSSIVEIS: # Caso o usuário digite exatamente como na lista
            novo_caso['classificacao_etaria'] = val
        else:
            novo_caso['classificacao_etaria'] = val # Usa o valor original se não for padrão
            print(
                f"Classificação '{val}' não está na lista pré-definida, mas será usada. Para melhores resultados, use uma da lista.")
        break


    while True:
        try:
            val_str = input(
                f"Duração em minutos desejada (aprox., {MIN_DURACAO}-{MAX_DURACAO}, Enter para ignorar): ").strip()
            if not val_str:
                break
            novo_caso['duracao_minutos'] = int(val_str)
            break
        except ValueError:
            print("Entrada inválida para duração. Use um número.")

    while True:
        try:
            val_str = input(
                f"Avaliação IMDb mínima desejada ({MIN_AVALIACAO_IMDB}-{MAX_AVALIACAO_IMDB}, Enter para ignorar): ").strip()
            if not val_str:
                break
            novo_caso['avaliacao_critica'] = float(val_str.replace(',', '.'))
            break
        except ValueError:
            print("Entrada inválida para avaliação. Use um número (ex: 7.5).")
    
    while True:
        try:
            val_str = input(
                f"Número mínimo de votos IMDb (Enter para ignorar): ").strip()
            if not val_str:
                break
            novo_caso['votos'] = int(val_str)
            break
        except ValueError:
            print("Entrada inválida para votos. Use um número.")

    val_str = input(
        f"Estrelas principais (separados por vírgula. Enter para ignorar): ").strip()
    if val_str:
        novo_caso['estrelas'] = parse_comma_separated_string(val_str)

    val_str = input(
        f"Diretor(es) (separados por vírgula. Enter para ignorar): ").strip()
    if val_str:
        novo_caso['diretores'] = parse_comma_separated_string(val_str)
    
    # Outros campos poderiam ser adicionados aqui (roteiristas, país, idioma, prêmios, etc.)

    # Ajuste de pesos
    print("\n--- Ajustar Pesos dos Atributos (0.0 a 1.0) ---")
    print("Deixe em branco para usar o valor padrão/atual.")
    for atributo, peso_atual in pesos_atuais.items():
        while True:
            try:
                novo_peso_str = input(
                    f"Peso para '{atributo}' (atual: {peso_atual:.2f}): ").strip()
                if not novo_peso_str: # Usuário pressionou Enter, mantém o peso atual
                    break
                novo_peso = float(novo_peso_str.replace(',', '.'))
                if 0.0 <= novo_peso <= 1.0:
                    pesos_novos[atributo] = novo_peso
                    break
                else:
                    print("Peso deve estar entre 0.0 e 1.0.")
            except ValueError:
                print("Entrada inválida para peso. Use um número (ex: 0.25).")
    
    if not novo_caso: # Se o usuário não forneceu nenhum critério para o filme
        print("Nenhum critério fornecido para o novo caso. Não é possível buscar.")
        return None, pesos_novos # Retorna None para o caso, mas os pesos (possivelmente modificados)
            
    return novo_caso, pesos_novos


def exibir_resultados(caso_entrada, casos_ordenados, top_n=10):
    """Exibe o caso de entrada e os TOP N casos recuperados."""
    print("\n\n--- RESULTADOS DA BUSCA ---")
    print("\nCaso de Entrada (Filme Buscado):")
    if caso_entrada:
        for chave, valor in caso_entrada.items():
            # Formata listas para exibição amigável
            if isinstance(valor, list):
                print(
                    f"  {chave.replace('_', ' ').capitalize()}: {', '.join(str(v) for v in valor) if valor else 'N/A'}")
            else:
                print(
                    f"  {chave.replace('_', ' ').capitalize()}: {valor if valor is not None else 'N/A'}")
    else:
        print("  Nenhum critério de busca fornecido.")

    # Filtra para mostrar apenas casos com similaridade > 0
    casos_para_exibir = [
        c for c in casos_ordenados if c['similaridade'] > 0][:top_n]

    if not casos_para_exibir:
        print("\nFilmes Encontrados (ordenados por similaridade):")
        print("  Nenhum filme encontrado com similaridade maior que zero ou critérios não permitiram correspondência.")
        return

    print(
        f"\nTop {len(casos_para_exibir)} Filmes Encontrados (ordenados por similaridade):")
    for item in casos_para_exibir:
        filme = item['caso']
        similaridade = item['similaridade']
        print(f"\n  ------------------------------------")
        print(f"  Título: {filme.get('titulo', 'N/A')}")
        if filme.get('link'): # Mostra o link se disponível
            print(f"  Link: {filme['link']}")
        print(f"  Similaridade com entrada: {similaridade*100:.2f}%")
        # Detalhes relevantes do filme encontrado
        print(f"    Gêneros: {', '.join(filme.get('generos', [])) or 'N/A'}")
        print(f"    Ano: {filme.get('ano_lancamento', 'N/A')}")
        print(f"    Duração: {filme.get('duracao_minutos', 'N/A')} min")
        print(f"    Classificação: {filme.get('classificacao_etaria', 'N/A')}")
        print(
            f"    Avaliação IMDb: {filme.get('avaliacao_critica', 'N/A')}/10 ({filme.get('votos', 'N/A')} votos)")
        if filme.get('diretores'):
            print(
                f"    Diretor(es): {', '.join(filme.get('diretores', [])) or 'N/A'}")
        if filme.get('estrelas'):
            print(
                f"    Estrelas: {', '.join(filme.get('estrelas', [])) or 'N/A'}")
    print(f"  ------------------------------------")


def salvar_resultados_em_markdown(caso_entrada, casos_ordenados, nome_arquivo_base="resultado_busca_filmes", top_n=10):
    """Salva o caso de entrada e os TOP N casos recuperados em um arquivo Markdown."""
    if not caso_entrada and (not casos_ordenados or not any(c['similaridade'] > 0 for c in casos_ordenados)):
        print("Nada para salvar (nenhuma entrada ou nenhum resultado relevante).")
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"{nome_arquivo_base}_{timestamp}.md"
    
    casos_para_salvar = [
        c for c in casos_ordenados if c['similaridade'] > 0][:top_n]

    try:
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            f.write("# Resultados da Busca de Filmes\n\n")
            f.write(
                f"Busca realizada em: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## Caso de Entrada (Filme Buscado)\n\n")
            if caso_entrada:
                for chave, valor in caso_entrada.items():
                    val_str = valor
                    if isinstance(valor, list):
                        val_str = ', '.join(str(v)
                                            for v in valor) if valor else "N/A"
                    elif valor is None:
                        val_str = "N/A"
                    f.write(
                        f"- **{chave.replace('_', ' ').capitalize()}**: {val_str}\n")
            else:
                f.write("- Nenhum critério de busca fornecido.\n")
            f.write("\n")

            if not casos_para_salvar:
                f.write("## Filmes Encontrados\n")
                f.write(
                    "- Nenhum filme encontrado com similaridade maior que zero.\n")
            else:
                f.write(
                    f"## Top {len(casos_para_salvar)} Filmes Encontrados (ordenados por similaridade)\n")
                for item in casos_para_salvar:
                    filme = item['caso']
                    similaridade = item['similaridade']
                    f.write("\n---\n\n") # Separador para cada filme
                    f.write(f"### Título: {filme.get('titulo', 'N/A')}\n\n")
                    if filme.get('link'):
                        f.write(
                            f"- **Link IMDB**: [{filme['link']}]({filme['link']})\n") # Link clicável
                    f.write(
                        f"- **Similaridade com entrada**: {similaridade*100:.2f}%\n")
                    # Detalhes do filme
                    f.write(
                        f"  - **Gêneros**: {', '.join(filme.get('generos', [])) or 'N/A'}\n")
                    f.write(
                        f"  - **Ano**: {filme.get('ano_lancamento', 'N/A')}\n")
                    f.write(
                        f"  - **Duração**: {filme.get('duracao_minutos', 'N/A')} min\n")
                    f.write(
                        f"  - **Classificação MPAA**: {filme.get('classificacao_etaria', 'N/A')}\n")
                    f.write(
                        f"  - **Avaliação IMDb**: {filme.get('avaliacao_critica', 'N/A')}/10 ({filme.get('votos', 'N/A')} votos)\n")
                    if filme.get('orcamento') is not None:
                        f.write(
                            f"  - **Orçamento**: ${filme.get('orcamento'):,.0f}\n") # Formata como moeda
                    if filme.get('bilheteria_mundial') is not None:
                        f.write(
                            f"  - **Bilheteria Mundial**: ${filme.get('bilheteria_mundial'):,.0f}\n") # Formata como moeda
                    if filme.get('diretores'):
                        f.write(
                            f"  - **Diretor(es)**: {', '.join(filme.get('diretores', [])) or 'N/A'}\n")
                    if filme.get('roteiristas'):
                        f.write(
                            f"  - **Roteirista(s)**: {', '.join(filme.get('roteiristas', [])) or 'N/A'}\n")
                    if filme.get('estrelas'):
                        f.write(
                            f"  - **Estrelas**: {', '.join(filme.get('estrelas', [])) or 'N/A'}\n")
                    if filme.get('pais_origem'):
                        f.write(
                            f"  - **País de Origem**: {', '.join(filme.get('pais_origem', [])) or 'N/A'}\n")
                    if filme.get('idioma'):
                        f.write(
                            f"  - **Idioma(s)**: {', '.join(filme.get('idioma', [])) or 'N/A'}\n")
                    if filme.get('vitorias') is not None:
                        f.write(
                            f"  - **Prêmios Ganhos**: {filme.get('vitorias')}\n")
                    if filme.get('indicacoes') is not None:
                        f.write(
                            f"  - **Indicações a Prêmios**: {filme.get('indicacoes')}\n")
                    if filme.get('oscars_indicados') is not None:
                        f.write(
                            f"  - **Indicações ao Oscar**: {filme.get('oscars_indicados')}\n")
        print(f"\nResultados salvos com sucesso no arquivo: {nome_arquivo}")
    except IOError as e:
        print(f"Erro ao salvar o arquivo '{nome_arquivo}': {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao tentar salvar o arquivo: {e}")


# --- Função Principal ---
def main():
    print("Bem-vindo ao Protótipo de RBC para Recomendação de Filmes (Schema Novo e Classificações Ampliadas)!")

    if not BASE_DE_CASOS: # Verifica se a base de casos foi carregada
        print("ERRO CRÍTICO: A base de casos está vazia. Verifique o arquivo CSV ou o caminho.")
        print("O programa não pode continuar sem uma base de dados.")
        return # Encerra o programa se não houver base

    pesos_atuais = PESOS_PADRAO.copy() # Inicia com os pesos padrão
    top_n_resultados = 10 # Número de top resultados para exibir/salvar

    while True:
        novo_caso, pesos_modificados = obter_caso_entrada_do_usuario(
            pesos_atuais)
        pesos_atuais = pesos_modificados # Atualiza os pesos para a próxima iteração, se modificados

        casos_ordenados_para_analise = [] # Para armazenar os resultados da busca

        if novo_caso is None: # Se o usuário não forneceu nenhum critério
            print("Nenhum caso de entrada fornecido para comparação.")
        else:
            print("\nCalculando similaridades...")
            resultados_similaridade = []
            for i, caso_base in enumerate(BASE_DE_CASOS):
                sim = calcular_similaridade_global(
                    novo_caso, caso_base, pesos_atuais)
                resultados_similaridade.append(
                    {'caso': caso_base, 'similaridade': sim})
                if (i + 1) % 500 == 0:  # Feedback visual para grandes datasets
                    print(
                        f"Processado {i+1}/{len(BASE_DE_CASOS)} filmes da base...")
            
            print("Ordenando resultados...")
            # Ordena pela similaridade em ordem decrescente
            casos_ordenados_completos = sorted(
                resultados_similaridade, key=lambda x: x['similaridade'], reverse=True)
            casos_ordenados_para_analise = casos_ordenados_completos

            exibir_resultados(
                novo_caso, casos_ordenados_para_analise, top_n=top_n_resultados)

            # Opção para salvar resultados
            if casos_ordenados_para_analise and any(c['similaridade'] > 0 for c in casos_ordenados_para_analise):
                while True:
                    salvar = input(
                        "\nVocê deseja salvar o resultado em arquivo Markdown? (S/N): ").strip().lower()
                    if salvar == 's':
                        salvar_resultados_em_markdown(
                            novo_caso, casos_ordenados_para_analise, top_n=top_n_resultados)
                        break
                    elif salvar == 'n' or not salvar: # Aceita 'n' ou Enter (vazio) como não
                        print("Resultado não será salvo.")
                        break
                    else:
                        print("Opção inválida. Digite 's' para sim ou 'n' para não.")
            elif novo_caso: # Se houve entrada mas nenhum resultado relevante
                print("Nenhum filme similar encontrado para salvar.")
        
        # Perguntar se deseja realizar outra busca
        continuar = input(
            "\nDeseja realizar outra busca? (s/N): ").strip().lower()
        if continuar != 's':
            break # Sai do loop principal
            
    print("Obrigado por usar o sistema de recomendação!")


if __name__ == "__main__":
    main()