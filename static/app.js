let currentLang = "zh"; // 默认中文，不读浏览器语言，避免探测 bug

function t(key) {
  return (window.I18N[currentLang] && window.I18N[currentLang][key]) || window.I18N.zh[key] || key;
}

function tr(zh, en) {
  return currentLang === "zh" ? zh : (en || zh);
}

function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.getAttribute("data-i18n"));
  });
  document.getElementById("lang-toggle").textContent = currentLang === "zh" ? "EN" : "中文";
}

document.getElementById("lang-toggle").addEventListener("click", () => {
  currentLang = currentLang === "zh" ? "en" : "zh";
  applyI18n();
  renderLegalLinks();
  if (lastData) render(lastData);
});

function num(id) {
  const v = parseFloat(document.getElementById(id).value);
  return isNaN(v) ? 0 : v;
}
function chk(id) {
  return document.getElementById(id).checked;
}
function val(id) {
  return document.getElementById(id).value;
}
function fmt(n) {
  return (n === null || n === undefined) ? "—" : Number(n).toLocaleString("en-US", { maximumFractionDigits: 2 });
}

// ===== 法规原文链接（官方来源） =====
const LEGAL_SOURCES = [
  { zh: "📄 本工具内置《法条依据》全文（离线可看，含全部法条原文与引用）", en: "📄 Built-in full legal basis (offline; all statutes & citations)", url: "/legal-basis" },
  { zh: "《中华人民共和国个人所得税法》（2018 修正）", en: "PRC Individual Income Tax Law (2018)", url: "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html" },
  { zh: "《个人所得税法实施条例》（国务院令第 707 号）", en: "IIT Law Implementing Regulations (Decree 707)", url: "https://www.chinatax.gov.cn/chinatax/n810219/n810744/n3752930/n3752974/c3963364/content.html" },
  { zh: "财政部 税务总局公告 2019 年第 34 号（居住天数判定）", en: "MOF/STA Announcement No.34 of 2019 (day counting)", url: "https://www.chinatax.gov.cn/chinatax/n810219/n810744/n3752930/n3752974/c4151944/content.html" },
  { zh: "中美税收协定（IRS 官方文本 PDF）", en: "U.S.–China tax treaty (IRS official text)", url: "https://www.irs.gov/pub/irs-trty/china.pdf" },
  { zh: "IRS 实质停留测试", en: "IRS Substantial Presence Test", url: "https://www.irs.gov/individuals/international-taxpayers/substantial-presence-test" },
  { zh: "IRS Pub 519（在美外国人税务指南）", en: "IRS Pub 519 (US Tax Guide for Aliens)", url: "https://www.irs.gov/publications/p519" },
  { zh: "IRS Pub 550（投资所得与费用）", en: "IRS Pub 550 (Investment Income & Expenses)", url: "https://www.irs.gov/publications/p550" },
  { zh: "IRS 2026 年度通胀调整（含 OBBB 修订）", en: "IRS 2026 inflation adjustments (incl. OBBB)", url: "https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill" },
  { zh: "IRS Topic 751（自雇税）", en: "IRS Topic 751 (Self-Employment Tax)", url: "https://www.irs.gov/taxtopics/tc751" },
  { zh: "IRS Schedule SE（自雇税表）", en: "IRS Schedule SE (Form 1040)", url: "https://www.irs.gov/pub/irs-pdf/f1040sse.pdf" },
  { zh: "国家税务总局税收法规库（检索 财税〔2015〕101号、财税字〔1998〕61号 等）", en: "STA tax law database (search 财税〔2015〕101号, 财税字〔1998〕61号, etc.)", url: "https://fgk.chinatax.gov.cn/" },
];

function renderLegalLinks() {
  const el = document.getElementById("legal-links-list");
  if (!el) return;
  el.innerHTML = LEGAL_SOURCES.map(s =>
    '<li><a href="' + s.url + '" target="_blank" rel="noopener">' + (currentLang === "zh" ? s.zh : s.en) + "</a></li>"
  ).join("");
}

