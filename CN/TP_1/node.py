import math
import random

from utils import choose_random_element

class Node:
    def __init__(self, data):
        self.left = None
        self.right = None
        self.data = data
        self.fitness = None

    def generate_expr(self, depth, func_set, term_set, method):
        if depth == 0 or (method == "grow" and random.random() < float(len(term_set))/(len(term_set) + len(func_set))):
            self.data = choose_random_element(term_set)
        else:
            self.data = choose_random_element(func_set)

            self.left = Node('')
            self.left.generate_expr(depth - 1, func_set, term_set, method)

            self.right = Node('')
            self.right.generate_expr(depth - 1, func_set, term_set, method)

    def unroll_expression(self, expr_list):
        expr_list.append(self.data)
        if self.left is not None:
            expr_list = self.left.unroll_expression(expr_list)
        if self.right is not None:
            expr_list = self.right.unroll_expression(expr_list)
        return expr_list

    def get_depth(self):
        left = 0
        right = 0
        if self.left is not None:
            left = self.left.get_depth()
        if self.right is not None:
            right = self.right.get_depth()
        return 1 + max(left, right)

    def PrintTree(self, origin=True):
        if self.left:
            self.left.PrintTree(False)
        print(self.data, end=' ')
        if self.right:
            self.right.PrintTree(False)
        if origin:
            print('\n', end='')