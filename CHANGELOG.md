# Changelog

本文件记录项目的所有重要变更。
格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### 计划中
- 层级拖拽排序
- 结果导出 Excel 报告
- 深色主题切换

---

## [2.0.0] - 2024-XX-XX

### Added
- ✨ 支持任意多列组合生成多级目录
- ✨ 每层可绑定独立数量列，自动展开子目录
- ✨ 中间层自动合并（同父目录只建一次）
- ✨ 空值层自动跳过
- ✨ 配置保存到 `config.json`，启动自动恢复
- ✨ 层级配置可视化控件 `LevelEditor`
- ✨ 示例数据生成脚本 `scripts/generate_sample.py`
- ✨ GitHub Actions 多平台自动打包

### Changed
- ♻️ 重构数据模型：`LevelConfig` / `FolderTask` / `AppConfig`
- ♻️ 重构展开逻辑：一行 → 多条路径 → 合并成树

### Fixed
- 🐛 修复旧版单层/双层逻辑的局限

---

## [1.0.0] - 2024-XX-XX

### Added
- 基础版：单列命名 + 数量展开（主 + 子两级）