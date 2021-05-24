
#include <bits/stdc++.h>

using namespace std;

#define endl '\n'

int main(){
    int n, m, num_snake, num_head;
    cin >> n >> m >> num_snake >> num_head;
    vector<vector<int>> field(n, vector<int>(m));
    for (int i = 0; i < n; i++){
        for (int j = 0; j < m; j++){
            cin >> field[i][j];
        }
    }


    pair<int, int> head;

    for (int i = 0; i < n; i++){
        for (int j = 0; j < m; j++){
            if (field[i][j] == num_head){
                head = {i, j};
            }
        }
    }
    
    vector<vector<int>> dists(n, vector<int>(m, -1));
    vector<vector<int>> blocks(n, vector<int>(m, -1));
    for (int i = 0; i < n; i++){
        for (int j = 0; j < m; j++){
            int number = 0;
            for (int k = i - i % 10; k < min(n, i + (10 - i % 10)); k++){
                for (int u = j - j % 10; u < min(m, j + (10 - j % 10)); u++){
                    if (field[k][u] > 1 && field[k][u] != num_head && field[k][u] != num_snake){
                        number++;
                    }
                }
            }
            blocks[i][j] = number;
            //cout << blocks[i][j] << " ";
        }
        //cout << endl;
    }

    

    vector<pair<int,int>> moves = {{0, 1}, {0, -1}, {-1, 0}, {1, 0}};
    set<pair<int, vector<pair<int,int>>>> s;
    set<pair<int,int>> used;
    vector<pair<int,int>> start = {head};
    s.insert({4 * blocks[head.first][head.second], start});
    //s.insert({0, start});

    while (!s.empty()){
        auto vertex = *s.begin();
        s.erase(s.begin());
        pair<int,int> ver = vertex.second.back();
        //cout << ver.first + 1 << " " << ver.second + 1 << " " << vertex.first << endl;
        if (field[ver.first][ver.second] == 1){
            for (auto move : moves){
                pair<int,int> next = {head.first + move.first, head.second + move.second};
                if (next == vertex.second[1]){
                    if (move == moves[0]){
                        cout << 1 << endl;
                    }
                    if (move == moves[1]){
                        cout << 3 << endl;
                    }                
                    if (move == moves[2]){
                        cout << 0 << endl;
                    }                
                    if (move == moves[3]){
                        cout << 2 << endl;
                    }  
                    //cout << "APPPLE " << vertex.second[1].first + 1 << " " << vertex.second[1].second + 1<< endl;
                    return 0;
                }
            }
        }
        for (auto move : moves){
            pair<int,int> next = {ver.first + move.first, ver.second + move.second};
            if (next.first > -1 && next.first < n && next.second > -1 && next.second < m){
                if (field[next.first][next.second] <= 1){
                    if (used.find(next) == used.end()){
                        used.insert(next);
                        int new_dist = vertex.first + 1;
                        vector<pair<int, int>> new_vec = vertex.second;
                        new_vec.push_back(next);
                        s.insert({new_dist + 4 * blocks[next.first][next.second], new_vec});
                        //s.insert({new_dist, new_vec});
                    }
                }
            }
        }
    }
    
 
    
    for (auto move : moves){
        pair<int,int> next = {head.first + move.first, head.second + move.second};
        if (next.first > -1 && next.first < n && next.second > -1 && next.second < m){
            if (field[next.first][next.second] == 0){
                if (move == moves[0]){
                    cout << 1 << endl;
                }
                if (move == moves[1]){
                    cout << 3 << endl;
                }                
                if (move == moves[2]){
                    cout << 0 << endl;
                }                
                if (move == moves[3]){
                    cout << 2 << endl;
                }                
                return 0;
            }
        }
    }    

    cout << 0 << endl;

    return 0;
}

/*

6 6
2 3

0 0 0 0 0 0
0 0 0 0 0 0
0 0 0 2 2 0
1 0 0 3 2 0
0 0 0 0 0 0
0 0 0 0 0 0


*/