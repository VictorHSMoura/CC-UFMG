#include <iostream>
#include <string>
#include <unordered_set>
#include <vector>
#include <algorithm>

using namespace std;
#define UNSYNC_CIN ios_base::sync_with_stdio(false);cin.tie(NULL);


vector<int> dfs(const int grafo[26][26], int node, int v, unordered_set<int>& visited) {
    visited.insert(node);

    vector<int> connected;
    connected.push_back(node);

    for (int i = 0; i < v; i++) {
        if (grafo[node][i] == 1 && visited.find(i) == visited.end()) {
            vector<int> aux = dfs(grafo, i, v, visited);
            connected.insert(connected.end(), aux.begin(), aux.end());
        }
    }

    return connected;
}


int main() {
    UNSYNC_CIN

    int n, v, e;
    
    cin >> n;    
    for (int i = 1; i <= n; i++) {
        int grafo[26][26] = {0};
        int conn = 0;
        char v1, v2;
        unordered_set<int> visited;

        cout << "Case #" << i << ":\n";

        cin >> v >> e;
        while (e > 0) {
            cin >> v1 >> v2;
            v1 = v1 - 'a';
            v2 = v2 - 'a';

            grafo[v1][v2] = 1;
            grafo[v2][v1] = 1;
            e--;
        }

        while (visited.size() < v) {
            int node = 0;
            while (node < v) {
                if (visited.find(node) == visited.end()) break;
                node++;
            }

            vector<int> connected = dfs(grafo, node, v, visited);
            sort(connected.begin(), connected.end());

            for (int c : connected)
                cout << char(c + 'a') << ",";
            cout << "\n";

            conn++;
        }

        cout << conn << " connected components\n\n";

    }

    return 0;
}