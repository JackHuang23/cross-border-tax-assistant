# Third-Party Notices

本项目使用以下开源库。打包分发（如 PyInstaller 二进制）时，需保留其许可证全文。

## 运行时依赖

| 包 | 许可证 | 说明 |
|---|---|---|
| Flask | BSD-3-Clause | Web 框架 |
| Werkzeug | BSD-3-Clause | Flask 依赖 |
| Jinja2 | BSD-3-Clause | Flask 依赖 |
| MarkupSafe | BSD-3-Clause | Jinja2 依赖 |
| itsdangerous | BSD-3-Clause | Flask 依赖 |
| click | BSD-3-Clause | Flask 依赖 |
| blinker | MIT | Flask 依赖 |
| waitress | ZPL-2.1 | 生产级 WSGI 服务器（可选） |

## 开发/测试依赖

| 包 | 许可证 |
|---|---|
| pytest | MIT |
| pluggy | MIT |
| iniconfig | MIT |
| packaging | Apache-2.0 OR BSD-2-Clause |

以上均为宽松许可证（BSD / MIT / Apache / ZPL），与本项目的 AGPL-3.0 兼容。
（唯一注意：Apache-2.0 只兼容 GPLv3 而非 GPLv2；此处仅作为开发期依赖，且其本身也是 BSD-2-Clause 双许可。）

许可证全文：
- BSD-3-Clause: https://opensource.org/license/bsd-3-clause
- MIT: https://opensource.org/license/mit
- Apache-2.0: https://www.apache.org/licenses/LICENSE-2.0
- ZPL-2.1: https://opensource.org/license/zpl-2-1
