#include <SFML/Graphics.hpp>
#include <SFML/Window.hpp>
#include <SFML/System.hpp>
#include <vector>
#include <random>
#include <iostream>
#include <string>
#include <algorithm>
#include <limits>
#include <unordered_map>
#include <chrono>
using namespace std;

// Constants and colors
const int BOARD_SIZE = 10;
const unsigned int maxWidth = 1080;
const unsigned int maxHeight = 720;
const sf::Color WHITE = sf::Color(200, 200, 200);
const sf::Color BLACK = sf::Color(10, 10, 10);
const sf::Color BOARD_COLOR = sf::Color(160, 140, 10);

const unsigned int winW = sf::VideoMode::getDesktopMode().width * 0.7 > maxWidth ? maxWidth : sf::VideoMode::getDesktopMode().width * 0.7;
const unsigned int winH = sf::VideoMode::getDesktopMode().height * 0.7 > maxHeight ? maxHeight : sf::VideoMode::getDesktopMode().height * 0.7;

enum class GameState
{
    MENU,
    COIN_SELECT,
    PLAYING,
    PAUSED,
    GAME_OVER
};

// Cell values for board
enum Cell
{
    CELL_EMPTY = 0,
    CELL_BLACK = 1,
    CELL_WHITE = 2
};

struct Button
{
    sf::RectangleShape rect;
    sf::Text label;
    Button() {}
    Button(const sf::Vector2f &pos, const sf::Vector2f &size, const sf::Font &font, const string &text, unsigned int charSize = 20)
    {
        rect.setPosition(pos);
        rect.setSize(size);
        rect.setFillColor(sf::Color(100, 100, 140));
        rect.setOutlineColor(sf::Color::Black);
        rect.setOutlineThickness(2.0f);

        label.setFont(font);
        label.setString(text);
        label.setCharacterSize(charSize);
        label.setFillColor(sf::Color::White);
        sf::FloatRect tb = label.getLocalBounds();
        label.setOrigin(tb.left + tb.width / 2.0f, tb.top + tb.height / 2.0f);
        label.setPosition(pos + size / 2.0f);
    }
    bool contains(const sf::Vector2f &p) const { return rect.getGlobalBounds().contains(p); }
    void draw(sf::RenderWindow &w) const
    {
        w.draw(rect);
        w.draw(label);
    }
};

// Transposition table for move caching
struct TranspositionTable {
    unordered_map<string, int> cache;
    
    string boardToKey(const vector<int>& board) const {
        return string(board.begin(), board.end());
    }
    
    bool contains(const vector<int>& board) const {
        return cache.find(boardToKey(board)) != cache.end();
    }
    
    int get(const vector<int>& board) const {
        auto it = cache.find(boardToKey(board));
        return it != cache.end() ? it->second : 0;
    }
    
    void set(const vector<int>& board, int value) {
        cache[boardToKey(board)] = value;
    }
    
    void clear() {
        cache.clear();
    }
};

