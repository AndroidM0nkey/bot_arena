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
    
    vector<vector<int>> dists(n, vector<int>(m, -1));
    queue<pair<int, int>> bfs;
    vector<pair<int,int>> moves = {{0, 1}, {0, -1}, {-1, 0}, {1, 0}};
    pair<int, int> head;

    for (int i = 0; i < n; i++){
        for (int j = 0; j < m; j++){
            if (field[i][j] != 1 && field[i][j] % 2 == 1 && field[i][j] != num_head){
                bfs.push({i, j});
                dists[i][j] = 0;
            }
            if (field[i][j] == num_head){
                head = {i, j};
            }
        }
    }
    
    while (!bfs.empty()){
        auto cur = bfs.front();
        bfs.pop();
        for (auto move : moves){
            pair<int,int> next = {cur.first + move.first, cur.second + move.second};
            if (next.first > -1 && next.first < n && next.second > -1 && next.second < m){
                if (field[next.first][next.second] == 0 && dists[next.first][next.second] == -1){
                    dists[next.first][next.second] = dists[cur.first][cur.second] + 1;
                    bfs.push(next);
                }
            }
        }
    }

    vector<pair<int, int>> pos;

    for (auto move : moves){
        pair<int,int> next = {head.first + move.first, head.second + move.second};
        if (next.first > -1 && next.first < n && next.second > -1 && next.second < m){
            if (dists[next.first][next.second] != -1){
                if (move == moves[0]){
                    pos.push_back({dists[next.first][next.second], 1});
                }
                if (move == moves[1]){
                    pos.push_back({dists[next.first][next.second], 3});
                }                
                if (move == moves[2]){
                    pos.push_back({dists[next.first][next.second], 0});
                }                
                if (move == moves[3]){
                    pos.push_back({dists[next.first][next.second], 2});
                }                
            }
        }
    }    

    pair<int,int> min_pos = {m * n + 1, 0};
    for (auto cur_pos : pos){
        if (cur_pos.first < min_pos.first){
            min_pos = cur_pos;
        }
    }
    
    cout << min_pos.second << endl;

    return 0;
}
