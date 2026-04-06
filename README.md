# 🤖CAD Copilot

> AI-Powered 3D CAD Modeling Assistant - Create complex 3D models using natural language

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PythonOCC](https://img.shields.io/badge/PythonOCC-7.7+-green.svg)](https://github.com/tpaviot/pythonocc-core)

[English](README.md) | [中文文档](README_CN.md)

## ✨ Features

- 🗣️ **Natural Language Interface** - Create 3D models using plain English commands
- 🧠 **AI-Powered Planning** - GPT-4 intelligently converts instructions into CAD operations
- 🎨 **Real-time 3D Visualization** - Interactive OpenCASCADE-based 3D viewer
- 🔧 **Boolean Operations** - Union, difference, and intersection operations
- 📦 **STL Export** - Export your models for 3D printing
- 📝 **Operation Logging** - Complete history tracking with feedback system
- 🎯 **Smart ID Resolution** - Automatic dependency tracking for complex multi-step operations

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Conda (recommended for PythonOCC installation)
- OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/voidO-O/cad-copilot.git
cd cad-copilot
```

2. **Create conda environment and install PythonOCC**
```bash
conda create -n cad python=3.10
conda activate cad
conda install -c conda-forge pythonocc-core
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure API key**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

5. **Run the application**
```bash
cd src
python main.py
```

## 💡 Usage Examples

### Basic Shapes
```
"Create a sphere with radius 10"
"Add a cylinder with radius 5 and height 20 to the right"
```

### Boolean Operations
```
"Merge the sphere and cylinder"
"Subtract a small sphere from the top"
```

### Complex Modeling
```
"Create a bearing housing with mounting holes"
"Make a gear with 20 teeth"
```

### Export
```
"Export the model as STL"
```

## 🏗️ Architecture

```
cad-copilot/
├── src/
│   ├── main.py              # GUI application entry point
│   ├── llm_real.py          # AI planning engine
│   ├── controller.py        # Execution controller
│   ├── cad_builder.py       # CAD geometry primitives
│   ├── tools.py             # Tool registry and implementations
│   ├── viewer.py            # 3D visualization
│   ├── session_context.py   # Object registry and state management
│   └── logger_utils.py      # Interaction logging
├── logs/                    # Operation logs
├── exports/                 # STL export directory
└── requirements.txt         # Python dependencies
```

## 🔑 Key Components

### AI Planning Engine (`llm_real.py`)
- Converts natural language to structured JSON operations
- Handles complex multi-step planning
- Automatic ID resolution and dependency tracking

### CAD Builder (`cad_builder.py`)
- Primitive shape creation (sphere, cylinder, cone, torus)
- Boolean operations (union, difference, intersection)
- Transformation operations

### Smart Controller (`controller.py`)
- Executes planned operations sequentially
- Manages object registry and visibility
- Error handling and recovery

## 📋 Supported Operations

| Category | Operations |
|----------|-----------|
| **Primitives** | Sphere, Cylinder, Cone, Torus |
| **Boolean** | Union (Fuse), Difference (Cut), Intersection (Common) |
| **Transform** | Translate, Scale |
| **Management** | Delete, Reset, Visibility Control |
| **Export** | STL Export |

## ⚙️ Configuration

Edit `.env` file to configure:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

## 🎬 Demo Recording Script

For creating demo videos, try these scenarios:

1. **Basic Modeling** (30s)
   - "Create a sphere with radius 10"
   - "Create a cylinder with radius 5 and height 20 at position [20, 0, 0]"

2. **Boolean Operations** (30s)
   - "Fuse the sphere and cylinder"
   - "Create a small sphere at the top and subtract it"

3. **Complex Example** (60s)
   - "Create a bearing housing with mounting holes"
   - Show the step-by-step AI planning

4. **Export** (15s)
   - "Export the model as bearing_housing.stl"

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [PythonOCC](https://github.com/tpaviot/pythonocc-core) - Python bindings for OpenCASCADE
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework
- [OpenAI](https://openai.com/) - AI language models

## 📧 Contact

Project Link: [https://github.com/voidO-O/cad-copilot](https://github.com/voidO-O/cad-copilot)

<video src="https://github.com/voidO-O/cad-copilot/blob/main/demo.mp4?raw=true" width="100%" controls>
  您的浏览器不支持视频播放。
</video>

---

⭐ Star this repo if you find it helpful!
