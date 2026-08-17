import streamlit as st
import pandas as pd
import datetime

# 設定網頁基本排版
st.set_page_config(page_title="身態模擬器", page_icon="🎮", layout="wide")

# 自訂高對比美化樣式 (徹底解決夜間模式字體看不見與數字過大的問題)
st.markdown("""
    <style>
    .main { background-color: var(--background-color); }
    .stMetric { background-color: var(--secondary-background-color); padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    /* 強制設定全域文字與標題顏色，確保深淺色模式皆清晰可見 */
    h1, h2, h3, h4, h5, h6, p, span, label, div { color: var(--text-color) !important; }
    </style>
""", unsafe_allow_html=True)

# 初始化暫存記憶體
if 'history' not in st.session_state:
    st.session_state.history = []
if 'water' not in st.session_state:
    st.session_state.water = 0

# 1. 精簡標題 (刪除副標題)
st.title("🌱 身態模擬器")

# ==================== 模擬 5000+ 筆大數據食物資料庫 ====================
@st.cache_data
def load_large_food_database():
    data = [
        {"name": "珍珠奶茶 (700cc 微糖)", "cal": 650, "pro": 2, "carb": 85, "fat": 15},
        {"name": "炸雞排", "cal": 600, "pro": 35, "carb": 30, "fat": 38},
        {"name": "健康水煮雞胸肉沙拉", "cal": 250, "pro": 28, "carb": 12, "fat": 8},
        {"name": "經典牛肉麵", "cal": 800, "pro": 40, "carb": 90, "fat": 25},
        {"name": "便利商店御飯糰 (鮪魚)", "cal": 200, "pro": 6, "carb": 38, "fat": 3},
        {"name": "拿鐵咖啡 (中杯)", "cal": 180, "pro": 8, "carb": 15, "fat": 9},
        {"name": "陽春麵 (小碗)", "cal": 380, "pro": 10, "carb": 60, "fat": 8},
        {"name": "滷肉飯 (中)", "cal": 550, "pro": 15, "carb": 70, "fat": 22},
        {"name": "水餃 (10顆)", "cal": 500, "pro": 20, "carb": 60, "fat": 20},
        {"name": "茶葉蛋 (1顆)", "cal": 75, "pro": 7, "carb": 1, "fat": 5},
    ]
    expanded_data = []
    for i in range(500):
        for item in data:
            expanded_data.append({
                "name": f"{item['name']} (風味 {i+1})" if i > 0 else item['name'],
                "cal": item['cal'] + (i % 20),
                "pro": item['pro'],
                "carb": item['carb'],
                "fat": item['fat']
            })
    return pd.DataFrame(expanded_data)

food_df = load_large_food_database()

# ==================== 側邊欄：基本資料設定 ====================
st.sidebar.header("🕹️ 角色數值設定面板")
char_name = st.sidebar.text_input("角色名稱", value="小勇士")
age = st.sidebar.number_input("年齡 (歲)", min_value=1, max_value=120, value=25)
gender = st.sidebar.selectbox("性別", ["女", "男"])
height = st.sidebar.number_input("身高 (cm)", value=150.0)
weight = st.sidebar.number_input("體重 (kg)", value=50.0)

if gender == "女":
    bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
else:
    bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
tdee = bmr * 1.2
bmi = weight / ((height / 100) ** 2)

# 計算今日已攝取總熱量與熱量盈餘
today_cal_sum = sum([item['cal'] for item in st.session_state.history])
calorie_surplus = tdee - today_cal_sum  # 剩餘可攝取熱量

# ==================== 2. 改名後的「熱量小幫手」與虛擬小人物儀表板 ====================
st.subheader(f"📊 【{char_name}】的熱量小幫手")

# 虛擬身態判定與角色頭像
if bmi < 18.5:
    avatar_emoji = "🏃"
    avatar_status = "纖瘦精靈"
elif 18.5 <= bmi < 24:
    avatar_emoji = "🌟"
    avatar_status = "平衡戰士"
else:
    avatar_emoji = "🛡️"
    avatar_status = "坦克重裝"

# 儀表板排版 (加入虛擬人物呈現)
col_avatar, col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1, 1])
col_avatar.metric("RPG 虛擬角色", f"{avatar_emoji} {avatar_status}")
col1.metric("基礎代謝 (BMR)", f"{bmr:.0f} kcal")
col2.metric("每日消耗 (TDEE)", f"{tdee:.0f} kcal")
col3.metric("目前 BMI", f"{bmi:.1f}")
col4.metric("今日熱量盈餘", f"{calorie_surplus:.0f} kcal")

st.divider()

# ==================== 3. 智能食物搜尋與三餐記錄 ====================
st.subheader("🍱 智能食物搜尋與三餐記錄")

meal_category = st.selectbox("選擇餐別", ["早餐", "午餐", "晚餐", "宵夜/其他"])
search_keyword = st.text_input("🔍 輸入食物關鍵字搜尋 (例如: 雞肉、珍奶、飯)", "")

if search_keyword:
    filtered_df = food_df[food_df["name"].str.contains(search_keyword, case=False, na=False)]
else:
    filtered_df = food_df

if len(filtered_df) == 0:
    st.warning("⚠️ 找不到相關食物，您可以直接使用下方的『自訂食物』手動輸入熱量喔！")
    preview_options = ["✏️ 自訂食物 (手動輸入)"]
else:
    max_preview = 5
    preview_options = filtered_df["name"].head(max_preview).tolist()
    preview_options.append("✏️ 自訂食物 (手動輸入)")

selected_food = st.selectbox(f"符合條件的搜尋結果 (顯示前 {min(len(filtered_df), max_preview)} 項 + 自訂)", preview_options)

if selected_food == "✏️ 自訂食物 (手動輸入)":
    c_cal = st.number_input("熱量 (大卡)", value=300)
    c_pro = st.number_input("蛋白質 (g)", value=10)
    c_carb = st.number_input("碳水化合物 (g)", value=30)
    c_fat = st.number_input("脂肪 (g)", value=10)
else:
    matched_row = food_df[food_df["name"] == selected_food].iloc[0]
    c_cal = st.number_input("熱量 (大卡)", value=int(matched_row["cal"]))
    c_pro = st.number_input("蛋白質 (g)", value=float(matched_row["pro"]))
    c_carb = st.number_input("碳水化合物 (g)", value=float(matched_row["carb"]))
    c_fat = st.number_input("脂肪 (g)", value=float(matched_row["fat"]))

if st.button("➕ 確認新增紀錄"):
    st.session_state.history.append({
        "date": str(datetime.date.today()),
        "meal": meal_category,
        "food": selected_food,
        "cal": c_cal,
        "pro": c_pro,
        "carb": c_carb,
        "fat": c_fat
    })
    st.success(f"成功記錄！『{char_name}』的冒險日誌已更新。")
    st.rerun()

if st.session_state.history:
    st.write("### 📋 目前累積紀錄明細")
    st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
