import streamlit as st
import pandas as pd
import datetime
import altair as alt
import requests
import io
import base64
from PIL import Image

# 設定網頁基本排版
st.set_page_config(page_title="身態模擬器", page_icon="🎮", layout="wide")

# 自訂高對比美化樣式
st.markdown("""
    <style>
    .main { background-color: var(--background-color); }
    .stMetric { background-color: var(--secondary-background-color); padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    h1, h2, h3, h4, h5, h6, p, span, label, div { color: var(--text-color) !important; }
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
    st.session_state.last_feedback = "🎮 歡迎進入身態模擬器！請設定數值並開始你的健康冒險吧！"

st.title("🌱 身態模擬器 (5 階段 RPG 成長版)")

# ==================== 自動裁切 5 階段 RPG 角色圖片 ====================
@st.cache_data
def load_and_crop_avatars():
    try:
        # 讀取同資料夾中的 rpg_chars.png
        img = Image.open("rpg_chars.png")
        w, h = img.size
        
        # 圖片結構：2行 (女, 男)，5列 (很瘦, 瘦, 正常, 胖, 超胖)
        row_h = h / 2.0
        col_w = w / 5.0
        
        avatars = {"女": [], "男": []}
        genders = ["女", "男"]
        
        for r_idx, gender in enumerate(genders):
            for c_idx in range(5):
                # 邊界微調以避開文字框
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
        # 若找不到圖片時的預設備用圖
        fallback = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300&auto=format&fit=crop&q=80"
        return {"女": [fallback]*5, "男": [fallback]*5}

avatars_dict = load_and_crop_avatars()

# ==================== 串接真實全球食物資料庫 API (Open Food Facts) ====================
@st.cache_data(ttl=3600)
def fetch_real_food_data(keyword):
    if not keyword:
        return pd.DataFrame()
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={keyword}&search_simple=1&action=process&json=1&page_size=15"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            food_list = []
            for p in products:
                name = p.get('product_name', '')
                nutriments = p.get('nutriments', {})
                cal = nutriments.get('energy-kcal_100g', 0)
                pro = nutriments.get('proteins_100g', 0)
                carb = nutriments.get('carbohydrates_100g', 0)
                fat = nutriments.get('fat_100g', 0)
                
                if name and cal and float(cal) > 0:
                    food_list.append({
                        "name": f"{name} (每100克)",
                        "cal": float(cal),
                        "pro": float(pro),
                        "carb": float(carb),
                        "fat": float(fat)
                    })
            return pd.DataFrame(food_list)
    except Exception:
        pass
    return pd.DataFrame()

# ==================== 側邊欄：角色數值與目標設定 ====================
st.sidebar.header("🕹️ 角色數值與目標設定")
char_name = st.sidebar.text_input("角色名稱", value="小勇士")
age = st.sidebar.number_input("年齡 (歲)", min_value=1, max_value=120, value=25)
gender = st.sidebar.selectbox("性別", ["女", "男"])
height = st.sidebar.number_input("身高 (cm)", value=150.0)
weight = st.sidebar.number_input("目前體重 (kg)", value=50.0)
target_weight = st.sidebar.number_input("目標體重 (kg)", value=45.0)

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
weight_diff = weight - target_weight

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

# 儀表板
st.subheader(f"📊 【{char_name}】的熱量小幫手 (目標體重：{target_weight} kg)")
col_av, col_m1, col_m2, col_m3, col_m4 = st.columns([1.2, 1, 1, 1, 1])
with col_av:
    st.markdown(f"""
        <div style="background:var(--secondary-background-color); padding:8px; border-radius:12px; text-align:center; border: 2px solid #ff4b4b;">
            <img src="{current_avatar_url}" width="95" style="object-fit:contain; height:105px; margin-bottom:4px;">
            <p style="margin:0; font-weight:bold; font-size:13px;">{body_state}</p>
        </div>
    """, unsafe_allow_html=True)

col_m1.metric("基礎代謝 (BMR)", f"{bmr:.0f} kcal")
col_m2.metric("每日消耗 (TDEE)", f"{tdee:.0f} kcal")
col_m3.metric("目前 BMI", f"{bmi:.1f}")
col_m4.metric("今日剩餘熱量", f"{calorie_remaining:.0f} kcal")

st.info(f"💬 {st.session_state.last_feedback}")
st.divider()

# 分頁架構
tab1, tab2, tab3, tab4 = st.tabs(["🍱 智能食物搜尋與三餐記錄", "📈 歷史熱量圖表", "💧 水分與日常追蹤", "🤖 AI 營養顧問 (我要吃嗎？)"])

# 分頁一：食物搜尋與記錄
with tab1:
    st.subheader("📝 三餐與營養素記錄 (串接全球真實食物資料庫)")
    meal_category = st.selectbox("選擇餐別", ["早餐", "午餐", "晚餐", "宵夜/其他"])
    search_keyword = st.text_input("🔍 輸入關鍵字搜尋真實食物 (例如: apple, chicken, rice, milk)", "")
    
    real_food_df = fetch_real_food_data(search_keyword)

    if search_keyword and real_food_df.empty:
        st.warning("⚠️ 在全球資料庫中找不到該食物，您可以直接使用下方的『自訂食物』手動輸入！")
        preview_options = ["✏️ 自訂食物 (手動輸入)"]
    elif real_food_df.empty:
        preview_options = ["✏️ 自訂食物 (手動輸入)"]
    else:
        preview_options = real_food_df["name"].tolist()
        preview_options.append("✏️ 自訂食物 (手動輸入)")

    selected_food = st.selectbox("選擇搜尋結果或自訂", preview_options)

    if selected_food == "✏️ 自訂食物 (手動輸入)":
        c_cal = st.number_input("熱量 (大卡)", value=300)
        c_pro = st.number_input("蛋白質 (g)", value=10)
        c_carb = st.number_input("碳水化合物 (g)", value=30)
        c_fat = st.number_input("脂肪 (g)", value=10)
    else:
        matched_row = real_food_df[real_food_df["name"] == selected_food].iloc[0]
        c_cal = st.number_input("熱量 (大卡)", value=float(matched_row["cal"]))
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
        
        new_total = sum([item['cal'] for item in st.session_state.history])
        if new_total > tdee + 200:
            st.session_state.last_feedback = f"哇！熱量超載囉！『{char_name}』的防禦力快被油膩吞沒了，要控制囉！"
        elif new_total >= tdee - 100:
            st.session_state.last_feedback = f"很棒！營養攝取非常均衡，繼續保持！"
        else:
            st.session_state.last_feedback = f"太神啦！目前維持完美的熱量赤字，『{char_name}』正在持續變強中！"

        st.success(f"成功記錄！『{char_name}』的冒險日誌已更新。")
        st.rerun()

    if st.session_state.history:
        st.write("### 📋 飲食紀錄")
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)

# 分頁二：歷史熱量圖表
with tab2:
    st.subheader("📈 歷史熱量圖表")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        filter_meal = st.selectbox("篩選想查看的餐別", ["全部"] + list(df["meal"].unique()))
        df_filtered = df[df["meal"] == filter_meal] if filter_meal != "全部" else df

        st.write(f"目前顯示【{filter_meal}】的熱量分佈圖：")
        chart_df = df_filtered.copy()
        chart_df['short_name'] = chart_df['food'].apply(lambda x: x.split(' (')[0] if ' (' in x else x)
        
        chart = alt.Chart(chart_df).mark_bar(color='#ff4b4b', cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X('short_name:N', sort=None, title='食物名稱', axis=alt.Axis(labelAngle=-25, labelLimit=250)),
            y=alt.Y('cal:Q', title='熱量 (大卡)', axis=alt.Axis(titleAngle=0, titleAnchor='end', titleY=-10)),
            tooltip=['food', 'cal', 'pro', 'carb', 'fat']
        ).properties(height=350)
        
        st.altair_chart(chart, use_container_width=True)
        
        total_cal_today = df["cal"].sum()
        st.info(f"💡 系統總結：今日累計攝取 **{total_cal_today} 大卡** (目標 TDEE：{tdee:.0f} 大卡)")
        
        if total_cal_today > tdee:
            st.error(f"⚠️ 【隔天超標智能提醒】注意！昨天熱量超載囉！『{char_name}』防禦力需要恢復～ 建議今天早餐吃水煮蛋加無糖豆漿，午餐多吃綠色蔬菜，晚餐將澱粉減半！")
        else:
            st.success(f"✨ 【完美狀態】『{char_name}』保持得非常棒！熱量控制在安全範圍內，請繼續維持這個節奏！")
    else:
        st.info("目前還沒有資料，請先至『智能食物搜尋與三餐記錄』分頁新增食物！")

# 分頁三：水分與日常追蹤
with tab3:
    st.subheader("💧 每日水分攝取量追蹤 (Water Tracker)")
    st.info(f"💡 根據您的身高 (**{height} cm**) 與體重 (**{weight} kg**) 計算，今日個人化建議飲水量為：**{recommended_water:.0f} c.c.**")
    
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
        st.success("水分與飲水紀錄已重置歸零！")
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

# --------- 分頁四：AI 營養顧問與角色視覺化模擬 ---------
with tab4:
    st.subheader("🤖 AI 營養顧問與身型預測模擬 (我要吃嗎？)")
    st.info(f"💡 目標體重：**{target_weight} kg**。輸入你想吃的食物，AI 顧問不僅會進行營養分析，還會**動態模擬**吃完後的角色外觀變化！")
    
    ai_keyword = st.text_input("🔍 輸入想評估的食物名稱 (例如: chicken cutlet, boba tea, cake)", "")
    ai_food_df = fetch_real_food_data(ai_keyword)

    if ai_keyword and not ai_food_df.empty:
        ai_options = ai_food_df["name"].tolist()
        ai_options.append("✏️ 自訂營養素評估")
        selected_ai_food = st.selectbox("選擇評估項目", ai_options)
        
        if selected_ai_food == "✏️ 自訂營養素評估":
            ai_cal = st.number_input("熱量 (大卡)", value=550)
            ai_pro = st.number_input("蛋白質 (g)", value=25)
            ai_carb = st.number_input("碳水化合物 (g)", value=45)
            ai_fat = st.number_input("脂肪 (g)", value=30)
        else:
            match_row = ai_food_df[ai_food_df["name"] == selected_ai_food].iloc[0]
            ai_cal = st.number_input("熱量 (大卡)", value=float(match_row["cal"]))
            ai_pro = st.number_input("蛋白質 (g)", value=float(match_row["pro"]))
            ai_carb = st.number_input("碳水化合物 (g)", value=float(match_row["carb"]))
            ai_fat = st.number_input("脂肪 (g)", value=float(match_row["fat"]))
    else:
        ai_cal = st.number_input("熱量 (大卡)", value=600)
        ai_pro = st.number_input("蛋白質 (g)", value=30)
        ai_carb = st.number_input("碳水化合物 (g)", value=40)
        ai_fat = st.number_input("脂肪 (g)", value=35)

    if st.button("🚀 啟動 AI 營養顧問與外觀模擬"):
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
        
        # 計算食用後的預估體重與 BMI 變化（假設長期累積或單日過量產生的視覺變化模擬）
        simulated_weight = weight + (max(0, -projected_remaining) / 7700 * 5)  # 趣味視覺模擬加權
        simulated_bmi = simulated_weight / ((height / 100) ** 2)
        simulated_tier, simulated_body_state = get_body_tier(simulated_bmi)
        
        # 若熱量超標，讓預估外觀至少比原本胖一階 (上限第 4 階超胖)
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
            
        # 4. 吃了之後怎麼辦 (Action Plan)
        st.markdown("#### 4️⃣ 💡 吃了之後的補救與行動計畫 (Post-meal Action Plan)")
        if projected_remaining < 0:
            st.info("""
            * **運動代償：** 建議飯後進行 45 分鐘至 1 小時的有氧運動（如慢跑或快走）來燃燒多餘熱量，維持防禦力。
            * **水分加速代謝：** 接下來請多補充 500 c.c. 至 800 c.c. 的水分，幫助身體代謝廢物。
            * **隔日微調：** 若真的吃完超標，明天早餐改為無糖豆漿與水煮蛋，午餐主食減半，將熱量平均拉回平衡！
            """)
        else:
            st.info("""
            * **維持節奏：** 保持目前的飲食與喝水節奏，記得今天的水分目標要喝夠喔！
            * **營養平衡：** 下一餐可以多攝取一些膳食纖維（如深色蔬菜），讓營養更全面。
            """)
