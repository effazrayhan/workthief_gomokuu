#include <SFML/Graphics.hpp>

#define ull unsigned long long
#define maxWidth 1080
#define maxHeight 720
#define MAX_HEALTH 100u

const sf::Color GREEN = sf::Color(10, 220, 20);
const sf::Color WHITE = sf::Color(200, 200, 200);
const sf::Color BLACK = sf::Color(10, 10, 10);
const sf::Color BOARD_COLOR = sf::Color(160, 140, 10);


const unsigned int winW = sf::VideoMode::getDesktopMode().width * 0.7 > maxWidth ? maxWidth : sf::VideoMode::getDesktopMode().width * 0.7;     // monitor display width er 80% or maxWidth
const unsigned int winH = sf::VideoMode::getDesktopMode().height * 0.7 > maxHeight ? maxHeight : sf::VideoMode::getDesktopMode().height * 0.7; // monitor display height er 80% or maxHeight
const float bufferOffset = 20.0f;
const float gravity = 9.81f; // m/s^2

class RamInfo
{
private:
    /* data */
    ull total_kb;
    ull available_kb;

public:
    RamInfo(/* args */);
    RamInfo(/* args */ ull total = 0, ull available = 0);
    ull getTotal() { return total_kb; }
    ull getAvailable() { return available_kb; }
    ull getUsed() { return total_kb - available_kb; }
    ~RamInfo();
};

class WindowSize
{
private:
    /* data */
    ull w;
    ull h;

public:
    WindowSize(/* args */);
    WindowSize(/* args */ ull w = 0, ull h = 0);
    ull getWidth() { return w; }
    ull getHeight() { return h; }
    ~WindowSize();
};

class CpuInfo
{
private:
    ull prev_total;
    ull prev_idle;

public:
    CpuInfo();
    // returns CPU usage percent (0.0 - 100.0)
    float getUsagePercent();
    ~CpuInfo();
};
