#include <iostream>
#include <list>
#include <algorithm>

using namespace std;
#define UNSYNC_CIN ios_base::sync_with_stdio(false);cin.tie(NULL);

int main() {
    UNSYNC_CIN

    int n;
    while (cin >> n) {
        list<int> slist, plist, qlist;
        bool s=true, q=true, pq=true;

        for (int i = 0; i < n; i++) {
            int type, number;
            
            cin >> type >> number;
            if (type == 1) {
                slist.push_back(number);
                qlist.push_back(number);
                plist.push_back(number);
            } else {
                if (s && number != slist.back()) {
                    s=false;
                } else if (s) {
                    slist.pop_back();
                }

                if (q && number != qlist.front()) {
                    q=false;
                } else if (q) {
                    qlist.pop_front();
                }
                
                if (pq) {
                    auto max = max_element(plist.begin(), plist.end());
                    if (number != *max) {
                        pq=false;
                    } else {
                        qlist.erase(max);
                    }
                }
            }
        }

        if (s && q || s && pq || q && pq) std::cout << "not sure" << std::endl;
        else if (!(s || q || pq)) std::cout << "impossible" << std::endl;
        else if (s) std::cout << "stack" << std::endl;
        else if (q) std::cout << "queue" << std::endl;
        else if (pq) std::cout << "priority queue" << std::endl;
    }

    return 0;
}