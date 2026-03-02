import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="My Tips Dashboard", layout="wide")
st.title("📊 Báo Cáo Tiền Tips Theo Tháng")


# --- KẾT NỐI DỮ LIỆU ---
@st.cache_data(ttl=600)
def load_data():
    # 1. Khai báo scope TRƯỚC khi sử dụng
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    try:
        # 2. Lấy credentials từ Secrets
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # 3. Mở sheet (Tên file phải khớp 100% trên Google Sheets)
        sheet = client.open("tips_received").sheet1
        data = sheet.get_all_records()

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # 4. Xử lý định dạng ngày tháng
        if 'Ngày' in df.columns:
            # errors='coerce' để tránh sập app nếu có dòng nhập sai ngày
            df['Ngày'] = pd.to_datetime(df['Ngày'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Ngày'])  # Xóa dòng lỗi ngày
            df['Tháng/Năm'] = df['Ngày'].dt.strftime('%m/%Y')
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối hoặc cấu hình Secrets: {e}")
        return pd.DataFrame()


# --- HIỂN THỊ GIAO DIỆN ---
try:
    df = load_data()

    if not df.empty:
        # Xử lý nhóm theo tháng
        df['Sort_Period'] = df['Ngày'].dt.to_period('M')
        df_monthly = df.groupby(['Sort_Period', 'Tháng/Năm'])['Tiền Tips'].sum().reset_index()
        df_monthly = df_monthly.sort_values('Sort_Period')

        st.subheader("🗓️ Tổng hợp thu nhập theo tháng")

        # Hiển thị các ô chỉ số (Metrics)
        cols = st.columns(len(df_monthly))
        for index, row in df_monthly.iterrows():
            with cols[index]:
                st.metric(label=f"Tháng {row['Tháng/Năm']}", value=f"{row['Tiền Tips']:,.0f} VNĐ")

        st.divider()

        # --- BIỂU ĐỒ CỘT ---
        st.subheader("📊 Biểu đồ so sánh thu nhập")
        fig_col = px.bar(
            df_monthly, x='Tháng/Năm', y='Tiền Tips',
            text_auto=',.0f', color='Tiền Tips',
            color_continuous_scale='Viridis'
        )
        # Giữ đúng thứ tự thời gian trên trục X
        fig_col.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': df_monthly['Tháng/Năm'].tolist()})
        st.plotly_chart(fig_col, use_container_width=True)

        # --- BẢNG CHI TIẾT ---
        with st.expander("Xem chi tiết hàng ngày"):
            st.dataframe(df.sort_values(by='Ngày', ascending=False), use_container_width=True)
    else:
        st.warning("Chưa có dữ liệu. Hãy kiểm tra Google Sheets hoặc quyền chia sẻ của Service Account.")

except Exception as e:
    st.error(f"Lỗi hiển thị: {e}")