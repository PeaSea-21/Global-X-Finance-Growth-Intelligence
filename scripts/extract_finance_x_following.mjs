import fs from "node:fs/promises";
import path from "node:path";
import { Workbook } from "@oai/artifact-tool";

const inputPath = "C:/Users/yinen/Documents/xwechat_files/wxid_p05ces5ccz2y22_b87e/msg/file/2026-08/twitter-正在关注-1784448167852.csv";
const outputDir = "outputs/01a019cd-4657-7a90-b9ce-b66b01926538";
const outputPath = path.join(outputDir, "X关注列表_股票财经AI相关候选账号.csv");

const existingProjectHandles = new Set([
  "AMD", "business", "ReutersBiz", "dylan522p", "nvidia", "Focus_Taiwan",
  "mingchikuo", "trendforce", "OpenAINewsroom", "GoogleAIStudio", "Alibaba_Qwen",
  "NVIDIAAI", "OpenAIDevs", "DarioAmodei", "deepseek_ai", "AnthropicAI",
  "IEObserve", "_LuoFuli", "testingcatalog", "SebastienBubeck", "Zai_org",
  "Kimi_Moonshot", "perplexity_ai", "miramurati", "claudeai", "jackclarkSF",
  "JeffDean", "polynoamial", "mikemeyerwq",
]);

const explicitHandles = new Map([
  ["Tesla", ["美股上市公司官方", "美股／AI与机器人", "一手公司动态", "HIGH"]],
  ["Meta", ["美股上市公司官方", "美股／AI", "一手公司动态", "HIGH"]],
  ["MorganStanley", ["金融机构官方", "全球市场", "机构研究与市场观点", "HIGH"]],
  ["RobinhoodApp", ["金融平台官方", "美股／零售交易", "市场参与和行业动态", "MEDIUM"]],
  ["NVIDIAGeForce", ["上市公司产品官方", "美股／AI半导体", "GPU产品和需求信号", "HIGH"]],
  ["nvidianewsroom", ["上市公司新闻室", "美股／AI半导体", "公司一手新闻", "HIGH"]],
  ["nikkei", ["财经媒体", "日本／全球市场", "亚洲宏观与公司新闻", "HIGH"]],
  ["KobeissiLetter", ["市场研究媒体", "全球市场", "宏观与跨资产市场观察", "MEDIUM"]],
  ["fundstrat", ["机构研究／市场策略", "美股／宏观", "市场策略观点", "MEDIUM"]],
  ["MacroMargin", ["宏观研究", "中国／全球宏观", "政策与美联储线索", "MEDIUM"]],
  ["cnfinancewatch", ["财经KOL／量化", "A股／美股", "盘前信息与量化观点", "MEDIUM"]],
  ["fupenglondon", ["宏观经济学家", "中国／全球宏观", "宏观与资产配置观点", "MEDIUM"]],
  ["TJ_Research", ["美股／宏观KOL", "美股／宏观／AI", "市场与政策观点", "MEDIUM"]],
  ["octopusycc", ["美股研究KOL", "美股／存储半导体", "期权流与存储产业观点", "MEDIUM"]],
  ["ParadisLabs", ["半导体投资研究", "AI／半导体", "产业与估值观点", "MEDIUM"]],
  ["LinQingV", ["半导体／资本市场研究", "AI芯片／全球市场", "产业与资本市场观点", "MEDIUM"]],
  ["dnystedt", ["半导体财经分析师", "台湾／半导体", "台湾产业与市场研究", "MEDIUM"]],
  ["tculpan", ["科技产业记者", "台湾／半导体", "芯片产业新闻", "MEDIUM"]],
  ["tengyanAI", ["AI基础设施研究", "AI算力／供应链", "AI基础设施产业研究", "MEDIUM"]],
  ["pequityresearch", ["半导体研究", "美股／半导体", "产业深度研究", "MEDIUM"]],
  ["jimmy_yoasobi", ["台湾半导体KOL", "台湾／美股半导体", "台积电与半导体产业观点", "MEDIUM"]],
  ["q083v4", ["半导体产业KOL", "中国／半导体", "供应链和材料观点", "LOW"]],
  ["AlphaguyTrading", ["AI半导体交易KOL", "美股／AI半导体", "交易复盘与产业观点", "LOW"]],
  ["wallstengine", ["美股市场媒体", "美股", "财报和市场快讯", "MEDIUM"]],
  ["TMTBreakout", ["TMT机构研究", "美股／科技", "华尔街研究与财报摘要", "MEDIUM"]],
  ["FundaAI", ["股票研究平台", "美股", "上市公司研究线索", "MEDIUM"]],
  ["citrini", ["跨资产投资研究", "全球市场", "主题与跨资产研究", "MEDIUM"]],
  ["jukan05", ["主题投资研究", "全球市场", "产业投资研究观点", "MEDIUM"]],
  ["Franktradinglog", ["宏观交易研究", "全球宏观", "宏观与商品市场观点", "MEDIUM"]],
  ["GarrettBullish", ["股票／宏观KOL", "美股／宏观", "市场与宏观观点", "LOW"]],
  ["Trader_S18", ["宏观／美股KOL", "美股／宏观", "跨资产市场观点", "LOW"]],
  ["vcmktasa", ["台美股研究者", "台湾／美股", "NVDA、TSM等台美股观点", "LOW"]],
  ["stockwilsonrice", ["台湾产业研究KOL", "台湾股市", "产业研究与投资观点", "LOW"]],
  ["ApeOfGreatWall", ["宏观市场研究", "中国／全球市场", "宏观至情绪的研究框架", "LOW"]],
  ["karpathy", ["AI研究领袖", "全球AI", "模型能力与AI产业趋势线索", "MEDIUM"]],
  ["ChatGPTapp", ["AI产品官方", "美股AI产业链", "OpenAI产品一手动态", "HIGH"]],
  ["alexandr_wang", ["AI公司高管", "美股AI产业链", "Meta与AI产业竞争线索", "MEDIUM"]],
  ["alexeheath", ["AI产业记者", "美股AI产业链", "AI竞争和公司新闻线索", "MEDIUM"]],
  ["NotTomBrown", ["AI公司高管", "美股AI产业链", "Anthropic算力与公司动态线索", "MEDIUM"]],
  ["sssjeffpu", ["科技股票研究", "美股／科技", "科技股与产业研究观点", "MEDIUM"]],
  ["Unclestocknotes", ["美股市场KOL", "美股／宏观", "市场、贸易与经济观点", "LOW"]],
  ["PeterSchiff", ["宏观经济学家", "全球宏观", "利率、通胀和风险资产观点", "MEDIUM"]],
  ["DavidSacks", ["科技投资人／政策顾问", "美股科技／政策", "科技政策和AI行业观点", "MEDIUM"]],
  ["vladtenev", ["金融平台高管", "美股／零售交易", "Robinhood与零售市场动态", "MEDIUM"]],
  ["coatuemgmt", ["科技投资机构", "美股／科技", "科技公司与资本市场线索", "MEDIUM"]],
]);

