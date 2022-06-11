#include <iostream>
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>

using namespace std;
#define UNSYNC_CIN ios_base::sync_with_stdio(false);cin.tie(NULL);

int checkWin(vector<char> p[13], int n, int w_p) {
    for (int i = 0; i < n; i++) {
        unordered_map<char, int> win;
        int win_c = 0;
        for (int c = 0; c < p[i].size(); c++) {
            if (win.find(p[i][c]) == win.end()) {
                win[p[i][c]] = 1;
                win_c++;
            } else {
                win[p[i][c]] += 1;
            }
        }

        for (const auto &[k, value] : win) {
            if (value == 4 && win_c == 1 && w_p != i) {
                return i + 1;
            }
        }
    }
    return 0;
}

int main() {
    UNSYNC_CIN
    
    vector<char> p[13];
    int n, k;
    string cards;

    cin >> n >> k;
    for (int i = 0; i < n; i++) {
        cin >> cards;

        p[i].push_back(cards[0]);
        p[i].push_back(cards[1]);
        p[i].push_back(cards[2]);
        p[i].push_back(cards[3]);
    }

    int w_round = 0, round = 0, w_p = k-1;
    while (true) {
        for (int idx = 0; idx < n; idx++) {
            int win = checkWin(p, n, w_p);
            if (win > 0) {
                cout << win << endl;
                return 0;
            }
            
            int i = (idx + k - 1)%n;
                        
            if (i == w_p && round > w_round) {
                w_p = (i+1)%n;
                w_round = round;
            } else {
                unordered_map<char, int> count;
                vector<char> rev_count[5];
                char choose;
                
                // count each card 
                for (int c = 0; c < p[i].size(); c++) {
                    if (count.find(p[i][c]) == count.end())
                        count[p[i][c]] = 1;
                    else
                        count[p[i][c]] += 1;
                }

                // find least frequent card
                int min = 5;
                for (const auto &[k, value] : count) {
                    if (value < min) min = value;
                    rev_count[value-1].push_back(k);
                }


                bool chosen = false;
                // find least valuable card
                if (rev_count[min-1].size() > 1) {
                    for (char card : "A23456789DQJK") {
                        for (char p_card : rev_count[min-1]) {
                            if (p_card == card) {
                                choose = p_card;
                                chosen = true;
                                break;
                            }
                        }
                        if (chosen) break;
                    }
                } else {
                    choose = rev_count[min-1][0];
                }

                // pass card
                for (int c = 0; c < p[i].size(); c++) {
                    if (choose == p[i][c]) {
                        char card = p[i][c];

                        p[i].erase(p[i].begin() + c);
                        p[(i+1)%n].push_back(card);
                        break;
                    }
                }
            }
        }

        round++;
    }

    return 0;
}