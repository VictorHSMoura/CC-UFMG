import random
import math
import copy
import numpy as np
import sys
import timeit
import operator as op

# Manipulação dos dados
import pandas as pd

# Métrica v_measure_score
from sklearn.metrics.cluster import v_measure_score

from sklearn.metrics import pairwise_distances

from sklearn.cluster import AgglomerativeClustering

# Funções para clustering utilizando PyClustering
from pyclustering.cluster.kmeans import kmeans
from pyclustering.cluster.center_initializer import kmeans_plusplus_initializer
from pyclustering.utils.metric import distance_metric, type_metric

from node import Node
from utils import choose_random_element

def map_value_to_param(value, params1, params2):
    if value[0] == 'a':
        return params1[int(value[1]) - 1]
    else:
        return params2[int(value[1]) - 1]

# @profile
def eval(params1, params2, func_set, operations, expr_list):
    reverse_expr = expr_list[::-1]
    new_expr = []
    for elem in reverse_expr:
        if elem not in func_set:
            value = map_value_to_param(elem, params1, params2)
            new_expr.append(value)
        else:
            value1 = new_expr.pop()
            value2 = new_expr.pop()
            
            new_expr.append(operations[elem](value1, value2))
    return abs(new_expr[0])

# these probabilities can (and probably will) change
def choose_node(node, instr, max_depth):
    if random.random() < 0.25 and (node.get_depth() - 1) <= max_depth:
        return node, instr
    else:
        if random.random() < 0.5:
            if node.left is not None:
                instr.append('l')
                return choose_node(node.left, instr, max_depth)
            elif node.right is not None:
                instr.append('r')
                return choose_node(node.right, instr, max_depth)
            else:
                return node, instr
        else:
            if node.right is not None:
                instr.append('r')
                return choose_node(node.right, instr, max_depth)
            elif node.left is not None:
                instr.append('l')
                return choose_node(node.left, instr, max_depth)
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
    child1 = node1
    child2 = node2

    cross_node_1, instr1 = choose_node(child1, [], max_depth)
    cn1_depth = len(instr1)
    # prevent generating too big children
    cross_node_2, instr2 = choose_node(child2, [], max_depth - cn1_depth)

    child1 = swap_node_by_instructions(child1, cross_node_2, instr1)
    child2 = swap_node_by_instructions(child2, cross_node_1, instr2)

    # reset fitness
    child1.fitness = None
    child2.fitness = None

    return child1, child2

def mutation(node, func_set, term_set, max_depth):
    child = node

    mutated_node, instr = choose_node(child, [], max_depth)

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

def calculate_fitness(ind, df, X, target, func_set, operations, number_of_clusters):
    ind_exp = ind.unroll_expression([])

    def fitness_distance(data1, data2):
        """
        input:
            point1 e point2 = pontos utilizados no cálculo da distância
        output:
            result = distância entre os dois pontos
        """
        result = eval(data1, data2, func_set, operations, ind_exp)
        return result

    # distance function
    fitness_metric = distance_metric(type_metric.USER_DEFINED, func=fitness_distance)

    k = number_of_clusters

    initial_centers = kmeans_plusplus_initializer(X, k).initialize()
    kmeans_instance = kmeans(X, initial_centers, metric=fitness_metric)
    kmeans_instance.process()
    clusters = kmeans_instance.get_clusters()

    for i in range(len(clusters)):
        df.loc[clusters[i], 'y_pred'] = i

    score = v_measure_score(target, df.y_pred)
    # reseting dataframe
    df = df.drop(['y_pred'], axis=1)

    return score
    
def read_data(file_name, drop_column):
    # read data from csv
    df = pd.read_csv(file_name)
    # drop categories column
    X = df.drop([drop_column], axis=1)

    return df, X

def get_fitness_data(pop):
    best_fitness = 0
    best_ind = None
    avg = 0.0
    worst_fitness = 1
    for ind in pop:
        avg += ind.fitness
        if ind.fitness > best_fitness:
            best_fitness = ind.fitness
            best_ind = ind
        if ind.fitness < worst_fitness:
            worst_fitness = ind.fitness
    
    avg /= pop.shape[0]
    return best_fitness, best_ind, avg, worst_fitness

def get_repeated(pop):
    exps = []
    equal = 0
    for ind in pop:
        exps.append(ind.unroll_expression([]))

    set_of_exps = [list(item) for item in set(tuple(row) for row in exps)]

    for exp in set_of_exps:
        repeats = exps.count(exp)
        if repeats > 1:
            equal += repeats

    return equal

