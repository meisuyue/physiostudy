# PhysioStudy

# 总体介绍
`PhysioStudy` 是一个基于 `PyQt6` 构建的生理学学习软件，面向医学与生理学相关词汇、词根词缀、简答题试卷和查词场景做了统一整合。软件目前主要适配 Windows 桌面环境，支持登录注册、学习进度记录、题库测试、语音朗读、查词检索和页面主题插图替换。

项目开源至[GitHub](https://github.com/meisuyue/physiostudy)，可在此获得后续有可能的更新。不过最重要的是
- ~~关注作者喵\~，关注作者谢谢喵\~~~

软件的整体目标不是单纯“背单词”，而是把：

- 单词学习
- 单词复习
- 词根词缀学习
- 试题训练
- 查询辅助

放进一套连续的学习流程里，尽量减少来回切换文件和手动整理资料的成本。

运行入口：

```bash
python physiostudy.py
```

依赖安装：

```bash
pip install -r requirements.txt
```

当前项目核心结构：

```text
physiotudy
├─ physiostudy.py
├─ README.md
├─ requirements.txt
├─ core/
│  ├─ app_config.py
│  ├─ app_window.py
│  ├─ login.py
│  ├─ project_paths.py
│  ├─ storage.py
│  ├─ tts_service.py
│  ├─ dialogs/
│  └─ pages/
├─ data/
│  ├─ dict/
│  ├─ icons/
│  ├─ papers/
│  ├─ quote/
│  ├─ user/
│  ├─ users.json
│  └─ login_memory.json
└─ temp/
   └─ tts/
```

# 菜单栏介绍
软件当前主要分为首页和学习功能面板两个入口区域，不同页面的菜单项略有不同，但核心逻辑一致。

首页常见菜单项：

- `首页`
  - 返回当前首页展示区域
- `设置`
  - 打开学习模式设置窗口
- `帮助`
  - 查看软件基本使用说明
- `联系作者`
  - 查看作者与联系邮箱

学习功能面板左侧侧边栏常见菜单项：

- `首页`
  - 返回软件首页
- `学习`
  - 打开单词学习 / 单词复习选择弹窗
- `练习`
  - 进入试题测试模块
- `复习`
  - 也会进入单词学习 / 单词复习选择弹窗，方便从复习角度切入
- `词根词缀`
  - 进入词根词缀学习
- `查询`
  - 打开查词窗口
- `设置`
  - 打开学习设置
- `帮助`
  - 打开帮助说明
- `关于`
  - 查看作者信息

# 每一个学习模块介绍
## 单词学习
单词学习模块整合了原先的中文词库学习与英文词库学习。点击后会先弹出选择框，提供四种入口：

- `中文学习`
  - 适合看到中文后回忆英文
- `英文学习`
  - 适合看到英文后回忆中文
- `中文复习`
  - 只复习已经标记保存过的中文方向词条
- `英文复习`
  - 只复习已经标记保存过的英文方向词条

主要特点：

- 支持学习页视觉主题背景
- 支持显示答案、上一题、下一题
- 支持标记并保存重点单词
- 支持错误次数统计和彩蛋逻辑
- 英文学中文时支持 TTS 语音朗读
- 按空格可重播当前语音
- 当前单词播放时，会后台预取下一条单词语音

## 词根词缀学习
词根词缀学习使用 `physiostudy\data\dict\roots_affixes.json` 作为数据源。

主要特点：

- 复用单词学习页的交互逻辑
- 可记录已学进度
- 可纳入学习进度统计
- 适合作为单词记忆的结构化补充

## 试题测试
试题测试会自动读取 `physiostudy\data\papers` 下的 `json` 试卷文件。

支持：

- 按文件区分不同试卷
- `所有试题随机抽取`
- 试题隐藏 / 显示
- 答案显示
- 中文解析显示
- 上一题 / 下一题切换
- 更换试卷
- 试题语音播放
- 空格重播当前题目语音

语音相关逻辑：

- 语音文件缓存到 `physiostudy\temp\tts`
- 优先使用 `edge-tts`，因此语音需联网使用
- 失败时回退到 `pyttsx3`
- 加载试卷时会先进入缓冲动画页

## 查询单词与释义
查询模块用于快速查找词条和释义，适合学习中临时卡住时使用。

支持：

- 自定义查询内容
- 自定义匹配阈值
- 回车直接查询
- 结果按匹配度排序展示
- 无结果时显示提示语与 `thinking.gif`

## 首页与学习功能面板
首页用于进入主流程，学习功能面板则把学习、练习、复习、词根、查询等内容汇总到一个界面中。

学习功能面板当前还会显示：

- 今日学习时间
- 三类学习进度
- 当前日期时间
- 日历视图

# 插图替换
软件大多数页面都已经支持“直接替换图片资源”的方式做主题更新。常见插图都位于：

```text
physiostudy\data\icons\default
```

以及：

```text
physiostudy\data\icons\items
```

常见替换方式如下：

- 首页背景
  - 替换 `home_page_bg.png`
- 学习功能面板背景
  - 替换 `study_hub.png`
- 单词学习背景
  - 替换 `word_page.png`
- 试题加载页背景
  - 替换 `loading_page.png`
- 联系作者弹窗图标
  - 替换 `contact.png`
- 查询无结果动图
  - 替换 `thinking.gif`
- 试题加载动画角色
  - 替换 `move.gif`
- 单词学习页按钮小图标
  - 如 `save.png`、`eye.png`、`write.png`
- 试题页图标
  - 如 `play.png`、`file.png`
- 学习功能面板功能卡图标
  - 从 `physiostudy\data\icons\items` 中随机读取

替换建议：

- 文件名尽量保持不变
- 分辨率可以调整，但尽量维持原有横纵比
- `png` 适合静态按钮与背景
- `gif` 适合反馈动画和提示动画

# 进度复原
软件的大多数学习进度都保存在：

```text
physiostudy\data\user\<用户名>\
```

不同模块的记录位置如下：

- 中文词库已学记录
  - `physiostudy\data\user\<用户名>\c_key\past\words.json`
- 中文词库重点标记
  - `physiostudy\data\user\<用户名>\c_key\important\words.json`
- 英文词库已学记录
  - `physiostudy\data\user\<用户名>\e_key\past\words.json`
- 英文词库重点标记
  - `physiostudy\data\user\<用户名>\e_key\important\words.json`
- 词根词缀已学记录
  - `physiostudy\data\user\<用户名>\roots_affixes\past\words.json`
- 词根词缀重点标记
  - `physiostudy\data\user\<用户名>\roots_affixes\important\words.json`
- 今日使用时长累计
  - `physiostudy\data\user\<用户名>\usage_stats.json`

如果需要复原进度，有两种常见方式：

- 保留原用户目录
  - 直接继续使用原来的用户名登录
- 备份后恢复
  - 将原来的用户文件夹复制回 `data/user` 下对应用户名目录

如果想“清空进度重新开始”，可以删除对应用户目录下的这些记录文件，但建议先备份。

# 其他说明
## 登录记忆
勾选“记住密码”后，软件会把信息保存到：

```text
physiostudy\data\login_memory.json
```

## 题库位置
当前试卷统一存放在：

```text
physiostudy\data\papers
```

## 名言位置
首页随机名言来自：

```text
physiostudy\data\quote\medical_quotes.json
```

## 注意事项
- 本项目当前主要按 Windows 桌面环境设计
- 如果替换大量资源图片，建议运行前先备份原文件
- 如果打包后出现资源缺失，优先检查 `data` 目录是否完整被带入
