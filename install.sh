#!/bin/bash

/usr/bin/g++ main.cpp -o gomoku.play -lsfml-graphics -lsfml-window -lsfml-system

echo "If no error shown then BUILD complete. Run \`./gomoku.play\` to start the game."