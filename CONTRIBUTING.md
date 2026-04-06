# Contributing to CAD Copilot

感谢你对 CAD Copilot 的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告Bug

1. 在 [Issues](https://github.com/voidO-O/cad-copilot/issues) 页面检查是否已有相同问题
2. 使用 Bug Report 模板创建新 Issue
3. 提供详细的复现步骤和环境信息

### 提交功能建议

1. 在 Issues 页面使用 Feature Request 模板
2. 描述你期望的功能和使用场景

### 提交代码

1. Fork 本仓库
2. 创建特性分支
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. 编写代码并确保：
   - 代码风格与项目一致
   - 添加必要的注释
   - 测试通过
4. 提交更改
   ```bash
   git commit -m "feat: add your feature description"
   ```
5. 推送并创建 Pull Request

## Commit 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

- `feat:` 新功能
- `fix:` Bug修复
- `docs:` 文档更新
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具变更

## 开发环境搭建

```bash
conda create -n cad python=3.10
conda activate cad
conda install -c conda-forge pythonocc-core
pip install -r requirements.txt
```

## 项目结构

- `src/main.py` - GUI入口
- `src/llm_real.py` - AI规划引擎
- `src/controller.py` - 执行控制器
- `src/cad_builder.py` - CAD几何体构建
- `src/tools.py` - 工具注册表
- `src/viewer.py` - 3D可视化
- `src/session_context.py` - 状态管理

## 行为准则

- 尊重所有贡献者
- 保持建设性的讨论
- 专注于技术问题

感谢你的贡献！🎉
