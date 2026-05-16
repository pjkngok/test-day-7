import streamlit as st
import pandas as pd
import io
import re

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Lead Scoring System - No Setup", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #2e7d32; color: white; font-weight: bold; }
    .stDownloadButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #1565c0; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- BỘ MÁY CHẤM ĐIỂM TỰ ĐỘNG ---
def score_lead_logic(text):
    text = str(text).lower()
    score = 0
    reasons = []
    
    # Quy tắc VIP (+50)
    vip_rules = {
        "Ngân sách khủng (>=20 tỷ)": [r"20 tỷ", "tài chính mạnh", "không thành vấn đề"],
        "Loại hình cao cấp": ["biệt thự đơn lập", "penthouse", "shophouse", "đất công nghiệp"],
        "Vị trí đắc địa": ["quận 1", "ven sông", "ocean park", "phú mỹ hưng"],
        "Đối tượng VIP": ["chủ doanh nghiệp", "nhà đầu tư chuyên nghiệp", "mua sỉ"]
    }
    
    # Quy tắc Rác (-50)
    trash_rules = {
        "Giá phi thực tế (Q1 giá rẻ)": [r"quận 1.*1 tỷ", r"quận 1.*2 tỷ", r"trung tâm.*vài trăm triệu"],
        "Không nhu cầu/Nhầm số": ["nhầm số", "dữ liệu cũ", "không có nhu cầu"],
        "Spam/Dịch vụ khác": ["bảo hiểm", "vay vốn", "mời chào"]
    }
    
    for cat, kws in vip_rules.items():
        if any(re.search(kw, text) if '*' in kw else kw in text for kw in kws):
            score += 50
            reasons.append(cat)
            
    for cat, kws in trash_rules.items():
        if any(re.search(kw, text) if '*' in kw else kw in text for kw in kws):
            score -= 50
            reasons.append(cat)

    classification = "VIP" if score >= 50 else ("Rác" if score <= -50 else "Tiềm năng")
    return score, ", ".join(reasons) if reasons else "Nhu cầu cơ bản", classification

# --- HÀM TẢI DỮ LIỆU ---
def load_data(option, url_or_file):
    try:
        if option == "Dán Link Google Sheet":
            sheet_id = url_or_file.split("/d/")[1].split("/")[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            return pd.read_csv(csv_url)
        elif option == "Tải file từ máy":
            if url_or_file.name.endswith('.csv'):
                return pd.read_csv(url_or_file)
            else:
                return pd.read_excel(url_or_file)
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return None

# --- GIAO DIỆN CHÍNH ---
def main():
    st.title("🚀 AI Lead Scoring System (Rule-Based)")
    st.markdown("##### Hệ thống chấm điểm khách hàng tự động - Không cần API Key")

    # SIDEBAR
    with st.sidebar:
        st.header("📥 Nhập dữ liệu")
        option = st.radio("Chọn nguồn:", ["Dán Link Google Sheet", "Tải file từ máy"])
        
        df = None
        if option == "Dán Link Google Sheet":
            url = st.text_input("Link Sheet (Công khai):", "https://docs.google.com/spreadsheets/d/161rDQEERl85IAANmx2scCWhZ_GmxIK5EWaeD7Vuyeuw/edit")
            if st.button("Tải từ Google Sheet"):
                df = load_data(option, url)
        else:
            uploaded_file = st.file_uploader("Chọn file Excel/CSV", type=["xlsx", "csv"])
            if uploaded_file:
                df = load_data(option, uploaded_file)

    # NỘI DUNG CHÍNH
    if df is not None:
        st.success(f"Đã tải {len(df)} dòng dữ liệu!")
        st.write("### 🔍 Xem trước dữ liệu")
        st.dataframe(df.head(10), use_container_width=True)
        
        target_col = st.selectbox("Chọn cột chứa mô tả nhu cầu để chấm điểm:", df.columns, index=len(df.columns)-1)
        
        if st.button("⚡ Bắt đầu chấm điểm tự động"):
            with st.spinner("Đang xử lý..."):
                results = df[target_col].apply(score_lead_logic)
                df[['Điểm', 'Lý do', 'Phân loại']] = pd.DataFrame(results.tolist(), index=df.index)
                st.session_state['scored_df'] = df
                st.success("Đã hoàn tất chấm điểm!")

        if 'scored_df' in st.session_state:
            st.divider()
            st.write("### ✅ Kết quả & Kiểm duyệt")
            # Cho phép sửa trực tiếp
            final_df = st.data_editor(st.session_state['scored_df'], use_container_width=True)
            
            # Xuất Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Tải file Excel kết quả",
                data=output.getvalue(),
                file_name="ket_qua_cham_diem.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("👈 Hãy chọn nguồn dữ liệu ở thanh bên trái để bắt đầu.")

if __name__ == "__main__":
    main()
