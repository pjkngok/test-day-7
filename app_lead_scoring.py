import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
import os
from dotenv import load_dotenv
import io

# 1. CẤU HÌNH & KHỞI TẠO
load_dotenv()
st.set_page_config(page_title="Lead Scoring System", layout="wide")

# Thiết lập Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    st.error("⚠️ Chưa tìm thấy GEMINI_API_KEY trong file .env")

# Đọc file skill để làm prompt cho AI
def get_scoring_rules():
    try:
        # Đường dẫn tương đối từ thư mục dự án lên thư mục cha
        skill_path = os.path.join(os.path.dirname(__file__), "..", "lead_scoring_skill.md")
        with open(skill_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Sử dụng quy tắc chấm điểm bất động sản thông thường. (Lỗi đọc file skill: {e})"

# 2. XỬ LÝ DỮ LIỆU GOOGLE SHEETS
def fetch_data_from_gsheet(sheet_url):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Lưu ý: Cần có file credentials.json trong thư mục
        creds_path = os.path.join(os.path.dirname(__file__), "credentials.json")
        creds = Credentials.from_service_account_file(creds_path, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(sheet_url).sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Google Sheets: {e}")
        st.info("💡 Mẹo: Hãy đảm bảo file credentials.json đã được đặt trong thư mục dự án và bạn đã share quyền Viewer/Editor cho email trong file đó.")
        return None

# 3. AI SCORING LOGIC
def ai_score_lead(lead_description):
    rules = get_scoring_rules()
    model = genai.GenerativeModel('gemini-1.5-flash') # Dùng bản flash cho nhanh và tiết kiệm
    prompt = f"""
    Bạn là một chuyên gia thẩm định khách hàng bất động sản. 
    Dựa trên bộ quy tắc sau:
    {rules}
    
    Hãy chấm điểm cho khách hàng có nhu cầu sau:
    "{lead_description}"
    
    Trả về kết quả duy nhất dưới dạng JSON (không có markdown):
    {{
        "score": number,
        "reason": "giải thích ngắn gọn",
        "classification": "VIP/Tiềm năng/Trung bình/Rác"
    }}
    """
    try:
        response = model.generate_content(prompt)
        import json
        res_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(res_text)
    except Exception as e:
        return {"score": 0, "reason": f"Lỗi phân tích AI: {e}", "classification": "Chưa rõ"}

# 4. GIAO DIỆN WEB APP (Human-in-the-loop)
def main():
    st.title("🚀 AI Lead Scoring System")
    st.markdown("### Hệ thống chấm điểm khách hàng tự động & Kiểm duyệt")

    # Sidebar: Cấu hình
    with st.sidebar:
        st.header("⚙️ Cấu hình")
        gsheet_url = st.text_input("Link Google Sheet", value="https://docs.google.com/spreadsheets/d/161rDQEERl85IAANmx2scCWhZ_GmxIK5EWaeD7Vuyeuw/edit")
        
        # Kiểm tra file config
        has_env = os.path.exists(os.path.join(os.path.dirname(__file__), ".env"))
        has_creds = os.path.exists(os.path.join(os.path.dirname(__file__), "credentials.json"))
        
        if not has_env: st.warning("⚠️ Thiếu file .env")
        if not has_creds: st.warning("⚠️ Thiếu file credentials.json")
        
        if st.button("📥 Lấy dữ liệu"):
            df = fetch_data_from_gsheet(gsheet_url)
            if df is not None:
                st.session_state['raw_data'] = df
                st.success(f"Đã lấy {len(df)} khách hàng")

    # Main Area
    if 'raw_data' in st.session_state:
        df = st.session_state['raw_data']
        
        tab1, tab2 = st.tabs(["🔍 Chấm điểm AI", "✅ Kiểm duyệt & Xuất file"])
        
        with tab1:
            st.dataframe(df, use_container_width=True)
            if st.button("🤖 Bắt đầu chấm điểm bằng AI"):
                scored_results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, row in df.iterrows():
                    status_text.text(f"Đang xử lý khách hàng: {row.get('ten_khach', 'N/A')}...")
                    res = ai_score_lead(row.get('nhu_cau_mo_ta', ''))
                    row_scored = {**row, **res}
                    scored_results.append(row_scored)
                    progress_bar.progress((i + 1) / len(df))
                
                status_text.text("✅ Hoàn tất chấm điểm!")
                st.session_state['scored_data'] = pd.DataFrame(scored_results)
                st.dataframe(st.session_state['scored_data'], use_container_width=True)

        with tab2:
            if 'scored_data' in st.session_state:
                st.markdown("#### Chỉnh sửa kết quả (Nếu cần)")
                # Cho phép người dùng sửa trực tiếp trên bảng
                edited_df = st.data_editor(st.session_state['scored_data'], num_rows="dynamic", use_container_width=True)
                
                st.divider()
                
                # Xuất file Excel
                if st.button("📥 Xuất file Excel bàn giao"):
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        edited_df.to_excel(writer, index=False, sheet_name='Leads_Scored')
                    
                    st.download_button(
                        label="💾 Click để tải file Excel",
                        data=buffer.getvalue(),
                        file_name="leads_scored_report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.info("Vui lòng thực hiện chấm điểm ở Tab 1 trước.")
    else:
        st.info("👈 Hãy nhập link Google Sheet và nhấn 'Lấy dữ liệu' ở thanh bên trái.")

if __name__ == "__main__":
    main()