// ===== 持仓/交易（统一：股息 + 买卖，未卖出不计资本利得） =====
function r2(n) { return Math.round(n * 100) / 100; }

function addHoldRow() {
  const tbody = document.getElementById("hold-rows");
  const tr = document.createElement("tr");
  tr.innerHTML =
    '<td><select class="hold-type"><option value="a_share">A股</option><option value="us">美股</option></select></td>' +
    '<td><input type="text" class="hold-ticker" placeholder="ICBC"></td>' +
    '<td><input type="date" class="hold-buy-date"></td>' +
    '<td><input type="number" class="hold-buy-price" min="0" step="0.01" value="0"></td>' +
    '<td><input type="number" class="hold-qty" min="0" step="0.01" value="0"></td>' +
    '<td><select class="hold-status"><option value="not_sold">未卖出</option><option value="sold">已卖出</option></select></td>' +
    '<td><input type="date" class="hold-sell-date" disabled></td>' +
    '<td><input type="number" class="hold-sell-price" min="0" step="0.01" value="0" disabled></td>' +
    '<td><input type="number" class="hold-dividend" min="0" step="0.01" value="0"></td>' +
    '<td><button type="button" class="rm-btn">×</button></td>';
  tbody.appendChild(tr);
  tr.querySelector(".rm-btn").addEventListener("click", () => tr.remove());
  tr.querySelector(".hold-status").addEventListener("change", (e) => {
    const sold = e.target.value === "sold";
    tr.querySelector(".hold-sell-date").disabled = !sold;
    tr.querySelector(".hold-sell-price").disabled = !sold;
  });
}
document.getElementById("hold-add").addEventListener("click", addHoldRow);
addHoldRow();

function computeHoldings() {
  const today = new Date();
  let divCn = 0, divUs = 0, cgCn = 0, st = 0, lt = 0;
  const cn = { lte1m: 0, m1_12m: 0, gt1y: 0 };
  let qualified = 0, nonqualified = 0;
  document.querySelectorAll("#hold-rows tr").forEach(tr => {
    const type = tr.querySelector(".hold-type").value;
    const bd = tr.querySelector(".hold-buy-date").value;
    const bp = parseFloat(tr.querySelector(".hold-buy-price").value);
    const q = parseFloat(tr.querySelector(".hold-qty").value);
    const status = tr.querySelector(".hold-status").value;
    const sd = tr.querySelector(".hold-sell-date").value;
    const sp = parseFloat(tr.querySelector(".hold-sell-price").value);
    const div = parseFloat(tr.querySelector(".hold-dividend").value) || 0;
    const start = bd ? new Date(bd) : null;
    const end = (status === "sold" && sd) ? new Date(sd) : today;
    const days = start ? Math.max(0, (end - start) / 86400000) : 0;
    const months = days / 30.44;

    // 已收股息：按类型汇总 + 按持有期分桶（A股 3 档；美股合格/非合格）
    if (div > 0) {
      if (type === "a_share") {
        divCn += div;
        if (months <= 1) cn.lte1m += div;
        else if (months <= 12) cn.m1_12m += div;
        else cn.gt1y += div;
      } else {
        divUs += div;
      }
      if (days > 60) qualified += div; else nonqualified += div;
    }

    // 资本利得：仅「已卖出」且信息完整时实现；A股暂免仅展示
    if (status === "sold" && start && !isNaN(bp) && !isNaN(sp) && !isNaN(q)) {
      const gain = (sp - bp) * q;
      if (type === "a_share") cgCn += gain;
      else if (days <= 365) st += gain; else lt += gain;
    }
  });
  return {
    div_cn: r2(divCn), div_us: r2(divUs), cg_cn: r2(cgCn),
    div_cn_lte_1m: r2(cn.lte1m), div_cn_1m_12m: r2(cn.m1_12m), div_cn_gt_1y: r2(cn.gt1y),
    div_qualified: r2(qualified), div_nonqualified: r2(nonqualified),
    st_gain: r2(st), lt_gain: r2(lt),
    has_data: (divCn + divUs + cgCn + st + lt) > 0,
  };
}

