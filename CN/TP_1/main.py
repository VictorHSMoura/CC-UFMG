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

def change_node_by_instructions(original_node, new_node, instr):
    if instr == []:
        original_node = new_node  
    elif instr[0] == 'l':
        original_node.left = change_node_by_instructions(original_node.left, new_node, instr[1:])
    else:
        original_node.right = change_node_by_instructions(original_node.right, new_node, instr[1:])
    return original_node

def crossover(node1, node2):
    child1 = copy.deepcopy(node1)
    child2 = copy.deepcopy(node2)  

    cross_node_1, instr1 = choose_node(child1, [])
    cross_node_2, instr2 = choose_node(child2, [])

    child1 = change_node_by_instructions(child1, cross_node_2, instr1)
    child2 = change_node_by_instructions(child2, cross_node_1, instr2)

    return child1, child2

def mutation(node, func_set, term_set, mutated=False):
    mut_prob = 0.25
    if mutated:
        return node, mutated
    else:
        if random.random() < mut_prob:
            if node.data in func_set:
                elem = node.data
                while elem == node.data:
                    elem = choose_random_element(func_set)
                
                node.data = elem
            elif node.data in term_set:
                elem = node.data
                while elem == node.data:
                    elem = choose_random_element(term_set)
                
                node.data = elem
            return node, True
        else:
            if node.left is not None and not mutated:
                node.left, mutated = mutation(node.left, func_set, term_set, mutated)
            if node.right is not None and not mutated:
                node.right, mutated = mutation(node.right, func_set, term_set, mutated)
    
    return node, mutated


def tests():
    root = Node('')
    root2 = Node('')

    func_set = ['+', '-', '*', '/']
    term_set = ['x1_1', 'x1_2', 'x2_1', 'x2_2']

    root.generate_expr(2, func_set, term_set, 'full')
    root2.generate_expr(2, func_set, term_set, 'full')

    child1, child2 = crossover(root, root2)

    print("\n\nTree 1 before mutation:\n")
    root.PrintTree()
    print("\n\nTree 1 after mutation:\n")
    node_mutated, _ = mutation(root, func_set, term_set)
    node_mutated.PrintTree()

    # print("Tree 1:\n")
    # root.PrintTree()
    # print("\n\nTree 2:\n")
    # root2.PrintTree()

    # expr = root.unroll_expression([])
    # expr2 = root2.unroll_expression([])

    # print(expr)
    # print(expr2)

    # print(root.eval([1, 2], [3, 4], expr))
    # print(root.eval([3, 1], [2, 4], expr))

    # print(root.eval([1, 2], [3, 4], expr2))
    # print(root.eval([3, 1], [2, 4], expr2))

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

if __name__ == "__main__" :
    # tests()

    # set functions and terminals
    func_set = ['+', '-', '*', '/']
    term_set = ['x1_1', 'x1_2', 'x1_3', 'x1_4', 'x1_5', 'x1_6', 'x1_7', 'x1_8', 'x1_9','x2_1', 'x2_2', 'x2_3', 'x2_4', 'x2_5', 'x2_6', 'x2_7', 'x2_8', 'x2_9']

    prob_crossover = 0.9
    prob_mutation = 0.05
    
    df, X = read_data('data/breast_cancer_coimbra_train.csv', 'Classification')

    #TODO: create a function that receives the probs and number of generations, and run all the generations

    pop = initiate_pop(60, 7, func_set, term_set)

    for ind in pop:
        ind.fitness = calculate_fitness(ind, df, X, df.Classification, func_set, 2)
    
    #TODO: remove parents from population and add children to it
    gen_prob = random.random()
    if gen_prob < prob_crossover:
        print('Crossover:\n')
        
        parent1, parent2 = tournament_selection(pop, 3, 2)
        print('Parent 1:')
        parent1.PrintTree()
        print('\nParent 2:')
        parent2.PrintTree()

        child1, child2 = crossover(parent1, parent2)
        print('\n\nChild 1:')
        child1.PrintTree()
        print('\nChild 2:')
        child2.PrintTree()

    elif gen_prob < prob_crossover + prob_mutation:
        print('Mutation:\n')

        parent, _ = tournament_selection(pop, 3, 1)
        print('Parent :')
        parent.PrintTree()

        child, _ = mutation(parent, func_set, term_set)
        print('Child :')
        child.PrintTree()
    else:
        print('Reproduction:\n')

        parent, _ = tournament_selection(pop, 3, 1)
        print('Parent :')
        parent.PrintTree()

        child = copy.deepcopy(parent)
        print('Child :')
        child.PrintTree()