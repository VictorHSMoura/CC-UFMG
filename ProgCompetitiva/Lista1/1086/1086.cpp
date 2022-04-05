#include <iostream>
#include <vector>

using namespace std;
#define UNSYNC_CIN ios_base::sync_with_stdio(false);cin.tie(NULL);

int main() {
    
    while (true) {
        int n, m, l, k;
        vector<int> planks;

        cin >> n >> m;
        if (n + m == 0) break;

        cin >> l >> k;
        for (int i = 0; i < k; i++) {
            int p;
            cin >> p;
            planks.push_back(p);
        }

        

        cout << endl;
    }

    return 0;
}
