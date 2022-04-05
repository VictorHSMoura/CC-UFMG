#include <iostream>
#include <string>
#include <map>

using namespace std;

#define UNSYNC_CIN ios_base::sync_with_stdio(false);cin.tie(NULL);

int main() {
    UNSYNC_CIN

    string s;
    map<string, bool> m;

    int count = 0;
    while(getline(cin, s)) {
        if (m.find(s) == m.end()) {
            m[s] = true;
            count ++;
        }
    }
    cout << count << endl;

    return 0;
}