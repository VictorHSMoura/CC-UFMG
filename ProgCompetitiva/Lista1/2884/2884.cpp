#include <iostream>
#include <vector>
#include <cstring>
#include <memory>

using namespace std;
#define UNSYNC_CIN ios_base::sync_with_stdio(false);cin.tie(NULL);

bool comp(bool start[], bool state[], int m) {
    for (int j = 0; j < m; j++) {
        if (start[j] != state[j]) return false;
    }
    return true;
}

bool xor_comp(bool start[], bool state[], bool x[], int m) {
    for (int j = 0; j < m; j++) {
        bool cp = state[j] != x[j];
        if (start[j] != cp) return false;
    }
    return true;
}

int main() {
    UNSYNC_CIN

    bool states[1000][1000], start[1000];
    int n, m, l, x;
    
    
    cin >> n >> m;
    cin >> l;

    while (l > 0) {
        cin >> x;
        start[x-1] = true;
        l--;
    }

    cin >> l;
    while (l > 0) {
        cin >> x;
        states[0][x - 1] = true;
        l--;
    }

    if (comp(start, states[0], m)) {
        std::cout << 1 << std::endl;
        return 0;
    }

    for (int i = 1; i < n; i++) {
        cin >> l;
        memcpy(states[i], states[i-1], m);
        while (l > 0) {
            cin >> x;
            states[i][x - 1] = !states[i - 1][x - 1];
            l--;
        }
        if (comp(start, states[i], m)) {
            std::cout << i+1 << std::endl;
            return 0;
        }
    }

    for (int i = 0; i < n; i++) {
        if (xor_comp(start, states[i], states[n-1], m)) {
            std::cout << (i + n + 1) << std::endl;
            return 0;
        }
    }

    std::cout << -1 << std::endl;

    return 0;
}