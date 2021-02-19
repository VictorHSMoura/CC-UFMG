import math
import random

def choose_random_element(chosen_set):
    index = math.floor(random.random() * len(chosen_set))
    return chosen_set[index]