#include "header.hpp"
#include <SFML/Graphics.hpp>
#include <vector>
#include <random>
#include <iostream>
#include <string>

enum class GameState
{
    MENU,
    COIN_SELECT,
    PLAYING,
    PAUSED
};


const int BOARD_SIZE = 10;

struct Button
{
    sf::RectangleShape rect;
    sf::Text label;
    Button() {}
    Button(const sf::Vector2f &pos, const sf::Vector2f &size, const sf::Font &font, const std::string &text, unsigned int charSize = 20)
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
        // center text inside button
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

// simple board cell values (distinct names to avoid colliding with color constants)
enum Cell
{
    CELL_EMPTY = 0,
    CELL_BLACK = 1,
    CELL_WHITE = 2
};

int main()
{
    sf::RenderWindow window(sf::VideoMode(winW, winH), "Gomoku - WorkThief");
    window.setFramerateLimit(60);
    window.setVerticalSyncEnabled(true);
    window.setPosition(sf::Vector2i(sf::VideoMode::getDesktopMode().width / 2u - winW / 2, sf::VideoMode::getDesktopMode().height / 2u - winH / 2));

    // font loading with fallbacks
    sf::Font font;
    bool fontLoaded = false;
    if (font.loadFromFile("./fonts/gf.ttf"))
        fontLoaded = true;
    else
    {std::cerr << "Warning: could not load fonts/arial.ttf or system fallback. Buttons will be blank." << std::endl;
    }

    // intro image
    sf::Image introImg;
    if (!introImg.loadFromFile("./images/intro.png"))
    {
        std::cerr << "Warning: could not load intro image." << std::endl;
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
        // create neutral rectangles with no labels (already safe)
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

    // Board layout
    float boardMargin = 40.0f;
    float boardSizePx = std::min(winW - 2 * boardMargin, winH - 2 * boardMargin - 60.0f);
    float cellSize = boardSizePx / (BOARD_SIZE - 1);
    sf::Vector2f boardOrigin((winW - boardSizePx) / 2.0f, (winH - boardSizePx) / 2.0f + 20.0f);

    // board storage
    std::vector<int> board(BOARD_SIZE * BOARD_SIZE, CELL_EMPTY);

    // player coin choice: humanColor, computerColor
    Cell humanColor = CELL_WHITE; // default
    Cell computerColor = CELL_BLACK;

    bool playerTurn = true; // human starts by default for simplicity

    // random generator for computer moves
    std::random_device rd;
    std::mt19937 rng(rd());

    // helper lambdas
    auto index = [&](int r, int c)
    { return r * BOARD_SIZE + c; };

    auto resetBoard = [&]()
    { std::fill(board.begin(), board.end(), CELL_EMPTY); };

    auto boardPosToCell = [&](const sf::Vector2f &p) -> std::pair<int, int>
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

    auto computerMove = [&]()
    {
        // choose a random empty cell
        std::vector<int> empties;
        for (int i = 0; i < (int)board.size(); ++i)
            if (board[i] == CELL_EMPTY)
                empties.push_back(i);
        if (empties.empty())
            return;
        std::uniform_int_distribution<int> dist(0, (int)empties.size() - 1);
        int pick = empties[dist(rng)];
        board[pick] = computerColor;
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
                sf::Vector2f mp = window.mapPixelToCoords({event.mouseButton.x, event.mouseButton.y});
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
                    if (!playerTurn)
                        break; // ignore clicks when computer's turn
                    auto [r, c] = boardPosToCell(mp);
                    if (r != -1 && c != -1)
                    {
                        int idx = index(r, c);
                        if (board[idx] == CELL_EMPTY)
                        {
                            board[idx] = humanColor;
                            playerTurn = false;
                            // immediate computer move (simple random) after small delay would be nicer
                            computerMove();
                        }
                    }
                }
                else if (state == GameState::PAUSED)
                {
                    // clicking anywhere resumes
                    state = GameState::PLAYING;
                }
            }
        }

        window.clear(BLACK);

        if (state == GameState::MENU)
        {
            // Draw title
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
                    // small outline for contrast
                    piece.setRadius(cellSize * 0.4f - 1.0f);
                    piece.setOrigin(piece.getRadius(), piece.getRadius());
                }

            if (state == GameState::PAUSED && fontLoaded)
            {
                window.draw(pausedText);
            }
        }

        window.display();
    }

    return 0;
}