// ===== 停留日历 =====
function addTripRow(containerId) {
  const div = document.getElementById(containerId);
  const row = document.createElement("div");
  row.className = "trip-row";
  row.innerHTML = '<input type="date" class="trip-start"> → <input type="date" class="trip-end"> ' +
    '<button type="button" class="rm-btn">×</button>';
  div.appendChild(row);
  row.querySelector(".rm-btn").addEventListener("click", () => row.remove());
}
document.getElementById("cn-trip-add").addEventListener("click", () => addTripRow("cn-trip-rows"));
document.getElementById("us-trip-add").addEventListener("click", () => addTripRow("us-trip-rows"));

function computeTrips(containerId, isUs) {
  let days = 0;
  document.querySelectorAll("#" + containerId + " .trip-row").forEach(row => {
    const s = row.querySelector(".trip-start").value;
    const e = row.querySelector(".trip-end").value;
    if (!s || !e) return;
    const diff = (new Date(e) - new Date(s)) / 86400000;
    days += isUs ? (diff + 1) : diff;
  });
  return Math.max(0, Math.round(days));
}

// ===== 豁免身份（可多种） =====
const EXEMPT_TYPES = [
  { v: "diplomat", zh: "外交官/政府相关（A/G 签证）", en: "Diplomat / government-related (A/G visa)" },
  { v: "teacher", zh: "教师/实习生（J/Q 签证）", en: "Teacher/trainee (J/Q visa)" },
  { v: "student", zh: "学生（F/J/M/Q 签证）", en: "Student (F/J/M/Q visa)" },
  { v: "athlete", zh: "职业运动员（慈善赛事）", en: "Professional athlete (charity event)" },
];

function exemptOptions() {
  return EXEMPT_TYPES.map(t => '<option value="' + t.v + '">' + (currentLang === "zh" ? t.zh : t.en) + "</option>").join("");
}

function addExemptRow() {
  const div = document.getElementById("exempt-rows");
  const row = document.createElement("div");
  row.className = "trip-row";
  row.innerHTML = '<select class="exempt-type">' + exemptOptions() + "</select>" +
    '<input type="number" class="exempt-days" min="0" value="0"> ' + tr("天", "days") +
    '<button type="button" class="rm-btn">×</button>';
  div.appendChild(row);
  row.querySelector(".rm-btn").addEventListener("click", () => { row.remove(); updateExemptTotal(); });
  row.querySelector(".exempt-days").addEventListener("input", updateExemptTotal);
}

function updateExemptTotal() {
  let total = 0;
  document.querySelectorAll("#exempt-rows .exempt-days").forEach(el => { total += parseFloat(el.value) || 0; });
  document.getElementById("us_ex_exempt").value = total;
}
document.getElementById("exempt-add").addEventListener("click", addExemptRow);

function collectExemptTypes() {
  const types = [];
  document.querySelectorAll("#exempt-rows .exempt-type").forEach(el => { if (!types.includes(el.value)) types.push(el.value); });
  return types.join(",");
}

// （逐笔股息已合并进「持仓/交易」表）

// ===== 中国专项扣除（三险一金 + 7 项专项附加扣除） =====
function computeDeductions() {
  const sp = num("sp_pension") + num("sp_medical") + num("sp_unemployment") + num("sp_housing");
  let sa = 0;
  if (chk("ad_child")) sa += 2000 * 12 * Math.max(1, num("ad_child_cnt"));
  if (chk("ad_continue")) sa += 400 * 12;
  if (chk("ad_illness")) sa += Math.min(num("ad_illness_amt"), 80000);
  if (chk("ad_loan")) sa += 1000 * 12;
  if (chk("ad_rent")) sa += num("ad_rent_city") * 12;
  if (chk("ad_elderly")) sa += 3000 * 12;
  if (chk("ad_infant")) sa += 2000 * 12 * Math.max(1, num("ad_infant_cnt"));
  return { sp: Math.round(sp * 100) / 100, sa: Math.round(sa * 100) / 100 };
}

