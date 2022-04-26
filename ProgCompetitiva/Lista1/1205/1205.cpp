#include <iostream>
#include <vector>

using namespace std;

#define UNSYNC_CIN ios_base::sync_with_stdio(false);cin.tie(NULL);
typedef pair<int, int> ii;

int main() {
    UNSYNC_CIN

    int n, m, k;
    double p;

    while (cin >> n >> m >> k >> p) {
        ii graph[1000][1000];
        vector<int> pos;

        int x, y, a, start, end;
        for (int i = 0; i < m; i++) {
            cin >> x >> y;
            graph[x-1][y-1] = {1, 0};
            graph[y-1][x-1] = {1, 0};
        }

        cin >> a;
        for (int i = 0; i < a; i++) {
            cin >> x;
            pos.push_back(x);

            for (int j = 0; j < n; j++) {
                if (graph[j][x-1].first == 1) {
                    graph[j][x-1] = {1, graph[j][x-1].second++};
                }
            }
        }

        cin >> start >> end;
    }

    return 0;
}