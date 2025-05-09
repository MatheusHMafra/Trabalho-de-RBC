def calcular_similaridade_numerica_simples(valor_problema, valor_base, max_diff):
    """
    Calcula a similaridade para atributos numéricos.
    Retorna um valor entre 0 e 1, onde 1 é identidade total.
    max_diff é a máxima diferença esperada para normalização.
    Se max_diff for 0 e os valores forem iguais, retorna 1, senão 0.
    """
    if max_diff == 0:
        return 1.0 if valor_problema == valor_base else 0.0
    diff = abs(valor_problema - valor_base)
    sim = 1 - (diff / max_diff)
    return max(0, sim)


def calcular_similaridade_categorica_simples(valor_problema, valor_base):
    """
    Calcula a similaridade para atributos categóricos.
    Retorna 1 se os valores forem iguais, 0 caso contrário.
    """
    return 1.0 if valor_problema == valor_base else 0.0


def similaridade_ponderada_global(caso_problema, caso_base, atributos_info, pesos):
    """
    Calcula a similaridade ponderada global entre dois casos.

    Args:
        caso_problema (dict): Dicionário representando o caso problema.
                              Ex: {'feature1': 10, 'feature2': 'A'}
        caso_base (dict): Dicionário representando o caso da base.
                          Ex: {'feature1': 12, 'feature2': 'A'}
        atributos_info (dict): Dicionário com informações sobre cada atributo,
                               incluindo seu tipo e, para numéricos, max_diff.
                               Ex: {
                                   'feature1': {'tipo': 'numerico', 'max_diff': 20},
                                   'feature2': {'tipo': 'categorico'}
                               }
        pesos (dict): Dicionário com os pesos para cada atributo.
                      Ex: {'feature1': 0.6, 'feature2': 0.4}

    Returns:
        float: A similaridade ponderada global (entre 0 e 1).
               Retorna 0.0 se a soma dos pesos for zero para evitar divisão por zero.
    """
    soma_similaridades_ponderadas = 0.0
    soma_pesos = 0.0

    # Itera sobre os atributos definidos nos pesos
    # Assume-se que os atributos em 'pesos' são os que devem ser considerados
    for atributo, peso in pesos.items():
        if atributo not in caso_problema or atributo not in caso_base:
            print(
                f"Aviso: Atributo '{atributo}' não encontrado em um dos casos. Pulando.")
            continue

        valor_problema = caso_problema[atributo]
        valor_base = caso_base[atributo]
        info_atributo = atributos_info.get(atributo)

        if not info_atributo:
            print(
                f"Aviso: Informações do atributo '{atributo}' não encontradas. Pulando.")
            continue

        sim_local = 0.0
        tipo_atributo = info_atributo.get('tipo')

        if tipo_atributo == 'numerico':
            # Default max_diff para evitar erros
            max_diff = info_atributo.get('max_diff', 1.0)
            if max_diff is None:  # Se max_diff for explicitamente None
                print(
                    f"Aviso: 'max_diff' não definido para o atributo numérico '{atributo}'. Pulando.")
                continue
            sim_local = calcular_similaridade_numerica_simples(
                valor_problema, valor_base, max_diff)
        elif tipo_atributo == 'categorico':
            sim_local = calcular_similaridade_categorica_simples(
                valor_problema, valor_base)
        else:
            print(
                f"Aviso: Tipo de atributo '{tipo_atributo}' desconhecido para '{atributo}'. Pulando.")
            continue

        soma_similaridades_ponderadas += peso * sim_local
        soma_pesos += peso

    if soma_pesos == 0:
        return 0.0  # Evita divisão por zero se não houver pesos ou atributos válidos

    return soma_similaridades_ponderadas / soma_pesos


