#include <iostream>

#define UNSYNC_CIN std::ios_base::sync_with_stdio(false);std::cin.tie(NULL);

int main() {
    UNSYNC_CIN

    int n1, n2;
    std::cin >> n1 >> n2;

    std::cout << "X = " << n1 + n2 << std::endl;
}