# slack-off

## Introduction

This project is a tool designed to help you *“stay idle productively”* .

It allows you to:
- Select which camera to use
- Configure an application window to automatically switch to
- Set a people-count threshold for the camera view

When the number of detected people on screen exceeds the specified threshold, the program will automatically switch to the selected application window.

Once everything is configured, you can start the tool and let it run in the background.

## Features

- Camera selection
- Automatic application window switching
- Configurable people-count threshold
- Simple graphical interface
- Designed for background usage

## Supported Platforms

- **Current support:** Windows  
- **Planned support:** macOS

## Requirements

Before running the program, make sure you have the following installed:

- Python
- [`uv`](https://github.com/astral-sh/uv) (Python package manager)

## Installation

1. Install `uv` if you haven’t already.
2. Clone this repository:
   ```bash
   git clone https://github.com/whoami13579/slack-off.git
   cd slack-off
   uv run main.py
