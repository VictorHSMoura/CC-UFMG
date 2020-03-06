def finite_automaton_matcher(text, transitions, m):
    n = len(text)
    q = 0
    for i in range(n):
        q = transitions[q][text[i]]
        if q == m:
            print("Pattern occurs with shift {}".format(i-m+1))
            return

def compute_transition_function(pattern, alphabet):
    m = len(pattern)
    transitions = {}
    for q in range(m):
        transitions[q] = {} 
        for char in alphabet:
            k = min(m+1, q+2)
            k = k-1
            while not (pattern[:q] + char).endswith(pattern[:k]):
                k = k-1
            transitions[q][char] = k

    return transitions

if __name__ == "__main__":
    print('Insert your text:')
    text = input()
    print('Insert your pattern:')
    pattern = input()

    alphabet = ''.join(set(text))
    transitions = compute_transition_function(pattern, alphabet)
    finite_automaton_matcher(text, transitions, len(pattern))