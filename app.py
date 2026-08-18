import streamlit as st
import pandas as pd
import datetime
import altair as alt
import io
import base64
from PIL import Image

# 設定網頁基本排版
st.set_page_config(page_title="身態模擬器", page_icon="🎮", layout="wide")

# 自訂高對比美化樣式與卡片設計
st.markdown("""
    <style>
    .main { background-color: var(--background-color); }
    .stMetric { background-color: var(--secondary-background-color); padding: 12px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    h1, h2, h3, h4, h5, h6, p, span, label, div { color: var(--text-color) !important; }
    .rpg-card {
        background: var(--secondary-background-color);
        border: 2px solid #ff4b4b;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        text-align: center;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

# 初始化暫存記憶體
if 'history' not in st.session_state:
    st.session_state.history = []
if 'water_history' not in st.session_state:
    st.session_state.water_history = []
if 'water' not in st.session_state:
    st.session_state.water = 0
if 'last_feedback' not in st.session_state:
    st.session_state.last_feedback = "🎮 歡迎進入身態模擬器！請設定你的基本資料並開始記錄健康生活吧！"

st.title("🌱 身態模擬器")

# ==================== 自動裁切 5 階段 RPG 角色圖片 ====================
@st.cache_data
def load_and_crop_avatars():
    try:
        img = Image.open("rpg_chars.png")
        w, h = img.size
        row_h = h / 2.0
        col_w = w / 5.0
        
        avatars = {"女": [], "男": []}
        genders = ["女", "男"]
        
        for r_idx, gender in enumerate(genders):
            for c_idx in range(5):
                left = c_idx * col_w + col_w * 0.08
                upper = r_idx * row_h + row_h * 0.12
                right = (c_idx + 1) * col_w - col_w * 0.08
                lower = (r_idx + 1) * row_h - row_h * 0.05
                
                cropped = img.crop((left, upper, right, lower))
                buffered = io.BytesIO()
                cropped.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                avatars[gender].append(f"data:image/png;base64,{img_str}")
        return avatars
    except Exception:
        fallback = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300&auto=format&fit=crop&q=80"
        return {"女": [fallback]*5, "男": [fallback]*5}

avatars_dict = load_and_crop_avatars()

# ==================== 專為台灣人設計的在地權威食物資料庫 ====================
TAIWAN_FOOD_DB = [
    {"name": "三明治 (Sandwich, 1份)", "cal": 320.0, "pro": 12.0, "carb": 35.0, "fat": 14.0},
    {"name": "三杯雞 (Three-Cup Chicken, 1份)", "cal": 480.0, "pro": 32.0, "carb": 8.0, "fat": 35.0},
    {"name": "滷肉飯 (Braised Pork Rice, 1碗)", "cal": 500.0, "pro": 15.0, "carb": 65.0, "fat": 20.0},
    {"name": "珍珠奶茶 (Bubble Tea, 700ml/微糖)", "cal": 450.0, "pro": 4.0, "carb": 75.0, "fat": 15.0},
    {"name": "台式雞排 (Fried Chicken Cutlet, 1份)", "cal": 650.0, "pro": 35.0, "carb": 40.0, "fat": 42.0},
    {"name": "牛肉麵 (Beef Noodle Soup, 1碗)", "cal": 600.0, "pro": 28.0, "carb": 70.0, "fat": 22.0},
    {"name": "小籠包 (Xiao Long Bao, 8顆)", "cal": 520.0, "pro": 24.0, "carb": 48.0, "fat": 26.0},
    {"name": "蛋餅 (Dan Bing, 1份)", "cal": 300.0, "pro": 10.0, "carb": 35.0, "fat": 12.0},
    {"name": "飯糰 (Taiwanese Rice Ball, 1顆)", "cal": 420.0, "pro": 12.0, "carb": 58.0, "fat": 15.0},
    {"name": "陽春麵 (Plain Noodle Soup, 1碗)", "cal": 350.0, "pro": 10.0, "carb": 60.0, "fat": 7.0},
    {"name": "無糖豆漿 (Soy Milk, 500ml)", "cal": 175.0, "pro": 16.0, "carb": 10.0, "fat": 7.0},
    {"name": "水煮雞胸肉 (Chicken Breast, 100g)", "cal": 165.0, "pro": 31.0, "carb": 0.0, "fat": 3.6},
    {"name": "蘋果 (Apple, 1顆)", "cal": 78.0, "pro": 0.4, "carb": 21.0, "fat": 0.3},
    {"name": "白米飯 (White Rice, 1碗)", "cal": 280.0, "pro": 5.4, "carb": 61.0, "fat": 0.6},
    {"name": "水煮蛋 (Boiled Egg, 1顆)", "cal": 72.0, "pro": 6.3, "carb": 0.4, "fat": 4.8},
    {"name": "地瓜 (Sweet Potato, 1條)", "cal": 130.0, "pro": 2.2, "carb": 30.0, "fat": 0.3},
    {"name": "鹹酥雞 (Salt Crispy Chicken, 1份)", "cal": 550.0, "pro": 25.0, "carb": 30.0, "fat": 35.0},
]

def search_taiwan_food(keyword):
    results = []
    if not keyword:
        results = TAIWAN_FOOD_DB
    else:
        keyword_lower = keyword.lower()
        for food in TAIWAN_FOOD_DB:
            if keyword_lower in food["name"].lower():
                results.append(food)
        # 若資料庫找不到，啟動 AI 網路智慧推估模擬
        if not results:
            results.append({
                "name": f"✨ AI 智慧推估食物：{keyword} (1份)",
                "cal": 400.0, "pro": 15.0, "carb": 45.0, "fat": 18.0
            })
    return results

# ==================== 版面配置：左側基本資料與數值，右側動態外觀角色卡片 ====================
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.markdown("### 📋 基本資料")
    char_name = st.text_input("角色名稱", value="小勇士")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        age = st.number_input("年齡 (歲)", min_value=1, max_value=120, value=25)
        height = st.number_input("身高 (cm)", value=150.0)
        target_weight = st.number_input("目標體重 (kg)", value=45.0)
    with col_s2:
        gender = st.selectbox("性別", ["女", "男"])
        weight = st.number_input("目前體重 (kg)", value=50.0)

# 計算 BMR, TDEE, BMI
if gender == "女":
    bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
else:
    bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
tdee = bmr * 1.2
bmi = weight / ((height / 100) ** 2)
recommended_water = max(1500, weight * 35 + (height - 150) * 3)

today_cal_sum = sum([item['cal'] for item in st.session_state.history])
calorie_remaining = tdee - today_cal_sum

# 5 階段外觀對應邏輯 (0:很瘦, 1:瘦, 2:正常, 3:胖, 4:超胖)
def get_body_tier(b):
    if b < 18.5:
        return 0, "很瘦 (過輕)"
    elif 18.5 <= b < 20.0:
        return 1, "瘦 (偏瘦)"
    elif 20.0 <= b < 24.0:
        return 2, "正常 (健康)"
    elif 24.0 <= b < 28.0:
        return 3, "胖 (過重)"
    else:
        return 4, "超胖 (肥胖)"

tier_idx, body_state = get_body_tier(bmi)
current_avatar_url = avatars_dict[gender][tier_idx]

with col_right:
    st.markdown("### 🎮 角色外觀視覺展示")
    st.markdown(f"""
        <div class="rpg-card">
            <img src="{current_avatar_url}" width="160" style="object-fit:contain; height:180px; border-radius:12px; background: rgba(255,255,255,0.05); margin-bottom: 10px;">
            <h2 style="margin:0; color:#ff4b4b;">{char_name}</h2>
            <p style="margin:5px 0 0 0; font-weight:bold; font-size:16px;">狀態：{body_state}</p>
            <p style="margin:2px 0; font-size:14px;">🎯 目標體重：<b>{target_weight} kg</b> | 📊 目前 BMI：<b>{bmi:.1f}</b></p>
        </div>
    """, unsafe_allow_html=True)

# 數據小卡列
st.write("")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("基礎代謝 (BMR)", f"{bmr:.0f} kcal")
col_m2.metric("每日消耗 (TDEE)", f"{tdee:.0f} kcal")
col_m3.metric("目前 BMI", f"{bmi:.1f}")
col_m4.metric("今日剩餘熱量", f"{calorie_remaining:.0f} kcal")

st.info(f"💬 {st.session_state.last_feedback}")
st.divider()

# 分頁架構
tab1, tab2, tab3, tab4 = st.tabs(["🍱 三餐紀錄", "📈 歷史熱量圖表", "💧 水分與日常追蹤", "🤖 我要吃嗎？"])

# 統一的關鍵字即時搜尋、自動帶入與手動調整函式
def render_food_selector_section(unique_key_prefix):
    st.markdown("#### 🔍 關鍵字搜尋與營養素自動帶入")
    search_keyword = st.text_input("關鍵字搜尋 (例如輸入: 三, 雞, 蘋果)", "", key=f"{unique_key_prefix}_kw")
    
    matched_foods = search_taiwan_food(search_keyword)
    options = [f["name"] for f in matched_foods]
    options.append("✏️ 自訂食物與營養素 (手動輸入)")
    
    selected_option = st.selectbox("選擇搜尋結果或常用食物", options, key=f"{unique_key_prefix}_sel")
    
    if selected_option == "✏️ 自訂食物與營養素 (手動輸入)":
        default_name = "自訂健康餐點"
        default_cal, default_pro, default_carb, default_fat = 350.0, 15.0, 40.0, 12.0
    else:
        matched_item = next((f for f in matched_foods if f["name"] == selected_option), matched_foods[0])
        default_name = matched_item["name"]
        default_cal = matched_item["cal"]
        default_pro = matched_item["pro"]
        default_carb = matched_item["carb"]
        default_fat = matched_item["fat"]
        
    st.markdown("##### ⚙️ 營養素數據調整 (自動帶入，亦可自由修改)")
    f_name = st.text_input("確認食物名稱", value=default_name, key=f"{unique_key_prefix}_fname")
    
    c1, c2, c3, c4 = st.columns(4)
    f_cal = c1.number_input("熱量 (kcal)", value=float(default_cal), key=f"{unique_key_prefix}_fcal")
    f_pro = c2.number_input("蛋白質 (g)", value=float(default_pro), key=f"{unique_key_prefix}_fpro")
    f_carb = c3.number_input("碳水 (g)", value=float(default_carb), key=f"{unique_key_prefix}_fcarb")
    f_fat = c4.number_input("脂肪 (g)", value=float(default_fat), key=f"{unique_key_prefix}_ffat")
    
    return f_name, f_cal, f_pro, f_carb, f_fat

# 分頁一：三餐紀錄
with tab1:
    st.subheader("📝 三餐與營養素記錄")
    meal_category = st.selectbox("選擇餐別", ["早餐", "午餐", "晚餐", "宵夜"])
    
    food_name, food_cal, food_pro, food_carb, food_fat = render_food_selector_section("tab1")

    if st.button("➕ 確認新增紀錄", type="primary"):
        st.session_state.history.append({
            "date": str(datetime.date.today()),
            "meal": meal_category,
            "food": food_name,
            "cal": food_cal,
            "pro": food_pro,
            "carb": food_carb,
            "fat": food_fat
        })
        
        new_total = sum([item['cal'] for item in st.session_state.history])
        if new_total > tdee + 200:
            st.session_state.last_feedback = f"⚠️ 警告！熱量超載！『{char_name}』的防禦力快被油膩吞沒了，要控制囉！"
        elif new_total >= tdee - 100:
            st.session_state.last_feedback = f"✨ 營養攝取非常均衡，『{char_name}』狀態極佳！"
        else:
            st.session_state.last_feedback = f"🌟 太神啦！目前維持完美的熱量赤字，『{char_name}』正在持續變強中！"

        st.success(f"成功記錄！『{char_name}』的冒險日誌已更新。")
        st.rerun()

    if st.session_state.history:
        st.write("### 📋 今日飲食清單")
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)

# 分頁二：歷史熱量圖表
with tab2:
    st.subheader("📈 歷史熱量圖表")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        filter_meal = st.selectbox("篩選想查看的餐別", ["全部"] + list(df["meal"].unique()))
        df_filtered = df[df["meal"] == filter_meal] if filter_meal != "全部" else df

        st.write(f"目前顯示【{filter_meal}】的熱量分佈圖：")
        
        chart = alt.Chart(df_filtered).mark_bar(color='#ff4b4b', cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X('food:N', sort=None, title='食物名稱', axis=alt.Axis(labelAngle=-25, labelLimit=250)),
            y=alt.Y('cal:Q', title='熱量 (大卡)', axis=alt.Axis(titleAngle=0, titleAnchor='end', titleY=-10)),
            tooltip=['food', 'cal', 'pro', 'carb', 'fat']
        ).properties(height=350)
        
        st.altair_chart(chart, use_container_width=True)
        
        total_cal_today = df["cal"].sum()
        st.info(f"💡 系統總結：今日累計攝取 **{total_cal_today} 大卡** (目標 TDEE：{tdee:.0f} 大卡)")
        
        if total_cal_today > tdee:
            st.error(f"⚠️ 【隔天超標智能提醒】注意！昨天熱量超標囉！建議今天早餐改吃水煮蛋與無糖豆漿，午餐主食減半，將熱量拉回平衡！")
        else:
            st.success(f"✨ 【完美狀態】『{char_name}』保持得非常棒！請繼續維持這個節奏！")
    else:
        st.info("目前還沒有資料，請先至『三餐紀錄』分頁新增食物！")

# 分頁三：水分與日常追蹤
with tab3:
    st.subheader("💧 每日水分攝取量追蹤")
    st.info(f"💡 根據您的身高 (**{height} cm**) 與體重 (**{weight} kg**) 計算，今日建議飲水量為：**{recommended_water:.0f} c.c.**")
    
    st.write(f"目前已補充水分：**{st.session_state.water} c.c.** / 目標 **{recommended_water:.0f} c.c.**")
    
    col_w1, col_w2, col_w3 = st.columns(3)
    if col_w1.button("💧 喝一杯水 (+250 c.c.)"):
        st.session_state.water += 250
        st.session_state.water_history.append({"date": str(datetime.date.today()), "action": "喝一杯水", "amount": "250 c.c.", "total_water": f"{st.session_state.water} c.c."})
        st.success("成功記錄 250 c.c. 水分！")
        st.rerun()
    if col_w2.button("🚰 大口灌水 (+500 c.c.)"):
        st.session_state.water += 500
        st.session_state.water_history.append({"date": str(datetime.date.today()), "action": "大口灌水", "amount": "500 c.c.", "total_water": f"{st.session_state.water} c.c."})
        st.success("成功記錄 500 c.c. 水分！")
        st.rerun()
    if col_w3.button("🔄 重置水分歸零"):
        st.session_state.water = 0
        st.session_state.water_history = []
        st.success("水分紀錄已重置歸零！")
        st.rerun()
        
    if st.session_state.water < recommended_water:
        st.warning("⚠️ 警告：角色出現『缺水 Debuff』，代謝速度下降中，請趕快多喝水！")
    else:
        st.success("🌟 狀態加成：水分充足，獲得『水潤新陳代謝 Buff』！")

    st.write("### 📋 飲水紀錄")
    if st.session_state.water_history:
        st.dataframe(pd.DataFrame(st.session_state.water_history), use_container_width=True)
    else:
        st.info("目前尚無飲水紀錄，點擊上方按鈕開始記錄水分吧！")

# 分頁四：我要吃嗎？
with tab4:
    st.subheader("🤖 我要吃嗎？ (AI 營養顧問與身型預測模擬)")
    st.info(f"💡 目標體重：**{target_weight} kg**。輸入你想吃的食物，AI 顧問會進行營養分析與動態外觀模擬！")
    
    ai_food_name, ai_cal, ai_pro, ai_carb, ai_fat = render_food_selector_section("tab4")

    if st.button("🚀 啟動 AI 營養顧問與外觀模擬", type="primary"):
        st.write("---")
        st.markdown(f"### 🛡️ 【{char_name}】的 AI 決策分析與外觀模擬報告")
        
        # 1. 營養素剖析
        st.markdown("#### 1️⃣ 營養素剖析 (Nutrient Breakdown)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("預估熱量", f"{ai_cal:.0f} kcal")
        c2.metric("蛋白質", f"{ai_pro:.1f} g")
        c3.metric("碳水化合物", f"{ai_carb:.1f} g")
        c4.metric("脂肪", f"{ai_fat:.1f} g")
        
        # 2. 模擬吃完後的體態變化
        projected_remaining = calorie_remaining - ai_cal
        simulated_weight = weight + (max(0, -projected_remaining) / 7700 * 5)
        simulated_bmi = simulated_weight / ((height / 100) ** 2)
        simulated_tier, simulated_body_state = get_body_tier(simulated_bmi)
        
        if projected_remaining < 0:
            simulated_tier = min(4, max(tier_idx + 1, simulated_tier))
            simulated_body_state += " (⚠️ 熱量超載警戒)"
            
        simulated_avatar_url = avatars_dict[gender][simulated_tier]

        st.markdown("#### 2️⃣ 角色外觀視覺模擬對比 (Before vs After)")
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            st.markdown(f"""
                <div style="background:var(--secondary-background-color); padding:15px; border-radius:12px; text-align:center; border: 2px solid #3498db;">
                    <p style="font-weight:bold; font-size:15px; margin-bottom:8px;">🔵 目前角色外觀</p>
                    <img src="{current_avatar_url}" width="120" style="object-fit:contain; height:130px; margin-bottom:8px;">
                    <p style="margin:0; font-size:14px; font-weight:bold;">{body_state}</p>
                </div>
            """, unsafe_allow_html=True)
        with col_img2:
            st.markdown(f"""
                <div style="background:var(--secondary-background-color); padding:15px; border-radius:12px; text-align:center; border: 2px solid #e74c3c;">
                    <p style="font-weight:bold; font-size:15px; margin-bottom:8px;">🔴 享用後的預估外觀</p>
                    <img src="{simulated_avatar_url}" width="120" style="object-fit:contain; height:130px; margin-bottom:8px;">
                    <p style="margin:0; font-size:14px; font-weight:bold;">{simulated_body_state}</p>
                </div>
            """, unsafe_allow_html=True)
                
        # 3. 該不該吃決策
        st.markdown("#### 3️⃣ AI 決策建議 (Should you eat it?)")
        if projected_remaining >= 150:
            st.success("🌟 **AI 建議：可以安心食用！** 你的熱量扣打相當充裕，這份食物不會妨礙你的目標體重進度，外觀保持完美！")
        elif projected_remaining >= 0:
            st.warning("⚠️ **AI 建議：可以吃，但請注意份量！** 吃了會剛好達到今日 TDEE 邊界。建議吃一半或分給朋友共食，以維持體態。")
        else:
            st.error(f"🚨 **AI 建議：強烈建議忍痛放棄或嚴格減半！** 吃了將會導致今日熱量超標約 **{abs(projected_remaining):.0f} kcal**，體態將往右側肥胖等級邁進！")
            
        # 4. 吃了之後怎麼辦
        st.markdown("#### 4️⃣ 💡 吃了之後的補救與行動計畫 (Post-meal Action Plan)")
        if projected_remaining < 0:
            st.info("""
            * **運動代償：** 建議飯後進行 45 分鐘至 1 小時的有氧運動（如慢跑或快走）來燃燒多餘熱量。
            * **水分加速代謝：** 接下來請多補充 500 c.c. 至 800 c.c. 的水分，幫助身體代謝廢物。
            * **隔日微調：** 若真的吃完超標，明天早餐改為無糖豆漿與水煮蛋，將熱量平均拉回平衡！
            """)
        else:
            st.info("""
            * **維持節奏：** 保持目前的飲食與喝水節奏，記得今天的水分目標要喝夠喔！
            * **營養平衡：** 下一餐可以多攝取一些膳食纖維，讓營養更全面。
            """)
