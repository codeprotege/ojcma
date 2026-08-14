from __future__ import annotations

import base64
from html import escape
from pathlib import Path
import re

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "無標題的表格 (回應).xlsx"
IMAGE_FILE = ROOT / "assets" / "jci-collab.jpg"
HERO_FILE = ROOT / "assets" / "jci-hero.jpg"
SDG_ICON_DIR = ROOT / "assets" / "sdgs"

st.set_page_config(
    page_title="浩洋會員興趣調查｜Editorial edition",
    page_icon="◒",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_survey() -> pd.DataFrame:
    data = pd.read_excel(DATA_FILE)
    data.columns = [re.sub(r"\s+", " ", str(name)).strip() for name in data.columns]
    data = data.rename(
        columns=dict(
            zip(
                data.columns,
                [
                    "timestamp",
                    "name",
                    "development_focus",
                    "resource_request",
                    "memorable_programmes",
                    "satisfaction",
                    "new_programmes",
                    "other_programmes",
                    "future_role",
                ],
            )
        )
    )
    answer_cols = list(data.columns)[2:]
    data[answer_cols] = data[answer_cols].replace({pd.NaT: pd.NA, "": pd.NA})
    return data[data[answer_cols].notna().any(axis=1)].copy()


survey = load_survey()

FOCUS = ["個人發展", "社會發展", "商務發展", "國際發展"]
SATISFACTION = ["非常滿意", "滿意", "一般", "有改進空間", "未曾參與今年活動"]
PROGRAMMES = {
    "港日交流塾": "港日交流塾（日語基礎班）",
    "項目管理爆SKILL": "從 I 到 TEAM：項目管理爆SKILL 營",
    "幼教生存劇本殺": "幼教生存劇本殺",
}
NEW_PROGRAMMES = {
    "AI與數位": "AI 與數位工具領袖應用工作坊",
    "青年精神健康": "青年精神健康與心理",
    "綠色永續": "綠色永續與企業 ESG 實踐專案",
    "姊妹會": "姊妹會深度交流與聯合工作計劃",
    "初創創業": "初創創業路演與跨界商務對接",
    "體育聯賽": "體育聯賽／戶外團隊建立",
}
SHORT = {
    "AI與數位": "AI 與數位工具",
    "青年精神健康": "青年精神健康",
    "綠色永續": "綠色永續／ESG",
    "姊妹會": "姊妹會交流",
    "初創創業": "初創路演",
    "體育聯賽": "團隊建立",
}
ROLES = {
    "擔任工作計劃主席（Project Chairman )": "工作計劃主席",
    "擔任籌委會成員（OC Member）": "籌委會成員",
    "嘗試擔任董事局成員（Board Member）": "董事局成員",
    "以參加者/會友身份支持活動": "參加者／會友支持",
    "視乎時間再作安排": "視乎時間安排",
}
PILLARS = ["品牌可見度", "領導力發展", "組織可持續", "數據驅動創新"]
SDG_TITLES = {
    1: "消除貧窮", 2: "消除飢餓", 3: "良好健康與福祉", 4: "優質教育", 5: "性別平等",
    6: "淨水及衛生", 7: "可負擔的清潔能源", 8: "合適的工作及經濟成長", 9: "工業、創新和基礎建設",
    10: "減少不平等", 11: "可持續城巿和社區", 12: "責任消費及生產", 13: "氣候行動",
    14: "水下生物", 15: "陸地生物", 16: "和平、正義及健全制度", 17: "促進目標實現的伙伴關係",
}
ALIGN = {
    "AI與數位": ([0, 2, 0, 2], "領導力發展、數據驅動創新", ["SDG 4", "SDG 8", "SDG 9"]),
    "青年精神健康": ([1, 1, 2, 0], "組織可持續", ["SDG 3", "SDG 10", "SDG 11"]),
    "綠色永續": ([2, 1, 2, 2], "品牌可見度、組織可持續、數據驅動創新", ["SDG 12", "SDG 13", "SDG 17"]),
    "姊妹會": ([2, 1, 1, 0], "品牌可見度、領導力發展", ["SDG 4", "SDG 17"]),
    "初創創業": ([2, 2, 1, 1], "品牌可見度、領導力發展", ["SDG 8", "SDG 9", "SDG 17"]),
    "體育聯賽": ([0, 1, 2, 0], "組織可持續", ["SDG 3", "SDG 10"]),
}
MEMBERSHIP = pd.DataFrame({"組別": ["正式會員", "總會資深商會會員", "浩洋資深青商會員"], "已繳費": [25, 19, 17], "總數": [25, 22, 27]})
MEMBERSHIP["比例"] = MEMBERSHIP["已繳費"] / MEMBERSHIP["總數"]
COMMENT_TERMS = {
    "活動策劃": ("籌辦多啲活動", "活動主題", "交流活動", "資源和活動"),
    "國際發展": ("國際範疇", "國際活動範疇", "香港境內的國際發展"),
    "跨行業連結": ("不同行業的朋友", "認識吓朋友"),
    "培訓": ("training",),
    "體驗工作坊": ("體驗工作坊",),
    "講座": ("講座",),
    "交流／分享": ("交流活動", "分享會類"),
    "司儀／簡報": ("司儀及簡報演練",),
    "合作": ("partnership",),
    "興趣活動": ("各種興趣",),
    "資深會友": ("資深會友",),
    "更大膽的主題": ("諗大d", "不要閉門造車"),
}

def count_choice(frame: pd.DataFrame, column: str, key: str) -> int:
    return int(frame[column].fillna("").astype(str).str.contains(key, regex=False).sum())


def html_bar_chart(
    data: pd.DataFrame,
    label_column: str,
    value_column: str,
    colors: list[str] | None = None,
    denominator: int | None = None,
) -> str:
    maximum = max(int(data[value_column].max()), 1)
    # The reference uses one orange signal family; value determines its intensity.
    palette = colors or ["#d6d4cb", "#d9af9a", "#e88561", "#ff5b20"]

    def gradient_color(intensity: float) -> str:
        position = intensity * (len(palette) - 1)
        lower = min(int(position), len(palette) - 1)
        upper = min(lower + 1, len(palette) - 1)
        fraction = position - lower
        start = tuple(int(palette[lower][offset : offset + 2], 16) for offset in (1, 3, 5))
        end = tuple(int(palette[upper][offset : offset + 2], 16) for offset in (1, 3, 5))
        rgb = tuple(round(a + (b - a) * fraction) for a, b in zip(start, end))
        return "#" + "".join(f"{channel:02x}" for channel in rgb)

    rows: list[str] = []
    for index, row in data.reset_index(drop=True).iterrows():
        label = escape(str(row[label_column]))
        value = int(row[value_column])
        width = value / maximum * 100
        annotation = f"{value} · {value / denominator:.0%}" if denominator else str(value)
        intensity = value / maximum
        color = gradient_color(intensity)
        rows.append(
            f"<div class='html-bar-row'>"
            f"<div class='html-bar-label'>{label}</div>"
            f"<div class='html-bar-track' aria-hidden='true'><div class='html-bar-fill' style='width:{width:.2f}%;background:{color}'></div></div>"
            f"<div class='html-bar-value'>{annotation}</div>"
            f"</div>"
        )
    return f"<div class='html-chart' role='img' aria-label='以長條圖呈現{escape(label_column)}與{escape(value_column)}的比較'>{''.join(rows)}</div>"


def html_strategy_matrix() -> str:
    headers = "".join(f"<div class='matrix-heading'>{escape(pillar)}</div>" for pillar in PILLARS)
    rows: list[str] = []
    for key, label in NEW_PROGRAMMES.items():
        cells: list[str] = []
        for score in ALIGN[key][0]:
            text = "直接" if score == 2 else "支援" if score == 1 else ""
            class_name = "matrix-direct" if score == 2 else "matrix-support" if score == 1 else "matrix-empty"
            cells.append(f"<div class='matrix-cell {class_name}'>{text}</div>")
        rows.append(f"<div class='matrix-label'>{escape(label)}</div>{''.join(cells)}")
    return f"<div class='strategy-matrix' role='table' aria-label='JCI 2023 至 2027 策略對照'><div></div>{headers}{''.join(rows)}</div>"


def html_lollipop_chart(data: pd.DataFrame, label_column: str, value_column: str) -> str:
    maximum = max(int(data[value_column].max()), 1)
    rows: list[str] = []
    for _, row in data.reset_index(drop=True).iterrows():
        value = int(row[value_column])
        position = value / maximum * 100
        rows.append(
            f"<div class='lollipop-row'><div class='lollipop-label'>{escape(str(row[label_column]))}</div>"
            f"<div class='lollipop-track'><span class='lollipop-axis'></span><span class='lollipop-line' style='width:{position:.2f}%'></span><span class='lollipop-dot' style='left:{position:.2f}%'></span></div>"
            f"<div class='lollipop-value'>{value}</div></div>"
        )
    return f"<div class='lollipop-chart' role='img' aria-label='以棒棒糖圖呈現{escape(label_column)}與{escape(value_column)}的比較'>{''.join(rows)}</div>"


def html_dot_scale(data: pd.DataFrame, label_column: str, value_column: str) -> str:
    maximum = max(int(data[value_column].max()), 1)
    rows: list[str] = []
    for _, row in data.reset_index(drop=True).iterrows():
        value = int(row[value_column])
        dots = "".join(
            f"<span class='scale-dot {'is-on' if index < value else ''}'></span>"
            for index in range(maximum)
        )
        rows.append(
            f"<div class='scale-row'><div class='scale-label'>{escape(str(row[label_column]))}</div>"
            f"<div class='scale-dots'>{dots}</div><div class='scale-value'>{value}</div></div>"
        )
    return f"<div class='scale-chart' role='img' aria-label='以點陣呈現{escape(label_column)}與{escape(value_column)}的回覆數'>{''.join(rows)}</div>"


def html_symbol_roles(data: pd.DataFrame) -> str:
    symbols = ["◉", "◇", "✦", "○", "◌"]
    rows: list[str] = []
    for index, row in data.reset_index(drop=True).iterrows():
        rows.append(
            f"<div class='role-symbol-row'><span class='role-symbol'>{symbols[index % len(symbols)]}</span>"
            f"<span class='role-symbol-label'>{escape(str(row['角色']))}</span><strong>{int(row['回覆'])}</strong></div>"
        )
    return f"<div class='role-symbol-chart' role='img' aria-label='以符號呈現未來角色回覆'>{''.join(rows)}</div>"


def html_comment_cloud(frame: pd.DataFrame) -> str:
    responses = frame["resource_request"].dropna().astype(str).str.strip()
    responses = responses[responses.ne("")]
    frequencies = []
    for term, needles in COMMENT_TERMS.items():
        count = sum(any(needle in response.lower() for needle in needles) for response in responses)
        if count:
            frequencies.append((term, count))

    if not frequencies:
        return "<div class='comment-cloud comment-cloud-empty'>沒有符合篩選條件的開放回覆</div>"

    words = []
    for index, (term, count) in enumerate(frequencies):
        words.append(
            f"<span class='cloud-word cloud-slot-{index} cloud-tone-{index % 4}' "
            f"style='--cloud-weight:{count}' title='{count} 則回覆'>{escape(term)}</span>"
        )
    return f"<div class='comment-cloud' role='img' aria-label='以文字雲呈現所需資源或活動形式的關鍵詞'>{''.join(words)}</div>"


def html_payment_grid(data: pd.DataFrame) -> str:
    rows = []
    for _, row in data.iterrows():
        paid = int(row["已繳費"])
        total = int(row["總數"])
        unpaid = total - paid
        cells = "".join("<i class='payment-cell is-paid'></i>" for _ in range(paid))
        cells += "".join("<i class='payment-cell is-unpaid'></i>" for _ in range(unpaid))
        rows.append(
            f"<div class='payment-grid-row' aria-label='{escape(str(row['組別']))}：已繳 {paid} 位，未繳 {unpaid} 位，共 {total} 位'>"
            f"<div class='payment-grid-label'>{escape(str(row['組別']))}</div>"
            f"<div class='payment-member-grid' aria-hidden='true'>{cells}</div>"
            f"<div class='payment-grid-value'>{paid}/{total}</div></div>"
        )
    return (
        "<div class='payment-grid-chart' role='img' aria-label='各類別會員繳費記錄'>"
        f"{''.join(rows)}"
        "<div class='payment-grid-key'><span><i class='payment-cell is-paid'></i>已繳</span>"
        "<span><i class='payment-cell is-unpaid'></i>未繳</span></div></div>"
    )


def html_membership_pie(data: pd.DataFrame) -> str:
    colors = ["#ff5b20", "#6d9bb2", "#91ad62"]
    total = int(data["總數"].sum())
    if total == 0:
        return "<div class='membership-pie-chart'>沒有會員類別資料</div>"

    start = 0.0
    slices = []
    legend = []
    for index, (_, row) in enumerate(data.iterrows()):
        count = int(row["總數"])
        share = count / total * 100
        end = start + share
        color = colors[index % len(colors)]
        slices.append(f"{color} {start:.2f}% {end:.2f}%")
        legend.append(
            f"<div class='membership-pie-key-row'><span class='membership-pie-swatch' style='--swatch:{color}'></span>"
            f"<span>{escape(str(row['組別']))}</span><strong>{count} · {share:.0f}%</strong></div>"
        )
        start = end

    return (
        "<div class='membership-pie-chart' role='img' aria-label='按會員類別呈現會員組成'>"
        f"<div class='membership-pie' style=\"background:conic-gradient({', '.join(slices)})\"></div>"
        f"<div class='membership-pie-key'>{''.join(legend)}</div></div>"
    )


def image_url(path: Path) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


image = image_url(IMAGE_FILE)
hero_image = image_url(HERO_FILE)
SDG_IMAGES = {goal: image_url(SDG_ICON_DIR / f"goal-{goal:02d}.jpg") for goal in SDG_TITLES}


def sdg_logo(goal: int, class_name: str = "sdg-logo") -> str:
    return (
        f"<img class='{class_name}' src='{SDG_IMAGES[goal]}' "
        f"alt='SDG {goal}：{SDG_TITLES[goal]}' title='SDG {goal}：{SDG_TITLES[goal]}'>"
    )


def html_sdg_logo_grid() -> str:
    logos = "".join(sdg_logo(goal) for goal in SDG_TITLES)
    return f"<div class='sdg-logo-grid' role='list' aria-label='聯合國可持續發展目標 1 至 17'>{logos}</div>"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');
    :root{--paper:#f5f3ea;--ink:#0c1222;--navy:#050d1b;--muted:#666971;--line:#d1d1c9;--orange:#ff5b20;--pale:#ecebe3;}
    .stApp{background:var(--paper);color:var(--ink);font-family:'DM Sans','Heiti TC','Arial Unicode MS',sans-serif;}
    [data-testid='stHeader']{display:none;}
    [data-testid='stSidebar']{background:var(--navy);}
    [data-testid='stSidebar'] *{color:#f7f4ea !important;}
    [data-testid='stSidebar'] div[data-baseweb='select'] *{color:var(--ink) !important;}
    [data-testid='stSidebar'] [data-baseweb='select']>div{background:#f7f4ea !important;border-radius:0 !important;}
    [data-testid='stMainBlockContainer']{max-width:1400px;padding:1.2rem 3.1rem 4rem;}
    h1,h2,h3{font-family:'Playfair Display','Songti TC','STSong','Heiti TC',serif !important;font-weight:600 !important;letter-spacing:0 !important;color:var(--ink);}
    h1{font-size:clamp(2.9rem,6vw,6.3rem) !important;line-height:.94 !important;margin:.1rem 0 .7rem !important;}
    h2{font-size:clamp(1.7rem,3.1vw,3.25rem) !important;line-height:1 !important;margin:.1rem 0 .5rem !important;}
    h3{font-size:1.28rem !important;line-height:1.14 !important;}
    .rail-kicker,.figure-label,.metric-label{font-family:'DM Mono',monospace;text-transform:uppercase;letter-spacing:.07em;font-size:.63rem;color:var(--muted);}
    .rail-kicker{color:var(--orange);margin-bottom:.65rem;}
    .hero-figure{min-height:240px;border-bottom:1px solid var(--line);display:flex;align-items:flex-end;padding:1rem 0 1.4rem;}
    .rail-nav{position:sticky;top:1.2rem;padding-top:.8rem;}
    .rail-nav a{display:block;color:#f1eee6;text-decoration:none;border-bottom:1px solid #364050;padding:.57rem 0;font-family:'DM Mono',monospace;font-size:.68rem;}
    .rail-nav a:hover{color:var(--orange);}
    .figure-head{border-top:1px solid var(--line);padding:.65rem 0 .35rem;font-family:'DM Mono',monospace;font-size:.62rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;}
    .quote{border:1px solid var(--line);background:var(--pale);padding:1.15rem 1.2rem;min-height:210px;}
    .quote p{font-family:'Playfair Display','Songti TC','STSong',serif;font-size:1.35rem;line-height:1.15;margin:.75rem 0 1rem;}
    .setup-meta{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--line);border-left:1px solid var(--line);margin:1rem 0 1.2rem;}
    .setup-meta div{border-right:1px solid var(--line);border-bottom:1px solid var(--line);padding:.65rem .75rem;min-height:72px;}
    .setup-meta strong{display:block;font-family:'Playfair Display','Songti TC','STSong',serif;font-size:1.15rem;line-height:1.15;margin-top:.25rem;}
    .questionnaire-grid{display:grid;grid-template-columns:repeat(2,1fr);border-top:1px solid var(--line);border-left:1px solid var(--line);background:var(--pale);}
    .question-item{min-height:116px;border-right:1px solid var(--line);border-bottom:1px solid var(--line);padding:.8rem .9rem;display:grid;grid-template-columns:38px 1fr;gap:.55rem;align-content:start;}
    .question-number{font-family:'DM Mono',monospace;color:var(--orange);font-size:.7rem;padding-top:.1rem;}
    .question-title{font-family:'Playfair Display','Songti TC','STSong',serif;font-size:1.02rem;line-height:1.18;color:var(--ink);}
    .question-type{font-family:'DM Mono',monospace;font-size:.6rem;letter-spacing:.05em;color:var(--muted);margin-top:.35rem;}
    .setup-rationale{max-width:790px;margin:.2rem 0 1.2rem;padding-left:1rem;border-left:3px solid var(--orange);font-size:.94rem;line-height:1.65;color:var(--muted);}
    .setup-rationale strong{color:var(--ink);font-weight:600;}
    .orange-mark{background:var(--orange);color:var(--ink);padding:0 .12em;}
    .giant-number{font-family:'Playfair Display','Songti TC','STSong',serif;color:var(--ink);font-size:clamp(5rem,11vw,11rem);line-height:.82;letter-spacing:-.035em;margin:.15rem 0 .5rem;}
    .rule{height:1px;background:var(--line);margin:1.65rem 0 1rem;}
    .section{padding:2.1rem 0 .6rem;}
    .signal-board{display:grid;grid-template-columns:minmax(0,1.12fr) minmax(280px,.88fr);gap:clamp(1.5rem,3vw,3rem) clamp(1rem,2.8vw,3rem);margin:.35rem 0 .25rem;}
    .signal-panel{min-width:0;display:flex;flex-direction:column;}
    .signal-panel .figure-head{margin:0;flex:0 0 auto;}
    .signal-panel .lollipop-chart{flex:0 0 auto;}
    .signal-panel .scale-chart,.signal-panel .role-symbol-chart,.signal-panel .membership-pie-chart{flex:1;box-sizing:border-box;}
    .signal-metric{min-height:146px;padding:.35rem 0 .8rem;border-bottom:1px solid var(--line);display:flex;align-items:flex-end;}
    .signal-metric .giant-number{font-size:clamp(4.75rem,8vw,8rem);margin:.2rem 0 0;}
    .chart-frame{background:var(--pale);border:1px solid var(--line);padding:.35rem .35rem 0;}
    .html-chart{background:var(--pale);border:1px solid var(--line);padding:.8rem 1rem .75rem;}
    .html-bar-row{display:grid;grid-template-columns:minmax(132px,1fr) minmax(120px,2.5fr) minmax(64px,.45fr);gap:.7rem;align-items:center;min-height:37px;border-bottom:1px solid color-mix(in srgb,var(--line) 72%,transparent);}
    .html-bar-row:last-child{border-bottom:0;}
    .html-bar-label{font-size:.78rem;line-height:1.22;color:var(--ink);}
    .html-bar-track{height:13px;background:#e1e0d9;position:relative;overflow:hidden;}
    .html-bar-fill{height:100%;min-width:2px;transition:width .6s cubic-bezier(.16,1,.3,1);}
    .html-bar-row:hover .html-bar-fill{filter:brightness(.88);transform:translateX(2px);}
    .html-bar-value{font-family:'DM Mono',monospace;font-size:.68rem;color:var(--muted);text-align:right;white-space:nowrap;}
    .lollipop-chart,.scale-chart,.role-symbol-chart{background:var(--pale);border:1px solid var(--line);padding:.8rem 1rem .75rem;}
    .lollipop-row{display:grid;grid-template-columns:minmax(132px,1fr) minmax(120px,2.5fr) minmax(32px,.35fr);gap:.7rem;align-items:center;min-height:43px;border-bottom:1px solid color-mix(in srgb,var(--line) 72%,transparent);}
    .lollipop-row:last-child{border-bottom:0;}
    .lollipop-label,.scale-label{font-size:.78rem;line-height:1.22;}
    .lollipop-track{height:22px;position:relative;}
    .lollipop-axis{position:absolute;left:0;right:0;top:10px;height:1px;background:#c8c8c0;}
    .lollipop-line{position:absolute;left:0;top:9px;height:3px;background:#e88561;}
    .lollipop-dot{position:absolute;top:4px;width:14px;height:14px;border-radius:50%;background:var(--orange);transform:translateX(-50%);box-shadow:0 0 0 3px var(--pale);}
    .lollipop-value,.scale-value{font-family:'DM Mono',monospace;font-size:.68rem;color:var(--muted);text-align:right;}
    .scale-row{display:grid;grid-template-columns:minmax(132px,1fr) minmax(120px,2.5fr) minmax(32px,.35fr);gap:.7rem;align-items:center;min-height:43px;border-bottom:1px solid color-mix(in srgb,var(--line) 72%,transparent);}
    .scale-row:last-child{border-bottom:0;}
    .scale-dots{display:flex;gap:.35rem;align-items:center;}
    .scale-dot{width:12px;height:12px;border-radius:50%;border:1px solid #b4b5af;background:#e1e0d9;}
    .scale-dot.is-on{background:var(--orange);border-color:var(--orange);}
    .role-symbol-row{display:grid;grid-template-columns:30px 1fr 35px;gap:.6rem;align-items:center;min-height:48px;border-bottom:1px solid color-mix(in srgb,var(--line) 72%,transparent);}
    .role-symbol-row:last-child{border-bottom:0;}
    .role-symbol{font-family:'Playfair Display','Songti TC','STSong',serif;font-size:1.35rem;color:var(--orange);text-align:center;}
    .role-symbol-label{font-family:'Playfair Display','Songti TC','STSong',serif;font-size:1.05rem;line-height:1.1;}
    .role-symbol-row strong{font-family:'DM Mono',monospace;text-align:right;font-size:.75rem;}
    .member-figure-row{display:grid;grid-template-columns:minmax(170px,1fr) minmax(150px,2.5fr) 34px;gap:.7rem;align-items:center;min-height:54px;border-bottom:1px solid color-mix(in srgb,var(--line) 72%,transparent);}
    .member-figure-row:last-child{border-bottom:0;}
    .member-figure-label{font-family:'Playfair Display','Songti TC','STSong',serif;font-size:1.02rem;line-height:1.12;}
    .member-figures{display:flex;flex-wrap:wrap;gap:5px 7px;align-items:center;}
    .member-figure{width:13px;height:20px;position:relative;display:inline-block;color:var(--orange);flex:0 0 13px;}
    .member-figure::before{content:'';position:absolute;top:0;left:4px;width:6px;height:6px;border-radius:50%;background:currentColor;}
    .member-figure::after{content:'';position:absolute;top:7px;left:2px;width:10px;height:12px;background:currentColor;clip-path:polygon(30% 0,70% 0,83% 27%,100% 42%,87% 53%,76% 39%,76% 100%,59% 100%,50% 70%,41% 100%,24% 100%,24% 39%,13% 53%,0 42%,17% 27%);}
    .member-figure-value{font-family:'DM Mono',monospace;font-size:.72rem;color:var(--muted);text-align:right;}
    .payment-grid-chart{background:var(--pale);border:1px solid var(--line);padding:.75rem 1rem;}
    .payment-grid-row{display:grid;grid-template-columns:minmax(156px,1fr) minmax(158px,1.8fr) 52px;gap:.85rem;align-items:center;min-height:62px;border-bottom:1px solid color-mix(in srgb,var(--line) 72%,transparent);}
    .payment-grid-label{font-family:'Playfair Display','Songti TC','STSong',serif;font-size:1.04rem;line-height:1.12;}
    .payment-member-grid{display:grid;grid-template-columns:repeat(9,12px);grid-auto-rows:12px;gap:4px;align-content:center;}
    .payment-cell{display:block;width:12px;height:12px;box-sizing:border-box;}
    .payment-cell.is-paid{background:var(--orange);border:1px solid var(--orange);}
    .payment-cell.is-unpaid{background:transparent;border:1px solid #a9aaa4;}
    .payment-grid-value{font-family:'DM Mono',monospace;font-size:.72rem;color:var(--muted);text-align:right;white-space:nowrap;}
    .payment-grid-key{display:flex;gap:1rem;padding-top:.7rem;font-family:'DM Mono',monospace;font-size:.62rem;color:var(--muted);}
    .payment-grid-key span{display:flex;align-items:center;gap:.35rem;}
    .payment-grid-key .payment-cell{width:10px;height:10px;}
    .membership-pie-chart{min-height:204px;background:var(--pale);border:1px solid var(--line);padding:.9rem;display:grid;grid-template-columns:minmax(130px,.8fr) minmax(150px,1.2fr);gap:1rem;align-items:center;}
    .membership-pie{width:min(100%,180px);aspect-ratio:1;border-radius:50%;justify-self:center;box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--ink) 12%,transparent);}
    .membership-pie-key{display:grid;gap:.48rem;}
    .membership-pie-key-row{display:grid;grid-template-columns:12px 1fr auto;gap:.45rem;align-items:center;font-size:.76rem;line-height:1.15;}
    .membership-pie-key-row strong{font-family:'DM Mono',monospace;font-size:.64rem;font-weight:500;color:var(--muted);white-space:nowrap;}
    .membership-pie-swatch{display:block;width:10px;height:10px;background:var(--swatch);}
    .comment-cloud{min-height:360px;position:relative;overflow:hidden;background:var(--navy);border:1px solid var(--navy);isolation:isolate;}
    .cloud-word{position:absolute;display:block;font-family:'Playfair Display','Songti TC','STSong',serif;font-size:calc(.72rem + (var(--cloud-weight) * .52rem));font-weight:600;line-height:1.02;letter-spacing:0;white-space:nowrap;padding:.12rem .18rem;transform:translate(-50%,-50%) rotate(var(--cloud-tilt,0deg));transition:transform .28s ease-out,filter .28s ease-out;}
    .cloud-word:hover{transform:translate(-50%,-50%) rotate(0deg) scale(1.08);filter:brightness(1.12);z-index:1;}
    .cloud-tone-0{color:#ff6e3b;}.cloud-tone-1{color:#f7f4ea;}.cloud-tone-2{color:#b8d3c7;}.cloud-tone-3{color:#e7c26a;}
    .cloud-slot-0{left:50%;top:51%;--cloud-tilt:-2deg;}.cloud-slot-1{left:53%;top:25%;--cloud-tilt:1deg;}.cloud-slot-2{left:25%;top:55%;--cloud-tilt:-4deg;}.cloud-slot-3{left:75%;top:53%;--cloud-tilt:3deg;}.cloud-slot-4{left:74%;top:34%;--cloud-tilt:-2deg;}.cloud-slot-5{left:27%;top:30%;--cloud-tilt:2deg;}.cloud-slot-6{left:71%;top:76%;--cloud-tilt:-3deg;}.cloud-slot-7{left:27%;top:77%;--cloud-tilt:2deg;}.cloud-slot-8{left:14%;top:43%;--cloud-tilt:-5deg;}.cloud-slot-9{left:86%;top:65%;--cloud-tilt:3deg;}.cloud-slot-10{left:48%;top:75%;--cloud-tilt:-1deg;}.cloud-slot-11{left:49%;top:89%;--cloud-tilt:2deg;}
    .comment-cloud-empty{font-family:'DM Mono',monospace;font-size:.72rem;color:#aeb4be;}
    .decision-line{border-top:1px solid var(--line);padding:.75rem 0;display:grid;grid-template-columns:46px 1fr 1.2fr;gap:.8rem;align-items:start;}
    .decision-line b{font-family:'DM Mono',monospace;font-size:.68rem;color:var(--orange);}
    .decision-line strong{font-family:'Playfair Display','Songti TC','STSong',serif;font-size:1.15rem;line-height:1.1;}
    .image-figure{position:relative;min-height:335px;overflow:hidden;background:#151b28;}
    .image-figure img{width:100%;height:335px;object-fit:cover;display:block;opacity:.74;}
    .image-overlay{position:absolute;left:1.25rem;bottom:1.2rem;right:1.25rem;color:#f7f4ea;}
    .image-overlay p{font-family:'Playfair Display','Songti TC','STSong',serif;font-size:1.65rem;line-height:1.08;max-width:610px;margin:.4rem 0 .65rem;}
    .image-overlay small{font-family:'DM Mono',monospace;font-size:.66rem;letter-spacing:.05em;}
    .visual-spread{display:grid;grid-template-columns:.72fr 1.28fr;gap:1px;background:var(--paper);border:1px solid var(--line);margin:1.6rem 0;}
    .visual-portrait{min-height:450px;background-size:cover;background-position:70% center;position:relative;}
    .visual-portrait:after{content:'OJC / 2026';position:absolute;left:1rem;bottom:1rem;background:var(--orange);color:var(--ink);font-family:'DM Mono',monospace;font-size:.62rem;padding:.32rem .42rem;}
    .visual-note{min-height:450px;background:var(--navy);padding:2.2rem;display:flex;flex-direction:column;justify-content:flex-end;color:#f7f4ea;}
    .visual-note .figure-label{color:#aeb4be;}
    .visual-note .statement{font-family:'Playfair Display','Songti TC','STSong',serif;font-size:clamp(1.8rem,3vw,3.5rem);line-height:1.04;margin:.45rem 0 1.1rem;max-width:700px;}
    .margin-index{display:flex;gap:.45rem;margin:1rem 0 0;}
    .margin-index span{width:19px;height:3px;background:#4a5361;}.margin-index span:first-child{background:var(--orange);width:39px;}
    .sdg-logo-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(48px,1fr));gap:6px;margin:.65rem 0 1.15rem;}
    .sdg-logo{display:block;width:100%;aspect-ratio:1;object-fit:cover;}
    .mapping-sdgs{display:flex;flex-wrap:wrap;gap:5px;align-items:center;}
    .mapping-sdgs .sdg-logo{width:40px;flex:0 0 40px;}
    .mapping{border-top:1px solid var(--line);padding:.75rem 0;display:grid;grid-template-columns:1.1fr .5fr 1.2fr 1.25fr;gap:.8rem;align-items:center;}
    .mapping-name{font-family:'Playfair Display','Songti TC','STSong',serif;font-size:1.05rem;}
    .mapping-demand{color:var(--orange);font-family:'DM Mono',monospace;font-size:.78rem;}
    .mapping-copy{color:var(--muted);font-size:.76rem;line-height:1.4;}
    .strategy-matrix{display:grid;grid-template-columns:minmax(180px,1.3fr) repeat(4,minmax(90px,1fr));border-top:1px solid var(--line);border-left:1px solid var(--line);background:var(--pale);}
    .strategy-matrix>div{min-height:47px;display:flex;align-items:center;justify-content:center;border-right:1px solid var(--line);border-bottom:1px solid var(--line);padding:.35rem;}
    .strategy-matrix .matrix-heading{font-family:'DM Mono',monospace;font-size:.62rem;line-height:1.2;color:var(--muted);text-align:center;}
    .strategy-matrix .matrix-label{justify-content:flex-start;font-family:'Playfair Display','Songti TC','STSong',serif;font-size:.95rem;line-height:1.15;}
    .matrix-cell{font-family:'DM Mono',monospace;font-size:.66rem;}
    .matrix-direct{background:var(--orange);color:var(--ink);font-weight:500;}
    .matrix-support{background:#d9d9d2;color:#3e4044;}
    .matrix-empty{background:var(--pale);}
    .footer-note{font-family:'DM Mono',monospace;color:var(--muted);font-size:.62rem;line-height:1.5;padding-top:.4rem;}
    .stDownloadButton button{border-radius:0;border:1px solid var(--navy);background:transparent;color:var(--navy);font-family:'DM Mono',monospace;font-size:.7rem;}
    @media(max-width:760px){[data-testid='stMainBlockContainer']{padding:1rem 1.05rem 3rem;}h1{font-size:3.5rem !important;}h2{font-size:2rem !important;}.hero-figure{min-height:255px;}.setup-meta{grid-template-columns:1fr 1fr;}.questionnaire-grid{grid-template-columns:1fr;}.decision-line{grid-template-columns:38px 1fr;}.mapping{grid-template-columns:1fr 1fr;gap:.4rem;}.image-figure,.image-figure img{min-height:295px;height:295px;}.visual-spread{grid-template-columns:1fr;}.visual-portrait{min-height:285px;}.visual-note{min-height:320px;padding:1.45rem;}.rail-nav{position:static;}.signal-board{grid-template-columns:1fr;gap:1.75rem;margin-top:.2rem;}.signal-metric{min-height:112px;padding:.2rem 0 .65rem;}.signal-metric .giant-number{font-size:4.5rem;}.html-chart,.lollipop-chart,.scale-chart,.role-symbol-chart{padding:.65rem .6rem;}.html-bar-row,.lollipop-row,.scale-row{grid-template-columns:92px minmax(85px,1fr) 55px;gap:.45rem;}.html-bar-label,.lollipop-label,.scale-label{font-size:.7rem;}.html-bar-value,.lollipop-value,.scale-value{font-size:.59rem;}.scale-dots{gap:.18rem;}.scale-dot{width:9px;height:9px;}.member-figure-row{grid-template-columns:96px minmax(100px,1fr) 28px;gap:.45rem;min-height:58px;}.member-figure-label{font-size:.78rem;}.member-figures{gap:4px 5px;}.member-figure{transform:scale(.88);transform-origin:left center;margin-right:-1px;}.member-figure-value{font-size:.62rem;}.payment-grid-chart{padding:.65rem .6rem;}.payment-grid-row{grid-template-columns:88px minmax(120px,1fr) 38px;gap:.45rem;min-height:70px;}.payment-grid-label{font-size:.76rem;}.payment-member-grid{grid-template-columns:repeat(9,9px);grid-auto-rows:9px;gap:3px;}.payment-cell{width:9px;height:9px;}.payment-grid-value{font-size:.6rem;}.payment-grid-key{gap:.7rem;font-size:.57rem;}.payment-grid-key .payment-cell{width:9px;height:9px;}.membership-pie-chart{min-height:150px;padding:.65rem;grid-template-columns:100px minmax(0,1fr);gap:.65rem;}.membership-pie-key{gap:.34rem;}.membership-pie-key-row{grid-template-columns:9px 1fr;gap:.3rem;font-size:.67rem;}.membership-pie-key-row strong{grid-column:2;font-size:.57rem;}.membership-pie-swatch{width:8px;height:8px;}.sdg-logo-grid{grid-template-columns:repeat(auto-fit,minmax(42px,1fr));gap:4px;}.mapping-sdgs .sdg-logo{width:34px;flex-basis:34px;}.comment-cloud{min-height:0;padding:.9rem .65rem;display:flex;flex-wrap:wrap;align-items:center;gap:.28rem .38rem;}.cloud-word{position:static;font-size:calc(.66rem + (var(--cloud-weight) * .37rem));transform:none;}.cloud-word:hover{transform:scale(1.04);}.strategy-matrix{grid-template-columns:112px repeat(4,minmax(58px,1fr));overflow-x:auto;}.strategy-matrix>div{min-height:54px;padding:.25rem;}.strategy-matrix .matrix-heading,.matrix-cell{font-size:.55rem;}.strategy-matrix .matrix-label{font-size:.72rem;}}
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("<div class='rail-kicker'>浩洋會員興趣調查 / 2026</div>", unsafe_allow_html=True)
st.sidebar.markdown("<nav class='rail-nav'><a href='#opening'>01 / 開場</a><a href='#signal'>02 / 會員訊號</a><a href='#comments'>03 / 開放意見</a><a href='#portfolio'>04 / 計劃組合</a><a href='#trace'>05 / 策略追溯</a></nav>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='rule'></div>", unsafe_allow_html=True)
satisfaction_filter = st.sidebar.selectbox("活動滿意度", ["全部"] + SATISFACTION)
focus_filter = st.sidebar.selectbox("主要發展方向", ["全部"] + FOCUS)

filtered = survey.copy()
if satisfaction_filter != "全部":
    filtered = filtered[filtered["satisfaction"] == satisfaction_filter]
if focus_filter != "全部":
    filtered = filtered[filtered["development_focus"].fillna("").str.contains(focus_filter, regex=False)]

total = len(filtered)
if total == 0:
    st.warning("沒有資料")
    st.stop()
satisfaction_answered = filtered[filtered["satisfaction"].notna()]
positive = int(satisfaction_answered["satisfaction"].isin(["滿意", "非常滿意"]).sum())
positive_rate = positive / len(satisfaction_answered) if len(satisfaction_answered) else 0
programme_counts = pd.DataFrame([{"key": key, "計劃": label, "回覆": count_choice(filtered, "new_programmes", key)} for key, label in NEW_PROGRAMMES.items()]).sort_values("回覆", ascending=False, kind="stable")
top_count = int(programme_counts.iloc[0]["回覆"])
top_names = "、".join(SHORT[key] for key in programme_counts[programme_counts["回覆"] == top_count]["key"].tolist()[:2])
leadership = int(filtered["future_role"].fillna("").str.contains("主席|籌委會|董事局", regex=True).sum())

st.markdown("<div id='opening'></div>", unsafe_allow_html=True)
st.markdown("<div class='hero-figure'><div><div class='rail-kicker'>MEMBER PULSE / OCEAN JUNIOR CHAMBER</div><h1>會員想成長，<br>也想連結。</h1></div></div>", unsafe_allow_html=True)

st.markdown("<div class='figure-head'>FIG 01 · 2026 浩洋會員興趣調查 / 回覆窗口 06–09 AUG</div>", unsafe_allow_html=True)
st.markdown(f"<div class='quote'><div class='figure-label'>FIG 01A · 首選訊號</div><p><span class='orange-mark'>{top_names}</span></p></div>", unsafe_allow_html=True)

st.markdown("<div class='rule'></div><div class='section'><div class='figure-label'>FIG 01A · 問卷設定</div><h2>問卷從六個面向，<br>收集會員下一步的選擇。</h2></div>", unsafe_allow_html=True)
st.markdown(
    "<div class='setup-meta'>"
    "<div><div class='figure-label'>問卷名稱</div><strong>浩洋會員興趣調查</strong></div>"
    "<div><div class='figure-label'>完成時間</div><strong>3–5 分鐘</strong></div>"
    "<div><div class='figure-label'>回覆窗口</div><strong>06–09 AUG 2026</strong></div>"
    "</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p class='setup-rationale'><strong>了解會員現在所想，以及他們對未來浩洋的期望。</strong>"
    "先找出最需要的發展方向與資源形式，再回看既有活動的共鳴與滿意度；"
    "最後確認下一輪計劃的優先次序，以及會員願意承擔的角色，讓工作計劃同時回應需求、改善體驗並配對執行人手。</p>",
    unsafe_allow_html=True,
)
questions = [
    ("01", "四大發展機會", "單選 · 個人／社會／國際／商務"),
    ("02", "所需資源或活動形式", "開放回覆"),
    ("03", "今年最有印象的工作計劃", "多選 · 三項既有活動"),
    ("04", "今年活動整體滿意度", "單選 · 五級評價／未曾參與"),
    ("05", "最希望的新工作計劃", "多選 · 六項發展提案＋其他"),
    ("06", "未來希望承擔的角色", "單選 · 主席／OC／董事局／支持／彈性"),
]
question_markup = "".join(
    f"<article class='question-item'><div class='question-number'>{number}</div><div><div class='question-title'>{title}</div><div class='question-type'>{question_type}</div></div></article>"
    for number, title, question_type in questions
)
st.markdown(f"<section class='questionnaire-grid'>{question_markup}</section>", unsafe_allow_html=True)

st.markdown("<div id='signal'></div><div class='section'><div class='figure-label'>FIG 02 · 需求分布</div><h2>會員要的不是更多活動，<br>而是更有用的活動。</h2></div>", unsafe_allow_html=True)
focus_data = pd.DataFrame({"方向": FOCUS, "回覆": [count_choice(filtered, "development_focus", key) for key in FOCUS]}).sort_values("回覆")
sat_data = filtered["satisfaction"].value_counts().reindex(SATISFACTION).fillna(0).astype(int).rename_axis("滿意度").reset_index(name="回覆")
existing = filtered[filtered["memorable_programmes"].notna()]
existing_data = pd.DataFrame({"活動": list(PROGRAMMES.values()), "提及": [count_choice(existing, "memorable_programmes", key) for key in PROGRAMMES]}).sort_values("提及", ascending=False)
existing_members = "".join(
    f"<div class='member-figure-row'><span class='member-figure-label'>{escape(str(row['活動']))}</span>"
    f"<span class='member-figures' aria-hidden='true'>{''.join('<i class="member-figure"></i>' for _ in range(int(row['提及'])))}</span>"
    f"<strong class='member-figure-value'>{int(row['提及'])}</strong></div>"
    for _, row in existing_data.iterrows()
)
signal_board = (
    "<div class='signal-board'>"
    "<section class='signal-panel'><div class='figure-head'>FIG 02A · JCI 四大發展機會 / 首選</div>"
    f"{html_lollipop_chart(focus_data, '方向', '回覆')}</section>"
    "<section class='signal-panel'><div class='signal-metric'><div><div class='figure-label'>正面滿意度</div>"
    f"<div class='giant-number'>{positive_rate:.0%}</div></div></div>"
    "<div class='figure-head'>FIG 02B · 活動整體滿意度</div>"
    f"{html_dot_scale(sat_data, '滿意度', '回覆')}</section>"
    "<section class='signal-panel'><div class='figure-head'>FIG 02C · 已有共鳴的形式</div>"
    f"<div class='role-symbol-chart' role='img' aria-label='以人形符號呈現提及既有活動的會員人數'>{existing_members}</div></section>"
    "<section class='signal-panel'><div class='figure-head'>FIG 02D · 會員類別結構</div>"
    f"{html_membership_pie(MEMBERSHIP)}</section></div>"
)
st.markdown(signal_board, unsafe_allow_html=True)

st.markdown("<div id='comments'></div><div class='section'><div class='figure-label'>FIG 02E · 開放意見</div><h2>會員想要的資源，<br>藏在他們的用字裡。</h2></div>", unsafe_allow_html=True)
st.markdown("<div class='figure-head'>FIG 02E · 所需資源或活動形式 / 關鍵詞</div>", unsafe_allow_html=True)
st.markdown(html_comment_cloud(filtered), unsafe_allow_html=True)

st.markdown("<div class='rule'></div><div class='image-figure'><img src='" + image + "'><div class='image-overlay'><small>FIG 03 · 會員參與</small></div></div>", unsafe_allow_html=True)

st.markdown(
    f"<section class='visual-spread'><div class='visual-portrait' style=\"background-image:url('{hero_image}')\"></div>"
    f"<div class='visual-note'><div class='figure-label'>FIELD NOTE · 會員參與</div>"
    f"<div class='statement'>一起完成。</div>"
    f"<div class='margin-index'><span></span><span></span><span></span><span></span></div></div></section>",
    unsafe_allow_html=True,
)

st.markdown("<div id='portfolio'></div><div class='section'><div class='figure-label'>FIG 04 · 計劃組合</div><h2>六個選項，<br>四個先後順序。</h2></div>", unsafe_allow_html=True)
portfolio_left, portfolio_right = st.columns([1.22, .78], gap="large")
with portfolio_left:
    chart_data = programme_counts.rename(columns={"回覆": "選擇"})
    st.markdown("<div class='figure-head'>FIG 04A · 新工作計劃 / 多選</div>", unsafe_allow_html=True)
    st.markdown(html_bar_chart(chart_data, "計劃", "選擇", denominator=total), unsafe_allow_html=True)
with portfolio_right:
    st.markdown("<div class='figure-label'>建議的年度節奏</div>", unsafe_allow_html=True)
    decisions = [
        ("01", "首季主打", "AI 與數位工具", ""),
        ("02", "首季主打", "姊妹會交流", ""),
        ("03", "第二波", "綠色永續／ESG", ""),
        ("04", "第二波", "青年精神健康", ""),
    ]
    for number, stage, title, copy in decisions:
        st.markdown(f"<div class='decision-line'><b>{number}<br>{stage}</b><strong>{title}</strong></div>", unsafe_allow_html=True)

st.markdown("<div class='rule'></div>", unsafe_allow_html=True)
st.markdown("<div class='figure-head'>FIG 04B · 參與設計</div>", unsafe_allow_html=True)
role_data = filtered["future_role"].dropna().value_counts()
role_data = pd.DataFrame({"角色": [ROLES.get(role, role) for role in role_data.index], "回覆": role_data.values})
st.markdown(html_symbol_roles(role_data), unsafe_allow_html=True)

st.markdown("<div id='trace'></div><div class='section'><div class='figure-label'>FIG 05 · 策略追溯</div><h2>計劃要能說清楚：<br>為甚麼是現在，為甚麼由 OJC 做。</h2></div>", unsafe_allow_html=True)
st.markdown("<div class='figure-head'>FIG 05A · JCI 2023–2027 四項策略</div>", unsafe_allow_html=True)
st.markdown(html_strategy_matrix(), unsafe_allow_html=True)

st.markdown("<div class='rule'></div>", unsafe_allow_html=True)
st.markdown("<div class='figure-head'>FIG 05B · UNSDG 對照</div>", unsafe_allow_html=True)
st.markdown(html_sdg_logo_grid(), unsafe_allow_html=True)
for key, label in NEW_PROGRAMMES.items():
    count = count_choice(filtered, "new_programmes", key)
    sdg_icons = "".join(sdg_logo(int(tag.split()[-1])) for tag in ALIGN[key][2])
    st.markdown(f"<div class='mapping'><div class='mapping-name'>{label}</div><div class='mapping-demand'>{count}／{total}</div><div class='mapping-copy'><b>JCI 策略</b><br>{ALIGN[key][1]}</div><div class='mapping-sdgs'>{sdg_icons}</div></div>", unsafe_allow_html=True)

st.markdown("<div class='rule'></div>", unsafe_allow_html=True)
st.markdown("<div class='figure-head'>FIG 05C · 各類別會員繳費記錄</div>", unsafe_allow_html=True)
st.markdown(html_payment_grid(MEMBERSHIP), unsafe_allow_html=True)

st.markdown("<div class='rule'></div>", unsafe_allow_html=True)
st.markdown("<div class='footer-note'>資料來源：data/無標題的表格 (回應).xlsx 及 PDF 匯出檔；繳費快照摘錄自 data/ 內 WhatsApp 圖像。JCI 對照參考 2023–2027 Strategic Plan；UNSDG 對照為規劃性映射。</div>", unsafe_allow_html=True)