let lastData = null;

function buildPayload() {
  const h = computeHoldings();
  const cnTripDays = computeTrips("cn-trip-rows", false);
  const usTripDays = computeTrips("us-trip-rows", true);
  const ded = computeDeductions();
  const cnDiv = h.has_data ? h.div_cn : num("div_cn");
  const usDiv = h.has_data ? h.div_us : num("div_us");
  const cgCn = h.has_data ? h.cg_cn : num("cg_cn");
  document.getElementById("hold-summary").textContent =
    (currentLang === "zh" ? "A股股息 " : "A-share div ") + cnDiv + " / " +
    (currentLang === "zh" ? "美股股息 " : "U.S. div ") + usDiv + " · " +
    (currentLang === "zh" ? "短期利得 $" : "short-term $") + h.st_gain + " / " +
    (currentLang === "zh" ? "长期利得 $" : "long-term $") + h.lt_gain;

  return {
    china: {
      has_domicile: chk("china_has_domicile"),
      full_24h_days: cnTripDays > 0 ? cnTripDays : num("china_full24"),
      consecutive_qualifying_years: num("china_consec"),
    },
    us: {
      is_citizen_or_gc: chk("us_gc"),
      gross_days_current: usTripDays > 0 ? usTripDays : num("us_cur"),
      gross_days_prev1: num("us_p1"),
      gross_days_prev2: num("us_p2"),
      exempt_type: collectExemptTypes(),
      exclusions: {
        commuter: num("us_ex_commuter"),
        transit_under_24h: num("us_ex_transit"),
        crew: num("us_ex_crew"),
        medical: num("us_ex_medical"),
        exempt: num("us_ex_exempt"),
      },
    },
    tiebreak: {
    },
    income: {
      dividend_cn: cnDiv,
      dividend_us: usDiv,
      div_cn_lte_1m: h.div_cn_lte_1m,
      div_cn_1m_12m: h.div_cn_1m_12m,
      div_cn_gt_1y: h.div_cn_gt_1y,
      div_qualified: h.div_qualified,
      div_nonqualified: h.div_nonqualified,
      cg_cn: cgCn,
      cg_us: num("cg_us"),
      st_gain: h.st_gain,
      lt_gain: h.lt_gain,
      salary_cn: num("sal_cn"),
      salary_us: num("sal_us"),
      service_cn: num("svc_cn"),
      service_us: num("svc_us"),
      royalty_cn: num("roy_cn"),
      royalty_us: num("roy_us"),
      cn_holding_months: num("cn_holding"),
      us_holding_days: num("us_holding"),
      us_taxable_income: num("us_taxable"),
      us_has_fixed_base: chk("us_has_fixed_base"),
      us_royalty_connected: chk("us_royalty_connected"),
      special_deduction: ded.sp,
      special_additional: ded.sa,
      fx_rate: num("fx_rate"),
    },
  };
}

function row(label, value, cite) {
  return "<tr><td>" + label + (cite ? '<div class="cite">' + cite + "</div>" : "") + "</td><td class='num'>" + value + "</td></tr>";
}

