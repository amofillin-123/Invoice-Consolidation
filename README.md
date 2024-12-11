# 发票合并程序 Web 版

这是一个简单易用的在线发票合并工具，可以将多个PDF或图片格式的发票文件合并成一个PDF文件，每页放置两张发票，布局整洁美观。用户可以直接在浏览器中使用，无需安装任何软件。

## 功能特点

- 支持多种文件格式：
  - PDF文件
  - 图片文件（PNG、JPG、JPEG、GIF、BMP、TIFF）
- 智能布局：
  - 每页自动放置两张发票
  - 自动保持原始比例
  - 合理的页面边距
- 便捷操作：
  - 现代化的Web界面
  - 支持多选文件
  - 实时处理进度显示
  - 自动下载合并后的文件
- 可靠性：
  - 自动错误处理
  - 详细的日志记录
  - 临时文件自动清理

## 在线使用

访问：[在线发票合并工具](https://[您的GitHub用户名].github.io/invoice-merger/)

## 本地开发

### 系统要求

- Python 3.11 或更高版本
- 必要的依赖包：
  ```bash
  pip install -r requirements.txt
  ```

### 本地运行

1. 克隆仓库：
   ```bash
   git clone https://github.com/[您的GitHub用户名]/invoice-merger.git
   cd invoice-merger
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 运行应用：
   ```bash
   python app.py
   ```

4. 访问：
   在浏览器中打开 http://localhost:1573

## 使用方法

1. 打开网页应用
2. 点击"选择文件"或将文件拖放到上传区域
3. 选择要合并的发票文件（支持多选）
4. 等待处理完成，期间可以查看实时进度
5. 处理完成后会自动下载合并后的PDF文件

## 技术栈

- 后端：Python + Flask
- 前端：HTML + CSS + JavaScript + Bootstrap 5
- 部署：GitHub Pages + GitHub Actions

## 开发相关

- 代码仓库：https://github.com/amofillin-123/Invoice-Consolidation
- 问题反馈：https://github.com/amofillin-123/Invoice-Consolidation/issues
- 开发文档：[docs/](./docs/)

## 贡献指南

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情
