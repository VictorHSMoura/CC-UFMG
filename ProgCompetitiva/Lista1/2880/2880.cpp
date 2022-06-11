#include <iostream>
#include <string>

using namespace std;
#define UNSYNC_CIN ios_base::sync_with_stdio(false);cin.tie(NULL);


int main() {
    UNSYNC_CIN

    string message, crib;
    cin >> message >> crib;

    int count = 0;
    for (int i = 0; i <= message.length() - crib.length(); i++) {
        bool no_match = true;
        for (int j = 0; j < crib.length(); j++) {
            if (message[i+j] == crib[j]){
                no_match = false;
                break;
            }
        }
        if (no_match) count++;
    }

    std::cout << count << std::endl;
    return 0;
}