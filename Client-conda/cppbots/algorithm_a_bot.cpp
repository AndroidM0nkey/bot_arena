
#include <iostream>
#include <vector>
#include <set>
#include <map>

class Cell {
private:

    int str, col;

public:

    Cell() {

    }

    Cell(const int& new_str, const int& new_col) {
        str = new_str;
        col = new_col;
    }

    friend std::ostream& operator<< (std::ostream &out, const Cell &cell);
    
    friend std::istream& operator>> (std::istream &in, Cell &cell);

    int getStr() const {
        return str;
    }

    int getCol() const {
        return col;
    }

    bool isCorrect(const int& n, const int& m) const {
        return str > -1 && str < n && col > -1 && col < m;
    }

    Cell operator +(const std::pair<int, int>& move) const {
        return Cell(str + move.first, col + move.second);
    }

    std::pair<int,int> operator -(const Cell& other_cell) const {
        return {str - other_cell.getStr(), col - other_cell.getCol()};
    }

    std::pair<int,int> toPair() const {
        return {str, col};
    }

    bool operator < (const Cell& other_cell) const {
        if (str < other_cell.getStr()){
            return true;
        }

        if (str == other_cell.getStr() && col < other_cell.getCol()) {
            return true;
        }

        return false;
    }
};

std::ostream& operator <<(std::ostream &out, const Cell &cell) {
    out <<  cell.str << " " << cell.col << std::endl;
    return out;
}

std::istream& operator >>(std::istream &in, Cell &cell) {
    in >>  cell.str >> cell.col;
    return in;
}

class GameState{
private:
    int height, width;
    int num_snake, num_head;

    Cell head;
    std::vector<std::vector<int>> field;

    const int BLOCK_SIZE = 5;

public:

    friend std::ostream& operator <<(std::ostream &out, const GameState &game_state);
    friend std::istream& operator>> (std::istream &in, GameState &game_state);

    GameState(){

    }

    Cell getHead() const {
        return head;
    }

    int getHeight() const {
        return height;
    }

    int getWidth() const {
        return width;
    }

    int operator [](const Cell& cell) const {
        return field[cell.getStr()][cell.getCol()];
    }

    int numberNearSnakes(const int& str, const int& col) const {
        int number = 0;
        for (int k = std::max(0, str - BLOCK_SIZE); k < 
                std::min(height, str + BLOCK_SIZE); k++) {
            for (int u = std::max(0, col - BLOCK_SIZE); 
                    u < std::min(width, col + BLOCK_SIZE); u++) {
                if (field[k][u] > 1 && field[k][u] != num_head && field[k][u] != num_snake) {
                    number++;
                }
            }
        }
        return number;
    }

    std::vector<std::vector<int>> calculateNearSnakes() const {
        std::vector<std::vector<int>> blocks(height, std::vector<int>(width, -1));
        for (int i = 0; i < height; i++) {
            for (int j = 0; j < width; j++) {
                blocks[i][j] = numberNearSnakes(i, j);
            }
        }
        return blocks;
    }

    std::vector<Cell> makeMoves(const Cell& cell, const std::vector<std::pair<int,int>>& moves) const {
        std::vector<Cell> next_cells;
        for (const auto& move : moves) {
            Cell next_cell = cell + move;
            if (next_cell.isCorrect(height, width)) {
                next_cells.push_back(next_cell);
            }
        }
        return next_cells;
    }

    bool isCellApple(const Cell& cell) const {
        return (*this)[cell] == 1;
    }

    bool isCellAppleorEmpty(const Cell& cell) const {
        return (*this)[cell] <= 1;
    }
};






std::ostream& operator <<(std::ostream &out, const GameState &game_state) {
    out << game_state.height << " " << game_state.width << std::endl;
    out << game_state.num_snake << " " << game_state.num_head << std::endl;
    for (int i = 0; i < game_state.height; i++) {
        for (int j = 0; j < game_state.width; j++) {
            out << game_state.field[i][j] << " ";
        }
        out << std::endl;
    }
    return out;
}

std::istream& operator >>(std::istream &in, GameState &game_state) {
    in >> game_state.height >> game_state.width;
    in >> game_state.num_snake >> game_state.num_head;
    game_state.field.assign(game_state.height, std::vector<int> (game_state.width));

    for (int i = 0; i < game_state.height; i++) {
        for (int j = 0; j < game_state.width; j++) {
            in >> game_state.field[i][j];
            if (game_state.field[i][j] == game_state.num_head) {
                game_state.head = Cell(i, j);
            }
        }
    }
    return in;
}


class AlgorithmA {
private:
    GameState game_state;
    const std::vector<std::pair<int,int>> moves = {{0, 1}, {0, -1}, {-1, 0}, {1, 0}};
    std::map<std::pair<int,int>, int> directions = 
        {{{0, 1}, 1}, {{0, -1}, 3}, {{-1, 0}, 0}, {{1, 0}, 2}};

    
public:

    AlgorithmA() {

    }

    void input_data() {
        std::cin >> game_state;
    }    

    bool goToEmptyCell() {
        Cell head = game_state.getHead();
        std::vector<Cell> next_cells = game_state.makeMoves(head, moves);
        for (const auto& next_cell : next_cells) {
            if (game_state[next_cell] == 0) {
                std::cout << directions[next_cell - head] << std::endl;   
                return true; 
            }
        }
        return false;
    }

    bool makeAlgorithmA() {
        std::vector<std::vector<int>> blocks = game_state.calculateNearSnakes();
        
        Cell head = game_state.getHead();

        std::set<std::pair<int, std::vector<Cell>>> algo_set;

        std::set<std::pair<int,int>> used;
        used.insert(head.toPair());
        std::vector<Cell> start = {head};    
        algo_set.insert({blocks[head.getStr()][head.getCol()], start});


        while (!algo_set.empty()) {
            auto element = *algo_set.begin();
            algo_set.erase(algo_set.begin());

            int distance = element.first;
            std::vector<Cell> cur_path = element.second;
            Cell vertex = element.second.back();

            if (game_state.isCellApple(vertex) == 1) {
                Cell next_cell = cur_path[1];
                std::cout << directions[next_cell - head] << std::endl;
                return true;
            }

            std::vector<Cell> next_cells = game_state.makeMoves(vertex, moves);
            for (auto next_cell : next_cells) {
                if (game_state.isCellAppleorEmpty(next_cell) && 
                                used.find(next_cell.toPair()) == used.end()) {
                    used.insert(next_cell.toPair());
                    
                    std::vector<Cell> new_path = cur_path;
                    new_path.push_back(next_cell);

                    int new_distance = distance + 1;
                    new_distance += blocks[next_cell.getStr()][next_cell.getStr()];

                    algo_set.insert({new_distance, new_path});
                }
            } 
        }
        return false;
    }
};



class Bot{
private:
    AlgorithmA algoritm;

    const int DEFAULT_DIRECTION = 0;
public:

    Bot(){

    }

    void findDirection(){
        algoritm.input_data();

        if (!algoritm.makeAlgorithmA()){
            if (!algoritm.goToEmptyCell()){
                std::cout << DEFAULT_DIRECTION << std::endl;
            }
        }
    }
};

int main(){
    Bot bot;
    bot.findDirection();

}