# --- Exemplo de Uso ---
if __name__ == "__main__":
    # Definindo os casos
    caso_problema_exemplo = {
        'idade': 30,          # Numérico
        'renda_anual': 50000,  # Numérico
        'estado_civil': 'solteiro',  # Categórico
        'tem_filhos': False    # Categórico (tratado como tal)
    }

    caso_base_exemplo_1 = {
        'idade': 35,
        'renda_anual': 55000,
        'estado_civil': 'solteiro',
        'tem_filhos': False
    }

    caso_base_exemplo_2 = {
        'idade': 25,
        'renda_anual': 40000,
        'estado_civil': 'casado',
        'tem_filhos': True
    }

    caso_base_exemplo_3 = {  # Caso idêntico para teste
        'idade': 30,
        'renda_anual': 50000,
        'estado_civil': 'solteiro',
        'tem_filhos': False
    }

    # Informações sobre os atributos (tipo e parâmetros para funções de similaridade)
    # Para 'idade', consideramos uma diferença máxima de 50 anos para normalização.
    # Para 'renda_anual', uma diferença máxima de 100000.
    atributos_info_exemplo = {
        'idade': {'tipo': 'numerico', 'max_diff': 50},
        'renda_anual': {'tipo': 'numerico', 'max_diff': 100000},
        'estado_civil': {'tipo': 'categorico'},
        # Booleano pode ser tratado como categórico
        'tem_filhos': {'tipo': 'categorico'}
    }

    # Pesos dos atributos (a soma não precisa ser 1, pois a fórmula normaliza)
    pesos_exemplo = {
        'idade': 0.3,
        'renda_anual': 0.4,
        'estado_civil': 0.2,
        'tem_filhos': 0.1
    }

    # Validando se a soma dos pesos é maior que zero
    if sum(pesos_exemplo.values()) <= 0:
        print("Erro: A soma dos pesos dos atributos deve ser maior que zero.")
    else:
        # Calculando a similaridade com o caso_base_exemplo_1
        sim1 = similaridade_ponderada_global(
            caso_problema_exemplo,
            caso_base_exemplo_1,
            atributos_info_exemplo,
            pesos_exemplo
        )
        print(f"Similaridade com Caso Base 1: {sim1:.4f}")

        # Calculando a similaridade com o caso_base_exemplo_2
        sim2 = similaridade_ponderada_global(
            caso_problema_exemplo,
            caso_base_exemplo_2,
            atributos_info_exemplo,
            pesos_exemplo
        )
        print(f"Similaridade com Caso Base 2: {sim2:.4f}")

        # Calculando a similaridade com o caso_base_exemplo_3 (idêntico)
        sim3 = similaridade_ponderada_global(
            caso_problema_exemplo,
            caso_base_exemplo_3,
            atributos_info_exemplo,
            pesos_exemplo
        )
        print(f"Similaridade com Caso Base 3 (Idêntico): {sim3:.4f}")

        # Exemplo com um atributo faltando no caso base
        caso_base_incompleto = {
            'idade': 35,
            # 'renda_anual': 55000, # Atributo faltando
            'estado_civil': 'solteiro',
            'tem_filhos': False
        }
        sim_incompleto = similaridade_ponderada_global(
            caso_problema_exemplo,
            caso_base_incompleto,
            atributos_info_exemplo,
            pesos_exemplo
        )
        print(f"Similaridade com Caso Base Incompleto: {sim_incompleto:.4f}")

        # Exemplo com informações de atributo faltando
        atributos_info_incompleto = {
            'idade': {'tipo': 'numerico', 'max_diff': 50},
            # 'renda_anual': {'tipo': 'numerico', 'max_diff': 100000}, # Info faltando
            'estado_civil': {'tipo': 'categorico'},
            'tem_filhos': {'tipo': 'categorico'}
        }
        sim_info_faltando = similaridade_ponderada_global(
            caso_problema_exemplo,
            caso_base_exemplo_1,
            atributos_info_incompleto,
            pesos_exemplo
        )
        print(
            f"Similaridade com Informações de Atributo Faltando: {sim_info_faltando:.4f}")

        # Exemplo onde a soma dos pesos é zero (ou um atributo com peso zero)
        pesos_zero = {
            'idade': 0,
            'renda_anual': 0,
            'estado_civil': 0,
            'tem_filhos': 0
        }
        sim_pesos_zero = similaridade_ponderada_global(
            caso_problema_exemplo,
            caso_base_exemplo_1,
            atributos_info_exemplo,
            pesos_zero
        )
        print(f"Similaridade com Pesos Zero: {sim_pesos_zero:.4f}")

        # Exemplo com max_diff = 0 para um atributo numérico
        atributos_max_diff_zero = {
            'idade': {'tipo': 'numerico', 'max_diff': 0},  # max_diff = 0
            'renda_anual': {'tipo': 'numerico', 'max_diff': 100000},
            'estado_civil': {'tipo': 'categorico'},
            'tem_filhos': {'tipo': 'categorico'}
        }
        caso_problema_max_diff_zero_igual = {
            'idade': 30, 'renda_anual': 50000, 'estado_civil': 'solteiro', 'tem_filhos': False}
        caso_base_max_diff_zero_igual = {
            'idade': 30, 'renda_anual': 55000, 'estado_civil': 'solteiro', 'tem_filhos': False}
        caso_base_max_diff_zero_dif = {
            'idade': 35, 'renda_anual': 55000, 'estado_civil': 'solteiro', 'tem_filhos': False}

        sim_max_diff_zero_igual = similaridade_ponderada_global(
            caso_problema_max_diff_zero_igual,
            caso_base_max_diff_zero_igual,
            atributos_max_diff_zero,
            pesos_exemplo
        )
        print(
            f"Similaridade com max_diff=0 (valores iguais para 'idade'): {sim_max_diff_zero_igual:.4f}")

        sim_max_diff_zero_dif = similaridade_ponderada_global(
            caso_problema_max_diff_zero_igual,
            caso_base_max_diff_zero_dif,
            atributos_max_diff_zero,
            pesos_exemplo
        )
        print(
            f"Similaridade com max_diff=0 (valores diferentes para 'idade'): {sim_max_diff_zero_dif:.4f}")
