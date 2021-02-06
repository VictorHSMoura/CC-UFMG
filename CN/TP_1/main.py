import random
import math
import copy
import numpy as np
import sys

# Manipulação dos dados
import pandas as pd

# Métrica v_measure_score
from sklearn.metrics.cluster import v_measure_score

# Funções para clustering utilizando PyClustering
from pyclustering.cluster.kmeans import kmeans
from pyclustering.cluster.center_initializer import kmeans_plusplus_initializer
from pyclustering.utils.metric import distance_metric, type_metric

from node import Node
from utils import choose_random_element


def map_value_to_param(value, params1, params2):
    if value[:2] == 'x1':
        return params1[int(value.split('_')[1]) - 1]
    else:
        return params2[int(value.split('_')[1]) - 1]

def eval(params1, params2, func_set, expr_list):
    reverse_expr = expr_list[::-1]
    new_expr = []
    for elem in reverse_expr:
        if elem not in func_set:
            value = map_value_to_param(elem, params1, params2)
            new_expr.append(value)
        else:
            value1 = new_expr.pop()

            value2 = new_expr.pop()
            
            if elem == '+':
                new_expr.append(value1 + value2)
            elif elem == '-':
                new_expr.append(value1 - value2)
            elif elem == '*':
                new_expr.append(value1 * value2)
            else:
                if value2 == 0:
                    new_expr.append(1)
                else:
                    new_expr.append(float(value1) / value2)
    return new_expr[0]

# these probabilities can (and probably will) change
def choose_node(node, instr):
    if random.random() < 0.2:
        return node, instr
    else:
        if random.random() < 0.5:
            if node.left is not None:
                instr.append('l')
                return choose_node(node.left, instr)
            elif node.right is not None:
                instr.append('r')
                return choose_node(node.right, instr)
            else:
                return node, instr
        else:
            if node.right is not None:
                instr.append('r')
                return choose_node(node.right, instr)
            elif node.left is not None:
                instr.append('l')
                return choose_node(node.left, instr)
            else:
                return node, instr

def swap_node_by_instructions(original_node, new_node, instr):
    if instr == []:
        original_node = new_node  
    elif instr[0] == 'l':
        original_node.left = swap_node_by_instructions(original_node.left, new_node, instr[1:])
    else:
        original_node.right = swap_node_by_instructions(original_node.right, new_node, instr[1:])
    return original_node

def change_node_by_instructions(original_node, new_node_data, instr):
    if instr == []:
        original_node.data = new_node_data
    elif instr[0] == 'l':
        original_node.left = change_node_by_instructions(original_node.left, new_node_data, instr[1:])
    else:
        original_node.right = change_node_by_instructions(original_node.right, new_node_data, instr[1:])
    return original_node

def crossover(node1, node2, max_depth):
    depth1 = max_depth + 1
    depth2 = max_depth + 1

    # prevent generating too big children
    while depth1 > max_depth or depth2 > max_depth:
        child1 = copy.deepcopy(node1)
        child2 = copy.deepcopy(node2)  

        cross_node_1, instr1 = choose_node(child1, [])
        cross_node_2, instr2 = choose_node(child2, [])

        child1 = swap_node_by_instructions(child1, cross_node_2, instr1)
        child2 = swap_node_by_instructions(child2, cross_node_1, instr2)

        depth1 = child1.get_depth() - 1
        depth2 = child2.get_depth() - 1

    # reset fitness
    child1.fitness = None
    child2.fitness = None

    return child1, child2

def mutation(node, func_set, term_set):
    child = copy.deepcopy(node)

    mutated_node, instr = choose_node(child, [])

    new_data = mutated_node.data
    if mutated_node.data in func_set:
        while mutated_node.data == new_data:
            new_data = choose_random_element(func_set)
    else:
        while mutated_node.data == new_data:
            new_data = choose_random_element(term_set)
        
    child = change_node_by_instructions(child, new_data, instr)

    # reset fitness
    child.fitness = None
    
    return child

# initiate population using the method "ramped half-and-half"
def initiate_pop(pop_size, max_depth, func_set, term_set):
    sizes = range(2, max_depth + 1)
    ind_per_depth = int(pop_size/len(sizes))
    pop = []

    for size in sizes:
        for _ in range(int(ind_per_depth/2)):
            grow = Node('')
            grow.generate_expr(size, func_set, term_set, "grow")
            pop.append(grow)

            full = Node('')
            full.generate_expr(size, func_set, term_set, "full")
            pop.append(full)

    return np.array(pop)

def select_max(selected):
    max_value = selected[0].fitness
    max_ind = selected[0]
    for i in range(len(selected)):
        if selected[i].fitness > max_value:
            max_value = selected[i].fitness
            max_ind = selected[i]

    return max_ind

def tournament_selection(pop, k, n_ind):
    shuffled_pop = copy.deepcopy(pop)
    np.random.shuffle(shuffled_pop)

    # choose the best individual among the k initial individuals from shuffled population
    best1 = select_max(shuffled_pop[:k])

    # if we need to select two individuals, the same rule above is applied, just choosing between the last k individuals from shuffled population
    best2 = None
    if n_ind == 2:
        best2 = select_max(shuffled_pop[-k:])

    return best1, best2

