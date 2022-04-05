#include <iostream>
#include <string>

#define UNSYNC_CIN std::ios_base::sync_with_stdio(false);std::cin.tie(NULL);

int main() {
    UNSYNC_CIN

    int d;
    char letra;

    do {
        std::cin >> d;
        if (d == 0) break;

        std::cin >> letra;
        std::cin.ignore(); // flush cin  \n

        if (letra == 'S') {
            std::string l1 = "", l2 = "", l3 = "", number;
            std::cin >> number;

            for (int i = 0; i < d; i++) {
                char n = number[i];

                if (i > 0) { l1 += " "; l2 += " "; l3 += " "; }
                switch (n) {
                    case '0': l1 += ".*"; l2 += "**"; l3 += "..";
                        break;
                    case '1': l1 += "*."; l2 += ".."; l3 += "..";
                        break;
                    case '2': l1 += "*."; l2 += "*."; l3 += "..";
                        break;
                    case '3': l1 += "**"; l2 += ".."; l3 += "..";
                        break;
                    case '4': l1 += "**"; l2 += ".*"; l3 += "..";
                        break;
                    case '5': l1 += "*."; l2 += ".*"; l3 += "..";
                        break;
                    case '6': l1 += "**"; l2 += "*."; l3 += "..";
                        break;
                    case '7': l1 += "**"; l2 += "**"; l3 += "..";
                        break;
                    case '8': l1 += "*."; l2 += "**"; l3 += "..";
                        break;
                    case '9': l1 += ".*"; l2 += "*."; l3 += "..";
                        break;
                    default:
                        break;
                }
            }
            std::cout << l1 << std::endl << l2 << std::endl << l3 << std::endl;
        } else {
            std::string l1, l2, l3, number = "";
            std::getline(std::cin, l1);
            std::getline(std::cin, l2);
            std::getline(std::cin, l3);
            
            int i = 0;
            while (i <= (d * 3) - 1) {
                std::string b = l1.substr(i, 2) + l2.substr(i, 2) + l3.substr(i, 2);
                
                if (b == ".***..") number += "0";
                else if (b == "*.....") number += "1";
                else if (b == "*.*...") number += "2";
                else if (b == "**....") number += "3";
                else if (b == "**.*..") number += "4";
                else if (b == "*..*..") number += "5";
                else if (b == "***...") number += "6";
                else if (b == "****..") number += "7";
                else if (b == "*.**..") number += "8";
                else if (b == ".**...") number += "9";
                
                i += 3;
            }
            std::cout << number << std::endl;
        }
    } while(d != 0);
}