function render(data) {
  const r = document.getElementById("results");
  let html = '<div class="result-card"><h2>' + t("res_title") + "</h2>";

  const cn = data.china;
  html += "<p><strong>" + t("cn_label") + "：</strong><span class='badge " +
    (cn.is_resident ? "resident" : "nonresident") + "'>" +
    (cn.is_resident ? t("cn_resident") : t("cn_nonresident")) + "</span></p>";
  html += '<p class="reason">' + tr(cn.reason, cn.reason_en) + "</p>";
  if (cn.six_year_rule_triggered) html += '<p class="note">' + t("six_year") + "</p>";
  if (cn.ninety_day_exemption) html += '<p class="note">' + t("ninety_day") + "</p>";

  const us = data.us;
  html += "<p><strong>" + t("us_label") + "：</strong><span class='badge " +
    (us.is_resident ? "resident" : "nonresident") + "'>" +
    (us.is_resident ? t("us_resident") : t("us_nra")) + "</span></p>";
  html += '<p class="reason">' + tr(us.reason, us.reason_en) + "</p>";
  html += '<p class="note">' + t("countable") + "：" +
    us.countable_days.current + " / " + us.countable_days.prev1 + " / " + us.countable_days.prev2 + "</p>";

  if (data.tiebreak) {
    html += "<p><strong>" + t("tie_winner") + "：</strong>" + tr(data.tiebreak.reason, data.tiebreak.reason_en) + "</p>";
    html += '<p class="cite">' + t("citations") + "：" + data.tiebreak.citation + "</p>";
  }

  html += '<p class="cite">' + t("citations") + "：" +
    cn.citations.join("、") + "；" + us.citations.join("、") + "</p></div>";

  const tax = data.tax;

  // 中国税负
  html += '<div class="result-card"><h2>' + t("cn_tax_title") + '</h2><table>';
  html += row(t("cn_comp_tax"), fmt(tax.china.comprehensive_tax) + " " + t("yuan"), tax.china.comprehensive_cite);
  html += row(t("cn_div_tax"), fmt(tax.china.dividend_tax) + " " + t("yuan"), tax.china.dividend_cite);
  html += row(t("cn_cg_tax"), fmt(tax.china.capital_gain_tax) + " " + t("yuan"), tax.china.capital_gain_cite);
  html += row(t("total_tax"), fmt(tax.china.total_tax) + " " + t("yuan"));
  html += "</table></div>";

  // 美国税负
  html += '<div class="result-card"><h2>' + t("us_tax_title") + '</h2><table>';
  html += row(t("us_ordinary_tax"), fmt(tax.us.ordinary_tax) + " " + t("usd"), tax.us.ordinary_cite);
  html += row(t("us_div_tax"), fmt(tax.us.dividend_tax) + " " + t("usd"));
  html += row(t("us_cg_tax"), fmt(tax.us.capital_gain_tax) + " " + t("usd"));
  if (tax.us.se_tax) html += row(t("us_se_tax"), fmt(tax.us.se_tax) + " " + t("usd"));
  html += row(t("total_tax"), fmt(tax.us.total_tax) + " " + t("usd"));
  (tax.us.notes || []).forEach(function (n) { html += '<tr><td colspan="2" class="note">' + n + "</td></tr>"; });
  html += "</table></div>";

  // 境外抵免
  html += '<div class="result-card"><h2>' + t("ftc_title") + '</h2>';
  if (tax.ftc.cn_credit_limit !== null) html += "<p>" + tr("中国侧", "China side") + t("ftc") + "：" + fmt(tax.ftc.cn_credit_limit) + " " + t("yuan") + "</p>";
  if (tax.ftc.us_credit_limit !== null) html += "<p>" + tr("美国侧", "U.S. side") + t("ftc") + "：" + fmt(tax.ftc.us_credit_limit) + " " + t("usd") + "</p>";
  if (tax.ftc.combined) {
    const c = tax.ftc.combined;
    const hiName = c.higher_country === "china" ? tr("中国", "China") : tr("美国", "U.S.");
    const loName = c.lower_country === "china" ? tr("中国", "China") : tr("美国", "U.S.");
    html += "<p><strong>" + tr("综合税负（一种分配方式）", "Combined tax burden (one allocation)") + "：</strong></p>";
    html += "<p>" + tr("较低税国", "Lower-tax country") + " " + loName + " " + tr("全额缴纳", "paid in full") + "：$" + fmt(c.lower_tax_usd) + "</p>";
    html += "<p>" + tr("较高税国", "Higher-tax country") + " " + hiName + " " + tr("缴纳差额", "pays the residue") + "：$" + fmt(c.residue_usd) + "</p>";
    html += "<p>" + tr("总税负（较高者）", "Total tax (the higher)") + "：$" + fmt(c.total_usd) + "</p>";
    html += '<p class="cite">' + tr("存在多种抵免分配方式，以上仅为一种（较低税国全额、较高税国差额）；按汇率 1 USD = " + c.fx + " CNY 折算（原始税额见上方中国/美国税负卡片）。", "Many credit-allocation options exist; this is one (lower side in full, higher side the residue). FX = 1 USD = " + c.fx + " CNY (raw tax amounts are shown in the China / U.S. tax cards above).") + "</p>";
  }
  html += '<p class="cite">' + tax.ftc.note + "</p></div>";

  // 跨境劳务/版税（NRA 时才有）
  if (data.cross_border && (data.cross_border.service || data.cross_border.royalty)) {
    const cbLabel = currentLang === "zh" ? "跨境劳务/版税" : "Cross-border services / royalties";
    html += '<div class="result-card"><h2>' + cbLabel + "</h2>";
    if (data.cross_border.service) {
      html += "<p><strong>" + (currentLang === "zh" ? "美国来源劳务" : "U.S.-source services") + "：</strong>" + tr(data.cross_border.service.reason, data.cross_border.service.reason_en) + "</p>";
      html += '<p class="cite">' + t("citations") + "：" + data.cross_border.service.citation + "</p>";
    }
    if (data.cross_border.royalty) {
      html += "<p><strong>" + (currentLang === "zh" ? "美国来源版税" : "U.S.-source royalties") + "：</strong>" + tr(data.cross_border.royalty.reason, data.cross_border.royalty.reason_en) + "</p>";
      html += '<p class="cite">' + t("citations") + "：" + data.cross_border.royalty.citation + "</p>";
    }
    html += "</div>";
  }

  if (data.obligations && data.obligations.length) {
    html += '<div class="result-card"><h2>' + t("obligations_title") + "</h2>";
    data.obligations.forEach(function (o) {
      html += '<div class="obligation"><strong>' + (currentLang === "zh" ? o.zh : o.en) + "</strong>" +
        '<div class="cite">' + o.form + " · " + o.deadline + " · " + o.cite + "</div></div>";
    });
    html += "</div>";
  }

  if (data.information_returns && data.information_returns.length) {
    html += '<div class="result-card"><h2>' + t("information_returns_title") + "</h2>";
    data.information_returns.forEach(function (o) {
      html += '<div class="obligation"><strong>' + (currentLang === "zh" ? o.zh : o.en) + "</strong>" +
        '<div class="cite">' + o.form + " · " + o.note + "</div></div>";
    });
    html += "</div>";
  }

  r.innerHTML = html;
  r.classList.remove("hidden");
  r.scrollIntoView({ behavior: "smooth" });
}

document.getElementById("calc-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const resp = await fetch("/api/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(buildPayload()),
  });
  if (!resp.ok) {
    alert(t("load_err"));
    return;
  }
  lastData = await resp.json();
  render(lastData);
});

document.getElementById("reset-btn").addEventListener("click", () => {
  document.querySelectorAll("#calc-form input[type='number']").forEach(el => { el.value = "0"; });
  document.querySelectorAll("#calc-form input[type='checkbox']").forEach(el => { el.checked = false; });
  document.getElementById("fx_rate").value = "7.0";
  document.getElementById("us_ex_exempt").value = "0";
  document.getElementById("ad_child_cnt").value = "1";
  document.getElementById("ad_infant_cnt").value = "1";
  document.getElementById("ad_rent_city").value = "1500";
  document.getElementById("hold-rows").innerHTML = "";
  document.getElementById("cn-trip-rows").innerHTML = "";
  document.getElementById("us-trip-rows").innerHTML = "";
  document.getElementById("exempt-rows").innerHTML = "";
  document.getElementById("hold-summary").textContent = "";
  addHoldRow();
  lastData = null;
  const r = document.getElementById("results");
  r.classList.add("hidden");
  r.innerHTML = "";
});

applyI18n();
renderLegalLinks();
