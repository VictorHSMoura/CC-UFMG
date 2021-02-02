import random
import math
import copy
import numpy as np

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

    print("Tree 1:")
    child1.PrintTree()
    print("\n\nTree 2:")
    child2.PrintTree()

    cross_node_1, instr1 = choose_node(child1, [])
    cross_node_2, instr2 = choose_node(child2, [])

    child1 = change_node_by_instructions(child1, cross_node_2, instr1)
    child2 = change_node_by_instructions(child2, cross_node_1, instr2)


    print("\n\nAfter crossover:")
    print("Tree 1:\n")
    child1.PrintTree()
    print("\n\nTree 2:\n")
    child2.PrintTree()

    return child1, child2

def mutation(node, func_set, term_set, prob):
    if random.random() < prob:
        if node.data in func_set:        
            node.data = choose_random_element(func_set)
        elif node.data in term_set:
            node.data = choose_random_element(term_set)
    if node.left is not None:
        node.left = mutation(node.left, func_set, term_set, prob)
    if node.right is not None:
        node.right = mutation(node.right, func_set, term_set, prob)
    
    return node


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
    mutation(root, func_set, term_set, 0.5).PrintTree()

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

    print(ind_per_depth)

    for size in sizes:
        for _ in range(int(ind_per_depth/2)):
            grow = Node('')
            grow.generate_expr(size, func_set, term_set, "grow")
            pop.append(grow)

            full = Node('')
            full.generate_expr(size, func_set, term_set, "full")
            pop.append(full)

    return np.array(pop)

def tournament_selection(pop, k):
    shuffled_pop = copy.deepcopy(pop)
    np.random.shuffle(shuffled_pop)

    # choose the first k individuals from shuffled population
    selected = shuffled_pop[:k]

    # TODO: calculate fitness after generating pop to return best individual
    best = selected[1]
    return best

    
if __name__ == "__main__" :
    # tests()

    func_set = ['+', '-', '*', '/']
    term_set = ['x1_1', 'x1_2', 'x2_1', 'x2_2']

    pop = initiate_pop(60, 7, func_set, term_set)
    print(pop)
    tournament_selection(pop, 3).PrintTree()