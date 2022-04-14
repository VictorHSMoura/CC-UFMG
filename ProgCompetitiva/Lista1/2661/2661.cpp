#include <iostream>
#include <vector>
#include <unordered_set>
#include <cmath>

using namespace std;
#define UNSYNC_CIN ios_base::sync_with_stdio(false);cin.tie(NULL);

vector<int64_t> geraPrimosAteN(int64_t n) {
    int64_t size = (int64_t) ceil(sqrt(n));

    vector<bool> numeros(size, true);
    vector<int64_t> primos;

    for (int64_t i = 2; i <= size; i++) {
        if (numeros[i]) {
            primos.push_back(i);
            for (int64_t m = i*i; m <= size; m += i)
                numeros[m] = false;
        }
    }

    return primos;
}

int main() {
    UNSYNC_CIN

    int64_t n;
    cin >> n;

    vector<int64_t> primos = geraPrimosAteN(n);
    unordered_set<int64_t> div;

    int count = 0;
    for (int64_t p : primos) {
        if (n % p == 0) {
            div.insert(p);
            n /= p;
        }
    }
    int divs = div.size();

    cout << pow(2, divs) - (divs + 1) << "\n";

    return 0;
}