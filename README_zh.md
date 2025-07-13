# CS2 物品模式

[English](README.md) | 中文

[![license](https://img.shields.io/github/license/somespecialone/cs2-items-schema)](https://github.com/somespecialone/cs2-items-schema/blob/master/LICENSE)
[![Schema](https://github.com/somespecialone/cs2-items-schema/actions/workflows/schema.yml/badge.svg)](https://github.com/somespecialone/cs2-items-schema/actions/workflows/schema.yml)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![steam](https://shields.io/badge/steam-1b2838?logo=steam)](https://store.steampowered.com/)

这是一个 `CS2`（前身为 `CSGO`）物品模式的存储仓库，致力于创建更易理解的 `CS2` 物品格式及其关系。

## 改进功能 🚀

本项目包含以下增强功能：

- **中文名称支持**: 为 CS2 物品添加了中文名称输出，为中文用户提供更好的可访问性
- **格式修复**: 优化了数据格式和结构，提高了可读性和一致性
- **本地文件支持**: 添加了 CS2 游戏文件的自动下载功能，支持多种数据源选项

> 如果需要的话，欢迎使用 😊

> [!IMPORTANT]
> 📦 仅包含从游戏文件中提取的数据。
> **不包含所有物品**

> [!TIP]
> 如果您正在寻找 [Steam 市场](https://steamcommunity.com/market/) 物品的 `itemnameid`，
> 请查看此仓库 [somespecialone/steam-item-name-ids](https://github.com/somespecialone/steam-item-name-ids)

> [!NOTE]
> 此仓库配置为使用 GitHub Actions `Schema` 工作流自动更新。
> 您可以在[这里](.github/workflows/schema.yml)详细了解

## 完整性模式 🧾

反映 `json` 模式和实体之间的关系

![integrity](integrity.png)

## 图表 📅

SQL 数据库图表

![diagram](diagram.png)

## 使用方法 🚀

### 基本用法（远程文件）

使用远程数据源运行模式收集器（默认行为）：

```bash
# 基本远程模式（不保存原始文件）
python collect.py

# 远程模式并缓存原始文件
python collect.py --save-raw
```

### 本地文件模式

#### 选项 1: 生成演示文件

创建用于测试和开发的示例文件：

```bash
# 生成演示文件并用于模式收集
python collect.py --download-demo --local
```

#### 选项 2: 使用现有本地文件

如果您已经在本地目录中有 CS2 游戏文件：

```bash
# 使用 ./static 目录中的现有文件（默认）
python collect.py --local

# 使用自定义目录中的文件
python collect.py --local --local-dir /path/to/your/files
```

#### 选项 3: Steam 登录下载（高级）

使用您的 Steam 账户直接从 Steam CDN 下载文件：

```bash
# Steam 登录（将安全地提示输入密码）
python collect.py --steam-login your_username --local

# 使用 2FA 验证码
python collect.py --steam-login your_username --steam-2fa 12345 --local
```

### 命令行选项

| 选项 | 描述 |
|--------|-------------|
| `--local` | 使用本地文件而不是远程 URL |
| `--local-dir PATH` | 包含本地游戏文件的目录（默认：`static`） |
| `--download-demo` | 生成用于测试的演示文件 |
| `--steam-login USERNAME` | 使用 Steam 登录下载（安全地提示输入密码） |
| `--steam-2fa CODE` | Steam 2FA 验证码（与 `--steam-login` 一起使用） |
| `--save-raw` | 在使用远程模式时将原始游戏文件保存到 static/ 目录 |

### Steam 登录要求

要使用 Steam 登录功能，请安装额外依赖：

```bash
pip install steam
```

### 文件结构

本地文件应按如下方式组织：

```
static/
├── items_game.txt      # 主要物品定义文件
├── csgo_english.txt    # 英文本地化
├── csgo_schinese.txt   # 中文本地化
├── items_game_cdn.txt  # CDN 信息
└── manifestId.txt      # 版本跟踪
```

## 待办事项

- [x] 贴纸胶囊
- [x] 纪念品包装
- [x] 物品套装
- [x] ~~涂鸦色调~~
- [x] SQL 脚本和模式
- [x] 本地文件支持和自动下载

## 致谢

* [csfloat/cs-files](https://github.com/csfloat/cs-files)
* [draw.io](https://draw.io)
* [dbdiagram.io](https://dbdiagram.io/)