int main()
{
    sf::RenderWindow window(sf::VideoMode(winW, winH), "Gomoku - WorkThief");
    window.setFramerateLimit(60);
    window.setVerticalSyncEnabled(true);
    window.setPosition(sf::Vector2i(sf::VideoMode::getDesktopMode().width / 2u - winW / 2, sf::VideoMode::getDesktopMode().height / 2u - winH / 2));

    sf::Font font;
    bool fontLoaded = false;
    if (font.loadFromFile("./fonts/gf.ttf"))
        fontLoaded = true;
    else
    {
        cerr << "Warning: could not load fonts/arial.ttf or system fallback. Buttons will be blank." << endl;
    }

    sf::Image introImg;
    if (!introImg.loadFromFile("./images/intro.png"))
    {
        cerr << "Warning: could not load intro image." << endl;
    }
    sf::Texture introTexture;
    introTexture.loadFromImage(introImg);
    sf::Sprite introImage;
    introImage.setTexture(introTexture);
    introImage.setPosition((winW - introTexture.getSize().x) / 2.0f, 30.0f);

    GameState state = GameState::MENU;

    // Menu buttons
    Button startBtn, exitBtn;
    if (fontLoaded)
    {
        startBtn = Button({winW / 2.0f - 120.0f, winH / 2.0f + 120.0f}, {240.0f, 50.0f}, font, "Start Game", 24);
        exitBtn = Button({winW / 2.0f - 120.0f, winH / 2.0f + 200.0f}, {240.0f, 50.0f}, font, "Exit", 24);
    }
    else
    {
        startBtn.rect.setPosition({winW / 2.0f, winH / 2.0f + 160.0f});
        startBtn.rect.setSize({240.0f, 50.0f});
        startBtn.rect.setFillColor(sf::Color(100, 100, 140));
        exitBtn.rect.setPosition({winW / 2.0f, winH / 2.0f + 200.0f});
        exitBtn.rect.setSize({240.0f, 50.0f});
        exitBtn.rect.setFillColor(sf::Color(100, 100, 140));
    }


    // Coin selection buttons
    Button whiteBtn, blackBtn, backBtn;
    if (fontLoaded)
    {
        whiteBtn = Button({winW / 2.0f - 140.0f, winH / 2.0f - 30.0f}, {300.0f, 60.0f}, font, "White (W)", 20);
        blackBtn = Button({winW / 2.0f - 140.0f, winH / 2.0f + 30.0f}, {300.0f, 60.0f}, font, "Black (B)", 20);
        backBtn = Button({20.0f, 20.0f}, {100.0f, 36.0f}, font, "Back", 18);
    }
    else
    {
        whiteBtn.rect.setPosition({winW / 2.0f - 260.0f, winH / 2.0f - 30.0f});
        whiteBtn.rect.setSize({200.0f, 60.0f});
        blackBtn.rect.setPosition({winW / 2.0f + 60.0f, winH / 2.0f - 30.0f});
        blackBtn.rect.setSize({200.0f, 60.0f});
        backBtn.rect.setPosition({20.0f, 20.0f});
        backBtn.rect.setSize({100.0f, 36.0f});
    }

    // Game over buttons
    Button newGameBtn, mainMenuBtn;
    if (fontLoaded)
    {
        newGameBtn = Button({winW / 2.0f - 130.0f, winH / 2.0f + 80.0f}, {250.0f, 50.0f}, font, "New Game", 22);
        mainMenuBtn = Button({winW / 2.0f - 130.0f, winH / 2.0f + 140.0f}, {250.0f, 50.0f}, font, "Main Menu", 22);
    }
    else
    {
        newGameBtn.rect.setPosition({winW / 2.0f - 125.0f, winH / 2.0f + 80.0f});
        newGameBtn.rect.setSize({250.0f, 50.0f});
        newGameBtn.rect.setFillColor(sf::Color(100, 100, 140));
        mainMenuBtn.rect.setPosition({winW / 2.0f - 125.0f, winH / 2.0f + 140.0f});
        mainMenuBtn.rect.setSize({250.0f, 50.0f});
        mainMenuBtn.rect.setFillColor(sf::Color(100, 100, 140));
    }

    // Board layout
    float boardMargin = 40.0f;
    float boardSizePx = min(winW - 2 * boardMargin, winH - 2 * boardMargin - 60.0f);
    float cellSize = boardSizePx / (BOARD_SIZE - 1);
    sf::Vector2f boardOrigin((winW - boardSizePx) / 2.0f, (winH - boardSizePx) / 2.0f + 20.0f);

    // board storage
    vector<int> board(BOARD_SIZE * BOARD_SIZE, CELL_EMPTY);

    // player coin choice
    Cell humanColor = CELL_WHITE;
    Cell computerColor = CELL_BLACK;

    bool playerTurn = true;

    // AI Game Logic Variables
    const int WIN_LENGTH = 5;
    const int MAX_DEPTH = 4;
    Cell winner = CELL_EMPTY;
    bool gameEnded = false;
    
    // Performance optimization: Transposition table
    TranspositionTable tt;
    
    // random generator for computer moves
    random_device rd;
    mt19937 rng(rd());

    // helper lambdas
    auto index = [&](int r, int c) { return r * BOARD_SIZE + c; };

    auto resetBoard = [&]()
    { 
        fill(board.begin(), board.end(), CELL_EMPTY);
        winner = CELL_EMPTY;
        gameEnded = false;
        playerTurn = true;
        tt.clear(); // Clear transposition table
    };

    auto boardPosToCell = [&](const sf::Vector2f &p) -> pair<int, int>
    {
        float x = p.x - boardOrigin.x;
        float y = p.y - boardOrigin.y;
        if (x < -cellSize * 0.5f || y < -cellSize * 0.5f)
            return {-1, -1};
        int c = int((x + cellSize * 0.5f) / cellSize + 0.0001f);
        int r = int((y + cellSize * 0.5f) / cellSize + 0.0001f);
        if (r < 0 || r >= BOARD_SIZE || c < 0 || c >= BOARD_SIZE)
            return {-1, -1};
        return {r, c};
    };

    // OPTIMIZED: Fast winning check
    auto checkWin = [&](const vector<int>& boardState, Cell player) -> bool
    {
        // Check all directions efficiently
        for (int r = 0; r < BOARD_SIZE; ++r)
        {
            for (int c = 0; c < BOARD_SIZE; ++c)
            {
                if (boardState[index(r, c)] != player) continue;
                
                // Check horizontal (right only)
                if (c <= BOARD_SIZE - WIN_LENGTH)
                {
                    bool win = true;
                    for (int i = 1; i < WIN_LENGTH; ++i)
                    {
                        if (boardState[index(r, c + i)] != player) { win = false; break; }
                    }
                    if (win) return true;
                }
                
                // Check vertical (down only)
                if (r <= BOARD_SIZE - WIN_LENGTH)
                {
                    bool win = true;
                    for (int i = 1; i < WIN_LENGTH; ++i)
                    {
                        if (boardState[index(r + i, c)] != player) { win = false; break; }
                    }
                    if (win) return true;
                }
                
                // Check diagonal (down-right only)
                if (r <= BOARD_SIZE - WIN_LENGTH && c <= BOARD_SIZE - WIN_LENGTH)
                {
                    bool win = true;
                    for (int i = 1; i < WIN_LENGTH; ++i)
                    {
                        if (boardState[index(r + i, c + i)] != player) { win = false; break; }
                    }
                    if (win) return true;
                }
                
                // Check anti-diagonal (down-left only)
                if (r <= BOARD_SIZE - WIN_LENGTH && c >= WIN_LENGTH - 1)
                {
                    bool win = true;
                    for (int i = 1; i < WIN_LENGTH; ++i)
                    {
                        if (boardState[index(r + i, c - i)] != player) { win = false; break; }
                    }
                    if (win) return true;
                }
            }
        }
        return false;
    };

    auto checkBoardFull = [&]() -> bool
    {
        for (int cell : board)
            if (cell == CELL_EMPTY)
                return false;
        return true;
    };

    // OPTIMIZED: Generate smart candidate moves only
    auto generateCandidateMoves = [&](const vector<int>& boardState) -> vector<pair<int, int>>
    {
        vector<pair<int, int>> moves;
        
        // If board is empty, start with center
        bool hasPieces = false;
        for (int cell : boardState)
        {
            if (cell != CELL_EMPTY) { hasPieces = true; break; }
        }
        
        if (!hasPieces)
        {
            int center = BOARD_SIZE / 2;
            moves.push_back({center, center});
            return moves;
        }
        
        // Only consider moves near existing pieces
        vector<vector<bool>> considered(BOARD_SIZE, vector<bool>(BOARD_SIZE, false));
        
        for (int r = 0; r < BOARD_SIZE; ++r)
        {
            for (int c = 0; c < BOARD_SIZE; ++c)
            {
                if (boardState[index(r, c)] != CELL_EMPTY)
                {
                    // Check nearby cells within radius 2
                    for (int dr = -2; dr <= 2; ++dr)
                    {
                        for (int dc = -2; dc <= 2; ++dc)
                        {
                            int nr = r + dr, nc = c + dc;
                            if (nr >= 0 && nr < BOARD_SIZE && nc >= 0 && nc < BOARD_SIZE)
                            {
                                if (!considered[nr][nc] && boardState[index(nr, nc)] == CELL_EMPTY)
                                {
                                    considered[nr][nc] = true;
                                    moves.push_back({nr, nc});
                                }
                            }
                        }
                    }
                }
            }
        }
        
        // Add center priority moves if not already included
        int center = BOARD_SIZE / 2;
        if (boardState[index(center, center)] == CELL_EMPTY)
        {
            // Insert center moves at the beginning
            moves.insert(moves.begin(), {center, center});
        }
        
        return moves;
    };


    // OPTIMIZED: Smart move ordering for better alpha-beta pruning
    auto sortMovesByPriority = [&](vector<pair<int, int>>& moves, const vector<int>& boardState, Cell aiPlayer)
    {
        Cell opponent = (aiPlayer == CELL_BLACK) ? CELL_WHITE : CELL_BLACK;
        
        sort(moves.begin(), moves.end(), [&](const pair<int, int>& a, const pair<int, int>& b)
        {
            int priorityA = 0, priorityB = 0;
            
            // Check if move creates immediate win
            auto tempBoardA = boardState;
            tempBoardA[index(a.first, a.second)] = aiPlayer;
            if (checkWin(tempBoardA, aiPlayer)) priorityA += 1000;
            
            auto tempBoardB = boardState;
            tempBoardB[index(b.first, b.second)] = aiPlayer;
            if (checkWin(tempBoardB, aiPlayer)) priorityB += 1000;
            
            // Check if move blocks opponent's immediate win
            tempBoardA = boardState;
            tempBoardA[index(a.first, a.second)] = opponent;
            if (checkWin(tempBoardA, opponent)) priorityA += 500;
            
            tempBoardB = boardState;
            tempBoardB[index(b.first, b.second)] = opponent;
            if (checkWin(tempBoardB, opponent)) priorityB += 500;
            
            // Center distance priority
            int centerDistA = abs(a.first - BOARD_SIZE/2) + abs(a.second - BOARD_SIZE/2);
            int centerDistB = abs(b.first - BOARD_SIZE/2) + abs(b.second - BOARD_SIZE/2);
            priorityA += (BOARD_SIZE - centerDistA);
            priorityB += (BOARD_SIZE - centerDistB);
            
            return priorityA > priorityB;
        });
    };

    // OPTIMIZED: Simple but effective board evaluation
    auto evaluateBoardOptimized = [&](const vector<int>& boardState, Cell aiPlayer) -> int
    {
        Cell opponent = (aiPlayer == CELL_BLACK) ? CELL_WHITE : CELL_BLACK;
        int score = 0;
        
        // Check all lines for patterns
        for (int r = 0; r < BOARD_SIZE; ++r)
        {
            for (int c = 0; c < BOARD_SIZE; ++c)
            {
                if (boardState[index(r, c)] != CELL_EMPTY) continue;
                
                // Check all directions from this empty cell
                const int directions[4][2] = {{0, 1}, {1, 0}, {1, 1}, {1, -1}};
                
                for (auto& dir : directions)
                {
                    int dr = dir[0], dc = dir[1];
                    
                    // Count consecutive pieces in both directions
                    int aiCount = 0, opponentCount = 0;
                    
                    // Forward direction
                    for (int i = 1; i < 5; ++i)
                    {
                        int nr = r + i * dr, nc = c + i * dc;
                        if (nr >= 0 && nr < BOARD_SIZE && nc >= 0 && nc < BOARD_SIZE)
                        {
                            Cell cell = static_cast<Cell>(boardState[index(nr, nc)]);
                            if (cell == aiPlayer) aiCount++;
                            else if (cell == opponent) { opponentCount++; break; }
                            else break;
                        }
                        else break;
                    }
                    
                    // Reverse direction
                    for (int i = 1; i < 5; ++i)
                    {
                        int nr = r - i * dr, nc = c - i * dc;
                        if (nr >= 0 && nr < BOARD_SIZE && nc >= 0 && nc < BOARD_SIZE)
                        {
                            Cell cell = static_cast<Cell>(boardState[index(nr, nc)]);
                            if (cell == aiPlayer) aiCount++;
                            else if (cell == opponent) { opponentCount++; break; }
                            else break;
                        }
                        else break;
                    }
                    
                    // Score based on what this move would create
                    if (opponentCount == 0) // No opponent blocking
                    {
                        if (aiCount >= 4) score += 10000; // Almost win
                        else if (aiCount == 3) score += 1000; // Strong threat
                        else if (aiCount == 2) score += 100; // Good position
                        else if (aiCount == 1) score += 10;
                    }
                    
                    if (aiCount == 0) // No AI pieces
                    {
                        if (opponentCount >= 4) score -= 10000; // Block opponent win
                        else if (opponentCount == 3) score -= 1000; // Block threat
                        else if (opponentCount == 2) score -= 100;
                        else if (opponentCount == 1) score -= 10;
                    }
                }
            }
        }
        
        return score;
    };

    // OPTIMIZED: Minimax with transposition table
    auto minimax = [&](auto&& self, vector<int>& boardState, int depth, int alpha, int beta, bool isMaximizing, Cell aiPlayer) -> int
    {
        // Check transposition table first
        if (depth < MAX_DEPTH - 2) // Cache only deeper positions
        {
            if (tt.contains(boardState))
            {
                return tt.get(boardState);
            }
        }
        
        Cell opponent = (aiPlayer == CELL_BLACK) ? CELL_WHITE : CELL_BLACK;
        
        // Terminal conditions (early exit for performance)
        if (checkWin(boardState, aiPlayer)) return 1000000 - depth;
        if (checkWin(boardState, opponent)) return -1000000 + depth;
        if (depth == 0 || checkBoardFull()) 
        {
            int eval = evaluateBoardOptimized(boardState, aiPlayer);
            if (depth < MAX_DEPTH - 2) tt.set(boardState, eval);
            return eval;
        }
        
        // Generate smart candidate moves
        auto possibleMoves = generateCandidateMoves(boardState);
        sortMovesByPriority(possibleMoves, boardState, aiPlayer);
        
        // Limit moves for performance (keep only best ones)
        if (possibleMoves.size() > 15)
        {
            possibleMoves.resize(15);
        }
        
        if (isMaximizing)
        {
            int maxEval = numeric_limits<int>::min();
            for (const auto& move : possibleMoves)
            {
                boardState[index(move.first, move.second)] = aiPlayer;
                int eval = self(self, boardState, depth - 1, alpha, beta, false, aiPlayer);
                boardState[index(move.first, move.second)] = CELL_EMPTY;
                
                maxEval = max(maxEval, eval);
                alpha = max(alpha, eval);
                if (beta <= alpha) break; // Alpha-beta pruning
            }
            
            if (depth < MAX_DEPTH - 2) tt.set(boardState, maxEval);
            return maxEval;
        }
        else
        {
            int minEval = numeric_limits<int>::max();
            for (const auto& move : possibleMoves)
            {
                boardState[index(move.first, move.second)] = opponent;
                int eval = self(self, boardState, depth - 1, alpha, beta, true, aiPlayer);
                boardState[index(move.first, move.second)] = CELL_EMPTY;
                
                minEval = min(minEval, eval);
                beta = min(beta, eval);
                if (beta <= alpha) break; // Alpha-beta pruning
            }
            
            if (depth < MAX_DEPTH - 2) tt.set(boardState, minEval);
            return minEval;
        }
    };

    auto getBestMoveOptimized = [&](vector<int>& boardState, Cell aiPlayer) -> pair<int, int>
    {
        pair<int, int> bestMove = {-1, -1};
        int bestScore = numeric_limits<int>::min();
        
        auto startTime = chrono::high_resolution_clock::now();
        
        // First check for immediate winning move
        for (int r = 0; r < BOARD_SIZE && bestMove.first == -1; ++r)
        {
            for (int c = 0; c < BOARD_SIZE && bestMove.first == -1; ++c)
            {
                if (boardState[index(r, c)] == CELL_EMPTY)
                {
                    boardState[index(r, c)] = aiPlayer;
                    if (checkWin(boardState, aiPlayer))
                    {
                        bestMove = {r, c};
                    }
                    boardState[index(r, c)] = CELL_EMPTY;
                }
            }
        }
        
        // Then check for immediate blocking move
        if (bestMove.first == -1)
        {
            Cell opponent = (aiPlayer == CELL_BLACK) ? CELL_WHITE : CELL_BLACK;
            for (int r = 0; r < BOARD_SIZE && bestMove.first == -1; ++r)
            {
                for (int c = 0; c < BOARD_SIZE && bestMove.first == -1; ++c)
                {
                    if (boardState[index(r, c)] == CELL_EMPTY)
                    {
                        boardState[index(r, c)] = opponent;
                        if (checkWin(boardState, opponent))
                        {
                            bestMove = {r, c};
                        }
                        boardState[index(r, c)] = CELL_EMPTY;
                    }
                }
            }
        }
        
        // Use optimized minimax for strategic move
        if (bestMove.first == -1)
        {
            auto possibleMoves = generateCandidateMoves(boardState);
            sortMovesByPriority(possibleMoves, boardState, aiPlayer);
            
            // Limit to top moves for performance
            if (possibleMoves.size() > 8)
            {
                possibleMoves.resize(8);
            }
            
            int alpha = numeric_limits<int>::min();
            int beta = numeric_limits<int>::max();
            
            for (const auto& move : possibleMoves)
            {
                boardState[index(move.first, move.second)] = aiPlayer;
                int score = minimax(minimax, boardState, MAX_DEPTH - 1, alpha, beta, false, aiPlayer);
                boardState[index(move.first, move.second)] = CELL_EMPTY;
                
                if (score > bestScore)
                {
                    bestScore = score;
                    bestMove = move;
                }
            }
        }
        
        auto endTime = chrono::high_resolution_clock::now();
        auto duration = chrono::duration_cast<chrono::milliseconds>(endTime - startTime);
        cout << "AI thinking time: " << duration.count() << "ms" << endl;
        
        return bestMove;
    };

    auto computerMove = [&]()
    {
        if (gameEnded) return;
        
        auto bestMove = getBestMoveOptimized(board, computerColor);
        if (bestMove.first != -1)
        {
            board[index(bestMove.first, bestMove.second)] = computerColor;
            
            if (checkWin(board, computerColor))
            {
                winner = computerColor;
                gameEnded = true;
                state = GameState::GAME_OVER;
            }
            else if (checkBoardFull())
            {
                winner = CELL_EMPTY;
                gameEnded = true;
                state = GameState::GAME_OVER;
            }
        }
        
        playerTurn = true;
    };

    // Pause indicator text
    sf::Text pausedText;
    if (fontLoaded)
    {
        pausedText.setFont(font);
        pausedText.setString("Paused - Press P to resume");
        pausedText.setCharacterSize(28);
        pausedText.setFillColor(sf::Color::White);
        sf::FloatRect pb = pausedText.getLocalBounds();
        pausedText.setOrigin(pb.left + pb.width / 2.0f, pb.top + pb.height / 2.0f);
        pausedText.setPosition(winW / 2.0f, 40.0f);
    }

    // Main loop
    while (window.isOpen())
    {
        sf::Event event;
        while (window.pollEvent(event))
        {
            if (event.type == sf::Event::Closed)
                window.close();
            if (event.type == sf::Event::KeyPressed)
            {
                if (event.key.code == sf::Keyboard::Escape)
                {
                    if (state == GameState::MENU)
                        window.close();
                    else
                        state = GameState::MENU;
                }
                if (event.key.code == sf::Keyboard::P)
                {
                    if (state == GameState::PLAYING)
                        state = GameState::PAUSED;
                    else if (state == GameState::PAUSED)
                        state = GameState::PLAYING;
                }
            }

            if (event.type == sf::Event::MouseButtonPressed && event.mouseButton.button == sf::Mouse::Left)
            {
                sf::Vector2i mousePos = sf::Mouse::getPosition(window);
                sf::Vector2f mp = window.mapPixelToCoords(mousePos);
                
                if (state == GameState::MENU)
                {
                    if (startBtn.contains(mp))
                    {
                        state = GameState::COIN_SELECT;
                    }
                    else if (exitBtn.contains(mp))
                    {
                        window.close();
                    }
                }
                else if (state == GameState::COIN_SELECT)
                {
                    if (whiteBtn.contains(mp))
                    {
                        humanColor = CELL_WHITE;
                        computerColor = CELL_BLACK;
                        playerTurn = true;
                        resetBoard();
                        state = GameState::PLAYING;
                    }
                    else if (blackBtn.contains(mp))
                    {
                        humanColor = CELL_BLACK;
                        computerColor = CELL_WHITE;
                        playerTurn = true;
                        resetBoard();
                        state = GameState::PLAYING;
                    }
                    else if (backBtn.contains(mp))
                    {
                        state = GameState::MENU;
                    }
                }
                else if (state == GameState::PLAYING)
                {
                    if (!playerTurn || gameEnded)
                    {
                        continue;
                    }
                    

                    pair<int, int> cellPos = boardPosToCell(mp);
                    int r = cellPos.first;
                    int c = cellPos.second;
                    
                    if (r != -1 && c != -1)
                    {
                        int idx = index(r, c);
                        if (board[idx] == CELL_EMPTY)
                        {
                            board[idx] = humanColor;
                            
                            if (checkWin(board, humanColor))
                            {
                                winner = humanColor;
                                gameEnded = true;
                                state = GameState::GAME_OVER;
                            }
                            else if (checkBoardFull())
                            {
                                winner = CELL_EMPTY;
                                gameEnded = true;
                                state = GameState::GAME_OVER;
                            }
                            else
                            {
                                playerTurn = false;
                                computerMove();
                            }
                        }
                    }
                }
                else if (state == GameState::PAUSED)
                {
                    state = GameState::PLAYING;
                }

                else if (state == GameState::GAME_OVER)
                {
                    if (newGameBtn.contains(mp))
                    {
                        resetBoard();
                        state = GameState::PLAYING;
                    }
                    else if (mainMenuBtn.contains(mp))
                    {
                        state = GameState::MENU;
                    }
                }
            }
        }

        window.clear(BLACK);

        if (state == GameState::MENU)
        {
            if (fontLoaded)
            {
                sf::Text title("Gomoku", font, 48);
                title.setFillColor(WHITE);
                sf::FloatRect tb = title.getLocalBounds();
                title.setOrigin(tb.left + tb.width / 2.0f, tb.top + tb.height / 2.0f);
                title.setPosition(winW / 2.0f, winH / 2.0f);
                window.draw(title);
            }
            window.draw(introImage);
            startBtn.draw(window);
            exitBtn.draw(window);
        }
        else if (state == GameState::COIN_SELECT)
        {
            if (fontLoaded)
            {
                sf::Text title("Choose Your Coin", font, 36);
                title.setFillColor(WHITE);
                sf::FloatRect tb = title.getLocalBounds();
                title.setOrigin(tb.left + tb.width / 2.0f, tb.top + tb.height / 2.0f);
                title.setPosition(winW / 2.0f, winH / 2.0f - 120.0f);
                window.draw(title);
            }
            whiteBtn.draw(window);
            blackBtn.draw(window);
            backBtn.draw(window);
        }
        else if (state == GameState::PLAYING || state == GameState::PAUSED)
        {
            // draw board background
            sf::RectangleShape bg;
            bg.setPosition(boardOrigin.x - cellSize / 2.0f, boardOrigin.y - cellSize / 2.0f);
            bg.setSize({cellSize * (BOARD_SIZE - 1) + cellSize, cellSize * (BOARD_SIZE - 1) + cellSize});
            bg.setFillColor(BOARD_COLOR);
            bg.setOutlineColor(sf::Color::Black);
            bg.setOutlineThickness(2.0f);
            window.draw(bg);

            // grid lines
            for (int i = 0; i < BOARD_SIZE; ++i)
            {
                sf::Vertex hline[] = {
                    sf::Vertex({boardOrigin.x, boardOrigin.y + i * cellSize}, sf::Color::Black),
                    sf::Vertex({boardOrigin.x + (BOARD_SIZE - 1) * cellSize, boardOrigin.y + i * cellSize}, sf::Color::Black)};
                sf::Vertex vline[] = {
                    sf::Vertex({boardOrigin.x + i * cellSize, boardOrigin.y}, sf::Color::Black),
                    sf::Vertex({boardOrigin.x + i * cellSize, boardOrigin.y + (BOARD_SIZE - 1) * cellSize}, sf::Color::Black)};
                window.draw(hline, 2, sf::Lines);
                window.draw(vline, 2, sf::Lines);
            }

            // draw pieces
            for (int r = 0; r < BOARD_SIZE; ++r)
                for (int c = 0; c < BOARD_SIZE; ++c)
                {
                    int v = board[index(r, c)];
                    if (v == CELL_EMPTY)
                        continue;
                    sf::CircleShape piece(cellSize * 0.4f);
                    sf::Vector2f center(boardOrigin.x + c * cellSize, boardOrigin.y + r * cellSize);
                    piece.setOrigin(piece.getRadius(), piece.getRadius());
                    piece.setPosition(center);
                    if (v == CELL_BLACK)
                        piece.setFillColor(sf::Color::Black);
                    else
                        piece.setFillColor(sf::Color::White);
                    window.draw(piece);
                    piece.setRadius(cellSize * 0.4f - 1.0f);
                    piece.setOrigin(piece.getRadius(), piece.getRadius());
                }

            if (state == GameState::PAUSED && fontLoaded)
            {
                window.draw(pausedText);
            }

            else if (state == GameState::GAME_OVER)
            {
                // Draw semi-transparent overlay
                sf::RectangleShape overlay;
                overlay.setSize(sf::Vector2f(winW, winH));
                overlay.setFillColor(sf::Color(0, 0, 0, 180));
                window.draw(overlay);
                
                if (fontLoaded)
                {
                    // Enhanced winner splash with better styling
                    sf::Text gameOverText;
                    gameOverText.setFont(font);
                    gameOverText.setCharacterSize(64);
                    
                    // Winner-specific colors
                    if (winner == CELL_EMPTY)
                    {
                        gameOverText.setString("IT'S A DRAW!");
                        gameOverText.setFillColor(sf::Color(200, 200, 200)); // Light gray for draw
                    }
                    else if (winner == humanColor)
                    {
                        gameOverText.setString("CONGRATULATIONS!");
                        gameOverText.setFillColor(sf::Color(50, 205, 50)); // Lime green for win
                    }
                    else
                    {
                        gameOverText.setString("GAME OVER");
                        gameOverText.setFillColor(sf::Color(220, 20, 60)); // Crimson for loss
                    }
                    
                    sf::FloatRect textBounds = gameOverText.getLocalBounds();
                    gameOverText.setOrigin(textBounds.left + textBounds.width / 2.0f, 
                                          textBounds.top + textBounds.height / 2.0f);
                    gameOverText.setPosition(winW / 2.0f, winH / 2.0f - 100.0f);
                    window.draw(gameOverText);
                    
                    // Subtitle with result
                    sf::Text subtitleText;
                    subtitleText.setFont(font);
                    subtitleText.setCharacterSize(32);
                    
                    if (winner == CELL_EMPTY)
                    {
                        subtitleText.setString("No winner this time");
                    }
                    else if (winner == humanColor)
                    {
                        subtitleText.setString("YOU WIN!");
                    }
                    else
                    {
                        subtitleText.setString("Computer wins");
                    }
                    
                    subtitleText.setFillColor(WHITE);
                    sf::FloatRect subtitleBounds = subtitleText.getLocalBounds();
                    subtitleText.setOrigin(subtitleBounds.left + subtitleBounds.width / 2.0f, 
                                          subtitleBounds.top + subtitleBounds.height / 2.0f);
                    subtitleText.setPosition(winW / 2.0f, winH / 2.0f - 40.0f);
                    window.draw(subtitleText);
                    
                    // Draw the new game buttons
                    newGameBtn.draw(window);
                    mainMenuBtn.draw(window);
                }
            }
        }

        window.display();
    }

    return 0;
}
