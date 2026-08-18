import streamlit as st
from PIL import Image, ImageDraw

# 頁面基本設定
st.set_page_config(
    page_title="身態模擬器",
    page_icon="🌿",
    layout="wide"
)

# 最佳化截圖與邊界裁切函數（整合最新演算法）
def get_optimal_character_crop(img, base_padding=20):
    """
    根據人物胖瘦比例自動偵測非透明邊界，並計算最適截圖與顯示比例
    
    Parameters:
        img (PIL.Image or str): 角色渲染後的圖片或圖片路徑
        base_padding (int): 基礎安全邊距
        
    Returns:
        PIL.Image: 裁切完成的最佳化圖片
    """
    if isinstance(img, str):
        img = Image.open(img).convert("RGBA")
    else:
        img = img.convert("RGBA")
        
    # 自動取得非透明區域的最小邊界框
    bbox = img.getbbox()
    
    if not bbox:
        return img  # 若整張圖皆為空，則直接回傳原圖
        
    left, upper, right, lower = bbox
    
    # 計算當前身形的寬高與胖瘦比例 (Aspect Ratio)
    width = right - left
    height = lower - upper
    aspect_ratio = width / height if height > 0 else 1.0  # 胖瘦比例：身形越寬，此數值越大
    
    # 動態調整邊距 (Padding)：體型變胖（寬度增加）時，水平方向自動增加額外留白
    dynamic_padding_x = int(base_padding * max(1.0, aspect_ratio * 1.2))
    dynamic_padding_y = base_padding
    
    # 計算最終裁切座標（確保不超出圖片原始尺寸範圍）
    img_width, img_height = img.size
    new_left = max(0, left - dynamic_padding_x)
    new_upper = max(0, upper - dynamic_padding_y)
    new_right = min(img_width, right + dynamic_padding_x)
    new_lower = min(img_height, lower + dynamic_padding_y)
    
    # 執行精準裁切
    cropped_img = img.crop((new_left, new_upper, new_right, new_lower))
    
    return cropped_img

# 主標題
st.title("🌿 身態模擬器")

# 建立兩欄式排版
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader("📋 基本資料")
    
    name = st.text_input("角色名稱", "小勇士")
    
    col_age, col_gender = st.columns(2)
    with col_age:
        age = st.number_input("年齡 (歲)", value=25, step=1)
    with col_gender:
        gender = st.selectbox("性別", ["女", "男"])
        
    col_height, col_weight = st.columns(2)
    with col_height:
        height = st.number_input("身高 (cm)", value=150.0, step=0.5)
    with col_weight:
        weight = st.number_input("目前體重 (kg)", value=50.0, step=0.5)
        
    target_weight = st.number_input("目標體重 (kg)", value=45.0, step=0.5)

# 計算健康指標 (BMI)
bmi = weight / ((height / 100) ** 2)

# BMR 計算 (Mifflin-St Jeor 公式)
if gender == "女":
    bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
else:
    bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5

tdee = bmr * 1.2  # 預設日常活動係數

with col_right:
    # 建立示範用透明畫布以模擬角色動態渲染
    img_width, img_height = 400, 600
    base_img = Image.new("RGBA", (img_width, img_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(base_img)
    
    # 根據體重動態改變身體寬度（模擬胖瘦身形變化）
    body_width = int(90 + (weight - 50) * 2.5)
    body_width = max(40, min(body_width, 220))
    
    # 繪製頭部
    draw.ellipse([img_width//2 - 45, 120, img_width//2 + 45, 210], fill=(255, 220, 200, 255))
    # 繪製軀幹（隨體重變寬/變窄）
    draw.rectangle([img_width//2 - body_width//2, 210, img_width//2 + body_width//2, 480], fill=(100, 150, 250, 255))
    
    # 應用最新的動態邊界截圖裁切函數
    processed_img = get_optimal_character_crop(base_img)
    
    # 判斷狀態
    if bmi < 18.5:
        status_text = "過輕"
    elif 18.5 <= bmi < 24:
        status_text = "正常 (健康)"
    elif 24 <= bmi < 27:
        status_text = "過重"
    else:
        status_text = "肥胖"
        
    st.markdown(f"<div style='text-align: center; font-size: 18px;'><b>狀態：{status_text}</b></div>", unsafe_allow_html=True)
    st.image(processed_img, caption=f"{name} 的身態預覽", use_column_width=True)

# 下方數據看板
st.markdown("---")
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("基礎代謝 (BMR)", f"{int(bmr)} kcal")
with m2:
    st.metric("每日消耗 (TDEE)", f"{int(tdee)} kcal")
with m3:
    st.metric("目前 BMI", f"{bmi:.1f}")
with m4:
    st.metric("今日剩餘熱量", f"{int(tdee)} kcal")

st.info("💡 歡迎進入身態模擬器！請設定你的基本資料並開始記錄健康生活吧！")
