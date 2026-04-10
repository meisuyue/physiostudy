# PhysioWords

一个基于 PyQt6 的生理学英文单词学习软件，支持登录注册、按词库顺序学习、标记重要单词、按用户学习进度跳过已学词、阅览自动播放模式。

## 功能

- 登录/注册窗口（自定义无边框，点击 `×` 下移淡化退出）
- 首页入口：
- `中文开始学习`
- `英文开始学习`
- `复习标记单词`
- `设置`（默写模式 / 阅览模式）
- 学习页：
- 按词库顺序显示 `key`
- 点击 `显示答案` 展示 `meaning / abbrev / page`
- `前一个单词 / 下一个单词`
- `保存该单词`（标记到 important）
- `返回首页`
- 反馈动效：
- `答对了` 播放 `right.gif`
- `没答对` 播放 `wrong.gif`
- 错误累计到 5 次播放 `lose.gif`，并清零
- 用户学习记录：
- 维护 `past`（已学习）和 `important`（已标记）
- 普通学习自动跳过 `past` 中单词
- 复习入口只学习 `important` 中单词

## 环境要求

- Python 3.10+
- Windows（当前项目按 Windows 路径组织）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```
或者
双击 physioword.exe

## 目录结构

```text
physiowords/
├─ main.py
├─ login.py
├─ app_window.py
├─ app_config.py
├─ storage.py
├─ requirements.txt
├─ README.md
├─ pages/
│  ├─ welcome_page.py
│  └─ study_page.py
└─ data/
   ├─ dict/
   │  ├─ c_key.json
   │  └─ e_key.json
   ├─ icons/
   │  ├─ default/
   │  └─ TandF/
   ├─ users.json
   └─ user/
      └─ <用户名>/
         ├─ c_key/
         │  ├─ past/words.json
         │  └─ important/words.json
         └─ e_key/
            ├─ past/words.json
            └─ important/words.json
```

## 学习数据规则

- `past/words.json`：记录已学习词条的 `key`
- `important/words.json`：记录手动保存的重要词条 `key`
- 普通学习会读取完整词库并过滤 `past`
- “复习标记单词”会读取完整词库并过滤 `important`


