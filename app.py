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
    # Khai báo scope chuẩn cho Google Sheets & Drive
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    try:
        # Lấy thông tin từ Streamlit Secrets
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # Mở file Google Sheets (Tên file phải khớp 100%)
        sheet = client.open("tips_received").sheet1
        data = sheet.get_all_records()

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Xử lý cột 'Ngày' và 'Tiền Tips'
        if 'Ngày' in df.columns:
            # dayfirst=True để hiểu đúng định dạng DD/MM/YYYY của Việt Nam
            df['Ngày'] = pd.to_datetime(df['Ngày'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Ngày'])
            df['Tháng/Năm'] = df['Ngày'].dt.strftime('%m/%Y')

        return df
    except Exception as e:
        st.error(f"Lỗi kết nối hoặc cấu hình: {e}")
        return pd.DataFrame()


# --- HIỂN THỊ GIAO DIỆN ---
try:
    df = load_data()

    if not df.empty:
        # Sắp xếp dữ liệu theo thời gian
        df['Sort_Period'] = df['Ngày'].dt.to_period('M')
        df_monthly = df.groupby(['Sort_Period', 'Tháng/Năm'])['Tiền Tips'].sum().reset_index()
        df_monthly = df_monthly.sort_values('Sort_Period')

        st.subheader("🗓️ Tổng hợp thu nhập theo tháng")

        # Hiển thị Metrics (Số tổng) theo hàng ngang
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
        # Đảm bảo trục X giữ đúng thứ tự thời gian
        fig_col.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': df_monthly['Tháng/Năm'].tolist()})
        st.plotly_chart(fig_col, use_container_width=True)

        # --- BẢNG CHI TIẾT ---
        with st.expander("🔍 Xem bảng chi tiết hàng ngày"):
            st.dataframe(df.sort_values(by='Ngày', ascending=False), use_container_width=True)
    else:
        st.warning("⚠️ Chưa có dữ liệu hoặc chưa cấp quyền cho Service Account. Hãy kiểm tra lại file Google Sheets.")

except Exception as e:
    st.error(f"Lỗi hiển thị biểu đồ: {e}")