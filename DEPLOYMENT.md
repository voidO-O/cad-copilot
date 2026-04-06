# 🚀 部署和发布指南

本文档提供完整的Git提交、版本管理和GitHub发布流程。

## 📦 初始化Git仓库

如果还没有初始化Git仓库：

```bash
cd d:\demo\cad-copilot
git init
git add .
git commit -m "Initial commit: CAD Copilot v2.0"
```

## 🔗 关联远程仓库

```bash
git remote add origin git@github.com:voidO-O/cad-copilot.git
git branch -M main
git push -u origin main
```

## 📝 日常开发流程

### 1. 创建功能分支

```bash
git checkout -b feature/your-feature-name
```

### 2. 提交代码

```bash
git add .
git commit -m "feat: add your feature description"
```

### 3. 推送并创建PR

```bash
git push origin feature/your-feature-name
# 然后在GitHub上创建Pull Request
```

## 🏷️ 版本发布流程

### 1. 更新版本号

在发布前，确保更新以下文件中的版本号：
- `src/main.py` (窗口标题)
- `README.md` 和 `README_CN.md`

### 2. 创建版本标签

```bash
# 查看当前标签
git tag

# 创建新版本标签
git tag -a v2.0.0 -m "Release v2.0.0: Professional Edition"

# 推送标签到远程
git push origin v2.0.0

# 或推送所有标签
git push origin --tags
```

### 3. 在GitHub创建Release

1. 访问 `https://github.com/voidO-O/cad-copilot/releases`
2. 点击 "Draft a new release"
3. 选择刚创建的标签 (v2.0.0)
4. 填写Release信息：

**Release Title**: `v2.0.0 - Professional Edition`

**Release Notes 模板**:
```markdown
## 🎉 新特性

- ✨ AI驱动的自然语言建模
- 🎨 实时3D可视化
- 🔧 完整的布尔运算支持
- 📦 STL导出功能

## 🐛 Bug修复

- 修复了ID映射的边界情况
- 改进了错误处理机制

## 📚 文档

- 添加了完整的中英文README
- 提供了详细的安装指南

## 🙏 致谢

感谢所有贡献者！

---

**完整更新日志**: https://github.com/voidO-O/cad-copilot/compare/v1.0.0...v2.0.0
```

5. 上传Demo视频/GIF（如果有）
6. 点击 "Publish release"

## 📹 Demo录制建议

### 录制工具
- **Windows**: OBS Studio / ScreenToGif
- **分辨率**: 1920x1080 或 1280x720
- **帧率**: 30fps

### 录制脚本

**场景1: 基础建模** (30秒)
```
1. 启动应用
2. 输入: "创建一个半径为10的球体"
3. 输入: "在右边创建一个圆柱，半径5，高度20"
4. 展示3D视图旋转
```

**场景2: 布尔运算** (30秒)
```
1. 输入: "合并球体和圆柱"
2. 输入: "在顶部创建一个小球体并减去它"
3. 展示最终效果
```

**场景3: 复杂建模** (60秒)
```
1. 输入: "创建一个轴承座，底座是圆柱，顶部有安装孔"
2. 展示AI的分步规划过程
3. 展示最终模型
```

**场景4: 导出** (15秒)
```
1. 输入: "导出为STL文件"
2. 打开exports文件夹展示导出的文件
```

### 后期处理
- 使用FFmpeg压缩视频
- 创建GIF预览（前10秒）用于README

```bash
# 视频转GIF
ffmpeg -i demo.mp4 -vf "fps=15,scale=800:-1" -t 10 demo.gif
```

## 🌟 推广建议

### 1. 社交媒体
- Reddit: r/Python, r/3Dprinting, r/CAD
- Twitter/X: 使用标签 #Python #CAD #AI
- HackerNews: Show HN

### 2. 技术社区
- 提交到 Awesome Lists
- 在相关论坛分享
- 写技术博客介绍

### 3. 持续维护
- 及时回复Issues
- 定期更新文档
- 收集用户反馈

## 🔄 版本号规范

使用语义化版本 (Semantic Versioning):

- **主版本号** (Major): 不兼容的API修改
- **次版本号** (Minor): 向下兼容的功能新增
- **修订号** (Patch): 向下兼容的问题修正

示例:
- `v2.0.0` - 重大更新
- `v2.1.0` - 新增功能
- `v2.1.1` - Bug修复

## ✅ 发布前检查清单

- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] 版本号已更新
- [ ] CHANGELOG已更新
- [ ] API密钥已移除（使用.env）
- [ ] Demo视频已录制
- [ ] README截图已更新
- [ ] 依赖版本已锁定

## 🆘 常见问题

**Q: 如何撤销已推送的标签？**
```bash
git tag -d v2.0.0
git push origin :refs/tags/v2.0.0
```

**Q: 如何修改最后一次提交？**
```bash
git commit --amend -m "new message"
git push --force
```

**Q: 如何查看两个版本之间的差异？**
```bash
git diff v1.0.0..v2.0.0
```

---

祝发布顺利！🎉
