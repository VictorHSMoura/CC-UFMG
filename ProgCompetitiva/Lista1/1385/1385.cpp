#include <iostream>
#include <string>
#include <cctype>

using namespace std;
#define UNSYNC_CIN ios_base::sync_with_stdio(false);cin.tie(NULL);

int main() {
    UNSYNC_CIN

    int c;
    cin >> c;
    cin.ignore();

    while (c > 0) {
    	string line, topFormatted = "";
    	getline(cin, line);

    	int pos = 0, ncol = 1;
    	while (pos < line.length()) {
    		if (line[pos] == 'P') {
    			topFormatted += line[pos];
    			topFormatted += line[pos+1];
    			topFormatted += ' ';
    			pos += 2;
    			ncol++;
    		} else {
    			topFormatted += line[pos];
    			pos++;
    		}
    	}
    	cout << topFormatted << endl;

    	while (true) {
    		string n_line = "";
    		int n_nums = 0;
    		bool space = false;

	    	getline(cin, line);

	    	if (line[0] == 'T' && line[1] == 'P') {
	    		break;
	    	}

	    	pos = 0;
	    	while (pos < line.length()) {
	    		if (isalpha(line[pos])) {
	    			n_line += line[pos];
	    		} else {
	    			if (!space) {
	    				n_line += ' ';
	    				space = true;
	    			}
	    			n_line += line[pos];
	    			n_nums++;
	    		}
	    		pos++;
	    	}

	    	cout << n_line << endl;
	    	cout << float(n_nums) / (ncol) << endl;
	    }
    	c--;
    }

    return 0;
}