const financeRegex = /股票|股市|台股|美股|港股|A股|投資|投资|证券|證券|券商|财报|財報|财经|財經|金融|宏观|宏觀|经济|經濟|美联储|美聯儲|利率|通胀|通膨|量化|portfolio|earnings|equity|stock market|financial markets|macro|economy|economics|federal reserve|central bank|wall street|capital markets|asset management|hedge fund|private equity/i;
const semiconductorRegex = /半导体|半導體|芯片|晶片|GPU|HBM|NVIDIA|台积电|台積電|TSMC|数据中心|資料中心|存储|儲存|記憶體|semiconductor|chip|memory|datacenter|data center|AI infrastructure|AI hardware|AI supply chain|HPC|compute/i;
const mediaRegex = /Bloomberg|Reuters|CNBC|Financial Times|Wall Street Journal|日経|日本経済新聞|财经|財經|财新|財新|证券时报|證券時報|华尔街|華爾街|Barron/i;
const cryptoDominantRegex = /crypto|web3|blockchain|defi|token|airdrop|meme|nft|binance|okx|bybit|solana|ethereum|bitcoin|btc|eth|staking|onchain|链上|鏈上|币安|幣安|交易所/i;
const stockConnectionRegex = /股票|股市|台股|美股|A股|stock|equity|earnings|macro|宏观|宏觀|财经|財經|financial markets|semiconductor|半导体|半導體|chip|台积电|台積電|TSMC|NVIDIA/i;

