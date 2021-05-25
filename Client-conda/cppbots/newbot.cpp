
#include <bits/stdc++.h>

using namespace std;

#define endl '\n'


class BotAlgorithmA{
private:
    int n, m;
    int num_snake, num_head;

    pair<int,int> head;
    vector<vector<int>> field;
    const vector<pair<int,int>> moves = {{0, 1}, {0, -1}, {-1, 0}, {1, 0}};
    map<const pair<int,int>, int> directions = 
        {{{0, 1}, 1}, {{0, -1}, 3}, {{-1, 0}, 0}, {{1, 0}, 2}};
public:

    void input(){
        cin >> n >> m >> num_snake >> num_head;
        field.assign(n, vector<int>(m));
        for (int i = 0; i < n; i++){
            for (int j = 0; j < m; j++){
                cin >> field[i][j];
            }
        }
    }

    void findHead(){
        for (int i = 0; i < n; i++){
            for (int j = 0; j < m; j++){
                if (field[i][j] == num_head){
                    head = {i, j};
                }
            }
        }
    }

    int number_near_snakes(int i, int j){
        int number = 0;
        for (int k = max(0, i - 10); k < min(n, i + 10); k++){
            for (int u = max(0, j - 10); u < min(m, j + 10); u++){
                if (field[k][u] > 1 && field[k][u] != num_head 
                                    && field[k][u] != num_snake){
                    number++;
                }
            }
        }
        return number;
    }

    vector<vector<int>> calculateBlocks(){
        vector<vector<int>> blocks(n, vector<int>(m, -1));
        for (int i = 0; i < n; i++){
            for (int j = 0; j < m; j++){
                blocks[i][j] = number_near_snakes(i, j);
            }
        }
        return blocks;
    }
    
    bool isCellCorrect(pair<int,int> cell){
        return cell.first > -1 && cell.first <  n 
            && cell.second > -1 && cell.second < m;
    }

    vector<pair<int,int>> makeMoves(pair<int,int> cell){
        vector<pair<int,int>> next_cells;
        for (auto move : moves){
            pair<int,int> next_cell = {cell.first + move.first, 
                                cell.second + move.second};
            if (isCellCorrect(next_cell)){
                next_cells.push_back(next_cell);
            }
        }
        return next_cells;
    }

    bool goToEmptyCell(pair<int, int> cell){
        auto next_cells = makeMoves(cell);
        for (auto next_cell : next_cells){
            if (field[next_cell.first][next_cell.second] == 0){
                pair<int,int> move = {next_cell.first - cell.first, 
                        next_cell.second - cell.second};
                cout << directions[move] << endl;   
                return true; 
            }
        }
        return false;
    }


    void findDirection(){
        findHead();
        vector<vector<int>> blocks = calculateBlocks();
    

        set<pair<int, vector<pair<int,int>>>> s;
        set<pair<int,int>> used;
        vector<pair<int,int>> start = {head};    
        s.insert({blocks[head.first][head.second], start});


        while (!s.empty()){
            auto element = *s.begin();
            s.erase(s.begin());

            int distance = element.first;
            vector<pair<int,int>> cur_path = element.second;
            pair<int,int> vertex = element.second.back();
            
            if (field[vertex.first][vertex.second] == 1){
                pair<int,int> next_cell = cur_path[1];
                pair<int,int> move = {next_cell.first - head.first, 
                        next_cell.second - head.second};
                cout << directions[move] << endl;
                return;
            }

            auto next_cells = makeMoves(vertex);

            for (auto next_cell : next_cells){
                if (field[next_cell.first][next_cell.second] <= 1 && 
                                used.find(next_cell) == used.end()) {
                    used.insert(next_cell);
                    vector<pair<int, int>> new_path = cur_path;
                    new_path.push_back(next_cell);
                    s.insert({distance + 1 + blocks[next_cell.first][next_cell.second], new_path});
                }
            } 
        }

        if (!goToEmptyCell(head)){;
            cout << 0 << endl;
        }
        return;
    }
 
};

int main(){
    BotAlgorithmA bot;
    bot.input();
    bot.findDirection();
    return 0;
}

/*

4 4
2 3
0 0 0 2
0 0 0 3
0 0 0 0
0 0 0 1

*/