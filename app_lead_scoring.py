import streamlit as st
import pandas as pd
import io
import re

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Lead Scoring System - Stable Version", layout="wide")

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
    
    vip_rules = {
        "Ngân sách lớn (>=20 tỷ)": [r"20 tỷ", "tài chính mạnh", "không thành vấn đề"],
        "Loại hình cao cấp": ["biệt thự đơn lập", "penthouse", "shophouse", "đất công nghiệp"],
        "Vị trí đắc địa": ["quận 1", "ven sông", "ocean park", "phú mỹ hưng"],
        "Đối tượng VIP": ["chủ doanh nghiệp", "nhà đầu tư chuyên nghiệp", "mua sỉ"]
    }
    
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
def load_data_from_url(url):
    try:
        sheet_id = url.split("/d/")[1].split("/")[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        return pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"Lỗi tải từ Google Sheet: {e}")
        return None

# --- GIAO DIỆN CHÍNH ---
def main():
    st.title("🚀 AI Lead Scoring System (Stable)")
    st.markdown("##### Hệ thống chấm điểm khách hàng tự động - Phiên bản ổn định")

    # Khởi tạo session state để lưu dữ liệu
    if 'raw_df' not in st.session_state:
        st.session_state['raw_df'] = None
    if 'scored_df' not in st.session_state:
        st.session_state['scored_df'] = None

    # SIDEBAR
    with st.sidebar:
        st.header("📥 Nhập dữ liệu")
        option = st.radio("Chọn nguồn:", ["Dán Link Google Sheet", "Tải file từ máy"])
        
        if option == "Dán Link Google Sheet":
            url = st.text_input("Link Sheet (Công khai):", "https://docs.google.com/spreadsheets/d/161rDQEERl85IAANmx2scCWhZ_GmxIK5EWaeD7Vuyeuw/edit")
            if st.button("Tải từ Google Sheet"):
                with st.spinner("Đang tải dữ liệu..."):
                    df = load_data_from_url(url)
                    if df is not None:
                        st.session_state['raw_df'] = df
                        st.session_state['scored_df'] = None # Reset kết quả cũ
                        st.success("Tải thành công!")
        else:
            uploaded_file = st.file_uploader("Chọn file Excel/CSV", type=["xlsx", "csv"])
            if uploaded_file:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                st.session_state['raw_df'] = df
                st.session_state['scored_df'] = None

    # NỘI DUNG CHÍNH
    if st.session_state['raw_df'] is not None:
        df = st.session_state['raw_df']
        st.write(f"✅ Đang có {len(df)} dòng dữ liệu sẵn sàng.")
        
        with st.expander("🔍 Xem trước dữ liệu gốc", expanded=True):
            st.dataframe(df.head(10), use_container_width=True)
        
        target_col = st.selectbox("Chọn cột chứa mô tả nhu cầu để chấm điểm:", df.columns, index=len(df.columns)-1)
        
        if st.button("⚡ Bắt đầu chấm điểm tự động"):
            with st.spinner("Đang phân tích từng dòng..."):
                results = df[target_col].apply(score_lead_logic)
                scored_df = df.copy()
                scored_df[['Điểm', 'Lý do', 'Phân loại']] = pd.DataFrame(results.tolist(), index=df.index)
                st.session_state['scored_df'] = scored_df
                st.success("Đã hoàn tất chấm điểm!")

        if st.session_state['scored_df'] is not None:
            st.divider()
            st.write("### ✅ Kết quả Chấm điểm & Kiểm duyệt")
            # Hiển thị bảng kết quả cho phép chỉnh sửa
            final_df = st.data_editor(st.session_state['scored_df'], use_container_width=True, key="editor")
            
            # Xuất Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Tải file Excel kết quả hoàn chỉnh",
                data=output.getvalue(),
                file_name="ket_qua_cham_diem_lead.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("👈 Hãy chọn nguồn dữ liệu ở thanh bên trái và nhấn nút 'Tải' để bắt đầu.")

if __name__ == "__main__":
    main()
