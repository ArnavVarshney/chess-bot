# Chess GUI Project

This project is a Graphical User Interface (GUI) for playing chess, written in Python. It provides a visually appealing and interactive way to play chess against another human player. The project is designed with a focus on usability and flexibility, offering various customization options to enhance the user experience.

## Features

- **Interactive Chess Board**: The chess board is fully interactive, allowing players to make moves by clicking on the pieces and their destination squares.

- **Board Color Customization**: The project offers the ability to change the color theme of the chess board. There are several predefined color themes available, including gray, green, blue, and brown.

- **Game Modes**: The game supports different modes, including a neutral mode and a play mode. The neutral mode is the default mode when the game is launched, and the play mode is activated when the player starts a game.

- **Game Status Updates**: The game status is continuously updated and displayed to the user, providing information about the current mode and other game-related details.

- **Move List**: The move list is updated in real-time as the game progresses, showing all the moves made by both players.

- **Real-time Chess Board Analysis**: The project uses a camera to read the real-time chess board status and displays it on the UI. This is achieved by capturing an image of the chess board using the camera, analyzing the image to determine the positions of the pieces on the board, and then updating the GUI to reflect the current state of the chess board. The analysis stats are stored in a JSON file for further use.

## Getting Started

To get started with this project, you need to have Python and the requirements in `requirements.txt` installed on your machine. Once Python is installed, you can clone the repository and run the `chess_gui.py` file to start the game.

## License

This project is licensed under the MIT License. Please see the `LICENSE` file for more details.
