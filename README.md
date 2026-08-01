# Minecraft Mod Translation

本仓库提供了简易的翻译文件到ParaTranz的集成和自动同步，以便于利用ParaTranz的资源，实现模组翻译或审阅的便利化。

## 项目目标

- 将源文件转换成 JSON 格式，并同步到 ParaTranz 进行翻译。
- 从 ParaTranz 拉取翻译结果并写回本地。
- 将翻译后的 JSON 文件转换为最终可发布的 TXT 格式文件。
- 保持本地项目结构清晰，并为未来继续增加其他翻译项目提供可扩展路径。
- 使用根目录 `sync-config.yml` 控制哪些项目会被同步。

## 当前工作原理

1. 本地源文件存储在：
   - `projects/{mod_namespace_id}/{mod_version}/{...}/en_us/`
   - `projects/{mod_namespace_id}/{mod_version}/{...}/en_us.json`
2. 将本地 `en_us` 文件上传到 ParaTranz：
   - `.github/scripts/github2para.py`
3. 拉取脚本：
   - `.github/scripts/para2github.py`
   - 从 ParaTranz 拉取翻译结果，写入：
    - `projects{mod_namespace_id}/{mod_version}/{...}/zh_cn/`
    - `projects{mod_namespace_id}/{mod_version}/{...}/zh_cn.json`
4. 后续处理。

## 目录结构

- `.github/scripts/`
  - `github2para.py`：上传源文件到 ParaTranz
  - `para2github.py`：从 ParaTranz 拉取翻译结果
  - `paratranz_api.py`：ParaTranz 简易客户端封装
  - `README.md`：脚本使用说明
- `.github/workflows/`
  - `github2para.yml`：上传来源的 CI 工作流
  - `para2github.yml`：拉取并提交翻译结果的 CI 工作流
- `projects/`：本地手册项目文件夹
- `sources/`：原始手册源数据目录
- `src/`：标签处理、后处理
- `tags/`：标签配置文件
- `translation/`：最终翻译文件输出目录

## 本地运行

### 同步配置

根目录 `sync-config.yml` 控制需要同步的项目。配置文件中的每个项目定义：

- `upload_source`：本地上传源路径
- `remote_prefix`：ParaTranz 上的来源路径前缀
- `download_target`：翻译 JSON 的本地保存位置

当前仓库已经提供示例配置：`sync-config.yml`

1. 安装依赖：
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. 配置 ParaTranz 凭证：
   - `PARA_TOKEN`
   - `PARA_PROJECT_ID`

3. 上传英文源文件到 ParaTranz：
   ```bash
   python .github/scripts/github2para.py
   ```

4. 从 ParaTranz 拉取翻译结果：
   ```bash
   python .github/scripts/para2github.py
   ```

5. 后续处理。

## CI 自动化

- `github2para.yml`：会在 `push` 或手动触发时上传源文件。
- `para2github.yml`：会在 `main` 分支 push、定时任务或手动触发时拉取翻译并提交。
- 同步项目由根目录 `sync-config.yml` 控制，配置文件中的项目列表决定哪些上传/拉取会执行。

## 贡献准则

- 使用分支开发，提交前先确保本地脚本和工作流逻辑正常。
- 提交消息请简洁明了，说明本次变更主要目的。
- 不要在仓库中提交明文凭证或私密 `.env` 内容。
- 新增翻译项目时，建议参考现有目录规则。
