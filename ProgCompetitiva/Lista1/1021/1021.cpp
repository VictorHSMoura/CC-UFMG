#include <iostream>
#include <iomanip>

#define UNSYNC_CIN std::ios_base::sync_with_stdio(false);std::cin.tie(NULL);

int main() {
    UNSYNC_CIN

    double dinheiro, resto;
    int notas[6] = { 100, 50, 20, 10, 5, 2 };
    double moedas[6] = { 100, 50, 25, 10, 5, 1 };

    std::cin >> dinheiro;
    std::cout << std::fixed << std::setprecision(2);
    
    std::cout << "NOTAS:" << std::endl;
    for (int i = 0; i < 6; i++) {
        int q = int(dinheiro) / notas[i];
        std::cout << q << " nota(s) de R$ " << float(notas[i]) << std::endl;
        dinheiro -= q * notas[i];
    }

    dinheiro *= 100;

    std::cout << "MOEDAS:" << std::endl;
    for (int i = 0; i < 6; i++) {
        int q = int(dinheiro) / moedas[i];
        std::cout << q << " moeda(s) de R$ " << float(moedas[i])/100.0 << std::endl;
        dinheiro -= q * moedas[i];
    }
    return 0;
}