# cross-border-tax-assistant · 跨境个人税务助理

面向「跨境个人」的开源税务测算工具：**中美税务居民身份判定 + 税负测算 + 申报义务提示**。浏览器打开即用，默认中文、可切换英文。

> ⚠️ **免责声明**：本工具仅供教学与参考，输出不构成税务、法律或财务意见。

## ✨ 功能

- **中国税务居民身份**：有住所 / 无住所满 183 天 / 6 年规则（30 天重置）/ 90 天规则
- **美国税务身份**：公民/绿卡 / 实质停留测试（31 天 + 加权 183 天）/ 5 类豁免身份
- **双重居民**：中美协定第 4 条第 2 款 —— 主管当局协商（MAP），非机械 tie-breaker
- **逐笔持仓/交易**：股息 + 买卖 + 未卖出选项，持有期自动联动税率（A 股 3 档 / 美股合格与否）
- **税负测算**：中国综合所得、A 股股息差别化、A 股转让暂免、美国普通税、合格/非合格股息、资本利得长短期、SE 税、特许权使用费/稿酬
- **专项扣除逐项**：三险一金 + 7 项专项附加扣除（含住房租金按城市分档）
- **跨境劳务/版税**：协定第 13 条 / 第 11 条
- **境外税收抵免** + **申报义务与表格**（W-8BEN / W-9 / 1040 / 1040-NR 等）
- **法条引用** + 内置《法条依据》全文（离线可看）

## 🚀 快速开始

### 方式一：在线版（零安装）

访问已部署的网址即可（见下方「部署」）。

### 方式二：Docker

```bash
docker build -t cross-border-tax-assistant .
docker run -p 5000:5000 cross-border-tax-assistant
# 打开 http://localhost:5000
```

### 方式三：源码

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python app.py        # 打开 http://localhost:5000
```

- Windows：双击 `run.bat`
- Linux / macOS：`./run.sh`

## 🧪 测试

```bash
./venv/bin/pip install -r requirements-dev.txt
./venv/bin/python -m pytest tests/ -v   # 36 例
```

## ☁️ 部署

- **Azure App Service**（Linux + Python 运行时）：启动命令 `python app.py`（自动读取 `PORT` 环境变量）。
- **Render**：仓库根已提供 `render.yaml`，点「New → Blueprint」一键部署。

## 📜 许可

本项目采用 **AGPL-3.0 + FLOSS 兼容性例外**（§7 额外许可）：

- 默认按 **AGPL-3.0**（见 `LICENSE`）。
- 与 GPL-2.0-only / EPL / CDDL 项目组合时，按 `LICENSE.EXCEPTION` 中的例外条款处理。
- 需要其它许可（更宽松或商业），请提 issue 逐案处理。
- 文档（`docs/`、README）按 **CC-BY-4.0** 授权。

## 📚 法条来源

完整引用与原文见 **`docs/法条依据.html`**（内置，App 内「法规原文链接」可直达）与 `docs/法条依据.pdf`。

> 一手 = 政府/官方；二级 = PwC/KPMG 仅用于交叉核对。

## 🙏 第三方

依赖均为宽松许可证（Flask 为 BSD-3-Clause、pytest 为 MIT 等），详见 **`THIRD-PARTY-NOTICES.md`**。

## 📁 目录结构

```
app.py             # Flask 应用 + /api/calculate JSON API（生产：waitress + PORT）
tax_engine/        # 纯 Python 税务引擎（身份/税负/跨境/申报，零第三方依赖）
templates/ static/ # 单页 UI（中英双语）
tests/             # pytest 单元测试（36 例）
docs/              # 法条依据全文（HTML/PDF）+ 一手法律原文
```

## ⚖️ 免责声明

本工具为财税教学演示原型，输出仅供参考，不构成税务意见；与德勤无关联。
