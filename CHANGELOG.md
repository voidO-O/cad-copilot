# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Unit test coverage
- More primitive shapes (box, prism)
- Sketch-based modeling
- Material and texture support

## [2.0.0] - 2024-XX-XX

### Added
- 🧠 AI-powered natural language interface using GPT-4
- 🎨 Real-time 3D visualization with PythonOCC
- 🔧 Complete boolean operations (union, difference, intersection)
- 📦 STL export functionality
- 📝 Comprehensive logging system with JSONL format
- 🎯 Smart ID resolution for complex multi-step operations
- 👍 User feedback system
- 🌐 Bilingual documentation (English & Chinese)

### Core Components
- `main.py` - Modern CustomTkinter GUI
- `llm_real.py` - AI planning engine with deterministic ID mapping
- `controller.py` - Execution controller with error handling
- `cad_builder.py` - CAD geometry primitives
- `tools.py` - Extensible tool registry
- `viewer.py` - Interactive 3D viewer
- `session_context.py` - Object registry and state management
- `logger_utils.py` - Interaction logging

### Supported Operations
- Primitives: Sphere, Cylinder, Cone, Torus
- Transforms: Translate, Scale
- Boolean: Cut, Fuse, Common
- Management: Delete, Reset, Visibility Control
- Export: STL format

## [1.0.0] - Initial Development

### Added
- Basic CAD modeling framework
- Simple command parser
- Initial 3D visualization

---

[Unreleased]: https://github.com/voidO-O/cad-copilot/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/voidO-O/cad-copilot/releases/tag/v2.0.0
[1.0.0]: https://github.com/voidO-O/cad-copilot/releases/tag/v1.0.0