def div_protected(a, b):
    return 1 if b == 0 else float(a)/b

def run_for_database(file_name, prob_crossover, prob_mutation, tour_size, pop_size, n_gen):
    # set functions and terminals
    func_set = ['+', '-', '*', '/']
    term_set = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9','b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8', 'b9']
    operations = {
        '+': op.add,
        '-': op.sub,
        '*': op.mul,
        '/': div_protected,
        'max': max,
        'min': min
    }
    
    print('Prob crossover: {} / Prob mutation: {} / Tour size: {} / Pop size: {} / N Gen: {}'. format(prob_crossover, prob_mutation, tour_size, pop_size, n_gen))

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
        ind.fitness = calculate_fitness(ind, df, X, df[labels_column], func_set, operations, n_clusters)

    best_fitness, best_ind, avg, worst_fitness = get_fitness_data(pop)
    repeated = get_repeated(pop)
    print('Initial best fitness: {} / Initial avg fitness: {} / Initial worst fitness: {}'.format(best_fitness, avg, worst_fitness))
    print('Repeated: {}\n'.format(repeated))

    for i in range(n_gen):
        better_than_parent = 0
        worse_than_parent = 0
        print('Running generation ' + str(i + 1))

        new_gen = np.array([best_ind])

        while new_gen.shape[0] < pop.shape[0]:
            gen_prob = random.random()
            if gen_prob < prob_crossover:
                parent1, parent2 = tournament_selection(pop, tour_size, 2)

                parents_mean_fitness = (parent1.fitness + parent2.fitness) / 2.0

                child1, child2 = crossover(parent1, parent2, tree_max_depth)

                child1.fitness = calculate_fitness(child1, df, X, df[labels_column], func_set, operations, n_clusters)

                child2.fitness = calculate_fitness(child2, df, X, df[labels_column], func_set, operations, n_clusters)

                if child1.fitness < parents_mean_fitness:
                    worse_than_parent += 1
                elif child1.fitness > parents_mean_fitness:
                    better_than_parent += 1
                
                if child2.fitness < parents_mean_fitness:
                    worse_than_parent += 1
                elif child2.fitness > parents_mean_fitness:
                    better_than_parent += 1

                new_gen = np.append(new_gen, [child1, child2])

            elif gen_prob < prob_crossover + prob_mutation:
                parent, _ = tournament_selection(pop, tour_size, 1)

                child = mutation(parent, func_set, term_set, tree_max_depth)

                new_gen = np.append(new_gen, child)

            else:
                parent, _ = tournament_selection(pop, tour_size, 1)

                child = copy.deepcopy(parent)

                new_gen = np.append(new_gen, child)

        # not necessary to recalculate the fitness for the nodes that we already know the fitness 
        for ind in new_gen:
            if ind.fitness == None:
                ind.fitness = calculate_fitness(ind, df, X, df[labels_column], func_set, operations, n_clusters)

        # writing a copy to prevent overwrite
        # if the new gen overpass the maximum number of individuals, we delete the last ones
        pop = np.copy(new_gen[:pop_size])

        best_fitness, best_ind, avg, worst_fitness = get_fitness_data(pop)
        repeated = get_repeated(pop)
        print('Best fitness: {} / Avg fitness: {} / Worst fitness: {}'.format(best_fitness, avg, worst_fitness))
        print('Repeated: {} / Better than parents: {} / Worse than parents: {}\n'.format(repeated, better_than_parent, worse_than_parent))


    test_result(file_name[:-9] + 'test.csv', func_set, operations, best_ind)

def test_result(file_name, func_set, operations, best_ind):
    print('Testing best individual on the test set')
    if file_name == 'data/breast_cancer_coimbra_test.csv':
        labels_column = 'Classification'
        n_clusters = 2
    else:
        labels_column = 'glass_type'
        n_clusters = 7

    df, X = read_data(file_name, labels_column)

    best_ind.fitness = calculate_fitness(best_ind, df, X, df[labels_column], func_set, operations, n_clusters)

    print('Achieved fitness: {}'.format(best_ind.fitness))
    

if __name__ == "__main__" :   
    db = 'data/glass_train.csv'

    run_for_database(file_name=db, prob_crossover=0.6, prob_mutation=0.3, tour_size=2, pop_size=24, n_gen=24)