function parseCsv(text) {
  const rows = [];
  let row = [];
  let value = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (quoted) {
      if (char === '"' && text[i + 1] === '"') {
        value += '"';
        i += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        value += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(value);
      value = "";
    } else if (char === "\n") {
      row.push(value.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      value = "";
    } else {
      value += char;
    }
  }
  if (value.length > 0 || row.length > 0) {
    row.push(value.replace(/\r$/, ""));
    rows.push(row);
  }
  return rows;
}

function csvEscape(value) {
  const stringValue = String(value ?? "");
  return /[",\r\n]/.test(stringValue) ? `"${stringValue.replaceAll('"', '""')}"` : stringValue;
}

function projectUse(category) {
  if (category.includes("财经") || category.includes("媒体")) return "事实新闻／市场快讯候选";
  if (category.includes("官方")) return "一手公司或产品动态候选";
  if (category.includes("宏观")) return "宏观政策与风险偏好线索";
  if (category.includes("半导体") || category.includes("AI")) return "AI／半导体产业链与预期线索";
  return "市场观点与选题线索";
}

const inputText = (await fs.readFile(inputPath, "utf8")).replace(/^\uFEFF/, "");
const parsed = parseCsv(inputText);
const [sourceHeaders, ...sourceRows] = parsed;
const sourceRecords = sourceRows.map((row) => Object.fromEntries(sourceHeaders.map((header, index) => [header, row[index] ?? ""])));
const selected = [];

for (const record of sourceRecords) {
  const text = `${record.screen_name} ${record.name} ${record.description} ${record.location} ${record.website}`;
  const lowerText = text.toLowerCase();
  let category;
  let market;
  let pathway;
  let confidence;
  let rationale;

  if (existingProjectHandles.has(record.screen_name)) {
    category = "项目现有候选账号";
    market = "见项目现有账号池";
    pathway = "已在项目候选池中；保留以便合并去重";
    confidence = "MEDIUM";
    rationale = "已存在于 config/x_accounts.csv；本次从关注列表中复核发现";
  } else if (explicitHandles.has(record.screen_name)) {
    [category, market, pathway, confidence] = explicitHandles.get(record.screen_name);
    rationale = "简介和账号身份直接表明与股票、宏观、AI半导体或项目既有市场范围相关";
  } else {
    // Prevent loose biography keywords from admitting crypto marketing, referral, and unrelated AI accounts.
    continue;
  }

  const triggerTerms = [
    ...(financeRegex.test(text) ? ["股票／财经／宏观"] : []),
    ...(semiconductorRegex.test(text) ? ["AI／半导体"] : []),
    ...(mediaRegex.test(text) ? ["财经媒体"] : []),
    ...(existingProjectHandles.has(record.screen_name) ? ["项目已有账号池"] : []),
  ].join("；");
  selected.push({
    "筛选类别": category,
    "建议用途": pathway,
    "市场范围": market,
    "置信度": confidence,
    "筛选依据": rationale,
    "命中维度": triggerTerms || "人工规则白名单",
    ...Object.fromEntries(sourceHeaders.map((header) => [header, record[header]])),
  });
}

selected.sort((a, b) => {
  const categoryOrder = ["项目现有候选账号", "美股上市公司官方", "上市公司", "金融机构官方", "财经媒体", "市场研究媒体", "半导体", "宏观", "市场", "跨市场"];
  const aRank = categoryOrder.findIndex((prefix) => a["筛选类别"].includes(prefix));
  const bRank = categoryOrder.findIndex((prefix) => b["筛选类别"].includes(prefix));
  const normalizedA = aRank === -1 ? 99 : aRank;
  const normalizedB = bRank === -1 ? 99 : bRank;
  return normalizedA - normalizedB || Number(b.followers_count) - Number(a.followers_count) || a.screen_name.localeCompare(b.screen_name);
});

const outputHeaders = ["筛选类别", "建议用途", "市场范围", "置信度", "筛选依据", "命中维度", ...sourceHeaders];
const csv = `\uFEFF${[outputHeaders, ...selected.map((record) => outputHeaders.map((header) => record[header] ?? ""))].map((row) => row.map(csvEscape).join(",")).join("\r\n")}\r\n`;
await fs.mkdir(outputDir, { recursive: true });
await fs.writeFile(outputPath, csv, "utf8");

// Re-import through the spreadsheet runtime and inspect the final CSV shape.
const workbook = await Workbook.fromCSV(csv, { sheetName: "财经账号候选" });
const preview = await workbook.render({
  sheetName: "财经账号候选",
  range: `A1:L${Math.min(selected.length + 1, 18)}`,
  scale: 1.25,
  format: "png",
});
await fs.writeFile(path.join(outputDir, "X关注列表_股票财经AI相关候选账号_preview.png"), new Uint8Array(await preview.arrayBuffer()));
const summary = await workbook.inspect({
  kind: "table",
  range: `财经账号候选!A1:F${Math.min(selected.length + 1, 12)}`,
  include: "values",
  tableMaxRows: 12,
  tableMaxCols: 6,
  maxChars: 5000,
});
const categories = Object.groupBy(selected, ({ "筛选类别": category }) => category);
console.log(JSON.stringify({
  inputRows: sourceRecords.length,
  outputRows: selected.length,
  outputPath,
  categoryCounts: Object.fromEntries(Object.entries(categories).map(([key, values]) => [key, values.length])),
  first: selected[0]?.screen_name,
  last: selected.at(-1)?.screen_name,
  artifactInspect: summary.ndjson,
}, null, 2));
