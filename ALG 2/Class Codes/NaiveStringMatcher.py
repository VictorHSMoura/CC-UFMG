def naive_string_matcher(text, pattern):
    n = len(text)
    m = len(pattern)

    for s in range(n-m):
        if pattern == text[s:s+m]:
            print('Pattern occurs with shift {}'.format(s))


if __name__ == "__main__":
    print('Insert your text:')
    text = input()
    print('Insert your pattern:')
    pattern = input()

    naive_string_matcher(text, pattern)    