def calculate_fitness(ind, df, X, target, func_set, number_of_clusters):
    ind_exp = ind.unroll_expression([])
    df_copy = copy.deepcopy(df)

    def fitness_distance(data1, data2):
        """
        input:
            point1 e point2 = pontos utilizados no cálculo da distância
        output:
            result = distância entre os dois pontos
        """
        result = eval(data1, data2, func_set, ind_exp)
        return result
    
    # distance function
    fitness_metric = distance_metric(type_metric.USER_DEFINED, func=fitness_distance)

    k = number_of_clusters

    initial_centers = kmeans_plusplus_initializer(X, k).initialize()
    kmeans_instance = kmeans(X, initial_centers, metric=fitness_metric)
    kmeans_instance.process()
    clusters = kmeans_instance.get_clusters()

    for i in range(len(clusters)):
        df_copy.loc[clusters[i], 'y_pred'] = i

    return v_measure_score(target, df_copy.y_pred)
    
def read_data(file_name, drop_column):
    # read data from csv
    df = pd.read_csv(file_name)
    # drop categories column
    X = df.drop([drop_column], axis=1)

    return df, X

def get_best_fitness(pop):
    best_fitness = 0
    best_ind = None
    for ind in pop:
        if ind.fitness > best_fitness:
            best_fitness = ind.fitness
            best_ind = ind

    return best_fitness, best_ind

def run_for_database(file_name, prob_crossover, prob_mutation, tour_size, pop_size, n_gen):
    # set functions and terminals
    func_set = ['+', '-', '*', '/']
    term_set = ['x1_1', 'x1_2', 'x1_3', 'x1_4', 'x1_5', 'x1_6', 'x1_7', 'x1_8', 'x1_9','x2_1', 'x2_2', 'x2_3', 'x2_4', 'x2_5', 'x2_6', 'x2_7', 'x2_8', 'x2_9']

    tree_max_depth = 7

    if file_name == 'data/breast_cancer_coimbra_train.csv':
        labels_column = 'Classification'
        n_clusters = 2
    else:
        labels_column = 'glass_type'
        n_clusters = 7
    
    df, X = read_data(file_name, labels_column)

    print('Initiating population')
    pop = initiate_pop(pop_size, tree_max_depth, func_set, term_set)

    print('Calculating initial fitness')
    for ind in pop:
        ind.fitness = calculate_fitness(ind, df, X, df[labels_column], func_set, n_clusters)

    best_fitness, best_ind = get_best_fitness(pop)
    print('Initial best fitness: ' + str(round(best_fitness, 5)))

    for i in range(n_gen):
        print('Running generation ' + str(i + 1))

        new_gen = np.array([best_ind])

        while new_gen.shape[0] < pop.shape[0]:
            gen_prob = random.random()
            if gen_prob < prob_crossover:
                parent1, parent2 = tournament_selection(pop, tour_size, 2)

                child1, child2 = crossover(parent1, parent2, tree_max_depth)

                new_gen = np.append(new_gen, [child1, child2])

            elif gen_prob < prob_crossover + prob_mutation:
                parent, _ = tournament_selection(pop, tour_size, 1)

                child = mutation(parent, func_set, term_set)

                new_gen = np.append(new_gen, child)

            else:
                parent, _ = tournament_selection(pop, tour_size, 1)

                child = copy.deepcopy(parent)

                new_gen = np.append(new_gen, child)

        print('Calculating fitness')
        # not necessary to recalculate the fitness for the nodes that we already know the fitness 
        for ind in new_gen:
            if ind.fitness == None:
                ind.fitness = calculate_fitness(ind, df, X, df[labels_column], func_set, n_clusters)

        # writing a copy to prevent overwrite
        # if the new gen overpass the maximum number of individuals, we delete the last ones
        pop = copy.deepcopy(new_gen[:pop_size])

        best_fitness, best_ind = get_best_fitness(pop)
        print('Best fitness: ' + str(round(best_fitness, 5)))
    

if __name__ == "__main__" :
    run_for_database(file_name='data/breast_cancer_coimbra_train.csv', prob_crossover=0.9, prob_mutation=0.05, tour_size=3, pop_size=60, n_gen=100)

    # run_for_database(file_name='data/glass_train.csv', prob_crossover=0.9, prob_mutation=0.05, tour_size=3, pop_size=60, n_gen=100)

    # pop = []

    # func_set = ['+', '-', '*', '/']
    # term_set = ['x1_1', 'x1_2', 'x1_3', 'x1_4', 'x1_5', 'x1_6', 'x1_7', 'x1_8', 'x1_9','x2_1', 'x2_2', 'x2_3', 'x2_4', 'x2_5', 'x2_6', 'x2_7', 'x2_8', 'x2_9']

    # for i in range(3):
    #     full = Node('')
    #     full.generate_expr(7, func_set, term_set, "full")
    #     pop.append(full)

    # pop = np.array(pop)

    # ind = pop[0]

    # print(ind.get_depth())
    # print(pop[1].get_depth())

    # print('Pai:')
    # ind.PrintTree()
    # print('\nPai:')
    # pop[1].PrintTree()

    # child1, child2 = crossover(pop[0], pop[1], 7)

    # print('\nFilho:')
    # child1.PrintTree()
    # print('\nFilho:')
    # child2.PrintTree()

    # print(child1.get_depth())
    # print(child2.get_depth())

    # print(np.where(pop == ind)[0])