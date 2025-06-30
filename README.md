# RPA
此项目是使用工作室标准RPA模板创建的。

## 项目描述

(这里填写关于此RPA机器人功能的简要描述，例如：该机器人用于每日自动从财务系统下载报表，并进行初步处理。)

## 环境设置

本项目使用 [Poetry](https://python-poetry.org/) 进行依赖管理。

1.  **安装Poetry:**
    请参照官方文档进行安装。

2.  **安装项目依赖:**
    在项目根目录运行以下命令，Poetry会自动创建虚拟环境并安装所有必需的库。
    ```bash
    poetry install
    ```

3.  **配置环境变量:**
    将 `.env.example` 文件复制一份并重命名为 `.env`，然后根据实际情况填写其中的配置项（如用户名、密码等）。
    ```bash
    cp .env.example .env
    ```

## 如何运行

1.  激活Poetry管理的虚拟环境：
    ```bash
    poetry shell
    ```

2.  运行主程序：
    ```bash
    python main.py
    ```

## 项目结构说明

(此处可以链接到工作室的完整SOP文档)